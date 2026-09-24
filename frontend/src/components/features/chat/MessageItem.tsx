import React, { useState } from 'react'
import type { ChatMessage } from '@/types/session'
import type { StructuredSynthesis, PrimaryStandard, AlliedReference } from '@/types/standards'
import { StandardCard } from '../standards/StandardCard'
import { TenderClauseViewer } from '../tender/TenderClauseViewer'
import { Badge } from '@/components/common/Badge'
import { useExport } from '@/hooks/useExport'
import { User, Bot, BookOpen, Layers, ShieldCheck, ChevronDown, ChevronUp, FileDown } from 'lucide-react'

interface MessageItemProps {
  message: ChatMessage
  sessionId: string
}

export const MessageItem: React.FC<MessageItemProps> = ({ message, sessionId }) => {
  const isUser = message.role === 'user'
  const [showAllied, setShowAllied] = useState(false)
  const { exportDocument, isExporting } = useExport()

  // Parse structured content if assistant
  let synthesis: StructuredSynthesis | null = null
  let rawText = ''

  if (typeof message.content === 'object' && message.content !== null) {
    if (message.content.structured_synthesis) {
      synthesis = message.content.structured_synthesis
    } else if (message.content.overview && message.content.primary_standards_summary) {
      synthesis = message.content as StructuredSynthesis
    } else {
      rawText = JSON.stringify(message.content, null, 2)
    }
  } else if (typeof message.content === 'string') {
    try {
      const parsed = JSON.parse(message.content)
      if (parsed.structured_synthesis) {
        synthesis = parsed.structured_synthesis
      } else if (parsed.overview) {
        synthesis = parsed
      } else {
        rawText = message.content
      }
    } catch {
      rawText = message.content
    }
  }

  if (isUser) {
    return (
      <div className="flex items-start justify-end gap-3 max-w-4xl mx-auto w-full animate-in fade-in duration-200">
        <div className="max-w-2xl rounded-2xl bg-blue-600 text-white p-4 shadow-sm border border-blue-700">
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
          <span className="text-[10px] text-blue-100 mt-2 block text-right font-medium">
            {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <div className="w-8 h-8 rounded-full bg-blue-600 border border-blue-400 flex items-center justify-center shrink-0 shadow-xs">
          <User className="w-4 h-4 text-white" />
        </div>
      </div>
    )
  }

  const targetIdentifier = message.message_id || sessionId

  return (
    <div className="flex items-start gap-3 max-w-4xl mx-auto w-full animate-in fade-in duration-200">
      <div className="w-8 h-8 rounded-full bg-amber-500 border border-amber-400 flex items-center justify-center shrink-0 shadow-xs">
        <Bot className="w-4 h-4 text-white font-bold" />
      </div>

      <div className="flex-1 space-y-4 max-w-3xl">
        {/* Assistant Header */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-800">ManakSpec BIS Intelligence</span>
          {message.execution_provider && (
            <Badge variant="ai" size="sm">
              {message.execution_provider}
            </Badge>
          )}
          <span className="text-[10px] text-slate-500">
            {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {synthesis ? (
          <div className="space-y-4">
            {/* Note: Overview section removed as per user instruction */}

            {/* Certification Scheme & Governing Body */}
            {synthesis.certification_details && (
              <div className="p-3.5 rounded-xl bg-white border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs shadow-xs">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span className="font-bold text-slate-900">
                    Scheme: {synthesis.certification_details.scheme_name}
                  </span>
                  <span className="text-slate-500">
                    ({synthesis.certification_details.governing_body_or_order})
                  </span>
                </div>
                <Badge variant="crs" size="sm">
                  {synthesis.certification_details.mark_type}
                </Badge>
              </div>
            )}

            {/* Primary Indian Standards */}
            {synthesis.primary_standards_summary && synthesis.primary_standards_summary.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
                  <BookOpen className="w-4 h-4 text-blue-600" />
                  <span>Primary Indian Standards (BIS)</span>
                  <span className="text-slate-500 text-[11px] font-medium">
                    ({synthesis.primary_standards_summary.length} standards verified)
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-3">
                  {synthesis.primary_standards_summary.map((std: PrimaryStandard) => (
                    <StandardCard key={std.is_number} standard={std} />
                  ))}
                </div>
              </div>
            )}

            {/* Allied References / Normative Standards */}
            {synthesis.allied_references && synthesis.allied_references.length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
                <button
                  type="button"
                  onClick={() => setShowAllied(!showAllied)}
                  className="w-full p-3 flex items-center justify-between text-xs font-bold text-slate-800 hover:bg-slate-50 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-slate-500" />
                    <span>Allied Standards, Test Methods & Code of Practice</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                      {synthesis.allied_references.length}
                    </span>
                  </div>
                  {showAllied ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {showAllied && (
                  <div className="p-3 border-t border-slate-100 space-y-2 text-xs bg-slate-50/50 animate-in fade-in duration-150">
                    {synthesis.allied_references.map((allied: AlliedReference, idx) => (
                      <div
                        key={idx}
                        className="flex flex-col sm:flex-row sm:items-center justify-between p-2 rounded-lg bg-white border border-slate-200 gap-2 shadow-2xs"
                      >
                        <div className="min-w-0">
                          <span className="font-mono text-amber-700 font-bold text-xs mr-2">
                            {allied.related_is_number || allied.parent_is_number}
                          </span>
                          <span className="text-slate-700">{allied.title_or_description}</span>
                        </div>
                        <Badge variant="neutral" size="sm" className="shrink-0 self-start sm:self-auto">
                          {allied.relation_type}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tender Clause Drafting Viewer */}
            {synthesis.tender_clause && (
              <TenderClauseViewer
                clause={synthesis.tender_clause}
                sessionId={sessionId}
                messageId={message.message_id}
              />
            )}

            {/* Direct Bottom Export Bar for this Chat Turn (Point 3) */}
            <div className="p-3 rounded-xl bg-slate-100 border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2 text-slate-700 font-semibold">
                <FileDown className="w-4 h-4 text-blue-600" />
                <span>Export this Consultation Schedule:</span>
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <button
                  onClick={() => exportDocument(targetIdentifier, 'docx')}
                  disabled={isExporting}
                  className="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:border-amber-500 hover:text-amber-800 text-slate-700 font-medium text-[11px] shadow-2xs transition-colors cursor-pointer"
                >
                  Word (.docx)
                </button>
                <button
                  onClick={() => exportDocument(targetIdentifier, 'pdf')}
                  disabled={isExporting}
                  className="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:border-amber-500 hover:text-amber-800 text-slate-700 font-medium text-[11px] shadow-2xs transition-colors cursor-pointer"
                >
                  PDF Document
                </button>
                <button
                  onClick={() => exportDocument(targetIdentifier, 'md')}
                  disabled={isExporting}
                  className="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:border-amber-500 hover:text-amber-800 text-slate-700 font-medium text-[11px] shadow-2xs transition-colors cursor-pointer"
                >
                  Markdown (.md)
                </button>
                <button
                  onClick={() => exportDocument(targetIdentifier, 'txt')}
                  disabled={isExporting}
                  className="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:border-amber-500 hover:text-amber-800 text-slate-700 font-medium text-[11px] shadow-2xs transition-colors cursor-pointer"
                >
                  Plain Text (.txt)
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Fallback text message */
          <div className="p-4 rounded-2xl bg-white border border-slate-200 text-sm text-slate-800 whitespace-pre-wrap leading-relaxed shadow-xs">
            {rawText || 'No recommendation synthesis returned.'}
          </div>
        )}
      </div>
    </div>
  )
}
