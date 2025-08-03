import { useState, useEffect, FormEvent } from 'react';
import { Edit2, Save, X, User, Phone, MapPin, Cake, UserCheck, FileTextIcon, Building, Briefcase } from 'lucide-react';
import { Client, DossierManualUpdate } from '../types';
import { dossierApi } from '../services/api';

interface DossierEditFormProps {
  client: Client;
  onUpdate: (client: Client) => void;
  onCancel: () => void;
}

export const DossierEditForm = ({
  client,
  onUpdate,
  onCancel,
}: DossierEditFormProps) => {
  const [formData, setFormData] = useState<DossierManualUpdate>({
    phone: '',
    current_location: '',
    birthday: '',
    gender: '',
    client_type: '',
    personal_notes: '',
    business_profile: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    // Заполняем форму текущими данными
    const clientInfo = client.dossier?.structured_data?.client_info || {};
    setFormData({
      phone: clientInfo.phone || '',
      current_location: clientInfo.current_location || '',
      birthday: clientInfo.birthday || '',
      gender: clientInfo.gender || '',
      client_type: clientInfo.client_type || '',
      personal_notes: clientInfo.personal_notes || '',
      business_profile: clientInfo.business_profile || '',
    });
  }, [client]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (formData.birthday && !/^\d{4}-\d{2}-\d{2}$/.test(formData.birthday)) {
      newErrors.birthday = 'Дата должна быть в формате YYYY-MM-DD';
    }

    if (formData.gender && !['male', 'female'].includes(formData.gender)) {
      newErrors.gender = 'Пол должен быть "male" или "female"';
    }

    if (formData.client_type && !['private', 'reseller', 'broker', 'dealer', 'transporter'].includes(formData.client_type)) {
      newErrors.client_type = 'Неверный тип клиента';
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
      // Получаем текущие данные досье для сравнения
      const currentClientInfo = client.dossier?.structured_data?.client_info || {};
      
      // Отправляем только измененные поля
      const update: DossierManualUpdate = {};
      Object.entries(formData).forEach(([key, newValue]) => {
        const currentValue = currentClientInfo[key] || '';
        const normalizedNewValue = newValue || '';
        const normalizedCurrentValue = currentValue || '';
        
        // Сравниваем нормализованные значения
        if (normalizedNewValue !== normalizedCurrentValue) {
          update[key as keyof DossierManualUpdate] = newValue;
        }
      });

      // Если нет изменений, не отправляем запрос
      if (Object.keys(update).length === 0) {
        console.log('Нет изменений для сохранения');
        setIsLoading(false);
        return;
      }

      console.log('Отправляем изменения:', update);
      const response = await dossierApi.updateManuallyByClient(client.id, update);
      
      // Обновляем клиента с новыми данными досье
      const updatedClient = { ...client, dossier: response.data };
      onUpdate(updatedClient);
      
    } catch (error) {
      console.error('Ошибка обновления досье:', error);
      setErrors({ submit: 'Ошибка при сохранении изменений' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: keyof DossierManualUpdate, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Очищаем ошибку для этого поля
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const isFieldManuallyModified = (field: string): boolean => {
    return !!client.dossier?.structured_data?.manual_modifications?.[field];
  };

  const getFieldIcon = (field: string) => {
    const icons: Record<string, any> = {
      phone: Phone,
      current_location: MapPin,
      birthday: Cake,
      gender: UserCheck,
      client_type: Building,
      personal_notes: User,
      business_profile: Briefcase,
    };
    const IconComponent = icons[field] || User;
    return <IconComponent className="w-4 h-4" />;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-neutral-900 flex items-center">
          <Edit2 className="w-5 h-5 mr-2" />
          Редактирование досье
        </h3>
      </div>

      {errors.submit && (
        <div className="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg">
          {errors.submit}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {/* Телефон */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            {getFieldIcon('phone')}
            <span className="ml-2">Телефон</span>
            {isFieldManuallyModified('phone') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <input
            type="tel"
            value={formData.phone || ''}
            onChange={(e) => handleChange('phone', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="+7 (999) 123-45-67"
          />
          {errors.phone && (
            <p className="mt-1 text-xs text-red-600">{errors.phone}</p>
          )}
        </div>

        {/* Местоположение */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            {getFieldIcon('current_location')}
            <span className="ml-2">Местоположение</span>
            {isFieldManuallyModified('current_location') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <input
            type="text"
            value={formData.current_location || ''}
            onChange={(e) => handleChange('current_location', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Москва"
          />
          {errors.current_location && (
            <p className="mt-1 text-xs text-red-600">{errors.current_location}</p>
          )}
        </div>

        {/* День рождения */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            {getFieldIcon('birthday')}
            <span className="ml-2">День рождения</span>
            {isFieldManuallyModified('birthday') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <input
            type="date"
            value={formData.birthday || ''}
            onChange={(e) => handleChange('birthday', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          {errors.birthday && (
            <p className="mt-1 text-xs text-red-600">{errors.birthday}</p>
          )}
        </div>

        {/* Пол */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            {getFieldIcon('gender')}
            <span className="ml-2">Пол</span>
            {isFieldManuallyModified('gender') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <select
            value={formData.gender || ''}
            onChange={(e) => handleChange('gender', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">Не указан</option>
            <option value="male">Мужской</option>
            <option value="female">Женский</option>
          </select>
          {errors.gender && (
            <p className="mt-1 text-xs text-red-600">{errors.gender}</p>
          )}
        </div>

        {/* Тип клиента */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            {getFieldIcon('client_type')}
            <span className="ml-2">Тип клиента</span>
            {isFieldManuallyModified('client_type') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <select
            value={formData.client_type || ''}
            onChange={(e) => handleChange('client_type', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">Не указан</option>
            <option value="private">Частное лицо</option>
            <option value="reseller">Перепродавец</option>
            <option value="broker">Брокер</option>
            <option value="dealer">Дилер</option>
            <option value="transporter">Перевозчик</option>
          </select>
          {errors.client_type && (
            <p className="mt-1 text-xs text-red-600">{errors.client_type}</p>
          )}
        </div>

        {/* Личные заметки */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            {getFieldIcon('personal_notes')}
            <span className="ml-2">Личные заметки</span>
            {isFieldManuallyModified('personal_notes') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <textarea
            value={formData.personal_notes || ''}
            onChange={(e) => handleChange('personal_notes', e.target.value)}
            rows={4}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            placeholder="Дополнительная информация о клиенте..."
          />
          {errors.personal_notes && (
            <p className="mt-1 text-xs text-red-600">{errors.personal_notes}</p>
          )}
        </div>

        {/* Бизнес-профиль */}
        <div>
          <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
            {getFieldIcon('business_profile')}
            <span className="ml-2">Бизнес-профиль</span>
            {isFieldManuallyModified('business_profile') && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Изменено вручную
              </span>
            )}
          </label>
          <textarea
            value={formData.business_profile || ''}
            onChange={(e) => handleChange('business_profile', e.target.value)}
            rows={4}
            className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            placeholder="Дополнительная информация о бизнесе клиента..."
          />
          {errors.business_profile && (
            <p className="mt-1 text-xs text-red-600">{errors.business_profile}</p>
          )}
        </div>
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
          {isLoading ? 'Сохранение...' : 'Сохранить'}
        </button>
      </div>
    </form>
  );
}; 