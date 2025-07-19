import { useEffect, useRef, useState, useCallback } from "react";

export function useLivePrices(symbols = []) {
  const [prices, setPrices] = useState({});
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [errors, setErrors] = useState({});
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (!symbols.length) {
      setConnectionStatus('idle');
      return;
    }

    const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const wsUrl = apiUrl.replace(/^http/, 'ws') + '/ws/realtime';
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      setConnectionStatus('connected');
      setErrors({});
      ws.send(JSON.stringify({ symbols }));
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.error) {
          setErrors(prev => ({ ...prev, general: data.error }));
          return;
        }
        if (data.updates) {
          const newPrices = {};
          const newErrors = {};
          data.updates.forEach(update => {
            if (update.error) {
              newErrors[update.symbol] = update.error;
            } else {
              newPrices[update.symbol] = {
                price: update.price,
                timestamp: update.timestamp,
                lastUpdate: new Date().toISOString()
              };
            }
          });
          setPrices(prev => ({ ...prev, ...newPrices }));
          setErrors(prev => ({ ...prev, ...newErrors }));
        }
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
    };
    
    ws.onclose = () => {
      setConnectionStatus('disconnected');
      // Auto-reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        if (symbols.length > 0) {
          connect();
        }
      }, 3000);
    };
  }, [symbols]);

  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    connect();
  }, [connect]);

  return {
    prices,
    connectionStatus,
    errors,
    reconnect
  };
}

export default useLivePrices;
