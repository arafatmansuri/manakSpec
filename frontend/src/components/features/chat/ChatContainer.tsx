import React, { useEffect, useRef } from 'react'
import type { ChatMessage } from '@/types/session'
import { MessageItem } from './MessageItem'
import { ShieldCheck, Sparkles, CheckCircle2 } from 'lucide-react'

interface ChatContainerProps {
  messages: ChatMessage[]
  isLoadingHistory?: boolean
  isGenerating?: boolean
  sessionId: string
  renderInputWhenEmpty?: React.ReactNode
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isLoadingHistory,
  isGenerating,
  sessionId,
  renderInputWhenEmpty,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isGenerating])

  if (isLoadingHistory) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 space-y-4">
        <div className="w-9 h-9 border-3 border-amber-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-slate-500 font-medium">Loading procurement consultation history...</p>
      </div>
    )
  }

  // Clean Centered View when no messages in session (Point 5)
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto w-full space-y-6 animate-in fade-in duration-300">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-amber-500 to-blue-600 flex items-center justify-center shadow-md">
          <ShieldCheck className="w-9 h-9 text-white font-bold" />
        </div>

        <div className="space-y-1.5">
          <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
            Intelligent Indian Standards & Tender Assistant
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
            Discover mandatory BIS standards, Quality Control Orders (QCO), and generate compliant procurement tender clauses.
          </p>
        </div>

        {/* Centered input box container */}
        <div className="w-full pt-2">
          {renderInputWhenEmpty}
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
      {messages.map((message) => (
        <MessageItem
          key={message.message_id}
          message={message}
          sessionId={sessionId}
        />
      ))}

      {/* Shimmer loading state while AI generates */}
      {isGenerating && (
        <div className="flex items-start gap-3 max-w-4xl mx-auto w-full animate-in fade-in duration-200">
          <div className="w-8 h-8 rounded-full bg-amber-100 border border-amber-300 flex items-center justify-center shrink-0">
            <Sparkles className="w-4 h-4 text-amber-600 animate-spin" />
          </div>

          <div className="flex-1 space-y-3 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-amber-800 animate-pulse">
                Analyzing BIS Database & Regulatory Gazette Orders...
              </span>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-xs">
              <div className="h-4 w-3/4 rounded bg-slate-200 animate-shimmer" />
              <div className="h-4 w-full rounded bg-slate-200 animate-shimmer" />
              <div className="h-4 w-5/6 rounded bg-slate-200 animate-shimmer" />
              <div className="pt-1 flex items-center gap-2 text-[11px] text-slate-500 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                <span>RAG Retrieval • Synthesizing Technical Specifications & Mandatory QCOs</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
