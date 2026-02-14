FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production

WORKDIR /app/backend

COPY backend/requirements.txt /app/backend/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install "curl-cffi" --only-binary=:all: \
    && python -m pip install -r requirements.txt

COPY backend /app/backend

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
