export interface CreateSessionRequest {
  user_id?: string;
  title?: string;
}

export interface CreateSessionResponse {
  user_id: string;
  session_id: string;
  title: string;
  created_at: string;
}

export interface SessionSummary {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  message_id: string;
  role: 'user' | 'assistant' | 'system';
  content: any;
  execution_provider?: string | null;
  created_at: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  title: string;
  messages: ChatMessage[];
}
