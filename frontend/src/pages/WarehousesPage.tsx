import { useEffect, useState } from 'react';
import { warehousesAPI } from '../services/api';
import { Plus, Trash2, MapPin } from 'lucide-react';

interface Warehouse {
  warehouse_id: string;
  name: string;
  location: string;
  manager_id: string;
  created_at: string;
}

export default function WarehousesPage() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', location: '' });
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    warehousesAPI.list()
      .then((res) => setWarehouses(res.data.warehouses || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadData(); }, []);

  const handleCreate = async () => {
    await warehousesAPI.create(form);
    setShowForm(false);
    setForm({ name: '', location: '' });
    loadData();
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this warehouse?')) return;
    await warehousesAPI.delete(id);
    loadData();
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Warehouses</h2>
        <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
          <Plus size={18} /> Add Warehouse
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">New Warehouse</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input placeholder="Warehouse Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="px-4 py-2 border rounded-lg" />
            <input placeholder="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} className="px-4 py-2 border rounded-lg" />
          </div>
          <div className="mt-4 flex gap-2">
            <button onClick={handleCreate} className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">Create</button>
            <button onClick={() => setShowForm(false)} className="bg-gray-200 px-4 py-2 rounded-lg hover:bg-gray-300">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {warehouses.map((w) => (
          <div key={w.warehouse_id} className="bg-white rounded-xl border p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold">{w.name}</h3>
                <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                  <MapPin size={14} /> {w.location}
                </p>
              </div>
              <button onClick={() => handleDelete(w.warehouse_id)} className="text-red-500 hover:text-red-700 p-1">
                <Trash2 size={16} />
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-3">ID: {w.warehouse_id.slice(0, 8)}...</p>
          </div>
        ))}
        {warehouses.length === 0 && (
          <div className="col-span-full text-center py-12 text-gray-400">No warehouses yet</div>
        )}
      </div>
    </div>
  );
}
