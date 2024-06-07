# Используем официальное изображение Python 3.11 из Docker Hub
FROM python:3.11-slim

# Устанавливаем рабочий каталог
WORKDIR /app

# Копируем файл requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем необходимые Python пакеты
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код приложения в контейнер
COPY . .

# Открываем порт, на котором работает приложение
EXPOSE 8000

# Запускаем приложение с использованием uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

