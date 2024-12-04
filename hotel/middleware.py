import time
import json
import logging
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import status

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    """Middleware to log all requests and responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start time of request
        start_time = time.time()
        
        # Generate request ID
        request_id = timezone.now().strftime('%Y%m%d%H%M%S-') + str(int(start_time * 1000))[-3:]
        request.request_id = request_id

        # Log request
        self.log_request(request)

        # Get response
        response = self.get_response(request)

        # Calculate request duration
        duration = time.time() - start_time

        # Log response
        self.log_response(request, response, duration)

        return response

    def log_request(self, request):
        """Log request details"""
        try:
            log_data = {
                'timestamp': timezone.now().isoformat(),
                'request_id': request.request_id,
                'method': request.method,
                'path': request.path,
                'user': str(request.user),
                'ip': self.get_client_ip(request)
            }

            # Log request body for POST/PUT/PATCH
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    log_data['body'] = json.loads(request.body) if request.body else None
                except json.JSONDecodeError:
                    log_data['body'] = 'Invalid JSON'

            logger.info(f"Request: {json.dumps(log_data)}")
        except Exception as e:
            logger.error(f"Error logging request: {str(e)}")

    def log_response(self, request, response, duration):
        """Log response details"""
        try:
            log_data = {
                'timestamp': timezone.now().isoformat(),
                'request_id': request.request_id,
                'status_code': response.status_code,
                'duration': f"{duration:.3f}s",
                'content_length': len(response.content) if hasattr(response, 'content') else 0
            }

            logger.info(f"Response: {json.dumps(log_data)}")
        except Exception as e:
            logger.error(f"Error logging response: {str(e)}")

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class ErrorHandlingMiddleware:
    """Middleware to handle exceptions and return appropriate responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Process exceptions and return appropriate responses"""
        error_id = timezone.now().strftime('%Y%m%d%H%M%S-') + str(int(time.time() * 1000))[-3:]
        
        # Log the error
        logger.error(f"Error ID: {error_id}", exc_info=True)
        
        # Prepare error response
        error_response = {
            'error_id': error_id,
            'timestamp': timezone.now().isoformat(),
            'type': exception.__class__.__name__
        }

        # Handle different types of exceptions
        if isinstance(exception, ValidationError):
            error_response.update({
                'message': 'Validation error',
                'details': exception.message_dict if hasattr(exception, 'message_dict') else str(exception)
            })
            status_code = status.HTTP_400_BAD_REQUEST

        elif isinstance(exception, PermissionError):
            error_response.update({
                'message': 'Permission denied',
                'details': str(exception)
            })
            status_code = status.HTTP_403_FORBIDDEN

        elif isinstance(exception, NotImplementedError):
            error_response.update({
                'message': 'Not implemented',
                'details': str(exception)
            })
            status_code = status.HTTP_501_NOT_IMPLEMENTED

        else:
            # Generic error handling
            if settings.DEBUG:
                error_response.update({
                    'message': str(exception),
                    'details': {
                        'traceback': str(exception.__traceback__)
                    }
                })
            else:
                error_response.update({
                    'message': 'Internal server error',
                    'details': 'Please contact support with the error ID'
                })
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return JsonResponse(error_response, status=status_code)

class PerformanceMonitoringMiddleware:
    """Middleware to monitor and log performance metrics"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slowest_threshold = 1.0  # seconds

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        # Log slow requests
        if duration > self.slowest_threshold:
            self.log_slow_request(request, duration)

        # Add performance headers
        response['X-Response-Time'] = f"{duration:.3f}s"

        return response

    def log_slow_request(self, request, duration):
        """Log details of slow requests"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'duration': f"{duration:.3f}s",
            'method': request.method,
            'path': request.path,
            'user': str(request.user),
            'ip': self.get_client_ip(request)
        }
        logger.warning(f"Slow request detected: {json.dumps(log_data)}")

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')