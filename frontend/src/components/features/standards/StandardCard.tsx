import React, { useState } from 'react'
import type { PrimaryStandard } from '@/types/standards'
import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { BookOpen, Calendar, ChevronDown, ChevronUp, Layers, CheckCircle2 } from 'lucide-react'

interface StandardCardProps {
  standard: PrimaryStandard
}

export const StandardCard: React.FC<StandardCardProps> = ({ standard }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const hasSpecs =
    standard.technical_specifications &&
    Object.keys(standard.technical_specifications).length > 0

  return (
    <Card hoverEffect className="border-slate-200 bg-white text-left space-y-3 shadow-xs">
      {/* Header with IS Number and Status Badges */}
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-blue-50 text-blue-700 border border-blue-200">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <span className="font-mono font-bold text-sm tracking-wide text-amber-600">
              {standard.is_number}
            </span>
            {standard.publication_year && (
              <span className="ml-2 text-[11px] text-slate-500 inline-flex items-center gap-1">
                <Calendar className="w-3 h-3 inline mr-0.5 text-slate-400" />
                {standard.publication_year}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {standard.is_mandatory_qco && (
            <Badge variant="qco" size="sm">
              Mandatory QCO
            </Badge>
          )}
          {standard.scheme_type && (
            <Badge variant="crs" size="sm">
              {standard.scheme_type}
            </Badge>
          )}
          {standard.status && (
            <Badge
              variant={standard.status.toLowerCase().includes('active') ? 'active' : 'neutral'}
              size="sm"
            >
              {standard.status}
            </Badge>
          )}
        </div>
      </div>

      {/* Title */}
      <h4 className="text-sm font-bold text-slate-900 leading-snug">
        {standard.title}
      </h4>

      {/* Scope or Summary */}
      {standard.scope_text && (
        <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
          {standard.scope_text}
        </p>
      )}

      {/* Committee & Match info */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-500 pt-2 border-t border-slate-100">
        {standard.committee_code && (
          <div className="flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <span>Committee: {standard.committee_code}</span>
          </div>
        )}
        {standard.similarity_score > 0 && (
          <div className="flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span className="font-medium text-emerald-800">Match: {(standard.similarity_score * 100).toFixed(0)}%</span>
          </div>
        )}
      </div>

      {/* Technical Specifications Accordion */}
      {hasSpecs && (
        <div className="pt-1">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center justify-between w-full p-2 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-[11px] font-semibold text-slate-700 transition-colors cursor-pointer"
          >
            <span>Technical Specifications & Parameter Limits</span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-500" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-500" />}
          </button>

          {isExpanded && (
            <div className="mt-2 p-3 rounded-xl bg-slate-50 border border-slate-200 font-mono text-[11px] text-slate-800 space-y-1.5 animate-in fade-in duration-150">
              {Object.entries(standard.technical_specifications).map(([key, val]) => (
                <div key={key} className="flex justify-between items-baseline gap-2 border-b border-slate-200/60 pb-1 last:border-0 last:pb-0">
                  <span className="text-slate-600 font-medium capitalize">{key.replace(/_/g, ' ')}:</span>
                  <span className="text-amber-800 font-semibold text-right">{String(val)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
