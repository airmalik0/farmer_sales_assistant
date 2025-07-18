import axios from 'axios';
import { Client, Message, Dossier } from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const clientsApi = {
  getAll: () => api.get<Client[]>('/clients'),
  getById: (id: number) => api.get<Client>(`/clients/${id}`),
  getByTelegramId: (telegramId: number) => api.get<Client>(`/clients/telegram/${telegramId}`),
  create: (client: Omit<Client, 'id' | 'created_at' | 'messages' | 'dossier'>) =>
    api.post<Client>('/clients', client),
  update: (id: number, client: Partial<Client>) =>
    api.put<Client>(`/clients/${id}`, client),
};

export const messagesApi = {
  getRecent: () => api.get<Message[]>('/messages'),
  getByClient: (clientId: number) => api.get<Message[]>(`/messages/client/${clientId}`),
  getById: (id: number) => api.get<Message>(`/messages/${id}`),
  create: (message: Omit<Message, 'id' | 'timestamp'>) =>
    api.post<Message>('/messages', message),
  update: (id: number, message: Partial<Message>) =>
    api.put<Message>(`/messages/${id}`, message),
};

export const dossierApi = {
  getByClient: (clientId: number) => api.get<Dossier>(`/dossier/client/${clientId}`),
  getById: (id: number) => api.get<Dossier>(`/dossier/${id}`),
  create: (dossier: Omit<Dossier, 'id' | 'last_updated'>) =>
    api.post<Dossier>('/dossier', dossier),
  update: (id: number, dossier: Partial<Dossier>) =>
    api.put<Dossier>(`/dossier/${id}`, dossier),
  updateByClient: (clientId: number, summary: string) =>
    api.put<Dossier>(`/dossier/client/${clientId}`, { summary }),
};

export default api;