# Repository standards

## 1) Monorepo layout

- `services/`: deployable services (backend/API, workers, etc.).
- `apps/`: user-facing applications (web/mobile/admin).
- `packages/`: reusable shared packages.
- `docs/`: ADRs, standards, architecture docs.
- `scripts/`: automation for setup, CI helpers, and release scripts.

### Current service/app mapping

- Backend API: `services/backend`
- Frontend app workspace: `apps/web`

## 2) Naming conventions

- Python modules/packages: `snake_case`
- JS/TS package names: scoped lowercase (for example `@dealopia/web`)
- Directories: lowercase with hyphen only when conventional for tooling
- Environment files: `.env.<environment>` (example: `.env.development`)

## 3) Tooling standards

- Python dependency metadata lives in `pyproject.toml`.
- JS workspaces are managed at the root via `pnpm-workspace.yaml`.
- Prefer repo-root commands to avoid path drift between local and CI.

## 4) Command standards

Use root-level commands:

```bash
# backend
python services/backend/manage.py runserver
PYTHONPATH=services/backend pytest

# frontend workspaces
pnpm install
pnpm dev
```

## 5) CI/CD standards

- CI must install from root and run backend and frontend checks independently.
- Service Docker contexts must point to each service directory.
- Avoid embedding environment-specific secrets in config files.

## 6) Growth guidelines

When adding new units:

1. New customer-facing app -> `apps/<app-name>`
2. New shared library -> `packages/<package-name>`
3. New deployable backend unit -> `services/<service-name>`
4. New standards/process docs -> `docs/`
