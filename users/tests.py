from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.cache import cache

from .models import User
from .utils import generate_password_reset_token, verify_password_reset_token


class UserRegistrationTestCase(APITestCase):
    def test_user_registration_success(self):
        """Test successful user registration"""
        data = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='john@example.com').exists())

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        User.objects.create_user(
            email='existing@example.com',
            full_name='Existing User',
            password='password123'
        )

        data = {
            'full_name': 'New User',
            'email': 'existing@example.com',
            'password': 'NewPassword123!',
            'password2': 'NewPassword123!'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserLoginTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='TestPassword123!'
        )

    def test_user_login_success(self):
        """Test successful user login"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('jwt_token', response.data)

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class PasswordResetTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='TestPassword123!'
        )

    def test_forgot_password_success(self):
        """Test forgot password functionality"""
        data = {'email': 'test@example.com'}
        response = self.client.post('/api/auth/forgot-password/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forgot_password_nonexistent_user(self):
        """Test forgot password with non-existent user"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post('/api/auth/forgot-password/', data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reset_password_success(self):
        """Test password reset functionality"""
        email = 'test@example.com'
        user = User.objects.get(email=email)
        token = generate_password_reset_token(user.id)

        data = {
            'token': token,
            'new_password': 'NewPassword123!',
            'new_password2': 'NewPassword123!'
        }
        response = self.client.post('/api/auth/reset-password/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))

class RedisTokenTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='TestPassword123!'
        )

    def test_token_storage_and_verification(self):
        """Test Redis token storage and verification"""
        email = 'test@example.com'
        user = User.objects.get(email=email)
        token = generate_password_reset_token(user.id)

        # Verify token
        self.assertTrue(verify_password_reset_token(token))

        # Token should be deleted after verification
        self.assertFalse(verify_password_reset_token(token))

    def test_invalid_token_verification(self):
        """Test verification with invalid token"""
        email = 'test@example.com'
        user = User.objects.get(email=email)
        valid_token = generate_password_reset_token(user.id)
        invalid_token = 'invalid-token'

        self.assertFalse(verify_password_reset_token(invalid_token))