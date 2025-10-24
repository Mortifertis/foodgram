# Foodgram — продуктовый помощник

Онлайн-сервис для публикации рецептов и формирования списка покупок.

## Адрес работающего сервиса
- Продакшн: https://foodgram17.mooo.com

## Состав docker-compose
- **backend** — Django + Gunicorn (образ публикуется в Docker Hub).
- **db** — PostgreSQL 13.
- **nginx** — отдаёт статику и проксирует запросы в backend.

Точки монтирования:
- `media_value` → `/app/media` (backend) и `/var/html/media` (nginx).
- `static_value` → `/app/collected_static` (backend) и `/var/html/static` (nginx).
- `pg_data` → `/var/lib/postgresql/data`.

## Переменные окружения backend
Основные параметры задаются в файле `.env`:

```
SECRET_KEY=django-secret
DEBUG=0
ALLOWED_HOSTS=foodgram17.mooo.com,127.0.0.1,localhost
DB_NAME=foodgram
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=strong-password
DB_HOST=db
DB_PORT=5432
```

## CI/CD
- GitHub Actions собирает Docker-образ (`backend/Dockerfile`) и публикует его в Docker Hub.
- Далее workflow переносит файлы конфигурации на удалённый сервер и запускает `docker compose up -d`.
- После обновления применяются миграции и выполняется `collectstatic`.
- По завершении рассылается уведомление в Telegram.
