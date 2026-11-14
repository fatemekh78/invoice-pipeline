FROM python:3.12-slim

# Tesseract with English, Finnish and Swedish (English comes with the base package)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-fin tesseract-ocr-swe \
    && rm -rf /var/lib/apt/lists/*

# Do not run as root
RUN useradd --create-home app
WORKDIR /app
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt

COPY src ./src
COPY assets ./assets
COPY tests ./tests
RUN chown -R app:app /app
USER app

EXPOSE 8000 8501

# Default: the API. The dashboard uses a different command (see README).
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]