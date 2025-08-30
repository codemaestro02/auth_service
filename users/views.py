from django.shortcuts import render

from rest_framework import viewsets, mixins, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from . import serializers

# Create your views here.
class RegisterView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class LoginView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.LoginSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ForgotPasswordView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.ForgotPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response("You are already logged in", status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ResetPasswordView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response("You are already logged in", status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)




