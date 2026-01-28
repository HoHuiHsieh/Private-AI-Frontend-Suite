#!/usr/bin/env python3
"""
API Key Endpoints Test Script

This script tests all API key management endpoints.
It sends HTTP requests to the running API server.

Usage:
    python test_apikey_endpoints.py [--host HOST] [--port PORT]

Requirements:
    - Server must be running
    - requests library (pip install requests)
    - Admin user must exist (created automatically on server startup)
"""

import requests
import json
import sys
import argparse
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 3000
BASE_URL = None

# Load environment variables from .env.dev if available
env_file = Path(__file__).parent.parent.parent / ".env.dev"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Test data
TEST_USER = {
    "username": os.getenv("DEFAULT_ADMIN_EMAIL", "admin"),
    "password": os.getenv("DEFAULT_ADMIN_PASSWORD", "secret")
}

# Store tokens and created API keys
access_token = None
created_api_keys = []


def print_test(test_name):
    """Print test header."""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")


def print_result(response, expected_status=None):
    """Print response details."""
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")
    
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")
    
    if expected_status:
        if response.status_code == expected_status:
            print(f"✓ PASS - Expected status {expected_status}")
            return True
        else:
            print(f"✗ FAIL - Expected {expected_status}, got {response.status_code}")
            return False
    return True


def get_auth_headers():
    """Get authorization headers with access token."""
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {}


# ============================================================================
# Test 0: Login to get access token
# ============================================================================

def test_login():
    """Login to get access token for subsequent tests."""
    global access_token
    
    print_test("POST /api/login - Login to get access token")
    
    url = f"{BASE_URL}/api/login"
    data = TEST_USER
    
    response = requests.post(url, data=data)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        result = response.json()
        access_token = result.get("access_token")
        print(f"✓ Login successful")
        print(f"  Access Token: {access_token[:20]}...")
        return True
    else:
        print(f"✗ Login failed - cannot proceed with tests")
        return False


# ============================================================================
# Test 1: GET /api/apikeys - List API keys (empty)
# ============================================================================

def test_list_api_keys_empty():
    """Test listing API keys when none exist."""
    print_test("GET /api/apikeys - List API keys (should be empty or show existing)")
    
    url = f"{BASE_URL}/api/apikeys"
    headers = get_auth_headers()
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        keys = response.json()
        print(f"✓ Retrieved {len(keys)} API keys")
        return True
    return False


# ============================================================================
# Test 2: POST /api/apikeys - Create API key (without name or expiry)
# ============================================================================

def test_create_api_key_basic():
    """Test creating a basic API key with required fields."""
    global created_api_keys
    
    print_test("POST /api/apikeys - Create API key (basic with required fields)")
    
    url = f"{BASE_URL}/api/apikeys"
    headers = {**get_auth_headers(), "Content-Type": "application/json"}
    data = {
        "name": "Basic Test Key",
        "days": 30
    }
    
    response = requests.post(url, json=data, headers=headers)
    success = print_result(response, expected_status=201)
    
    if success and response.status_code == 201:
        key_data = response.json()
        created_api_keys.append(key_data)
        print(f"✓ API key created successfully")
        print(f"  Key ID: {key_data.get('id')}")
        print(f"  Name: {key_data.get('name')}")
        print(f"  API Key: {key_data.get('api_key')}")
        print(f"  ⚠ IMPORTANT: Save this key - you won't see it again!")
        return True
    return False


# ============================================================================
# Test 3: POST /api/apikeys - Create API key with name
# ============================================================================

def test_create_api_key_with_name():
    """Test creating an API key with a different name."""
    global created_api_keys
    
    print_test("POST /api/apikeys - Create API key with different name")
    
    url = f"{BASE_URL}/api/apikeys"
    headers = {**get_auth_headers(), "Content-Type": "application/json"}
    data = {
        "name": "Test Key with Custom Name",
        "days": 60
    }
    
    response = requests.post(url, json=data, headers=headers)
    success = print_result(response, expected_status=201)
    
    if success and response.status_code == 201:
        key_data = response.json()
        created_api_keys.append(key_data)
        print(f"✓ API key created successfully")
        print(f"  Key ID: {key_data.get('id')}")
        print(f"  Name: {key_data.get('name')}")
        print(f"  API Key: {key_data.get('api_key')}")
        return True
    return False


# ============================================================================
# Test 4: POST /api/apikeys - Create API key with expiration
# ============================================================================

def test_create_api_key_with_expiry():
    """Test creating an API key with expiration date."""
    global created_api_keys
    
    print_test("POST /api/apikeys - Create API key with expiration (7 days)")
    
    url = f"{BASE_URL}/api/apikeys"
    headers = {**get_auth_headers(), "Content-Type": "application/json"}
    
    data = {
        "name": "Expiring Test Key",
        "days": 7
    }
    
    response = requests.post(url, json=data, headers=headers)
    success = print_result(response, expected_status=201)
    
    if success and response.status_code == 201:
        key_data = response.json()
        created_api_keys.append(key_data)
        print(f"✓ API key created successfully")
        print(f"  Key ID: {key_data.get('id')}")
        print(f"  Name: {key_data.get('name')}")
        print(f"  Expires At: {key_data.get('expires_at')}")
        return True
    return False


# ============================================================================
# Test 5: GET /api/apikeys - List API keys (with keys)
# ============================================================================

def test_list_api_keys_with_data():
    """Test listing API keys after creating some."""
    print_test("GET /api/apikeys - List API keys (should show created keys)")
    
    url = f"{BASE_URL}/api/apikeys"
    headers = get_auth_headers()
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        keys = response.json()
        print(f"✓ Retrieved {len(keys)} API keys")
        
        # Verify keys are masked
        for key in keys:
            api_key = key.get('api_key', '')
            if api_key.startswith('sk-') and '***' in api_key:
                print(f"  ✓ Key {key.get('id')} is properly masked: {api_key}")
            else:
                print(f"  ⚠ Key {key.get('id')} might not be masked properly: {api_key}")
        
        return True
    return False


# ============================================================================
# Test 6: POST /api/apikeys - Create API key with invalid days (should fail)
# ============================================================================

def test_create_api_key_missing_fields():
    """Test creating an API key without required fields (should fail)."""
    print_test("POST /api/apikeys - Create API key without required fields (should fail)")
    
    url = f"{BASE_URL}/api/apikeys"
    headers = {**get_auth_headers(), "Content-Type": "application/json"}
    
    # Missing both name and days
    data = {}
    
    response = requests.post(url, json=data, headers=headers)
    success = print_result(response, expected_status=422)
    
    if success and response.status_code == 422:
        print(f"✓ Correctly rejected missing required fields")
        return True
    return False


# ============================================================================
# Test 7: POST /api/apikeys - Create API key with invalid days (should fail)
# ============================================================================

def test_create_api_key_past_expiry():
    """Test creating an API key with invalid days value (should fail)."""
    print_test("POST /api/apikeys - Create API key with negative days (should fail)")
    
    url = f"{BASE_URL}/api/apikeys"
    headers = {**get_auth_headers(), "Content-Type": "application/json"}
    
    data = {
        "name": "Invalid Negative Days Key",
        "days": -1
    }
    
    response = requests.post(url, json=data, headers=headers)
    success = print_result(response, expected_status=422)
    
    if success and response.status_code == 422:
        print(f"✓ Correctly rejected negative days value")
        return True
    return False


# ============================================================================
# Test 7: POST /api/apikeys/{key_id}/revoke - Revoke API key
# ============================================================================

def test_revoke_api_key():
    """Test revoking an API key."""
    if not created_api_keys:
        print_test("POST /api/apikeys/{key_id}/revoke - Revoke API key")
        print("⚠ No API keys created, skipping test")
        return False
    
    key_to_revoke = created_api_keys[0]
    key_id = key_to_revoke.get('id')
    
    print_test(f"POST /api/apikeys/{{key_id}}/revoke - Revoke API key {key_id}")
    
    url = f"{BASE_URL}/api/apikeys/{key_id}/revoke"
    headers = get_auth_headers()
    
    response = requests.post(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        result = response.json()
        print(f"✓ API key revoked: {result.get('detail')}")
        return True
    return False


# ============================================================================
# Test 8: POST /api/apikeys/{key_id}/revoke - Revoke already revoked key (should fail)
# ============================================================================

def test_revoke_already_revoked_key():
    """Test revoking an already revoked API key (should fail)."""
    if not created_api_keys:
        print_test("POST /api/apikeys/{key_id}/revoke - Revoke already revoked key")
        print("⚠ No API keys created, skipping test")
        return False
    
    key_id = created_api_keys[0].get('id')
    
    print_test(f"POST /api/apikeys/{{key_id}}/revoke - Revoke already revoked key (should fail)")
    
    url = f"{BASE_URL}/api/apikeys/{key_id}/revoke"
    headers = get_auth_headers()
    
    response = requests.post(url, headers=headers)
    success = print_result(response, expected_status=400)
    
    if success and response.status_code == 400:
        print(f"✓ Correctly rejected revocation of already revoked key")
        return True
    return False


# ============================================================================
# Test 9: POST /api/apikeys/{key_id}/revoke - Revoke non-existent key (should fail)
# ============================================================================

def test_revoke_nonexistent_key():
    """Test revoking a non-existent API key (should fail)."""
    print_test("POST /api/apikeys/{key_id}/revoke - Revoke non-existent key (should fail)")
    
    url = f"{BASE_URL}/api/apikeys/999999/revoke"
    headers = get_auth_headers()
    
    response = requests.post(url, headers=headers)
    success = print_result(response, expected_status=404)
    
    if success and response.status_code == 404:
        print(f"✓ Correctly returned 404 for non-existent key")
        return True
    return False


# ============================================================================
# Main Test Runner
# ============================================================================

def run_tests():
    """Run all tests in sequence."""
    print("\n" + "="*80)
    print(f"API KEY ENDPOINTS TEST SUITE")
    print(f"Server: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = []
    
    # Authentication
    print("\n" + "─"*80)
    print("SECTION 0: Authentication")
    print("─"*80)
    
    login_success = test_login()
    results.append(("Login", login_success))
    
    if not login_success:
        print("\n✗ Cannot proceed without authentication")
        return False
    
    # API Key Tests
    print("\n" + "─"*80)
    print("SECTION 1: API Key Management")
    print("─"*80)
    
    results.append(("List API Keys (Initial)", test_list_api_keys_empty()))
    results.append(("Create API Key (Basic)", test_create_api_key_basic()))
    results.append(("Create API Key (With Name)", test_create_api_key_with_name()))
    results.append(("Create API Key (With Expiry - 7 days)", test_create_api_key_with_expiry()))
    results.append(("List API Keys (After Creation)", test_list_api_keys_with_data()))
    
    # Validation Tests
    print("\n" + "─"*80)
    print("SECTION 2: Validation Tests")
    print("─"*80)
    
    results.append(("Create API Key (Missing Fields - Should Fail)", test_create_api_key_missing_fields()))
    results.append(("Create API Key (Negative Days - Should Fail)", test_create_api_key_past_expiry()))
    
    # Revocation Tests
    print("\n" + "─"*80)
    print("SECTION 3: Revocation Tests")
    print("─"*80)
    
    results.append(("Revoke API Key", test_revoke_api_key()))
    results.append(("Revoke Already Revoked Key (Should Fail)", test_revoke_already_revoked_key()))
    results.append(("Revoke Non-existent Key (Should Fail)", test_revoke_nonexistent_key()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Cleanup info
    if created_api_keys:
        print("\n" + "─"*80)
        print("CLEANUP INFO")
        print("─"*80)
        print(f"Created {len(created_api_keys)} API key(s) during testing:")
        for key in created_api_keys:
            status = "REVOKED" if key == created_api_keys[0] else "ACTIVE"
            print(f"  - Key ID {key.get('id')}: {key.get('name', 'Unnamed')} ({status})")
        print("Note: You can manually revoke remaining keys through the API or database")
    
    print("="*80 + "\n")
    
    return passed == total


def main():
    """Main entry point."""
    global BASE_URL
    
    parser = argparse.ArgumentParser(description="Test API key endpoints")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"API host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"API port (default: {DEFAULT_PORT})")
    args = parser.parse_args()
    
    BASE_URL = f"http://{args.host}:{args.port}"
    
    try:
        # Check if server is running
        print(f"Checking server connectivity at {BASE_URL}...")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✓ Server is running (status: {response.status_code})\n")
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to server at {BASE_URL}")
        print(f"  Error: {e}")
        print(f"\nPlease ensure the server is running:")
        print(f"  cd /workspace/server/src")
        print(f"  python main.py")
        sys.exit(1)
    
    success = run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
