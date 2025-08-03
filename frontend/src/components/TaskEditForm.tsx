import { useState, FormEvent, useEffect } from 'react';
import { Edit2, Save, X, Calendar, AlertTriangle, CheckSquare, Trash2, Zap, Plus } from 'lucide-react';
import { Task, TaskManualUpdate, Trigger } from '../types';
import { tasksApi, triggersApi } from '../services/api';
import { TriggerForm } from './TriggerForm';
import { Modal } from './Modal';

interface TaskEditFormProps {
  task: Task;
  onUpdate: (task: Task) => void;
  onDelete?: (taskId: number) => void;
  onCancel: () => void;
}

export const TaskEditForm = ({
  task,
  onUpdate,
  onDelete,
  onCancel,
}: TaskEditFormProps) => {
  const [formData, setFormData] = useState<TaskManualUpdate>({
    description: task.description,
    due_date: task.due_date || undefined,
    is_completed: task.is_completed,
    priority: task.priority,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showTriggerModal, setShowTriggerModal] = useState(false);
  const [trigger, setTrigger] = useState<Trigger | null>(null);
  const [loadingTrigger, setLoadingTrigger] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.description || formData.description.trim() === '') {
      newErrors.description = 'Описание задачи обязательно';
    }

    if (formData.due_date && !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?$/.test(formData.due_date)) {
      newErrors.due_date = 'Дата должна быть в формате YYYY-MM-DD или YYYY-MM-DDTHH:MM:SS';
    }

    if (formData.priority && !['low', 'normal', 'high'].includes(formData.priority)) {
      newErrors.priority = 'Приоритет должен быть: low, normal или high';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      // Отправляем только измененные поля
      const update: TaskManualUpdate = {};
      let hasChanges = false;
      
      if (formData.description !== task.description) {
        update.description = formData.description;
        hasChanges = true;
      }
      // Compare dates by converting both to date-only format for comparison
      const formDataDate = formData.due_date ? formatDate(formData.due_date) : null;
      const taskDate = task.due_date ? formatDate(task.due_date) : null;
      if (formDataDate !== taskDate) {
        update.due_date = formData.due_date;
        hasChanges = true;
      }
      if (formData.is_completed !== task.is_completed) {
        update.is_completed = formData.is_completed;
        hasChanges = true;
      }
      if (formData.priority !== task.priority) {
        update.priority = formData.priority;
        hasChanges = true;
      }

      // Если нет изменений, не отправляем запрос
      if (!hasChanges) {
        console.log('Нет изменений в задаче для сохранения');
        setIsLoading(false);
        return;
      }

      console.log('Отправляем изменения задачи:', update);
      const response = await tasksApi.updateManually(task.id, update);
      onUpdate(response.data);
      
    } catch (error) {
      console.error('Ошибка обновления задачи:', error);
      setErrors({ submit: 'Ошибка при сохранении изменений' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!onDelete || !confirm('Вы уверены, что хотите удалить эту задачу?')) {
      return;
    }

    setIsDeleting(true);
    try {
      await tasksApi.delete(task.id);
      onDelete(task.id);
      onCancel(); // Закрываем форму после успешного удаления
    } catch (error) {
      console.error('Ошибка удаления задачи:', error);
      setErrors({ submit: 'Ошибка при удалении задачи' });
    } finally {
      setIsDeleting(false);
    }
  };

  // Загружаем информацию о триггере, если он связан с задачей
  useEffect(() => {
    if (task.trigger_id) {
      setLoadingTrigger(true);
      triggersApi.getById(task.trigger_id)
        .then(response => {
          setTrigger(response.data);
        })
        .catch(error => {
          console.error('Ошибка загрузки триггера:', error);
        })
        .finally(() => {
          setLoadingTrigger(false);
        });
    }
  }, [task.trigger_id]);

  const isFieldManuallyModified = (field: string): boolean => {
    return !!task.extra_data?.manual_modifications?.[field];
  };

  const handleChange = (field: keyof TaskManualUpdate, value: any) => {
    let processedValue = value;
    
    // Convert date string to ISO datetime format for the backend
    if (field === 'due_date' && value && typeof value === 'string') {
      // If it's a date string (YYYY-MM-DD), convert to datetime with 08:00:00 time
      if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        processedValue = `${value}T08:00:00`;
      }
    }
    
    setFormData(prev => ({ ...prev, [field]: processedValue }));
    // Очищаем ошибку для этого поля
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleTriggerCreated = (createdTrigger: any) => {
    console.log('Триггер создан:', createdTrigger);
    setShowTriggerModal(false);
    // Можно обновить информацию о триггере или перезагрузить задачу
  };

  const handleToggleTrigger = async () => {
    if (!trigger) return;
    
    try {
      const response = await triggersApi.toggle(trigger.id);
      setTrigger(prev => prev ? { ...prev, status: response.data.trigger.status } : null);
    } catch (error) {
      console.error('Ошибка переключения триггера:', error);
    }
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'high':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'low':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      default:
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <AlertTriangle className="w-4 h-4" />;
      case 'low':
        return <CheckSquare className="w-4 h-4" />;
      default:
        return <Calendar className="w-4 h-4" />;
    }
  };

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

  const formatDate = (dateString: string | undefined): string => {
    if (!dateString) return '';
    try {
      return dateString.split('T')[0]; // Возвращаем только дату без времени
    } catch {
      return dateString;
    }
  };

  return (
    <>
      {/* Модальное окно для создания триггера */}
      <Modal
        isOpen={showTriggerModal}
        onClose={() => setShowTriggerModal(false)}
        title="Создание триггера"
        size="xl"
      >
        <TriggerForm
          clientId={task.client_id}
          onTriggerCreated={handleTriggerCreated}
          onCancel={() => setShowTriggerModal(false)}
        />
      </Modal>

      <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-neutral-900 flex items-center">
          <Edit2 className="w-5 h-5 mr-2" />
          Редактирование задачи
        </h3>
        {onDelete && (
          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-2 text-neutral-400 hover:text-red-600 transition-colors disabled:opacity-50"
            title="Удалить задачу"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {errors.submit && (
        <div className="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg">
          {errors.submit}
        </div>
      )}

      {/* Текущая информация о задаче */}
      <div className="p-4 bg-neutral-50 rounded-lg border border-neutral-200">
        <h4 className="text-sm font-medium text-neutral-700 mb-3">Текущая информация:</h4>
        <div className="space-y-2 text-xs text-neutral-600">
          <div>Создана: {new Date(task.created_at).toLocaleString('ru-RU')}</div>
          <div>Обновлена: {new Date(task.updated_at).toLocaleString('ru-RU')}</div>
          <div>Источник: {task.source === 'trigger' ? 'Триггер' : task.source === 'ai' ? 'ИИ' : 'Ручное создание'}</div>
          {task.manually_modified && (
            <div className="flex items-center">
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2">
                Изменено вручную
              </span>
              {task.manual_modification_time && (
                <span>
                  {new Date(task.manual_modification_time).toLocaleString('ru-RU')}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Информация о триггере */}
      {(task.trigger_id || trigger) && (
        <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
          <h4 className="text-sm font-medium text-purple-900 mb-3 flex items-center">
            <Zap className="w-4 h-4 mr-2" />
            Связанный триггер
          </h4>
          {loadingTrigger ? (
            <div className="text-sm text-neutral-600">Загрузка информации о триггере...</div>
          ) : trigger ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-purple-900">{trigger.name}</div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    trigger.status === 'active' 
                      ? 'bg-green-100 text-green-800' 
                      : trigger.status === 'paused'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {trigger.status === 'active' ? 'Активен' : trigger.status === 'paused' ? 'Приостановлен' : 'Неактивен'}
                  </span>
                  <button
                    type="button"
                    onClick={handleToggleTrigger}
                    className="px-2 py-1 text-xs text-purple-600 hover:text-purple-700 border border-purple-300 rounded transition-colors"
                  >
                    {trigger.status === 'active' ? 'Остановить' : 'Активировать'}
                  </button>
                </div>
              </div>
              {trigger.description && (
                <div className="text-xs text-purple-700">{trigger.description}</div>
              )}
              <div className="text-xs text-purple-600">
                Срабатывал: {trigger.trigger_count} раз
                {trigger.last_triggered_at && (
                  <span className="ml-2">
                    (последний раз: {new Date(trigger.last_triggered_at).toLocaleString('ru-RU')})
                  </span>
                )}
              </div>
              <div className="text-xs text-purple-600">
                Действие: {trigger.action_type === 'create_task' ? 'Создание задач' : 'Уведомления'}
              </div>
            </div>
          ) : (
            <div className="text-sm text-neutral-600">Не удалось загрузить информацию о триггере</div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {/* Описание */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            <Edit2 className="w-4 h-4 mr-2" />
            Описание задачи
            {isFieldManuallyModified('description') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <textarea
            value={formData.description || ''}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            placeholder="Описание задачи..."
            required
          />
          {errors.description && (
            <p className="mt-1 text-xs text-red-600">{errors.description}</p>
          )}
        </div>

        {/* Срок выполнения */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            <Calendar className="w-4 h-4 mr-2" />
            Срок выполнения
            {isFieldManuallyModified('due_date') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <input
            type="date"
            value={formatDate(formData.due_date)}
            onChange={(e) => handleChange('due_date', e.target.value || undefined)}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          {errors.due_date && (
            <p className="mt-1 text-xs text-red-600">{errors.due_date}</p>
          )}
        </div>

        {/* Приоритет */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            {getPriorityIcon(formData.priority || 'normal')}
            <span className="ml-2">Приоритет</span>
            {isFieldManuallyModified('priority') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <select
            value={formData.priority || 'normal'}
            onChange={(e) => handleChange('priority', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="low">Низкий</option>
            <option value="normal">Обычный</option>
            <option value="high">Высокий</option>
          </select>
          {errors.priority && (
            <p className="mt-1 text-xs text-red-600">{errors.priority}</p>
          )}
          {/* Показываем текущий приоритет */}
          <div className="mt-2">
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(formData.priority || 'normal')}`}>
              {getPriorityIcon(formData.priority || 'normal')}
              <span className="ml-1">{formatPriority(formData.priority || 'normal')}</span>
            </span>
          </div>
        </div>

        {/* Статус выполнения */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            <CheckSquare className="w-4 h-4 mr-2" />
            Статус
            {isFieldManuallyModified('is_completed') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_completed || false}
                onChange={(e) => handleChange('is_completed', e.target.checked)}
                className="w-4 h-4 text-primary-600 bg-neutral-100 border-neutral-300 rounded focus:ring-primary-500 focus:ring-2"
              />
              <span className="ml-2 text-sm text-neutral-700">
                Задача выполнена
              </span>
            </label>
            {formData.is_completed && (
              <div className="ml-6">
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-green-700 bg-green-50 border border-green-200">
                  <CheckSquare className="w-3 h-3 mr-1" />
                  Выполнено
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Кнопки */}
      <div className="flex justify-between items-center pt-4 border-t border-neutral-200">
        {/* Кнопка создания триггера */}
        {!task.trigger_id && (
          <button
            type="button"
            onClick={() => setShowTriggerModal(true)}
            className="px-4 py-2 text-sm font-medium text-purple-700 bg-purple-100 hover:bg-purple-200 rounded-lg transition-colors flex items-center"
          >
            <Plus className="w-4 h-4 mr-1" />
            Создать триггер
          </button>
        )}
        
        {/* Основные кнопки */}
        <div className="flex space-x-3 ml-auto">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
            disabled={isLoading || isDeleting}
          >
            <X className="w-4 h-4 mr-1 inline" />
            Отменить
          </button>
          <button
            type="submit"
            disabled={isLoading || isDeleting}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            <Save className="w-4 h-4 mr-1 inline" />
            {isLoading ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </form>
    </>
  );
}; 