#!/usr/bin/env python3
"""
Chat Agent Endpoints Test Script

This script tests the /api/chatagent/* endpoints.
It sends HTTP requests to the running API server.

Usage:
    python test_chatagent_endpoints.py [--host HOST] [--port PORT]

Requirements:
    - Server must be running
    - requests library (pip install requests)
    - Valid admin credentials
"""

import argparse
import json
import os
import sys
import time
import requests
from datetime import datetime

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 3000
BASE_URL = None
DEFAULT_MODEL = "qwen3-30b-a3b"
DEFAULT_EMBED = "embeddinggemma-300m"


# Admin credentials
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
        if truncate_content and "data" in data and isinstance(data["data"], list):
            # Truncate long content for readability
            for item in data["data"]:
                if isinstance(item, dict) and "content" in item:
                    content = item["content"]
                    if isinstance(content, str) and len(content) > 100:
                        item["content"] = content[:100] + "..."
        print(f"{Colors.OKBLUE}Response:{Colors.ENDC}")
        print(json.dumps(data, indent=2))
    except:
        print(response.text[:500])


def login_admin():
    """Login as admin and return access token"""
    print_info("Logging in as admin...")

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
                if key_data.get("is_active"):
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
            "name": f"test_chatagent_key_{int(time.time())}",
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


def test_get_chatagent_models(access_token):
    """
    Test GET /api/chatagent/models
    """
    print_header("TEST: Get Chat Agent Models (GET /api/chatagent/models)")

    try:
        response = requests.get(
            f"{BASE_URL}/api/chatagent/models",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()

            # Validate response structure
            if data.get("object") == "object" and "data" in data:
                print_success("Response structure is valid")

                # Check if data contains expected fields
                model_data = data.get("data", {})
                if "chat" in model_data and "embedding" in model_data and "collections" in model_data:
                    print_success(
                        "Model data contains chat, embedding, and collections")
                    print_info(f"Chat models: {model_data.get('chat')}")
                    print_info(
                        f"Embedding models: {model_data.get('embedding')}")
                    print_info(f"Collections: {model_data.get('collections')}")
                else:
                    print_warning("Model data missing expected fields")

                return True
            else:
                print_error("Invalid response structure")
                return False

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_get_chatagent_sessions(access_token):
    """
    Test GET /api/chatagent/sessions
    """
    print_header("TEST: Get Chat Agent Sessions (GET /api/chatagent/sessions)")

    try:
        response = requests.get(
            f"{BASE_URL}/api/chatagent/sessions",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()

            # Validate response structure
            if data.get("object") == "list" and "data" in data:
                print_success("Response structure is valid")
                sessions = data.get("data", [])
                print_info(f"Found {len(sessions)} sessions")

                # Validate session data structure
                if sessions:
                    session = sessions[0]
                    if "user_id" in session and "session_id" in session and "title" in session:
                        print_success("Session data structure is valid")
                    else:
                        print_warning("Session data missing expected fields")

                return True
            else:
                print_error("Invalid response structure")
                return False

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_chat_agent_stream(access_token, api_key):
    """
    Test POST /api/chatagent/chat/{session_id} - Streaming response
    """
    print_header(
        "TEST: Chat Agent Stream (POST /api/chatagent/chat/{session_id})")

    try:
        # Use a test session ID
        session_id = f"test_session_1768873092"

        request_data = {
            "model": DEFAULT_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": "** Say hello in one sentence **",
                    "additional_kwargs": {
                        "id": "msg1",
                        "reasoning": None,
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }
                }
            ],
            "max_completion_tokens": 100,
            "temperature": 0.7,
            "stream": True,
            "additional_kwargs": {
                "embedding_model": DEFAULT_EMBED,
                "collections": []
            }
        }

        print_info("Request payload:")
        print(json.dumps(request_data, indent=2))
        print_info(f"Session ID: {session_id}")

        response = requests.post(
            f"{BASE_URL}/api/chatagent/chat/{session_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=request_data,
            stream=True
        )

        print(f"{Colors.OKBLUE}Status Code: {response.status_code}{Colors.ENDC}")

        if response.status_code == 200:
            print_success("Chat agent stream started")
            print_info("Streaming response:")

            full_content = ""
            chunk_count = 0

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        chunk_count += 1
                        data_str = line_str[6:]  # Remove 'data: ' prefix

                        if data_str == '[DONE]':
                            print_info("\n[Stream completed]")
                            break

                        try:
                            chunk_data = json.loads(data_str)
                            if "choices" in chunk_data and chunk_data["choices"]:
                                delta = chunk_data["choices"][0].get(
                                    "delta", {})
                                if "content" in delta:
                                    content = delta["content"]
                                    full_content += content
                                    print(content, end='', flush=True)
                        except json.JSONDecodeError:
                            pass

            print()  # New line after streaming
            print_info(f"Received {chunk_count} chunks")
            print_info(f"Total content length: {len(full_content)} characters")

            if chunk_count > 0:
                print_success("Streaming response received successfully")
                return True, session_id
            else:
                print_error("No chunks received")
                return False, None

        print_error(f"Failed with status code: {response.status_code}")
        print_response(response)
        return False, None

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False, None


def test_get_chat_history(access_token, session_id):
    """
    Test GET /api/chatagent/chat/{session_id}
    """
    print_header(
        "TEST: Get Chat History (GET /api/chatagent/chat/{session_id})")

    try:
        print_info(f"Fetching history for session: {session_id}")

        response = requests.get(
            f"{BASE_URL}/api/chatagent/chat/{session_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print_response(response, truncate_content=True)

        if response.status_code == 200:
            data = response.json()

            # Validate response structure
            if data.get("object") == "list" and "data" in data:
                print_success("Response structure is valid")
                messages = data.get("data", [])
                print_info(f"Found {len(messages)} messages")

                # Validate message structure
                if messages:
                    message = messages[0]
                    if "role" in message and "content" in message:
                        print_success("Message structure is valid")
                        return True, messages
                    else:
                        print_warning("Message missing expected fields")
                else:
                    print_warning("No messages in history yet")

                return True, messages
            else:
                print_error("Invalid response structure")
                return False, []

        print_error(f"Failed with status code: {response.status_code}")
        return False, []

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False, []


def test_get_chat_message(access_token, session_id, message_id):
    """
    Test GET /api/chatagent/message/{message_id}/chat/{session_id}
    """
    print_header(
        "TEST: Get Chat Message (GET /api/chatagent/message/{message_id}/chat/{session_id})")

    try:
        print_info(f"Fetching message {message_id} from session {session_id}")

        response = requests.get(
            f"{BASE_URL}/api/chatagent/message/{message_id}/chat/{session_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print_response(response, truncate_content=True)

        if response.status_code == 200:
            data = response.json()

            # Validate message structure
            if "role" in data and "content" in data:
                print_success("Message retrieved successfully")
                return True
            else:
                print_warning("Message missing expected fields")
                return False

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_update_chat_message(access_token, session_id, message_id):
    """
    Test POST /api/chatagent/message/{message_id}/chat/{session_id}
    """
    print_header(
        "TEST: Update Chat Message (POST /api/chatagent/message/{message_id}/chat/{session_id})")

    try:
        print_info(f"Updating message {message_id} in session {session_id}")

        update_data = {
            "role": "user",
            "content": "Updated message content"
        }

        print_info("Update payload:")
        print(json.dumps(update_data, indent=2))

        response = requests.post(
            f"{BASE_URL}/api/chatagent/message/{message_id}/chat/{session_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=update_data
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if "detail" in data:
                print_success(f"Message updated: {data['detail']}")
                return True
            else:
                print_error("Unexpected response format")
                return False

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_delete_chat_message(access_token, session_id, message_id):
    """
    Test DELETE /api/chatagent/message/{message_id}/chat/{session_id}
    """
    print_header(
        "TEST: Delete Chat Message (DELETE /api/chatagent/message/{message_id}/chat/{session_id})")

    try:
        print_info(f"Deleting message {message_id} from session {session_id}")

        response = requests.delete(
            f"{BASE_URL}/api/chatagent/message/{message_id}/chat/{session_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if "detail" in data:
                print_success(f"Message deleted: {data['detail']}")
                return True
            else:
                print_error("Unexpected response format")
                return False

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_delete_chat_session(access_token, session_id):
    """
    Test DELETE /api/chatagent/chat/{session_id}
    """
    print_header(
        "TEST: Delete Chat Session (DELETE /api/chatagent/chat/{session_id})")

    try:
        print_info(f"Deleting session: {session_id}")

        response = requests.delete(
            f"{BASE_URL}/api/chatagent/chat/{session_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if "detail" in data:
                print_success(f"Session deleted: {data['detail']}")
                return True
            else:
                print_error("Unexpected response format")
                return False

        print_error(f"Failed with status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_chatagent_without_auth():
    """
    Test chat agent endpoints without authentication (should fail)
    """
    print_header("TEST: Chat Agent Without Authentication (Should Fail)")

    try:
        response = requests.get(f"{BASE_URL}/api/chatagent/models")
        print_response(response)

        if response.status_code in [401, 403]:
            print_success("Correctly rejected request without authentication")
            return True
        else:
            print_error(f"Expected 401/403, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_chat_agent_invalid_session():
    """
    Test GET chat history with invalid session ID
    """
    print_header(
        "TEST: Get Chat History with Invalid Session (Should Handle Gracefully)")

    try:
        # Login to get access token
        access_token = login_admin()
        if not access_token:
            return False

        invalid_session_id = "nonexistent_session_12345"

        response = requests.get(
            f"{BASE_URL}/api/chatagent/chat/{invalid_session_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print_response(response)

        # Server might return 200 with empty data or 404, both are acceptable
        if response.status_code in [200, 404]:
            if response.status_code == 200:
                data = response.json()
                if data.get("object") == "list" and len(data.get("data", [])) == 0:
                    print_success("Returned empty list for invalid session")
                    return True
            else:
                print_success("Returned 404 for invalid session")
                return True

        print_error(f"Unexpected status code: {response.status_code}")
        return False

    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def run_all_tests():
    """Run all test cases"""
    print_header("Chat Agent Endpoints Test Suite")
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

    # Store session_id and message_id for subsequent tests
    test_session_id = None
    test_message_id = None

    # Run tests
    tests = [
        ("Get chat agent models", lambda: test_get_chatagent_models(access_token)),
        ("Get chat agent sessions", lambda: test_get_chatagent_sessions(access_token)),
        ("Chat agent without auth", test_chatagent_without_auth),
        ("Get chat history with invalid session", test_chat_agent_invalid_session),
    ]

    # Run initial tests
    for test_name, test_func in tests:
        results["total"] += 1
        try:
            if test_func():
                results["passed"] += 1
                print_success(f"{test_name} - PASSED")
            else:
                results["failed"] += 1
                print_error(f"{test_name} - FAILED")
        except Exception as e:
            results["failed"] += 1
            print_error(f"{test_name} - EXCEPTION: {str(e)}")

        time.sleep(0.5)  # Small delay between tests

    # Test chat agent stream and get session ID
    results["total"] += 1
    try:
        success, test_session_id = test_chat_agent_stream(
            access_token, api_key)
        if success and test_session_id:
            results["passed"] += 1
            print_success("Chat agent stream - PASSED")
        else:
            results["failed"] += 1
            print_error("Chat agent stream - FAILED")
    except Exception as e:
        results["failed"] += 1
        print_error(f"Chat agent stream - EXCEPTION: {str(e)}")

    time.sleep(1)  # Wait for message to be saved

    # If we have a session, test history and message operations
    if test_session_id:
        # Test get chat history
        results["total"] += 1
        try:
            success, messages = test_get_chat_history(
                access_token, test_session_id)
            if success and messages:
                results["passed"] += 1
                print_success("Get chat history - PASSED")

                # Extract message ID from history
                if messages and "additional_kwargs" in messages[0]:
                    test_message_id = messages[0]["additional_kwargs"].get(
                        "id")
                    print_info(f"Found message ID: {test_message_id}")
            else:
                results["failed"] += 1
                print_error("Get chat history - FAILED")
        except Exception as e:
            results["failed"] += 1
            print_error(f"Get chat history - EXCEPTION: {str(e)}")

        time.sleep(0.5)

        # If we have a message ID, test message operations
        if test_message_id:
            message_tests = [
                ("Get chat message", lambda: test_get_chat_message(
                    access_token, test_session_id, test_message_id)),
                ("Update chat message", lambda: test_update_chat_message(
                    access_token, test_session_id, test_message_id)),
                ("Delete chat message", lambda: test_delete_chat_message(
                    access_token, test_session_id, test_message_id)),
            ]

            for test_name, test_func in message_tests:
                results["total"] += 1
                try:
                    if test_func():
                        results["passed"] += 1
                        print_success(f"{test_name} - PASSED")
                    else:
                        results["failed"] += 1
                        print_error(f"{test_name} - FAILED")
                except Exception as e:
                    results["failed"] += 1
                    print_error(f"{test_name} - EXCEPTION: {str(e)}")

                time.sleep(0.5)

        # Finally, delete the session
        results["total"] += 1
        try:
            if test_delete_chat_session(access_token, test_session_id):
                results["passed"] += 1
                print_success("Delete chat session - PASSED")
            else:
                results["failed"] += 1
                print_error("Delete chat session - FAILED")
        except Exception as e:
            results["failed"] += 1
            print_error(f"Delete chat session - EXCEPTION: {str(e)}")

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
        description="Test /api/chatagent/* endpoints")
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
