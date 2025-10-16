#!/bin/sh
set -euo pipefail

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

python <<'PY'
import os
import sys
import time

import django
from django.db import connections
from django.db.utils import OperationalError

django.setup()

max_attempts = int(os.getenv('DB_WAIT_ATTEMPTS', 30))
delay = float(os.getenv('DB_WAIT_DELAY', 2))

for attempt in range(1, max_attempts + 1):
    try:
        connections['default'].cursor()
    except OperationalError as exc:
        print(f"Database unavailable (attempt {attempt}/{max_attempts}): {exc}")
        time.sleep(delay)
    else:
        print("Database connection established.")
        break
else:
    print("Database is unavailable after waiting.", file=sys.stderr)
    sys.exit(1)
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:10000 --workers "${GUNICORN_WORKERS:-3}" --timeout "${GUNICORN_TIMEOUT:-120}"
