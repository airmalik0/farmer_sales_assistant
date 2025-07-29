import axios from 'axios';
import { Client, Message, Dossier, CarInterest, Task, DossierManualUpdate, CarInterestManualUpdate, TaskManualUpdate } from '../types';

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
  approveName: (id: number) =>
    api.post<Client>(`/clients/${id}/approve-name`),
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
  updateByClient: (clientId: number, structuredData: any) =>
    api.put<Dossier>(`/dossier/client/${clientId}`, structuredData),
  
  // Новые методы для ручного редактирования
  updateManually: (id: number, update: DossierManualUpdate) =>
    api.put<Dossier>(`/dossier/${id}/manual`, update),
  updateManuallyByClient: (clientId: number, update: DossierManualUpdate) =>
    api.put<Dossier>(`/dossier/client/${clientId}/manual`, update),
};

export const carInterestApi = {
  getByClient: (clientId: number) => api.get<CarInterest>(`/car_interest/client/${clientId}`),
  getById: (id: number) => api.get<CarInterest>(`/car_interest/${id}`),
  create: (carInterest: Omit<CarInterest, 'id' | 'last_updated'>) =>
    api.post<CarInterest>('/car_interest', carInterest),
  update: (id: number, carInterest: Partial<CarInterest>) =>
    api.put<CarInterest>(`/car_interest/${id}`, carInterest),
  updateByClient: (clientId: number, structuredData: any) =>
    api.put<CarInterest>(`/car_interest/client/${clientId}`, structuredData),
  
  // Новые методы для ручного редактирования
  updateManually: (id: number, update: CarInterestManualUpdate) =>
    api.put<CarInterest>(`/car_interest/${id}/manual`, update),
  updateManuallyByClient: (clientId: number, update: CarInterestManualUpdate) =>
    api.put<CarInterest>(`/car_interest/client/${clientId}/manual`, update),
};

export const tasksApi = {
  getByClient: (clientId: number, activeOnly?: boolean) => 
    api.get<Task[]>(`/tasks/client/${clientId}${activeOnly ? '?active_only=true' : ''}`),
  getById: (id: number) => api.get<Task>(`/tasks/${id}`),
  create: (task: Omit<Task, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<Task>('/tasks', task),
  update: (id: number, task: Partial<Task>) =>
    api.put<Task>(`/tasks/${id}`, task),
  complete: (id: number) =>
    api.post<Task>(`/tasks/${id}/complete`),
  delete: (id: number) =>
    api.delete(`/tasks/${id}`),
  
  // Новые методы для ручного редактирования
  updateManually: (id: number, update: TaskManualUpdate) =>
    api.put<Task>(`/tasks/${id}/manual`, update),
};

export const telegramApi = {
  sendMessage: (data: { client_id: number; content: string; content_type?: string }) =>
    api.post('/telegram/send', data),
  broadcast: (data: { content: string; content_type?: string; include_greeting?: boolean }) =>
    api.post('/telegram/broadcast', data),
  validateBroadcast: (data: { content: string; content_type?: string }) =>
    api.post('/telegram/validate-broadcast', data),
};

export const settingsApi = {
  getGreeting: () => api.get('/settings/greeting'),
  setGreeting: (greetingText: string, enabled: boolean = true) =>
    api.post('/settings/greeting', {
      greeting_text: greetingText,
      enabled: enabled,
    }),
  updateGreeting: (greetingText?: string, enabled?: boolean) =>
    api.put('/settings/greeting', {
      ...(greetingText !== undefined && { greeting_text: greetingText }),
      ...(enabled !== undefined && { enabled: enabled }),
    }),
  clearGreeting: () => api.delete('/settings/greeting'),
  previewGreeting: (greetingText: string, firstName: string = 'Иван', lastName: string = 'Иванов') =>
    api.get('/settings/greeting/preview', {
      params: {
        greeting_text: greetingText,
        first_name: firstName,
        last_name: lastName,
      },
    }),
};

export const triggersApi = {
  getAll: (skip?: number, limit?: number, status?: string) => {
    const params = new URLSearchParams();
    if (skip !== undefined) params.append('skip', skip.toString());
    if (limit !== undefined) params.append('limit', limit.toString());
    if (status) params.append('status', status);
    return api.get(`/triggers?${params.toString()}`);
  },
  getById: (id: number) => api.get(`/triggers/${id}`),
  create: (trigger: any) => api.post('/triggers', trigger),
  update: (id: number, trigger: any) => api.put(`/triggers/${id}`, trigger),
  delete: (id: number) => api.delete(`/triggers/${id}`),
  toggle: (id: number) => api.post(`/triggers/${id}/toggle`),
  test: (id: number, carId?: string) => {
    const params = carId ? `?car_id=${carId}` : '';
    return api.post(`/triggers/${id}/test${params}`);
  },
  getLogs: (id: number, skip?: number, limit?: number) => {
    const params = new URLSearchParams();
    if (skip !== undefined) params.append('skip', skip.toString());
    if (limit !== undefined) params.append('limit', limit.toString());
    return api.get(`/triggers/${id}/logs?${params.toString()}`);
  },
  getStats: (id: number) => api.get(`/triggers/${id}/stats`),
};

export const taskTriggersApi = {
  createWithTrigger: (data: any) => api.post('/task-triggers/create-with-trigger', data),
  createNotificationTrigger: (data: {
    trigger_name: string;
    conditions: any;
    message?: string;
    channels?: string[];
    check_interval?: number;
  }) => api.post('/task-triggers/notify-trigger', data),
  getClientTriggers: (clientId: number) => api.get(`/task-triggers/client/${clientId}/triggers`),
  getClientTasksWithTriggers: (clientId: number) => api.get(`/task-triggers/client/${clientId}/tasks-with-triggers`),
  toggleTriggerForClient: (triggerId: number, clientId: number) => 
    api.post(`/task-triggers/trigger/${triggerId}/toggle-for-client/${clientId}`),
};

export default api;