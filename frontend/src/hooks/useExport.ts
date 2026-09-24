import { useState } from 'react'
import { standardsApi } from '@/api/standardsApi'
import { useAppDispatch } from '@/store/hooks'
import { addToast } from '@/store/slices/uiSlice'

export function useExport() {
  const [isExporting, setIsExporting] = useState(false)
  const dispatch = useAppDispatch()

  const exportDocument = async (
    identifier: string,
    format: 'pdf' | 'docx' | 'txt' | 'md' = 'docx',
    filenamePrefix: string = 'ManakSpec_Tender_Clause'
  ) => {
    try {
      setIsExporting(true)
      const blob = await standardsApi.exportTender(identifier, format)
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${filenamePrefix}_${identifier.substring(0, 8)}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      dispatch(
        addToast({
          message: `Successfully downloaded ${format.toUpperCase()} document!`,
          type: 'success',
        })
      )
    } catch (err: any) {
      dispatch(
        addToast({
          message: `Export failed: ${err.message || 'Server error during export.'}`,
          type: 'error',
        })
      )
    } finally {
      setIsExporting(false)
    }
  }

  return { exportDocument, isExporting }
}
