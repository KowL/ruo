import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  channel: string;
  data?: any;
  symbol?: string;
  timestamp?: string;
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onAlert?: (alert: any) => void;
  onPriceUpdate?: (symbol: string, data: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  reconnectAttempts?: number;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onAlert,
    onPriceUpdate,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    reconnectAttempts = 5
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const subscribedSymbolsRef = useRef<Set<string>>(new Set());

  const getWsUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.REACT_APP_WS_HOST || window.location.host;
    return `${protocol}//${host}/ws`;
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = getWsUrl();
      console.log('Connecting to WebSocket:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectCountRef.current = 0;
        
        if (subscribedSymbolsRef.current.size > 0) {
          ws.send(JSON.stringify({
            action: 'subscribe',
            symbols: Array.from(subscribedSymbolsRef.current)
          }));
        }
        
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          switch (message.channel) {
            case 'alert':
              onAlert?.(message.data);
              break;
            case 'price':
              if (message.symbol && message.data) {
                onPriceUpdate?.(message.symbol, message.data);
              }
              break;
          }
          
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        onDisconnect?.();
        
        if (reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++;
          console.log(`Reconnecting... (${reconnectCountRef.current}/${reconnectAttempts})`);
          reconnectTimerRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [getWsUrl, onMessage, onAlert, onPriceUpdate, onConnect, onDisconnect, onError, reconnectInterval, reconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  const subscribe = useCallback((symbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        symbols
      }));
    }
    symbols.forEach(symbol => subscribedSymbolsRef.current.add(symbol));
  }, []);

  const unsubscribe = useCallback((symbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        symbols
      }));
    }
    symbols.forEach(symbol => subscribedSymbolsRef.current.delete(symbol));
  }, []);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'ping',
        timestamp: Date.now()
      }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  useEffect(() => {
    if (!isConnected) return;
    const heartbeatInterval = setInterval(sendPing, 30000);
    return () => clearInterval(heartbeatInterval);
  }, [isConnected, sendPing]);

  return {
    isConnected,
    lastMessage,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendPing
  };
}

export default useWebSocket;
