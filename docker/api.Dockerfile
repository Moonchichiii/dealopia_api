FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml requirements.txt README.md /app/
RUN uv pip install --system -e .

COPY apps/api /app/apps/api

WORKDIR /app/apps/api
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
