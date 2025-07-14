FROM python:3.11-slim

WORKDIR /app

# 1) Install system deps if needed (e.g. gcc for psycopg2)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# 2) Copy & install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Copy your application code
COPY . .

# 4) Launch Uvicorn on 0.0.0.0 so it's reachable from the host
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
