# **Foodgram API**

**Социальная платформа для обмена рецептами**

# Оглавление

* [Авторы](#авторы)
* [Технологический стек](#технологический-стек)
* [Установка и запуск проекта](#установка-и-запуск-проекта)
* [API эндпоинты](#api-эндпоинты)
* [Тестирование](#тестирование)
* [Лицензия](#лицензия)

---

## Авторы

**(контакт для связи по email)**

* [Артур Соколов](mailto:roshan94@yandex.ru) — разработчик
* Репозиторий: [GitHub](https://github.com/Artur-Sokolov/foodgram.git)

---

## Технологический стек

* Python 3.9+
* Django 4.2.23
* Django REST Framework
* django-filter (фильтрация запросов)
* PostgreSQL (в продакшен) или SQLite (по умолчанию)
* Docker & Docker Compose
* Gunicorn
* Nginx

---

## Установка и запуск проекта

**1. Клонирование и настройка виртуального окружения**

```bash
git clone https://github.com/Artur-Sokolov/foodgram.git
cd foodgram
```

**2. Сборка и запуск контейнеров**

```bash
docker compose up --build -d
```

**3. Выполнение миграций и сборка статики внутри контейнера**

```bash
# Выполнить миграции
docker compose exec backend python manage.py migrate

# Собрать статику
docker compose exec backend python manage.py collectstatic --noinput

# Переместить статику в дирректорию
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```

**4. Перезапуск контейнеров**

```bash
docker compose stop && docker compose up
```

**5. Остановка контейнеров**

```bash
docker compose down
```

---

## API эндпоинты

**Полная документация доступна после запуска сервера:**

* Server: `http://localhost:8000`

Основные маршруты:

| Метод | Путь                 | Описание                                 |
| ----- | -------------------- | ---------------------------------------- |
| POST  | `/api/users/`        | Регистрация пользователя                 |
| POST  | `/api/auth/token/`   | Получение токена (email + пароль)        |
| GET   | `/api/users/me/`     | Профиль текущего пользователя            |
| GET   | `/api/recipes/`      | Получение списка рецептов                |
| POST  | `/api/recipes/`      | Создание рецепта (авторизован)           |
| GET   | `/api/recipes/{id}/` | Получение рецепта по ID                  |
| GET   | `/api/tags/`         | Список тегов                             |
| GET   | `/api/ingredients/`  | Список ингредиентов (с поиском по имени) |

---

## Тестирование

**Статический анализ кода (flake8):**

```bash
flake8 .
```

---

## Лицензия

**Sokolov Artur License © 2025**
