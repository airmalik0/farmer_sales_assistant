export interface Client {
  id: number;
  telegram_id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  created_at: string;
  messages: Message[];
  dossier?: Dossier;
}

export interface Message {
  id: number;
  client_id: number;
  sender: 'client' | 'farmer';
  content_type: string;
  content: string;
  timestamp: string;
}

export interface Dossier {
  id: number;
  client_id: number;
  summary?: string;
  last_updated: string;
}

export interface WebSocketMessage {
  type: 'new_message' | 'dossier_update';
  data: any;
  client_id?: number;
}