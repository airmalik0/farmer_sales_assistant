import React from 'react';
import { User, Calendar, MessageCircle, FileText } from 'lucide-react';
import { Client } from '../types';
import { getClientDisplayName, formatDate } from '../utils';

interface ClientCardProps {
  client?: Client;
}

export const ClientCard: React.FC<ClientCardProps> = ({ client }) => {
  if (!client) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <User className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg mb-2">Информация о клиенте</p>
          <p className="text-sm">Выберите клиента для просмотра досье</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Карточка клиента</h2>
      </div>

      <div className="p-4 space-y-6">
        {/* Основная информация */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center mb-4">
            <User className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-sm font-medium text-gray-900">Основная информация</h3>
          </div>
          
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500">Имя</p>
              <p className="text-sm font-medium text-gray-900">
                {getClientDisplayName(client)}
              </p>
            </div>
            
            <div>
              <p className="text-sm text-gray-500">Telegram ID</p>
              <p className="text-sm font-medium text-gray-900">{client.telegram_id}</p>
            </div>
            
            {client.username && (
              <div>
                <p className="text-sm text-gray-500">Username</p>
                <p className="text-sm font-medium text-gray-900">@{client.username}</p>
              </div>
            )}
            
            <div className="flex items-center">
              <Calendar className="w-4 h-4 text-gray-400 mr-2" />
              <div>
                <p className="text-sm text-gray-500">Дата регистрации</p>
                <p className="text-sm font-medium text-gray-900">
                  {formatDate(client.created_at)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Статистика сообщений */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center mb-4">
            <MessageCircle className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-sm font-medium text-gray-900">Статистика</h3>
          </div>
          
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500">Всего сообщений</p>
              <p className="text-lg font-semibold text-gray-900">
                {client.messages?.length || 0}
              </p>
            </div>
            
            {client.messages && client.messages.length > 0 && (
              <div>
                <p className="text-sm text-gray-500">Последнее сообщение</p>
                <p className="text-sm font-medium text-gray-900">
                  {formatDate(client.messages[0].timestamp)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Досье клиента */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center mb-4">
            <FileText className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-sm font-medium text-gray-900">AI Досье</h3>
          </div>
          
          {client.dossier?.summary ? (
            <div className="space-y-3">
              <div className="text-sm text-gray-700 whitespace-pre-wrap">
                {client.dossier.summary}
              </div>
              <div className="text-xs text-gray-500 border-t pt-2">
                Обновлено: {formatDate(client.dossier.last_updated)}
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Досье ещё не сформировано</p>
              <p className="text-xs mt-1">
                Досье будет автоматически создано после диалога с клиентом
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};