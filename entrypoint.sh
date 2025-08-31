#!/usr/bin/env bash
set -e

# Run migrations on container start
python manage.py migrate --noinput

# Start Gunicorn bound to $PORT
exec gunicorn core.wsgi --bind 0.0.0.0:${PORT} --workers 3 --log-file -