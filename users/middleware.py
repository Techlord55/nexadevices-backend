# users/middleware.py
import time
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings

class RateLimitMiddleware:
    """
    Simple rate limiting middleware to prevent brute force attacks
    Uses Django's cache backend (configure Redis for production)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_paths = [
            '/api/webhooks/clerk/',
            '/api/webhooks/stripe/',
            '/api/users/me/',
            '/api/orders/',
        ]
        self.max_requests = 100  # requests per window
        self.window_seconds = 60  # 1 minute window
        
    def __call__(self, request):
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Check if path should be rate limited
        should_limit = any(request.path.startswith(path) for path in self.rate_limit_paths)
        
        if should_limit and not self.check_rate_limit(ip, request.path):
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after': self.window_seconds
            }, status=429)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_rate_limit(self, ip, path):
        """Check if request should be rate limited"""
        cache_key = f'rate_limit:{ip}:{path}'
        
        # Get current request count
        request_count = cache.get(cache_key, 0)
        
        if request_count >= self.max_requests:
            return False
        
        # Increment counter
        cache.set(cache_key, request_count + 1, self.window_seconds)
        return True


class SecurityHeadersMiddleware:
    """
    Add security headers to all responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'same-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https: blob:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.stripe.com https://api.clerk.com; "
                "frame-ancestors 'none';"
            )
        
        return response


class RequestLoggingMiddleware:
    """
    Log suspicious requests for security monitoring
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.suspicious_patterns = [
            'admin', 'login', 'password', 'root', 'api/auth',
            '../', '..\\', '<script', 'SELECT', 'UNION', 'DROP'
        ]
    
    def __call__(self, request):
        # Check for suspicious patterns
        full_path = request.get_full_path().lower()
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        is_suspicious = any(pattern.lower() in full_path for pattern in self.suspicious_patterns)
        
        if is_suspicious:
            import logging
            logger = logging.getLogger('django.security')
            logger.warning(
                f'Suspicious request detected: '
                f'IP={self.get_client_ip(request)}, '
                f'Path={request.path}, '
                f'Method={request.method}, '
                f'UserAgent={user_agent}'
            )
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')