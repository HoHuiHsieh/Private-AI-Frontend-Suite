#!/usr/bin/env python3
"""
Usage Endpoints Test Script

This script tests all usage tracking and health monitoring endpoints.
It sends HTTP requests to the running API server.

Usage:
    python test_usage_endpoints.py [--host HOST] [--port PORT]

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
TEST_ADMIN = {
    "username": os.getenv("DEFAULT_ADMIN_EMAIL", "admin"),
    "password": os.getenv("DEFAULT_ADMIN_PASSWORD", "secret")
}

# Store tokens
admin_access_token = None


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
        # Truncate large responses for readability
        if isinstance(data, list) and len(data) > 3:
            print(f"Response: [{len(data)} items, showing first 2]")
            print(json.dumps(data[:2], indent=2))
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text[:500]}")
    
    if expected_status:
        if response.status_code == expected_status:
            print(f"✓ PASS - Expected status {expected_status}")
            return True
        else:
            print(f"✗ FAIL - Expected {expected_status}, got {response.status_code}")
            return False
    return True


def get_auth_headers(use_admin=False):
    """Get authorization headers with access token."""
    token = admin_access_token if use_admin else admin_access_token
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ============================================================================
# Test 0: Login as admin to get access token
# ============================================================================

def test_admin_login():
    """Login as admin to get access token for subsequent tests."""
    global admin_access_token
    
    print_test("POST /api/login - Login as admin")
    
    url = f"{BASE_URL}/api/login"
    data = TEST_ADMIN
    
    response = requests.post(url, data=data)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        result = response.json()
        admin_access_token = result.get("access_token")
        print(f"✓ Admin login successful")
        print(f"  Access Token: {admin_access_token[:20]}...")
        return True
    else:
        print(f"✗ Admin login failed - cannot proceed with tests")
        return False


# ============================================================================
# USER USAGE ENDPOINTS
# ============================================================================

# Test 1: GET /api/usage/overview
def test_get_user_usage_overview():
    """Test getting user usage overview."""
    print_test("GET /api/usage/overview - Get user usage overview (default period)")
    
    url = f"{BASE_URL}/api/usage/overview"
    headers = get_auth_headers()
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved usage overview")
        print(f"  Total Tokens: {data.get('total_tokens')}")
        print(f"  Total Requests: {data.get('total_requests')}")
        print(f"  Period: {data.get('period_start')} to {data.get('period_end')}")
        return True
    return False


# Test 2: GET /api/usage/overview with days parameter
def test_get_user_usage_overview_with_days():
    """Test getting user usage overview with days parameter."""
    print_test("GET /api/usage/overview?days=7 - Get user usage overview (7 days)")
    
    url = f"{BASE_URL}/api/usage/overview"
    headers = get_auth_headers()
    params = {"days": 7}
    
    response = requests.get(url, headers=headers, params=params)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved usage overview for 7 days")
        print(f"  Daily Data Points: {len(data.get('daily_data', []))}")
        return True
    return False


# Test 3: GET /api/usage/models
def test_get_user_model_usage():
    """Test getting per-model usage for user."""
    print_test("GET /api/usage/models - Get user per-model usage")
    
    url = f"{BASE_URL}/api/usage/models"
    headers = get_auth_headers()
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved model usage data")
        print(f"  Number of models: {len(data)}")
        if data:
            print(f"  Top model: {data[0].get('model_name')} ({data[0].get('total_requests')} requests)")
        return True
    return False


# Test 4: GET /api/usage/models with interval parameter
def test_get_user_model_usage_with_interval():
    """Test getting per-model usage with interval parameter."""
    print_test("GET /api/usage/models?interval=week&period=4 - Get user model usage (4 weeks)")
    
    url = f"{BASE_URL}/api/usage/models"
    headers = get_auth_headers()
    params = {"interval": "week", "period": 4}
    
    response = requests.get(url, headers=headers, params=params)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved model usage for 4 weeks")
        print(f"  Number of models: {len(data)}")
        return True
    return False


# Test 5: GET /api/usage/logs
def test_get_user_usage_logs():
    """Test getting paginated usage logs for user."""
    print_test("GET /api/usage/logs - Get user usage logs (default pagination)")
    
    url = f"{BASE_URL}/api/usage/logs"
    headers = get_auth_headers()
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved usage logs")
        print(f"  Number of logs: {len(data)}")
        if data:
            print(f"  Latest log: Model={data[0].get('model')}, Tokens={data[0].get('total_tokens')}")
        return True
    return False


# Test 6: GET /api/usage/logs with pagination
def test_get_user_usage_logs_paginated():
    """Test getting paginated usage logs with skip and limit."""
    print_test("GET /api/usage/logs?skip=0&limit=10 - Get user usage logs (paginated)")
    
    url = f"{BASE_URL}/api/usage/logs"
    headers = get_auth_headers()
    params = {"skip": 0, "limit": 10}
    
    response = requests.get(url, headers=headers, params=params)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved paginated usage logs")
        print(f"  Returned logs: {len(data)} (max 10)")
        return True
    return False


# ============================================================================
# ADMIN HEALTH ENDPOINTS
# ============================================================================

# Test 7: GET /api/admin/health/overview
def test_get_system_overview():
    """Test getting system-wide usage overview (admin only)."""
    print_test("GET /api/admin/health/overview - Get system-wide usage overview")
    
    url = f"{BASE_URL}/api/admin/health/overview"
    headers = get_auth_headers(use_admin=True)
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved system overview")
        print(f"  Total Tokens: {data.get('total_tokens')}")
        print(f"  Total Requests: {data.get('total_requests')}")
        print(f"  Total Users: {data.get('total_users')}")
        print(f"  Active Users: {data.get('active_users')}")
        return True
    return False


# Test 8: GET /api/admin/health/overview with date range
def test_get_system_overview_with_dates():
    """Test getting system overview with custom date range."""
    print_test("GET /api/admin/health/overview - Get system overview (custom dates)")
    
    url = f"{BASE_URL}/api/admin/health/overview"
    headers = get_auth_headers(use_admin=True)
    
    # Last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    params = {
        "start_date": start_date.isoformat() + "Z",
        "end_date": end_date.isoformat() + "Z"
    }
    
    response = requests.get(url, headers=headers, params=params)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved system overview with custom dates")
        print(f"  Daily Data Points: {len(data.get('daily_data', []))}")
        return True
    return False


# Test 9: GET /api/admin/health/models
def test_get_system_model_usage():
    """Test getting system-wide per-model usage (admin only)."""
    print_test("GET /api/admin/health/models - Get system-wide model usage")
    
    url = f"{BASE_URL}/api/admin/health/models"
    headers = get_auth_headers(use_admin=True)
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved system model usage")
        print(f"  Number of models: {len(data)}")
        if data:
            print(f"  Top model: {data[0].get('model_name')} ({data[0].get('total_requests')} requests)")
        return True
    return False


# Test 10: GET /api/admin/health/models with interval
def test_get_system_model_usage_with_interval():
    """Test getting system-wide model usage with interval."""
    print_test("GET /api/admin/health/models?interval=month&period=3 - System model usage (3 months)")
    
    url = f"{BASE_URL}/api/admin/health/models"
    headers = get_auth_headers(use_admin=True)
    params = {"interval": "month", "period": 3}
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved system model usage for 3 months")
        print(f"  Number of models: {len(data)}")
        return True
    return False


# Test 11: GET /api/admin/health/gpu
def test_get_gpu_status():
    """Test getting GPU status (admin only)."""
    print_test("GET /api/admin/health/gpu - Get GPU status")
    
    url = f"{BASE_URL}/api/admin/health/gpu"
    headers = get_auth_headers(use_admin=True)
    
    response = requests.get(url, headers=headers)
    success = print_result(response, expected_status=200)
    
    if success and response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved GPU status")
        print(f"  Number of GPUs: {len(data)}")
        for gpu in data:
            print(f"  GPU {gpu.get('gpu_id')}: {gpu.get('label')}")
            print(f"    Memory: {gpu.get('memory_used_gb'):.2f}/{gpu.get('memory_total_gb'):.2f} GB")
            print(f"    Utilization: {gpu.get('utilization_percent'):.1f}%")
            if gpu.get('temperature_celsius'):
                print(f"    Temperature: {gpu.get('temperature_celsius'):.1f}°C")
        return True
    else:
        print(f"✗ Failed to retrieve GPU status")
        return False


# Test 12: Test unauthorized access to admin endpoints
def test_admin_endpoint_unauthorized():
    """Test that admin endpoints require admin scope."""
    print_test("GET /api/admin/health/overview - Test unauthorized access (should fail)")
    
    # Try to access without token
    url = f"{BASE_URL}/api/admin/health/overview"
    
    response = requests.get(url)
    
    # Should return 401 or 403
    if response.status_code in [401, 403]:
        print_result(response, expected_status=response.status_code)
        print(f"✓ Correctly rejected unauthorized access")
        return True
    else:
        print_result(response)
        print(f"✗ Expected 401 or 403, got {response.status_code}")
        return False


# ============================================================================
# Main Test Runner
# ============================================================================

def run_tests():
    """Run all tests in sequence."""
    print("\n" + "="*80)
    print(f"USAGE ENDPOINTS TEST SUITE")
    print(f"Server: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = []
    
    # Authentication
    print("\n" + "─"*80)
    print("SECTION 0: Authentication")
    print("─"*80)
    
    admin_login_success = test_admin_login()
    results.append(("Admin Login", admin_login_success))
    
    if not admin_login_success:
        print("\n✗ Cannot proceed without authentication")
        return False
    
    # User Usage Endpoints
    print("\n" + "─"*80)
    print("SECTION 1: User Usage Endpoints")
    print("─"*80)
    
    results.append(("Get User Usage Overview", test_get_user_usage_overview()))
    results.append(("Get User Usage Overview (7 days)", test_get_user_usage_overview_with_days()))
    results.append(("Get User Model Usage", test_get_user_model_usage()))
    results.append(("Get User Model Usage (4 weeks)", test_get_user_model_usage_with_interval()))
    results.append(("Get User Usage Logs", test_get_user_usage_logs()))
    results.append(("Get User Usage Logs (Paginated)", test_get_user_usage_logs_paginated()))
    
    # Admin Health Endpoints
    print("\n" + "─"*80)
    print("SECTION 2: Admin Health Endpoints")
    print("─"*80)
    
    results.append(("Get System Overview", test_get_system_overview()))
    results.append(("Get System Overview (Custom Dates)", test_get_system_overview_with_dates()))
    results.append(("Get System Model Usage", test_get_system_model_usage()))
    results.append(("Get System Model Usage (3 months)", test_get_system_model_usage_with_interval()))
    results.append(("Get GPU Status", test_get_gpu_status()))
    
    # Security Tests
    print("\n" + "─"*80)
    print("SECTION 3: Security Tests")
    print("─"*80)
    
    results.append(("Admin Endpoint Unauthorized Access", test_admin_endpoint_unauthorized()))
    
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
    
    # Note about empty data
    if passed == total:
        print("\n" + "─"*80)
        print("NOTE")
        print("─"*80)
        print("If usage data is empty (0 tokens/requests), this is expected for a fresh database.")
        print("Usage data will accumulate as the API is used for actual requests.")
    
    print("="*80 + "\n")
    
    return passed == total


def main():
    """Main entry point."""
    global BASE_URL
    
    parser = argparse.ArgumentParser(description="Test usage endpoints")
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
