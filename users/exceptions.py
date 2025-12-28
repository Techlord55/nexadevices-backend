# users/exceptions.py
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that logs errors and
    returns consistent error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get the request from context
    request = context.get('request')
    view = context.get('view')
    
    if response is not None:
        # Standardize error response format
        custom_response_data = {
            'error': True,
            'status_code': response.status_code,
            'message': get_error_message(exc, response),
            'details': response.data if settings.DEBUG else None,
        }
        
        # Log the error
        if response.status_code >= 500:
            logger.error(
                f'Server Error: {exc.__class__.__name__} - {str(exc)} | '
                f'Path: {request.path if request else "N/A"} | '
                f'View: {view.__class__.__name__ if view else "N/A"}',
                exc_info=True
            )
        elif response.status_code >= 400:
            logger.warning(
                f'Client Error: {exc.__class__.__name__} - {str(exc)} | '
                f'Path: {request.path if request else "N/A"} | '
                f'User: {request.user if request and hasattr(request, "user") else "Anonymous"}'
            )
        
        response.data = custom_response_data
    else:
        # Handle non-DRF exceptions
        logger.error(
            f'Unhandled Exception: {exc.__class__.__name__} - {str(exc)} | '
            f'Path: {request.path if request else "N/A"}',
            exc_info=True
        )
        
        # Return generic error response for unhandled exceptions
        response = Response(
            {
                'error': True,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'An unexpected error occurred. Our team has been notified.',
                'details': str(exc) if settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response


def get_error_message(exc, response):
    """
    Extract a user-friendly error message from the exception
    """
    # Handle validation errors
    if hasattr(response, 'data') and isinstance(response.data, dict):
        if 'detail' in response.data:
            return str(response.data['detail'])
        
        # Handle field-specific validation errors
        errors = []
        for field, messages in response.data.items():
            if isinstance(messages, list):
                errors.extend([f"{field}: {msg}" for msg in messages])
            else:
                errors.append(f"{field}: {messages}")
        
        if errors:
            return '; '.join(errors)
    
    # Default to exception message
    return str(exc) if str(exc) else 'An error occurred'


class DatabaseConnectionError(Exception):
    """Custom exception for database connection issues"""
    pass


class ExternalAPIError(Exception):
    """Custom exception for external API failures (Clerk, Stripe, etc.)"""
    pass


class InsufficientStockError(Exception):
    """Custom exception for inventory issues"""
    pass


class PaymentProcessingError(Exception):
    """Custom exception for payment failures"""
    pass