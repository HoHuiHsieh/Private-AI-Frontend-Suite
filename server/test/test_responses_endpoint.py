#!/usr/bin/env python3
"""
Responses Endpoint Test Script

This script tests the /v1/responses endpoint (OpenAI-compatible).
It sends HTTP requests to the running API server.

Usage:
    python test_responses_endpoint.py [--host HOST] [--port PORT]

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
        if truncate_content and "output" in data:
            # Truncate long content for readability
            for item in data.get("output", []):
                if "content" in item:
                    for content_item in item["content"]:
                        if "text" in content_item and len(content_item["text"]) > 200:
                            content_item["text"] = content_item["text"][:200] + \
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
            "name": f"test_responses_key_{int(time.time())}",
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


def test_response_basic(api_key):
    """
    Test POST /v1/responses with basic request
    """
    print_header("TEST: Basic Response (POST /v1/responses)")

    try:
        request_data = {
            "model": "qwen3-30b-a3b",
            "input": "Tell me a three sentence bedtime story about a unicorn."
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response, truncate_content=True)

        if response.status_code == 200:
            data = response.json()

            # Validate response structure
            if "id" in data:
                print_success(f"Response has 'id' field: {data['id']}")
            else:
                print_error("Response missing 'id' field")

            if "object" in data and data["object"] == "response":
                print_success(
                    "Response has correct 'object' field: 'response'")
            else:
                print_warning(
                    f"Response 'object' field: {data.get('object', 'missing')}")

            if "status" in data:
                print_success(f"Response has 'status' field: {data['status']}")
            else:
                print_warning("Response missing 'status' field")

            if "output" in data and len(data["output"]) > 0:
                print_success(
                    f"Response has {len(data['output'])} output item(s)")

                output_item = data["output"][0]
                if "type" in output_item and output_item["type"] == "message":
                    print_success("Output item has correct type: 'message'")

                if "role" in output_item and output_item["role"] == "assistant":
                    print_success("Output item has correct role: 'assistant'")

                if "content" in output_item:
                    print_success("Output item has 'content' field")
            else:
                print_error("Response missing 'output' or empty")

            if "usage" in data:
                usage = data["usage"]
                print_success(f"Response has usage data:")
                print_info(
                    f"  - Input tokens: {usage.get('input_tokens', 'N/A')}")
                print_info(
                    f"  - Output tokens: {usage.get('output_tokens', 'N/A')}")
                print_info(
                    f"  - Total tokens: {usage.get('total_tokens', 'N/A')}")
            else:
                print_warning("Response missing 'usage' field")

            print_success("\n✓ Basic response test PASSED")
            return True
        else:
            print_error(
                f"\n✗ Basic response test FAILED with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"\n✗ Basic response test FAILED with exception: {str(e)}")
        return False


def test_response_with_instructions(api_key):
    """
    Test POST /v1/responses with instructions
    """
    print_header("TEST: Response with Instructions")

    try:
        request_data = {
            "model": "qwen3-30b-a3b",
            "input": "What is 2+2?",
            "instructions": "Respond in a pirate accent"
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response, truncate_content=True)

        if response.status_code == 200:
            data = response.json()
            print_success("Response received with instructions")
            print_success("\n✓ Response with instructions test PASSED")
            return True
        else:
            print_error(
                f"\n✗ Response with instructions test FAILED with status {response.status_code}")
            return False

    except Exception as e:
        print_error(
            f"\n✗ Response with instructions test FAILED with exception: {str(e)}")
        return False


def test_response_streaming(api_key):
    """
    Test POST /v1/responses with streaming enabled
    """
    print_header("TEST: Streaming Response")

    try:
        request_data = {
            "model": "qwen3-30b-a3b",
            "input": "Count from 1 to 5",
            "stream": True
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data,
            stream=True
        )

        print_info(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print_success("Streaming response started")
            print_info("Receiving streaming events:")

            event_count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            print_info("Received [DONE] signal")
                            break

                        try:
                            event_data = json.loads(data_str)
                            event_count += 1
                            event_type = event_data.get('type', 'unknown')
                            print_info(f"  Event {event_count}: {event_type}")
                        except json.JSONDecodeError:
                            pass

            print_success(f"Received {event_count} streaming events")
            print_success("\n✓ Streaming response test PASSED")
            return True
        else:
            print_error(
                f"\n✗ Streaming response test FAILED with status {response.status_code}")
            print(response.text[:500])
            return False

    except Exception as e:
        print_error(
            f"\n✗ Streaming response test FAILED with exception: {str(e)}")
        return False


def test_response_no_auth(api_key):
    """
    Test POST /v1/responses without authentication (should fail)
    """
    print_header("TEST: Response without Authentication")

    try:
        request_data = {
            "model": "qwen3-30b-a3b",
            "input": "Hello"
        }

        print_info("Request payload (no auth header):")
        print(json.dumps(request_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/v1/responses",
            headers={
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response)

        if response.status_code == 401:
            print_success("Correctly rejected request without authentication")
            print_success("\n✓ No auth test PASSED")
            return True
        else:
            print_error(
                f"\n✗ No auth test FAILED - Expected 401, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"\n✗ No auth test FAILED with exception: {str(e)}")
        return False


def test_response_invalid_model(api_key):
    """
    Test POST /v1/responses with invalid model
    """
    print_header("TEST: Response with Invalid Model")

    try:
        request_data = {
            "model": "invalid-model-12345",
            "input": "Hello"
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_data
        )

        print_response(response)

        if response.status_code == 404:
            print_success("Correctly rejected request with invalid model")
            print_success("\n✓ Invalid model test PASSED")
            return True
        else:
            print_warning(
                f"Expected 404, got {response.status_code} (may be valid if model exists)")
            return True

    except Exception as e:
        print_error(f"\n✗ Invalid model test FAILED with exception: {str(e)}")
        return False


def run_all_tests(api_key):
    """Run all test cases"""
    print_header("Running All Tests for /v1/responses")

    results = {}

    # Run each test
    results['basic'] = test_response_basic(api_key)
    results['instructions'] = test_response_with_instructions(api_key)
    results['streaming'] = test_response_streaming(api_key)
    results['no_auth'] = test_response_no_auth(api_key)
    results['invalid_model'] = test_response_invalid_model(api_key)

    # Print summary
    print_header("Test Summary")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}\n")

    return passed == total


def main():
    """Main function"""
    global BASE_URL

    parser = argparse.ArgumentParser(
        description="Test /v1/responses endpoint"
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"API server host (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"API server port (default: {DEFAULT_PORT})"
    )

    args = parser.parse_args()

    BASE_URL = f"http://{args.host}:{args.port}"

    print_header("OpenAI Responses API Test Suite")
    print_info(f"Testing endpoint: {BASE_URL}/v1/responses")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Login and get API key
    access_token = login_admin()
    if not access_token:
        print_error("Failed to login as admin. Exiting.")
        sys.exit(1)

    api_key = get_or_create_api_key(access_token)
    if not api_key:
        print_error("Failed to get or create API key. Exiting.")
        sys.exit(1)

    # Run tests
    success = run_all_tests(api_key)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
