import React from 'react';
import { Client } from '../types';
import { getClientDisplayName, formatTime } from '../utils';
import { cn } from '../utils';

interface ClientListProps {
  clients: Client[];
  selectedClientId?: number;
  onClientSelect: (client: Client) => void;
}

export const ClientList: React.FC<ClientListProps> = ({
  clients,
  selectedClientId,
  onClientSelect,
}) => {
  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Диалоги</h2>
      </div>
      
      <div className="space-y-1 p-2">
        {clients.map((client) => {
          const lastMessage = client.messages?.[0];
          const isSelected = client.id === selectedClientId;
          
          return (
            <div
              key={client.id}
              onClick={() => onClientSelect(client)}
              className={cn(
                'p-3 rounded-lg cursor-pointer transition-colors',
                isSelected
                  ? 'bg-primary-50 border border-primary-200'
                  : 'hover:bg-gray-50 border border-transparent'
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {getClientDisplayName(client)}
                  </p>
                  {lastMessage && (
                    <p className="text-xs text-gray-500 truncate mt-1">
                      {lastMessage.sender === 'client' ? 'Клиент: ' : 'Вы: '}
                      {lastMessage.content_type === 'text' 
                        ? lastMessage.content 
                        : `[${lastMessage.content_type}]`
                      }
                    </p>
                  )}
                </div>
                
                {lastMessage && (
                  <div className="text-xs text-gray-400 ml-2">
                    {formatTime(lastMessage.timestamp)}
                  </div>
                )}
              </div>
              
              {/* Индикатор новых сообщений можно добавить здесь */}
            </div>
          );
        })}
      </div>
      
      {clients.length === 0 && (
        <div className="flex items-center justify-center h-32 text-gray-500">
          Нет активных диалогов
        </div>
      )}
    </div>
  );
};