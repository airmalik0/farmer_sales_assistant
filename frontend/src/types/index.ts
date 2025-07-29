export interface Client {
  id: number;
  telegram_id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  name_approved: boolean;
  created_at: string;
  messages: Message[];
  dossier?: Dossier;
  car_interest?: CarInterest;
  tasks?: Task[];
}

export interface Message {
  id: number;
  client_id: number;
  sender: 'client' | 'farmer';
  content_type: string;
  content: string;
  timestamp: string;
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
  notes?: string;
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
    telegram_id: number;
    username?: string;
    name_approved: boolean;
  }>;
  clients_with_unapproved_names: Array<{
    id: number;
    telegram_id: number;
    username?: string;
    first_name?: string;
    last_name?: string;
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
    first_name: string;
    last_name: string;
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