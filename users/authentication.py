# users/authentication.py
import logging
import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User

logger = logging.getLogger(__name__)

class ClerkAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication backend for Clerk
    Includes caching to reduce API calls
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
        
        try:
            # Extract token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                raise AuthenticationFailed('Invalid token header format. Use: Bearer <token>')
            
            token = parts[1]
        except IndexError:
            raise AuthenticationFailed('Invalid token header format')
        
        # Check cache first to reduce API calls
        cache_key = f'clerk_token:{token[:20]}'  # Use part of token as key
        cached_user_id = cache.get(cache_key)
        
        if cached_user_id:
            try:
                user = User.objects.get(clerk_id=cached_user_id)
                return (user, None)
            except User.DoesNotExist:
                cache.delete(cache_key)
        
        # Verify token with Clerk
        try:
            clerk_user_id = self.verify_clerk_token(token)
            clerk_user_data = self.fetch_clerk_user(clerk_user_id)
            
            # Get or create user
            user = self.get_or_create_user(clerk_user_id, clerk_user_data)
            
            # Cache the user ID for 5 minutes
            cache.set(cache_key, clerk_user_id, timeout=300)
            
            return (user, None)
            
        except requests.RequestException as e:
            logger.error(f'Clerk API request failed: {str(e)}')
            raise AuthenticationFailed('Authentication service unavailable')
        except Exception as e:
            logger.error(f'Authentication error: {str(e)}', exc_info=True)
            raise AuthenticationFailed('Authentication failed')
    
    def verify_clerk_token(self, token):
        """
        Verify token with Clerk API
        Returns clerk_user_id if valid
        """
        try:
            response = requests.post(
                f'{settings.CLERK_API_URL}/tokens/verify',
                headers={
                    'Authorization': f'Bearer {settings.CLERK_SECRET_KEY}',
                    'Content-Type': 'application/json'
                },
                json={'token': token},
                timeout=5  # 5 second timeout
            )
            
            if response.status_code == 200:
                token_data = response.json()
                clerk_user_id = token_data.get('sub') or token_data.get('user_id')
                
                if not clerk_user_id:
                    raise AuthenticationFailed('User ID not found in token')
                
                return clerk_user_id
            elif response.status_code == 401:
                raise AuthenticationFailed('Invalid or expired token')
            else:
                logger.error(f'Clerk token verification failed: {response.status_code}')
                raise AuthenticationFailed('Token verification failed')
                
        except requests.Timeout:
            logger.error('Clerk API timeout during token verification')
            raise AuthenticationFailed('Authentication service timeout')
    
    def fetch_clerk_user(self, clerk_user_id):
        """
        Fetch full user details from Clerk
        """
        try:
            response = requests.get(
                f'{settings.CLERK_API_URL}/users/{clerk_user_id}',
                headers={
                    'Authorization': f'Bearer {settings.CLERK_SECRET_KEY}',
                    'Content-Type': 'application/json'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f'Failed to fetch Clerk user: {response.status_code}')
                raise AuthenticationFailed('Could not fetch user details')
                
        except requests.Timeout:
            logger.error('Clerk API timeout during user fetch')
            raise AuthenticationFailed('Authentication service timeout')
    
    def get_or_create_user(self, clerk_user_id, clerk_user_data):
        """
        Get or create Django user from Clerk data
        """
        try:
            # Try to get existing user
            user = User.objects.get(clerk_id=clerk_user_id)
            
            # Update user info if needed
            self.update_user_info(user, clerk_user_data)
            
            return user
            
        except User.DoesNotExist:
            # Create new user
            return self.create_user(clerk_user_id, clerk_user_data)
    
    def create_user(self, clerk_user_id, clerk_user_data):
        """
        Create a new Django user from Clerk data
        """
        email_addresses = clerk_user_data.get('email_addresses', [])
        email = email_addresses[0].get('email_address', '') if email_addresses else ''
        
        # Generate unique username
        base_username = clerk_user_data.get('username')
        if not base_username:
            base_username = email.split('@')[0] if email else f'user_{clerk_user_id[:8]}'
        
        username = self.generate_unique_username(base_username)
        
        user = User.objects.create(
            clerk_id=clerk_user_id,
            username=username,
            email=email,
            first_name=clerk_user_data.get('first_name', ''),
            last_name=clerk_user_data.get('last_name', ''),
            avatar=clerk_user_data.get('image_url', ''),
        )
        
        logger.info(f'New user created: {user.username} (clerk_id: {clerk_user_id})')
        return user
    
    def update_user_info(self, user, clerk_user_data):
        """
        Update user information from Clerk data
        """
        email_addresses = clerk_user_data.get('email_addresses', [])
        
        updated = False
        
        if email_addresses:
            new_email = email_addresses[0].get('email_address', user.email)
            if new_email != user.email:
                user.email = new_email
                updated = True
        
        if clerk_user_data.get('first_name') and clerk_user_data['first_name'] != user.first_name:
            user.first_name = clerk_user_data['first_name']
            updated = True
        
        if clerk_user_data.get('last_name') and clerk_user_data['last_name'] != user.last_name:
            user.last_name = clerk_user_data['last_name']
            updated = True
        
        if clerk_user_data.get('image_url') and clerk_user_data['image_url'] != user.avatar:
            user.avatar = clerk_user_data['image_url']
            updated = True
        
        if updated:
            user.save()
            logger.info(f'User updated: {user.username}')
    
    def generate_unique_username(self, base_username):
        """
        Generate a unique username by appending numbers if needed
        """
        username = base_username
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f'{base_username}{counter}'
            counter += 1
        
        return username
    
    def authenticate_header(self, request):
        """
        Return authentication header for 401 responses
        """
        return 'Bearer realm="api"'