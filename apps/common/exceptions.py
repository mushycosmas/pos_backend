from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        return Response({
            'success': False,
            'message': response.data.get('detail', 'An error occurred'),
            'errors': response.data,
        }, status=response.status_code)
    
    return Response({
        'success': False,
        'message': 'Internal server error',
        'errors': None,
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)