# Используем легковесный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости, необходимые для сборки некоторых Python пакетов
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем Python-зависимости бэкенда
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код бэкенда
COPY backend/ ./backend/

# Копируем скомпилированные статические файлы фронтенда
# Благодаря этому бэкенд сможет раздавать React SPA из коробки
COPY frontend/dist/ ./frontend/dist/

# Открываем порт для приложения
EXPOSE 8000

# Переменные окружения по умолчанию
ENV DEBUG=False
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000

# Запускаем FastAPI через uvicorn
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
