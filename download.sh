#!/bin/bash
set -e

# Function to print status messages
log() {
	echo -e "\033[1;32m$1\033[0m"
}

# Step 1: Create venv directory (hf_env) if it doesn't exist
if [ ! -d "hf_env" ]; then
	log "Creating Python virtual environment in hf_env..."
	python3 -m venv hf_env
else
	log "Virtual environment already exists."
fi

# Step 2: Activate the virtual environment
source hf_env/bin/activate

# Step 3: Install required packages (huggingface_hub)
if ! pip show huggingface_hub > /dev/null 2>&1; then
	log "Installing huggingface_hub[cli]..."
	pip install --upgrade pip
	pip install "huggingface_hub[cli]"
else
	log "huggingface_hub is already installed."
fi

# Step 4: Download models from Hugging Face
MODELS=(
	# "openai/qwen3-30b-a3b"
	"Qwen/Qwen3-30B-A3B-Instruct-2507"
	"google/embeddinggemma-300m"
)


# Download models into Hugging Face cache
for model in "${MODELS[@]}"; do
       log "Ensuring $model is downloaded into Hugging Face cache..."
       hf download $model
done

# Step 5: Deactivate the virtual environment
deactivate
log "All done!"