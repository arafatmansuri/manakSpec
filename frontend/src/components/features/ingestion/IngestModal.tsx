import React, { useState } from 'react'
import { Modal } from '@/components/common/Modal'
import { Button } from '@/components/common/Button'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { setActiveModal, addToast } from '@/store/slices/uiSlice'
import { standardsApi } from '@/api/standardsApi'
import { UploadCloud, FileArchive } from 'lucide-react'

export const IngestModal: React.FC = () => {
  const dispatch = useAppDispatch()
  const activeModal = useAppSelector((state) => state.ui.activeModal)
  const isOpen = activeModal === 'ingest'

  const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single')
  const [file, setFile] = useState<File | null>(null)
  const [bulkFiles, setBulkFiles] = useState<FileList | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Single Standard Form Overrides
  const [isNumber, setIsNumber] = useState('')
  const [title, setTitle] = useState('')
  const [year, setYear] = useState('')
  const [scope, setScope] = useState('')
  const [isQco, setIsQco] = useState(false)
  const [schemeType, setSchemeType] = useState('ISI Scheme-I')
  const [specsJson, setSpecsJson] = useState('')

  const handleClose = () => {
    dispatch(setActiveModal(null))
    setFile(null)
    setBulkFiles(null)
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
      if (isNumber) formData.append('is_number', isNumber)
      if (title) formData.append('title', title)
      if (year) formData.append('publication_year', year)
      if (scope) formData.append('scope', scope)
      formData.append('is_mandatory_qco', String(isQco))
      if (schemeType) formData.append('scheme_type', schemeType)
      if (specsJson) formData.append('technical_specifications_json', specsJson)

      await standardsApi.ingestStandard(formData)
      dispatch(addToast({ message: `Successfully ingested standard ${isNumber || file.name}!`, type: 'success' }))
      handleClose()
    } catch (err: any) {
      dispatch(addToast({ message: `Ingestion failed: ${err.message}`, type: 'error' }))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!bulkFiles || bulkFiles.length === 0) {
      dispatch(addToast({ message: 'Please select files or a ZIP archive.', type: 'error' }))
      return
    }

    try {
      setIsSubmitting(true)
      const formData = new FormData()
      for (let i = 0; i < bulkFiles.length; i++) {
        formData.append('files', bulkFiles[i])
      }

      await standardsApi.ingestBulk(formData)
      dispatch(addToast({ message: 'Bulk ingestion job queued successfully!', type: 'success' }))
      handleClose()
    } catch (err: any) {
      dispatch(addToast({ message: `Bulk ingestion failed: ${err.message}`, type: 'error' }))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Ingest Indian Standards (BIS)" maxWidth="lg">
      <div className="space-y-4">
        {/* Tab switch */}
        <div className="flex border-b border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab('single')}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
              activeTab === 'single'
                ? 'border-amber-500 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Single Standard Upload
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('bulk')}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
              activeTab === 'bulk'
                ? 'border-amber-500 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Bulk Ingestion (ZIP / Multi-PDF)
          </button>
        </div>

        {activeTab === 'single' ? (
          <form onSubmit={handleSingleSubmit} className="space-y-3 text-xs">
            {/* File input */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">BIS Document (.pdf or .json) *</label>
              <input
                type="file"
                accept=".pdf,.json"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div>
                <label className="block font-medium text-slate-600 mb-1">IS Code Override</label>
                <input
                  type="text"
                  placeholder="e.g. IS 16106:2023"
                  value={isNumber}
                  onChange={(e) => setIsNumber(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-600 mb-1">Publication Year</label>
                <input
                  type="number"
                  placeholder="e.g. 2023"
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            <div>
              <label className="block font-medium text-slate-600 mb-1">Standard Title</label>
              <input
                type="text"
                placeholder="Title of Indian Standard"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-600 mb-1">Scope & Overview</label>
              <textarea
                rows={2}
                placeholder="Brief scope text..."
                value={scope}
                onChange={(e) => setScope(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-600 mb-1">Technical Specifications (JSON format, optional)</label>
              <textarea
                rows={2}
                placeholder='e.g. {"luminous_efficacy": "100 lm/W", "surge_limit": "2.5 kV"}'
                value={specsJson}
                onChange={(e) => setSpecsJson(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 font-mono text-[11px] text-slate-900 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex items-center gap-4 pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={isQco}
                  onChange={(e) => setIsQco(e.target.checked)}
                  className="rounded text-amber-500 focus:ring-amber-400"
                />
                <span className="font-semibold text-slate-800">Mandatory Quality Control Order (QCO)</span>
              </label>

              <select
                value={schemeType}
                onChange={(e) => setSchemeType(e.target.value)}
                className="bg-slate-50 border border-slate-300 rounded-lg px-2 py-1 text-xs text-slate-800"
              >
                <option value="ISI Scheme-I">ISI Scheme-I</option>
                <option value="CRS Scheme-II">CRS Scheme-II</option>
                <option value="Voluntary Scheme">Voluntary Scheme</option>
              </select>
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
              <Button type="button" variant="outline" size="sm" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" variant="amber" size="sm" isLoading={isSubmitting} leftIcon={<UploadCloud className="w-4 h-4" />}>
                Ingest Standard
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleBulkSubmit} className="space-y-4 text-xs">
            <div className="p-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 text-center">
              <FileArchive className="w-8 h-8 text-blue-500 mx-auto mb-2" />
              <p className="font-semibold text-slate-800">Upload ZIP Archive or Multiple PDF/JSON Files</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Files will be extracted and embedded in database automatically.</p>
              <input
                type="file"
                multiple
                accept=".zip,.pdf,.json"
                onChange={(e) => setBulkFiles(e.target.files)}
                className="mt-3 w-full text-xs text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
                required
              />
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
              <Button type="button" variant="outline" size="sm" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting} leftIcon={<UploadCloud className="w-4 h-4" />}>
                Start Bulk Processing
              </Button>
            </div>
          </form>
        )}
      </div>
    </Modal>
  )
}
