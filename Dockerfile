FROM python:3.10-slim

# Instalar o FFmpeg no sistema Linux
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Rodar a API na porta 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]