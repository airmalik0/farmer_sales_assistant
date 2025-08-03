import { useState, useEffect, useCallback, useRef } from 'react';
import { ClientList } from './components/ClientList';
import { ChatWindow } from './components/ChatWindow';
import { ClientCard } from './components/ClientCard';
import { BroadcastModal } from './components/BroadcastModal';
import { useWebSocket } from './hooks/useWebSocket';
import { clientsApi, messagesApi, pactApi } from './services/api';
import { Client, Message, WebSocketMessage } from './types';

function App() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBroadcast, setShowBroadcast] = useState(false);

  // Используем ref для хранения selectedClient чтобы избежать пересоздания callback'ов
  const selectedClientRef = useRef<Client | undefined>();
  selectedClientRef.current = selectedClient;

  // WebSocket обработчики с стабильными ссылками
  const handleWebSocketMessage = useCallback((wsMessage: WebSocketMessage) => {
    console.log('WebSocket message:', wsMessage);
    
    if (wsMessage.type === 'new_message') {
      // Обновляем сообщения и список клиентов
      loadClients();
      const currentSelectedClient = selectedClientRef.current;
      if (currentSelectedClient && wsMessage.data.client_id === currentSelectedClient.id) {
        loadMessages(currentSelectedClient.id);
        
        // Обновляем selectedClient для актуальной статистики
        clientsApi.getById(currentSelectedClient.id).then(response => {
          setSelectedClient(response.data);
        }).catch(error => {
          console.error('Ошибка при получении обновленных данных клиента:', error);
        });
      }
    } else if (wsMessage.type === 'new_client') {
      // Новый клиент через Pact API
      console.log('Получен новый клиент через Pact:', wsMessage.data);
      loadClients();
    } else if (wsMessage.type === 'dossier_update') {
      console.log('Получено обновление досье для клиента:', wsMessage.client_id);
      
      // Обновляем досье в данных клиента напрямую из WebSocket сообщения
      if (wsMessage.data && wsMessage.client_id) {
        setClients(prevClients => 
          prevClients.map(client => 
            client.id === wsMessage.client_id
              ? { ...client, dossier: wsMessage.data }
              : client
          )
        );
        
        // Если обновленный клиент является выбранным, обновляем selectedClient
        const currentSelectedClient = selectedClientRef.current;
        if (currentSelectedClient && currentSelectedClient.id === wsMessage.client_id) {
          setSelectedClient(prev => prev ? { ...prev, dossier: wsMessage.data } : prev);
        }
      }
    } else if (wsMessage.type === 'car_interest_update') {
      console.log('Получено обновление автомобильных интересов для клиента:', wsMessage.client_id);
      
      // Обновляем автомобильные интересы в данных клиента напрямую из WebSocket сообщения
      if (wsMessage.data && wsMessage.client_id) {
        setClients(prevClients => 
          prevClients.map(client => 
            client.id === wsMessage.client_id
              ? { ...client, car_interest: wsMessage.data }
              : client
          )
        );
        
        // Если обновленный клиент является выбранным, обновляем selectedClient
        const currentSelectedClient = selectedClientRef.current;
        if (currentSelectedClient && currentSelectedClient.id === wsMessage.client_id) {
          setSelectedClient(prev => prev ? { ...prev, car_interest: wsMessage.data } : prev);
        }
      }
    } else if (wsMessage.type === 'task_update') {
      console.log('Получено обновление задач для клиента:', wsMessage.client_id);
      
      // Обновляем задачи в данных клиента напрямую из WebSocket сообщения
      if (wsMessage.data && wsMessage.client_id) {
        // Если это данные о задачах (массив)
        if (wsMessage.data.tasks) {
          setClients(prevClients => 
            prevClients.map(client => 
              client.id === wsMessage.client_id
                ? { ...client, tasks: wsMessage.data.tasks }
                : client
            )
          );
          
          // Если обновленный клиент является выбранным, обновляем selectedClient
          const currentSelectedClient = selectedClientRef.current;
          if (currentSelectedClient && currentSelectedClient.id === wsMessage.client_id) {
            setSelectedClient(prev => prev ? { ...prev, tasks: wsMessage.data.tasks } : prev);
          }
        }
        // Если это удаление задачи
        else if (wsMessage.data.deleted_task_id) {
          setClients(prevClients => 
            prevClients.map(client => 
              client.id === wsMessage.client_id
                ? { 
                    ...client, 
                    tasks: client.tasks?.filter(task => task.id !== wsMessage.data.deleted_task_id) || []
                  }
                : client
            )
          );
          
          // Если обновленный клиент является выбранным, обновляем selectedClient
          const currentSelectedClient = selectedClientRef.current;
          if (currentSelectedClient && currentSelectedClient.id === wsMessage.client_id) {
            setSelectedClient(prev => prev ? { 
              ...prev, 
              tasks: prev.tasks?.filter(task => task.id !== wsMessage.data.deleted_task_id) || []
            } : prev);
          }
        }
      }
    }
  }, []);

  // WebSocket
  const { isConnected } = useWebSocket({
    onMessage: handleWebSocketMessage,
    onConnect: () => console.log('WebSocket connected'),
    onDisconnect: () => console.log('WebSocket disconnected')
  });

  // Загрузка клиентов
  const loadClients = useCallback(async () => {
    try {
      const response = await clientsApi.getAll();
      const sortedClients = response.data.sort((a, b) => {
        const aLastMessage = a.messages?.[0]?.timestamp;
        const bLastMessage = b.messages?.[0]?.timestamp;
        
        if (!aLastMessage && !bLastMessage) return 0;
        if (!aLastMessage) return 1;
        if (!bLastMessage) return -1;
        
        return new Date(bLastMessage).getTime() - new Date(aLastMessage).getTime();
      });
      setClients(sortedClients);
    } catch (error) {
      console.error('Ошибка загрузки клиентов:', error);
    }
  }, []);

  // Загрузка сообщений
  const loadMessages = useCallback(async (clientId: number) => {
    try {
      const response = await messagesApi.getByClient(clientId);
      const sortedMessages = response.data.sort((a, b) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );
      setMessages(sortedMessages);
    } catch (error) {
      console.error('Ошибка загрузки сообщений:', error);
    }
  }, []);

  // Отправка сообщения
  const handleSendMessage = useCallback(async (content: string, contentType: string = 'text') => {
    const currentSelectedClient = selectedClientRef.current;
    if (!currentSelectedClient) return;

    try {
      // Отправляем сообщение через Pact API
      await pactApi.sendMessage({
        client_id: currentSelectedClient.id,
        content: content,
        content_type: contentType
      });

      // Перезагружаем сообщения и клиентов после отправки
      await loadMessages(currentSelectedClient.id);
      await loadClients();
      
      // Обновляем selectedClient для актуальной статистики
      try {
        const response = await clientsApi.getById(currentSelectedClient.id);
        setSelectedClient(response.data);
      } catch (error) {
        console.error('Ошибка при получении обновленных данных клиента:', error);
      }
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error);
    }
  }, [loadClients, loadMessages]);

  // Выбор клиента
  const handleClientSelect = useCallback(async (client: Client) => {
    setSelectedClient(client);
    await loadMessages(client.id);
  }, [loadMessages]);

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
    <div className="h-screen bg-neutral-50 flex">
      {/* Левая колонка - Список диалогов */}
      <div className="w-80 bg-white border-r border-neutral-200">
        <ClientList
          clients={clients}
          selectedClientId={selectedClient?.id}
          onClientSelect={handleClientSelect}
          onBroadcastClick={() => setShowBroadcast(true)}
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
      <div className="w-96 bg-neutral-50 border-l border-neutral-200">
        <ClientCard 
          client={selectedClient} 
          onClientUpdate={(updatedClient) => {
            setSelectedClient(updatedClient);
            loadClients(); // Перезагружаем список клиентов
          }}
        />
      </div>

      {/* Индикатор WebSocket соединения */}
      <div className="fixed bottom-6 right-6">
        <div
          className={`px-3 py-2 rounded-xl text-sm font-medium shadow-lg backdrop-blur-sm transition-all duration-200 ${
            isConnected
              ? 'bg-success-50 text-success-600 border border-success-200'
              : 'bg-error-50 text-error-600 border border-error-200'
          }`}
        >
          {isConnected ? 'Онлайн' : 'Офлайн'}
        </div>
      </div>

      {/* Модалка рассылки */}
      <BroadcastModal
        isOpen={showBroadcast}
        onClose={() => setShowBroadcast(false)}
        onSuccess={() => {
          loadClients(); // Перезагружаем клиентов после рассылки
        }}
      />
    </div>
  );
}

export default App;