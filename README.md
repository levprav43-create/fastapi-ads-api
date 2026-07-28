# FastAPI REST API - Сайт объявлений

REST API для сайта объявлений на FastAPI с PostgreSQL в Docker.

## Поля объявления

- **id** - уникальный идентификатор (автогенерация)
- **title** - заголовок (обязательное)
- **description** - описание
- **price** - цена (обязательное, > 0)
- **author** - автор (обязательное)
- **created_at** - дата создания (проставляется автоматически)

## Установка и запуск

### 1. Запуск базы данных:
docker compose up -d

### 2. Установка зависимостей:
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

### 3. Запуск приложения:
uvicorn app.main:app --reload

Приложение запустится на http://localhost:8000

## API Документация

После запуска открой в браузере:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Эндпоинты

### POST /advertisement - создать объявление

### GET /advertisement/{id} - получить объявление по ID

### PATCH /advertisement/{id} - обновить объявление

### DELETE /advertisement/{id} - удалить объявление

### GET /advertisement - поиск по полям
Параметры: ?title=ноутбук&description=RAM&author=Лев&min_price=10000&max_price=100000&min_date=2026-07-01&max_date=2026-07-31
