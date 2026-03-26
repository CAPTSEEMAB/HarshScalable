import { useEffect, useState } from 'react';
import { transactionsAPI } from '../services/api';

interface Transaction {
  transaction_id: string;
  type: string;
  product_id: string;
  warehouse_id: string;
  quantity: number;
  total_price: number;
  timestamp: string;
}

const TYPE_COLORS: Record<string, string> = {
  PURCHASE: 'bg-blue-100 text-blue-700',
  SALE: 'bg-green-100 text-green-700',
  RETURN: 'bg-yellow-100 text-yellow-700',
  DAMAGE: 'bg-red-100 text-red-700',
};

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    const params = filter ? { type: filter as string } : undefined;
    transactionsAPI.history(params)
      .then((res) => setTransactions(res.data.transactions || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filter]);

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Transactions</h2>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} className="px-4 py-2 border rounded-lg">
          <option value="">All Types</option>
          <option value="PURCHASE">Purchases</option>
          <option value="SALE">Sales</option>
          <option value="RETURN">Returns</option>
          <option value="DAMAGE">Damages</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Type</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Product ID</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Quantity</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Total</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {transactions.map((tx) => (
              <tr key={tx.transaction_id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${TYPE_COLORS[tx.type] || 'bg-gray-100'}`}>
                    {tx.type}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm font-mono">{tx.product_id.slice(0, 8)}...</td>
                <td className="px-4 py-3 text-sm text-right">{tx.quantity}</td>
                <td className="px-4 py-3 text-sm text-right">£{Number(tx.total_price).toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{new Date(tx.timestamp).toLocaleString()}</td>
              </tr>
            ))}
            {transactions.length === 0 && (
              <tr><td colSpan={5} className="text-center py-8 text-gray-400">No transactions yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
