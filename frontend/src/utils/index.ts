import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getClientDisplayName(client: { first_name?: string; last_name?: string; username?: string; telegram_id: number }): string {
  // Приоритет: first_name/last_name -> username -> telegram_id
  if (client.first_name) {
    return client.last_name ? `${client.first_name} ${client.last_name}` : client.first_name;
  }
  if (client.username) {
    return `@${client.username}`;
  }
  return `ID: ${client.telegram_id}`;
}

export function getContentTypeDisplay(contentType: string): string {
  const types: Record<string, string> = {
    text: 'Текст',
    voice: 'Голосовое',
    video_note: 'Видео-кружок',
    document: 'Документ',
    photo: 'Фото',
    other: 'Другое',
  };
  return types[contentType] || contentType;
}

// Утилиты для работы с медиафайлами
export interface MediaFile {
  fileId: string;
  type: 'voice' | 'video_note' | 'document' | 'photo';
  filename?: string;
}

export function parseMediaContent(content: string, contentType: string): MediaFile | null {
  if (contentType === 'voice' && content.startsWith('voice_file_id:')) {
    return {
      fileId: content.split('voice_file_id:')[1],
      type: 'voice'
    };
  }
  
  if (contentType === 'video_note' && content.startsWith('video_note_file_id:')) {
    return {
      fileId: content.split('video_note_file_id:')[1],
      type: 'video_note'
    };
  }
  
  if (contentType === 'document' && content.startsWith('document_file_id:')) {
    const parts = content.split('document_file_id:')[1].split(', filename:');
    return {
      fileId: parts[0],
      type: 'document',
      filename: parts[1] || 'document'
    };
  }
  
  if (contentType === 'photo' && content.startsWith('photo_file_id:')) {
    return {
      fileId: content.split('photo_file_id:')[1],
      type: 'photo'
    };
  }
  
  return null;
}

export function getMediaUrl(fileId: string): string {
  // URL к нашему API endpoint для получения медиафайлов
  return `/api/v1/telegram/media/${encodeURIComponent(fileId)}`;
}

export function isMediaContent(contentType: string): boolean {
  return ['voice', 'video_note', 'document', 'photo'].includes(contentType);
}