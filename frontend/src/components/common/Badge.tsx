import React from 'react'
import { cn } from '@/utils/cn'
import { AlertCircle, CheckCircle2, ShieldAlert, Sparkles } from 'lucide-react'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'qco' | 'active' | 'withdrawn' | 'crs' | 'neutral' | 'ai'
  size?: 'sm' | 'md'
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  className,
  variant = 'neutral',
  size = 'sm',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full select-none'

  const sizes = {
    sm: 'text-xs px-2.5 py-0.5 gap-1.5',
    md: 'text-sm px-3 py-1 gap-2',
  }

  const variants = {
    qco: 'bg-amber-50 text-amber-900 border border-amber-300 shadow-[0_0_8px_rgba(245,158,11,0.25)] animate-pulse font-semibold',
    active: 'bg-emerald-50 text-emerald-800 border border-emerald-300 font-medium',
    withdrawn: 'bg-rose-50 text-rose-800 border border-rose-300 font-medium',
    crs: 'bg-blue-50 text-blue-800 border border-blue-200 font-medium',
    neutral: 'bg-slate-100 text-slate-700 border border-slate-200',
    ai: 'bg-indigo-50 text-indigo-700 border border-indigo-200 font-medium',
  }

  const icons = {
    qco: <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />,
    active: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />,
    withdrawn: <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />,
    crs: null,
    neutral: null,
    ai: <Sparkles className="w-3.5 h-3.5 text-indigo-600 shrink-0" />,
  }

  return (
    <span className={cn(baseStyles, sizes[size], variants[variant], className)} {...props}>
      {icons[variant]}
      {children}
    </span>
  )
}
