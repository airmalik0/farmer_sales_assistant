import { Provider, ProviderInfo, Client } from '../types';

// Утилиты для работы с датами
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatDateShort = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 1) {
    return 'Сегодня';
  } else if (diffDays === 2) {
    return 'Вчера';
  } else if (diffDays <= 7) {
    return `${diffDays - 1} дн. назад`;
  } else {
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit'
    });
  }
};

// Утилиты для работы с провайдерами
export const getProviderInfo = (provider: Provider): ProviderInfo => {
  switch (provider) {
    case 'whatsapp':
      return {
        name: 'WhatsApp',
        icon: '💬', // Можно заменить на иконку
        color: 'text-green-600'
      };
    case 'telegram_personal':
      return {
        name: 'Telegram',
        icon: '✈️', // Можно заменить на иконку  
        color: 'text-blue-600'
      };
    default:
      return {
        name: 'Unknown',
        icon: '❓',
        color: 'text-gray-600'
      };
  }
};

export const getProviderIcon = (provider: Provider): string => {
  return getProviderInfo(provider).icon;
};

export const getProviderName = (provider: Provider): string => {
  return getProviderInfo(provider).name;
};

export const getProviderColor = (provider: Provider): string => {
  return getProviderInfo(provider).color;
};

// Утилита для получения отображаемого имени клиента
export const getClientDisplayName = (client: Client): string => {
  if (client.name) {
    return client.name;
  }
  
  if (client.username) {
    return `@${client.username}`;
  }
  
  if (client.phone_number) {
    return client.phone_number;
  }
  
  return client.sender_external_id || `ID: ${client.id}`;
};

// Утилита для получения контактной информации клиента
export const getClientContact = (client: Client): string => {
  if (client.provider === 'whatsapp' && client.phone_number) {
    return client.phone_number;
  }
  
  if (client.provider === 'telegram_personal' && client.username) {
    return `@${client.username}`;
  }
  
  return client.sender_external_id;
};

// Утилита для форматирования размера файла
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Б';
  
  const k = 1024;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Утилита для проверки типа вложения
export const isImageAttachment = (mimeType: string): boolean => {
  return mimeType.startsWith('image/');
};

export const isVideoAttachment = (mimeType: string): boolean => {
  return mimeType.startsWith('video/');
};

export const isAudioAttachment = (mimeType: string): boolean => {
  return mimeType.startsWith('audio/');
};

export const isDocumentAttachment = (mimeType: string): boolean => {
  return !isImageAttachment(mimeType) && 
         !isVideoAttachment(mimeType) && 
         !isAudioAttachment(mimeType);
};

// Утилита для получения иконки типа файла
export const getFileTypeIcon = (mimeType: string): string => {
  if (isImageAttachment(mimeType)) return '🖼️';
  if (isVideoAttachment(mimeType)) return '🎥';
  if (isAudioAttachment(mimeType)) return '🎵';
  if (mimeType.includes('pdf')) return '📄';
  if (mimeType.includes('word') || mimeType.includes('document')) return '📝';
  if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '📊';
  return '📎';
};

// Утилиты для работы с приоритетами задач
export const formatPriority = (priority: string): string => {
  switch (priority) {
    case 'high':
      return 'Высокий';
    case 'normal':
      return 'Обычный';
    case 'low':
      return 'Низкий';
    default:
      return priority;
  }
};

export const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'high':
      return 'text-red-600 bg-red-50';
    case 'normal':
      return 'text-blue-600 bg-blue-50';
    case 'low':
      return 'text-gray-600 bg-gray-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
};

// Утилита для работы со статусами сообщений
export const getMessageStatusIcon = (status: string): string => {
  switch (status) {
    case 'sent':
      return '✓';
    case 'delivered':
      return '✓✓';
    case 'read':
      return '✓✓';
    case 'error':
      return '❌';
    default:
      return '⏳';
  }
};

export const getMessageStatusColor = (status: string): string => {
  switch (status) {
    case 'sent':
      return 'text-gray-500';
    case 'delivered':
      return 'text-gray-500';
    case 'read':
      return 'text-blue-500';
    case 'error':
      return 'text-red-500';
    default:
      return 'text-gray-400';
  }
};

// Утилита для обрезки текста
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substr(0, maxLength) + '...';
};