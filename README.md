# Advanced Dynamic Survey Platform (ADSP)

Enterprise-level dynamic survey platform backend built with Django 5.x, featuring multi-dimensional conditional logic, partial submission persistence, and horizontal scalability.

## Features

- **Dynamic Survey Builder**: Survey > Section > Field hierarchies with JSONB storage
- **Conditional Logic Engine**: Supports equals, not_equals, greater_than, contains, and more
- **Cross-Section Dependencies**: Filter options based on previous answers
- **Partial Saves (Heartbeat)**: Auto-save progress with session tokens
- **Real-time Validation**: Server-side logic engine validation on submission
- **PII Encryption**: Sensitive fields encrypted via django-cryptography
- **RBAC**: Object-level permissions (Admins, Analysts, Viewers)
- **Audit Trail**: Immutable logging of all API mutations
- **Redis Caching**: Survey template caching for performance
- **Celery Tasks**: Async CSV exports and batch email invitations

## Tech Stack

- **Framework**: Django 5.x + Django REST Framework
- **Database**: PostgreSQL with JSONB
- **Cache/Broker**: Redis
- **Task Queue**: Celery
- **API Docs**: drf-spectacular (OpenAPI/Swagger)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services
docker compose up -d

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Access at http://localhost:8000
```

### Local Development

```bash
# Install dependencies
pipenv install --dev

# Activate environment
pipenv shell

# Copy environment file
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

## API Endpoints

All endpoints are versioned: `/api/v1/...`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/surveys/` | GET, POST | List/Create surveys |
| `/api/v1/surveys/{id}/` | GET, PUT, DELETE | Retrieve/Update/Delete survey |
| `/api/v1/surveys/{id}/duplicate/` | POST | Duplicate survey |
| `/api/v1/surveys/{id}/sections/` | GET, POST | Manage sections |
| `/api/v1/surveys/{id}/partial/` | GET, POST | Save/retrieve progress |
| `/api/v1/surveys/{id}/submit/` | POST | Final submission |
| `/api/v1/surveys/{id}/responses/` | GET | List responses |
| `/api/v1/surveys/{id}/responses/export/` | POST | Trigger CSV export |

**API Documentation**: http://localhost:8000/api/docs/

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=apps

# Specific module
pytest apps/logic_engine/tests.py -v
```

## Project Structure

```
├── config/                 # Django settings & config
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── celery.py
│   └── urls.py
├── apps/
│   ├── users/             # Custom User, RBAC permissions
│   ├── surveys/           # Survey, Section, Field models & views
│   ├── responses/         # Response, PartialResponse & submission
│   ├── logic_engine/      # Conditional logic evaluation
│   └── audit/             # Audit logging
├── docker-compose.yml
├── Dockerfile
├── Pipfile
└── pytest.ini
```

## License

Proprietary - All rights reserved
