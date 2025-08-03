import { useState, useEffect } from 'react';
import { X, Send, AlertTriangle, Users, CheckCircle, Settings, Eye, Trash2, Save } from 'lucide-react';
import { pactApi, settingsApi } from '../services/api';
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
      const response = await pactApi.validateBroadcast({
        content: '',
        content_type: 'text'
      });
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
      await pactApi.broadcast({
        content: message.trim(),
        content_type: 'text',
        include_greeting: includeGreeting
      });
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
                      Неодобренные имена
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-orange-900 mt-2">
                    {validation.clients_with_unapproved_names.length}
                  </p>
                </div>
                
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <div className="flex items-center">
                    <X className="w-5 h-5 text-red-600 mr-2" />
                    <span className="text-sm font-medium text-red-800">
                      Без имен
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-red-900 mt-2">
                    {validation.clients_without_names.length}
                  </p>
                </div>
              </div>

              {/* Проблемы с клиентами */}
              {(validation.clients_without_names.length > 0 || validation.clients_with_unapproved_names.length > 0) && (
                <div className="space-y-4">
                  {validation.clients_without_names.length > 0 && (
                    <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                      <h3 className="text-red-800 font-medium mb-3">
                        Клиенты без имен ({validation.clients_without_names.length})
                      </h3>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {validation.clients_without_names.map((client) => (
                          <div key={client.id} className="flex items-center justify-between bg-red-100 p-2 rounded">
                            <span className="text-red-900 text-sm">
                              {client.provider === 'whatsapp' ? '📱' : '✈️'} {client.sender_external_id}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {validation.clients_with_unapproved_names.length > 0 && (
                    <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                      <h3 className="text-orange-800 font-medium mb-3">
                        Клиенты с неодобренными именами ({validation.clients_with_unapproved_names.length})
                      </h3>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {validation.clients_with_unapproved_names.map((client) => (
                          <div key={client.id} className="flex items-center justify-between bg-orange-100 p-2 rounded">
                            <span className="text-orange-900 text-sm">
                              {client.provider === 'whatsapp' ? '📱' : '✈️'} {client.name || client.sender_external_id}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Кнопки */}
              <div className="flex items-center justify-between pt-4 border-t border-neutral-200">
                <button
                  onClick={() => setStep('greeting')}
                  className="flex items-center gap-2 px-4 py-2 text-neutral-600 hover:text-neutral-700 hover:bg-neutral-50 rounded-lg transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  Настроить приветствие
                </button>
                
                {validation.can_broadcast && (
                  <button
                    onClick={() => setStep('compose')}
                    className="flex items-center gap-2 px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                  >
                    <Send className="w-4 h-4" />
                    Продолжить ({validation.clients_ready} клиентов)
                  </button>
                )}
              </div>
            </div>
          ) : step === 'greeting' ? (
            <div className="space-y-6">
              {/* Текущее приветствие */}
              {currentGreeting && (
                <div className="bg-neutral-50 p-4 rounded-lg border border-neutral-200">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-neutral-900">
                      Текущее приветствие
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        currentGreeting.enabled 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {currentGreeting.enabled ? 'Включено' : 'Отключено'}
                      </span>
                      <button
                        onClick={clearGreeting}
                        disabled={greetingLoading}
                        className="text-red-600 hover:text-red-700 p-1 hover:bg-red-50 rounded transition-colors"
                        title="Удалить приветствие"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <p className="text-neutral-700 whitespace-pre-wrap">
                    {currentGreeting.greeting_text}
                  </p>
                </div>
              )}

              {/* Редактирование приветствия */}
              <div className="space-y-4">
                <h3 className="font-medium text-neutral-900">
                  {currentGreeting ? 'Изменить приветствие' : 'Создать приветствие'}
                </h3>
                
                <textarea
                  value={editingGreeting}
                  onChange={(e) => {
                    setEditingGreeting(e.target.value);
                    previewGreeting(e.target.value);
                  }}
                  placeholder="Введите текст приветствия. Используйте {name} для подстановки имени клиента."
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                  rows={4}
                />
                
                {greetingPreview && (
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2 mb-2">
                      <Eye className="w-4 h-4 text-blue-600" />
                      <span className="text-blue-800 font-medium">Предварительный просмотр</span>
                    </div>
                    <p className="text-blue-900 whitespace-pre-wrap">
                      {greetingPreview.preview}
                    </p>
                  </div>
                )}
              </div>

              {/* Кнопки */}
              <div className="flex items-center justify-between pt-4 border-t border-neutral-200">
                <button
                  onClick={() => setStep('validation')}
                  className="px-4 py-2 text-neutral-600 hover:text-neutral-700 hover:bg-neutral-50 rounded-lg transition-colors"
                >
                  Назад
                </button>
                
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => updateGreeting(editingGreeting, true)}
                    disabled={!editingGreeting.trim() || greetingLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Save className="w-4 h-4" />
                    {greetingLoading ? 'Сохранение...' : 'Сохранить'}
                  </button>
                </div>
              </div>
            </div>
          ) : step === 'compose' ? (
            <div className="space-y-6">
              {/* Информация о получателях */}
              {validation && (
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-5 h-5 text-blue-600" />
                    <span className="text-blue-800 font-medium">
                      Рассылка будет отправлена {validation.clients_ready} клиентам
                    </span>
                  </div>
                  <p className="text-blue-700 text-sm">
                    Через WhatsApp и Telegram Personal каналы
                  </p>
                </div>
              )}

              {/* Настройки приветствия */}
              {currentGreeting && currentGreeting.enabled && (
                <div className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg border border-neutral-200">
                  <div>
                    <p className="font-medium text-neutral-900">Включить приветствие</p>
                    <p className="text-sm text-neutral-600">
                      Приветствие будет добавлено в начало сообщения
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeGreeting}
                      onChange={(e) => setIncludeGreeting(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
              )}

              {/* Поле ввода сообщения */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-neutral-700">
                  Текст сообщения
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Введите текст сообщения для рассылки..."
                  className="w-full p-4 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                  rows={6}
                />
                <p className="text-sm text-neutral-500">
                  Сообщение будет отправлено всем активным клиентам с одобренными именами.
                </p>
              </div>

              {/* Кнопки */}
              <div className="flex items-center justify-between pt-4 border-t border-neutral-200">
                <button
                  onClick={() => setStep('validation')}
                  className="px-4 py-2 text-neutral-600 hover:text-neutral-700 hover:bg-neutral-50 rounded-lg transition-colors"
                >
                  Назад
                </button>
                
                <button
                  onClick={handleSendBroadcast}
                  disabled={!message.trim()}
                  className="flex items-center gap-2 px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="w-4 h-4" />
                  Отправить рассылку
                </button>
              </div>
            </div>
          ) : step === 'sending' ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
              <p className="text-neutral-600 font-medium">Отправка рассылки...</p>
              <p className="text-sm text-neutral-500 mt-2">
                Это может занять несколько минут
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}; 