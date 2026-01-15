import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { exportsApi, downloadFile } from '@/services/api'
import {
  FileText,
  FileSpreadsheet,
  Download,
  Loader2,
  ChevronDown,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface ExportButtonsProps {
  calculId?: string
  projetId?: string
  calculName?: string
  projetReference?: string
}

export default function ExportButtons({
  calculId,
  projetId,
  calculName = 'calcul',
  projetReference = 'projet',
}: ExportButtonsProps) {
  const [showMenu, setShowMenu] = useState(false)

  // Export calcul PDF
  const exportPdfMutation = useMutation({
    mutationFn: () => exportsApi.downloadCalculPdf(calculId!),
    onSuccess: (blob) => {
      downloadFile(blob, `note_calcul_${calculName.replace(/\s/g, '_')}.pdf`)
    },
  })

  // Export calcul Excel
  const exportExcelMutation = useMutation({
    mutationFn: () => exportsApi.downloadCalculExcel(calculId!),
    onSuccess: (blob) => {
      downloadFile(blob, `calcul_${calculName.replace(/\s/g, '_')}.xlsx`)
    },
  })

  // Export nomenclature
  const exportNomenclatureMutation = useMutation({
    mutationFn: () => exportsApi.downloadNomenclature(projetId!),
    onSuccess: (blob) => {
      downloadFile(blob, `nomenclature_${projetReference}.xlsx`)
    },
  })

  // Export quantitatif
  const exportQuantitatifMutation = useMutation({
    mutationFn: () => exportsApi.downloadQuantitatif(projetId!),
    onSuccess: (blob) => {
      downloadFile(blob, `quantitatif_${projetReference}.xlsx`)
    },
  })

  const isLoading =
    exportPdfMutation.isPending ||
    exportExcelMutation.isPending ||
    exportNomenclatureMutation.isPending ||
    exportQuantitatifMutation.isPending

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        disabled={isLoading}
        className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Download className="h-4 w-4" />
        )}
        Exporter
        <ChevronDown className="h-4 w-4" />
      </button>

      {showMenu && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border z-20">
            <div className="py-1">
              {calculId && (
                <>
                  <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase">
                    Calcul
                  </div>
                  <button
                    onClick={() => {
                      exportPdfMutation.mutate()
                      setShowMenu(false)
                    }}
                    disabled={exportPdfMutation.isPending}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FileText className="h-4 w-4 text-red-600" />
                    Note de calcul (PDF)
                  </button>
                  <button
                    onClick={() => {
                      exportExcelMutation.mutate()
                      setShowMenu(false)
                    }}
                    disabled={exportExcelMutation.isPending}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FileSpreadsheet className="h-4 w-4 text-green-600" />
                    Résultats (Excel)
                  </button>
                </>
              )}

              {projetId && (
                <>
                  <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase border-t mt-1 pt-2">
                    Projet
                  </div>
                  <button
                    onClick={() => {
                      exportNomenclatureMutation.mutate()
                      setShowMenu(false)
                    }}
                    disabled={exportNomenclatureMutation.isPending}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FileSpreadsheet className="h-4 w-4 text-green-600" />
                    Nomenclature (Excel)
                  </button>
                  <button
                    onClick={() => {
                      exportQuantitatifMutation.mutate()
                      setShowMenu(false)
                    }}
                    disabled={exportQuantitatifMutation.isPending}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <FileSpreadsheet className="h-4 w-4 text-blue-600" />
                    Quantitatif (Excel)
                  </button>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
