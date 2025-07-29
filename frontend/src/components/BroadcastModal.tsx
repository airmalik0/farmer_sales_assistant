import { useState, useEffect } from 'react';
import { X, Send, AlertTriangle, Users, CheckCircle, Settings, Eye, Trash2, Save } from 'lucide-react';
import { telegramApi, settingsApi } from '../services/api';
import { BroadcastValidation, GreetingResponse, GreetingPreview } from '../types';

interface BroadcastModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const BroadcastModal = ({ isOpen, onClose, onSuccess }: BroadcastModalProps) => {
  const [step, setStep] = useState<'validation' | 'compose' | 'sending' | 'greeting'>('validation');
  const [validation, setValidation] = useState<BroadcastValidation | null>(null);
  const [message, setMessage] = useState('');
  const [includeGreeting, setIncludeGreeting] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Состояния для управления приветствием
  const [currentGreeting, setCurrentGreeting] = useState<GreetingResponse | null>(null);
  const [editingGreeting, setEditingGreeting] = useState('');
  const [greetingPreview, setGreetingPreview] = useState<GreetingPreview | null>(null);
  const [greetingLoading, setGreetingLoading] = useState(false);

  // Загрузка валидации при открытии модалки
  useEffect(() => {
    if (isOpen) {
      loadValidation();
      loadCurrentGreeting();
    }
  }, [isOpen]);

  const loadValidation = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await telegramApi.validateBroadcast();
      setValidation(response.data);
      
      // Переходим к составлению только если действительно нет проблем
      const hasNoIssues = response.data.clients_without_names.length === 0 && 
                          response.data.clients_with_unapproved_names.length === 0;
      
      if (response.data.can_broadcast && hasNoIssues) {
        setStep('compose');
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка при проверке клиентов';
      setError(errorMessage);
      console.error('Validation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentGreeting = async () => {
    setGreetingLoading(true);
    try {
      const response = await settingsApi.getGreeting();
      setCurrentGreeting(response.data);
    } catch (err: any) {
      console.error('Error loading greeting:', err);
      setError('Ошибка при загрузке приветствия');
    } finally {
      setGreetingLoading(false);
    }
  };

  const updateGreeting = async (greetingText: string, enabled: boolean = true) => {
    setGreetingLoading(true);
    try {
      const response = await settingsApi.setGreeting(greetingText, enabled);
      setCurrentGreeting(response.data);
      setEditingGreeting('');
      setGreetingPreview(null);
      setStep('compose');
    } catch (err: any) {
      console.error('Error updating greeting:', err);
      setError('Ошибка при обновлении приветствия');
    } finally {
      setGreetingLoading(false);
    }
  };

  const clearGreeting = async () => {
    setGreetingLoading(true);
    try {
      await settingsApi.clearGreeting();
      await loadCurrentGreeting(); // Перезагружаем приветствие
      setStep('compose');
    } catch (err: any) {
      console.error('Error clearing greeting:', err);
      setError('Ошибка при очистке приветствия');
    } finally {
      setGreetingLoading(false);
    }
  };

  const previewGreeting = async (text: string) => {
    if (!text.trim()) {
      setGreetingPreview(null);
      return;
    }
    
    try {
      const response = await settingsApi.previewGreeting(text);
      setGreetingPreview(response.data);
    } catch (err: any) {
      console.error('Error previewing greeting:', err);
    }
  };

  const handleSendBroadcast = async () => {
    if (!message.trim()) return;
    
    setStep('sending');
    setError('');
    try {
      await telegramApi.broadcast(message.trim(), 'text', includeGreeting);
      onSuccess?.();
      onClose();
      setMessage('');
      setStep('validation');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка при отправке рассылки';
      setError(errorMessage);
      console.error('Broadcast error:', err);
      setStep('compose');
    }
  };

  const handleClose = () => {
    onClose();
    setStep('validation');
    setMessage('');
    setError('');
    setValidation(null);
    setCurrentGreeting(null);
    setEditingGreeting('');
    setGreetingPreview(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Заголовок */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200">
          <h2 className="text-xl font-semibold text-neutral-900">
            Массовая рассылка
          </h2>
          <button
            onClick={handleClose}
            className="text-neutral-400 hover:text-neutral-600 p-1 hover:bg-neutral-100 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Контент */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <p className="text-red-600 font-medium">{error}</p>
              <button
                onClick={loadValidation}
                className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              >
                Повторить попытку
              </button>
            </div>
          ) : step === 'validation' && validation ? (
            <div className="space-y-6">
              {/* Статистика */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                  <div className="flex items-center">
                    <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                    <span className="text-sm font-medium text-green-800">
                      Готовы к рассылке
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-green-900 mt-2">
                    {validation.clients_ready}
                  </p>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                  <div className="flex items-center">
                    <AlertTriangle className="w-5 h-5 text-orange-600 mr-2" />
                    <span className="text-sm font-medium text-orange-800">
                      Без имени
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-orange-900 mt-2">
                    {validation.clients_without_names.length}
                  </p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <div className="flex items-center">
                    <X className="w-5 h-5 text-red-600 mr-2" />
                    <span className="text-sm font-medium text-red-800">
                      Не одобрены
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-red-900 mt-2">
                    {validation.clients_with_unapproved_names.length}
                  </p>
                </div>
              </div>

              {/* Список клиентов без имени */}
              {validation.clients_without_names.length > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <h3 className="font-medium text-orange-900 mb-3 flex items-center">
                    <Users className="w-4 h-4 mr-2" />
                    Клиенты без имени
                  </h3>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {validation.clients_without_names.map((client) => (
                      <div key={client.id} className="flex items-center justify-between bg-white p-2 rounded border">
                        <span className="text-sm text-neutral-700">
                          {client.username ? `@${client.username}` : `ID: ${client.telegram_id}`}
                        </span>
                        <span className="text-xs text-neutral-500">
                          Требует имя
                        </span>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-orange-700 mt-3">
                    Эти клиенты не получат персонализированное приветствие. 
                    Добавьте им имена.
                  </p>
                </div>
              )}

              {/* Список клиентов с неодобренными именами */}
              {validation.clients_with_unapproved_names.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h3 className="font-medium text-red-900 mb-3 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2" />
                    Клиенты с неодобренными именами
                  </h3>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {validation.clients_with_unapproved_names.map((client) => (
                      <div key={client.id} className="flex items-center justify-between bg-white p-2 rounded border">
                        <span className="text-sm text-neutral-700">
                          {client.first_name} {client.last_name}
                          {client.username && ` (@${client.username})`}
                        </span>
                        <span className="text-xs text-red-600">
                          Требует одобрения
                        </span>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-red-700 mt-3">
                    Эти клиенты имеют имена, но они не одобрены для рассылки. 
                    Одобрите их имена в карточках клиентов.
                  </p>
                </div>
              )}

              {/* Блок с информацией о блокировке */}
              {!validation.can_broadcast && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <X className="w-5 h-5 text-red-600 mr-2" />
                    <span className="font-medium text-red-900">Рассылка заблокирована</span>
                  </div>
                  <p className="text-sm text-red-700">
                    Рассылка невозможна пока все клиенты не будут иметь одобренные имена. 
                    Добавьте имена клиентам без имен и одобрите имена в их карточках.
                  </p>
                </div>
              )}

              {/* Предупреждение или продолжение */}
              <div className="flex gap-3">
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors"
                >
                  Отмена
                </button>
                <button
                  onClick={() => setStep('compose')}
                  disabled={!validation.can_broadcast}
                  className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-primary-500 transition-colors"
                  title={validation.can_broadcast ? 'Продолжить к составлению сообщения' : 'Сначала одобрите все имена'}
                >
                  {validation.can_broadcast ? 'Продолжить' : 'Заблокировано'}
                </button>
              </div>
            </div>
          ) : step === 'compose' ? (
            <div className="space-y-6">
              {/* Настройки */}
              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="includeGreeting"
                    checked={includeGreeting}
                    onChange={(e) => setIncludeGreeting(e.target.checked)}
                    className="mr-3 rounded border-neutral-300 text-primary-500 focus:ring-primary-500"
                  />
                  <label htmlFor="includeGreeting" className="text-sm font-medium text-neutral-700">
                    Включить персонализированное приветствие
                  </label>
                </div>
                
                {includeGreeting && (
                  <div className="ml-6 space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="block text-sm font-medium text-neutral-700">
                        Управление приветствием
                      </label>
                      <button
                        onClick={() => setStep('greeting')}
                        className="text-xs px-2 py-1 bg-primary-100 text-primary-700 rounded hover:bg-primary-200 transition-colors flex items-center gap-1"
                      >
                        <Settings className="w-3 h-3" />
                        Настроить
                      </button>
                    </div>
                    
                    {currentGreeting && (
                      <div className="bg-neutral-50 p-3 rounded-lg border">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-neutral-600">
                            Текущее приветствие
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            currentGreeting.is_custom 
                              ? 'bg-blue-100 text-blue-700' 
                              : 'bg-neutral-100 text-neutral-700'
                          }`}>
                            {currentGreeting.is_custom ? 'Кастомное' : 'Стандартное'}
                          </span>
                        </div>
                        <p className="text-sm text-neutral-800">
                          {currentGreeting.greeting_text}
                        </p>
                      </div>
                    )}
                    
                    <p className="text-xs text-neutral-500">
                      Будет использовано {currentGreeting?.is_custom ? 'кастомное' : 'стандартное'} приветствие из настроек
                    </p>
                  </div>
                )}
                
                {!includeGreeting && (
                  <p className="text-xs text-neutral-500 ml-6">
                    Будет отправлено только ваше сообщение
                  </p>
                )}
              </div>

              {/* Текст сообщения */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Текст сообщения
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Введите текст для рассылки..."
                  className="w-full p-3 border border-neutral-300 rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={6}
                />
              </div>

              {/* Кнопки */}
              <div className="flex gap-3">
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors"
                >
                  Отмена
                </button>
                <button
                  onClick={handleSendBroadcast}
                  disabled={!message.trim()}
                  className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                >
                  <Send className="w-4 h-4 mr-2" />
                  Отправить рассылку
                </button>
              </div>
            </div>
          ) : step === 'greeting' ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-neutral-900">
                  Настройка приветствия
                </h3>
                {currentGreeting && (
                  <span className={`text-xs px-2 py-1 rounded ${
                    currentGreeting.is_custom 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'bg-neutral-100 text-neutral-700'
                  }`}>
                    {currentGreeting.is_custom ? 'Кастомное' : 'Стандартное'}
                  </span>
                )}
              </div>

              {/* Текущее приветствие */}
              {currentGreeting && (
                <div className="bg-neutral-50 p-4 rounded-lg border">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-neutral-700">
                      Текущее приветствие
                    </span>
                    {currentGreeting.is_custom && (
                      <button
                        onClick={clearGreeting}
                        disabled={greetingLoading}
                        className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors flex items-center gap-1"
                      >
                        <Trash2 className="w-3 h-3" />
                        Очистить
                      </button>
                    )}
                  </div>
                  <p className="text-sm text-neutral-800 mb-2">
                    {currentGreeting.greeting_text}
                  </p>
                  <p className="text-xs text-neutral-500">
                    {currentGreeting.is_custom ? 'Кастомное приветствие' : 'Стандартное приветствие'}
                  </p>
                </div>
              )}

              {/* Форма редактирования */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-2">
                    Новое приветствие
                  </label>
                  <textarea
                    value={editingGreeting}
                    onChange={(e) => {
                      setEditingGreeting(e.target.value);
                      previewGreeting(e.target.value);
                    }}
                    placeholder="Привет, [Имя Клиента]! Как дела?"
                    className="w-full p-3 border border-neutral-300 rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    rows={3}
                  />
                  <p className="text-xs text-neutral-500 mt-1">
                    Используйте переменные: <code>[Имя Клиента]</code>, <code>[Фамилия Клиента]</code>
                  </p>
                </div>

                {/* Предпросмотр */}
                {greetingPreview && editingGreeting.trim() && (
                  <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                    <div className="flex items-center mb-2">
                      <Eye className="w-4 h-4 text-blue-600 mr-2" />
                      <span className="text-sm font-medium text-blue-800">
                        Предпросмотр
                      </span>
                    </div>
                    <p className="text-sm text-blue-900 mb-2">
                      {greetingPreview.preview}
                    </p>
                    <p className="text-xs text-blue-600">
                      Пример для: {greetingPreview.variables.first_name} {greetingPreview.variables.last_name}
                    </p>
                  </div>
                )}
              </div>

              {/* Кнопки */}
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setStep('compose');
                    setEditingGreeting('');
                    setGreetingPreview(null);
                  }}
                  className="flex-1 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors"
                >
                  Назад
                </button>
                <button
                  onClick={() => updateGreeting(editingGreeting, true)}
                  disabled={!editingGreeting.trim() || greetingLoading}
                  className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                >
                  {greetingLoading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  Сохранить
                </button>
              </div>
            </div>
          ) : step === 'sending' ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
              <p className="text-lg font-medium text-neutral-900 mb-2">
                Отправляем рассылку...
              </p>
              <p className="text-sm text-neutral-500">
                Пожалуйста, подождите
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}; 