import { apiClient } from './client'
import type { RecommendationOutput } from '@/types/standards'

export interface RecommendPayload {
  session_id: string
  user_id: string
  query_text?: string
  file?: File | null
  language?: string
}

export const standardsApi = {
  getRecommendation: async (payload: RecommendPayload): Promise<RecommendationOutput> => {
    const formData = new FormData()
    formData.append('session_id', payload.session_id)
    formData.append('user_id', payload.user_id)

    if (payload.query_text) {
      formData.append('query_text', payload.query_text)
    }

    if (payload.file) {
      formData.append('file', payload.file)
    }

    if (payload.language) {
      formData.append('language', payload.language)
    }

    const res = await apiClient.post<RecommendationOutput>('/standards/recommend', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return res.data
  },

  exportTender: async (identifier: string, format: 'pdf' | 'docx' | 'txt' | 'md' = 'docx'): Promise<Blob> => {
    const res = await apiClient.get(`/standards/export/${identifier}`, {
      params: { format },
      responseType: 'blob',
    })
    return res.data
  },

  exportMessage: async (messageId: string, format: 'pdf' | 'docx' | 'txt' | 'md' = 'docx'): Promise<Blob> => {
    const res = await apiClient.get(`/standards/export/message/${messageId}`, {
      params: { format },
      responseType: 'blob',
    })
    return res.data
  },

  ingestStandard: async (formData: FormData): Promise<any> => {
    const res = await apiClient.post('/standards/ingest', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return res.data
  },

  ingestBulk: async (formData: FormData): Promise<any> => {
    const res = await apiClient.post('/standards/ingest-bulk', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return res.data
  },

  getIngestJob: async (jobId: string) => {
    const res = await apiClient.get(`/standards/ingest-job/${jobId}`)
    return res.data
  },
}
