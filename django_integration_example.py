"""Example integration with Django using requests."""
import os
import requests
from typing import Optional, Dict, Any


class UMSClient:
    """Client for interacting with the User Management Service API from Django."""
    
    def __init__(self, base_url: str = None):
        """Initialize the UMS client.
        
        Args:
            base_url: Base URL of the UMS API (e.g., http://localhost:5000/api)
        """
        self.base_url = base_url or os.getenv('UMS_API_URL', 'http://localhost:5000/api')
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization."""
        headers = {'Content-Type': 'application/json'}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers
    
    def register(self, username: str, email: str, password: str, 
                 first_name: str = '', last_name: str = '') -> Dict[str, Any]:
        """Register a new user.
        
        Args:
            username: Unique username
            email: User email address
            password: User password
            first_name: User's first name
            last_name: User's last name
            
        Returns:
            API response with user data
        """
        data = {
            'username': username,
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name
        }
        response = requests.post(
            f'{self.base_url}/auth/register',
            json=data,
            headers=self._get_headers()
        )
        return response.json()
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and get JWT tokens.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            API response with tokens and user data
        """
        data = {'username': username, 'password': password}
        response = requests.post(
            f'{self.base_url}/auth/login',
            json=data,
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result.get('access_token')
            self.refresh_token = result.get('refresh_token')
        
        return response.json()
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user profile.
        
        Returns:
            User profile data
        """
        response = requests.get(
            f'{self.base_url}/auth/me',
            headers=self._get_headers()
        )
        return response.json()
    
    def refresh_access_token(self) -> str:
        """Refresh the access token using refresh token.
        
        Returns:
            New access token
        """
        # Temporarily use refresh token
        temp_token = self.access_token
        self.access_token = self.refresh_token
        
        response = requests.post(
            f'{self.base_url}/auth/refresh',
            headers=self._get_headers()
        )
        
        # Restore access token
        self.access_token = temp_token
        
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
        
        return self.access_token
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User data
        """
        response = requests.get(
            f'{self.base_url}/users/{user_id}',
            headers=self._get_headers()
        )
        return response.json()
    
    def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Update user profile.
        
        Args:
            user_id: User ID
            **kwargs: Fields to update (email, first_name, last_name, is_active)
            
        Returns:
            Updated user data
        """
        response = requests.patch(
            f'{self.base_url}/users/{user_id}',
            json=kwargs,
            headers=self._get_headers()
        )
        return response.json()
    
    def list_labs(self) -> Dict[str, Any]:
        """Get all labs.
        
        Returns:
            List of labs
        """
        response = requests.get(
            f'{self.base_url}/labs',
            headers=self._get_headers()
        )
        return response.json()
    
    def get_user_labs(self, user_id: int) -> Dict[str, Any]:
        """Get all labs a user is a member of.
        
        Args:
            user_id: User ID
            
        Returns:
            List of lab memberships
        """
        response = requests.get(
            f'{self.base_url}/users/{user_id}/labs',
            headers=self._get_headers()
        )
        return response.json()
    
    def get_lab_members(self, lab_id: int) -> Dict[str, Any]:
        """Get all members of a lab.
        
        Args:
            lab_id: Lab ID
            
        Returns:
            List of lab members
        """
        response = requests.get(
            f'{self.base_url}/labs/{lab_id}/members',
            headers=self._get_headers()
        )
        return response.json()


# Example Django view using the UMS client
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .ums_client import UMSClient

@require_http_methods(["POST"])
def django_login_view(request):
    '''Django view that authenticates with UMS.'''
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    ums = UMSClient()
    result = ums.login(username, password)
    
    if 'access_token' in result:
        # Store tokens in session
        request.session['ums_access_token'] = result['access_token']
        request.session['ums_refresh_token'] = result['refresh_token']
        request.session['user_data'] = result['user']
        
        return JsonResponse({
            'status': 'success',
            'user': result['user']
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Authentication failed'
        }, status=401)

@require_http_methods(["GET"])
def get_user_labs_view(request, user_id):
    '''Get labs for a user.'''
    # Get token from session
    access_token = request.session.get('ums_access_token')
    
    ums = UMSClient()
    ums.access_token = access_token
    
    try:
        result = ums.get_user_labs(user_id)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
"""
