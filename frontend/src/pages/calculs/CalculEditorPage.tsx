import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { calculsApi } from '@/services/api'
import {
  ArrowLeft,
  Play,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Save,
} from 'lucide-react'
import { cn, statusLabels, statusColors, typeProduitLabels } from '@/lib/utils'
import type { CalculParametres, Calcul } from '@/types'
import ExportButtons from '@/components/calculs/ExportButtons'
import PlancherPoutrellesForm from '@/components/calculs/PlancherPoutrellesForm'
import PlancherResultats from '@/components/calculs/PlancherResultats'

export default function CalculEditorPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const [parametres, setParametres] = useState<CalculParametres>({
    geometrie: { portee: 5.0, largeur: 1.0, hauteur: 0.2 },
    charges: { permanentes: 5.0, exploitation: 2.5 },
    materiaux: { classe_beton: 'C30/37', classe_acier: 'S500' },
    conditions: { classe_exposition: 'XC1', duree_vie: 50 },
  })

  const { data: calcul, isLoading } = useQuery({
    queryKey: ['calcul', id],
    queryFn: () => calculsApi.get(id!),
    enabled: !!id,
  })

  // Update parametres when calcul data is loaded
  useEffect(() => {
    if (calcul?.parametres && Object.keys(calcul.parametres).length > 0) {
      setParametres(calcul.parametres as CalculParametres)
    } else if (calcul?.type_produit === 'plancher_poutrelles_hourdis') {
      // Default parameters for plancher poutrelles-hourdis
      setParametres({
        geometrie: { portee: 5.0 },
        charges: { permanentes: 2.5, exploitation: 2.5 },
        materiaux: {},
        conditions: { optimisation: 'economique' },
      })
    }
  }, [calcul])

  const updateMutation = useMutation({
    mutationFn: (params: CalculParametres) =>
      calculsApi.update(id!, { parametres: params }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calcul', id] })
    },
  })

  const runMutation = useMutation({
    mutationFn: () => calculsApi.run(id!, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calcul', id] })
    },
  })

  const handleSave = () => {
    updateMutation.mutate(parametres)
  }

  const handleRun = () => {
    updateMutation.mutate(parametres, {
      onSuccess: () => {
        runMutation.mutate()
      },
    })
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!calcul) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Calcul non trouvé</p>
      </div>
    )
  }

  const resultats = calcul.resultats || {}
  const isComputed = calcul.status === 'completed'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/calculs" className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <p className="text-sm text-gray-500">
              {typeProduitLabels[calcul.type_produit]} - {calcul.norme}
            </p>
            <h1 className="text-2xl font-bold text-gray-900">{calcul.name}</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={cn(
              'px-3 py-1 text-sm rounded-full',
              statusColors[calcul.status]
            )}
          >
            {statusLabels[calcul.status]}
          </span>
          {isComputed && (
            <ExportButtons
              calculId={id}
              projetId={calcul.projet_id}
              calculName={calcul.name}
            />
          )}
          <button
            onClick={handleSave}
            disabled={updateMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Save className="h-4 w-4" />
            Sauvegarder
          </button>
          <button
            onClick={handleRun}
            disabled={runMutation.isPending || updateMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            {runMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Calculer
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input parameters */}
        <div className="space-y-6">
          {/* Geometry */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Géométrie</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Portée (m)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={parametres.geometrie.portee || ''}
                  onChange={(e) =>
                    setParametres({
                      ...parametres,
                      geometrie: {
                        ...parametres.geometrie,
                        portee: parseFloat(e.target.value),
                      },
                    })
                  }
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Largeur (m)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={parametres.geometrie.largeur || ''}
                  onChange={(e) =>
                    setParametres({
                      ...parametres,
                      geometrie: {
                        ...parametres.geometrie,
                        largeur: parseFloat(e.target.value),
                      },
                    })
                  }
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Hauteur (m)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={parametres.geometrie.hauteur || ''}
                  onChange={(e) =>
                    setParametres({
                      ...parametres,
                      geometrie: {
                        ...parametres.geometrie,
                        hauteur: parseFloat(e.target.value),
                      },
                    })
                  }
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                />
              </div>
            </div>
          </div>

          {/* Loads */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Charges (kN/m²)</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Permanentes (G)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={parametres.charges.permanentes || ''}
                  onChange={(e) =>
                    setParametres({
                      ...parametres,
                      charges: {
                        ...parametres.charges,
                        permanentes: parseFloat(e.target.value),
                      },
                    })
                  }
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Exploitation (Q)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={parametres.charges.exploitation || ''}
                  onChange={(e) =>
                    setParametres({
                      ...parametres,
                      charges: {
                        ...parametres.charges,
                        exploitation: parseFloat(e.target.value),
                      },
                    })
                  }
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                />
              </div>
            </div>
          </div>

          {/* Materials */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Matériaux</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Classe béton
                </label>
                <select
                  value={parametres.materiaux.classe_beton || 'C30/37'}
                  onChange={(e) =>
                    setParametres({
                      ...parametres,
                      materiaux: {
                        ...parametres.materiaux,
                        classe_beton: e.target.value,
                      },
                    })
                  }
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                >
                  <option value="C20/25">C20/25</option>
                  <option value="C25/30">C25/30</option>
                  <option value="C30/37">C30/37</option>
                  <option value="C35/45">C35/45</option>
                  <option value="C40/50">C40/50</option>
                  <option value="C45/55">C45/55</option>
                  <option value="C50/60">C50/60</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Classe acier
                </label>
                <select
                  value={parametres.materiaux.classe_acier || 'S500'}
                  onChange={(e) =>
                    setParametres({
                      ...parametres,
                      materiaux: {
                        ...parametres.materiaux,
                        classe_acier: e.target.value,
                      },
                    })
                  }
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                >
                  <option value="S400">S400</option>
                  <option value="S500">S500</option>
                  <option value="S500B">S500B</option>
                  <option value="S500C">S500C</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="space-y-6">
          {/* Summary */}
          {isComputed && resultats.summary && (
            <div
              className={cn(
                'rounded-lg shadow p-6',
                resultats.summary.verification_globale === 'OK'
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              )}
            >
              <div className="flex items-center gap-3">
                {resultats.summary.verification_globale === 'OK' ? (
                  <CheckCircle className="h-8 w-8 text-green-600" />
                ) : (
                  <XCircle className="h-8 w-8 text-red-600" />
                )}
                <div>
                  <h2 className="font-semibold text-gray-900">
                    Vérification {resultats.summary.verification_globale}
                  </h2>
                  <p className="text-sm text-gray-600">
                    {resultats.summary.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Flexion */}
          {isComputed && resultats.flexion && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">Flexion</h2>
                {resultats.flexion.verification_ok ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600" />
                )}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Moment ELU:</span>
                  <span className="font-medium">
                    {resultats.flexion.moment_elu_kNm?.toFixed(2)} kN.m
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Section acier:</span>
                  <span className="font-medium">
                    {resultats.flexion.as_final_cm2?.toFixed(2)} cm²
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Deflection */}
          {isComputed && resultats.fleche && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">Flèche</h2>
                {resultats.fleche.verification_ok ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600" />
                )}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Flèche calculée:</span>
                  <span className="font-medium">
                    {resultats.fleche.fleche_totale_mm?.toFixed(2)} mm
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Flèche limite:</span>
                  <span className="font-medium">
                    {resultats.fleche.fleche_limite_mm?.toFixed(2)} mm
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Shear */}
          {isComputed && resultats.effort_tranchant && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">Effort tranchant</h2>
                {resultats.effort_tranchant.verification_ok ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600" />
                )}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">VEd:</span>
                  <span className="font-medium">
                    {resultats.effort_tranchant.effort_tranchant_kN?.toFixed(2)} kN
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Armatures transv.:</span>
                  <span className="font-medium">
                    {resultats.effort_tranchant.as_transversal_cm2_m?.toFixed(2)} cm²/m
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Reinforcement summary */}
          {isComputed && resultats.ferraillage && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="font-semibold text-gray-900 mb-4">Ferraillage</h2>
              <div className="space-y-2 text-sm">
                {resultats.ferraillage.armatures_inferieures?.designation && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Armatures inférieures:</span>
                    <span className="font-medium font-mono">
                      {resultats.ferraillage.armatures_inferieures.designation}
                    </span>
                  </div>
                )}
                {resultats.ferraillage.armatures_superieures?.designation && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Armatures supérieures:</span>
                    <span className="font-medium font-mono">
                      {resultats.ferraillage.armatures_superieures.designation}
                    </span>
                  </div>
                )}
                {resultats.ferraillage.armatures_transversales?.designation && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Cadres:</span>
                    <span className="font-medium font-mono">
                      {resultats.ferraillage.armatures_transversales.designation}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Not computed yet */}
          {!isComputed && calcul.status !== 'computing' && (
            <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                Aucun résultat
              </h3>
              <p className="text-gray-500 mt-2">
                Configurez les paramètres et cliquez sur "Calculer"
              </p>
            </div>
          )}

          {calcul.status === 'computing' && (
            <div className="bg-blue-50 rounded-lg border border-blue-200 p-12 text-center">
              <Loader2 className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-spin" />
              <h3 className="text-lg font-medium text-gray-900">
                Calcul en cours...
              </h3>
            </div>
          )}

          {calcul.status === 'error' && (
            <div className="bg-red-50 rounded-lg border border-red-200 p-6">
              <div className="flex items-center gap-3">
                <XCircle className="h-8 w-8 text-red-600" />
                <div>
                  <h3 className="font-medium text-red-800">Erreur de calcul</h3>
                  <p className="text-sm text-red-600">{calcul.error_message}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
