import React from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/common/Button'
import { ShieldAlert, Home } from 'lucide-react'

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-4">
      <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
        <ShieldAlert className="w-8 h-8 text-amber-400" />
      </div>
      <h1 className="text-2xl font-extrabold text-slate-100">404 - Page Not Found</h1>
      <p className="text-xs text-slate-400 max-w-sm">
        The requested procurement page or BIS standard reference could not be located.
      </p>
      <Link to="/">
        <Button variant="amber" size="md" leftIcon={<Home className="w-4 h-4" />}>
          Back to Assistant
        </Button>
      </Link>
    </div>
  )
}
