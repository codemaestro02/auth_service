import os
import secrets
import dotenv

from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from django_redis import get_redis_connection, exceptions
from redis.exceptions import ConnectionError


dotenv.load_dotenv()

def get_tokens_for_user(user):
    """
    Generate JWT tokens for the given user.

    Args:
        user: The user instance for whom to generate tokens.

    Returns:
        A dictionary containing access and refresh tokens.
    """
    refresh = RefreshToken.for_user(user)
    token_lifetime = refresh.lifetime

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'expiry_time_seconds': int(token_lifetime.total_seconds()),
    }


def generate_password_reset_token(user_id):
    """
    Generate a password reset token and store it in Redis or Django Cache.

    Args:
        user_id: The ID of the user requesting password reset.

    Returns:
        str: The generated reset token.
    """
    token = secrets.token_urlsafe(32)

    try:
        redis_conn = get_redis_connection("default")
        redis_conn.setex(f"password_reset_{token}", int(os.getenv("PASSWORD_RESET_EXPIRY_SECONDS", 600)), str(user_id))
    except (exceptions.ConnectionInterrupted, ConnectionError):
        cache.set(f"password_reset_{token}", str(user_id), int(os.getenv("PASSWORD_RESET_EXPIRY_SECONDS", 600)))
    return token


def verify_password_reset_token(token):
    """
    Verify if a password-reset token is valid and return the associated user ID.

    Args:
        token: The reset token to verify.

    Returns:
        str: The user ID if token is valid, None otherwise.
    """
    try:
        redis_conn = get_redis_connection("default")
        user_id = redis_conn.get(f"password_reset_{token}")
        if user_id:
            redis_conn.delete(f"password_reset_{token}")
            return user_id.decode()
        else:
            return None
    except (exceptions.ConnectionInterrupted, ConnectionError):
        user_id = cache.get(f"password_reset_{token}")
        if user_id:
            cache.delete(f"password_reset_{token}")
            return user_id
        else:
            return None

