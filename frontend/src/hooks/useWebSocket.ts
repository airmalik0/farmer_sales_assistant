import { useEffect, useRef, useState } from 'react';
import { WebSocketMessage } from '../types';

interface UseWebSocketProps {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export const useWebSocket = ({ onMessage, onConnect, onDisconnect }: UseWebSocketProps = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Подключаемся к WebSocket серверу FastAPI
    const wsUrl = 'ws://localhost:8000/api/v1/ws/dashboard';
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      setIsConnected(true);
      onConnect?.();
    };

    ws.onclose = () => {
      setIsConnected(false);
      onDisconnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        onMessage?.(message);
      } catch (error) {
        console.error('Ошибка парсинга WebSocket сообщения:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket ошибка:', error);
    };

    return () => {
      ws.close();
    };
  }, [onMessage, onConnect, onDisconnect]);

  const sendMessage = (message: any) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  return {
    isConnected,
    sendMessage,
  };
};