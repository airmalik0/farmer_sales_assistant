import { useState, FormEvent } from 'react';
import { 
  Zap, 
  Save, 
  X, 
  Plus, 
  AlertTriangle, 
  Bell, 
  Settings, 
  Car,
  Calendar,
  DollarSign,
  MapPin,
  Trash2
} from 'lucide-react';
import { 
  TriggerConditions, 
  TriggerActionConfig, 
  Trigger 
} from '../types';
import { taskTriggersApi, triggersApi } from '../services/api';

interface TriggerFormProps {
  clientId: number;
  onTriggerCreated?: (trigger: any) => void;
  onCancel: () => void;
  existingTrigger?: Trigger;
}

export const TriggerForm = ({
  clientId,
  onTriggerCreated,
  onCancel,
  existingTrigger,
}: TriggerFormProps) => {
  const [formData, setFormData] = useState<{
    name: string;
    description: string;
    conditions: TriggerConditions;
    action_type: 'notify' | 'create_task';
    action_config: TriggerActionConfig;
    check_interval_minutes: number;
  }>({
    name: existingTrigger?.name || '',
    description: existingTrigger?.description || '',
    conditions: existingTrigger?.conditions || {},
    action_type: existingTrigger?.action_type === 'create_task' ? 'create_task' : 'notify',
    action_config: existingTrigger?.action_config || {},
    check_interval_minutes: existingTrigger?.check_interval_minutes || 5,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleConditionChange = (field: keyof TriggerConditions, value: any) => {
    setFormData(prev => ({
      ...prev,
      conditions: {
        ...prev.conditions,
        [field]: value,
      },
    }));
  };

  const handleActionConfigChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      action_config: {
        ...prev.action_config,
        [field]: value,
      },
    }));
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Название триггера обязательно';
    }

    // Проверяем, что есть хотя бы одно условие
    const hasConditions = Object.values(formData.conditions).some(
      value => {
        if (Array.isArray(value)) {
          return value.some(item => item && item.toString().trim() !== '');
        }
        return value !== undefined && value !== null && value.toString().trim() !== '';
      }
    );
    if (!hasConditions) {
      newErrors.conditions = 'Необходимо указать хотя бы одно условие';
    }

    // Валидация ценового диапазона
    if (formData.conditions.price_min && formData.conditions.price_max) {
      if (formData.conditions.price_min >= formData.conditions.price_max) {
        newErrors.price_range = 'Минимальная цена должна быть меньше максимальной';
      }
    }

    // Валидация годового диапазона
    if (formData.conditions.year_min && formData.conditions.year_max) {
      if (formData.conditions.year_min > formData.conditions.year_max) {
        newErrors.year_range = 'Минимальный год должен быть меньше или равен максимальному';
      }
    }

    // Проверяем конфигурацию действия
    if (formData.action_type === 'notify' && !formData.action_config.message?.trim()) {
      newErrors.action_message = 'Сообщение для уведомления обязательно';
    }

    if (formData.action_type === 'create_task' && !formData.action_config.title?.trim()) {
      newErrors.action_title = 'Заголовок задачи обязателен';
    }

    console.log('🔍 Валидация:', {
      formData,
      conditions: formData.conditions,
      hasConditions,
      errors: newErrors
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    console.log('🚀 Отправка формы триггера начата');
    console.log('📝 Данные формы:', formData);
    
    if (!validateForm()) {
      console.log('❌ Валидация не прошла');
      return;
    }

    setIsLoading(true);
    try {
      if (existingTrigger) {
        console.log('🔄 Обновление существующего триггера');
        // Обновляем существующий триггер
        const response = await triggersApi.update(existingTrigger.id, {
          name: formData.name,
          description: formData.description,
          conditions: formData.conditions,
          action_type: formData.action_type,
          action_config: formData.action_config,
          check_interval_minutes: formData.check_interval_minutes,
        });
        console.log('✅ Триггер обновлен:', response.data);
        onTriggerCreated?.(response.data);
      } else {
        console.log('🆕 Создание нового триггера');
        // Создаем новый триггер
        if (formData.action_type === 'create_task') {
          console.log('📋 Создаем триггер для создания задач');
          // Создаем триггер, который будет создавать задачи
          const requestData = {
            client_id: clientId,
            description: formData.action_config.description || 'Автоматическая задача',
            priority: formData.action_config.priority || 'normal',
            trigger_name: formData.name,
            trigger_conditions: formData.conditions,
          };
          console.log('📤 Отправляемые данные для createWithTrigger:', requestData);
          
          const response = await taskTriggersApi.createWithTrigger(requestData);
          console.log('✅ Триггер создан:', response.data);
          onTriggerCreated?.(response.data);
        } else {
          console.log('🔔 Создаем триггер для уведомлений');
          // Создаем триггер уведомлений
          const requestData = {
            trigger_name: formData.name,
            conditions: formData.conditions,
            message: formData.action_config.message || 'Найден подходящий автомобиль!',
            channels: formData.action_config.channels || ['telegram'],
            check_interval: formData.check_interval_minutes,
          };
          console.log('📤 Отправляемые данные для createNotificationTrigger:', requestData);
          
          const response = await taskTriggersApi.createNotificationTrigger(requestData);
          console.log('✅ Триггер создан:', response.data);
          onTriggerCreated?.(response.data);
        }
      }
    } catch (error: any) {
      console.error('❌ Ошибка создания/обновления триггера:', error);
      console.error('📊 Подробности ошибки:', {
        message: error?.message,
        response: error?.response?.data,
        status: error?.response?.status,
      });
      
      // Более подробное сообщение об ошибке
      let errorMessage = 'Ошибка при сохранении триггера';
      if (error?.response?.data?.detail) {
        // Если detail это объект или массив, преобразуем в строку
        if (typeof error.response.data.detail === 'object') {
          // Если это массив ошибок валидации от FastAPI
          if (Array.isArray(error.response.data.detail)) {
            errorMessage = error.response.data.detail
              .map((err: any) => err.msg || err.message || String(err))
              .join(', ');
          } else {
            errorMessage = JSON.stringify(error.response.data.detail);
          }
        } else {
          errorMessage = String(error.response.data.detail);
        }
      } else if (error?.message) {
        errorMessage = String(error.message);
      }
      
      setErrors({ submit: errorMessage });
    } finally {
      setIsLoading(false);
      console.log('🏁 Обработка формы завершена');
    }
  };



  const addBrandOrModel = (field: 'brand' | 'model') => {
    const currentValue = formData.conditions[field];
    if (typeof currentValue === 'string') {
      handleConditionChange(field, [currentValue, '']);
    } else if (Array.isArray(currentValue)) {
      handleConditionChange(field, [...currentValue, '']);
    } else {
      handleConditionChange(field, ['']);
    }
  };

  const removeBrandOrModel = (field: 'brand' | 'model', index: number) => {
    const currentValue = formData.conditions[field];
    if (Array.isArray(currentValue)) {
      const newArray = currentValue.filter((_, i) => i !== index);
      handleConditionChange(field, newArray.length === 1 ? newArray[0] : newArray);
    }
  };

  const updateBrandOrModel = (field: 'brand' | 'model', index: number, value: string) => {
    const currentValue = formData.conditions[field];
    if (Array.isArray(currentValue)) {
      const newArray = [...currentValue];
      newArray[index] = value;
      handleConditionChange(field, newArray);
    }
  };

  const renderBrandModelField = (field: 'brand' | 'model', label: string, icon: any) => {
    const value = formData.conditions[field];
    const isArray = Array.isArray(value);
    const items = isArray ? value : [value || ''];

    return (
      <div>
        <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
          {icon}
          <span className="ml-2">{label}</span>
        </label>
        <div className="space-y-2">
          {items.map((item, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type="text"
                value={item || ''}
                onChange={(e) => 
                  isArray 
                    ? updateBrandOrModel(field, index, e.target.value)
                    : handleConditionChange(field, e.target.value)
                }
                className="flex-1 px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder={`${label}...`}
              />
              {isArray && items.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeBrandOrModel(field, index)}
                  className="p-2 text-neutral-400 hover:text-red-600 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={() => addBrandOrModel(field)}
            className="flex items-center px-3 py-2 text-sm text-primary-600 hover:text-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4 mr-1" />
            Добавить {label.toLowerCase()}
          </button>
        </div>
      </div>
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-neutral-900 flex items-center">
          <Zap className="w-5 h-5 mr-2" />
          {existingTrigger ? 'Редактирование триггера' : 'Создание триггера'}
        </h3>
      </div>

      {errors.submit && (
        <div className="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg">
          {errors.submit}
        </div>
      )}

      {/* Основная информация */}
      <div className="space-y-4">
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            <Settings className="w-4 h-4 mr-2" />
            Название триггера
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Например: BMW дешевле $50k"
            required
          />
          {errors.name && (
            <p className="mt-1 text-xs text-red-600">{errors.name}</p>
          )}
        </div>

        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            <Settings className="w-4 h-4 mr-2" />
            Описание
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            rows={2}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            placeholder="Описание триггера..."
          />
        </div>
      </div>

      {/* Условия срабатывания */}
      <div className="space-y-4">
        <h4 className="text-md font-medium text-neutral-900 flex items-center">
          <AlertTriangle className="w-4 h-4 mr-2" />
          Условия срабатывания
        </h4>
        {errors.conditions && (
          <p className="text-xs text-red-600">{errors.conditions}</p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* ID автомобиля */}
          <div>
            <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
              <Car className="w-4 h-4 mr-2" />
              ID автомобиля
            </label>
            <input
              type="text"
              value={formData.conditions.car_id || ''}
              onChange={(e) => handleConditionChange('car_id', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Например: GE-38"
            />
          </div>

          {/* Локация */}
          <div>
            <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
              <MapPin className="w-4 h-4 mr-2" />
              Локация
            </label>
            <input
              type="text"
              value={formData.conditions.location || ''}
              onChange={(e) => handleConditionChange('location', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Например: Авто в Тбилиси"
            />
          </div>
        </div>

        {/* Марка и модель */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {renderBrandModelField('brand', 'Марка', <Car className="w-4 h-4" />)}
          {renderBrandModelField('model', 'Модель', <Car className="w-4 h-4" />)}
        </div>

        {/* Цена */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
              <DollarSign className="w-4 h-4 mr-2" />
              Цена от
            </label>
            <input
              type="number"
              value={formData.conditions.price_min || ''}
              onChange={(e) => handleConditionChange('price_min', e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="0"
              min="0"
            />
          </div>
          <div>
            <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
              <DollarSign className="w-4 h-4 mr-2" />
              Цена до
            </label>
            <input
              type="number"
              value={formData.conditions.price_max || ''}
              onChange={(e) => handleConditionChange('price_max', e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="999999"
              min="0"
            />
          </div>
          {errors.price_range && (
            <div className="col-span-full">
              <p className="text-xs text-red-600">{errors.price_range}</p>
            </div>
          )}
        </div>

        {/* Год */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
              <Calendar className="w-4 h-4 mr-2" />
              Год от
            </label>
            <input
              type="number"
              value={formData.conditions.year_min || ''}
              onChange={(e) => handleConditionChange('year_min', e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="2000"
              min="1900"
              max={new Date().getFullYear()}
            />
          </div>
          <div>
            <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
              <Calendar className="w-4 h-4 mr-2" />
              Год до
            </label>
            <input
              type="number"
              value={formData.conditions.year_max || ''}
              onChange={(e) => handleConditionChange('year_max', e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="2024"
              min="1900"
              max={new Date().getFullYear()}
            />
          </div>
          {errors.year_range && (
            <div className="col-span-full">
              <p className="text-xs text-red-600">{errors.year_range}</p>
            </div>
          )}
        </div>

        {/* Пробег */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            <Car className="w-4 h-4 mr-2" />
            Максимальный пробег (км)
          </label>
          <input
            type="number"
            value={formData.conditions.mileage_max || ''}
            onChange={(e) => handleConditionChange('mileage_max', e.target.value ? Number(e.target.value) : undefined)}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="100000"
            min="0"
          />
        </div>
      </div>

      {/* Тип действия */}
      <div className="space-y-4">
        <h4 className="text-md font-medium text-neutral-900 flex items-center">
          <Bell className="w-4 h-4 mr-2" />
          Действие при срабатывании
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="flex items-center p-4 border border-neutral-300 rounded-lg cursor-pointer hover:bg-neutral-50">
            <input
              type="radio"
              name="action_type"
              value="notify"
              checked={formData.action_type === 'notify'}
              onChange={(e) => setFormData(prev => ({ ...prev, action_type: e.target.value as 'notify' | 'create_task' }))}
              className="mr-3"
            />
            <div>
              <div className="font-medium text-neutral-900">Уведомление</div>
              <div className="text-sm text-neutral-600">Отправить уведомление в Telegram</div>
            </div>
          </label>

          <label className="flex items-center p-4 border border-neutral-300 rounded-lg cursor-pointer hover:bg-neutral-50">
            <input
              type="radio"
              name="action_type"
              value="create_task"
              checked={formData.action_type === 'create_task'}
              onChange={(e) => setFormData(prev => ({ ...prev, action_type: e.target.value as 'notify' | 'create_task' }))}
              className="mr-3"
            />
            <div>
              <div className="font-medium text-neutral-900">Создать задачу</div>
              <div className="text-sm text-neutral-600">Автоматически создать задачу</div>
            </div>
          </label>
        </div>

        {/* Конфигурация действия */}
        {formData.action_type === 'notify' && (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Текст уведомления
              </label>
              <textarea
                value={formData.action_config.message || ''}
                onChange={(e) => handleActionConfigChange('message', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                placeholder="Найден автомобиль, подходящий под ваши критерии!"
                required
              />
              {errors.action_message && (
                <p className="mt-1 text-xs text-red-600">{errors.action_message}</p>
              )}
            </div>
          </div>
        )}

        {formData.action_type === 'create_task' && (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Заголовок задачи
              </label>
              <input
                type="text"
                value={formData.action_config.title || ''}
                onChange={(e) => handleActionConfigChange('title', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Проверить новый автомобиль"
                required
              />
              {errors.action_title && (
                <p className="mt-1 text-xs text-red-600">{errors.action_title}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Описание задачи
              </label>
              <textarea
                value={formData.action_config.description || ''}
                onChange={(e) => handleActionConfigChange('description', e.target.value)}
                rows={2}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                placeholder="Проверить новый автомобиль, соответствующий критериям"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Приоритет задачи
              </label>
              <select
                value={formData.action_config.priority || 'normal'}
                onChange={(e) => handleActionConfigChange('priority', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="low">Низкий</option>
                <option value="normal">Обычный</option>
                <option value="high">Высокий</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Интервал проверки */}
      <div>
        <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
          <Calendar className="w-4 h-4 mr-2" />
          Интервал проверки (минуты)
        </label>
        <select
          value={formData.check_interval_minutes}
          onChange={(e) => setFormData(prev => ({ ...prev, check_interval_minutes: Number(e.target.value) }))}
          className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value={5}>Каждые 5 минут</option>
          <option value={15}>Каждые 15 минут</option>
          <option value={30}>Каждые 30 минут</option>
          <option value={60}>Каждый час</option>
          <option value={360}>Каждые 6 часов</option>
          <option value={1440}>Каждый день</option>
        </select>
      </div>

      {/* Кнопки */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-neutral-200">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
          disabled={isLoading}
        >
          <X className="w-4 h-4 mr-1 inline" />
          Отменить
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
        >
          <Save className="w-4 h-4 mr-1 inline" />
          {isLoading ? 'Сохранение...' : existingTrigger ? 'Обновить' : 'Создать триггер'}
        </button>
      </div>
    </form>
  );
}; 