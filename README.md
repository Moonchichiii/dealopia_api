# 🚀 Dealopia Monorepo

> Full-stack project connecting communities with local deals they'll love.

Dealopia is now organized as a **full-stack monorepo** with:
- `apps/api` for the Django backend
- `apps/client` for the React + Vite frontend
- `packages/shared` for shared cross-app code
- `infra/nginx` for reverse proxy configuration
- `docker/` for compose and image definitions

## 📂 Project Structure

```plaintext
dealopia-monorepo/
├── apps/
│   ├── api/                 # Django backend
│   └── client/              # React + Vite frontend
├── packages/
│   └── shared/              # Shared JS utilities/types/config
├── infra/
│   └── nginx/
│       ├── default.conf
│       └── Dockerfile
├── docker/
│   ├── api.Dockerfile
│   ├── client.Dockerfile
│   └── docker-compose.yml
├── pyproject.toml
├── package.json
└── Makefile
```

## 🛠️ Tooling Choices

- **Backend package manager:** `uv`
- **Frontend package manager/runtime:** `bun`
- **API framework:** Django + DRF
- **Frontend framework:** React + Vite
- **Reverse proxy:** Nginx

## 🚦 Getting Started

### 1) Bootstrap everything

```bash
make bootstrap
```

### 2) Run API locally

```bash
make api-dev
```

### 3) Run Client locally

```bash
make client-dev
```

### 4) Run full stack with Docker Compose

```bash
make compose-up
```

## 🧪 Testing

```bash
make test
```

## 🌐 Reverse Proxy (Nginx)

Nginx routes:
- `/api/` and `/admin/` -> Django API upstream
- `/static/` and `/media/` -> served as static aliases
- `/` -> client app upstream
