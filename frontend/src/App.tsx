import React, { useState, useEffect, useCallback } from 'react';
import { ClientList } from './components/ClientList';
import { ChatWindow } from './components/ChatWindow';
import { ClientCard } from './components/ClientCard';
import { useWebSocket } from './hooks/useWebSocket';
import { clientsApi, messagesApi } from './services/api';
import { Client, Message, WebSocketMessage } from './types';

function App() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);

  // WebSocket обработчики
  const handleWebSocketMessage = useCallback((wsMessage: WebSocketMessage) => {
    console.log('WebSocket message:', wsMessage);
    
    if (wsMessage.type === 'new_message') {
      // Обновляем сообщения и список клиентов
      loadClients();
      if (selectedClient && wsMessage.data.client_id === selectedClient.id) {
        loadMessages(selectedClient.id);
      }
    } else if (wsMessage.type === 'dossier_update') {
      // Обновляем досье клиента
      if (selectedClient && wsMessage.client_id === selectedClient.id) {
        loadClients(); // Перезагружаем клиентов чтобы получить обновленное досье
      }
    }
  }, [selectedClient]);

  const { isConnected } = useWebSocket({
    onMessage: handleWebSocketMessage,
    onConnect: () => setWsConnected(true),
    onDisconnect: () => setWsConnected(false),
  });

  // Загрузка клиентов
  const loadClients = async () => {
    try {
      const response = await clientsApi.getAll();
      setClients(response.data);
    } catch (error) {
      console.error('Ошибка загрузки клиентов:', error);
    }
  };

  // Загрузка сообщений для клиента
  const loadMessages = async (clientId: number) => {
    try {
      const response = await messagesApi.getByClient(clientId);
      setMessages(response.data.reverse()); // Разворачиваем для правильного порядка
    } catch (error) {
      console.error('Ошибка загрузки сообщений:', error);
    }
  };

  // Отправка сообщения
  const handleSendMessage = async (content: string, contentType: string) => {
    if (!selectedClient) return;

    try {
      const newMessage = await messagesApi.create({
        client_id: selectedClient.id,
        sender: 'farmer',
        content_type: contentType,
        content: content,
      });

      // Обновляем локальное состояние
      setMessages(prev => [...prev, newMessage.data]);
      
      // Обновляем список клиентов
      await loadClients();
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error);
    }
  };

  // Выбор клиента
  const handleClientSelect = async (client: Client) => {
    setSelectedClient(client);
    await loadMessages(client.id);
  };

  // Инициализация
  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await loadClients();
      setLoading(false);
    };

    init();
  }, []);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-100 flex">
      {/* Левая колонка - Список диалогов */}
      <div className="w-80 bg-white border-r border-gray-200">
        <ClientList
          clients={clients}
          selectedClientId={selectedClient?.id}
          onClientSelect={handleClientSelect}
        />
      </div>

      {/* Центральная колонка - Окно чата */}
      <div className="flex-1 bg-white">
        <ChatWindow
          client={selectedClient}
          messages={messages}
          onSendMessage={handleSendMessage}
        />
      </div>

      {/* Правая колонка - Карточка клиента */}
      <div className="w-96 bg-gray-50 border-l border-gray-200">
        <ClientCard client={selectedClient} />
      </div>

      {/* Индикатор WebSocket соединения */}
      <div className="fixed bottom-4 right-4">
        <div
          className={`px-3 py-1 rounded-full text-xs font-medium ${
            isConnected
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}
        >
          {isConnected ? 'Онлайн' : 'Офлайн'}
        </div>
      </div>
    </div>
  );
}

export default App;