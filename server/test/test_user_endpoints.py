#!/usr/bin/env python3
"""
User Endpoints Test Script

This script tests all user authentication and management endpoints.
It sends HTTP requests to the running API server.

Usage:
    python test_user_endpoints.py [--host HOST] [--port PORT]

Requirements:
    - Server must be running
    - requests library (pip install requests)
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

# Test data - use timestamp to ensure unique usernames
TIMESTAMP = int(time.time())

TEST_ADMIN = {
    "username": os.getenv("DEFAULT_ADMIN_EMAIL"),
    "password": os.getenv("DEFAULT_ADMIN_PASSWORD"),
}

TEST_USER_REGISTER = {
    "username": f"testuser{TIMESTAMP}",
    "email": f"testuser{TIMESTAMP}@example.com",
    "fullname": "Test User",
    "password": "testpass123"
}

TEST_USER_CREATE = {
    "username": f"createduser{TIMESTAMP}",
    "email": f"created{TIMESTAMP}@example.com",
    "fullname": "Created User",
    "password": "created123",
    "active": True,
    "scopes": ["user"]
}

TEST_USER_UPDATE = {
    "fullname": "Updated Name",
    "active": False
}

# Store tokens for authenticated requests
access_token = None
refresh_token = None


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
# Test 1: POST /api/register
# ============================================================================

def test_register():
    """Test user registration."""
    print_test("POST /api/register - Register new user")
    
    url = f"{BASE_URL}/api/register"
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=TEST_USER_REGISTER, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ User registered: {data.get('username')}")
        return True
    return False


# ============================================================================
# Test 2: POST /api/login
# ============================================================================

def test_login():
    """Test user login with registered user."""
    global access_token, refresh_token
    
    print_test("POST /api/login - Login with registered user")
    
    url = f"{BASE_URL}/api/login"
    data = {
        "username": TEST_USER_REGISTER["username"],
        "password": TEST_USER_REGISTER["password"]
    }
    
    response = requests.post(url, data=data)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        result = response.json()
        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")
        print(f"✓ Login successful")
        print(f"  Access Token: {access_token[:20]}...")
        print(f"  Refresh Token: {refresh_token[:20]}...")
        print(f"  Token Type: {result.get('token_type')}")
        print(f"  Expires In: {result.get('expires_in')} seconds")
        return True
    return False


# ============================================================================
# Test 3: POST /api/refresh
# ============================================================================

def test_refresh_token():
    """Test refresh token endpoint."""
    global access_token
    
    print_test("POST /api/refresh - Refresh access token")
    
    url = f"{BASE_URL}/api/refresh"
    headers = {"Content-Type": "application/json"}
    data = {"refresh_token": refresh_token}
    
    response = requests.post(url, json=data, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        result = response.json()
        old_token = access_token
        access_token = result.get("access_token")
        print(f"✓ Token refreshed successfully")
        print(f"  Old Token: {old_token[:20]}...")
        print(f"  New Token: {access_token[:20]}...")
        return True
    return False


# ============================================================================
# Test 4: GET /api/admin/scopes
# ============================================================================

def test_get_scopes():
    """Test get scopes endpoint."""
    print_test("GET /api/admin/scopes - Get available scopes")
    
    url = f"{BASE_URL}/api/admin/scopes"
    headers = get_auth_headers()
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        scopes = response.json()
        print(f"✓ Available scopes: {scopes}")
        return True
    return False


# ============================================================================
# Test 5: POST /api/login (Admin)
# ============================================================================

def test_admin_login():
    """Test admin login."""
    global access_token, refresh_token
    
    print_test("POST /api/login - Login as admin")
    
    url = f"{BASE_URL}/api/login"
    data = TEST_ADMIN
    
    response = requests.post(url, data=data)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        result = response.json()
        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")
        print(f"✓ Admin login successful")
        return True
    else:
        print("⚠ Admin login failed - admin user may not exist")
        print("  Please create an admin user manually or use existing credentials")
        return False


# ============================================================================
# Test 6: GET /api/admin/users
# ============================================================================

def test_get_users():
    """Test get users list."""
    print_test("GET /api/admin/users - Get all users (paginated)")
    
    url = f"{BASE_URL}/api/admin/users"
    headers = get_auth_headers()
    params = {"skip": 0, "limit": 10}
    
    response = requests.get(url, headers=headers, params=params)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        users = response.json()
        print(f"✓ Retrieved {len(users)} users")
        return True
    return False


# ============================================================================
# Test 7: GET /api/admin/users/{username}
# ============================================================================

def test_get_user_by_username():
    """Test get user by username."""
    print_test(f"GET /api/admin/users/{{username}} - Get user '{TEST_USER_REGISTER['username']}'")
    
    url = f"{BASE_URL}/api/admin/users/{TEST_USER_REGISTER['username']}"
    headers = get_auth_headers()
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        user = response.json()
        print(f"✓ User found: {user.get('username')}")
        return True
    return False


# ============================================================================
# Test 8: POST /api/admin/users
# ============================================================================

def test_create_user():
    """Test create user endpoint."""
    print_test("POST /api/admin/users - Create new user")
    
    url = f"{BASE_URL}/api/admin/users"
    headers = {**get_auth_headers(), "Content-Type": "application/json"}
    
    response = requests.post(url, json=TEST_USER_CREATE, headers=headers)
    success = print_result(response, expected_status=201)
    
    if success and response.status_code == 201:
        user = response.json()
        print(f"✓ User created: {user.get('username')}")
        return True
    return False


# ============================================================================
# Test 9: PUT /api/admin/users/{username}
# ============================================================================

def test_update_user():
    """Test update user endpoint."""
    print_test(f"PUT /api/admin/users/{{username}} - Update user '{TEST_USER_CREATE['username']}'")
    
    url = f"{BASE_URL}/api/admin/users/{TEST_USER_CREATE['username']}"
    headers = {**get_auth_headers(), "Content-Type": "application/json"}
    
    response = requests.put(url, json=TEST_USER_UPDATE, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        user = response.json()
        print(f"✓ User updated: {user.get('username')}")
        print(f"  New fullname: {user.get('fullname')}")
        print(f"  Active: {user.get('active')}")
        return True
    return False


# ============================================================================
# Test 10: DELETE /api/admin/users/{username}
# ============================================================================

def test_delete_user():
    """Test delete user endpoint."""
    print_test(f"DELETE /api/admin/users/{{username}} - Delete user '{TEST_USER_CREATE['username']}'")
    
    url = f"{BASE_URL}/api/admin/users/{TEST_USER_CREATE['username']}"
    headers = get_auth_headers()
    
    response = requests.delete(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        result = response.json()
        print(f"✓ User deleted: {result.get('detail')}")
        return True
    return False


# ============================================================================
# Main Test Runner
# ============================================================================

def run_tests():
    """Run all tests in sequence."""
    print("\n" + "="*80)
    print(f"USER ENDPOINTS TEST SUITE")
    print(f"Server: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = []
    
    # Authentication tests (non-admin)
    print("\n" + "─"*80)
    print("SECTION 1: User Authentication")
    print("─"*80)
    
    results.append(("Register User", test_register()))
    results.append(("Login User", test_login()))
    results.append(("Refresh Token", test_refresh_token()))
    results.append(("Get Scopes", test_get_scopes()))
    
    # Admin tests
    print("\n" + "─"*80)
    print("SECTION 2: Admin Operations")
    print("─"*80)
    
    admin_logged_in = test_admin_login()
    results.append(("Admin Login", admin_logged_in))
    
    if admin_logged_in:
        results.append(("Get Users List", test_get_users()))
        results.append(("Get User by Username", test_get_user_by_username()))
        results.append(("Create User (Admin)", test_create_user()))
        results.append(("Update User (Admin)", test_update_user()))
        results.append(("Delete User (Admin)", test_delete_user()))
    else:
        print("\n⚠ Skipping admin tests due to failed admin login")
    
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
    print("="*80 + "\n")
    
    return passed == total


def main():
    """Main entry point."""
    global BASE_URL
    
    parser = argparse.ArgumentParser(description="Test user endpoints")
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
