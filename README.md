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
# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config({
  extends: [
    // Remove ...tseslint.configs.recommended and replace with this
    ...tseslint.configs.recommendedTypeChecked,
    // Alternatively, use this for stricter rules
    ...tseslint.configs.strictTypeChecked,
    // Optionally, add this for stylistic rules
    ...tseslint.configs.stylisticTypeChecked,
  ],
  languageOptions: {
    // other options...
    parserOptions: {
      project: ['./tsconfig.node.json', './tsconfig.app.json'],
      tsconfigRootDir: import.meta.dirname,
    },
  },
})
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config({
  plugins: {
    // Add the react-x and react-dom plugins
    'react-x': reactX,
    'react-dom': reactDom,
  },
  rules: {
    // other rules...
    // Enable its recommended typescript rules
    ...reactX.configs['recommended-typescript'].rules,
    ...reactDom.configs.recommended.rules,
  },
})
```
