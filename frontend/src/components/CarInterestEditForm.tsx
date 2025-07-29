import { useState, useEffect, FormEvent } from 'react';
import { Edit2, Save, X, Car, Plus, Trash2 } from 'lucide-react';
import { Client, CarInterestManualUpdate, CarQueryManualUpdate } from '../types';
import { carInterestApi } from '../services/api';

interface CarInterestEditFormProps {
  client: Client;
  onUpdate: (client: Client) => void;
  onCancel: () => void;
}

export const CarInterestEditForm = ({
  client,
  onUpdate,
  onCancel,
}: CarInterestEditFormProps) => {
  const [queries, setQueries] = useState<CarQueryManualUpdate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    // Заполняем форму текущими данными
    const existingQueries = client.car_interest?.structured_data?.queries || [];
    if (existingQueries.length > 0) {
      setQueries(existingQueries.map(query => ({ ...query })));
    } else {
      // Создаем один пустой запрос по умолчанию
      setQueries([createEmptyQuery()]);
    }
  }, [client]);

  const createEmptyQuery = (): CarQueryManualUpdate => ({
    brand: '',
    model: '',
    price_min: undefined,
    price_max: undefined,
    year_min: undefined,
    year_max: undefined,
    mileage_max: undefined,
    exterior_color: '',
    interior_color: '',
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    queries.forEach((query, index) => {
      if (query.price_min && query.price_max && query.price_min > query.price_max) {
        newErrors[`query_${index}_price`] = 'Минимальная цена не может быть больше максимальной';
      }
      if (query.year_min && query.year_max && query.year_min > query.year_max) {
        newErrors[`query_${index}_year`] = 'Минимальный год не может быть больше максимального';
      }
    });

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
      // Получаем текущие данные для сравнения
      const currentQueries = client.car_interest?.structured_data?.queries || [];
      
      // Фильтруем пустые запросы
      const filteredQueries = queries.filter(query => {
        return Object.values(query).some(value => 
          value !== undefined && value !== null && value !== ''
        );
      });

      // Проверяем, есть ли изменения
      const hasChanges = JSON.stringify(filteredQueries) !== JSON.stringify(currentQueries);
      
      if (!hasChanges) {
        console.log('Нет изменений в автомобильных интересах для сохранения');
        setIsLoading(false);
        return;
      }

      const update: CarInterestManualUpdate = {
        queries: filteredQueries
      };

      console.log('Отправляем изменения автомобильных интересов:', update);
      const response = await carInterestApi.updateManuallyByClient(client.id, update);
      
      // Обновляем клиента с новыми данными автомобильных интересов
      const updatedClient = { ...client, car_interest: response.data };
      onUpdate(updatedClient);
      
    } catch (error) {
      console.error('Ошибка обновления автомобильных интересов:', error);
      setErrors({ submit: 'Ошибка при сохранении изменений' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleQueryChange = (index: number, field: keyof CarQueryManualUpdate, value: any) => {
    setQueries(prev => 
      prev.map((query, i) => 
        i === index ? { ...query, [field]: value } : query
      )
    );
    
    // Очищаем ошибки для этого запроса
    const errorKeys = Object.keys(errors).filter(key => key.startsWith(`query_${index}_`));
    if (errorKeys.length > 0) {
      setErrors(prev => {
        const newErrors = { ...prev };
        errorKeys.forEach(key => delete newErrors[key]);
        return newErrors;
      });
    }
  };

  const addQuery = () => {
    setQueries(prev => [...prev, createEmptyQuery()]);
  };

  const removeQuery = (index: number) => {
    if (queries.length > 1) {
      setQueries(prev => prev.filter((_, i) => i !== index));
    }
  };

  const isFieldManuallyModified = (queryIndex: number, field: string): boolean => {
    const fieldKey = `queries.${queryIndex}.${field}`;
    return !!client.car_interest?.structured_data?.manual_modifications?.[fieldKey];
  };

  const parseStringOrArray = (value: string | string[]): string => {
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    return value || '';
  };

  const parseToStringOrArray = (value: string): string | string[] => {
    if (value.includes(',')) {
      return value.split(',').map(s => s.trim()).filter(s => s);
    }
    return value.trim();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-neutral-900 flex items-center">
          <Edit2 className="w-5 h-5 mr-2" />
          Редактирование автомобильных интересов
        </h3>
      </div>

      {errors.submit && (
        <div className="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg">
          {errors.submit}
        </div>
      )}

      <div className="space-y-6">
        {queries.map((query, queryIndex) => (
          <div key={queryIndex} className="p-4 border border-neutral-200 rounded-lg space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-neutral-900 flex items-center">
                <Car className="w-4 h-4 mr-2" />
                Запрос {queryIndex + 1}
              </h4>
              {queries.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeQuery(queryIndex)}
                  className="p-1 text-neutral-400 hover:text-red-600 transition-colors"
                  title="Удалить запрос"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Марка */}
              <div>
                <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
                  Марка
                  {isFieldManuallyModified(queryIndex, 'brand') && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Изменено вручную
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={parseStringOrArray(query.brand || '')}
                  onChange={(e) => handleQueryChange(queryIndex, 'brand', parseToStringOrArray(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Toyota, Honda (через запятую)"
                />
              </div>

              {/* Модель */}
              <div>
                <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
                  Модель
                  {isFieldManuallyModified(queryIndex, 'model') && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Изменено вручную
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={parseStringOrArray(query.model || '')}
                  onChange={(e) => handleQueryChange(queryIndex, 'model', parseToStringOrArray(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Camry, Accord (через запятую)"
                />
              </div>

              {/* Цена от */}
              <div>
                <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
                  Цена от, $
                  {isFieldManuallyModified(queryIndex, 'price_min') && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Изменено вручную
                    </span>
                  )}
                </label>
                <input
                  type="number"
                  value={query.price_min || ''}
                  onChange={(e) => handleQueryChange(queryIndex, 'price_min', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="10000"
                  min="0"
                />
              </div>

              {/* Цена до */}
              <div>
                <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
                  Цена до, $
                  {isFieldManuallyModified(queryIndex, 'price_max') && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Изменено вручную
                    </span>
                  )}
                </label>
                <input
                  type="number"
                  value={query.price_max || ''}
                  onChange={(e) => handleQueryChange(queryIndex, 'price_max', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="50000"
                  min="0"
                />
                {errors[`query_${queryIndex}_price`] && (
                  <p className="mt-1 text-xs text-red-600">{errors[`query_${queryIndex}_price`]}</p>
                )}
              </div>

              {/* Год от */}
              <div>
                <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
                  Год от
                  {isFieldManuallyModified(queryIndex, 'year_min') && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Изменено вручную
                    </span>
                  )}
                </label>
                <input
                  type="number"
                  value={query.year_min || ''}
                  onChange={(e) => handleQueryChange(queryIndex, 'year_min', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="2015"
                  min="1900"
                  max={new Date().getFullYear() + 1}
                />
              </div>

              {/* Год до */}
              <div>
                <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
                  Год до
                  {isFieldManuallyModified(queryIndex, 'year_max') && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Изменено вручную
                    </span>
                  )}
                </label>
                <input
                  type="number"
                  value={query.year_max || ''}
                  onChange={(e) => handleQueryChange(queryIndex, 'year_max', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="2023"
                  min="1900"
                  max={new Date().getFullYear() + 1}
                />
                {errors[`query_${queryIndex}_year`] && (
                  <p className="mt-1 text-xs text-red-600">{errors[`query_${queryIndex}_year`]}</p>
                )}
              </div>

              {/* Пробег до */}
              <div>
                <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
                  Пробег до, км
                  {isFieldManuallyModified(queryIndex, 'mileage_max') && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Изменено вручную
                    </span>
                  )}
                </label>
                <input
                  type="number"
                  value={query.mileage_max || ''}
                  onChange={(e) => handleQueryChange(queryIndex, 'mileage_max', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="100000"
                  min="0"
                />
              </div>

              {/* Цвет кузова */}
              <div>
                <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
                  Цвет кузова
                  {isFieldManuallyModified(queryIndex, 'exterior_color') && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Изменено вручную
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={parseStringOrArray(query.exterior_color || '')}
                  onChange={(e) => handleQueryChange(queryIndex, 'exterior_color', parseToStringOrArray(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Белый, Черный (через запятую)"
                />
              </div>

              {/* Цвет салона */}
              <div>
                <label className="flex items-center text-sm font-medium text-neutral-700 mb-2">
                  Цвет салона
                  {isFieldManuallyModified(queryIndex, 'interior_color') && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Изменено вручную
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={parseStringOrArray(query.interior_color || '')}
                  onChange={(e) => handleQueryChange(queryIndex, 'interior_color', parseToStringOrArray(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Серый, Бежевый (через запятую)"
                />
              </div>
            </div>
          </div>
        ))}

        {/* Добавить новый запрос */}
        <button
          type="button"
          onClick={addQuery}
          className="flex items-center px-4 py-2 text-sm font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 border border-primary-200 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          Добавить запрос
        </button>
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