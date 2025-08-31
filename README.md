# Auth Service

A Django REST API for user authentication: registration, login (JWT), profile management, and password reset with optional Redis-backed token storage and Swagger/OpenAPI documentation.

## Tech Stack
- Python 3.13
- Django + Django REST Framework
- JWT (djangorestframework-simplejwt)
- Swagger/OpenAPI (drf-spectacular)
- Optional: Redis (django-redis) for password reset tokens
- Rate limiting (django-ratelimit)

---

## Setup

1) Clone and enter the project directory
- Ensure Python 3.13 is installed.

2) Create and activate a virtual environment
- Linux/macOS:
  - python3 -m venv .venv
  - source .venv/bin/activate
- Windows (PowerShell):
  - python -m venv .venv
  - .venv\Scripts\activate

3) Install dependencies
- pip install -r requirements.txt

4) Configure environment variables
- Create a .env file in the project root (see Environment Variables section below).

5) Run database migrations
- python manage.py migrate

6) (Optional) Create a superuser
- python manage.py createsuperuser

7) Start the server
- python manage.py runserver
- API available at: http://127.0.0.1:8000

---

## Environment Variables

Create a .env file with the following keys (examples shown):

- Core
  - SECRET_KEY==django-insecure-s6eb^$=1#*xp%#qfa*5ukrq_rx^nzyf684l(7k2d0fpt6y0se_
  - DEBUG=True
  - DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
  - CORS_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000

- Database (choose ONE configuration)
  - DATABASE_URL=postgres://auth_service_user:authpassword@localhost:5432/auth_service_db
  - or detailed config:
    - DB_NAME=auth_service_db
    - DB_USER=auth_service_user
    - DB_PASS=authpassword
    - DB_HOST=localhost
    - DB_PORT=5432

- Cache / Redis (optional; if omitted, an in-memory cache is used)
  - REDIS_URL=redis://127.0.0.1:6379/0

- JWT lifetimes
  - ACCESS_TOKEN_LIFETIME_MINUTES=5
  - REFRESH_TOKEN_LIFETIME_DAYS=1

- Password reset token expiry
  - PASSWORD_RESET_EXPIRY_SECONDS=900

Notes:
- If REDIS_URL is set, make sure a Redis server is reachable at that URL.
- For production, set DEBUG=False and provide proper DJANGO_ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS.

---

## API Documentation

Interactive docs:
- Swagger UI: https://auth-service-app.up.railway.app/api/docs/
- ReDoc: https://auth-service-app.up.railway.app/api/redoc/
- OpenAPI schema: https://auth-service-app.up.railway.app/api/schema/

These docs are generated automatically via OpenAPI/Swagger.

---

## Authentication

- JWT-based authentication.
- Include the access token in requests:
  - Authorization: Bearer <access_token>

---

## Endpoints

Base path: /api/auth/

- POST /register/
  - Body: { "email": "user@example.com", "password": "password123", "password2": "password123", "full_name": "Jane Doe" }
  - Response: { "message": "User created successfully.", "user": { "id": ..., "email": "...", "full_name": "..." } }
  - Notes: Password must be at least 8 characters.

- POST /login/
  - Body: { "email": "user@example.com", "password": "password123" }
  - Response: { "user": { ... }, "jwt_token": { "refresh": "...", "access": "...", "expiry_time_seconds": ... } }

- GET /profile/
  - Headers: Authorization: Bearer <access_token>
  - Response: { "id": ..., "email": "...", "full_name": "..." }

- PUT /update-profile/
  - Headers: Authorization: Bearer <access_token>
  - Body: { "email": "new@example.com", "full_name": "New Name" }
  - Response: { "id": ..., "email": "...", "full_name": "..." }

- POST /forgot-password/
  - Body: { "email": "user@example.com" }
  - Response: { "user_id": ..., "email": "user@example.com", "token": "<reset_token>" }
  - Notes: In production you’d typically email the token instead of returning it.

- POST /reset-password/
  - Body: { "token": "<reset_token>", "new_password": "newpass123", "new_password2": "newpass123" }
  - Response: { "user_id": ..., "message": "Password reset successful." }

Example curl:
- Login:
  - curl -X POST https://auth-service-app.up.railway.app/api/auth/login/ -H "Content-Type: application/json" -d '{"email":"user@example.com","password":"password123"}'
- Forgot password:
  - curl -X POST https://auth-service-app.up.railway.app/api/auth/forgot-password/ -H "Content-Type: application/json" -d '{"email":"user@example.com"}'

---

## Rate Limiting

- The service applies per-IP rate limits to sensitive endpoints:
  - Login: 5 requests per minute
  - Forgot Password: 3 requests per minute
- Backed by the default Django cache (Redis if configured, otherwise in-memory).

---

## Running with Redis (Optional)

- Docker:
  - docker run --name auth-redis -p 6379:6379 -d redis:7
  - Set REDIS_URL=redis://auth-redis:6379/0

- Native:
  - Install and start redis-server
  - Set REDIS_URL accordingly

If REDIS_URL is not set, the service falls back to in-memory cache.

---

## Deployment

- Deployment URL: https://auth-service-app.up.railway.app
  - Swagger UI: https://auth-service-app.up.railway.app/api/docs/
  - ReDoc: https://auth-service-app.up.railway.app/api/redoc/
  - Base API: https://auth-service-app.up.railway.app/api/auth/

Basic deployment checklist:
- Set DEBUG=False
- Configure DJANGO_ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS
- Configure DATABASE_URL
- Optionally set REDIS_URL
- Collect static files:
  - python manage.py collectstatic
- Use a production WSGI server (e.g., gunicorn) behind a reverse proxy (e.g., Nginx)
- Ensure secure SECRET_KEY in environment

---

## Testing

- Run tests:
  - python manage.py test

---

## Troubleshooting

- Swagger “Failed to fetch”:
  - Ensure you’re calling the correct route prefix (/api/auth/...).
  - Check browser devtools network tab for actual status codes.
  - Configure CORS_ALLOWED_ORIGINS if calling from a different origin.

- Redis connection errors:
  - Verify REDIS_URL is correct and Redis is running/reachable.
  - Unset REDIS_URL to use in-memory cache during development.

- 429 Too Many Requests:
  - Rate limit exceeded; wait and retry later.