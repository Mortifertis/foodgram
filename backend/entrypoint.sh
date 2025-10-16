#!/bin/sh
set -euo pipefail

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:10000 --workers "${GUNICORN_WORKERS:-3}" --timeout "${GUNICORN_TIMEOUT:-120}"
