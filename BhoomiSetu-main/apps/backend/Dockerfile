FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar \
    && rm -rf /var/lib/apt/lists/*

COPY apps/backend/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

COPY apps/backend/ .

RUN python scripts/train_models.py

CMD ["sh", "-c", "alembic upgrade head && python -m scripts.seed_data --if-empty && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
