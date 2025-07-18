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