import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip } from 'lucide-react';
import { Message, Client } from '../types';
import { formatTime, getContentTypeDisplay, getClientDisplayName, cn, parseMediaContent, isMediaContent } from '../utils';
import { MediaMessage } from './MediaMessage';

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
      <div className="h-full flex items-center justify-center bg-neutral-50">
        <div className="text-center text-neutral-500">
          <p className="text-xl mb-3 font-medium text-neutral-700">Выберите диалог</p>
          <p className="text-sm text-neutral-500">Выберите клиента из списка для начала общения</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Заголовок чата */}
      <div className="p-6 border-b border-neutral-200 bg-white">
        <div className="flex items-center">
          <div>
            <h3 className="text-xl font-semibold text-neutral-900">
              {getClientDisplayName(client)}
            </h3>
            <p className="text-sm text-neutral-500 font-mono">
              Telegram ID: {client.telegram_id}
            </p>
          </div>
        </div>
      </div>

      {/* Область сообщений */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-hide bg-neutral-50/50">
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
                'max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-2xl shadow-sm',
                message.sender === 'farmer'
                  ? 'bg-primary-500 text-white'
                  : 'bg-white text-neutral-900 border border-neutral-200'
              )}
            >
              {message.content_type !== 'text' && (
                <div className={cn(
                  "text-xs font-medium mb-2 px-2 py-1 rounded-lg",
                  message.sender === 'farmer' 
                    ? 'bg-primary-400/30 text-primary-100' 
                    : 'bg-neutral-100 text-neutral-600'
                )}>
                  {getContentTypeDisplay(message.content_type)}
                </div>
              )}
              
              {/* Отображение контента сообщения */}
              {isMediaContent(message.content_type) ? (
                (() => {
                  const media = parseMediaContent(message.content, message.content_type);
                  return media ? (
                    <MediaMessage media={media} />
                  ) : (
                    <div className="break-words leading-relaxed">{message.content}</div>
                  );
                })()
              ) : (
                <div className="break-words leading-relaxed">{message.content}</div>
              )}

              <div
                className={cn(
                  'text-xs mt-2 font-medium',
                  message.sender === 'farmer' ? 'text-primary-200' : 'text-neutral-500'
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
      <div className="p-6 border-t border-neutral-200 bg-white">
        <div className="flex items-end space-x-3">
          <button
            type="button"
            className="p-3 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-50 rounded-xl transition-all duration-200"
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
              className="w-full p-4 border border-neutral-200 rounded-2xl resize-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all duration-200 bg-neutral-50 focus:bg-white"
              rows={1}
              style={{
                minHeight: '56px',
                maxHeight: '120px',
              }}
            />
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={!messageText.trim()}
            className="p-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md disabled:hover:shadow-sm"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};