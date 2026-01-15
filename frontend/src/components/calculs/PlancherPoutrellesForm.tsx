/**
 * Formulaire de paramètres pour le calcul plancher poutrelles-hourdis.
 */
import { useQuery } from '@tanstack/react-query'
import { fabricantsApi } from '@/services/fabricantsApi'
import { hauteursHourdis, entraxesCourants, optimisationLabels } from '@/lib/utils'
import type { CalculParametres, Fabricant, CahierPortees } from '@/types'

interface Props {
  parametres: CalculParametres
  onChange: (parametres: CalculParametres) => void
}

export default function PlancherPoutrellesForm({ parametres, onChange }: Props) {
  // Fetch fabricants
  const { data: fabricants } = useQuery({
    queryKey: ['fabricants'],
    queryFn: () => fabricantsApi.list()
  })

  // Extract fabricant_id from cahier selection
  const selectedCahierId = parametres.cahier_portees_id
  const selectedFabricantId = parametres.geometrie?.fabricant_id as string | undefined

  // Fetch cahiers for selected fabricant
  const { data: cahiers } = useQuery({
    queryKey: ['cahiers', selectedFabricantId],
    queryFn: () => selectedFabricantId ? fabricantsApi.listCahiers(selectedFabricantId) : Promise.resolve([]),
    enabled: !!selectedFabricantId
  })

  const handleFabricantChange = (fabricantId: string) => {
    onChange({
      ...parametres,
      cahier_portees_id: undefined,
      geometrie: {
        ...parametres.geometrie,
        fabricant_id: fabricantId
      }
    })
  }

  const handleCahierChange = (cahierId: string) => {
    onChange({
      ...parametres,
      cahier_portees_id: cahierId
    })
  }

  return (
    <div className="space-y-6">
      {/* Cahier de portées */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Cahier de portées</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Fabricant *
            </label>
            <select
              value={selectedFabricantId || ''}
              onChange={(e) => handleFabricantChange(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
            >
              <option value="">Sélectionner un fabricant</option>
              {fabricants?.map((fab: Fabricant) => (
                <option key={fab.id} value={fab.id}>
                  {fab.nom} ({fab.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Cahier de portées *
            </label>
            <select
              value={selectedCahierId || ''}
              onChange={(e) => handleCahierChange(e.target.value)}
              disabled={!selectedFabricantId}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary disabled:bg-gray-100"
            >
              <option value="">
                {selectedFabricantId ? 'Sélectionner un cahier' : 'Sélectionnez d\'abord un fabricant'}
              </option>
              {cahiers?.map((cahier: CahierPortees) => (
                <option key={cahier.id} value={cahier.id}>
                  {cahier.nom} {cahier.version && `(v${cahier.version})`}
                </option>
              ))}
            </select>
            {selectedFabricantId && cahiers?.length === 0 && (
              <p className="mt-1 text-sm text-amber-600">
                Aucun cahier disponible pour ce fabricant
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Géométrie */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Géométrie</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700">
              Portée (m) *
            </label>
            <input
              type="number"
              step="0.01"
              min="1"
              max="15"
              value={parametres.geometrie?.portee || ''}
              onChange={(e) =>
                onChange({
                  ...parametres,
                  geometrie: {
                    ...parametres.geometrie,
                    portee: parseFloat(e.target.value)
                  }
                })
              }
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              placeholder="Ex: 5.50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Entraxe souhaité
            </label>
            <select
              value={parametres.geometrie?.entraxe_souhaite || ''}
              onChange={(e) =>
                onChange({
                  ...parametres,
                  geometrie: {
                    ...parametres.geometrie,
                    entraxe_souhaite: e.target.value ? parseInt(e.target.value) : undefined
                  }
                })
              }
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
            >
              <option value="">Tous (automatique)</option>
              {entraxesCourants.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">Laisser vide pour sélection automatique</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Hauteur hourdis
            </label>
            <select
              value={parametres.geometrie?.hauteur_hourdis || ''}
              onChange={(e) =>
                onChange({
                  ...parametres,
                  geometrie: {
                    ...parametres.geometrie,
                    hauteur_hourdis: e.target.value ? parseInt(e.target.value) : undefined
                  }
                })
              }
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
            >
              <option value="">Toutes (automatique)</option>
              {hauteursHourdis.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">Laisser vide pour sélection automatique</p>
          </div>
        </div>
      </div>

      {/* Charges */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Charges (kN/m²)</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Permanentes (G) *
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={parametres.charges?.permanentes || ''}
              onChange={(e) =>
                onChange({
                  ...parametres,
                  charges: {
                    ...parametres.charges,
                    permanentes: parseFloat(e.target.value)
                  }
                })
              }
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              placeholder="Ex: 2.5"
            />
            <p className="mt-1 text-xs text-gray-500">Hors poids propre du plancher</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Exploitation (Q) *
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={parametres.charges?.exploitation || ''}
              onChange={(e) =>
                onChange({
                  ...parametres,
                  charges: {
                    ...parametres.charges,
                    exploitation: parseFloat(e.target.value)
                  }
                })
              }
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              placeholder="Ex: 2.5"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Cloisons
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={parametres.charges?.cloisons || ''}
              onChange={(e) =>
                onChange({
                  ...parametres,
                  charges: {
                    ...parametres.charges,
                    cloisons: e.target.value ? parseFloat(e.target.value) : undefined
                  }
                })
              }
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
              placeholder="Ex: 0.5"
            />
          </div>
        </div>
      </div>

      {/* Options */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Options de calcul</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Mode d'optimisation
          </label>
          <select
            value={parametres.conditions?.optimisation || 'economique'}
            onChange={(e) =>
              onChange({
                ...parametres,
                conditions: {
                  ...parametres.conditions,
                  optimisation: e.target.value as 'economique' | 'minimal_hauteur' | 'maximal_reserve'
                }
              })
            }
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
          >
            {Object.entries(optimisationLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <p className="mt-2 text-xs text-gray-500">
            {parametres.conditions?.optimisation === 'economique' &&
              'Maximise l\'utilisation de la poutrelle (plus économique)'}
            {parametres.conditions?.optimisation === 'minimal_hauteur' &&
              'Minimise la hauteur totale du plancher'}
            {parametres.conditions?.optimisation === 'maximal_reserve' &&
              'Maximise la réserve de portée (plus de sécurité)'}
          </p>
        </div>
      </div>
    </div>
  )
}
