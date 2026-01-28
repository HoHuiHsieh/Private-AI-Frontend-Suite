import sys
import os
import json
import numpy as np
import glob
import triton_python_backend_utils as pb_utils
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer


class TritonPythonModel:

    def initialize(self, args):
        """
        This function allows the model to initialize any state associated with this model.

        Parameters
        ----------
        args : dict
          Both keys and values are strings. The dictionary keys and values are:
          * model_config: A JSON string containing the model configuration
          * model_instance_kind: A string containing model instance kind
          * model_instance_device_id: A string containing model instance device ID
          * model_repository: Model repository path
          * model_version: Model version
          * model_name: Model name
        """
        # Parse model configs
        model_config = json.loads(args["model_config"])
        model_path = model_config["parameters"]["model_path"]["string_value"]
        model_device = model_config["parameters"]["device"]["string_value"]
        batch_size = int(model_config["parameters"]["batch_size"]["string_value"])
        # Load model with tokenizer on specified device
        # Check device availability
        if model_device.lower() == "cuda" and not torch.cuda.is_available():
            print(f"CUDA requested but not available. Falling back to CPU.")
            model_device = "cpu"

        print(f"Initializing EmbeddingGemma model on device: {model_device} with batch size: {batch_size}")
        self.model = SentenceTransformer(model_path, device=model_device)
        self.batch_size = batch_size

    def execute(self, requests):
        """
        This function is called when an inference is requested for this model. 

        Parameters
        ----------
        requests : list
          A list of pb_utils.InferenceRequest

        Returns
        -------
        list
          A list of pb_utils.InferenceResponse. The length of this list must
          be the same as `requests`
        """

        responses = []

        # Every Python backend must iterate over everyone of the requests
        # and create a pb_utils.InferenceResponse for each of them.
        for idx, request in enumerate(requests):
            try:
                # Get query as a string (dims: [1])
                # With max_batch_size: 0, no batch dimension is added by Triton
                query = pb_utils.get_input_tensor_by_name(request, "query")
                if query is not None:
                    query_array = query.as_numpy()
                    # Extract the string from shape (1,)
                    query = query_array[0].decode("utf8") if isinstance(
                        query_array[0], bytes) else str(query_array[0])

                # Get documents as a list of strings (dims: [1, -1])
                documents = pb_utils.get_input_tensor_by_name(
                    request, "documents")
                if documents is not None:
                    documents_array = documents.as_numpy()
                    # For dims [1, -1]: if shape is (1, n), extract from first dimension
                    # For dims [-1]: if shape is (n,), use directly
                    if documents_array.ndim == 2:
                        # Shape: (1, n) - extract strings from first row
                        documents = [doc.decode("utf8") if isinstance(doc, bytes) else str(doc)
                                     for doc in documents_array[0]]
                    else:
                        # Shape: (n,) - use directly
                        documents = [doc.decode("utf8") if isinstance(doc, bytes) else str(doc)
                                     for doc in documents_array]

                # get the embeddings
                if query is not None:
                    # Use query prompt - expects a single string
                    embeddings = self.model.encode_query(query)
                    # Returns shape: (embedding_dim,)
                elif documents is not None and len(documents) > 0:
                    # Use document prompt - expects a list of strings
                    # Batch encoding with max batch size 10
                    batch_size = self.batch_size
                    all_embeddings = []
                    for i in range(0, len(documents), batch_size):
                        batch = documents[i:i + batch_size]
                        batch_embeddings = self.model.encode_document(batch)
                        all_embeddings.append(batch_embeddings)
                    embeddings = np.concatenate(all_embeddings, axis=0)
                    # Returns shape: (num_docs, embedding_dim)
                else:
                    raise ValueError(
                        "Either 'query' or 'documents' input must be provided.")

                # Convert to numpy if it's a torch tensor and ensure it's on CPU
                if isinstance(embeddings, torch.Tensor):
                    embeddings = embeddings.cpu().numpy()

                # Ensure embeddings is 2D with shape (1, embedding_dim) for output dims: [1, -1]
                if embeddings.ndim == 1:
                    embeddings = embeddings.reshape(1, -1)

                # Prepare results - output shape should be (1, embedding_dim)
                context_output = pb_utils.Tensor(
                    "embeddings", embeddings.astype(np.float32)
                )
                inference_response = pb_utils.InferenceResponse(
                    output_tensors=[context_output]
                )
                responses.append(inference_response)

            except Exception as error:
                print(sys.exc_info()[2])
                responses.append(pb_utils.InferenceResponse(output_tensors=[],
                                                            error=pb_utils.TritonError(error)))

        # You should return a list of pb_utils.InferenceResponse. Length
        # of this list must match the length of `requests` list.
        return responses

    def finalize(self):
        """
        This function allows the model to perform any necessary clean ups before exit.
        """
        print("Cleaning up...")
