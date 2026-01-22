import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { calculsApi, projetsApi } from '@/services/api'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Plus,
  Calculator,
  X,
  Loader2,
  Search,
} from 'lucide-react'
import { cn, statusLabels, statusColors, formatDate, typeProduitLabels } from '@/lib/utils'
import type { CalculCreate, TypeProduit, NormeType } from '@/types'
import { NormeSelector, NormeBadge } from '@/components/common'

const calculSchema = z.object({
  projet_id: z.string().min(1, 'Projet requis'),
  name: z.string().min(1, 'Nom du niveau requis'),
  type_produit: z.enum(['plancher_poutrelles_hourdis']),
  norme: z.enum(['EC2', 'ACI318', 'BAEL91', 'BS8110', 'CSA_A23']).default('EC2'),
})

const typesProduit: { value: string; label: string; description: string }[] = [
  { value: 'plancher_poutrelles_hourdis', label: 'Plancher poutrelles-hourdis', description: 'Poutrelles précontraintes ou treillis' },
]

export default function CalculsPage() {
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const projetIdFromUrl = searchParams.get('projet_id')
  const projetNameFromUrl = searchParams.get('projet_name')

  const [search, setSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(!!projetIdFromUrl)

  const { data: calculs = [], isLoading } = useQuery({
    queryKey: ['calculs'],
    queryFn: () => calculsApi.list(),
  })

  const { data: projets = [] } = useQuery({
    queryKey: ['projets'],
    queryFn: () => projetsApi.list(),
  })

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<CalculCreate>({
    resolver: zodResolver(calculSchema),
    defaultValues: {
      projet_id: projetIdFromUrl || '',
      norme: 'EC2',
    },
  })

  const createMutation = useMutation({
    mutationFn: calculsApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['calculs'] })
      setShowCreateModal(false)
      reset()
      // Navigate to the new calculation
      window.location.href = `/calculs/${data.id}`
    },
  })

  const onSubmit = (data: CalculCreate) => {
    createMutation.mutate(data)
  }

  const filteredCalculs = calculs.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      typeProduitLabels[c.type_produit].toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Calculs</h1>
          <p className="text-gray-500">Vos calculs de structure béton</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
        >
          <Plus className="h-5 w-5" />
          Nouveau calcul
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher un calcul..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
        />
      </div>

      {/* Calculations list */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : filteredCalculs.length === 0 ? (
        <div className="text-center py-12">
          <Calculator className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Aucun calcul</h3>
          <p className="text-gray-500">
            Commencez par créer votre premier calcul
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nom
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Norme
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredCalculs.map((calcul) => (
                <tr
                  key={calcul.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => window.location.href = `/calculs/${calcul.id}`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{calcul.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {typeProduitLabels[calcul.type_produit]}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <NormeBadge norme={calcul.norme} size="sm" />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={cn(
                        'px-2 py-1 text-xs rounded-full',
                        statusColors[calcul.status]
                      )}
                    >
                      {statusLabels[calcul.status]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(calcul.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowCreateModal(false)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">
                {projetIdFromUrl ? 'Ajouter un niveau' : 'Nouveau calcul'}
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Projet *
                </label>
                {projetIdFromUrl && projetNameFromUrl ? (
                  <>
                    <input type="hidden" {...register('projet_id')} />
                    <div className="mt-1 px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-gray-700">
                      {decodeURIComponent(projetNameFromUrl)}
                    </div>
                  </>
                ) : (
                  <select
                    {...register('projet_id')}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  >
                    <option value="">Sélectionner un projet</option>
                    {projets.map((projet) => (
                      <option key={projet.id} value={projet.id}>
                        {projet.reference} - {projet.name}
                      </option>
                    ))}
                  </select>
                )}
                {errors.projet_id && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.projet_id.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Nom du niveau *
                </label>
                <input
                  {...register('name')}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="RDC, Étage 1, Étage 2..."
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.name.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Type de produit *
                </label>
                <select
                  {...register('type_produit')}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                >
                  {typesProduit.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <Controller
                  name="norme"
                  control={control}
                  render={({ field }) => (
                    <NormeSelector
                      value={field.value as NormeType}
                      onChange={field.onChange}
                      label="Norme de calcul"
                      description="Norme utilisée pour ce calcul"
                    />
                  )}
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
                >
                  {createMutation.isPending ? (
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
    </div>
  )
}
