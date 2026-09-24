import React from 'react'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { removeToast } from '@/store/slices/uiSlice'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'
import { cn } from '@/utils/cn'

export const ToastContainer: React.FC = () => {
  const toasts = useAppSelector((state) => state.ui.toasts)
  const dispatch = useAppDispatch()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            'pointer-events-auto flex items-center justify-between p-3.5 rounded-xl border shadow-lg backdrop-blur-md transition-all duration-300 animate-in slide-in-from-bottom-5',
            toast.type === 'success' && 'bg-white border-emerald-300 text-emerald-950',
            toast.type === 'error' && 'bg-white border-rose-300 text-rose-950',
            toast.type === 'info' && 'bg-white border-blue-300 text-blue-950'
          )}
        >
          <div className="flex items-center gap-2.5 min-w-0 pr-2">
            {toast.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />}
            {toast.type === 'error' && <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />}
            {toast.type === 'info' && <Info className="w-5 h-5 text-blue-600 shrink-0" />}
            <span className="text-xs font-semibold text-slate-800 break-words">{toast.message}</span>
          </div>

          <button
            onClick={() => dispatch(removeToast(toast.id))}
            className="text-slate-400 hover:text-slate-700 p-1 rounded-md hover:bg-slate-100 transition-colors shrink-0 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )
}
