# FastAPI Ads API (Part 2)

Проект для курса Нетология (Python-разработчик).

## Реализовано
- JWT-авторизация (POST /login, токен на 48 часов, 401 при неверных данных)
- CRUD пользователей (группы: user / admin)
- GET /user — список всех пользователей (без токена)
- GET /user/{user_id} — пользователь по ID (без токена)
- Ролевая модель доступа (403 при недостатке прав)
- Связь User -> Advertisement (CASCADE)
- CRUD объявлений + поиск по полям

## Технологии
FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16 (Docker), bcrypt, python-jose, Python 3.14

## Запуск
1. docker compose up -d
2. pip install -r requirements.txt
3. uvicorn app.main:app --reload

Документация: http://127.0.0.1:8000/docs

Автор: Лев, студент Нетологии
