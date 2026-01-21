import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { calculsApi, type PdfExtractionResult, type ExtractedValue } from '@/services/api'
import {
  Upload,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  AlertTriangle,
  Eye,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface PdfPlanUploaderProps {
  onExtracted?: (data: PdfExtractionResult) => void
  onApplyData?: (params: ExtractedParameters) => void
}

export interface ExtractedParameters {
  portee_m?: number
  charge_permanente_kn_m2?: number
  charge_exploitation_kn_m2?: number
  entraxe_cm?: number
  epaisseur_dalle_cm?: number
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'text-green-600 bg-green-50'
  if (confidence >= 0.5) return 'text-yellow-600 bg-yellow-50'
  return 'text-red-600 bg-red-50'
}

function getConfidenceIcon(confidence: number) {
  if (confidence >= 0.8) return <CheckCircle className="h-4 w-4" />
  if (confidence >= 0.5) return <AlertTriangle className="h-4 w-4" />
  return <AlertCircle className="h-4 w-4" />
}

function ExtractedValueDisplay({
  label,
  value,
  unit,
}: {
  label: string
  value: ExtractedValue | null
  unit?: string
}) {
  if (!value) {
    return (
      <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
        <span className="text-sm text-gray-500">{label}</span>
        <span className="text-sm text-gray-400 italic">Non trouvé</span>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-between py-2 px-3 bg-white border rounded">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold">
          {value.value}
          {unit && <span className="text-gray-500 ml-1">{unit}</span>}
        </span>
        <span
          className={cn(
            'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs',
            getConfidenceColor(value.confidence)
          )}
          title={`Source: ${value.source}`}
        >
          {getConfidenceIcon(value.confidence)}
          {Math.round(value.confidence * 100)}%
        </span>
      </div>
    </div>
  )
}

export default function PdfPlanUploader({ onExtracted, onApplyData }: PdfPlanUploaderProps) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [useOcr, setUseOcr] = useState(false)
  const [extractedData, setExtractedData] = useState<PdfExtractionResult | null>(null)
  const [showPreview, setShowPreview] = useState(false)

  const uploadMutation = useMutation({
    mutationFn: (file: File) => calculsApi.importPdf(file, useOcr),
    onSuccess: (data) => {
      setExtractedData(data)
      if (onExtracted) {
        onExtracted(data)
      }
    },
  })

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      const file = files[0]
      if (file.name.toLowerCase().endsWith('.pdf')) {
        setSelectedFile(file)
        setExtractedData(null)
      }
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setSelectedFile(files[0])
      setExtractedData(null)
    }
  }

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile)
    }
  }

  const resetUpload = () => {
    setSelectedFile(null)
    setExtractedData(null)
    setShowPreview(false)
  }

  const handleApplyData = () => {
    if (!extractedData || !onApplyData) return

    const params: ExtractedParameters = {}
    const data = extractedData.data

    // Get first non-null values
    if (data.portees.length > 0 && data.portees[0]) {
      params.portee_m = data.portees[0].value as number
    }
    if (data.charges_permanentes.length > 0 && data.charges_permanentes[0]) {
      params.charge_permanente_kn_m2 = data.charges_permanentes[0].value as number
    }
    if (data.charges_exploitation.length > 0 && data.charges_exploitation[0]) {
      params.charge_exploitation_kn_m2 = data.charges_exploitation[0].value as number
    }
    if (data.entre_axes.length > 0 && data.entre_axes[0]) {
      params.entraxe_cm = data.entre_axes[0].value as number
    }
    if (data.epaisseur_dalle) {
      params.epaisseur_dalle_cm = data.epaisseur_dalle.value as number
    }

    onApplyData(params)
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={cn(
          'border-2 border-dashed rounded-lg p-6 text-center transition-colors',
          dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400',
          uploadMutation.isPending && 'pointer-events-none opacity-50'
        )}
      >
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="hidden"
          id="pdf-upload"
        />

        {!selectedFile ? (
          <label htmlFor="pdf-upload" className="cursor-pointer">
            <Upload className="h-10 w-10 text-gray-400 mx-auto mb-3" />
            <p className="text-base font-medium text-gray-700">
              Glissez un plan PDF ici
            </p>
            <p className="text-sm text-gray-500 mt-1">
              ou cliquez pour sélectionner
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Les données (portées, charges, etc.) seront extraites automatiquement
            </p>
          </label>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-3">
              <FileText className="h-8 w-8 text-blue-600" />
              <div className="text-left">
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button onClick={resetUpload} className="p-1 hover:bg-gray-100 rounded">
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            {!extractedData && (
              <div className="space-y-3">
                <label className="flex items-center justify-center gap-2 text-sm text-gray-600">
                  <input
                    type="checkbox"
                    checked={useOcr}
                    onChange={(e) => setUseOcr(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span>Utiliser OCR (pour plans scannés)</span>
                </label>

                <button
                  onClick={handleUpload}
                  disabled={uploadMutation.isPending}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {uploadMutation.isPending ? (
                    <span className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Extraction en cours...
                    </span>
                  ) : (
                    'Extraire les données'
                  )}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error */}
      {uploadMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Erreur d'extraction</p>
            <p className="text-sm text-red-600">
              {(uploadMutation.error as any)?.response?.data?.detail ||
                "Une erreur est survenue lors de l'extraction du PDF"}
            </p>
          </div>
        </div>
      )}

      {/* Extracted data */}
      {extractedData && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="font-medium text-gray-900">Données extraites</span>
              <span
                className={cn(
                  'px-2 py-0.5 rounded text-xs font-medium',
                  getConfidenceColor(extractedData.extraction_confidence)
                )}
              >
                Confiance: {Math.round(extractedData.extraction_confidence * 100)}%
              </span>
            </div>
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
            >
              <Eye className="h-4 w-4" />
              {showPreview ? 'Masquer' : 'Texte brut'}
            </button>
          </div>

          <div className="p-4 space-y-2">
            <ExtractedValueDisplay
              label="Portée"
              value={extractedData.data.portees[0] || null}
              unit="m"
            />
            <ExtractedValueDisplay
              label="Charge permanente (G)"
              value={extractedData.data.charges_permanentes[0] || null}
              unit="kN/m²"
            />
            <ExtractedValueDisplay
              label="Charge d'exploitation (Q)"
              value={extractedData.data.charges_exploitation[0] || null}
              unit="kN/m²"
            />
            <ExtractedValueDisplay
              label="Entre-axe"
              value={extractedData.data.entre_axes[0] || null}
              unit="cm"
            />
            <ExtractedValueDisplay
              label="Épaisseur dalle"
              value={extractedData.data.epaisseur_dalle}
              unit="cm"
            />
            <ExtractedValueDisplay
              label="Type hourdis"
              value={extractedData.data.type_hourdis}
            />

            {extractedData.tables_found > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                {extractedData.tables_found} tableau(x) détecté(s) dans le PDF
              </p>
            )}
          </div>

          {showPreview && extractedData.raw_text_preview && (
            <div className="px-4 pb-4">
              <div className="bg-gray-900 rounded p-3 max-h-40 overflow-auto">
                <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">
                  {extractedData.raw_text_preview}
                </pre>
              </div>
            </div>
          )}

          <div className="px-4 py-3 bg-gray-50 border-t flex gap-2">
            {onApplyData && (
              <button
                onClick={handleApplyData}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
              >
                Appliquer au formulaire
              </button>
            )}
            <button
              onClick={resetUpload}
              className="px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Importer un autre fichier
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
