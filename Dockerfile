# Используем официальное изображение Python 3.11 из Docker Hub
FROM python:3.11-slim

# Устанавливаем рабочий каталог
WORKDIR /app

# Копируем файл requirements.txt в контейнер
COPY requirements.txt requirements.txt

# Устанавливаем необходимые Python пакеты
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код приложения в контейнер
COPY . .

# Устанавливаем переменные окружения
ENV FLASK_APP=app.py

# Открываем порт, на котором работает приложение
EXPOSE 5000

# Запускаем приложение с использованием gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
