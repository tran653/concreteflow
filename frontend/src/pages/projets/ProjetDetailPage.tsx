import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projetsApi, calculsApi, plansApi } from '@/services/api'
import {
  ArrowLeft,
  Calculator,
  FileText,
  MapPin,
  Phone,
  Mail,
  Calendar,
  Loader2,
  Upload,
  Map,
  Trash2,
} from 'lucide-react'
import { cn, statusLabels, statusColors, formatDate, typeProduitLabels } from '@/lib/utils'
import DxfUploader from '@/components/calculs/DxfUploader'
import PlanCanvas from '@/components/calculs/PlanCanvas'
import ExportButtons from '@/components/calculs/ExportButtons'

export default function ProjetDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDxfUploader, setShowDxfUploader] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const deleteMutation = useMutation({
    mutationFn: () => projetsApi.delete(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projets'] })
      navigate('/projets')
    },
  })

  const handleDelete = () => {
    if (showDeleteConfirm) {
      deleteMutation.mutate()
    } else {
      setShowDeleteConfirm(true)
    }
  }

  const { data: projet, isLoading: loadingProjet } = useQuery({
    queryKey: ['projet', id],
    queryFn: () => projetsApi.get(id!),
    enabled: !!id,
  })

  const { data: stats } = useQuery({
    queryKey: ['projet-stats', id],
    queryFn: () => projetsApi.getStats(id!),
    enabled: !!id,
  })

  const { data: calculs = [] } = useQuery({
    queryKey: ['calculs', { projet_id: id }],
    queryFn: () => calculsApi.list({ projet_id: id }),
    enabled: !!id,
  })

  const { data: plans = [], refetch: refetchPlans } = useQuery({
    queryKey: ['plans', id],
    queryFn: () => plansApi.list(id!),
    enabled: !!id,
  })

  const { data: selectedPlanGeometry } = useQuery({
    queryKey: ['plan-geometry', selectedPlanId],
    queryFn: () => plansApi.getGeometry(selectedPlanId!),
    enabled: !!selectedPlanId,
  })

  if (loadingProjet) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!projet) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Projet non trouvé</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/projets"
          className="p-2 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <p className="text-sm text-gray-500">{projet.reference}</p>
          <h1 className="text-2xl font-bold text-gray-900">{projet.name}</h1>
        </div>
        <ExportButtons projetId={id} projetReference={projet.reference} />
        <button
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
            showDeleteConfirm
              ? 'bg-red-600 text-white hover:bg-red-700'
              : 'text-gray-600 hover:bg-gray-100 hover:text-red-600'
          )}
          title="Supprimer le projet"
        >
          <Trash2 className="h-4 w-4" />
          {showDeleteConfirm && (
            <span className="text-sm">
              {deleteMutation.isPending ? 'Suppression...' : 'Confirmer'}
            </span>
          )}
        </button>
        {showDeleteConfirm && (
          <button
            onClick={() => setShowDeleteConfirm(false)}
            className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            Annuler
          </button>
        )}
        <span
          className={cn(
            'px-3 py-1 text-sm rounded-full',
            statusColors[projet.status]
          )}
        >
          {statusLabels[projet.status]}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Plans</p>
          <p className="text-2xl font-bold">{plans.length || stats?.plans_count || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Calculs</p>
          <p className="text-2xl font-bold">{stats?.calculs_count || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Validés</p>
          <p className="text-2xl font-bold text-green-600">
            {stats?.calculs_completed || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">En attente</p>
          <p className="text-2xl font-bold text-yellow-600">
            {stats?.calculs_pending || 0}
          </p>
        </div>
      </div>

      {/* Plans section */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Plans DXF</h2>
          <button
            onClick={() => setShowDxfUploader(!showDxfUploader)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/90"
          >
            <Upload className="h-4 w-4" />
            Importer DXF
          </button>
        </div>

        {showDxfUploader && (
          <div className="p-4 border-b bg-gray-50">
            <DxfUploader
              projetId={id!}
              onUploadComplete={(plan) => {
                setShowDxfUploader(false)
                setSelectedPlanId(plan.id)
                refetchPlans()
              }}
            />
          </div>
        )}

        <div className="p-4">
          {plans.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Map className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>Aucun plan importé</p>
              <p className="text-sm">Importez un fichier DXF pour commencer</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Plan list */}
              <div className="flex flex-wrap gap-2">
                {plans.map((plan: any) => (
                  <button
                    key={plan.id}
                    onClick={() => setSelectedPlanId(plan.id)}
                    className={cn(
                      'px-4 py-2 rounded-lg border text-sm font-medium transition-colors',
                      selectedPlanId === plan.id
                        ? 'bg-primary text-white border-primary'
                        : 'bg-white text-gray-700 border-gray-300 hover:border-primary'
                    )}
                  >
                    {plan.name}
                  </button>
                ))}
              </div>

              {/* Plan viewer */}
              {selectedPlanGeometry && (
                <PlanCanvas
                  bounds={selectedPlanGeometry.bounds}
                  contours={selectedPlanGeometry.contours}
                  openings={selectedPlanGeometry.openings}
                  height={400}
                />
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Project info */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Informations</h2>

          {projet.description && (
            <p className="text-gray-600 mb-4">{projet.description}</p>
          )}

          <div className="space-y-3">
            {projet.client_name && (
              <div className="flex items-center gap-2 text-gray-600">
                <FileText className="h-4 w-4" />
                <span>Client: {projet.client_name}</span>
              </div>
            )}

            {projet.city && (
              <div className="flex items-center gap-2 text-gray-600">
                <MapPin className="h-4 w-4" />
                <span>
                  {projet.address && `${projet.address}, `}
                  {projet.postal_code} {projet.city}
                </span>
              </div>
            )}

            {projet.client_phone && (
              <div className="flex items-center gap-2 text-gray-600">
                <Phone className="h-4 w-4" />
                <span>{projet.client_phone}</span>
              </div>
            )}

            {projet.client_email && (
              <div className="flex items-center gap-2 text-gray-600">
                <Mail className="h-4 w-4" />
                <span>{projet.client_email}</span>
              </div>
            )}

            <div className="flex items-center gap-2 text-gray-600">
              <Calendar className="h-4 w-4" />
              <span>Créé le {formatDate(projet.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Calculations */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Calculs</h2>
            <Link
              to={`/calculs?projet_id=${projet.id}`}
              className="text-sm text-primary hover:underline"
            >
              Nouveau calcul
            </Link>
          </div>

          <div className="divide-y">
            {calculs.length === 0 ? (
              <div className="p-8 text-center">
                <Calculator className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Aucun calcul pour ce projet</p>
                <Link
                  to={`/calculs?projet_id=${projet.id}`}
                  className="inline-block mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                >
                  Créer un calcul
                </Link>
              </div>
            ) : (
              calculs.map((calcul) => (
                <Link
                  key={calcul.id}
                  to={`/calculs/${calcul.id}`}
                  className="p-4 hover:bg-gray-50 flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-gray-900">{calcul.name}</p>
                    <p className="text-sm text-gray-500">
                      {typeProduitLabels[calcul.type_produit]} - {formatDate(calcul.created_at)}
                    </p>
                  </div>
                  <span
                    className={cn(
                      'px-2 py-1 text-xs rounded-full',
                      statusColors[calcul.status]
                    )}
                  >
                    {statusLabels[calcul.status]}
                  </span>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
