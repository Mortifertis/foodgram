FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    libpq-dev \
    libjpeg62-turbo-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=foodgram_backend.settings

RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "foodgram_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
