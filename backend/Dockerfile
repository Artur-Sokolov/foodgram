FROM python:3.9-slim

WORKDIR /app

# 1) Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Копируем код проекта в образ
COPY . .

# 3) Сбор статики Django при DEBUG=False
RUN python manage.py collectstatic --noinput

# 4) Открываем порт Gunicorn
EXPOSE 8000

# 5) Запускаем Gunicorn
CMD ["gunicorn", "foodgram_backend.wsgi:application", "--bind", "0.0.0.0:8000"]