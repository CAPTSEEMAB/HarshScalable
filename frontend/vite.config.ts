import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    define: {
      
      __ENV__: JSON.stringify(env),
    },
    server: {
      port: 5173,
      
      proxy: {
        '/api/v1/auth': {
          target: process.env.VITE_AUTH_SERVICE || 'http:
          changeOrigin: true,
        },
        '/api/v1/products': {
          target: process.env.VITE_PRODUCT_SERVICE || 'http:
          changeOrigin: true,
        },
        '/api/v1/categories': {
          target: process.env.VITE_PRODUCT_SERVICE || 'http:
          changeOrigin: true,
        },
        '/api/v1/inventory': {
          target: process.env.VITE_INVENTORY_SERVICE || 'http:
          changeOrigin: true,
        },
        '/api/v1/warehouses': {
          target: process.env.VITE_INVENTORY_SERVICE || 'http:
          changeOrigin: true,
        },
        '/api/v1/transactions': {
          target: process.env.VITE_TRANSACTION_SERVICE || 'http:
          changeOrigin: true,
        },
        '/api/v1/analytics': {
          target: process.env.VITE_ANALYTICS_SERVICE || 'http:
          changeOrigin: true,
        },
        '/api/v1/resources': {
          target: process.env.VITE_RESOURCE_SERVICE || 'http:
          changeOrigin: true,
        },
        '/api/v1/notifications': {
          target: process.env.VITE_NOTIFICATION_SERVICE || 'http:
          changeOrigin: true,
        },
      },
    },
    build: {
      
      target: 'es2020',
      minify: 'terser',
      sourcemap: false,
    },
  };
});
