FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd -r app && useradd -r -g app -u 10001 -d /app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . /app

USER app

ENV PORT=5001
EXPOSE 5001

# Shell form so ${PORT} is expanded at runtime (Bunny Magic Containers / Cloud Run
# style platforms inject the port they expect the app to listen on).
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 2 --timeout 60 --graceful-timeout 30 --access-logfile - --error-logfile - main:app"]
