# Dealopia Monorepo

Full-stack monorepo for the Dealopia platform.

## Workspaces
- `apps/api`: Django + DRF backend
- `apps/client`: React + Vite frontend
- `packages/shared`: shared types/constants
- `infra/`: infrastructure assets (nginx, monitoring)
- `docker/`: container build and compose definitions

## Quick start
```bash
make bootstrap
make api-dev
make client-dev
```

## CI
GitHub Actions workflow is located at `.github/workflows/ci-cd.yml`.
