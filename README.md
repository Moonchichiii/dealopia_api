# 🚀 Dealopia Monorepo

> Full-stack project connecting communities with local deals they'll love

Dealopia is a community-focused platform for discovering the best local deals on clothes, books, wellness, and more. This repository is now the **Dealopia monorepo**, with the Django backend living in `services/backend` and workspace support for the frontend and shared packages.

- [Legacy Frontend Repository](https://github.com/Moonchichiii/dealopia_client)

## 📋 Table of Contents

- [🔍 Overview](#-overview)
- [🛠️ Technologies](#️-technologies)
- [📂 Project Structure](#-project-structure)
- [⚡ Features](#-features)
- [🚦 Getting Started](#-getting-started)
- [🧪 Testing](#-testing)
- [🏗️ Monorepo Workspaces](#️-monorepo-workspaces)

## ✨ Overview

The backend API is built with Django and Django REST Framework. It leverages JWT authentication (with OAuth social logins), a robust PostgreSQL/PostGIS database for location queries, Redis caching, and Celery for background tasks such as web scraping and notifications. Our focus is on performance, real-time search, and a highly responsive user experience.

## 🛠️ Technologies

- **Backend Framework:** Django 5.1.6, Django REST Framework
- **Authentication:** JWT, OAuth social logins
- **Admin & CMS:** Unfold, Wagtail
- **Database:** PostgreSQL with PostGIS (for geolocation)
- **Caching & Queue:** Redis, Celery
- **Performance:** Optimized queries (select_related, prefetch_related), custom SQL where needed
- **Internationalization:** Django's i18n framework with language middleware

## 📂 Project Structure

```plaintext
dealopia_api/
├── services/
│   └── backend/
│       ├── api/       # REST API (v1 endpoints, serializers, views)
│       ├── apps/      # Domain apps: accounts, deals, shops, locations, etc.
│       ├── config/    # Django settings and URL routing
│       ├── core/      # Shared backend utilities and middleware
│       ├── tests/     # Backend test suite
│       └── manage.py  # Django management entrypoint
├── apps/
│   └── web/           # Frontend app workspace
├── packages/          # Shared packages/libs workspace
├── docs/              # Architecture and standards documentation
├── scripts/           # Automation utilities
├── package.json       # JS workspace root
├── pnpm-workspace.yaml
├── pyproject.toml     # Unified Python project/dependency configuration
└── README.md
```

## ⚡ Features

### High Performance

- Aggressive caching using Redis
- Optimized database queries with proper indexing and query optimizations
- Asynchronous background processing with Celery for tasks like web scraping and notifications

### Robust API

- RESTful endpoints with versioning, pagination, and dynamic field filtering
- Secure JWT authentication and OAuth social logins
- Custom permissions and middleware (including language detection)

### Internationalization

- Built-in i18n support with language files and middleware for user preferences

## 🚦 Getting Started

### 1. Install Dependencies

```bash
pip install -e .
```

> `requirements.txt` is kept as a compatibility shim and now installs from `pyproject.toml`.

### 2. Database Setup

- Ensure PostgreSQL (with PostGIS extension) is installed and configured
- Update your `.env` file with your database settings
- Run migrations:

```bash
python services/backend/manage.py migrate
```

### 3. Run the Development Server

```bash
python services/backend/manage.py runserver
```

### 4. Running Background Tasks

- Start a Celery worker to handle asynchronous tasks:

```bash
PYTHONPATH=services/backend celery -A config worker -l info
```

### 5. Monorepo JavaScript Workspaces (Frontend + Shared Packages)

```bash
pnpm install
```

## 🧪 Testing

### Unit Tests

```bash
python services/backend/manage.py test
```

Run specific test cases:

```bash
python services/backend/manage.py test apps.deals.tests
```

### Integration Tests

End-to-end test coverage for critical API workflows:

```bash
PYTHONPATH=services/backend pytest
```

### Performance Testing

Load testing with Locust to ensure API performance under stress:

Locust configuration is planned as part of the monorepo performance suite setup.

## 🏗️ Monorepo Workspaces

- `apps/web`: frontend application (integrated workspace location).
- `packages/*`: shared frontend/backend utilities and client SDKs.
- `services/backend`: Django API service.

Use repo-root commands and workspace tooling to keep backend and frontend changes aligned.
