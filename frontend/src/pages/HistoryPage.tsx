import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { setActiveSessionId } from '@/store/slices/sessionSlice'
import { addToast } from '@/store/slices/uiSlice'
import { useUserSessions, useCreateSession, useDeleteSession } from '@/hooks/useSessions'
import { useExport } from '@/hooks/useExport'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { Clock, MessageSquare, ArrowRight, FileDown, Plus, Search, Calendar, ChevronDown, Trash2 } from 'lucide-react'

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const userId = useAppSelector((state) => state.session.userId)
  const activeSessionId = useAppSelector((state) => state.session.activeSessionId)
  const { data: sessions, isLoading } = useUserSessions(userId)
  const createSessionMutation = useCreateSession()
  const deleteSessionMutation = useDeleteSession(userId)
  const { exportDocument, isExporting } = useExport()
  const [search, setSearch] = useState('')
  const [openExportMenuId, setOpenExportMenuId] = useState<string | null>(null)

  const handleOpenSession = (sessionId: string) => {
    dispatch(setActiveSessionId(sessionId))
    navigate(`/chat/${sessionId}`)
  }

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    try {
      await deleteSessionMutation.mutateAsync(sessionId)
      dispatch(addToast({ message: 'Consultation deleted successfully.', type: 'success' }))
      if (sessionId === activeSessionId) {
        dispatch(setActiveSessionId(null))
      }
    } catch (err: any) {
      dispatch(addToast({ message: `Failed to delete session: ${err.message}`, type: 'error' }))
    }
  }

  const handleNewChat = async () => {
    const newSession = await createSessionMutation.mutateAsync({
      user_id: userId,
      title: 'New Procurement Review',
    })
    dispatch(setActiveSessionId(newSession.session_id))
    navigate(`/chat/${newSession.session_id}`)
  }

  const filteredSessions = sessions?.filter((s) =>
    s.title?.toLowerCase().includes(search.toLowerCase())
  )

  const handleExport = (e: React.MouseEvent, sessionId: string, format: 'pdf' | 'docx' | 'txt' | 'md') => {
    e.stopPropagation()
    exportDocument(sessionId, format)
    setOpenExportMenuId(null)
  }

  return (
    <div className="flex-1 p-4 md:p-8 max-w-6xl mx-auto w-full space-y-6 bg-slate-50">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 flex items-center gap-2">
            <Clock className="w-6 h-6 text-amber-600" />
            <span>Procurement History & Saved Consultations</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Access previous technical compliance evaluations, tender drafting sessions, and exports.
          </p>
        </div>

        <Button
          variant="amber"
          size="sm"
          onClick={handleNewChat}
          isLoading={createSessionMutation.isPending}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          New Analysis
        </Button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter consultation history by title..."
          className="w-full bg-white border border-slate-300 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-amber-500 shadow-2xs"
        />
      </div>

      {/* Sessions Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-white border border-slate-200 animate-pulse shadow-xs" />
          ))}
        </div>
      ) : filteredSessions && filteredSessions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredSessions.map((session) => (
            <Card
              key={session.session_id}
              hoverEffect
              className="flex flex-col justify-between space-y-3 cursor-pointer group bg-white border-slate-200 relative"
              onClick={() => handleOpenSession(session.session_id)}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-1.5 font-mono text-[11px]">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(session.updated_at || session.created_at).toLocaleDateString()}</span>
                  </div>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold">
                    {session.session_id.substring(0, 8)}
                  </span>
                </div>

                <div className="flex items-start gap-2.5">
                  <MessageSquare className="w-4 h-4 text-amber-600 shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-amber-800 transition-colors line-clamp-2">
                    {session.title || 'Untitled Procurement Query'}
                  </h3>
                </div>
              </div>

              {/* Bottom Actions with Multi-format download (Point 4) */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between relative">
                <div className="relative">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      setOpenExportMenuId(openExportMenuId === session.session_id ? null : session.session_id)
                    }}
                    disabled={isExporting}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-300 text-xs font-semibold text-slate-700 transition-colors cursor-pointer"
                  >
                    <FileDown className="w-3.5 h-3.5 text-blue-600" />
                    <span>Export</span>
                    <ChevronDown className="w-3 h-3 text-slate-400" />
                  </button>

                  {/* Multi-format export dropdown (Point 4) */}
                  {openExportMenuId === session.session_id && (
                    <div
                      onClick={(e) => e.stopPropagation()}
                      className="absolute left-0 bottom-full mb-1.5 w-36 rounded-xl bg-white border border-slate-200 shadow-xl py-1 z-30 animate-in fade-in zoom-in-95 duration-150"
                    >
                      <button
                        onClick={(e) => handleExport(e, session.session_id, 'docx')}
                        className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center justify-between cursor-pointer"
                      >
                        <span>Word (.docx)</span>
                        <span className="text-[10px] font-mono text-slate-400">DOCX</span>
                      </button>
                      <button
                        onClick={(e) => handleExport(e, session.session_id, 'pdf')}
                        className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center justify-between cursor-pointer"
                      >
                        <span>PDF Document</span>
                        <span className="text-[10px] font-mono text-slate-400">PDF</span>
                      </button>
                      <button
                        onClick={(e) => handleExport(e, session.session_id, 'md')}
                        className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center justify-between cursor-pointer"
                      >
                        <span>Markdown</span>
                        <span className="text-[10px] font-mono text-slate-400">MD</span>
                      </button>
                      <button
                        onClick={(e) => handleExport(e, session.session_id, 'txt')}
                        className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center justify-between cursor-pointer"
                      >
                        <span>Plain Text</span>
                        <span className="text-[10px] font-mono text-slate-400">TXT</span>
                      </button>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={(e) => handleDeleteSession(e, session.session_id)}
                    className="p-1 text-slate-400 hover:text-red-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                    title="Delete consultation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>

                  <div className="flex items-center gap-1 text-xs font-semibold text-blue-600 group-hover:translate-x-1 transition-transform">
                    <span>Resume</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center p-8 space-y-3 bg-white border-slate-200">
          <Clock className="w-10 h-10 text-slate-400 mx-auto opacity-60" />
          <h3 className="text-sm font-bold text-slate-800">No consultation sessions found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Consultations will be automatically recorded here whenever you analyze products or draft tender clauses.
          </p>
          <Button variant="amber" size="sm" onClick={handleNewChat} className="mt-2">
            Start Your First Query
          </Button>
        </Card>
      )}
    </div>
  )
}
