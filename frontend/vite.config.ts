import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    define: {
      // Make env variables available in the app
      __ENV__: JSON.stringify(env),
    },
    server: {
      port: 5173,
      // Development proxy configuration for local services
      proxy: {
        '/api/v1/auth': {
          target: process.env.VITE_AUTH_SERVICE || 'http://localhost:8001',
          changeOrigin: true,
        },
        '/api/v1/products': {
          target: process.env.VITE_PRODUCT_SERVICE || 'http://localhost:8002',
          changeOrigin: true,
        },
        '/api/v1/categories': {
          target: process.env.VITE_PRODUCT_SERVICE || 'http://localhost:8002',
          changeOrigin: true,
        },
        '/api/v1/inventory': {
          target: process.env.VITE_INVENTORY_SERVICE || 'http://localhost:8003',
          changeOrigin: true,
        },
        '/api/v1/warehouses': {
          target: process.env.VITE_INVENTORY_SERVICE || 'http://localhost:8003',
          changeOrigin: true,
        },
        '/api/v1/transactions': {
          target: process.env.VITE_TRANSACTION_SERVICE || 'http://localhost:8004',
          changeOrigin: true,
        },
        '/api/v1/analytics': {
          target: process.env.VITE_ANALYTICS_SERVICE || 'http://localhost:8005',
          changeOrigin: true,
        },
        '/api/v1/resources': {
          target: process.env.VITE_RESOURCE_SERVICE || 'http://localhost:8006',
          changeOrigin: true,
        },
        '/api/v1/notifications': {
          target: process.env.VITE_NOTIFICATION_SERVICE || 'http://localhost:8007',
          changeOrigin: true,
        },
      },
    },
    build: {
      // Production optimizations
      target: 'es2020',
      minify: 'terser',
      sourcemap: false,
    },
  };
});
