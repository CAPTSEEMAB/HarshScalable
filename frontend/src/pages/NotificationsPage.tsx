import { useState, useEffect } from 'react';
import { Bell, AlertCircle, Info, CheckCircle, ExternalLink } from 'lucide-react';
import { notificationsAPI } from '../services/api';

interface Notification {
  notification_id: string;
  type: 'warning' | 'info' | 'success' | 'error';
  subject: string;
  message: string;
  status: 'read' | 'unread';
  timestamp: string;
  action_url?: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        setLoading(true);
        const response = await notificationsAPI.list();
        setNotifications(response.data.notifications || []);
        setError(null);
      } catch (err) {
                setError('Failed to load notifications');
      } finally {
        setLoading(false);
      }
    };

    fetchNotifications();
  }, []);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <AlertCircle size={18} className="text-yellow-500" />;
      case 'success':
        return <CheckCircle size={18} className="text-green-500" />;
      case 'info':
        return <Info size={18} className="text-blue-500" />;
      case 'error':
        return <AlertCircle size={18} className="text-red-500" />;
      default:
        return <Bell size={18} className="text-gray-500" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'warning':
        return 'bg-yellow-50 border-l-4 border-yellow-400';
      case 'success':
        return 'bg-green-50 border-l-4 border-green-400';
      case 'info':
        return 'bg-blue-50 border-l-4 border-blue-400';
      case 'error':
        return 'bg-red-50 border-l-4 border-red-400';
      default:
        return 'bg-gray-50 border-l-4 border-gray-400';
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Notifications</h2>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl border">
        {loading ? (
          <div className="flex justify-center items-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <Bell size={48} strokeWidth={1} />
            <p className="mt-4 font-medium">No notifications yet</p>
            <p className="text-sm mt-1">Low-stock alerts and reorder reminders will appear here</p>
          </div>
        ) : (
          <div className="divide-y">
            {notifications.map((n) => (
              <div
                key={n.notification_id}
                className={`p-4 hover:bg-opacity-75 transition ${getTypeColor(n.type)} ${
                  n.status === 'unread' ? 'font-medium' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    {getTypeIcon(n.type)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-sm">{n.subject}</h4>
                        {n.status === 'unread' && (
                          <span className="inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 mt-1">{n.message}</p>
                      <p className="text-xs text-gray-400 mt-2">
                        {new Date(n.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  {n.action_url && (
                    <a
                      href={n.action_url}
                      className="ml-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition flex items-center gap-1 whitespace-nowrap"
                    >
                      View <ExternalLink size={12} />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
