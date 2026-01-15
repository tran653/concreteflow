import { useState, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { plansApi } from '@/services/api'
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DxfUploaderProps {
  projetId: string
  onUploadComplete?: (plan: any) => void
}

export default function DxfUploader({ projetId, onUploadComplete }: DxfUploaderProps) {
  const queryClient = useQueryClient()
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadResult, setUploadResult] = useState<any>(null)

  const uploadMutation = useMutation({
    mutationFn: (file: File) => plansApi.uploadDxf(projetId, file),
    onSuccess: (data) => {
      setUploadResult(data)
      queryClient.invalidateQueries({ queryKey: ['plans', projetId] })
      if (onUploadComplete) {
        onUploadComplete(data)
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
      if (file.name.toLowerCase().endsWith('.dxf')) {
        setSelectedFile(file)
        setUploadResult(null)
      }
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setSelectedFile(files[0])
      setUploadResult(null)
    }
  }

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile)
    }
  }

  const resetUpload = () => {
    setSelectedFile(null)
    setUploadResult(null)
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
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
          dragActive
            ? 'border-primary bg-primary/5'
            : 'border-gray-300 hover:border-gray-400',
          uploadMutation.isPending && 'pointer-events-none opacity-50'
        )}
      >
        <input
          type="file"
          accept=".dxf"
          onChange={handleFileSelect}
          className="hidden"
          id="dxf-upload"
        />

        {!selectedFile ? (
          <label htmlFor="dxf-upload" className="cursor-pointer">
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-gray-700">
              Glissez un fichier DXF ici
            </p>
            <p className="text-sm text-gray-500 mt-1">
              ou cliquez pour sélectionner
            </p>
          </label>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-3">
              <File className="h-8 w-8 text-primary" />
              <div className="text-left">
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button
                onClick={resetUpload}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            {!uploadResult && (
              <button
                onClick={handleUpload}
                disabled={uploadMutation.isPending}
                className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
              >
                {uploadMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Import en cours...
                  </span>
                ) : (
                  'Importer le fichier'
                )}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Error */}
      {uploadMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Erreur d'import</p>
            <p className="text-sm text-red-600">
              {(uploadMutation.error as any)?.response?.data?.detail ||
                'Une erreur est survenue'}
            </p>
          </div>
        </div>
      )}

      {/* Success result */}
      {uploadResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-green-800">Import réussi</p>
              <div className="mt-2 text-sm text-green-700 space-y-1">
                <p>Fichier: {uploadResult.parse_result?.filename}</p>
                <p>Entités trouvées: {uploadResult.parse_result?.entity_count || 0}</p>
                <p>Contours: {uploadResult.parse_result?.contour_count || 0}</p>
                <p>Ouvertures: {uploadResult.parse_result?.opening_count || 0}</p>
                {uploadResult.geometry?.main_dimensions && (
                  <p>
                    Dimensions: {uploadResult.geometry.main_dimensions.length_m}m x{' '}
                    {uploadResult.geometry.main_dimensions.width_m}m
                  </p>
                )}
                {uploadResult.geometry?.net_area_m2 && (
                  <p>Surface nette: {uploadResult.geometry.net_area_m2} m²</p>
                )}
              </div>
            </div>
          </div>

          <div className="mt-4 flex gap-2">
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
