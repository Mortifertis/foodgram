# Foodgram — продуктовый помощник

Онлайн-сервис для публикации рецептов и формирования списка покупок.

## Адрес работающего сервиса
- Продакшн: https://foodgram17.mooo.com

## Быстрый старт локально
1. Скопируйте файл `.env.backend` или создайте свой на основе примера из папки [`FOR-SERVER`](FOR-SERVER/ENV.example).
2. Запустите сервисы:
   ```bash
   docker compose up -d
   ```
3. Примените миграции и соберите статику (при запуске контейнера выполняется автоматически, но команды можно повторить вручную):
   ```bash
   docker compose run --rm backend python manage.py migrate --noinput
   docker compose run --rm backend python manage.py collectstatic --noinput
   ```
4. API и документация будут доступны на http://localhost:10000, документация — http://localhost:10000/api/docs/.

## Состав docker-compose
- **backend** — Django + Gunicorn (образ публикуется в Docker Hub).
- **db** — PostgreSQL 15.
- **nginx** — отдаёт статику и проксирует запросы в backend.

Точки монтирования:
- `media_value` → `/app/media` (backend) и `/var/html/media` (nginx).
- `static_value` → `/app/collected_static` (backend) и `/var/html/static` (nginx).
- `pg_data` → `/var/lib/postgresql/data`.

## Переменные окружения backend
Основные параметры задаются в файле `.env.backend`:

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

## Папка `FOR-SERVER`
В каталоге [`FOR-SERVER`](FOR-SERVER) собраны файлы для ручной настройки сервера:
- `docker-compose.yml` — production-версия docker compose.
- `ENV.example` — пример `.env.backend`.
- `nginx/foodgram.conf` — конфигурация для `/etc/nginx/sites-enabled/` на хосте.
- `README.md` — пошаговое руководство по настройке.

Скопируйте их на сервер и адаптируйте под свою инфраструктуру.