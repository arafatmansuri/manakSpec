import React, { useState } from 'react'
import type { TenderClause } from '@/types/standards'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { useExport } from '@/hooks/useExport'
import { Copy, Check, FileDown, ShieldAlert, FileText, CheckCircle2, ChevronDown, Sparkles } from 'lucide-react'

interface TenderClauseViewerProps {
  clause: TenderClause
  sessionId?: string
  messageId?: string
}

export const TenderClauseViewer: React.FC<TenderClauseViewerProps> = ({
  clause,
  sessionId,
  messageId,
}) => {
  const [copied, setCopied] = useState(false)
  const { exportDocument, isExporting } = useExport()
  const [showExportMenu, setShowExportMenu] = useState(false)

  const handleCopy = async () => {
    const fullText = `
=== TENDER SPECIFICATION CLAUSE ===
${clause.title}

1. STANDARD COMPLIANCE:
${clause.standard_compliance}

2. MANDATORY REGULATORY CERTIFICATION (QCO):
${clause.mandatory_cert_clause}

3. TECHNICAL SPECIFICATIONS & PARAMETERS:
${clause.technical_specifications?.map((s) => `• ${s}`).join('\n')}

4. TESTING, INSPECTION & DOCUMENTATION:
${clause.testing_and_documentation}
===================================
`.trim()

    await navigator.clipboard.writeText(fullText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleExport = (format: 'pdf' | 'docx' | 'txt' | 'md') => {
    const targetIdentifier = messageId || sessionId
    if (targetIdentifier) {
      exportDocument(targetIdentifier, format)
    }
    setShowExportMenu(false)
  }

  return (
    <Card className="border-amber-300/80 bg-gradient-to-br from-white via-white to-amber-50/40 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-amber-100">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-100 text-amber-800 border border-amber-300">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-amber-900 flex items-center gap-1.5">
              <span>Procurement Tender Clause Drafting</span>
              <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            </h4>
            <p className="text-[11px] text-slate-500">
              Ready to copy and paste into GeM bids, NIT schedules, or RFP documents
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleCopy}
            className="text-xs"
            leftIcon={
              copied ? (
                <Check className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <Copy className="w-3.5 h-3.5 text-slate-600" />
              )
            }
          >
            {copied ? 'Copied to Clipboard!' : 'Copy Clause'}
          </Button>

          {/* Export Dropdown */}
          <div className="relative">
            <Button
              size="sm"
              variant="amber"
              onClick={() => setShowExportMenu(!showExportMenu)}
              isLoading={isExporting}
              className="text-xs"
              leftIcon={<FileDown className="w-3.5 h-3.5" />}
              rightIcon={<ChevronDown className="w-3 h-3 ml-0.5" />}
            >
              Download
            </Button>

            {showExportMenu && (
              <div className="absolute right-0 mt-1.5 w-40 rounded-xl bg-white border border-slate-200 shadow-xl py-1 z-30 animate-in fade-in zoom-in-95 duration-150">
                <button
                  onClick={() => handleExport('docx')}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <span className="font-medium">Word Document</span>
                  <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">.docx</span>
                </button>
                <button
                  onClick={() => handleExport('pdf')}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <span className="font-medium">PDF Document</span>
                  <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">.pdf</span>
                </button>
                <button
                  onClick={() => handleExport('md')}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <span className="font-medium">Markdown</span>
                  <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">.md</span>
                </button>
                <button
                  onClick={() => handleExport('txt')}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <span className="font-medium">Plain Text</span>
                  <span className="text-[10px] font-mono text-slate-400 font-bold uppercase">.txt</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Clause Sections */}
      <div className="space-y-3 text-xs leading-relaxed">
        {/* Title */}
        {clause.title && (
          <div className="p-3 rounded-xl bg-amber-50/60 border border-amber-200/80 font-semibold text-slate-900">
            <span className="text-amber-800 font-bold uppercase tracking-wider text-[10px] block mb-0.5">
              Subject Clause
            </span>
            {clause.title}
          </div>
        )}

        {/* Standard Compliance */}
        {clause.standard_compliance && (
          <div className="space-y-1">
            <span className="text-slate-700 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              1. Standard Compliance
            </span>
            <p className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-800">
              {clause.standard_compliance}
            </p>
          </div>
        )}

        {/* Mandatory Certification (QCO) */}
        {clause.mandatory_cert_clause && (
          <div className="space-y-1">
            <span className="text-amber-900 font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
              2. Mandatory Certification Order (QCO Compliance)
            </span>
            <p className="p-3 rounded-xl bg-amber-50/50 border border-amber-200 text-amber-950 font-medium">
              {clause.mandatory_cert_clause}
            </p>
          </div>
        )}

        {/* Technical Specifications */}
        {clause.technical_specifications && clause.technical_specifications.length > 0 && (
          <div className="space-y-1">
            <span className="text-slate-700 font-bold text-[11px] uppercase tracking-wide block">
              3. Prescribed Technical Specifications & Limits
            </span>
            <ul className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 text-slate-800">
              {clause.technical_specifications.map((spec, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-amber-600 font-mono text-xs font-bold">•</span>
                  <span>{spec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Testing & Documentation */}
        {clause.testing_and_documentation && (
          <div className="space-y-1">
            <span className="text-slate-700 font-bold text-[11px] uppercase tracking-wide block">
              4. Testing, Inspection & Verification
            </span>
            <p className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-800">
              {clause.testing_and_documentation}
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}
