# health/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
import time

@csrf_exempt
@require_GET
def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if application is running
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'nexadevices-backend'
    })

@csrf_exempt
@require_GET
def database_check(request):
    """
    Check database connectivity
    """
    try:
        # Try to execute a simple query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': time.time()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': time.time()
        }, status=503)

@csrf_exempt
@require_GET
def cache_check(request):
    """
    Check cache connectivity (Redis/Memcached)
    """
    try:
        # Test cache operations
        test_key = 'health_check_test'
        test_value = 'ok'
        
        cache.set(test_key, test_value, timeout=10)
        cached_value = cache.get(test_key)
        cache.delete(test_key)
        
        if cached_value == test_value:
            return JsonResponse({
                'status': 'healthy',
                'cache': 'connected',
                'timestamp': time.time()
            })
        else:
            raise Exception("Cache read/write failed")
            
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'cache': 'disconnected',
            'error': str(e),
            'timestamp': time.time()
        }, status=503)
