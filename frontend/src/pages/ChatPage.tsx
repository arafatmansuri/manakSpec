import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { setActiveSessionId } from '@/store/slices/sessionSlice'
import { addToast } from '@/store/slices/uiSlice'
import { useChatHistory, useCreateSession } from '@/hooks/useSessions'
import { useGetRecommendation } from '@/hooks/useRecommendations'
import { ChatContainer } from '@/components/features/chat/ChatContainer'
import { PromptInputForm } from '@/components/features/chat/PromptInputForm'
import type { ChatMessage } from '@/types/session'

export const ChatPage: React.FC = () => {
  const { sessionId: routeSessionId } = useParams<{ sessionId?: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const dispatch = useAppDispatch()

  const userId = useAppSelector((state) => state.session.userId)
  const activeSessionId = useAppSelector((state) => state.session.activeSessionId)
  const preferredLanguage = useAppSelector((state) => state.session.preferredLanguage)

  // Local optimistic messages state to show immediate prompt feedback
  const [localOptimisticMessages, setLocalOptimisticMessages] = useState<ChatMessage[]>([])

  const currentSessionId = routeSessionId || activeSessionId

  // Fetch chat history from server
  const { data: chatData, isLoading: isLoadingHistory, refetch } = useChatHistory(currentSessionId)
  const createSessionMutation = useCreateSession()
  const recommendationMutation = useGetRecommendation()

  // Handle URL query parameter pre-fill (Point 9)
  const consultQuery = searchParams.get('consult')
  const initialQuery = consultQuery ? `Draft tender specification and compliance clause for ${consultQuery}` : ''

  // Sync route param with Redux
  useEffect(() => {
    if (routeSessionId && routeSessionId !== activeSessionId) {
      dispatch(setActiveSessionId(routeSessionId))
    }
  }, [routeSessionId, activeSessionId, dispatch])

  // Clear optimistic messages once server history updates with new messages
  useEffect(() => {
    if (chatData?.messages) {
      setLocalOptimisticMessages([])
    }
  }, [chatData?.messages])

  const handlePromptSubmit = async ({
    query_text,
    file,
    language,
  }: {
    query_text: string
    file: File | null
    language: string
  }) => {
    let targetSessionId = currentSessionId

    try {
      // 1. If no active session yet, create one
      if (!targetSessionId) {
        const title = query_text ? query_text.substring(0, 40) + '...' : (file?.name || 'New Procurement Query')
        const newSession = await createSessionMutation.mutateAsync({
          user_id: userId,
          title,
        })
        targetSessionId = newSession.session_id
        dispatch(setActiveSessionId(targetSessionId))
        navigate(`/chat/${targetSessionId}`, { replace: true })
      }

      // 2. Add optimistic user message to display immediately
      const optimisticUserMsg: ChatMessage = {
        message_id: `temp_${Date.now()}`,
        role: 'user',
        content: file ? `${query_text ? query_text + '\n\n' : ''}[Attached Document: ${file.name}]` : query_text,
        created_at: new Date().toISOString(),
      }
      setLocalOptimisticMessages((prev) => [...prev, optimisticUserMsg])

      // 3. Call backend recommendation endpoint
      await recommendationMutation.mutateAsync({
        session_id: targetSessionId,
        user_id: userId,
        query_text,
        file,
        language: language || preferredLanguage,
      })

      // Refetch history to get the exact saved state
      refetch()
    } catch (err: any) {
      dispatch(
        addToast({
          message: `Error: ${err.message || 'Could not process procurement request.'}`,
          type: 'error',
        })
      )
    }
  }

  // Combine server messages with any pending optimistic message
  const serverMessages = chatData?.messages || []
  const displayMessages = [...serverMessages, ...localOptimisticMessages]
  const hasMessages = displayMessages.length > 0

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50">
      {/* Scrollable Chat Area */}
      <ChatContainer
        messages={displayMessages}
        isLoadingHistory={isLoadingHistory}
        isGenerating={recommendationMutation.isPending}
        sessionId={currentSessionId || ''}
        renderInputWhenEmpty={
          !hasMessages ? (
            <PromptInputForm
              onSubmit={handlePromptSubmit}
              isLoading={recommendationMutation.isPending || createSessionMutation.isPending}
              initialQuery={initialQuery}
              centered
            />
          ) : undefined
        }
      />

      {/* Sticky Bottom Input Form when conversation has started (Points 5 & 6) */}
      {hasMessages && (
        <div className="p-3 bg-white/95 border-t border-slate-200/90 shadow-2xs shrink-0 sticky bottom-0 z-20">
          <PromptInputForm
            onSubmit={handlePromptSubmit}
            isLoading={recommendationMutation.isPending || createSessionMutation.isPending}
            initialQuery={initialQuery}
          />
        </div>
      )}
    </div>
  )
}
