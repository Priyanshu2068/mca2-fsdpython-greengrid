"""
GreenGrid Unified Exception Handler.
Enforces the mandatory error response envelope:
{"error": {"status": int, "code": str, "message": str, "details": dict | list | str}}
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)

def custom_exception_handler(exc, context):
    """
    Transforms any DRF or Django exception into the standardized error format.
    """
    # Convert Django's core ValidationError to DRF's format
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, 'message_dict'):
            details = exc.message_dict
        elif hasattr(exc, 'messages'):
            details = exc.messages
        else:
            details = str(exc)
        return Response(
            {
                'error': {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'code': 'VALIDATION_ERROR',
                    'message': 'Validation failed.',
                    'details': details,
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    response = exception_handler(exc, context)

    # Standard status code to error code mapping
    code_map = {
        status.HTTP_400_BAD_REQUEST: 'VALIDATION_ERROR',
        status.HTTP_401_UNAUTHORIZED: 'AUTHENTICATION_REQUIRED',
        status.HTTP_403_FORBIDDEN: 'PERMISSION_DENIED',
        status.HTTP_404_NOT_FOUND: 'RESOURCE_NOT_FOUND',
        status.HTTP_405_METHOD_NOT_ALLOWED: 'METHOD_NOT_ALLOWED',
        status.HTTP_429_TOO_MANY_REQUESTS: 'RATE_LIMIT_EXCEEDED',
        status.HTTP_500_INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
    }

    if response is not None:
        status_code = response.status_code
        error_code = code_map.get(status_code, 'APPLICATION_ERROR')

        # Determine user-friendly top-level message
        if isinstance(response.data, dict) and 'detail' in response.data:
            message = str(response.data['detail'])
            details = response.data.get('details', response.data['detail'])
        elif isinstance(response.data, dict):
            message = 'Invalid request parameters or constraints violated.'
            details = response.data
        elif isinstance(response.data, list):
            message = 'Request payload validation failed.'
            details = response.data
        else:
            message = str(response.data)
            details = response.data

        # Map status codes to standard codes
        error_code = code_map.get(status_code, 'APPLICATION_ERROR')

        # Allow explicit business codes on custom exceptions if provided (and not DRF defaults like 'invalid')
        if hasattr(exc, 'code') and exc.code:
            error_code = str(exc.code).upper()
        elif hasattr(exc, 'default_code') and exc.default_code and exc.default_code not in ('invalid', 'not_found', 'permission_denied', 'authentication_failed', 'not_authenticated'):
            error_code = str(exc.default_code).upper()

        response.data = {
            'error': {
                'status': status_code,
                'code': error_code,
                'message': message,
                'details': details,
            }
        }
        return response

    # Handle unhandled Python exceptions gracefully
    return Response(
        {
            'error': {
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected server error occurred.',
                'details': str(exc) if hasattr(exc, 'message') else str(exc),
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
