from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from jsonschema.exceptions import ValidationError

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
        email = data.get('email')
        password = data.get('password')
        password2 = data.get('password2')

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already in use.")
        if not password or not password2:
            raise serializers.ValidationError("Please set both passwords.")
        if password != password2:
            raise serializers.ValidationError("Passwords don't match.")
        self.validate_password(password)
        return data

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def create(self, validated_data):
        # Remove helper field and extract credentials
        validated_data.pop('password2', None)
        password = validated_data.pop('password')
        email = validated_data.get('email')

        # Create and return the user instance (not a dict)
        user = User.objects.create_user(email=email, password=password, **{k: v for k, v in validated_data.items() if k != 'email'})
        return user

    def to_representation(self, instance):
        # Provide a friendly message alongside the serialized user fields
        base = super().to_representation(instance)
        return {
            'message': 'User created successfully.',
            'user': base
        }


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
        # Use 'username' and include request for compatibility with common auth backends
        user = authenticate(self.context.get('request'), username=email, password=password)

        if user is None:
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError("Invalid password.")
            else:
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
        return {
            'user_id': user.id,
            'email': user.email,
            'token': token
        }


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(max_length=128, required=True)
    new_password2 = serializers.CharField(max_length=128, required=True)

    def validate(self, data):
        token = data.get('token', None)
        if token is None:
            raise serializers.ValidationError("Token is required.")
        user_id = verify_password_reset_token(token)
        if user_id is None:
            raise serializers.ValidationError("Invalid or expired token.")
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError("Passwords don't match.")
        validate_password(data['new_password'], user=User(id=user_id))
        data.update(
            {
                'user_id': user_id,
            }
        )
        return data

    def create(self, validated_data):
        new_password = validated_data.pop('new_password', None)
        validated_data.pop('new_password2', None)
        try:
            user = User.objects.get(id=validated_data.get('user_id', None))
            user.set_password(new_password)
            user.save()

        except User.DoesNotExist:
            return serializers.ValidationError("User not found.")

        return {
            'user_id': validated_data.get('user_id', None),
            'message': 'Password reset successful.'
        }
