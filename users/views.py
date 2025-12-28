from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User, Address
from .serializers import UserSerializer, AddressSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# --- Custom Error Handlers ---
# These functions handle the errors referenced in your backend/urls.py

def custom_bad_request(request, exception=None):
    return JsonResponse({
        'error': 'Bad Request',
        'message': 'The request could not be understood by the server.'
    }, status=400)

def custom_permission_denied(request, exception=None):
    return JsonResponse({
        'error': 'Permission Denied',
        'message': 'You do not have permission to access this resource.'
    }, status=403)

def custom_page_not_found(request, exception=None):
    return JsonResponse({
        'error': 'Not Found',
        'message': 'The requested resource was not found on this server.'
    }, status=404)

def custom_server_error(request):
    return JsonResponse({
        'error': 'Server Error',
        'message': 'An unexpected error occurred on the server.'
    }, status=500)