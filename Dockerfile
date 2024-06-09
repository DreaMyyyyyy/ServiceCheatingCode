FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Установите переменную окружения для URL базы данных
ENV DATABASE_URL="sqlite:///./test.db"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]


