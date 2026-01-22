/**
 * Page Réglages - Gestion des fabricants et cahiers de portées.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fabricantsApi } from '@/services/fabricantsApi'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Settings,
  Plus,
  Upload,
  Trash2,
  Building2,
  FileSpreadsheet,
  Loader2,
  X,
  ChevronDown,
  ChevronRight,
  AlertCircle,
} from 'lucide-react'
import { cn, formatDate } from '@/lib/utils'
import type { Fabricant, FabricantCreate, CahierPortees, TypePoutrelle } from '@/types'

const fabricantSchema = z.object({
  nom: z.string().min(1, 'Nom requis'),
  code: z.string().min(1, 'Code requis').max(20, 'Code trop long'),
  description: z.string().optional(),
  telephone: z.string().optional(),
  email: z.string().email('Email invalide').optional().or(z.literal('')),
  site_web: z.string().url('URL invalide').optional().or(z.literal('')),
})

const typePoutrelleLabels: Record<TypePoutrelle, string> = {
  precontrainte: 'Poutrelles précontraintes',
  treillis: 'Poutrelles à âme treillis',
}

export default function ReglagesPage() {
  const queryClient = useQueryClient()
  const [expandedFabricants, setExpandedFabricants] = useState<Set<string>>(new Set())
  const [showCreateFabricant, setShowCreateFabricant] = useState(false)
  const [importingFor, setImportingFor] = useState<{ fabricantId: string; fabricantNom: string } | null>(null)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importTypePoutrelle, setImportTypePoutrelle] = useState<TypePoutrelle>('precontrainte')
  const [importNom, setImportNom] = useState('')
  const [deletingCahier, setDeletingCahier] = useState<string | null>(null)

  // Fetch fabricants
  const { data: fabricants = [], isLoading: loadingFabricants } = useQuery({
    queryKey: ['fabricants'],
    queryFn: () => fabricantsApi.list(false), // Include inactive
  })

  // Form for creating fabricant
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FabricantCreate>({
    resolver: zodResolver(fabricantSchema),
  })

  // Create fabricant mutation
  const createFabricantMutation = useMutation({
    mutationFn: fabricantsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fabricants'] })
      setShowCreateFabricant(false)
      reset()
    },
  })

  // Delete fabricant mutation
  const deleteFabricantMutation = useMutation({
    mutationFn: fabricantsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fabricants'] })
    },
  })

  // Import cahier mutation
  const importCahierMutation = useMutation({
    mutationFn: async ({ fabricantId, file, nom, typePoutrelle }: {
      fabricantId: string
      file: File
      nom: string
      typePoutrelle: TypePoutrelle
    }) => {
      // Note: We'll pass type_poutrelle as query param
      const formData = new FormData()
      formData.append('file', file)

      const params = new URLSearchParams()
      if (nom) params.append('nom', nom)
      params.append('type_poutrelle', typePoutrelle)

      const response = await fetch(
        `/api/fabricants/${fabricantId}/cahiers/import?${params.toString()}`,
        {
          method: 'POST',
          body: formData,
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      )
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Erreur lors de l\'import')
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fabricants'] })
      queryClient.invalidateQueries({ queryKey: ['cahiers'] })
      setImportingFor(null)
      setImportFile(null)
      setImportNom('')
    },
  })

  // Delete cahier mutation
  const deleteCahierMutation = useMutation({
    mutationFn: fabricantsApi.deleteCahier,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fabricants'] })
      queryClient.invalidateQueries({ queryKey: ['cahiers'] })
      setDeletingCahier(null)
    },
  })

  const toggleFabricant = (id: string) => {
    setExpandedFabricants((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleImport = () => {
    if (!importingFor || !importFile) return
    importCahierMutation.mutate({
      fabricantId: importingFor.fabricantId,
      file: importFile,
      nom: importNom || importFile.name.replace(/\.[^.]+$/, ''),
      typePoutrelle: importTypePoutrelle,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Settings className="h-7 w-7" />
            Réglages
          </h1>
          <p className="text-gray-500">Gérez les fabricants et leurs cahiers de portées</p>
        </div>
        <button
          onClick={() => setShowCreateFabricant(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
        >
          <Plus className="h-5 w-5" />
          Nouveau fabricant
        </button>
      </div>

      {/* Fabricants list */}
      {loadingFabricants ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : fabricants.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Aucun fabricant</h3>
          <p className="text-gray-500 mt-1">
            Ajoutez un fabricant pour importer ses cahiers de portées
          </p>
          <button
            onClick={() => setShowCreateFabricant(true)}
            className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Ajouter un fabricant
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {fabricants.map((fabricant) => (
            <FabricantCard
              key={fabricant.id}
              fabricant={fabricant}
              isExpanded={expandedFabricants.has(fabricant.id)}
              onToggle={() => toggleFabricant(fabricant.id)}
              onImport={() => setImportingFor({ fabricantId: fabricant.id, fabricantNom: fabricant.nom })}
              onDelete={() => deleteFabricantMutation.mutate(fabricant.id)}
              onDeleteCahier={(cahierId) => setDeletingCahier(cahierId)}
            />
          ))}
        </div>
      )}

      {/* Create fabricant modal */}
      {showCreateFabricant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowCreateFabricant(false)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Nouveau fabricant</h2>
              <button
                onClick={() => setShowCreateFabricant(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit((data) => createFabricantMutation.mutate(data))} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Nom *</label>
                <input
                  {...register('nom')}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="Ex: Rector, KP1, Spurgin..."
                />
                {errors.nom && (
                  <p className="mt-1 text-sm text-red-600">{errors.nom.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Code *</label>
                <input
                  {...register('code')}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="Ex: RECT, KP1..."
                />
                {errors.code && (
                  <p className="mt-1 text-sm text-red-600">{errors.code.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  {...register('description')}
                  rows={2}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Téléphone</label>
                  <input
                    {...register('telephone')}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <input
                    {...register('email')}
                    type="email"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Site web</label>
                <input
                  {...register('site_web')}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="https://..."
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateFabricant(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={createFabricantMutation.isPending}
                  className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
                >
                  {createFabricantMutation.isPending ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    'Créer'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import cahier modal */}
      {importingFor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setImportingFor(null)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Importer un cahier de portées</h2>
              <button
                onClick={() => setImportingFor(null)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              Fabricant: <span className="font-medium text-gray-900">{importingFor.fabricantNom}</span>
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type de poutrelle *
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setImportTypePoutrelle('precontrainte')}
                    className={cn(
                      'p-3 border-2 rounded-lg text-left transition-colors',
                      importTypePoutrelle === 'precontrainte'
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 hover:border-gray-300'
                    )}
                  >
                    <p className="font-medium text-sm">Précontrainte</p>
                    <p className="text-xs text-gray-500">Poutrelles béton précontraint</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setImportTypePoutrelle('treillis')}
                    className={cn(
                      'p-3 border-2 rounded-lg text-left transition-colors',
                      importTypePoutrelle === 'treillis'
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 hover:border-gray-300'
                    )}
                  >
                    <p className="font-medium text-sm">Âme treillis</p>
                    <p className="text-xs text-gray-500">Poutrelles métalliques</p>
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Nom du cahier
                </label>
                <input
                  value={importNom}
                  onChange={(e) => setImportNom(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="Ex: Gamme standard 2024"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Fichier Excel *
                </label>
                <div
                  className={cn(
                    'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
                    importFile ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-gray-400'
                  )}
                  onClick={() => document.getElementById('import-file')?.click()}
                >
                  <input
                    id="import-file"
                    type="file"
                    accept=".xlsx,.xls"
                    className="hidden"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  />
                  {importFile ? (
                    <div className="flex items-center justify-center gap-2">
                      <FileSpreadsheet className="h-6 w-6 text-primary" />
                      <span className="font-medium">{importFile.name}</span>
                    </div>
                  ) : (
                    <>
                      <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-500">
                        Cliquez pour sélectionner un fichier Excel
                      </p>
                    </>
                  )}
                </div>
              </div>

              {importCahierMutation.error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                  <AlertCircle className="h-4 w-4" />
                  {(importCahierMutation.error as Error).message}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setImportingFor(null)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Annuler
                </button>
                <button
                  onClick={handleImport}
                  disabled={!importFile || importCahierMutation.isPending}
                  className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
                >
                  {importCahierMutation.isPending ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    'Importer'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete cahier confirmation */}
      {deletingCahier && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setDeletingCahier(null)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
            <h2 className="text-lg font-semibold mb-2">Supprimer le cahier ?</h2>
            <p className="text-gray-500 text-sm mb-4">
              Cette action supprimera définitivement le cahier et toutes ses données de portées.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeletingCahier(null)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={() => deleteCahierMutation.mutate(deletingCahier)}
                disabled={deleteCahierMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {deleteCahierMutation.isPending ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  'Supprimer'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Fabricant card component
function FabricantCard({
  fabricant,
  isExpanded,
  onToggle,
  onImport,
  onDelete,
  onDeleteCahier,
}: {
  fabricant: Fabricant
  isExpanded: boolean
  onToggle: () => void
  onImport: () => void
  onDelete: () => void
  onDeleteCahier: (cahierId: string) => void
}) {
  // Fetch cahiers for this fabricant
  const { data: cahiers = [] } = useQuery({
    queryKey: ['cahiers', fabricant.id],
    queryFn: () => fabricantsApi.listCahiers(fabricant.id),
    enabled: isExpanded,
  })

  // Group cahiers by type_poutrelle
  const cahiersByType = cahiers.reduce((acc, cahier) => {
    const type = cahier.type_poutrelle || 'precontrainte'
    if (!acc[type]) acc[type] = []
    acc[type].push(cahier)
    return acc
  }, {} as Record<TypePoutrelle, CahierPortees[]>)

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Header */}
      <div
        className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
          <Building2 className="h-6 w-6 text-primary" />
          <div>
            <p className="font-medium text-gray-900">{fabricant.nom}</p>
            <p className="text-sm text-gray-500">{fabricant.code}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onImport()
            }}
            className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"
            title="Importer un cahier"
          >
            <Upload className="h-4 w-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
            className="p-2 text-gray-500 hover:bg-red-50 hover:text-red-600 rounded-lg"
            title="Supprimer le fabricant"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t px-4 py-4">
          {cahiers.length === 0 ? (
            <div className="text-center py-6 text-gray-500">
              <FileSpreadsheet className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Aucun cahier de portées</p>
              <button
                onClick={onImport}
                className="text-sm text-primary hover:underline mt-1"
              >
                Importer un cahier Excel
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Poutrelles précontraintes */}
              {cahiersByType.precontrainte && cahiersByType.precontrainte.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full" />
                    Poutrelles précontraintes
                  </h4>
                  <div className="space-y-2">
                    {cahiersByType.precontrainte.map((cahier) => (
                      <CahierRow key={cahier.id} cahier={cahier} onDelete={() => onDeleteCahier(cahier.id)} />
                    ))}
                  </div>
                </div>
              )}

              {/* Poutrelles treillis */}
              {cahiersByType.treillis && cahiersByType.treillis.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <span className="w-2 h-2 bg-orange-500 rounded-full" />
                    Poutrelles à âme treillis
                  </h4>
                  <div className="space-y-2">
                    {cahiersByType.treillis.map((cahier) => (
                      <CahierRow key={cahier.id} cahier={cahier} onDelete={() => onDeleteCahier(cahier.id)} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Cahier row component
function CahierRow({ cahier, onDelete }: { cahier: CahierPortees; onDelete: () => void }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3">
        <FileSpreadsheet className="h-5 w-5 text-green-600" />
        <div>
          <p className="font-medium text-sm text-gray-900">{cahier.nom}</p>
          <p className="text-xs text-gray-500">
            {cahier.version && `v${cahier.version} • `}
            Importé le {formatDate(cahier.imported_at || cahier.created_at)}
          </p>
        </div>
      </div>
      <button
        onClick={onDelete}
        className="p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600 rounded"
        title="Supprimer"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  )
}
