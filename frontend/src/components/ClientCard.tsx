import { useState } from 'react';
import { User, Calendar, MessageCircle, FileText, Edit2, Check, X, Shield, ShieldCheck, Phone, MapPin, Cake, UserCheck, FileTextIcon, Car, CheckSquare, Plus } from 'lucide-react';
import { Client, DossierField, CarQuery, Task } from '../types';
import { getClientDisplayName, formatDate } from '../utils';
import { clientsApi, tasksApi } from '../services/api';
import { DossierEditForm } from './DossierEditForm';
import { CarInterestEditForm } from './CarInterestEditForm';
import { TaskEditForm } from './TaskEditForm';

// Схема полей досье с titles для отображения
const DOSSIER_FIELD_SCHEMA = {
  phone: { title: 'Телефон', icon: Phone },
  current_location: { title: 'Местоположение', icon: MapPin },
  birthday: { title: 'День рождения', icon: Cake },
  gender: { title: 'Пол', icon: UserCheck },
  notes: { title: 'Заметки', icon: FileTextIcon }
};

interface ClientCardProps {
  client?: Client;
  onClientUpdate?: (client: Client) => void;
}

export const ClientCard = ({ client, onClientUpdate }: ClientCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editFirstName, setEditFirstName] = useState('');
  const [editLastName, setEditLastName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  
  // Новые состояния для редактирования
  const [editingDossier, setEditingDossier] = useState(false);
  const [editingCarInterest, setEditingCarInterest] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [creatingTask, setCreatingTask] = useState(false);
  const [taskData, setTaskData] = useState({ description: '', due_date: '', priority: 'normal' });

  const handleEditStart = () => {
    setEditFirstName(client?.first_name || '');
    setEditLastName(client?.last_name || '');
    setIsEditing(true);
  };

  const handleEditCancel = () => {
    setIsEditing(false);
    setEditFirstName('');
    setEditLastName('');
  };

  const handleEditSave = async () => {
    if (!client) return;
    
    setIsSaving(true);
    try {
      const response = await clientsApi.update(client.id, { 
        first_name: editFirstName.trim() || undefined,
        last_name: editLastName.trim() || undefined
      });
      onClientUpdate?.(response.data);
      setIsEditing(false);
      setEditFirstName('');
      setEditLastName('');
    } catch (error) {
      console.error('Ошибка обновления имени клиента:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleApproveName = async () => {
    if (!client) return;
    
    setIsApproving(true);
    try {
      const response = await clientsApi.approveName(client.id);
      onClientUpdate?.(response.data);
    } catch (error) {
      console.error('Ошибка одобрения имени клиента:', error);
    } finally {
      setIsApproving(false);
    }
  };

  // Новые обработчики для редактирования
  const handleDossierUpdate = (updatedClient: Client) => {
    onClientUpdate?.(updatedClient);
    setEditingDossier(false);
  };

  const handleCarInterestUpdate = (updatedClient: Client) => {
    onClientUpdate?.(updatedClient);
    setEditingCarInterest(false);
  };

  const handleTaskUpdate = async (updatedTask: Task) => {
    if (client && onClientUpdate) {
      const updatedClient = {
        ...client,
        tasks: client.tasks?.map(task => 
          task.id === updatedTask.id ? updatedTask : task
        ) || [updatedTask]
      };
      onClientUpdate(updatedClient);
    }
    setEditingTask(null);
  };

  const handleTaskDelete = async (taskId: number) => {
    if (client && onClientUpdate) {
      const updatedTasks = client.tasks?.filter(task => task.id !== taskId) || [];
      const updatedClient = { ...client, tasks: updatedTasks };
      onClientUpdate(updatedClient);
    }
    setEditingTask(null);
  };

  const handleTaskCreate = async (taskData: { description: string; due_date?: string; priority?: string }) => {
    if (!client) return;
    
    try {
      const newTask = {
        client_id: client.id,
        description: taskData.description,
        due_date: taskData.due_date || null,
        priority: taskData.priority || 'normal',
        is_completed: false,
      };
      
      const response = await tasksApi.create(newTask);
      
      if (onClientUpdate) {
        const updatedClient = {
          ...client,
          tasks: [...(client.tasks || []), response.data]
        };
        onClientUpdate(updatedClient);
      }
      setCreatingTask(false);
    } catch (error) {
      console.error('Ошибка создания задачи:', error);
    }
  };

  // Функция для получения отформатированных полей досье
  const getDossierFields = (): DossierField[] => {
    if (!client?.dossier?.structured_data?.client_info) return [];
    
    const clientInfo = client.dossier.structured_data.client_info;
    const manualModifications = client.dossier.structured_data.manual_modifications || {};
    const fields: DossierField[] = [];
    
    // Проходим по схеме полей и извлекаем данные
    Object.entries(DOSSIER_FIELD_SCHEMA).forEach(([key, config]) => {
      const value = clientInfo[key];
      if (value !== null && value !== undefined && value !== '') {
        fields.push({
          key,
          title: config.title,
          value: String(value),
          isManuallyModified: !!manualModifications[key]
        });
      }
    });
    
    return fields;
  };

  // Функция для форматирования значения поля
  const formatFieldValue = (key: string, value: string | null): string => {
    if (!value) return '';
    
    switch (key) {
      case 'gender':
        return value === 'male' ? 'Мужской' : value === 'female' ? 'Женский' : value;
      case 'birthday':
        if (value.match(/^\d{4}-\d{2}-\d{2}$/)) {
          return new Date(value).toLocaleDateString('ru-RU');
        }
        return value;
      default:
        return value;
    }
  };

  // Функция для получения иконки поля
  const getFieldIcon = (key: string) => {
    const IconComponent = DOSSIER_FIELD_SCHEMA[key as keyof typeof DOSSIER_FIELD_SCHEMA]?.icon || FileText;
    return <IconComponent className="w-4 h-4 text-neutral-400" />;
  };

  // Функции для работы с автомобильными интересами
  const getCarQueries = (): CarQuery[] => {
    return client?.car_interest?.structured_data?.queries || [];
  };

  const formatCarQuery = (query: CarQuery): string => {
    const parts: string[] = [];
    
    if (query.brand) {
      const brands = Array.isArray(query.brand) ? query.brand : [query.brand];
      parts.push(`Марка: ${brands.join(', ')}`);
    }
    
    if (query.model) {
      const models = Array.isArray(query.model) ? query.model : [query.model];
      parts.push(`Модель: ${models.join(', ')}`);
    }
    
    if (query.price_min && query.price_max) {
      parts.push(`Цена: $${query.price_min.toLocaleString()} - $${query.price_max.toLocaleString()}`);
    } else if (query.price_min) {
      parts.push(`Цена от: $${query.price_min.toLocaleString()}`);
    } else if (query.price_max) {
      parts.push(`Цена до: $${query.price_max.toLocaleString()}`);
    }
    
    if (query.year_min && query.year_max) {
      parts.push(`Год: ${query.year_min} - ${query.year_max}`);
    } else if (query.year_min) {
      parts.push(`Год от: ${query.year_min}`);
    } else if (query.year_max) {
      parts.push(`Год до: ${query.year_max}`);
    }
    
    if (query.mileage_max) {
      parts.push(`Пробег до: ${query.mileage_max.toLocaleString()} км`);
    }
    
    if (query.exterior_color) {
      const colors = Array.isArray(query.exterior_color) ? query.exterior_color : [query.exterior_color];
      parts.push(`Цвет кузова: ${colors.join(', ')}`);
    }
    
    if (query.interior_color) {
      const colors = Array.isArray(query.interior_color) ? query.interior_color : [query.interior_color];
      parts.push(`Цвет салона: ${colors.join(', ')}`);
    }
    
    return parts.length > 0 ? parts.join(' | ') : 'Параметры не указаны';
  };

  // Функция для получения задач клиента
  const getTasks = (): Task[] => {
    return client?.tasks || [];
  };

  // Функция для форматирования приоритета задачи
  const formatPriority = (priority: string): string => {
    switch (priority) {
      case 'high':
        return 'Высокий';
      case 'low':
        return 'Низкий';
      default:
        return 'Обычный';
    }
  };

  // Функция для получения цвета приоритета
  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'low':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    }
  };

  if (!client) {
    return (
      <div className="h-full flex items-center justify-center bg-neutral-50">
        <div className="text-center text-neutral-500">
          <User className="w-12 h-12 mx-auto mb-4 text-neutral-300" />
          <p className="text-lg mb-2 font-medium text-neutral-700">Информация о клиенте</p>
          <p className="text-sm text-neutral-500">Выберите клиента для просмотра досье</p>
        </div>
      </div>
    );
  }

  // Если редактируем досье
  if (editingDossier) {
    return (
      <div className="h-full overflow-y-auto scrollbar-hide">
        <div className="p-6 border-b border-neutral-200 bg-white">
          <h2 className="text-xl font-semibold text-neutral-900">Карточка клиента</h2>
        </div>
        <div className="p-6">
          <DossierEditForm
            client={client}
            onUpdate={handleDossierUpdate}
            onCancel={() => setEditingDossier(false)}
          />
        </div>
      </div>
    );
  }

  // Если редактируем автомобильные интересы
  if (editingCarInterest) {
    return (
      <div className="h-full overflow-y-auto scrollbar-hide">
        <div className="p-6 border-b border-neutral-200 bg-white">
          <h2 className="text-xl font-semibold text-neutral-900">Карточка клиента</h2>
        </div>
        <div className="p-6">
          <CarInterestEditForm
            client={client}
            onUpdate={handleCarInterestUpdate}
            onCancel={() => setEditingCarInterest(false)}
          />
        </div>
      </div>
    );
  }

  // Если редактируем задачу
  if (editingTask) {
    return (
      <div className="h-full overflow-y-auto scrollbar-hide">
        <div className="p-6 border-b border-neutral-200 bg-white">
          <h2 className="text-xl font-semibold text-neutral-900">Карточка клиента</h2>
        </div>
        <div className="p-6">
          <TaskEditForm
            task={editingTask}
            onUpdate={handleTaskUpdate}
            onDelete={handleTaskDelete}
            onCancel={() => setEditingTask(null)}
          />
        </div>
      </div>
    );
  }

  const dossierFields = getDossierFields();
  const tasks = getTasks();

  return (
    <div className="h-full overflow-y-auto scrollbar-hide">
      <div className="p-6 border-b border-neutral-200 bg-white">
        <h2 className="text-xl font-semibold text-neutral-900">Карточка клиента</h2>
      </div>

      <div className="p-6 space-y-6">
        {/* Основная информация */}
        <div className="card p-5">
          <div className="flex items-center mb-4">
            <User className="w-5 h-5 text-neutral-400 mr-3" />
            <h3 className="text-base font-medium text-neutral-900">Основная информация</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">Имя</p>
                {!isEditing && (
                  <button 
                    onClick={handleEditStart}
                    className="text-neutral-400 hover:text-neutral-600 p-1 hover:bg-neutral-100 rounded transition-colors"
                    title="Редактировать имя"
                  >
                    <Edit2 className="w-3 h-3" />
                  </button>
                )}
              </div>
              {isEditing ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={editFirstName}
                      onChange={(e) => setEditFirstName(e.target.value)}
                      className="flex-1 text-sm font-medium text-neutral-900 bg-white border border-neutral-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="Имя"
                      disabled={isSaving}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleEditSave();
                        if (e.key === 'Escape') handleEditCancel();
                      }}
                      autoFocus
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={editLastName}
                      onChange={(e) => setEditLastName(e.target.value)}
                      className="flex-1 text-sm font-medium text-neutral-900 bg-white border border-neutral-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="Фамилия"
                      disabled={isSaving}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleEditSave();
                        if (e.key === 'Escape') handleEditCancel();
                      }}
                    />
                    <button
                      onClick={handleEditSave}
                      disabled={isSaving}
                      className="text-green-600 hover:text-green-700 p-1 hover:bg-green-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Сохранить"
                    >
                      <Check className="w-3 h-3" />
                    </button>
                    <button
                      onClick={handleEditCancel}
                      disabled={isSaving}
                      className="text-neutral-400 hover:text-neutral-600 p-1 hover:bg-neutral-100 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Отменить"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-neutral-900">
                    {getClientDisplayName(client)}
                  </p>
                  
                  {/* Статус одобрения имени */}
                  <div className="flex items-center gap-2">
                    {client.first_name ? (
                      client.name_approved ? (
                        <div className="flex items-center gap-1 px-2 py-1 bg-green-50 border border-green-200 rounded-full">
                          <ShieldCheck className="w-3 h-3 text-green-600" />
                          <span className="text-xs font-medium text-green-700">Одобрено</span>
                        </div>
                      ) : (
                        <button
                          onClick={handleApproveName}
                          disabled={isApproving}
                          className="flex items-center gap-1 px-2 py-1 bg-orange-50 border border-orange-200 rounded-full hover:bg-orange-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Одобрить имя для рассылки"
                        >
                          <Shield className="w-3 h-3 text-orange-600" />
                          <span className="text-xs font-medium text-orange-700">
                            {isApproving ? 'Одобряем...' : 'Одобрить'}
                          </span>
                        </button>
                      )
                    ) : (
                      <div className="flex items-center gap-1 px-2 py-1 bg-neutral-50 border border-neutral-200 rounded-full">
                        <X className="w-3 h-3 text-neutral-500" />
                        <span className="text-xs font-medium text-neutral-600">Нет имени</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-neutral-500 mb-1">Telegram ID</p>
              <p className="text-sm font-medium text-neutral-900 font-mono">{client.telegram_id}</p>
            </div>
            
            {client.username && (
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-neutral-500 mb-1">Username</p>
                <p className="text-sm font-medium text-neutral-900 font-mono">@{client.username}</p>
              </div>
            )}
            
            <div className="flex items-start pt-2">
              <Calendar className="w-4 h-4 text-neutral-400 mr-3 mt-0.5" />
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-neutral-500 mb-1">Дата регистрации</p>
                <p className="text-sm font-medium text-neutral-900">
                  {formatDate(client.created_at)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Статистика сообщений */}
        <div className="card p-5">
          <div className="flex items-center mb-4">
            <MessageCircle className="w-5 h-5 text-neutral-400 mr-3" />
            <h3 className="text-base font-medium text-neutral-900">Статистика</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-neutral-500 mb-1">Всего сообщений</p>
              <p className="text-2xl font-semibold text-neutral-900">
                {client.messages?.length || 0}
              </p>
            </div>
            
            {client.messages && client.messages.length > 0 && (
              <div className="pt-2 border-t border-neutral-100">
                <p className="text-xs font-medium uppercase tracking-wide text-neutral-500 mb-1">Последнее сообщение</p>
                <p className="text-sm font-medium text-neutral-700">
                  {formatDate(client.messages[0].timestamp)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* AI Досье */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <FileText className="w-5 h-5 text-neutral-400 mr-3" />
              <h3 className="text-base font-medium text-neutral-900">AI Досье</h3>
            </div>
            <button
              onClick={() => setEditingDossier(true)}
              className="text-neutral-400 hover:text-neutral-600 p-1 hover:bg-neutral-100 rounded transition-colors"
              title="Редактировать досье"
            >
              <Edit2 className="w-4 h-4" />
            </button>
          </div>
          
          {dossierFields.length > 0 ? (
            <div className="space-y-6">
              {/* Информация о клиенте */}
              {dossierFields.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-neutral-700 mb-3 flex items-center">
                    <User className="w-4 h-4 mr-2" />
                    Информация о клиенте
                  </h4>
                  <div className="space-y-4">
                    {dossierFields.map((field) => (
                      <div key={field.key} className="flex items-start gap-3">
                        {getFieldIcon(field.key)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
                              {field.title}
                            </p>
                            {field.isManuallyModified && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                Изменено вручную
                              </span>
                            )}
                          </div>
                          {field.key === 'notes' ? (
                            <p className="text-sm text-neutral-700 whitespace-pre-wrap leading-relaxed">
                              {field.value}
                            </p>
                          ) : (
                            <p className="text-sm font-medium text-neutral-900">
                              {formatFieldValue(field.key, field.value)}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {client.dossier && (
                <div className="text-xs text-neutral-500 border-t border-neutral-100 pt-3">
                  Обновлено: {formatDate(client.dossier.last_updated)}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-neutral-500 py-8">
              <FileText className="w-8 h-8 mx-auto mb-3 text-neutral-300" />
              <p className="text-sm font-medium text-neutral-600 mb-1">Досье ещё не сформировано</p>
              <p className="text-xs text-neutral-500">
                Досье будет автоматически создано после диалога с клиентом
              </p>
            </div>
          )}
        </div>

        {/* Автомобильные интересы */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Car className="w-5 h-5 text-neutral-400 mr-3" />
              <h3 className="text-base font-medium text-neutral-900">Автомобильные интересы</h3>
            </div>
            <button
              onClick={() => setEditingCarInterest(true)}
              className="text-neutral-400 hover:text-neutral-600 p-1 hover:bg-neutral-100 rounded transition-colors"
              title="Редактировать автомобильные интересы"
            >
              <Edit2 className="w-4 h-4" />
            </button>
          </div>
          
          {getCarQueries().length > 0 ? (
            <div className="space-y-4">
              {getCarQueries().map((query, index) => (
                <div key={index} className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center mt-0.5">
                      <span className="text-xs font-medium text-primary-700">{index + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-neutral-700 leading-relaxed break-words">
                        {formatCarQuery(query)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              
              <div className="text-xs text-neutral-500 border-t border-neutral-100 pt-3">
                Обновлено: {formatDate(client.car_interest!.last_updated)}
              </div>
            </div>
          ) : (
            <div className="text-center text-neutral-500 py-8">
              <Car className="w-8 h-8 mx-auto mb-3 text-neutral-300" />
              <p className="text-sm font-medium text-neutral-600 mb-1">Автомобильные интересы не определены</p>
              <p className="text-xs text-neutral-500">
                Интересы будут автоматически определены после диалога о покупке автомобиля
              </p>
            </div>
          )}
        </div>

        {/* Задачи */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <CheckSquare className="w-5 h-5 text-neutral-400 mr-3" />
              <h3 className="text-base font-medium text-neutral-900">Задачи</h3>
            </div>
            <button
              onClick={() => setCreatingTask(true)}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-colors"
              title="Добавить задачу"
            >
              <Plus className="w-4 h-4" />
              Добавить
            </button>
          </div>
          
          {creatingTask && (
            <div className="mb-4 p-4 bg-neutral-50 rounded-lg border border-neutral-200">
              <div className="flex items-center gap-2 mb-2">
                <input
                  type="text"
                  value={taskData.description}
                  onChange={(e) => setTaskData({ ...taskData, description: e.target.value })}
                  className="flex-1 text-sm font-medium text-neutral-900 bg-white border border-neutral-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Описание задачи"
                  autoFocus
                />
                <button
                  onClick={() => handleTaskCreate(taskData)}
                  disabled={isSaving}
                  className="text-green-600 hover:text-green-700 p-1 hover:bg-green-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Сохранить задачу"
                >
                  <Check className="w-3 h-3" />
                </button>
                <button
                  onClick={() => setCreatingTask(false)}
                  disabled={isSaving}
                  className="text-neutral-400 hover:text-neutral-600 p-1 hover:bg-neutral-100 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Отменить"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  value={taskData.due_date || ''}
                  onChange={(e) => setTaskData({ ...taskData, due_date: e.target.value })}
                  className="text-sm font-medium text-neutral-900 bg-white border border-neutral-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Срок выполнения"
                />
                <select
                  value={taskData.priority || 'normal'}
                  onChange={(e) => setTaskData({ ...taskData, priority: e.target.value })}
                  className="text-sm font-medium text-neutral-900 bg-white border border-neutral-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="normal">Обычный</option>
                  <option value="low">Низкий</option>
                  <option value="high">Высокий</option>
                </select>
              </div>
            </div>
          )}

          {tasks.length > 0 ? (
            <div className="space-y-4">
              {tasks.map((task, index) => (
                <div key={task.id} className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center mt-0.5">
                      <span className="text-xs font-medium text-primary-700">{index + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm text-neutral-900 font-medium mb-1">
                            {task.description}
                          </p>
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(task.priority)}`}>
                              {formatPriority(task.priority)}
                            </span>
                            {task.is_completed && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-green-700 bg-green-50 border border-green-200">
                                Выполнено
                              </span>
                            )}
                            {task.manually_modified && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                Изменено вручную
                              </span>
                            )}
                          </div>
                          {task.due_date && (
                            <p className="text-xs text-neutral-500">
                              Срок: {formatDate(task.due_date)}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => setEditingTask(task)}
                          className="text-neutral-400 hover:text-neutral-600 p-1 hover:bg-neutral-100 rounded transition-colors ml-2"
                          title="Редактировать задачу"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-neutral-500 py-8">
              <CheckSquare className="w-8 h-8 mx-auto mb-3 text-neutral-300" />
              <p className="text-sm font-medium text-neutral-600 mb-1">Задачи не определены</p>
              <p className="text-xs text-neutral-500">
                Задачи будут автоматически определены после диалога с клиентом
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};