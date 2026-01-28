#!/usr/bin/env python3
"""
Chat Completions Endpoint Test Script

This script tests the /v1/chat/completions endpoint (OpenAI-compatible).
It sends HTTP requests to the running API server.

Usage:
    python test_chat_endpoint.py [--host HOST] [--port PORT]

Requirements:
    - Server must be running
    - requests library (pip install requests)
    - Valid API key or admin credentials
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

# Model name to test
CHAT_MODEL = "qwen3-30b-a3b"

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


def print_response(response, truncate_content=False):
    """Pretty print response"""
    print(f"{Colors.OKBLUE}Status Code: {response.status_code}{Colors.ENDC}")
    try:
        data = response.json()
        if truncate_content and "choices" in data:
            # Truncate long content for readability
            for choice in data["choices"]:
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    if len(content) > 200:
                        choice["message"]["content"] = content[:200] + \
                            "... (truncated)"
        print(f"{Colors.OKBLUE}Response:{Colors.ENDC}")
        print(json.dumps(data, indent=2))
    except:
        print(response.text[:500])


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
        print_response(response)
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
            "name": f"test_chat_key_{int(time.time())}",
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
        print_response(response)
        return None


def test_chat_completion_basic(api_key):
    """
    Test POST /v1/chat/completions with basic request
    """
    print_header("TEST: Basic Chat Completion (POST /v1/chat/completions)")

    try:
        request_data = {
            "model": CHAT_MODEL,
            "messages": [
                {"role": "user", "content": "Say hello in one word"}
            ],
            "max_completion_tokens": 100,
            "reasoning_effort": "none"
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()

            # Validate response structure (OpenAI-compatible)
            if "id" in data:
                print_success(f"Response has 'id' field: {data['id']}")
            else:
                print_error("Response missing 'id' field")

            if "object" in data and data["object"] == "chat.completion":
                print_success(
                    "Response has correct 'object' field: 'chat.completion'")
            else:
                print_warning(
                    f"Response 'object' field: {data.get('object', 'missing')}")

            if "created" in data:
                created_time = datetime.fromtimestamp(data["created"])
                print_success(f"Response has 'created' field: {created_time}")
            else:
                print_warning("Response missing 'created' field")

            if "model" in data:
                print_success(f"Response has 'model' field: {data['model']}")
            else:
                print_warning("Response missing 'model' field")

            if "choices" in data and len(data["choices"]) > 0:
                print_success(f"Response has {len(data['choices'])} choice(s)")

                choice = data["choices"][0]
                if "message" in choice:
                    message = choice["message"]
                    if "role" in message and "content" in message:
                        print_success(
                            f"Choice has message with role '{message['role']}' and content")
                        print_info(f"Content: {message['content']}")
                    else:
                        print_error("Message missing 'role' or 'content'")

                if "finish_reason" in choice:
                    print_success(
                        f"Choice has finish_reason: {choice['finish_reason']}")
                else:
                    print_warning("Choice missing 'finish_reason'")
            else:
                print_error("Response missing 'choices' or empty")

            if "usage" in data:
                usage = data["usage"]
                print_success(f"Response has usage data:")
                print_info(
                    f"  - Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print_info(
                    f"  - Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print_info(
                    f"  - Total tokens: {usage.get('total_tokens', 'N/A')}")
            else:
                print_warning("Response missing 'usage' field")

            print_success("\n✓ Basic chat completion test PASSED")
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_chat_completion_with_system_message(api_key):
    """
    Test chat completion with system message
    """
    print_header("TEST: Chat Completion with System Message")

    try:
        request_data = {
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system",
                    "content": "You are a helpful assistant that speaks like a pirate."},
                {"role": "user", "content": "Tell me about the weather"}
            ],
            "max_completion_tokens": 100,
            "reasoning_effort": "none"
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response, truncate_content=True)

        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                print_success("✓ Chat completion with system message PASSED")
                return True

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_chat_completion_multi_turn(api_key):
    """
    Test multi-turn conversation
    """
    print_header("TEST: Multi-turn Chat Conversation")

    try:
        request_data = {
            "model": CHAT_MODEL,
            "messages": [
                {"role": "user", "content": "What is 2+2?"},
                {"role": "assistant", "content": "2+2 equals 4."},
                {"role": "user", "content": "What about 3+3?"}
            ],
            "max_completion_tokens": 100,
            "reasoning_effort": "none"
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response, truncate_content=True)

        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                print_success("✓ Multi-turn conversation test PASSED")
                return True

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_chat_completion_with_temperature(api_key):
    """
    Test chat completion with temperature parameter
    """
    print_header("TEST: Chat Completion with Temperature Parameter")

    try:
        request_data = {
            "model": CHAT_MODEL,
            "messages": [
                {"role": "user", "content": "Say something creative"}
            ],
            "max_completion_tokens": 100,
            "temperature": 1,
            "reasoning_effort": "none"
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response, truncate_content=True)

        if response.status_code == 200:
            print_success("✓ Chat completion with temperature test PASSED")
            return True

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_chat_completion_streaming(api_key):
    """
    Test streaming chat completion
    """
    print_header("TEST: Streaming Chat Completion")

    try:
        request_data = {
            "model": CHAT_MODEL,
            "messages": [
                {"role": "user", "content": "Count from 1 to 5"}
            ],
            "max_completion_tokens": 100,
            "stream": True,
            "reasoning_effort": "none"
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data,
            stream=True
        )

        print(f"{Colors.OKBLUE}Status Code: {response.status_code}{Colors.ENDC}")

        if response.status_code == 200:
            print_info("Receiving streaming response...")
            chunk_count = 0

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            print_info("\nReceived [DONE] signal")
                            break
                        try:
                            chunk = json.loads(data_str)
                            chunk_count += 1
                            if chunk_count <= 3:  # Show first 3 chunks
                                print(
                                    f"{Colors.OKBLUE}Chunk {chunk_count}:{Colors.ENDC}")
                                print(json.dumps(chunk, indent=2))
                        except json.JSONDecodeError:
                            pass

            if chunk_count > 0:
                print_success(
                    f"\n✓ Streaming test PASSED (received {chunk_count} chunks)")
                return True
            else:
                print_error("No chunks received")
                return False

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_chat_completion_without_auth():
    """
    Test chat completion without authentication (should fail)
    """
    print_header("TEST: Chat Completion Without Authentication (Should Fail)")

    try:
        request_data = {
            "model": CHAT_MODEL,
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "reasoning_effort": "none"
        }

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=request_data
        )

        print_response(response)

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


def test_chat_completion_invalid_model(api_key):
    """
    Test chat completion with invalid model (should fail)
    """
    print_header("TEST: Chat Completion with Invalid Model (Should Fail)")

    try:
        request_data = {
            "model": "invalid-model-xyz",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "reasoning_effort": "none"
        }

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response)

        if response.status_code in [400, 404]:
            print_success(
                f"✓ Correctly rejected invalid model with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected 400/404, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_chat_completion_missing_messages(api_key):
    """
    Test chat completion without messages (should fail)
    """
    print_header("TEST: Chat Completion Without Messages (Should Fail)")

    try:
        request_data = {
            "model": CHAT_MODEL,
            "reasoning_effort": "none"
        }

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response)

        if response.status_code in [400, 422]:
            print_success(
                f"✓ Correctly rejected missing messages with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected 400/422, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def run_all_tests():
    """Run all test cases"""
    print_header("OpenAI-Compatible Chat Completions Endpoint Test Suite")
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

    # Run tests
    tests = [
        ("Basic chat completion", lambda: test_chat_completion_basic(api_key)),
        ("Chat with system message",
         lambda: test_chat_completion_with_system_message(api_key)),
        ("Multi-turn conversation", lambda: test_chat_completion_multi_turn(api_key)),
        ("Chat with temperature", lambda: test_chat_completion_with_temperature(api_key)),
        ("Streaming chat completion", lambda: test_chat_completion_streaming(api_key)),
        ("Chat without authentication", test_chat_completion_without_auth),
        ("Chat with invalid model", lambda: test_chat_completion_invalid_model(api_key)),
        ("Chat without messages", lambda: test_chat_completion_missing_messages(api_key)),
    ]

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
        description="Test /v1/chat/completions endpoint")
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
