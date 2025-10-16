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

# Используем SQLite во время сборки, чтобы успешно выполнить миграции
ENV USE_SQLITE_FOR_BUILD=1
RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput
ENV USE_SQLITE_FOR_BUILD=0

RUN chmod +x /app/entrypoint.sh

EXPOSE 10000

ENTRYPOINT ["/app/entrypoint.sh"]
