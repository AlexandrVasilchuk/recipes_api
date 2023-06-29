#!/bin/sh

python manage.py migrate;
python manage.py collectstatic --no-input;
gunicorn -b 0:8000 foodgram_backend.wsgi;