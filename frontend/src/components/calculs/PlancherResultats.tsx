/**
 * Affichage des résultats du calcul plancher poutrelles-hourdis.
 */
import { CheckCircle, XCircle, AlertCircle, Loader2, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CalculResultats, CalculStatus } from '@/types'

interface Props {
  resultats: CalculResultats
  status: CalculStatus
  errorMessage?: string
}

export default function PlancherResultats({ resultats, status, errorMessage }: Props) {
  const isComputed = status === 'completed'
  const verificationOk = resultats.verification?.ratio_utilisation_pct !== undefined
    && resultats.verification.ratio_utilisation_pct <= 100

  // Not computed yet
  if (status === 'draft' || status === 'pending') {
    return (
      <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
        <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">
          Aucun résultat
        </h3>
        <p className="text-gray-500 mt-2">
          Configurez les paramètres et cliquez sur "Calculer"
        </p>
      </div>
    )
  }

  // Computing
  if (status === 'computing') {
    return (
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-12 text-center">
        <Loader2 className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-spin" />
        <h3 className="text-lg font-medium text-gray-900">
          Sélection en cours...
        </h3>
        <p className="text-gray-500 mt-2">
          Recherche de la poutrelle optimale
        </p>
      </div>
    )
  }

  // Error
  if (status === 'error') {
    return (
      <div className="bg-red-50 rounded-lg border border-red-200 p-6">
        <div className="flex items-center gap-3">
          <XCircle className="h-8 w-8 text-red-600 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-red-800">Erreur de calcul</h3>
            <p className="text-sm text-red-600">{errorMessage}</p>
          </div>
        </div>
      </div>
    )
  }

  // Computed results
  return (
    <div className="space-y-6">
      {/* Summary card */}
      <div
        className={cn(
          'rounded-lg shadow p-6',
          verificationOk
            ? 'bg-green-50 border border-green-200'
            : 'bg-red-50 border border-red-200'
        )}
      >
        <div className="flex items-start gap-4">
          {verificationOk ? (
            <CheckCircle className="h-10 w-10 text-green-600 flex-shrink-0" />
          ) : (
            <XCircle className="h-10 w-10 text-red-600 flex-shrink-0" />
          )}
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900">
              {verificationOk ? 'Vérification OK' : 'Portée insuffisante'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {resultats.summary?.message}
            </p>
          </div>
        </div>
      </div>

      {/* Selected poutrelle */}
      {resultats.poutrelle && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Poutrelle sélectionnée</h2>
          <div className="bg-blue-50 rounded-lg p-4 mb-4">
            <p className="text-2xl font-bold text-blue-700">
              {resultats.poutrelle.reference}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Hauteur hourdis:</span>
              <span className="font-medium">{resultats.poutrelle.hauteur_hourdis_cm} cm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Entraxe:</span>
              <span className="font-medium">{resultats.poutrelle.entraxe_cm} cm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Épaisseur table:</span>
              <span className="font-medium">{resultats.poutrelle.epaisseur_table_cm} cm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Hauteur totale:</span>
              <span className="font-medium font-bold">{resultats.poutrelle.hauteur_totale_cm} cm</span>
            </div>
          </div>
        </div>
      )}

      {/* Verification details */}
      {resultats.verification && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Vérification</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-500">Portée demandée:</span>
              <span className="font-medium">{resultats.verification.portee_demandee_m?.toFixed(2)} m</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500">Portée limite:</span>
              <span className="font-medium">{resultats.verification.portee_limite_m?.toFixed(2)} m</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500">Charge de calcul:</span>
              <span className="font-medium">{resultats.verification.charge_utilisee_kg_m2} kg/m²</span>
            </div>

            {/* Progress bar for utilization ratio */}
            <div className="pt-2">
              <div className="flex justify-between items-center mb-1">
                <span className="text-gray-500">Taux d'utilisation:</span>
                <span className={cn(
                  'font-bold',
                  (resultats.verification.ratio_utilisation_pct || 0) <= 85 ? 'text-green-600' :
                  (resultats.verification.ratio_utilisation_pct || 0) <= 100 ? 'text-amber-600' : 'text-red-600'
                )}>
                  {resultats.verification.ratio_utilisation_pct?.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={cn(
                    'h-3 rounded-full transition-all',
                    (resultats.verification.ratio_utilisation_pct || 0) <= 85 ? 'bg-green-500' :
                    (resultats.verification.ratio_utilisation_pct || 0) <= 100 ? 'bg-amber-500' : 'bg-red-500'
                  )}
                  style={{ width: `${Math.min(resultats.verification.ratio_utilisation_pct || 0, 100)}%` }}
                />
              </div>
            </div>

            {resultats.verification.reserve_portee_m !== undefined && (
              <div className="flex justify-between items-center pt-2">
                <span className="text-gray-500">Réserve de portée:</span>
                <span className={cn(
                  'font-medium',
                  (resultats.verification.reserve_portee_m || 0) > 0 ? 'text-green-600' : 'text-red-600'
                )}>
                  {resultats.verification.reserve_portee_m > 0 ? '+' : ''}{resultats.verification.reserve_portee_m?.toFixed(2)} m
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Charges recap */}
      {resultats.charges && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Charges</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Permanentes:</span>
              <span className="font-medium">{resultats.charges.permanentes_kN_m2?.toFixed(2)} kN/m²</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Exploitation:</span>
              <span className="font-medium">{resultats.charges.exploitation_kN_m2?.toFixed(2)} kN/m²</span>
            </div>
            <div className="border-t pt-2 mt-2">
              <div className="flex justify-between">
                <span className="text-gray-700 font-medium">Total G+Q:</span>
                <span className="font-bold">{resultats.charges.totale_kg_m2} kg/m²</span>
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Charge cahier utilisée:</span>
                <span>{resultats.charges.calcul_kg_m2} kg/m²</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alternatives */}
      {resultats.alternatives && resultats.alternatives.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="font-semibold text-gray-900">Alternatives</h2>
            <Info className="h-4 w-4 text-gray-400" />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="pb-2 font-medium text-gray-500">Référence</th>
                  <th className="pb-2 font-medium text-gray-500 text-center">Hourdis</th>
                  <th className="pb-2 font-medium text-gray-500 text-center">Entraxe</th>
                  <th className="pb-2 font-medium text-gray-500 text-center">H. totale</th>
                  <th className="pb-2 font-medium text-gray-500 text-center">Portée max</th>
                  <th className="pb-2 font-medium text-gray-500 text-center">Utilisation</th>
                </tr>
              </thead>
              <tbody>
                {resultats.alternatives.map((alt, idx) => (
                  <tr key={idx} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-2 font-medium">{alt.reference}</td>
                    <td className="py-2 text-center">{alt.hauteur_hourdis_cm} cm</td>
                    <td className="py-2 text-center">{alt.entraxe_cm} cm</td>
                    <td className="py-2 text-center">{alt.hauteur_totale_cm} cm</td>
                    <td className="py-2 text-center">{alt.portee_limite_m?.toFixed(2)} m</td>
                    <td className="py-2 text-center">
                      <span className={cn(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        alt.ratio_utilisation_pct <= 85 ? 'bg-green-100 text-green-700' :
                        alt.ratio_utilisation_pct <= 100 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
                      )}>
                        {alt.ratio_utilisation_pct?.toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
