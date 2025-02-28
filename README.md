# 🚀 Dealopia API

> Full-stack project connecting communities with local deals they'll love

Dealopia is a community-focused platform for discovering the best local deals on clothes, books, wellness, and more. This backend powers the Dealopia API, enabling fast, reliable access to deals, shop profiles, and geolocation-based searches.

- [Frontend Repository](https://github.com/Moonchichiii/dealopia_client)

## 📋 Table of Contents

- [🔍 Overview](#-overview)
- [🛠️ Technologies](#️-technologies)
- [📂 Project Structure](#-project-structure)
- [⚡ Features](#-features)
- [🚦 Getting Started](#-getting-started)
- [🧪 Testing](#-testing)

## ✨ Overview

The API is built with Django and Django REST Framework. It leverages JWT authentication (with OAuth social logins), a robust PostgreSQL/PostGIS database for location queries, Redis caching, and Celery for background tasks such as web scraping and notifications. Our focus is on performance, real-time search, and a highly responsive user experience.

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
dealopia/
├── backend/
│   ├── config/        # Project settings and URL routing
│   ├── apps/          # Core apps: accounts, deals, shops, locations, etc.
│   ├── api/           # REST API (v1 endpoints, serializers, views)
│   ├── core/          # Utilities, middleware, and custom model managers
│   ├── templates/     # HTML templates (admin & Wagtail)
│   ├── static/        # Static assets
│   ├── locale/        # Translation files
│   ├── media/         # User uploaded files
│   └── manage.py      # Django management script
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
pip install -r requirements.txt
```

### 2. Database Setup

- Ensure PostgreSQL (with PostGIS extension) is installed and configured
- Update your `.env` file with your database settings
- Run migrations:

```bash
python manage.py migrate
```

### 3. Run the Development Server

```bash
python manage.py runserver
```

### 4. Running Background Tasks

- Start a Celery worker to handle asynchronous tasks:

```bash
celery -A backend worker -l info
```

## 🧪 Testing

### Unit Tests

```bash
python manage.py test
```

Run specific test cases:

```bash
python manage.py test apps.deals.tests
```

### Integration Tests

End-to-end test coverage for critical API workflows:

```bash
pytest
```

### Performance Testing

Load testing with Locust to ensure API performance under stress:

```bash
locust -f tests/locust/locustfile.py
```

Then access the Locust web interface at `http://localhost:8089` to configure and start your tests.
