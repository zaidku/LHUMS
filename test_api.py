"""Test script to verify the UMS API is working correctly."""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def print_response(response, title="Response"):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def main():
    """Test the main API endpoints."""
    print("🚀 Testing Flask UMS API...")
    
    # Test 1: Register a new user
    print("\n📝 Test 1: Register a new user")
    register_data = {
        "username": "apitest",
        "email": "apitest@example.com",
        "password": "testpass123",
        "first_name": "API",
        "last_name": "Tester"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print_response(response, "Registration Response")
    
    # Test 2: Login
    print("\n🔐 Test 2: Login")
    login_data = {
        "username": "apitest",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print_response(response, "Login Response")
    
    if response.status_code == 200:
        access_token = response.json()['access_token']
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Test 3: Get current user
        print("\n👤 Test 3: Get current user profile")
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print_response(response, "Current User Response")
        
        # Test 4: List labs
        print("\n🏢 Test 4: List all labs")
        response = requests.get(f"{BASE_URL}/labs", headers=headers)
        print_response(response, "Labs List Response")
        
        # Test 5: Update user profile
        print("\n✏️  Test 5: Update user profile")
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        user_id = requests.get(f"{BASE_URL}/auth/me", headers=headers).json()['user']['id']
        response = requests.patch(f"{BASE_URL}/users/{user_id}", json=update_data, headers=headers)
        print_response(response, "Update Profile Response")
        
    print("\n✅ API Testing Complete!")
    print("\nNote: Some tests may fail if the user already exists.")
    print("To reset, delete the database file and run 'python init_db.py'")

if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("Make sure the server is running: python run.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
