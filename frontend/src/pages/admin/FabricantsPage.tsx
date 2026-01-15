/**
 * Page de gestion des fabricants et cahiers de portées.
 */
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Upload, Trash2, FileSpreadsheet, Building2, ChevronDown, ChevronRight } from 'lucide-react'
import { fabricantsApi } from '@/services/fabricantsApi'
import { formatDate } from '@/lib/utils'
import type { Fabricant, CahierPortees, FabricantCreate } from '@/types'

export default function FabricantsPage() {
  const queryClient = useQueryClient()
  const [selectedFabricant, setSelectedFabricant] = useState<string | null>(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [expandedFabricants, setExpandedFabricants] = useState<Set<string>>(new Set())
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadingFor, setUploadingFor] = useState<string | null>(null)

  // Queries
  const { data: fabricants, isLoading } = useQuery({
    queryKey: ['fabricants'],
    queryFn: () => fabricantsApi.list()
  })

  const { data: cahiers } = useQuery({
    queryKey: ['cahiers', selectedFabricant],
    queryFn: () => selectedFabricant ? fabricantsApi.listCahiers(selectedFabricant) : Promise.resolve([]),
    enabled: !!selectedFabricant
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: FabricantCreate) => fabricantsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fabricants'] })
      setShowCreateDialog(false)
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => fabricantsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fabricants'] })
    }
  })

  const importMutation = useMutation({
    mutationFn: ({ fabricantId, file }: { fabricantId: string; file: File }) =>
      fabricantsApi.importCahier(fabricantId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['cahiers', variables.fabricantId] })
      setUploadingFor(null)
    }
  })

  const deleteCahierMutation = useMutation({
    mutationFn: (cahierId: string) => fabricantsApi.deleteCahier(cahierId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cahiers'] })
    }
  })

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedFabricants)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
      if (selectedFabricant === id) setSelectedFabricant(null)
    } else {
      newExpanded.add(id)
      setSelectedFabricant(id)
    }
    setExpandedFabricants(newExpanded)
  }

  const handleFileUpload = (fabricantId: string) => {
    setUploadingFor(fabricantId)
    fileInputRef.current?.click()
  }

  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && uploadingFor) {
      importMutation.mutate({ fabricantId: uploadingFor, file })
    }
    e.target.value = ''
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fabricants</h1>
          <p className="text-gray-600">Gérez les fabricants et leurs cahiers de portées limites</p>
        </div>
        <button
          onClick={() => setShowCreateDialog(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Nouveau fabricant
        </button>
      </div>

      {/* Liste des fabricants */}
      <div className="bg-white rounded-lg shadow">
        {!fabricants?.length ? (
          <div className="p-8 text-center text-gray-500">
            <Building2 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Aucun fabricant enregistré</p>
            <button
              onClick={() => setShowCreateDialog(true)}
              className="mt-4 text-blue-600 hover:underline"
            >
              Ajouter votre premier fabricant
            </button>
          </div>
        ) : (
          <div className="divide-y">
            {fabricants.map((fab) => (
              <div key={fab.id}>
                {/* En-tête fabricant */}
                <div
                  className="flex items-center justify-between p-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => toggleExpanded(fab.id)}
                >
                  <div className="flex items-center gap-3">
                    {expandedFabricants.has(fab.id) ? (
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-gray-400" />
                    )}
                    <Building2 className="h-5 w-5 text-blue-600" />
                    <div>
                      <h3 className="font-medium text-gray-900">{fab.nom}</h3>
                      <p className="text-sm text-gray-500">Code: {fab.code}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleFileUpload(fab.id)
                      }}
                      className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title="Importer un cahier"
                    >
                      <Upload className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm('Supprimer ce fabricant ?')) {
                          deleteMutation.mutate(fab.id)
                        }
                      }}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                      title="Supprimer"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Cahiers de portées (expandable) */}
                {expandedFabricants.has(fab.id) && selectedFabricant === fab.id && (
                  <div className="bg-gray-50 px-4 pb-4">
                    <div className="ml-8">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Cahiers de portées</h4>
                      {!cahiers?.length ? (
                        <p className="text-sm text-gray-500 italic">Aucun cahier importé</p>
                      ) : (
                        <div className="space-y-2">
                          {cahiers.map((cahier) => (
                            <CahierCard
                              key={cahier.id}
                              cahier={cahier}
                              onDelete={() => deleteCahierMutation.mutate(cahier.id)}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Input file caché pour upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        onChange={handleFileSelected}
        className="hidden"
      />

      {/* Dialog création fabricant */}
      {showCreateDialog && (
        <CreateFabricantDialog
          onClose={() => setShowCreateDialog(false)}
          onSubmit={(data) => createMutation.mutate(data)}
          isLoading={createMutation.isPending}
        />
      )}

      {/* Loading overlay pour import */}
      {importMutation.isPending && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Import en cours...</p>
          </div>
        </div>
      )}
    </div>
  )
}

// Composant carte cahier
function CahierCard({ cahier, onDelete }: { cahier: CahierPortees; onDelete: () => void }) {
  return (
    <div className="flex items-center justify-between p-3 bg-white rounded border">
      <div className="flex items-center gap-3">
        <FileSpreadsheet className="h-5 w-5 text-green-600" />
        <div>
          <p className="font-medium text-gray-900">{cahier.nom}</p>
          <p className="text-xs text-gray-500">
            {cahier.version && `v${cahier.version} - `}
            Importé le {formatDate(cahier.imported_at || cahier.created_at)}
          </p>
        </div>
      </div>
      <button
        onClick={onDelete}
        className="p-1 text-gray-400 hover:text-red-600"
        title="Supprimer"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  )
}

// Dialog création fabricant
function CreateFabricantDialog({
  onClose,
  onSubmit,
  isLoading
}: {
  onClose: () => void
  onSubmit: (data: FabricantCreate) => void
  isLoading: boolean
}) {
  const [formData, setFormData] = useState<FabricantCreate>({
    nom: '',
    code: '',
    description: '',
    email: '',
    telephone: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold mb-4">Nouveau fabricant</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nom *
            </label>
            <input
              type="text"
              required
              value={formData.nom}
              onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="Ex: RECTOR, KP1, SEAC..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Code *
            </label>
            <input
              type="text"
              required
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="Ex: REC, KP1..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
              rows={2}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Téléphone
              </label>
              <input
                type="tel"
                value={formData.telephone || ''}
                onChange={(e) => setFormData({ ...formData, telephone: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Création...' : 'Créer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
