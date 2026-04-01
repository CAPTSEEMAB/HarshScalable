import axios from 'axios';
import { config } from '../config/env';

const API_BASE = config.api_base;

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', res.data.access_token);
          localStorage.setItem('refresh_token', res.data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(originalRequest);
        } catch {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

export const authAPI = {
  register: (data: { name: string; email: string; password: string; role?: string }) =>
    api.post('/auth/register', data),
  login: (data: { email: string; password: string }) => api.post('/auth/login', data),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data: { name?: string; email?: string }) => api.put('/auth/profile', data),
  deleteAccount: () => api.delete('/auth/account'),
};

export const productsAPI = {
  list: (categoryId?: string) =>
    api.get('/products', { params: categoryId ? { category_id: categoryId } : {} }),
  get: (id: string) => api.get(`/products/${id}`),
  create: (data: Record<string, unknown>) => api.post('/products', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/products/${id}`, data),
  delete: (id: string) => api.delete(`/products/${id}`),
};

export const categoriesAPI = {
  list: () => api.get('/categories'),
  create: (data: { name: string; description?: string }) => api.post('/categories', data),
  delete: (id: string) => api.delete(`/categories/${id}`),
};

export const inventoryAPI = {
  list: (warehouseId?: string) =>
    api.get('/inventory', { params: warehouseId ? { warehouse_id: warehouseId } : {} }),
  getByProduct: (productId: string) => api.get(`/inventory/${productId}`),
  stockIn: (data: { product_id: string; warehouse_id: string; quantity: number; notes?: string }) =>
    api.post('/inventory/stock-in', data),
  stockOut: (data: { product_id: string; warehouse_id: string; quantity: number; reason?: string; notes?: string }) =>
    api.post('/inventory/stock-out', data),
  transfer: (data: {
    product_id: string;
    from_warehouse_id: string;
    to_warehouse_id: string;
    quantity: number;
  }) => api.post('/inventory/transfer', data),
  history: (productId: string) => api.get(`/inventory/history/${productId}`),
};

export const warehousesAPI = {
  list: () => api.get('/warehouses'),
  get: (id: string) => api.get(`/warehouses/${id}`),
  create: (data: { name: string; location: string }) => api.post('/warehouses', data),
  delete: (id: string) => api.delete(`/warehouses/${id}`),
};

export const transactionsAPI = {
  purchase: (data: Record<string, unknown>) => api.post('/transactions/purchase', data),
  sale: (data: Record<string, unknown>) => api.post('/transactions/sale', data),
  return_: (data: Record<string, unknown>) => api.post('/transactions/return', data),
  damage: (data: Record<string, unknown>) => api.post('/transactions/damage', data),
  history: (params?: Record<string, string>) => api.get('/transactions/history', { params }),
  get: (id: string) => api.get(`/transactions/${id}`),
};

export const analyticsAPI = {
  dashboard: () => api.get('/analytics/dashboard'),
  lowStock: () => api.get('/analytics/low-stock'),
  topProducts: (limit?: number) => api.get('/analytics/top-products', { params: { limit } }),
  slowProducts: (limit?: number) => api.get('/analytics/slow-products', { params: { limit } }),
  warehousePerformance: () => api.get('/analytics/warehouse-performance'),
  reorderRecommendations: () => api.get('/analytics/reorder-recommendations'),
  forecast: (productId: string, days?: number) =>
    api.get(`/analytics/forecast/${productId}`, { params: { days } }),
};

export const resourcesAPI = {
  suppliers: (params?: Record<string, string>) => api.get('/resources/suppliers', { params }),
  recommendations: (category?: string) =>
    api.get('/resources/recommendations', { params: category ? { category } : {} }),
  restockGuides: (category?: string) =>
    api.get('/resources/restock-guides', { params: category ? { category } : {} }),
  vendorSearch: (q: string) => api.get('/resources/vendor-search', { params: { q } }),
};

export const notificationsAPI = {
  list: () => api.get('/notifications'),
  create: (data: { type: string; subject: string; message: string; action_url?: string }) =>
    api.post('/notifications', data),
};

export const externalAPI = {
  
  weather: (city?: string, warehouseId?: string) =>
    api.get('/external/weather', { params: { city, warehouse_id: warehouseId } }),

  currency: (base?: string, target?: string, amount?: number) =>
    api.get('/external/currency', { params: { base, target, amount } }),

  countries: (name?: string, region?: string) =>
    api.get('/external/countries', { params: { name, region } }),
};

export const batchAPI = {
  
  inventory: (operations: Array<{
    type: 'stock_in' | 'stock_out' | 'transfer';
    product_id: string;
    warehouse_id: string;
    quantity: number;
  }>) => api.post('/inventory/batch', { operations }),

  transactions: (transactions: Array<{
    type: 'sale' | 'purchase';
    product_id: string;
    quantity: number;
    unit_price: number;
  }>) => api.post('/transactions/batch', { transactions }),
};
