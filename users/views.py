from django.shortcuts import render
from django_ratelimit.core import is_ratelimited

from rest_framework import viewsets, mixins, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ErrorDetail

from . import serializers
from .models import User


def get_error_message(error):
    if hasattr(error, 'detail'):
        error = error.detail
        if isinstance(error, (list, tuple, dict)):
            error = error[0] \
                if isinstance(error, (list, tuple)) and error else next(iter(error.values()))[0] \
                if isinstance(error, dict) and error else str(error)
        elif isinstance(error, ErrorDetail):
            error = str(error)

    if isinstance(error, dict):
        # Get first error message from dictionary
        for field, errors in error.items():
            if isinstance(errors, list):
                return errors[0]
            return str(errors)
    elif isinstance(error, list):
        # Get first error from list
        return error[0]
    elif isinstance(error, ErrorDetail):
        return str(error)

    return str(error)


# Create your views here.
class RegisterView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            return Response({'error': get_error_message(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.LoginSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Rate limit: 5 login attempts per minute per IP
        limited = is_ratelimited(
            request=request,
            group='login',
            key='ip',
            rate='5/m',
            method=['POST'],
            increment=True
        )
        if limited:
            return Response({'error': 'Too many login attempts. Please try again later.'}, status=429)

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': get_error_message(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(viewsets.GenericViewSet):
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=['GET'])
    def profile(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['PUT'], url_path='update-profile', url_name='update-profile')
    def update_profile(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': get_error_message(e)}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.ForgotPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response("You are already logged in", status=status.HTTP_403_FORBIDDEN)
        # Pre-check user existence to return proper 404 for nonexistent email
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not User.objects.filter(email=email).exists():
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': get_error_message(e)}, status=status.HTTP_400_BAD_REQUEST)



class ResetPasswordView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response({'error': "You are already logged in"}, status=status.HTTP_403_FORBIDDEN)
        # Rate limit: 3 reset requests per minute per IP
        limited = is_ratelimited(
            request=request,
            group='forgot-password',
            key='ip',
            rate='3/m',
            method=['POST'],
            increment=True
        )
        if limited:
            return Response({'error': 'Too many password reset requests. Please try again later.'}, status=429)

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': get_error_message(e)}, status=status.HTTP_400_BAD_REQUEST)
