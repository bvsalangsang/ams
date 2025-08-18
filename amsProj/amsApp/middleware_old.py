from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseRedirect

class HRISAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to check HRIS authentication for protected views
    """
    
    # URLs that don't require authentication (both with and without leading slash)
    EXEMPT_URLS = [
        'dashboard/login/',
        'dashboard/logview/',
        'dashboard/logout/',
        'dashboard/api/',  # This will exempt all API endpoints
        'admin/',
        'static/',
        'media/',
    ]
    
    def process_request(self, request):
        # Remove leading slash for consistent comparison
        path = request.path.lstrip('/')
        
        print(f"Middleware called for path: '{request.path}' (processed: '{path}')")  # Debug line
        print(f"Session hris_id: {request.session.get('hris_id')}")  # Debug line
        print(f"Session keys: {list(request.session.keys())}")  # Debug line
        
        # Skip authentication check for exempt URLs
        if any(path.startswith(url) for url in self.EXEMPT_URLS):
            print("URL is exempt")  # Debug line
            return None
        
        # Check if user is authenticated via HRIS session
        if not request.session.get('hris_id'):
            print("User not authenticated, redirecting to login")  # Debug line
            # Store the requested URL to redirect after login
            request.session['next_url'] = request.get_full_path()
            return HttpResponseRedirect(reverse('login'))
        
        print("User is authenticated")  # Debug line
        return None