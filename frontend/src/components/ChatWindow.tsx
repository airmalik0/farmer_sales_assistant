import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip } from 'lucide-react';
import { Message, Client } from '../types';
import { 
  formatTime, 
  getClientDisplayName, 
  getClientContact, 
  getProviderIcon, 
  getProviderName, 
  getProviderColor,
  getMessageStatusIcon,
  getMessageStatusColor,
  getFileTypeIcon,
  formatFileSize,
  isImageAttachment,
  isVideoAttachment,
  isAudioAttachment 
} from '../utils';

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

  // Компонент для отображения вложения
  const AttachmentMessage = ({ attachment }: { attachment: any }) => {
    const isImage = isImageAttachment(attachment.mime_type);
    const isVideo = isVideoAttachment(attachment.mime_type);
    const isAudio = isAudioAttachment(attachment.mime_type);

    if (isImage) {
      return (
        <div className="mb-2">
          <img 
            src={attachment.attachment_url} 
            alt={attachment.file_name}
            className="max-w-full rounded-lg"
            style={{ maxHeight: '200px' }}
          />
          <p className="text-xs text-neutral-500 mt-1">{attachment.file_name}</p>
        </div>
      );
    }

    if (isVideo) {
      return (
        <div className="mb-2">
          <video 
            src={attachment.attachment_url} 
            controls
            className="max-w-full rounded-lg"
            style={{ maxHeight: '200px' }}
          />
          <p className="text-xs text-neutral-500 mt-1">{attachment.file_name}</p>
        </div>
      );
    }

    if (isAudio) {
      return (
        <div className="mb-2">
          <audio src={attachment.attachment_url} controls className="w-full" />
          <p className="text-xs text-neutral-500 mt-1">{attachment.file_name}</p>
        </div>
      );
    }

    // Для остальных файлов показываем как ссылку
    return (
      <div className="mb-2">
        <a 
          href={attachment.attachment_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-2 p-2 bg-neutral-100 rounded-lg hover:bg-neutral-200 transition-colors"
        >
          <span>{getFileTypeIcon(attachment.mime_type)}</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-neutral-900 truncate">{attachment.file_name}</p>
            <p className="text-xs text-neutral-500">{formatFileSize(attachment.size)}</p>
          </div>
        </a>
      </div>
    );
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
        <div className="flex items-center gap-3">
          <span className="text-2xl">{getProviderIcon(client.provider)}</span>
          <div>
            <h3 className="text-xl font-semibold text-neutral-900">
              {getClientDisplayName(client)}
            </h3>
            <div className="flex items-center gap-2">
              <span className={`text-sm font-medium ${getProviderColor(client.provider)}`}>
                {getProviderName(client.provider)}
              </span>
              <span className="text-neutral-300">•</span>
              <span className="text-sm text-neutral-500 font-mono">
                {getClientContact(client)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Область сообщений */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-hide bg-neutral-50/50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.sender === 'farmer' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-2xl shadow-sm ${
                message.sender === 'farmer'
                  ? 'bg-primary-500 text-white'
                  : 'bg-white text-neutral-900 border border-neutral-200'
              }`}
            >
              {/* Отображение вложений */}
              {message.attachments && message.attachments.length > 0 && (
                <div className="mb-2">
                  {message.attachments.map((attachment) => (
                    <AttachmentMessage key={attachment.id} attachment={attachment} />
                  ))}
                </div>
              )}
              
              {/* Текстовое содержимое */}
              {message.content && (
                <div className="break-words leading-relaxed">{message.content}</div>
              )}

              {/* Время и статус сообщения */}
              <div className="flex items-center justify-between mt-2">
                <div
                  className={`text-xs font-medium ${
                    message.sender === 'farmer' ? 'text-primary-200' : 'text-neutral-500'
                  }`}
                >
                  {formatTime(message.timestamp)}
                </div>
                
                {/* Статус для исходящих сообщений */}
                {message.sender === 'farmer' && (
                  <div className="flex items-center gap-1">
                    <span className={`text-xs ${
                      message.sender === 'farmer' ? 'text-primary-200' : getMessageStatusColor(message.status)
                    }`}>
                      {getMessageStatusIcon(message.status)}
                    </span>
                  </div>
                )}
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
              placeholder={`Отправить сообщение через ${getProviderName(client.provider)}...`}
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