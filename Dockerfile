FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.8.4

WORKDIR /app
COPY pyproject.toml poetry.lock* README.md ./
COPY src ./src
COPY .env.example ./
COPY requirements.txt ./

RUN poetry config virtualenvs.create false \
    && (poetry install --no-interaction --no-ansi --only main --no-root || pip install --no-cache-dir -r requirements.txt) \
    && python -m playwright install chromium

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import importlib; importlib.import_module('job_brain_bot.main')" || exit 1

CMD ["python", "-m", "job_brain_bot.main"]
