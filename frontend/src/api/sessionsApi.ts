import { apiClient } from './client'
import type {
  CreateSessionRequest,
  CreateSessionResponse,
  SessionSummary,
  ChatHistoryResponse,
} from '@/types/session'

export const sessionsApi = {
  createSession: async (data: CreateSessionRequest): Promise<CreateSessionResponse> => {
    const res = await apiClient.post<CreateSessionResponse>('/sessions/', data)
    return res.data
  },

  getUserSessions: async (userId: string): Promise<SessionSummary[]> => {
    const res = await apiClient.get<SessionSummary[]>(`/sessions/${userId}`)
    return res.data
  },

  getChatHistory: async (sessionId: string): Promise<ChatHistoryResponse> => {
    const res = await apiClient.get<ChatHistoryResponse>(`/sessions/chat/${sessionId}`)
    return res.data
  },

  deleteSession: async (sessionId: string): Promise<{ status: string; message: string }> => {
    const res = await apiClient.delete<{ status: string; message: string }>(`/sessions/${sessionId}`)
    return res.data
  },
}
