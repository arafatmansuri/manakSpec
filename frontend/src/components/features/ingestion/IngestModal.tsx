import React, { useState, useRef } from 'react'
import { Modal } from '@/components/common/Modal'
import { Button } from '@/components/common/Button'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { setActiveModal, addToast } from '@/store/slices/uiSlice'
import { standardsApi } from '@/api/standardsApi'
import { UploadCloud, FileArchive, FileText, FileCode, X, Plus, ChevronDown, ChevronUp, Check } from 'lucide-react'

export const IngestModal: React.FC = () => {
  const dispatch = useAppDispatch()
  const activeModal = useAppSelector((state) => state.ui.activeModal)
  const isOpen = activeModal === 'ingest'

  const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single')
  const [file, setFile] = useState<File | null>(null)
  const [bulkFiles, setBulkFiles] = useState<File[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Toggle for manual metadata entry (Point 2)
  const [showManualOverrides, setShowManualOverrides] = useState(false)

  // Single Standard Form Overrides
  const [isNumber, setIsNumber] = useState('')
  const [title, setTitle] = useState('')
  const [year, setYear] = useState('')
  const [scope, setScope] = useState('')
  const [isQco, setIsQco] = useState(false)
  // Default to empty string so ISI Scheme-I is NOT selected automatically (Point 3)
  const [schemeType, setSchemeType] = useState('')
  const [specsJson, setSpecsJson] = useState('')

  const bulkInputRef = useRef<HTMLInputElement>(null)

  const handleClose = () => {
    dispatch(setActiveModal(null))
    setFile(null)
    setBulkFiles([])
    setShowManualOverrides(false)
    setIsNumber('')
    setTitle('')
    setYear('')
    setScope('')
    setIsQco(false)
    setSchemeType('')
    setSpecsJson('')
  }

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      dispatch(addToast({ message: 'Please select a BIS PDF or JSON document.', type: 'error' }))
      return
    }

    try {
      setIsSubmitting(true)
      const formData = new FormData()
      formData.append('file', file)
      if (showManualOverrides) {
        if (isNumber.trim()) formData.append('is_number', isNumber.trim())
        if (title.trim()) formData.append('title', title.trim())
        if (year.trim()) formData.append('publication_year', year.trim())
        if (scope.trim()) formData.append('scope', scope.trim())
        formData.append('is_mandatory_qco', String(isQco))
        if (schemeType.trim()) formData.append('scheme_type', schemeType.trim())
        if (specsJson.trim()) formData.append('technical_specifications_json', specsJson.trim())
      }

      await standardsApi.ingestStandard(formData)
      dispatch(addToast({ message: `Successfully ingested standard ${isNumber || file.name}!`, type: 'success' }))
      handleClose()
    } catch (err: any) {
      dispatch(addToast({ message: `Ingestion failed: ${err.message}`, type: 'error' }))
    } finally {
      setIsSubmitting(false)
    }
  }

  // Handle bulk file selection with persistence (Point 4)
  const handleBulkFilesSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedList = Array.from(e.target.files)
      setBulkFiles((prev) => {
        const existingNames = new Set(prev.map((f) => f.name))
        const newFiles = selectedList.filter((f) => !existingNames.has(f.name))
        return [...prev, ...newFiles]
      })
    }
    // reset input value so re-selecting same file triggers event
    if (bulkInputRef.current) bulkInputRef.current.value = ''
  }

  const handleRemoveBulkFile = (index: number) => {
    setBulkFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (bulkFiles.length === 0) {
      dispatch(addToast({ message: 'Please add at least one file or ZIP archive.', type: 'error' }))
      return
    }

    try {
      setIsSubmitting(true)
      const formData = new FormData()
      for (const f of bulkFiles) {
        formData.append('files', f)
      }

      await standardsApi.ingestBulk(formData)
      dispatch(addToast({ message: `Bulk ingestion queued for ${bulkFiles.length} file(s)!`, type: 'success' }))
      handleClose()
    } catch (err: any) {
      dispatch(addToast({ message: `Bulk ingestion failed: ${err.message}`, type: 'error' }))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Ingest Indian Standards (BIS)" maxWidth="lg">
      <div className="space-y-4 max-h-[80vh] overflow-y-auto pr-1">
        {/* Responsive Tab switcher */}
        <div className="flex border-b border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab('single')}
            className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-colors cursor-pointer ${
              activeTab === 'single'
                ? 'border-amber-500 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            Single Standard Upload
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('bulk')}
            className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-colors cursor-pointer ${
              activeTab === 'bulk'
                ? 'border-amber-500 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            Bulk Ingestion (ZIP / Multi-file)
          </button>
        </div>

        {activeTab === 'single' ? (
          <form onSubmit={handleSingleSubmit} className="space-y-4 text-xs">
            {/* Primary Document File Input */}
            <div className="p-4 rounded-xl border border-dashed border-slate-300 bg-slate-50/70 hover:bg-slate-50 transition-colors">
              <label className="block font-bold text-slate-800 mb-1.5">
                BIS Standard Document (.pdf or .json) *
              </label>
              <input
                type="file"
                accept=".pdf,.json"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
                required
              />
              {file && (
                <div className="mt-2 text-[11px] text-emerald-700 font-semibold flex items-center gap-1.5">
                  <Check className="w-3.5 h-3.5" />
                  <span>Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                </div>
              )}
            </div>

            {/* Checkbox to reveal manual entry (Point 2) */}
            <div className="pt-1">
              <label className="flex items-center gap-2.5 text-xs font-semibold text-slate-700 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={showManualOverrides}
                  onChange={(e) => setShowManualOverrides(e.target.checked)}
                  className="rounded text-amber-500 focus:ring-amber-400 w-4 h-4"
                />
                <span>Add manual metadata overrides (Optional)</span>
                {showManualOverrides ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
              </label>
            </div>

            {/* Manual entry inputs (Hidden by default) */}
            {showManualOverrides && (
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-3 animate-in fade-in duration-150">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">IS Code Override</label>
                    <input
                      type="text"
                      placeholder="e.g. IS 16106:2023"
                      value={isNumber}
                      onChange={(e) => setIsNumber(e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-amber-500 shadow-2xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Publication Year</label>
                    <input
                      type="number"
                      placeholder="e.g. 2023"
                      value={year}
                      onChange={(e) => setYear(e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-amber-500 shadow-2xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Standard Title</label>
                  <input
                    type="text"
                    placeholder="Title of Indian Standard"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-amber-500 shadow-2xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Scope & Overview</label>
                  <textarea
                    rows={2}
                    placeholder="Brief description of the standard scope..."
                    value={scope}
                    onChange={(e) => setScope(e.target.value)}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-amber-500 shadow-2xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Technical Specifications (JSON format)</label>
                  <textarea
                    rows={2}
                    placeholder='{"luminous_efficacy": "100 lm/W", "surge_limit": "2.5 kV"}'
                    value={specsJson}
                    onChange={(e) => setSpecsJson(e.target.value)}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 font-mono text-[11px] text-slate-900 focus:outline-none focus:border-amber-500 shadow-2xs"
                  />
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={isQco}
                      onChange={(e) => setIsQco(e.target.checked)}
                      className="rounded text-amber-500 focus:ring-amber-400 w-4 h-4"
                    />
                    <span className="font-semibold text-slate-800">Mandatory Quality Control Order (QCO)</span>
                  </label>

                  {/* Scheme type: Default is empty (Point 3) */}
                  <div className="flex items-center gap-2">
                    <label className="font-semibold text-slate-700 shrink-0">Scheme:</label>
                    <select
                      value={schemeType}
                      onChange={(e) => setSchemeType(e.target.value)}
                      className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-amber-500 shadow-2xs"
                    >
                      <option value="">Select Scheme (Optional)</option>
                      <option value="ISI Scheme-I">ISI Scheme-I</option>
                      <option value="CRS Scheme-II">CRS Scheme-II</option>
                      <option value="Voluntary Scheme">Voluntary Scheme</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            <div className="pt-3 border-t border-slate-200 flex justify-end gap-2">
              <Button type="button" variant="outline" size="sm" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="amber"
                size="sm"
                isLoading={isSubmitting}
                leftIcon={<UploadCloud className="w-4 h-4" />}
              >
                Ingest Standard
              </Button>
            </div>
          </form>
        ) : (
          /* Bulk Ingestion with persistent file list and removal (Point 4) */
          <form onSubmit={handleBulkSubmit} className="space-y-4 text-xs">
            {/* Hidden file input for adding files */}
            <input
              ref={bulkInputRef}
              type="file"
              multiple
              accept=".zip,.pdf,.json"
              onChange={handleBulkFilesSelect}
              className="hidden"
            />

            <div
              onClick={() => bulkInputRef.current?.click()}
              className="p-5 rounded-xl border border-dashed border-slate-300 bg-slate-50/80 hover:bg-slate-50 transition-colors text-center cursor-pointer group"
            >
              <FileArchive className="w-8 h-8 text-blue-600 mx-auto mb-2 group-hover:scale-105 transition-transform" />
              <p className="font-bold text-slate-800">Click to select ZIP Archive or PDF/JSON Documents</p>
              <p className="text-[11px] text-slate-500 mt-1">You can add multiple times to expand the upload queue.</p>
            </div>

            {/* List of selected files with remove buttons (Point 4) */}
            {bulkFiles.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-700">
                    Selected Files ({bulkFiles.length})
                  </span>
                  <button
                    type="button"
                    onClick={() => bulkInputRef.current?.click()}
                    className="text-blue-600 hover:text-blue-800 font-bold flex items-center gap-1 text-[11px] cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add More Files</span>
                  </button>
                </div>

                <div className="max-h-48 overflow-y-auto space-y-1.5 p-2 rounded-xl bg-slate-50 border border-slate-200">
                  {bulkFiles.map((f, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200 shadow-2xs text-xs"
                    >
                      <div className="flex items-center gap-2 min-w-0 pr-2">
                        {f.name.endsWith('.pdf') ? (
                          <FileText className="w-4 h-4 text-red-500 shrink-0" />
                        ) : f.name.endsWith('.json') ? (
                          <FileCode className="w-4 h-4 text-blue-500 shrink-0" />
                        ) : (
                          <FileArchive className="w-4 h-4 text-amber-500 shrink-0" />
                        )}
                        <span className="font-medium text-slate-800 truncate">{f.name}</span>
                        <span className="text-[10px] text-slate-400 shrink-0">
                          ({(f.size / 1024 / 1024).toFixed(2)} MB)
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleRemoveBulkFile(idx)}
                        className="text-slate-400 hover:text-red-600 p-1 rounded transition-colors cursor-pointer shrink-0"
                        title="Remove file"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-3 border-t border-slate-200 flex justify-end gap-2">
              <Button type="button" variant="outline" size="sm" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={isSubmitting}
                disabled={bulkFiles.length === 0}
                leftIcon={<UploadCloud className="w-4 h-4" />}
              >
                Upload & Ingest ({bulkFiles.length} files)
              </Button>
            </div>
          </form>
        )}
      </div>
    </Modal>
  )
}
