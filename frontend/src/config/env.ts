/**
 * Frontend Environment Configuration
 * Loads from .env file and provides API endpoints
 * Production-ready with environment-based routing
 */

interface EnvironmentConfig {
  api_base: string;
  auth_service: string;
  product_service: string;
  inventory_service: string;
  transaction_service: string;
  analytics_service: string;
  resource_service: string;
  notification_service: string;
  environment: 'development' | 'production';
  debug: boolean;
}

declare global {
  interface ImportMeta {
    readonly env: Record<string, string | undefined>;
  }
}

function getConfig(): EnvironmentConfig {
  // In development, use relative paths (proxied through Vite)
  // In production, use full API URLs from environment
  
  const mode = (import.meta as any).env?.MODE || 'production';
  const isDev = mode === 'development';

  if (isDev) {
    // Development: Vite proxies to localhost:800X
    return {
      api_base: '/api/v1',
      auth_service: '/api/v1/auth',
      product_service: '/api/v1/products',
      inventory_service: '/api/v1/inventory',
      transaction_service: '/api/v1/transactions',
      analytics_service: '/api/v1/analytics',
      resource_service: '/api/v1/resources',
      notification_service: '/api/v1/notifications',
      environment: 'development',
      debug: true,
    };
  }

  // Production: Use environment variables or defaults
  const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8001';
  
  return {
    api_base: apiBase,
    auth_service: (import.meta as any).env?.VITE_AUTH_SERVICE || `${apiBase}/auth`,
    product_service: (import.meta as any).env?.VITE_PRODUCT_SERVICE || `${apiBase}/products`,
    inventory_service: (import.meta as any).env?.VITE_INVENTORY_SERVICE || `${apiBase}/inventory`,
    transaction_service: (import.meta as any).env?.VITE_TRANSACTION_SERVICE || `${apiBase}/transactions`,
    analytics_service: (import.meta as any).env?.VITE_ANALYTICS_SERVICE || `${apiBase}/analytics`,
    resource_service: (import.meta as any).env?.VITE_RESOURCE_SERVICE || `${apiBase}/resources`,
    notification_service: (import.meta as any).env?.VITE_NOTIFICATION_SERVICE || `${apiBase}/notifications`,
    environment: 'production',
    debug: false,
  };
}

export const config = getConfig();

if (config.debug) {
  console.log('[Config]', config);
}
