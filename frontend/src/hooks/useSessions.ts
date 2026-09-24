import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionsApi } from '@/api/sessionsApi'
import { QUERY_KEYS } from '@/api/queryKeys'
import type { CreateSessionRequest } from '@/types/session'

export function useUserSessions(userId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.sessions(userId),
    queryFn: () => sessionsApi.getUserSessions(userId),
    enabled: !!userId,
  })
}

export function useChatHistory(sessionId: string | null) {
  return useQuery({
    queryKey: QUERY_KEYS.chatHistory(sessionId || ''),
    queryFn: () => sessionsApi.getChatHistory(sessionId!),
    enabled: !!sessionId,
    refetchOnWindowFocus: false,
  })
}

export function useCreateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateSessionRequest) => sessionsApi.createSession(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.sessions(data.user_id),
      })
    },
  })
}

export function useDeleteSession(userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => sessionsApi.deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.sessions(userId),
      })
    },
  })
}
