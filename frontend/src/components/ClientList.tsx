import React from 'react';
import { Radio } from 'lucide-react';
import { Client } from '../types';
import { getClientDisplayName, formatTime } from '../utils';
import { cn } from '../utils';

interface ClientListProps {
  clients: Client[];
  selectedClientId?: number;
  onClientSelect: (client: Client) => void;
  onBroadcastClick?: () => void;
}

export const ClientList: React.FC<ClientListProps> = ({
  clients,
  selectedClientId,
  onClientSelect,
  onBroadcastClick,
}) => {
  return (
    <div className="h-full overflow-y-auto scrollbar-hide">
      <div className="p-6 border-b border-neutral-200 bg-white">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-neutral-900">Диалоги</h2>
          {onBroadcastClick && (
            <button
              onClick={onBroadcastClick}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-colors"
              title="Массовая рассылка"
            >
              <Radio className="w-4 h-4" />
              Рассылка
            </button>
          )}
        </div>
      </div>
      
      <div className="p-3">
        {clients.map((client) => {
          const lastMessage = client.messages?.[0];
          const isSelected = client.id === selectedClientId;
          
          return (
            <div
              key={client.id}
              onClick={() => onClientSelect(client)}
              className={cn(
                'p-4 rounded-xl cursor-pointer transition-all duration-200 mb-2',
                isSelected
                  ? 'bg-primary-50 border border-primary-200 shadow-sm'
                  : 'hover:bg-neutral-50 border border-transparent hover:shadow-sm'
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-900 truncate mb-1">
                    {getClientDisplayName(client)}
                  </p>
                  {lastMessage && (
                    <p className="text-xs text-neutral-500 truncate leading-relaxed">
                      <span className={cn(
                        "font-medium",
                        lastMessage.sender === 'client' ? 'text-neutral-600' : 'text-neutral-500'
                      )}>
                        {lastMessage.sender === 'client' ? 'Клиент: ' : 'Вы: '}
                      </span>
                      {lastMessage.content_type === 'text' 
                        ? lastMessage.content 
                        : `[${lastMessage.content_type}]`
                      }
                    </p>
                  )}
                </div>
                
                {lastMessage && (
                  <div className="text-xs text-neutral-400 ml-3 mt-0.5 font-medium">
                    {formatTime(lastMessage.timestamp)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      {clients.length === 0 && (
        <div className="flex items-center justify-center h-32 text-neutral-500">
          <div className="text-center">
            <p className="text-sm font-medium text-neutral-600 mb-1">Нет активных диалогов</p>
            <p className="text-xs text-neutral-500">Диалоги появятся здесь после получения сообщений</p>
          </div>
        </div>
      )}
    </div>
  );
};