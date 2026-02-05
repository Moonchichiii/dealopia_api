# Repository standards

## Monorepo architecture (Turborepo-style)

- `apps/api`: Django backend service.
- `apps/client`: React/Vite frontend app.
- `packages/shared`: shared frontend/backend JS modules.
- `infra/nginx`: reverse-proxy and edge configuration.
- `docker`: image definitions and compose orchestration.

## Naming conventions

- JS/TS folders: `kebab-case`
- React components: `PascalCase`
- Python modules/packages: `snake_case`
- Environment files: `.env.<environment>`

## Tooling standards

- Python dependency and metadata are managed in `pyproject.toml` and installed via `uv`.
- JavaScript workspaces are managed via `bun` with root `workspaces`.
- CI validates API and client independently before image build.

## Frontend architecture standard

Use Feature-Sliced Design baseline in `apps/client/src`:
- `entities/`
- `features/`
- `shared/`

## Infrastructure standard

- Nginx must terminate edge traffic and route API/admin/client paths.
- Compose manifests should live in `docker/`.
