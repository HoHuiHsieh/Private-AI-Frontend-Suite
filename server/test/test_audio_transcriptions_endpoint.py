#!/usr/bin/env python3
"""
Audio Transcriptions Endpoint Test Script
Tests OpenAI-compatible /v1/audio/transcriptions endpoint
"""
import os
import requests
import json
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 3000
BASE_URL = None

# Admin credentials for obtaining API key
ADMIN_CREDENTIALS = {
    "username": os.getenv("DEFAULT_ADMIN_EMAIL"),
    "password": os.getenv("DEFAULT_ADMIN_PASSWORD"),
}

# Test model and audio file
# TEST_MODEL = "gpt-4o-transcribe"
TEST_MODEL = "whisper-tiny"
TEST_AUDIO_FILE = Path(__file__).parent / "harvard.wav"

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


def print_response(response, truncate_text=True):
    """Pretty print response (truncate long text for readability)"""
    print(f"{Colors.OKBLUE}Status Code: {response.status_code}{Colors.ENDC}")
    try:
        data = response.json()
        # Truncate long text for readability
        if truncate_text and 'text' in data:
            text = data['text']
            if len(text) > 200:
                data['text'] = f"{text[:200]}... (truncated, total length: {len(text)})"
        print(f"{Colors.OKBLUE}Response:{Colors.ENDC}")
        print(json.dumps(data, indent=2))
    except:
        response_text = response.text
        if truncate_text and len(response_text) > 300:
            print(f"{response_text[:300]}... (truncated)")
        else:
            print(response_text)


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
        print_response(response, truncate_text=False)
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
            "name": f"test_audio_key_{int(time.time())}",
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
        print_response(response, truncate_text=False)
        return None


def test_transcription_basic(api_key, model):
    """
    Test POST /v1/audio/transcriptions with basic parameters
    """
    print_header(f"TEST: Basic Audio Transcription - Model: {model}")
    
    if not TEST_AUDIO_FILE.exists():
        print_warning(f"Audio file not found: {TEST_AUDIO_FILE}")
        print_info("Skipping test - audio file required")
        return True  # Don't fail if file doesn't exist
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as audio_file:
            files = {
                'file': (TEST_AUDIO_FILE.name, audio_file, 'audio/mpeg')
            }
            data = {
                'model': model
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data
            )
        
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            
            # Validate response structure
            if "text" in result:
                text = result["text"]
                print_success(f"Transcribed text received (length: {len(text)})")
                print_info(f"Text preview: {text[:100]}...")
            else:
                print_error("Response missing 'text' field")
                return False
            
            # Check for usage information
            if "usage" in result:
                usage = result["usage"]
                print_success(f"Usage information:")
                if usage and "total_tokens" in usage:
                    print_info(f"  - Total tokens: {usage['total_tokens']}")
                if usage and "seconds" in usage:
                    print_info(f"  - Audio duration: {usage['seconds']}s")
            else:
                print_info("No usage information in response")
            
            print_success("\n✓ Basic transcription test PASSED")
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        import traceback
        print_error(traceback.format_exc())
        return False


def test_transcription_with_language(api_key, model):
    """
    Test POST /v1/audio/transcriptions with language parameter
    """
    print_header(f"TEST: Transcription with Language - Model: {model}")
    
    if not TEST_AUDIO_FILE.exists():
        print_warning(f"Audio file not found: {TEST_AUDIO_FILE}")
        return True
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as audio_file:
            files = {
                'file': (TEST_AUDIO_FILE.name, audio_file, 'audio/mpeg')
            }
            data = {
                'model': model,
                'language': 'en'  # English
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data
            )
        
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            if "text" in result:
                print_success(f"Transcription with language succeeded")
                print_info(f"Language specified: en")
                print_success("\n✓ Transcription with language test PASSED")
                return True
            else:
                print_error("Response missing 'text' field")
                return False
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_transcription_with_prompt(api_key, model):
    """
    Test POST /v1/audio/transcriptions with prompt parameter
    """
    print_header(f"TEST: Transcription with Prompt - Model: {model}")
    
    if not TEST_AUDIO_FILE.exists():
        print_warning(f"Audio file not found: {TEST_AUDIO_FILE}")
        return True
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as audio_file:
            files = {
                'file': (TEST_AUDIO_FILE.name, audio_file, 'audio/mpeg')
            }
            data = {
                'model': model,
                'prompt': 'This is a test audio file for transcription.'
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data
            )
        
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            if "text" in result:
                print_success(f"Transcription with prompt succeeded")
                print_success("\n✓ Transcription with prompt test PASSED")
                return True
            else:
                print_error("Response missing 'text' field")
                return False
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_transcription_with_temperature(api_key, model):
    """
    Test POST /v1/audio/transcriptions with temperature parameter
    """
    print_header(f"TEST: Transcription with Temperature - Model: {model}")
    
    if not TEST_AUDIO_FILE.exists():
        print_warning(f"Audio file not found: {TEST_AUDIO_FILE}")
        return True
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as audio_file:
            files = {
                'file': (TEST_AUDIO_FILE.name, audio_file, 'audio/mpeg')
            }
            data = {
                'model': model,
                'temperature': '0.0'  # Most deterministic
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data
            )
        
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            if "text" in result:
                print_success(f"Transcription with temperature succeeded")
                print_info(f"Temperature: 0.0")
                print_success("\n✓ Transcription with temperature test PASSED")
                return True
            else:
                print_error("Response missing 'text' field")
                return False
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_transcription_json_format(api_key, model):
    """
    Test POST /v1/audio/transcriptions with JSON response format (default)
    """
    print_header(f"TEST: JSON Response Format - Model: {model}")
    
    if not TEST_AUDIO_FILE.exists():
        print_warning(f"Audio file not found: {TEST_AUDIO_FILE}")
        return True
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as audio_file:
            files = {
                'file': (TEST_AUDIO_FILE.name, audio_file, 'audio/mpeg')
            }
            data = {
                'model': model,
                'response_format': 'json'
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data
            )
        
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            if "text" in result:
                print_success(f"JSON format response received")
                print_success("\n✓ JSON format test PASSED")
                return True
            else:
                print_error("Response missing 'text' field")
                return False
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_transcription_without_auth(model):
    """
    Test POST /v1/audio/transcriptions without authentication
    Should return 401 or 403
    """
    print_header(f"TEST: Without Authentication - Model: {model}")
    
    if not TEST_AUDIO_FILE.exists():
        print_warning(f"Audio file not found: {TEST_AUDIO_FILE}")
        return True
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as audio_file:
            files = {
                'file': (TEST_AUDIO_FILE.name, audio_file, 'audio/mpeg')
            }
            data = {
                'model': model
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                files=files,
                data=data
            )
        
        print_response(response, truncate_text=False)
        
        if response.status_code in [401, 403]:
            print_success(f"✓ Correctly rejected with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected 401/403, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_transcription_invalid_model(api_key):
    """
    Test POST /v1/audio/transcriptions with invalid model
    Should return error
    """
    print_header("TEST: Invalid Model")
    
    if not TEST_AUDIO_FILE.exists():
        print_warning(f"Audio file not found: {TEST_AUDIO_FILE}")
        return True
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as audio_file:
            files = {
                'file': (TEST_AUDIO_FILE.name, audio_file, 'audio/mpeg')
            }
            data = {
                'model': 'invalid-model-name-12345'
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data
            )
        
        print_response(response, truncate_text=False)
        
        if response.status_code in [400, 404, 500]:
            print_success(f"✓ Correctly rejected with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected error status, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_transcription_missing_file(api_key, model):
    """
    Test POST /v1/audio/transcriptions with missing file
    Should return 422 validation error
    """
    print_header(f"TEST: Missing File - Model: {model}")
    
    try:
        data = {
            'model': model
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            data=data
        )
        
        print_response(response, truncate_text=False)
        
        if response.status_code == 422:
            print_success(f"✓ Correctly rejected with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def test_transcription_missing_model(api_key):
    """
    Test POST /v1/audio/transcriptions with missing model
    Should return 422 validation error
    """
    print_header("TEST: Missing Model Parameter")
    
    if not TEST_AUDIO_FILE.exists():
        print_warning(f"Audio file not found: {TEST_AUDIO_FILE}")
        return True
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as audio_file:
            files = {
                'file': (TEST_AUDIO_FILE.name, audio_file, 'audio/mpeg')
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files
            )
        
        print_response(response, truncate_text=False)
        
        if response.status_code == 422:
            print_success(f"✓ Correctly rejected with status {response.status_code}")
            return True
        else:
            print_warning(f"⚠ Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False


def run_all_tests():
    """Run all test cases"""
    print_header("OpenAI-Compatible Audio Transcriptions Endpoint Test Suite")
    print_info(f"Testing server at: {BASE_URL}")
    print_info(f"Test audio file: {TEST_AUDIO_FILE}")
    print_info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check if audio file exists
    if not TEST_AUDIO_FILE.exists():
        print_warning(f"Audio file not found: {TEST_AUDIO_FILE}")
        print_warning("Some tests will be skipped")
    
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
        # Basic Tests
        (f"Basic transcription - {TEST_MODEL}", lambda: test_transcription_basic(api_key, TEST_MODEL)),
        (f"With language parameter - {TEST_MODEL}", lambda: test_transcription_with_language(api_key, TEST_MODEL)),
        (f"With prompt parameter - {TEST_MODEL}", lambda: test_transcription_with_prompt(api_key, TEST_MODEL)),
        (f"With temperature parameter - {TEST_MODEL}", lambda: test_transcription_with_temperature(api_key, TEST_MODEL)),
        
        # Response Format Tests
        (f"JSON format - {TEST_MODEL}", lambda: test_transcription_json_format(api_key, TEST_MODEL)),
        
        # Error Cases
        (f"No auth - {TEST_MODEL}", lambda: test_transcription_without_auth(TEST_MODEL)),
        ("Invalid model", lambda: test_transcription_invalid_model(api_key)),
        (f"Missing file - {TEST_MODEL}", lambda: test_transcription_missing_file(api_key, TEST_MODEL)),
        ("Missing model parameter", lambda: test_transcription_missing_model(api_key)),
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
    
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    return results


def main():
    """Main function"""
    global BASE_URL
    
    parser = argparse.ArgumentParser(description="Test /v1/audio/transcriptions endpoint")
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
