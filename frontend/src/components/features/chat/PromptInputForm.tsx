import React, { useState, useRef, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useAppSelector } from '@/store/hooks'
import { Button } from '@/components/common/Button'
import { Send, Paperclip, X, FileText, Image, FileCode, CheckCircle2 } from 'lucide-react'
import type { RecommendationFormInputs } from '@/types/form'

interface PromptInputFormProps {
  onSubmit: (data: { query_text: string; file: File | null; language: string }) => void
  isLoading?: boolean
  initialQuery?: string
  centered?: boolean
}

export const PromptInputForm: React.FC<PromptInputFormProps> = ({
  onSubmit,
  isLoading,
  initialQuery = '',
  centered = false,
}) => {
  const [showAttachMenu, setShowAttachMenu] = useState(false)
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const preferredLanguage = useAppSelector((state) => state.session.preferredLanguage)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [currentAccept, setCurrentAccept] = useState('.pdf,.docx,.txt,.png,.jpg,.jpeg')

  const { register, handleSubmit, reset, setValue, watch } = useForm<RecommendationFormInputs>({
    defaultValues: {
      query_text: initialQuery,
      language: preferredLanguage,
    },
  })

  const queryText = watch('query_text') || ''

  // Sync initial query if passed (e.g. from Draft Clause button)
  useEffect(() => {
    if (initialQuery) {
      setValue('query_text', initialQuery)
      textareaRef.current?.focus()
    }
  }, [initialQuery, setValue])

  // Auto-resize textarea as query expands
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const newHeight = Math.min(textareaRef.current.scrollHeight, 180)
      textareaRef.current.style.height = `${Math.max(newHeight, 38)}px`
    }
  }, [queryText])

  const handleSelectFileType = (acceptType: string) => {
    setCurrentAccept(acceptType)
    setShowAttachMenu(false)
    setTimeout(() => {
      fileInputRef.current?.click()
    }, 50)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setAttachedFile(e.target.files[0])
    }
  }

  const handleFormSubmit = (data: RecommendationFormInputs) => {
    if (!data.query_text?.trim() && !attachedFile) {
      return
    }

    onSubmit({
      query_text: data.query_text || '',
      file: attachedFile,
      language: preferredLanguage,
    })

    reset({ query_text: '', language: preferredLanguage })
    setAttachedFile(null)
    if (textareaRef.current) {
      textareaRef.current.style.height = '38px'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(handleFormSubmit)()
    }
  }

  const { ref: registerRef, ...registerRest } = register('query_text')

  return (
    <div className={`w-full ${centered ? 'max-w-2xl' : 'max-w-4xl'} mx-auto`}>
      {/* Hidden file input controlled by mini selection box */}
      <input
        ref={fileInputRef}
        type="file"
        accept={currentAccept}
        onChange={handleFileChange}
        className="hidden"
      />

      <form
        onSubmit={handleSubmit(handleFormSubmit)}
        className="relative rounded-2xl bg-white border border-slate-300 shadow-sm focus-within:border-amber-500 focus-within:ring-2 focus-within:ring-amber-500/20 transition-all p-2 sm:p-2.5"
      >
        {/* Attached file chip */}
        {attachedFile && (
          <div className="mb-2 flex items-center justify-between p-1.5 px-3 rounded-lg bg-amber-50 border border-amber-200 text-xs">
            <div className="flex items-center gap-2 min-w-0 pr-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span className="font-semibold text-amber-900 truncate">{attachedFile.name}</span>
              <span className="text-[10px] text-amber-700 shrink-0">
                ({(attachedFile.size / 1024 / 1024).toFixed(2)} MB)
              </span>
            </div>
            <button
              type="button"
              onClick={() => setAttachedFile(null)}
              className="text-amber-700 hover:text-amber-900 p-0.5 rounded cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        <div className="flex items-end gap-2">
          {/* Attachment button & mini selection menu */}
          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => setShowAttachMenu(!showAttachMenu)}
              className={`p-2 rounded-xl text-xs transition-colors cursor-pointer ${
                attachedFile
                  ? 'bg-amber-100 text-amber-800 border border-amber-300'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
              }`}
              title="Attach Tender / Specification Document"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            {/* Mini Selection Box (Point 11) */}
            {showAttachMenu && (
              <div className="absolute bottom-full left-0 mb-2 w-48 rounded-xl bg-white border border-slate-200 shadow-xl py-1 z-30 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                  Select Document Type
                </div>
                <button
                  type="button"
                  onClick={() => handleSelectFileType('.pdf')}
                  className="w-full text-left px-3 py-2 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center gap-2.5 transition-colors cursor-pointer"
                >
                  <FileText className="w-4 h-4 text-red-500" />
                  <span className="font-medium">PDF Tender Document</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectFileType('.docx')}
                  className="w-full text-left px-3 py-2 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center gap-2.5 transition-colors cursor-pointer"
                >
                  <FileCode className="w-4 h-4 text-blue-500" />
                  <span className="font-medium">Word Document (.docx)</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectFileType('.txt,.csv')}
                  className="w-full text-left px-3 py-2 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center gap-2.5 transition-colors cursor-pointer"
                >
                  <FileText className="w-4 h-4 text-slate-500" />
                  <span className="font-medium">Plain Text / CSV</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectFileType('.png,.jpg,.jpeg')}
                  className="w-full text-left px-3 py-2 text-xs text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center gap-2.5 transition-colors cursor-pointer"
                >
                  <Image className="w-4 h-4 text-emerald-500" />
                  <span className="font-medium">Scanned Image / Spec</span>
                </button>
              </div>
            )}
          </div>

          {/* Auto-expanding Textarea */}
          <div className="flex-1 min-w-0">
            <textarea
              {...registerRest}
              ref={(e) => {
                registerRef(e)
                ;(textareaRef as any).current = e
              }}
              onKeyDown={handleKeyDown}
              placeholder="Describe product or paste RFP requirements... (Shift+Enter for newline)"
              rows={1}
              style={{ minHeight: '38px' }}
              className="w-full bg-transparent text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none resize-none leading-relaxed py-1.5 px-1"
            />
          </div>

          {/* Submit Button (Sleek and compact - Point 6) */}
          <div className="shrink-0 flex items-center">
            <Button
              type="submit"
              variant="amber"
              size="sm"
              isLoading={isLoading}
              disabled={isLoading || (!queryText?.trim() && !attachedFile)}
              className="h-9 px-3 rounded-xl font-bold shadow-xs text-xs"
              rightIcon={<Send className="w-3.5 h-3.5" />}
            >
              <span className="hidden sm:inline">Analyze</span>
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}
