from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.conf import settings
import hashlib
import hmac
import time

from urllib3 import request

class HRISAuthenticationMiddleware(MiddlewareMixin):
    """
    Enhanced middleware with API authentication
    """
    
    # URLs that don't require any authentication
    EXEMPT_URLS = [
        'dashboard/login/',
        'dashboard/logview/',
        'dashboard/logout/',
        'admin/',
        'static/',
        'media/',
    ]
    
    # API endpoints that require API authentication
    API_URLS = [
        'dashboard/api/get-data-punch',
        'dashboard/api/get-data-shift',
        'dashboard/api/add-punch',
        'dashboard/api/add-tamper',
        'dashboard/api/get-server-time/',
        'dashboard/api/get-punch-by-date/',
        'dashboard/api/get-punch-by-id/',
        'dashboard/api/get-schedule/',
        'dashboard/api/get-schedule-by-date/',
        'dashboard/api/get-location-by-id/',
        'dashboard/api/get-sysinfo/',
    ]
    
    def process_request(self, request):
        # Remove leading slash for consistent comparison
        path = request.path.lstrip('/')
        
        print(f"Middleware called for path: '{request.path}' (processed: '{path}')")  # Debug line
        print(f"Request method: {request.method}")  # Debug line
        
        # IMPORTANT: Always allow OPTIONS requests to pass through
        # CORS preflight requests must not be blocked
        if request.method == 'OPTIONS':
            print("OPTIONS request - allowing through for CORS")
            return None  # Let the request continue to be processed by CORS
        
        # Skip authentication check for exempt URLs
        if any(path.startswith(url) for url in self.EXEMPT_URLS):
            print("URL is exempt")  # Debug line
            return None
        
        # Check if this is an API endpoint
        if any(path.startswith(url) for url in self.API_URLS):
            return self.authenticate_api(request)
        
        # For non-API endpoints, check web authentication
        if not request.session.get('hris_id'):
            print("User not authenticated, redirecting to login")  # Debug line
            request.session['next_url'] = request.get_full_path()
            return HttpResponseRedirect(reverse('login'))
        
        print("User is authenticated")  # Debug line
        return None
    
    def authenticate_api(self, request):
        """
        Authenticate API requests using multiple methods
        """
        print("Authenticating API request")  # Debug line
        print(f"Request headers: {dict(request.headers)}")  # Debug line
        
        # Method 1: API Key Authentication
        api_key = request.headers.get('X-API-Key')
        if api_key:
            print(f"Found API key: {api_key}")  # Debug line
            return self.validate_api_key(request, api_key)
        
        # Method 2: HMAC Signature Authentication
        signature = request.headers.get('X-Signature')
        timestamp = request.headers.get('X-Timestamp')
        if signature and timestamp:
            return self.validate_hmac_signature(request, signature, timestamp)
        
        # Method 3: Bearer Token Authentication
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            return self.validate_bearer_token(request, token)
        
        # No valid authentication found
        print("API authentication failed - no valid credentials")
        return self.create_cors_json_response({
            'error': 'Authentication required',
            'code': 'AUTH_REQUIRED'
        }, status=401)
    
    def validate_api_key(self, request, api_key):
        """
        Validate API key against stored keys
        """
        # Get valid API keys from settings
        valid_keys = getattr(settings, 'FLUTTER_API_KEYS', [])
        print(f"Checking API key '{api_key}' against valid keys: {valid_keys}")  # Debug line
        
        if api_key in valid_keys:
            print("API Key authentication successful")
            # Optional: Add API client info to request
            request.api_authenticated = True
            request.api_client = 'flutter_app'
            return None
        
        print("Invalid API key provided")
        return self.create_cors_json_response({
            'error': 'Invalid API key',
            'code': 'INVALID_API_KEY',
            'received_key': api_key,  # For debugging - remove in production
        }, status=401)
    
    def validate_hmac_signature(self, request, signature, timestamp):
        """
        Validate HMAC signature for enhanced security
        """
        try:
            # Check timestamp to prevent replay attacks (5 minute window)
            current_time = int(time.time())
            request_time = int(timestamp)
            
            if abs(current_time - request_time) > 300:  # 5 minutes
                return self.create_cors_json_response({
                    'error': 'Request timestamp too old',
                    'code': 'TIMESTAMP_EXPIRED'
                }, status=401)
            
            # Create signature string
            method = request.method
            path = request.path
            body = request.body.decode('utf-8') if request.body else ''
            
            message = f"{method}|{path}|{body}|{timestamp}"
            
            # Calculate expected signature
            secret_key = getattr(settings, 'FLUTTER_API_SECRET', '').encode('utf-8')
            expected_signature = hmac.new(
                secret_key,
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if hmac.compare_digest(signature, expected_signature):
                print("HMAC signature authentication successful")
                request.api_authenticated = True
                request.api_client = 'flutter_app_secure'
                return None
            
            print("Invalid HMAC signature")
            return self.create_cors_json_response({
                'error': 'Invalid signature',
                'code': 'INVALID_SIGNATURE'
            }, status=401)
            
        except (ValueError, TypeError) as e:
            print(f"HMAC validation error: {e}")
            return self.create_cors_json_response({
                'error': 'Invalid authentication format',
                'code': 'INVALID_FORMAT'
            }, status=401)
    
    def validate_bearer_token(self, request, token):
        """
        Validate JWT or custom bearer token
        """
        # You can implement JWT validation here
        # For now, using a simple token validation
        
        valid_tokens = getattr(settings, 'FLUTTER_API_TOKENS', [])
        
        if token in valid_tokens:
            print("Bearer token authentication successful")
            request.api_authenticated = True
            request.api_client = 'flutter_app_token'
            return None
        
        print("Invalid bearer token")
        return self.create_cors_json_response({
            'error': 'Invalid bearer token',
            'code': 'INVALID_TOKEN'
        }, status=401)
    
    def create_cors_json_response(self, data, status=200):
        """
        Create a JsonResponse with CORS headers
        This ensures that API error responses include CORS headers
        """
        response = JsonResponse(data, status=status)
        
        # Add CORS headers manually for API responses
        # This is needed because the response is created in middleware
        # before the CORS middleware can add headers in the response phase
        
        if getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False):
            response['Access-Control-Allow-Origin'] = '*'
        else:
            # You might want to set this based on the request origin
            allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
            origin = request.META.get('HTTP_ORIGIN')
            if origin in allowed_origins:
                response['Access-Control-Allow-Origin'] = origin
        
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, X-Signature, X-Timestamp'
        
        if getattr(settings, 'CORS_ALLOW_CREDENTIALS', False):
            response['Access-Control-Allow-Credentials'] = 'true'
        
        return response