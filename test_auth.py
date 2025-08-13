"""
Test script for authentication system
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_authentication():
    """Test the authentication system"""
    print("🚀 Testing BrainFlash Authentication System")
    print("=" * 50)
    
    # Test 1: Access protected endpoint without authentication (should fail)
    print("\n1. Testing protected endpoint without authentication...")
    response = requests.get(f"{BASE_URL}/tts/protected/user-stats")
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly rejected unauthorized access")
    else:
        print("❌ Should have rejected unauthorized access")
    
    # Test 2: Register a new user
    print("\n2. Registering a new user...")
    import time
    timestamp = int(time.time())
    user_data = {
        "email": f"test{timestamp}@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ User registered successfully")
        user_info = response.json()
        print(f"User ID: {user_info['id']}")
        print(f"Email: {user_info['email']}")
    else:
        print(f"❌ Registration failed: {response.text}")
        return
    
    # Test 3: Login with the user
    print("\n3. Logging in with the user...")
    login_data = {
        "username": user_data["email"],  # fastapi-users uses 'username' field for email
        "password": user_data["password"]
    }
    
    response = requests.post(f"{BASE_URL}/auth/jwt/login", data=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Login successful")
        token_info = response.json()
        access_token = token_info["access_token"]
        print(f"Access token received: {access_token[:20]}...")
    else:
        print(f"❌ Login failed: {response.text}")
        return
    
    # Test 4: Access protected endpoint with authentication
    print("\n4. Testing protected endpoint with authentication...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/tts/protected/user-stats", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Successfully accessed protected endpoint")
        stats = response.json()
        print(f"User stats: {json.dumps(stats, indent=2)}")
    else:
        print(f"❌ Failed to access protected endpoint: {response.text}")
    
    # Test 5: Access user profile
    print("\n5. Testing user profile endpoint...")
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Successfully retrieved user profile")
        profile = response.json()
        print(f"Profile: {json.dumps(profile, indent=2)}")
    else:
        print(f"❌ Failed to retrieve user profile: {response.text}")
    
    # Test 6: Test logout
    print("\n6. Testing logout...")
    response = requests.post(f"{BASE_URL}/auth/jwt/logout", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 204]:
        print("✅ Successfully logged out")
    else:
        print(f"❌ Logout failed: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Authentication system test completed!")

if __name__ == "__main__":
    test_authentication()
