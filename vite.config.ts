import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';
import { VitePWA } from 'vite-plugin-pwa';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        cleanupOutdatedCaches: true,
        skipWaiting: true,
        clientsClaim: true,
        maximumFileSizeToCacheInBytes: 3_000_000,
      },
      manifest: {
        name: 'Dealopia',
        short_name: 'Dealopia',
        description: 'Modern local deals website',
        theme_color: '#6366f1',
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
    }),
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages'     : path.resolve(__dirname, './src/pages'),
      '@lib'       : path.resolve(__dirname, './src/lib'),
      '@api'       : path.resolve(__dirname, './src/api'),
      '@hooks'     : path.resolve(__dirname, './src/hooks'),
      '@types'     : path.resolve(__dirname, './src/types'),
      '@context'   : path.resolve(__dirname, './src/context'),
      '@utils'     : path.resolve(__dirname, './src/utils'),
    },
  },

  server: {
    port: 5173,
    strictPort: true,
    host: true,
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 5173,
      timeout: 30_000,
      clientPort: 5173,
      path: '/ws',
      overlay: true,
    },
    proxy: {
      '^/api/v1/.*': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        cookieDomainRewrite: 'localhost',
        cookiePathRewrite: '/',
        logLevel: 'info',
        configure: (proxy) => {
          proxy.on('error',  (err)       => console.error('[proxy] error', err));
          proxy.on('proxyReq', (req)     => console.log('[proxy] →', req.method, req.path));
          proxy.on('proxyRes', (res)     =>
            console.log('[proxy] ←', res.statusCode, res.req?.path));
        },
      },
      '^/(static|media|admin|accounts)/.*': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        logLevel: 'warn',
      },
    },
  },

  build: {
    target: 'esnext',
    minify: 'esbuild',
    cssMinify: 'lightningcss',
    reportCompressedSize: false,
    sourcemap: true,
    chunkSizeWarningLimit: 1000,
    assetsInlineLimit: 4096,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          query: [
            '@tanstack/react-query',
            '@tanstack/query-sync-storage-persister',
            '@tanstack/react-query-persist-client',
          ],
          forms: ['react-hook-form', 'zod'],
          ui: ['react-toastify', 'lucide-react', 'clsx', 'tailwind-merge'],
          cloud: ['@cloudinary/react', '@cloudinary/url-gen'],
          i18n: ['i18next', 'react-i18next', 'i18next-browser-languagedetector'],
        },
      },
    },
  },

  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'react-hook-form',
      'zod',
      'axios',
      'clsx',
      'tailwind-merge',
      '@cloudinary/react',
      '@cloudinary/url-gen',
    ],
  },

  preview: {
    port: 5173,
    strictPort: true,
    host: true,
  },
});
