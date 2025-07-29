import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketMessage } from '../types';

interface UseWebSocketProps {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export const useWebSocket = ({ onMessage, onConnect, onDisconnect }: UseWebSocketProps = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pingIntervalRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isReconnectingRef = useRef(false);
  const isMountedRef = useRef(false);
  
  const maxReconnectAttempts = 10;
  const baseReconnectDelay = 1000; // 1 секунда

  const connectWebSocket = useCallback(() => {
    if (!isMountedRef.current) return;
    
    if (isReconnectingRef.current && wsRef.current?.readyState === WebSocket.CONNECTING) {
      return; // Уже подключаемся
    }

    // Закрываем существующее соединение если есть
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close(1000, 'Reconnecting');
    }

    isReconnectingRef.current = true;
    
    try {
      // Определяем WebSocket URL
      let wsUrl: string;
      
      // В development режиме Vite проксирует запросы к /api через свой dev server
      // В production нужно будет настроить nginx или другой reverse proxy
      const isProduction = import.meta.env.PROD;
      
      if (isProduction) {
        // В production используем тот же хост что и фронтенд
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${protocol}//${window.location.host}/api/v1/ws/dashboard`;
      } else {
        // В development используем WebSocket через Vite proxy
        // Vite автоматически проксирует ws:// запросы к /api
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${protocol}//${window.location.host}/api/v1/ws/dashboard`;
      }
      
      console.log('WebSocket URL:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.onopen = () => {
        if (!isMountedRef.current) return;
        
        console.log('WebSocket: Подключение установлено');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        isReconnectingRef.current = false;
        onConnect?.();
        
        // Отправляем начальное сообщение подключения
        console.log('WebSocket: Отправляем сообщение подключения');
        ws.send(JSON.stringify({ type: 'connect', timestamp: Date.now() }));
        
        // Очищаем предыдущий ping интервал если есть
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }
        
        // Отправляем ping каждые 30 секунд для поддержания соединения
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket: Отправляем ping');
            ws.send(JSON.stringify({ type: 'ping' }));
          } else {
            if (pingIntervalRef.current) {
              clearInterval(pingIntervalRef.current);
              pingIntervalRef.current = null;
            }
          }
        }, 30000);
      };

      ws.onclose = (event) => {
        if (!isMountedRef.current) return;
        
        console.log('WebSocket: Соединение закрыто', event.code, event.reason);
        setIsConnected(false);
        isReconnectingRef.current = false;
        
        // Очищаем ping интервал
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        
        onDisconnect?.();
        
        // Только переподключаемся если закрытие не было преднамеренным
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current), 30000);
          console.log(`WebSocket переподключение через ${delay}ms (попытка ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connectWebSocket();
          }, delay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error('Достигнуто максимальное количество попыток переподключения WebSocket');
        }
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;
        
        console.log('WebSocket: Получено сообщение', event.data);
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket: Распарсенное сообщение', message);
          
          // Обрабатываем системные сообщения
          if (message.type === 'welcome') {
            console.log('WebSocket: Получено приветственное сообщение');
          } else if (message.type === 'pong') {
            console.log('WebSocket: Получен pong');
          } else if (message.type === 'connected') {
            console.log('WebSocket: Подтверждение подключения получено');
          } else {
            // Передаем другие сообщения в обработчик
            onMessage?.(message);
          }
        } catch (error) {
          console.error('Ошибка парсинга WebSocket сообщения:', error);
        }
      };

      ws.onerror = (error) => {
        if (!isMountedRef.current) return;
        
        console.error('WebSocket ошибка:', error);
        isReconnectingRef.current = false;
      };
      
    } catch (error) {
      console.error('Ошибка создания WebSocket:', error);
      isReconnectingRef.current = false;
    }
  }, [onMessage, onConnect, onDisconnect]);

  useEffect(() => {
    isMountedRef.current = true;
    connectWebSocket();

    return () => {
      isMountedRef.current = false;
      
      // Отменяем таймер переподключения
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      
      // Очищаем ping интервал
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
      
      // Закрываем соединение
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close(1000, 'Component unmounting');
        wsRef.current = null;
      }
    };
  }, [connectWebSocket]);

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