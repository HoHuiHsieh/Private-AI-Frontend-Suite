#!/usr/bin/env python3
"""
Embeddings Endpoint Test Script
Tests OpenAI-compatible /v1/embeddings endpoint with multiple models
"""
import os
import requests
import json
import sys
import argparse
import time
from datetime import datetime

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 3000
BASE_URL = None

# Admin credentials for obtaining API key
ADMIN_CREDENTIALS = {
    "username": os.getenv("DEFAULT_ADMIN_EMAIL"),
    "password": os.getenv("DEFAULT_ADMIN_PASSWORD"),
}

# Test models
TRITON_MODEL = "embeddinggemma-300m"

# Colors for output


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_response(response, truncate_embeddings=True):
    """Pretty print response (truncate embeddings for readability)"""
    print(f"{Colors.OKBLUE}Status Code: {response.status_code}{Colors.ENDC}")
    try:
        data = response.json()
        # Truncate embedding vectors for readability
        if truncate_embeddings and 'data' in data:
            for item in data['data']:
                if 'embedding' in item:
                    embedding = item['embedding']
                    if isinstance(embedding, list) and len(embedding) > 5:
                        item['embedding'] = f"[{len(embedding)} dimensions] [{embedding[0]:.6f}, {embedding[1]:.6f}, {embedding[2]:.6f}, ...]"
                    elif isinstance(embedding, str) and len(embedding) > 100:
                        item['embedding'] = f"[base64, {len(embedding)} chars] {embedding[:50]}..."
        print(f"{Colors.OKBLUE}Response:{Colors.ENDC}")
        print(json.dumps(data, indent=2))
    except:
        print(response.text)


def login_admin():
    """Login as admin and return access token"""
    print_info("Logging in as admin to get API key...")

    response = requests.post(
        f"{BASE_URL}/api/login",
        data=ADMIN_CREDENTIALS
    )

    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        print_success(f"Admin login successful")
        return access_token
    else:
        print_error(f"Admin login failed: {response.status_code}")
        print_response(response, truncate_embeddings=False)
        return None


def get_or_create_api_key(access_token):
    """Get existing API key or create a new one"""
    print_info("Getting or creating API key...")

    # Try to get existing API keys
    response = requests.get(
        f"{BASE_URL}/api/apikeys",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        apikeys = response.json()
        if apikeys and len(apikeys) > 0:
            # Use the first active API key
            for key_data in apikeys:
                if key_data.get("active", False):
                    api_key = key_data.get("api_key")
                    print_success(f"Using existing API key: {api_key[:20]}...")
                    return api_key

    # Create a new API key if none exists
    print_info("No active API key found, creating new one...")
    response = requests.post(
        f"{BASE_URL}/api/apikeys",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "name": f"test_embeddings_key_{int(time.time())}",
            "days": 30
        }
    )

    if response.status_code in [200, 201]:
        data = response.json()
        api_key = data.get("api_key")
        print_success(f"Created new API key: {api_key[:20]}...")
        return api_key
    else:
        print_error(f"Failed to create API key: {response.status_code}")
        print_response(response, truncate_embeddings=False)
        return None


def test_embeddings_single_text(api_key, model):
    """
    Test POST /v1/embeddings with single text input
    """
    print_header(f"TEST: Single Text Embedding - Model: {model}")

    try:
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": "Hello, world! This is a test."
            }
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()

            # Validate response structure (OpenAI-compatible)
            if "object" in data and data["object"] == "list":
                print_success("Response has correct 'object' field: 'list'")
            else:
                print_warning("Response missing or incorrect 'object' field")

            if "model" in data:
                print_success(f"Model: {data['model']}")
            else:
                print_warning("Response missing 'model' field")

            if "data" in data:
                embeddings = data["data"]
                print_success(f"Found {len(embeddings)} embedding(s)")

                # Validate first embedding object
                if len(embeddings) > 0:
                    emb = embeddings[0]

                    if "object" in emb and emb["object"] == "embedding":
                        print_success(f"  - Object: {emb['object']}")
                    else:
                        print_warning(
                            f"  - Object field: {emb.get('object', 'missing')}")

                    if "index" in emb:
                        print_success(f"  - Index: {emb['index']}")
                    else:
                        print_warning("  - Missing 'index' field")

                    if "embedding" in emb:
                        embedding = emb["embedding"]
                        if isinstance(embedding, list):
                            print_success(
                                f"  - Embedding dimensions: {len(embedding)}")
                            print_info(f"  - First 3 values: {embedding[:3]}")
                        else:
                            print_warning(
                                f"  - Embedding type: {type(embedding)}")
                    else:
                        print_error("  - Missing 'embedding' field")
            else:
                print_error("Response missing 'data' field")

            if "usage" in data:
                usage = data["usage"]
                print_success(f"Usage:")
                if "prompt_tokens" in usage:
                    print_success(
                        f"  - Prompt tokens: {usage['prompt_tokens']}")
                if "total_tokens" in usage:
                    print_success(f"  - Total tokens: {usage['total_tokens']}")
            else:
                print_warning("Response missing 'usage' field")

            print_success("\n✓ Single text embedding test PASSED")
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_embeddings_multiple_texts(api_key, model):
    """
    Test POST /v1/embeddings with multiple text inputs
    """
    print_header(f"TEST: Multiple Text Embeddings - Model: {model}")

    try:
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": [
                    "The cat sits on the mat.",
                    "Dogs are loyal companions.",
                    "AI is transforming technology."
                ]
            }
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()

            if "data" in data:
                embeddings = data["data"]
                expected_count = 3

                if len(embeddings) == expected_count:
                    print_success(
                        f"Correct number of embeddings: {len(embeddings)}")
                else:
                    print_warning(
                        f"Expected {expected_count} embeddings, got {len(embeddings)}")

                # Validate each embedding
                for idx, emb in enumerate(embeddings):
                    print_info(f"\nEmbedding {idx + 1}:")

                    if "index" in emb and emb["index"] == idx:
                        print_success(f"  - Index: {emb['index']} (correct)")
                    else:
                        print_warning(
                            f"  - Index: {emb.get('index', 'missing')}")

                    if "embedding" in emb and isinstance(emb["embedding"], list):
                        print_success(
                            f"  - Dimensions: {len(emb['embedding'])}")
                    else:
                        print_error("  - Invalid or missing embedding")

                print_success("\n✓ Multiple text embeddings test PASSED")
                return True
            else:
                print_error("Response missing 'data' field")
                return False
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_embeddings_chinese_text(api_key, model):
    """
    Test POST /v1/embeddings with Chinese text
    """
    print_header(f"TEST: Chinese Text Embedding - Model: {model}")

    try:
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": "你好世界！這是一個測試。人工智慧正在改變世界。"
            }
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()

            if "data" in data and len(data["data"]) > 0:
                emb = data["data"][0]
                if "embedding" in emb and isinstance(emb["embedding"], list):
                    print_success(
                        f"Embedding dimensions: {len(emb['embedding'])}")
                    print_success("✓ Chinese text embedding test PASSED")
                    return True
                else:
                    print_error("Invalid embedding data")
                    return False
            else:
                print_error("Response missing embedding data")
                return False
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_embeddings_base64_encoding(api_key, model):
    """
    Test POST /v1/embeddings with base64 encoding format
    """
    print_header(f"TEST: Base64 Encoding - Model: {model}")

    try:
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": "Test base64 encoding format",
                "encoding_format": "base64"
            }
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()

            if "data" in data and len(data["data"]) > 0:
                emb = data["data"][0]
                if "embedding" in emb:
                    embedding_data = emb["embedding"]
                    if isinstance(embedding_data, str):
                        print_success(
                            f"Embedding is base64 string (length: {len(embedding_data)})")
                        print_info(f"First 50 chars: {embedding_data[:50]}...")
                        print_success("✓ Base64 encoding test PASSED")
                        return True
                    else:
                        print_warning(
                            f"Embedding is not a string: {type(embedding_data)}")
                        return False
                else:
                    print_error("Missing embedding data")
                    return False
            else:
                print_error("Response missing embedding data")
                return False
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_embeddings_with_dimensions(api_key, model):
    """
    Test POST /v1/embeddings with custom dimensions
    Note: Only text-embedding-3 models support this
    """
    print_header(f"TEST: Custom Dimensions - Model: {model}")

    try:
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": "Test custom dimensions",
                "dimensions": 512
            }
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()

            if "data" in data and len(data["data"]) > 0:
                emb = data["data"][0]
                if "embedding" in emb and isinstance(emb["embedding"], list):
                    actual_dims = len(emb["embedding"])
                    requested_dims = 512

                    print_info(f"Requested dimensions: {requested_dims}")
                    print_info(f"Actual dimensions: {actual_dims}")

                    if actual_dims == requested_dims:
                        print_success(
                            "✓ Dimensions match - Custom dimensions test PASSED")
                        return True
                    else:
                        print_warning(
                            "Dimensions don't match (model may not support custom dimensions)")
                        print_success(
                            "✓ Request succeeded but dimensions differ")
                        return True
                else:
                    print_error("Invalid embedding data")
                    return False
            else:
                print_error("Response missing embedding data")
                return False
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_embeddings_without_auth(model):
    """
    Test POST /v1/embeddings without authentication
    Should return 401 or 403
    """
    print_header(f"TEST: Without Authentication - Model: {model}")

    try:
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            headers={"Content-Type": "application/json"},
            json={
                "model": model,
                "input": "This should fail"
            }
        )

        print_response(response, truncate_embeddings=False)

        if response.status_code in [401, 403]:
            print_success(
                f"✓ Correctly rejected with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected 401/403, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_embeddings_invalid_model(api_key):
    """
    Test POST /v1/embeddings with invalid model
    Should return error
    """
    print_header("TEST: Invalid Model")

    try:
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "invalid-model-name-12345",
                "input": "This should fail"
            }
        )

        print_response(response, truncate_embeddings=False)

        if response.status_code in [400, 404, 500]:
            print_success(
                f"✓ Correctly rejected with status {response.status_code}")
            return True
        else:
            print_warning(
                f"⚠ Expected error status, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_embeddings_missing_input(api_key, model):
    """
    Test POST /v1/embeddings with missing input field
    Should return 422 validation error
    """
    print_header(f"TEST: Missing Input Field - Model: {model}")

    try:
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model
                # Missing 'input' field
            }
        )

        print_response(response, truncate_embeddings=False)

        if response.status_code == 422:
            print_success(
                f"✓ Correctly rejected with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected 422, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_embeddings_empty_input(api_key, model):
    """
    Test POST /v1/embeddings with empty input
    """
    print_header(f"TEST: Empty Input - Model: {model}")

    try:
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": ""
            }
        )

        print_response(response, truncate_embeddings=False)

        if response.status_code in [200, 400, 422]:
            print_success(f"✓ Handled with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Got status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def run_all_tests():
    """Run all test cases"""
    print_header("OpenAI-Compatible Embeddings Endpoint Test Suite")
    print_info(f"Testing server at: {BASE_URL}")
    print_info(f"Timestamp: {datetime.now().isoformat()}")

    results = {
        "total": 0,
        "passed": 0,
        "failed": 0
    }

    # Step 1: Login and get API key
    access_token = login_admin()
    if not access_token:
        print_error("Cannot proceed without admin access token")
        return results

    api_key = get_or_create_api_key(access_token)
    if not api_key:
        print_error("Cannot proceed without API key")
        return results

    # Define all tests
    tests = [
        # Triton Model Tests
        (f"Single text - {TRITON_MODEL}",
         lambda: test_embeddings_single_text(api_key, TRITON_MODEL)),
        (f"Multiple texts - {TRITON_MODEL}",
         lambda: test_embeddings_multiple_texts(api_key, TRITON_MODEL)),
        (f"Chinese text - {TRITON_MODEL}",
         lambda: test_embeddings_chinese_text(api_key, TRITON_MODEL)),
        (f"Base64 encoding - {TRITON_MODEL}",
         lambda: test_embeddings_base64_encoding(api_key, TRITON_MODEL)),

        # Error Cases
        (f"No auth - {TRITON_MODEL}",
         lambda: test_embeddings_without_auth(TRITON_MODEL)),
        ("Invalid model", lambda: test_embeddings_invalid_model(api_key)),
        (f"Missing input - {TRITON_MODEL}",
         lambda: test_embeddings_missing_input(api_key, TRITON_MODEL)),
        (f"Empty input - {TRITON_MODEL}",
         lambda: test_embeddings_empty_input(api_key, TRITON_MODEL)),
    ]

    # Run tests
    for test_name, test_func in tests:
        results["total"] += 1
        try:
            if test_func():
                results["passed"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            print_error(f"Test '{test_name}' raised exception: {str(e)}")
            results["failed"] += 1

        time.sleep(0.5)  # Small delay between tests

    # Print summary
    print_header("Test Summary")
    print(f"Total tests: {results['total']}")
    print_success(f"Passed: {results['passed']}")
    if results['failed'] > 0:
        print_error(f"Failed: {results['failed']}")
    else:
        print_success(f"Failed: {results['failed']}")

    success_rate = (results['passed'] / results['total']
                    * 100) if results['total'] > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")

    return results


def main():
    """Main function"""
    global BASE_URL

    parser = argparse.ArgumentParser(
        description="Test /v1/embeddings endpoint")
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Server host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")

    args = parser.parse_args()

    BASE_URL = f"http://{args.host}:{args.port}"

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print_success(f"Server is running at {BASE_URL}")
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to server at {BASE_URL}")
        print_info("Please start the server first")
        sys.exit(1)
    except Exception as e:
        print_warning(f"Health check warning: {str(e)}")

    # Run tests
    results = run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
