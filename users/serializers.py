from django.contrib.auth import authenticate

from rest_framework import serializers

from .models import User
from .utils import get_tokens_for_user, generate_password_reset_token, verify_password_reset_token


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name')

    def validate_password_length(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.save()
        return instance


class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password2', 'full_name')
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'password2': {'write_only': True, 'required': True},
        }

    def validate(self, data):
        if data['email'] and User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("This email is already in use.")
        if not data['password'] or not data['password2']:
            raise serializers.ValidationError("Please set both passwords.")
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords don't match.")
        self.validate_password(data['password'])
        return data

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        email = validated_data.pop('email', None)
        try:
            user = User.objects.create_user(email, password, **validated_data)
            user.save()
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=128, write_only=True, required=True)
    jwt_token = serializers.DictField(read_only=True)

    def validate(self, data):
        email = data.get('email', None)
        password = data.pop('password', None)
        if email is None:
            raise serializers.ValidationError("Email is required.")
        if password is None:
            raise serializers.ValidationError("Password is required.")
        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid credentials.")
        login_data = get_tokens_for_user(user)
        data['user'] = user
        data['jwt_token'] = login_data
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, data):
        email = data.get('email', None)
        if email is None:
            raise serializers.ValidationError("Email is required.")
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is not registered.")
        return data

    def create(self, validated_data):
        email = validated_data.get('email', None)
        user = User.objects.get(email=email)
        token = generate_password_reset_token(user.id)
        return token


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)

    def validate(self, data):
        token = data.get('token', None)
        if token is None:
            raise serializers.ValidationError("Token is required.")
        user_id = verify_password_reset_token(token)
        if user_id is None:
            raise serializers.ValidationError("Invalid token.")
        return data

    def create(self, validated_data):
        return {
            'user_id': validated_data.get('user_id', None),
            'message': 'Password reset successful.'
        }
