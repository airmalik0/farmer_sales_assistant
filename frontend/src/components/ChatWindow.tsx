import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip } from 'lucide-react';
import { Message, Client } from '../types';
import { formatTime, getContentTypeDisplay, getClientDisplayName } from '../utils';
import { cn } from '../utils';

interface ChatWindowProps {
  client?: Client;
  messages: Message[];
  onSendMessage: (content: string, contentType: string) => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  client,
  messages,
  onSendMessage,
}) => {
  const [messageText, setMessageText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = () => {
    if (messageText.trim()) {
      onSendMessage(messageText.trim(), 'text');
      setMessageText('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!client) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <p className="text-lg mb-2">Выберите диалог</p>
          <p className="text-sm">Выберите клиента из списка для начала общения</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Заголовок чата */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {getClientDisplayName(client)}
            </h3>
            <p className="text-sm text-gray-500">
              Telegram ID: {client.telegram_id}
            </p>
          </div>
        </div>
      </div>

      {/* Область сообщений */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex',
              message.sender === 'farmer' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                'max-w-xs lg:max-w-md xl:max-w-lg px-4 py-2 rounded-lg',
                message.sender === 'farmer'
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-200 text-gray-900'
              )}
            >
              {message.content_type !== 'text' && (
                <div className="text-xs opacity-75 mb-1">
                  {getContentTypeDisplay(message.content_type)}
                </div>
              )}
              <div className="break-words">{message.content}</div>
              <div
                className={cn(
                  'text-xs mt-1',
                  message.sender === 'farmer' ? 'text-primary-100' : 'text-gray-500'
                )}
              >
                {formatTime(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Поле ввода сообщения */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="flex items-end space-x-2">
          <button
            type="button"
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Прикрепить файл"
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          <div className="flex-1">
            <textarea
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Введите сообщение..."
              className="w-full p-2 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows={1}
              style={{
                minHeight: '40px',
                maxHeight: '120px',
              }}
            />
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={!messageText.trim()}
            className="p-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};