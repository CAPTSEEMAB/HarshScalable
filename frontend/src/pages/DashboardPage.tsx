import { useEffect, useState } from 'react';
import { analyticsAPI } from '../services/api';
import StatCard from '../components/StatCard';
import { Package, Warehouse, ArrowLeftRight, AlertTriangle, TrendingUp, DollarSign } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface DashboardData {
  total_products: number;
  total_warehouses: number;
  total_stock_units: number;
  total_transactions: number;
  total_sales_value: number;
  total_purchase_value: number;
  low_stock_alerts: number;
}

interface TopProduct {
  product_id: string;
  product_name: string;
  total_sold: number;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([analyticsAPI.dashboard(), analyticsAPI.topProducts(6)])
      .then(([dashRes, topRes]) => {
        setDashboard(dashRes.data);
        setTopProducts(topRes.data.top_products || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Products"
          value={dashboard?.total_products || 0}
          icon={<Package size={24} />}
          color="primary"
        />
        <StatCard
          title="Warehouses"
          value={dashboard?.total_warehouses || 0}
          icon={<Warehouse size={24} />}
          color="green"
        />
        <StatCard
          title="Total Stock Units"
          value={dashboard?.total_stock_units?.toLocaleString() || 0}
          icon={<ArrowLeftRight size={24} />}
          color="purple"
        />
        <StatCard
          title="Low Stock Alerts"
          value={dashboard?.low_stock_alerts || 0}
          icon={<AlertTriangle size={24} />}
          color="red"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <StatCard
          title="Total Sales Value"
          value={`£${(dashboard?.total_sales_value || 0).toLocaleString()}`}
          icon={<TrendingUp size={24} />}
          color="green"
        />
        <StatCard
          title="Total Purchase Value"
          value={`£${(dashboard?.total_purchase_value || 0).toLocaleString()}`}
          icon={<DollarSign size={24} />}
          color="yellow"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products Bar Chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Top Selling Products</h3>
          {topProducts.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topProducts}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="product_name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total_sold" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-12">No sales data yet</p>
          )}
        </div>

        {/* Top Products Pie Chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Sales Distribution</h3>
          {topProducts.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={topProducts}
                  dataKey="total_sold"
                  nameKey="product_name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ product_name }: TopProduct) => product_name}
                >
                  {topProducts.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-12">No sales data yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
