# Foodgram — сервис рецептов и списков покупок

Foodgram — fullstack-сервис, где пользователи публикуют рецепты,
добавляют их в избранное, подписываются на авторов и формируют список
покупок по выбранным блюдам.

## Моя роль

Проект выполнен как учебная выпускная работа курса Python-разработчика.

Моя зона ответственности: backend-часть проекта, REST API, модели данных, сериализаторы, viewsets, permissions, фильтрация, работа с избранным, списком покупок, подписками, короткими ссылками, загрузкой изображений, Docker Compose и CI/CD через GitHub Actions.

Frontend был предоставлен как часть учебного проекта. Я интегрировал его с backend API и инфраструктурой запуска, но не позиционирую frontend-код как полностью авторскую работу.

## Возможности

- регистрация и авторизация пользователей;
- создание, редактирование и удаление рецептов;
- загрузка изображений рецептов в формате Base64;
- фильтрация рецептов по автору, тегам, избранному и списку покупок;
- добавление рецептов в избранное;
- добавление рецептов в список покупок;
- скачивание сводного списка ингредиентов;
- подписки на авторов;
- короткие ссылки на рецепты;
- API-документация через OpenAPI и Redoc.

## Стек

### Backend

- Python 3.10
- Django 4.2
- Django REST Framework
- Djoser
- django-filter
- PostgreSQL
- Gunicorn
- Docker / Docker Compose
- Nginx
- GitHub Actions

### Frontend

- React
- готовый frontend из учебного проекта, интегрированный с backend API

### Infrastructure

- Dockerized deployment
- CI/CD pipeline
- PostgreSQL healthcheck
- автоматический запуск миграций и `collectstatic` при деплое
- уведомление о деплое в Telegram

## Моя роль

Я реализовал backend-часть проекта: модели, сериализаторы, viewsets,
permissions, фильтрацию, работу с избранным, списком покупок, подписками,
короткими ссылками, загрузкой изображений и настройкой деплоя через Docker
Compose и GitHub Actions.

Frontend был предоставлен как часть учебного проекта; моя задача заключалась
в интеграции его с backend API и инфраструктурой запуска.

## Что реализовано технически

- Спроектированы модели рецептов, тегов, ингредиентов, избранного, списка
  покупок и подписок.
- Добавлены ограничения уникальности: уникальная пара `ингредиент + единица
  измерения`, уникальность рецепта у автора, запрет дублей ингредиентов в
  рецепте, избранном и списке покупок.
- Реализована генерация короткой ссылки при сохранении рецепта.
- Настроены фильтры рецептов по тегам, автору, избранному и списку покупок.
- Реализована сборка списка покупок с агрегацией ингредиентов по выбранным
  рецептам.
- Подключена token-based авторизация через Djoser.
- Настроена OpenAPI/Redoc-документация.
- Настроен CI/CD: lint, тесты, сборка backend/frontend/gateway Docker-образов,
  деплой по SSH, миграции, `collectstatic`, healthcheck gateway и
  Telegram-уведомление.

## Архитектура проекта

```text
foodgram/
├── backend/                 # Django backend и REST API
│   ├── api/                 # serializers, viewsets, filters, permissions
│   ├── foodgram_backend/    # settings, urls, wsgi/asgi
│   ├── recipes/             # модели и бизнес-логика рецептов
│   └── users/               # кастомный пользователь и подписки
├── frontend/                # React frontend
├── nginx/                   # Dockerfile и конфигурация gateway
├── infra/                   # дополнительная nginx/compose-конфигурация
├── data/                    # демо-данные ингредиентов и тегов
├── docs/                    # OpenAPI-схема, Redoc и материалы документации
├── docker-compose.yml       # локальный запуск
└── docker-compose.production.yml
```

## Локальный запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Mortifertis/foodgram.git
cd foodgram
```

### 2. Создать `.env`

```bash
cp .env.example .env
```

При необходимости измените значения в `.env`: домены, пароли, настройки
PostgreSQL и флаги безопасности cookie.

### 3. Запустить контейнеры

```bash
docker compose up --build
```

После запуска приложение будет доступно локально:

- frontend: <http://localhost:10000/>
- API: <http://localhost:10000/api/>
- Redoc: <http://localhost:10000/api/docs/>
- admin: <http://localhost:10000/admin/>

### 4. Применить миграции

```bash
docker compose exec backend python manage.py migrate
```

### 5. Собрать статику

```bash
docker compose exec backend python manage.py collectstatic --noinput
```

### 6. Создать суперпользователя

```bash
docker compose exec backend python manage.py createsuperuser
```

### 7. Загрузить демо-данные

```bash
docker compose exec backend python manage.py load_tags
```

```bash
docker compose exec backend python manage.py load_ingredients
```

## API

Документация API доступна через Redoc:

```text
/api/docs/
```

Основные группы эндпоинтов:

- `/api/users/` — пользователи;
- `/api/auth/token/login/` — получение токена;
- `/api/auth/token/logout/` — удаление токена;
- `/api/recipes/` — рецепты;
- `/api/recipes/{id}/favorite/` — избранное;
- `/api/recipes/{id}/shopping_cart/` — список покупок;
- `/api/recipes/download_shopping_cart/` — скачивание списка ингредиентов;
- `/api/users/subscriptions/` — подписки;
- `/api/ingredients/` — ингредиенты;
- `/api/tags/` — теги.

OpenAPI-схема хранится в `docs/openapi-schema.yml`, статическая Redoc-страница
— в `docs/redoc.html`.

## Тесты и проверки

Локально backend можно проверить так:

```bash
python -m pip install -r backend/requirements.txt
flake8 backend/
cd backend && python manage.py test -v 2
```

В CI эти проверки запускаются автоматически перед сборкой Docker-образов.

## CI/CD

Workflow GitHub Actions выполняет полный цикл проверки и деплоя:

1. поднимает PostgreSQL service container;
2. устанавливает зависимости backend;
3. запускает `flake8 backend/`;
4. запускает `python manage.py test -v 2`;
5. собирает и публикует Docker-образы backend, frontend и gateway;
6. копирует production compose-файл на сервер;
7. деплоит проект по SSH;
8. применяет миграции и собирает статику;
9. проверяет healthcheck gateway;
10. отправляет Telegram-уведомление об успешном деплое.

## Переменные окружения

Пример переменных находится в `.env.example`. Для локального запуска достаточно
скопировать его в `.env` и при необходимости заменить значения.

Ключевые переменные:

- `SECRET_KEY` — секретный ключ Django;
- `DEBUG` — режим отладки;
- `ALLOWED_HOSTS` — разрешенные хосты Django;
- `CSRF_TRUSTED_ORIGINS` — доверенные origin для CSRF;
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` — параметры PostgreSQL;
- `DB_HOST`, `DB_PORT` — адрес и порт базы данных;
- `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` — security-флаги cookie.

## Статус проекта

Проект готов к локальному запуску и демонстрирует backend-сервис с полноценным
циклом разработки и деплоя: REST API, PostgreSQL, Docker, Nginx и CI/CD.

Потенциальное следующее улучшение — разделить dev/prod-настройки Django и
сделать production-режим строже: обязательный `SECRET_KEY` без fallback и
wildcard-хосты только для локальной разработки.
