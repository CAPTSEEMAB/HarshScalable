import { useEffect, useState } from 'react';
import { resourcesAPI } from '../services/api';
import { Search, Star, BookOpen, Truck } from 'lucide-react';

interface Supplier { supplier_id: string; name: string; categories: string[]; rating: number; lead_time_days: number; region: string; contact_email: string; }
interface Guide { guide_id: string; title: string; summary: string; category: string; url: string; }

export default function ResourcesPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [guides, setGuides] = useState<Guide[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Supplier[]>([]);
  const [tab, setTab] = useState<'suppliers' | 'guides' | 'search'>('suppliers');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([resourcesAPI.suppliers(), resourcesAPI.restockGuides()])
      .then(([sRes, gRes]) => {
        setSuppliers(sRes.data.suppliers || []);
        setGuides(gRes.data.guides || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    const res = await resourcesAPI.vendorSearch(searchQuery);
    setSearchResults(res.data.results || []);
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Resources & Recommendations</h2>

      <div className="flex gap-2 mb-6">
        {(['suppliers', 'guides', 'search'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === t ? 'bg-primary-600 text-white' : 'bg-white border hover:bg-gray-50'}`}>
            {t === 'suppliers' ? 'Suppliers' : t === 'guides' ? 'Restock Guides' : 'Vendor Search'}
          </button>
        ))}
      </div>

      {tab === 'suppliers' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {suppliers.map((s) => (
            <div key={s.supplier_id} className="bg-white rounded-xl border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-lg">{s.name}</h3>
                  <p className="text-sm text-gray-500">{s.region}</p>
                </div>
                <div className="flex items-center gap-1 text-yellow-500">
                  <Star size={14} fill="currentColor" /> <span className="text-sm font-medium">{s.rating}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mt-3">
                {s.categories.map((c) => (
                  <span key={c} className="text-xs bg-primary-50 text-primary-700 px-2 py-1 rounded-full">{c}</span>
                ))}
              </div>
              <div className="mt-3 text-sm text-gray-500 flex items-center gap-1">
                <Truck size={14} /> {s.lead_time_days} day lead time
              </div>
              <p className="mt-2 text-xs text-gray-400">{s.contact_email}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'guides' && (
        <div className="space-y-4">
          {guides.map((g) => (
            <div key={g.guide_id} className="bg-white rounded-xl border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-3">
                <BookOpen size={20} className="text-primary-500 mt-1" />
                <div>
                  <h3 className="font-semibold">{g.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{g.summary}</p>
                  <span className="inline-block mt-2 text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">{g.category}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'search' && (
        <div>
          <div className="flex gap-2 mb-6">
            <div className="relative flex-1">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                placeholder="Search vendors by name, category, or region..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full pl-10 pr-4 py-2 border rounded-lg"
              />
            </div>
            <button onClick={handleSearch} className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">Search</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {searchResults.map((s) => (
              <div key={s.supplier_id} className="bg-white rounded-xl border p-6">
                <h3 className="font-semibold">{s.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{s.region} · {s.lead_time_days}d lead · {s.rating}/5</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {s.categories.map((c) => (
                    <span key={c} className="text-xs bg-gray-100 px-2 py-1 rounded-full">{c}</span>
                  ))}
                </div>
              </div>
            ))}
            {searchResults.length === 0 && searchQuery && <p className="text-gray-400 col-span-full text-center py-8">No results found</p>}
          </div>
        </div>
      )}
    </div>
  );
}
