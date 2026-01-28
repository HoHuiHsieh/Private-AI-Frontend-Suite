#!/usr/bin/env python3
"""
Models Endpoint Test Script
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


def print_response(response):
    """Pretty print response"""
    print(f"{Colors.OKBLUE}Status Code: {response.status_code}{Colors.ENDC}")
    try:
        print(f"{Colors.OKBLUE}Response:{Colors.ENDC}")
        print(json.dumps(response.json(), indent=2))
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
            "name": f"test_models_key_{int(time.time())}",
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


def test_list_models(api_key):
    """
    Test GET /v1/models endpoint
    This is the OpenAI-compatible models listing endpoint
    """
    print_header("TEST: List Available Models (GET /v1/models)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure (OpenAI-compatible)
            if "object" in data and data["object"] == "list":
                print_success("Response has correct 'object' field: 'list'")
            else:
                print_warning("Response missing or incorrect 'object' field")
            
            if "data" in data:
                models = data["data"]
                print_success(f"Found {len(models)} models")
                
                # Validate each model object
                for idx, model in enumerate(models):
                    print_info(f"\nModel {idx + 1}:")
                    
                    # Check required fields
                    if "id" in model:
                        print_success(f"  - ID: {model['id']}")
                    else:
                        print_error("  - Missing 'id' field")
                    
                    if "object" in model and model["object"] == "model":
                        print_success(f"  - Object: {model['object']}")
                    else:
                        print_warning(f"  - Object field: {model.get('object', 'missing')}")
                    
                    if "created" in model:
                        timestamp = model["created"]
                        created_time = datetime.fromtimestamp(timestamp)
                        print_success(f"  - Created: {created_time}")
                    else:
                        print_warning("  - Missing 'created' field")
                    
                    if "owned_by" in model:
                        print_success(f"  - Owned by: {model['owned_by']}")
                    else:
                        print_warning("  - Missing 'owned_by' field")
                    
                    # Optional fields
                    if "description" in model:
                        print_info(f"  - Description: {model['description']}")
                    
                    if "context_window" in model:
                        print_info(f"  - Context window: {model['context_window']}")
                    
                    if "max_output_tokens" in model:
                        print_info(f"  - Max output tokens: {model['max_output_tokens']}")
                
                print_success("\n✓ List models test PASSED")
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


def test_list_models_without_auth():
    """
    Test GET /v1/models endpoint without authentication
    Should return 401 or 403
    """
    print_header("TEST: List Models Without Authentication (Should Fail)")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/models")
        
        print_response(response)
        
        if response.status_code in [401, 403]:
            print_success(f"✓ Correctly rejected with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected 401/403, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_list_models_with_invalid_key():
    """
    Test GET /v1/models endpoint with invalid API key
    Should return 401 or 403
    """
    print_header("TEST: List Models With Invalid API Key (Should Fail)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/v1/models",
            headers={"Authorization": "Bearer invalid_api_key_12345"}
        )
        
        print_response(response)
        
        if response.status_code in [401, 403]:
            print_success(f"✓ Correctly rejected with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected 401/403, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def run_all_tests():
    """Run all test cases"""
    print_header("OpenAI-Compatible Models Endpoint Test Suite")
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
        ("List models with valid API key", lambda: test_list_models(api_key)),
        ("List models without authentication", test_list_models_without_auth),
        ("List models with invalid API key", test_list_models_with_invalid_key),
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
    
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    return results


def main():
    """Main function"""
    global BASE_URL
    
    parser = argparse.ArgumentParser(description="Test /v1/models endpoint")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Server host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})")
    
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
