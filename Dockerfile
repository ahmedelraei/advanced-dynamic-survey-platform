FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install pipenv
RUN pip install --upgrade pip pipenv

# Copy Pipfile and install dependencies
# Use --skip-lock to avoid needing Pipfile.lock
COPY Pipfile ./
RUN pipenv install --system --skip-lock --dev

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "config.wsgi:application"]
