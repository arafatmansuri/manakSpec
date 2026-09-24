import React from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { setSidebarOpen, setActiveModal } from '@/store/slices/uiSlice'
import { setActiveSessionId } from '@/store/slices/sessionSlice'
import { useUserSessions, useCreateSession } from '@/hooks/useSessions'
import { Plus, MessageSquare, BookOpen, Clock, ShieldCheck, FileCheck2, X, ChevronRight, UploadCloud } from 'lucide-react'
import { cn } from '@/utils/cn'

export const Sidebar: React.FC = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { sessionId } = useParams<{ sessionId?: string }>()

  const isSidebarOpen = useAppSelector((state) => state.ui.isSidebarOpen)
  const userId = useAppSelector((state) => state.session.userId)

  const { data: sessions, isLoading } = useUserSessions(userId)
  const createSessionMutation = useCreateSession()

  const handleNewChat = async () => {
    try {
      const newSession = await createSessionMutation.mutateAsync({
        user_id: userId,
        title: 'New Procurement Review',
      })
      dispatch(setActiveSessionId(newSession.session_id))
      navigate(`/chat/${newSession.session_id}`)
      if (window.innerWidth < 1024) {
        dispatch(setSidebarOpen(false))
      }
    } catch {
      navigate('/')
    }
  }

  const handleSelectSession = (id: string) => {
    dispatch(setActiveSessionId(id))
    navigate(`/chat/${id}`)
    if (window.innerWidth < 1024) {
      dispatch(setSidebarOpen(false))
    }
  }

  return (
    <>
      {/* Mobile backdrop */}
      {isSidebarOpen && (
        <div
          onClick={() => dispatch(setSidebarOpen(false))}
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden animate-in fade-in"
        />
      )}

      {/* Sidebar drawer - fixed and independent scroll */}
      <aside
        className={cn(
          'fixed lg:static inset-y-0 lg:top-0 left-0 z-50 lg:z-20 w-72 h-full bg-white border-r border-slate-200 flex flex-col transition-all duration-300 ease-in-out shrink-0 shadow-sm lg:shadow-none',
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:w-0 lg:opacity-0 lg:pointer-events-none'
        )}
      >
        {/* Top Actions */}
        <div className="p-4 border-b border-slate-100">
          <div className="flex items-center justify-between lg:hidden mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Navigation</span>
            <button
              onClick={() => dispatch(setSidebarOpen(false))}
              className="p-1 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={handleNewChat}
            disabled={createSessionMutation.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-xs active:scale-[0.98] transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Procurement Query</span>
          </button>
        </div>

        {/* Quick Links */}
        <div className="p-3 border-b border-slate-100 space-y-1">
          <Link
            to="/standards"
            onClick={() => window.innerWidth < 1024 && dispatch(setSidebarOpen(false))}
            className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:text-slate-950 hover:bg-slate-100 transition-colors"
          >
            <BookOpen className="w-4 h-4 text-blue-600" />
            <span>BIS Standards & QCOs</span>
          </Link>
          <Link
            to="/history"
            onClick={() => window.innerWidth < 1024 && dispatch(setSidebarOpen(false))}
            className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:text-slate-950 hover:bg-slate-100 transition-colors"
          >
            <Clock className="w-4 h-4 text-amber-600" />
            <span>All Procurement Sessions</span>
          </Link>
          <button
            type="button"
            onClick={() => {
              dispatch(setActiveModal('ingest'))
              if (window.innerWidth < 1024) dispatch(setSidebarOpen(false))
            }}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:text-slate-950 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <UploadCloud className="w-4 h-4 text-emerald-600" />
            <span>Ingest BIS Standards</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="flex items-center justify-between px-2 pb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Recent Consultations
            </span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600">
              {sessions?.length || 0}
            </span>
          </div>

          {isLoading ? (
            <div className="space-y-2 p-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 rounded-xl bg-slate-100 animate-pulse" />
              ))}
            </div>
          ) : sessions && sessions.length > 0 ? (
            sessions.map((s) => {
              const isActive = sessionId === s.session_id
              return (
                <button
                  key={s.session_id}
                  onClick={() => handleSelectSession(s.session_id)}
                  className={cn(
                    'w-full text-left flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition-all duration-150 group cursor-pointer',
                    isActive
                      ? 'bg-amber-50 text-amber-900 font-bold border border-amber-300 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-950 hover:bg-slate-100'
                  )}
                >
                  <div className="flex items-center gap-2.5 min-w-0 pr-2">
                    <MessageSquare
                      className={cn(
                        'w-4 h-4 shrink-0 transition-colors',
                        isActive ? 'text-amber-600' : 'text-slate-400 group-hover:text-slate-600'
                      )}
                    />
                    <span className="truncate">{s.title || 'Untitled Query'}</span>
                  </div>
                  <ChevronRight
                    className={cn(
                      'w-3.5 h-3.5 shrink-0 transition-opacity',
                      isActive ? 'opacity-100 text-amber-600' : 'opacity-0 group-hover:opacity-100 text-slate-400'
                    )}
                  />
                </button>
              )
            })
          ) : (
            <div className="p-4 text-center">
              <FileCheck2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-xs text-slate-600 font-semibold">No previous sessions</p>
              <p className="text-[11px] text-slate-400 mt-1">Start by asking for an Indian Standard recommendation.</p>
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="p-3 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-emerald-100 border border-emerald-300 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-4 h-4 text-emerald-700" />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-bold text-slate-800 truncate">QCO Enforced</p>
              <p className="text-[10px] text-slate-500 truncate">BIS Standards Verified</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
