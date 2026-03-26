import { useEffect, useState } from 'react';
import { inventoryAPI, productsAPI, warehousesAPI } from '../services/api';
import { ArrowDownToLine, ArrowUpFromLine, ArrowLeftRight } from 'lucide-react';

interface InventoryItem {
  inventory_id: string;
  product_id: string;
  warehouse_id: string;
  quantity: number;
}

interface Product { product_id: string; name: string; sku: string; }
interface Warehouse { warehouse_id: string; name: string; }

type StockAction = 'in' | 'out' | 'transfer';

export default function InventoryPage() {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<StockAction | null>(null);
  const [form, setForm] = useState({ product_id: '', warehouse_id: '', to_warehouse_id: '', quantity: '' });
  const [message, setMessage] = useState('');

  const loadData = () => {
    Promise.all([inventoryAPI.list(), productsAPI.list(), warehousesAPI.list()])
      .then(([iRes, pRes, wRes]) => {
        setInventory(iRes.data.inventory || []);
        setProducts(pRes.data.products || []);
        setWarehouses(wRes.data.warehouses || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadData(); }, []);

  const productName = (id: string) => products.find((p) => p.product_id === id)?.name || id.slice(0, 8);
  const warehouseName = (id: string) => warehouses.find((w) => w.warehouse_id === id)?.name || id.slice(0, 8);

  const handleSubmit = async () => {
    setMessage('');
    try {
      const qty = parseInt(form.quantity);
      if (action === 'in') {
        await inventoryAPI.stockIn({ product_id: form.product_id, warehouse_id: form.warehouse_id, quantity: qty });
        setMessage('Stock added successfully');
      } else if (action === 'out') {
        await inventoryAPI.stockOut({ product_id: form.product_id, warehouse_id: form.warehouse_id, quantity: qty });
        setMessage('Stock removed successfully');
      } else if (action === 'transfer') {
        await inventoryAPI.transfer({ product_id: form.product_id, from_warehouse_id: form.warehouse_id, to_warehouse_id: form.to_warehouse_id, quantity: qty });
        setMessage('Stock transferred successfully');
      }
      setAction(null);
      setForm({ product_id: '', warehouse_id: '', to_warehouse_id: '', quantity: '' });
      loadData();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Operation failed';
      setMessage(msg);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Inventory</h2>
        <div className="flex gap-2">
          <button onClick={() => setAction('in')} className="flex items-center gap-1 bg-green-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-green-700">
            <ArrowDownToLine size={16} /> Stock In
          </button>
          <button onClick={() => setAction('out')} className="flex items-center gap-1 bg-red-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-red-700">
            <ArrowUpFromLine size={16} /> Stock Out
          </button>
          <button onClick={() => setAction('transfer')} className="flex items-center gap-1 bg-purple-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-purple-700">
            <ArrowLeftRight size={16} /> Transfer
          </button>
        </div>
      </div>

      {message && <div className="bg-blue-50 text-blue-700 p-3 rounded-lg mb-4 text-sm">{message}</div>}

      {action && (
        <div className="bg-white rounded-xl border p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4 capitalize">Stock {action}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <select value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })} className="px-4 py-2 border rounded-lg">
              <option value="">Select Product</option>
              {products.map((p) => <option key={p.product_id} value={p.product_id}>{p.name} ({p.sku})</option>)}
            </select>
            <select value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })} className="px-4 py-2 border rounded-lg">
              <option value="">{action === 'transfer' ? 'From Warehouse' : 'Select Warehouse'}</option>
              {warehouses.map((w) => <option key={w.warehouse_id} value={w.warehouse_id}>{w.name}</option>)}
            </select>
            {action === 'transfer' && (
              <select value={form.to_warehouse_id} onChange={(e) => setForm({ ...form, to_warehouse_id: e.target.value })} className="px-4 py-2 border rounded-lg">
                <option value="">To Warehouse</option>
                {warehouses.filter((w) => w.warehouse_id !== form.warehouse_id).map((w) => <option key={w.warehouse_id} value={w.warehouse_id}>{w.name}</option>)}
              </select>
            )}
            <input type="number" placeholder="Quantity" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} className="px-4 py-2 border rounded-lg" min="1" />
          </div>
          <div className="mt-4 flex gap-2">
            <button onClick={handleSubmit} className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">Confirm</button>
            <button onClick={() => setAction(null)} className="bg-gray-200 px-4 py-2 rounded-lg hover:bg-gray-300">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Product</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Warehouse</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Quantity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {inventory.map((item) => (
              <tr key={item.inventory_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium">{productName(item.product_id)}</td>
                <td className="px-4 py-3 text-sm">{warehouseName(item.warehouse_id)}</td>
                <td className="px-4 py-3 text-sm text-right font-mono">{item.quantity}</td>
              </tr>
            ))}
            {inventory.length === 0 && (
              <tr><td colSpan={3} className="text-center py-8 text-gray-400">No inventory records</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
