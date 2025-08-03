export interface Client {
  id: number;
  // Pact данные
  pact_conversation_id: number;
  pact_contact_id: number;
  pact_company_id: number;
  
  // Идентификаторы контакта
  sender_external_id: string;
  sender_external_public_id?: string;
  
  // Информация о контакте
  name?: string;
  phone_number?: string;
  username?: string;
  avatar_url?: string;
  
  // Канал и статус
  provider: 'whatsapp' | 'telegram_personal';
  operational_state: string;
  replied_state: string;
  
  // Системные поля
  name_approved: boolean;
  created_at: string;
  last_message_at?: string;
  last_pact_message_id?: number;
  
  // Relationships
  messages: Message[];
  dossier?: Dossier;
  car_interest?: CarInterest;
  tasks?: Task[];
  triggers?: Trigger[];
}

export interface MessageAttachment {
  id: number;
  message_id: number;
  pact_attachment_id?: number;
  file_name: string;
  mime_type: string;
  size: number;
  attachment_url: string;
  preview_url?: string;
  aspect_ratio?: number;
  width?: number;
  height?: number;
  push_to_talk?: boolean;
  created_at: string;
}

export interface Message {
  id: number;
  client_id: number;
  
  // Pact данные
  pact_message_id?: number;
  external_id?: string;
  external_created_at?: string;
  
  // Сообщение
  sender: 'client' | 'farmer';
  content_type: string;
  content?: string;
  
  // Статус и метаданные
  income: boolean;
  status: string;
  timestamp: string;
  
  // Ответы и реакции
  replied_to_id?: string;
  reactions?: any[];
  details?: any;
  
  // Relationships
  attachments: MessageAttachment[];
}

export interface ManualModification {
  modified_at: string;
  modified_by: string;
}

export interface DossierField {
  title: string;
  value: string | null;
  key: string;
  isManuallyModified?: boolean;
}

export interface Task {
  id: number;
  client_id: number;
  description: string;
  due_date: string | null;
  is_completed: boolean;
  priority: string;
  source?: string; // manual, trigger, ai
  trigger_id?: number;
  extra_data?: Record<string, any>;
  telegram_notification_sent: boolean;
  created_at: string;
  updated_at: string;
  manually_modified?: boolean;
  manual_modification_time?: string;
}

export interface Dossier {
  id: number;
  client_id: number;
  structured_data?: {
    client_info?: Record<string, any>;
    manual_modifications?: Record<string, ManualModification>;
  };
  last_updated: string;
}

export interface CarQuery {
  brand?: string | string[];
  model?: string | string[];
  price_min?: number;
  price_max?: number;
  year_min?: number;
  year_max?: number;
  mileage_max?: number;
  exterior_color?: string | string[];
  interior_color?: string | string[];
}

export interface CarInterest {
  id: number;
  client_id: number;
  structured_data?: {
    queries?: CarQuery[];
    manual_modifications?: Record<string, ManualModification>;
  };
  last_updated: string;
}

// Types for manual editing
export interface DossierManualUpdate {
  phone?: string;
  current_location?: string;
  birthday?: string; // Format: YYYY-MM-DD
  gender?: string; // "male" or "female"
  client_type?: string; // "private", "reseller", "broker", "dealer", "transporter"
  personal_notes?: string; // Личные заметки о клиенте
  business_profile?: string; // Бизнес-профиль (только для бизнес-клиентов)
}

export interface CarQueryManualUpdate {
  brand?: string | string[];
  model?: string | string[];
  price_min?: number;
  price_max?: number;
  year_min?: number;
  year_max?: number;
  mileage_max?: number;
  exterior_color?: string | string[];
  interior_color?: string | string[];
}

export interface CarInterestManualUpdate {
  queries?: CarQueryManualUpdate[];
}

export interface TaskManualUpdate {
  description?: string;
  due_date?: string; // Format: YYYY-MM-DD
  is_completed?: boolean;
  priority?: string; // "normal", "high", "low"
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  client_id?: number;
  timestamp?: string;
  provider?: string; // Новое поле для провайдера
}

export interface SendMessageRequest {
  client_id: number;
  content: string;
  content_type?: string;
}

export interface BroadcastRequest {
  content: string;
  content_type?: string;
  include_greeting?: boolean;
}

export interface MediaData {
  type: 'voice' | 'video_note' | 'document' | 'photo';
  file_id: string;
  file_name?: string;
  duration?: number;
}

export interface ApiResponse<T> {
  data: T;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface BroadcastValidation {
  clients_without_names: Array<{
    id: number;
    name?: string;
    provider: string;
    sender_external_id: string;
    name_approved: boolean;
  }>;
  clients_with_unapproved_names: Array<{
    id: number;
    name?: string;
    provider: string;
    sender_external_id: string;
    username?: string;
    phone_number?: string;
    name_approved: boolean;
  }>;
  total_clients: number;
  clients_ready: number;
  can_broadcast: boolean;
}

// Типы для медиафайлов
export interface MediaFile {
  fileId: string;
  type: 'voice' | 'video_note' | 'document' | 'photo';
  filename?: string;
}

// Типы для приветствия
export interface GreetingResponse {
  greeting_text: string;
  enabled: boolean;
  is_custom: boolean;
}

export interface GreetingRequest {
  greeting_text: string;
  enabled?: boolean;
}

export interface GreetingUpdateRequest {
  greeting_text?: string;
  enabled?: boolean;
}

export interface GreetingPreview {
  original: string;
  preview: string;
  variables: {
    name: string; // Обновлено с first_name/last_name на name
  };
}

// Типы для триггеров
export interface TriggerConditions {
  car_id?: string;
  brand?: string | string[];
  model?: string | string[];
  location?: string;
  price_min?: number;
  price_max?: number;
  year_min?: number;
  year_max?: number;
  mileage_max?: number;
  status?: string | string[];
}

export interface TriggerActionConfig {
  // Для уведомлений
  message?: string;
  channels?: string[];
  
  // Для создания задач
  title?: string;
  description?: string;
  priority?: string;
  
  // Для webhook
  url?: string;
  method?: string;
  headers?: Record<string, string>;
}

export interface TriggerBase {
  name: string;
  description?: string;
  status: 'active' | 'inactive' | 'paused';
  conditions: TriggerConditions;
  action_type: 'notify' | 'create_task' | 'send_message' | 'webhook';
  action_config?: TriggerActionConfig;
  check_interval_minutes: number;
}

export interface TriggerCreate extends TriggerBase {}

export interface TriggerUpdate {
  name?: string;
  description?: string;
  status?: 'active' | 'inactive' | 'paused';
  conditions?: TriggerConditions;
  action_type?: 'notify' | 'create_task' | 'send_message' | 'webhook';
  action_config?: TriggerActionConfig;
  check_interval_minutes?: number;
}

export interface Trigger extends TriggerBase {
  id: number;
  created_at: string;
  updated_at: string;
  last_checked_at?: string;
  last_triggered_at?: string;
  trigger_count: number;
}

export interface TriggerSummary {
  id: number;
  name: string;
  status: 'active' | 'inactive' | 'paused';
  action_type: 'notify' | 'create_task' | 'send_message' | 'webhook';
  trigger_count: number;
  last_triggered_at?: string;
  created_at: string;
}

export interface TaskWithTrigger {
  client_id: number;
  description: string;
  due_date?: string;
  priority: string;
  trigger_name: string;
  trigger_conditions: TriggerConditions;
  trigger_action_config?: TriggerActionConfig;
}

// Новые типы для Pact API
export interface ClientStats {
  total: number;
  whatsapp: number;
  telegram_personal: number;
  approved: number;
}

export interface MessageStats {
  total: number;
  incoming: number;
  outgoing: number;
}

export interface AdminStats {
  clients: ClientStats;
  messages: MessageStats;
  pact: {
    status: string;
    last_webhook: string;
  };
}

export interface PactMessageSend {
  text?: string;
  attachment_ids?: number[];
  replied_to_id?: string;
}

// Утилитарные типы для провайдеров
export type Provider = 'whatsapp' | 'telegram_personal';

export interface ProviderInfo {
  name: string;
  icon: string;
  color: string;
}