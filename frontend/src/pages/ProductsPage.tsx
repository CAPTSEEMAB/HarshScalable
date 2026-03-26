import { useEffect, useState } from 'react';
import { productsAPI, categoriesAPI } from '../services/api';
import { Plus, Trash2 } from 'lucide-react';

interface Product {
  product_id: string;
  sku: string;
  name: string;
  category_id: string;
  unit_price: number;
  reorder_threshold: number;
  description: string;
}

interface Category {
  category_id: string;
  name: string;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ sku: '', name: '', category_id: '', unit_price: '', reorder_threshold: '10', description: '' });
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    Promise.all([productsAPI.list(), categoriesAPI.list()])
      .then(([pRes, cRes]) => {
        setProducts(pRes.data.products || []);
        setCategories(cRes.data.categories || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadData(); }, []);

  const handleCreate = async () => {
    try {
      await productsAPI.create({
        ...form,
        unit_price: parseFloat(form.unit_price),
        reorder_threshold: parseInt(form.reorder_threshold),
      });
      setShowForm(false);
      setForm({ sku: '', name: '', category_id: '', unit_price: '', reorder_threshold: '10', description: '' });
      loadData();
    } catch (err) { console.error(err); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this product?')) return;
    await productsAPI.delete(id);
    loadData();
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Products</h2>
        <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
          <Plus size={18} /> Add Product
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">New Product</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input placeholder="SKU" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} className="px-4 py-2 border rounded-lg" />
            <input placeholder="Product Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="px-4 py-2 border rounded-lg" />
            <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} className="px-4 py-2 border rounded-lg">
              <option value="">Select Category</option>
              {categories.map((c) => <option key={c.category_id} value={c.category_id}>{c.name}</option>)}
            </select>
            <input placeholder="Unit Price" type="number" step="0.01" value={form.unit_price} onChange={(e) => setForm({ ...form, unit_price: e.target.value })} className="px-4 py-2 border rounded-lg" />
            <input placeholder="Reorder Threshold" type="number" value={form.reorder_threshold} onChange={(e) => setForm({ ...form, reorder_threshold: e.target.value })} className="px-4 py-2 border rounded-lg" />
            <input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="px-4 py-2 border rounded-lg" />
          </div>
          <div className="mt-4 flex gap-2">
            <button onClick={handleCreate} className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">Create</button>
            <button onClick={() => setShowForm(false)} className="bg-gray-200 px-4 py-2 rounded-lg hover:bg-gray-300">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">SKU</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Name</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Price</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Reorder At</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {products.map((p) => (
              <tr key={p.product_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-mono">{p.sku}</td>
                <td className="px-4 py-3 text-sm font-medium">{p.name}</td>
                <td className="px-4 py-3 text-sm">£{Number(p.unit_price).toFixed(2)}</td>
                <td className="px-4 py-3 text-sm">{p.reorder_threshold}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => handleDelete(p.product_id)} className="text-red-500 hover:text-red-700 p-1">
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
            {products.length === 0 && (
              <tr><td colSpan={5} className="text-center py-8 text-gray-400">No products yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
