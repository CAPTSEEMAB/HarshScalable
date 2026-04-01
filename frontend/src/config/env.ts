

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

  const mode = (import.meta as any).env?.MODE || 'production';
  const isDev = mode === 'development';

  const awsApiBase = 'https:

  if (isDev) {
    
    return {
      api_base: awsApiBase,
      auth_service: `${awsApiBase}/auth`,
      product_service: `${awsApiBase}/products`,
      inventory_service: `${awsApiBase}/inventory`,
      transaction_service: `${awsApiBase}/transactions`,
      analytics_service: `${awsApiBase}/analytics`,
      resource_service: `${awsApiBase}/resources`,
      notification_service: `${awsApiBase}/notifications`,
      environment: 'development',
      debug: true,
    };
  }

  const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'https:
  
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
  }
