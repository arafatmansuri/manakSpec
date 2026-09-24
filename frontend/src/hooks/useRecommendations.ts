import { useMutation, useQueryClient } from '@tanstack/react-query'
import { standardsApi, type RecommendPayload } from '@/api/standardsApi'
import { QUERY_KEYS } from '@/api/queryKeys'

export function useGetRecommendation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: RecommendPayload) => standardsApi.getRecommendation(payload),
    onSuccess: (data) => {
      // Refresh chat history for the session
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.chatHistory(data.session_id),
      })
      // Refresh session list so updated timestamps / titles update
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.sessions(data.user_id),
      })
    },
  })
}
