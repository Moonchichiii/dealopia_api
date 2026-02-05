# Repository standards

## Monorepo layout

- `services/`: deployable backend services.
- `apps/`: product-facing applications (web/mobile).
- `packages/`: shared libraries consumed by services/apps.
- `docs/`: architecture and onboarding docs.
- `scripts/`: automation scripts used in local dev and CI.

## Naming conventions

- Python packages and modules use `snake_case`.
- Django apps use plural, descriptive names (`deals`, `shops`, `locations`).
- Environment files use `.env.<environment>` (example: `.env.development`).
- Root-level files use lowercase, hyphenated names unless required by tooling.

## Backend location

The Django backend source lives in `services/backend/`.
Run commands from the repository root with explicit paths, for example:

```bash
python services/backend/manage.py runserver
```

## Migration guideline for frontend integration

When adding the frontend repo into this monorepo:

1. Place it under `apps/web/`.
2. Move reusable UI helpers to `packages/ui/`.
3. Add shared API client code to `packages/api-client/`.
4. Keep deployment manifests in service/app directories, not repo root.
