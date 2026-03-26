import { useEffect, useState } from 'react';
import { analyticsAPI } from '../services/api';
import { AlertTriangle, BarChart3, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface LowStockItem { product_id: string; product_name: string; warehouse_id: string; current_quantity: number; reorder_threshold: number; deficit: number; }
interface Recommendation { product_id: string; product_name: string; warehouse_id: string; current_quantity: number; recommended_order_qty: number; urgency: string; days_until_stockout: number; }
interface ForecastDay { date: string; predicted_demand: number; }
interface ForecastResult { product_name: string; forecast: { daily_forecast: ForecastDay[]; confidence: string; method: string; total_predicted_demand: number; }; }

export default function AnalyticsPage() {
  const [lowStock, setLowStock] = useState<LowStockItem[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [forecastProductId, setForecastProductId] = useState('');
  const [tab, setTab] = useState<'low-stock' | 'reorder' | 'forecast'>('low-stock');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([analyticsAPI.lowStock(), analyticsAPI.reorderRecommendations()])
      .then(([lsRes, rrRes]) => {
        setLowStock(lsRes.data.low_stock_items || []);
        setRecommendations(rrRes.data.recommendations || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const loadForecast = async () => {
    if (!forecastProductId) return;
    try {
      const res = await analyticsAPI.forecast(forecastProductId, 14);
      setForecast(res.data);
    } catch (err) { console.error(err); }
  };

  const urgencyColor = (u: string) => {
    const map: Record<string, string> = { critical: 'bg-red-100 text-red-700', high: 'bg-orange-100 text-orange-700', moderate: 'bg-yellow-100 text-yellow-700', low: 'bg-green-100 text-green-700' };
    return map[u] || 'bg-gray-100';
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Analytics & Forecasting</h2>

      <div className="flex gap-2 mb-6">
        {(['low-stock', 'reorder', 'forecast'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === t ? 'bg-primary-600 text-white' : 'bg-white border hover:bg-gray-50'}`}>
            {t === 'low-stock' ? 'Low Stock' : t === 'reorder' ? 'Reorder Recs' : 'Forecast'}
          </button>
        ))}
      </div>

      {tab === 'low-stock' && (
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="p-4 border-b flex items-center gap-2">
            <AlertTriangle size={18} className="text-red-500" />
            <h3 className="font-semibold">Low Stock Alerts ({lowStock.length})</h3>
          </div>
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Product</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Current</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Threshold</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Deficit</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {lowStock.map((item, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">{item.product_name}</td>
                  <td className="px-4 py-3 text-sm text-right font-mono text-red-600">{item.current_quantity}</td>
                  <td className="px-4 py-3 text-sm text-right">{item.reorder_threshold}</td>
                  <td className="px-4 py-3 text-sm text-right font-bold text-red-600">-{item.deficit}</td>
                </tr>
              ))}
              {lowStock.length === 0 && <tr><td colSpan={4} className="text-center py-8 text-gray-400">No low stock items</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'reorder' && (
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="p-4 border-b flex items-center gap-2">
            <RefreshCw size={18} className="text-primary-500" />
            <h3 className="font-semibold">Reorder Recommendations ({recommendations.length})</h3>
          </div>
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Product</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Stock</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Order Qty</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Days Left</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Urgency</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {recommendations.map((r, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">{r.product_name}</td>
                  <td className="px-4 py-3 text-sm text-right">{r.current_quantity}</td>
                  <td className="px-4 py-3 text-sm text-right font-bold">{r.recommended_order_qty}</td>
                  <td className="px-4 py-3 text-sm text-right">{r.days_until_stockout}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${urgencyColor(r.urgency)}`}>{r.urgency}</span>
                  </td>
                </tr>
              ))}
              {recommendations.length === 0 && <tr><td colSpan={5} className="text-center py-8 text-gray-400">No recommendations</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'forecast' && (
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={18} className="text-primary-500" />
            <h3 className="font-semibold">Demand Forecast</h3>
          </div>
          <div className="flex gap-2 mb-6">
            <input placeholder="Product ID" value={forecastProductId} onChange={(e) => setForecastProductId(e.target.value)} className="px-4 py-2 border rounded-lg flex-1" />
            <button onClick={loadForecast} className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">Forecast</button>
          </div>
          {forecast && (
            <div>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-500">Product</p>
                  <p className="font-semibold">{forecast.product_name}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-500">Total Predicted</p>
                  <p className="font-semibold">{forecast.forecast.total_predicted_demand} units</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-500">Confidence</p>
                  <p className="font-semibold capitalize">{forecast.forecast.confidence} ({forecast.forecast.method})</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={forecast.forecast.daily_forecast}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="predicted_demand" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          {!forecast && <p className="text-gray-400 text-center py-12">Enter a product ID and click Forecast</p>}
        </div>
      )}
    </div>
  );
}
