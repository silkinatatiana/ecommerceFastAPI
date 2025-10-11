FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models/ ./models/
COPY database/ ./database/
COPY general_functions/ ./general_functions/
COPY schemas.py ./schemas.py
COPY config.py ./config.py
COPY alembic.ini ./alembic.ini
COPY .env ./

COPY app/ ./app/

RUN mkdir -p /app/app/static

ENV PYTHONPATH=/app

WORKDIR /app/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]