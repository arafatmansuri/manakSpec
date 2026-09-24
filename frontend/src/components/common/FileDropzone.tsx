import React, { useRef, useState } from 'react'
import { UploadCloud, FileText, X, AlertCircle } from 'lucide-react'
import { cn } from '@/utils/cn'

interface FileDropzoneProps {
  onFileSelect: (file: File | null) => void
  selectedFile: File | null
  className?: string
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({
  onFileSelect,
  selectedFile,
  className,
}) => {
  const [isDragOver, setIsDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const allowedExtensions = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg']

  const validateAndSet = (file: File) => {
    setError(null)
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!allowedExtensions.includes(ext)) {
      setError(`Unsupported format (${ext}). Use PDF, DOCX, TXT, or images.`)
      return
    }
    if (file.size > 25 * 1024 * 1024) {
      setError('File size exceeds 25MB limit.')
      return
    }
    onFileSelect(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSet(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSet(e.target.files[0])
    }
  }

  return (
    <div className={cn('w-full', className)}>
      {!selectedFile ? (
        <div
          onDragOver={(e) => {
            e.preventDefault()
            setIsDragOver(true)
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={cn(
            'group relative flex flex-col items-center justify-center p-4 border border-dashed rounded-xl cursor-pointer transition-all duration-200',
            isDragOver
              ? 'border-amber-500 bg-amber-500/10'
              : 'border-slate-700/80 bg-slate-900/40 hover:bg-slate-800/40 hover:border-slate-600'
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
            onChange={handleChange}
            className="hidden"
          />
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 group-hover:text-amber-400 group-hover:border-amber-500/40 transition-colors">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-200">
                Attach RFP, Tender Schedule, or Specification Doc
              </p>
              <p className="text-[11px] text-slate-400">
                Supports PDF, Word (.docx), TXT, or scan images (max 25MB)
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/90 border border-slate-700/90 shadow-sm animate-in fade-in zoom-in-95 duration-200">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-slate-200 truncate">
                {selectedFile.name}
              </p>
              <p className="text-[10px] text-slate-400">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Ready for Indian Standards Analysis
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onFileSelect(null)}
            className="p-1.5 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
            title="Remove attachment"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-1.5 mt-2 text-xs text-rose-400">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}
