FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.8.4

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY .env.example ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev \
    && python -m playwright install chromium

CMD ["python", "-m", "job_brain_bot.main"]
