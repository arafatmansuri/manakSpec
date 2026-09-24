import React from 'react'
import { cn } from '@/utils/cn'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  hoverEffect = false,
  ...props
}) => {
  return (
    <div
      className={cn(
        'rounded-2xl bg-white border border-slate-200/90 p-5 shadow-xs',
        hoverEffect &&
          'transition-all duration-200 hover:border-slate-300 hover:bg-white hover:-translate-y-0.5 hover:shadow-md',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
