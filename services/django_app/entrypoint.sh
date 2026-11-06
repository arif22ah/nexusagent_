#!/bin/sh
set -e
python manage.py migrate --noinput
# Create the admin user once (credentials come from env vars)
python manage.py createsuperuser --noinput || true
exec python manage.py runserver 0.0.0.0:8001
