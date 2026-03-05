import React, { useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { AlertTriangle, Wifi, WifiOff } from 'lucide-react';

/**
 * 实时推送通知组件
 * 显示WebSocket连接状态和接收到的预警通知
 */
const RealtimeNotification: React.FC = () => {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [isFirstConnect, setIsFirstConnect] = useState(true);

  const { isConnected } = useWebSocket({
    onAlert: (alert) => {
      setAlerts(prev => [alert, ...prev].slice(0, 10));

      if (Notification.permission === 'granted') {
        new Notification('持仓预警', {
          body: `${alert.stock_name} (${alert.symbol}): ${alert.message}`,
          icon: '/favicon.ico'
        });
      }
    },
    onPriceUpdate: (_symbol, _data) => {
      // 价格更新回调
    },
    onConnect: () => {
      if (isFirstConnect) {
        setIsFirstConnect(false);
        if (Notification.permission === 'default') {
          Notification.requestPermission();
        }
      }
    }
  });

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {/* 连接状态指示器 */}
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg shadow-lg ${isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
        }`}>
        {isConnected ? <Wifi size={16} /> : <WifiOff size={16} />}
        <span className="text-sm font-medium">
          {isConnected ? '实时推送已连接' : '实时推送已断开'}
        </span>
      </div>

      {/* 预警通知列表 */}
      {alerts.length > 0 && (
        <div className="space-y-2 max-w-sm">
          {alerts.map((alert, index) => (
            <div
              key={index}
              className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 shadow-lg"
            >
              <div className="flex items-start gap-2">
                <AlertTriangle className="text-red-400 mt-0.5" size={16} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-red-300">
                    预警: {alert.stock_name} ({alert.symbol})
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {alert.message}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(alert.triggered_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RealtimeNotification;
