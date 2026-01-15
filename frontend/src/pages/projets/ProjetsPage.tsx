import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { projetsApi } from '@/services/api'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Plus,
  Search,
  FolderKanban,
  MapPin,
  Calendar,
  X,
  Loader2,
} from 'lucide-react'
import { cn, statusLabels, statusColors, formatDate } from '@/lib/utils'
import type { ProjetCreate } from '@/types'

const projetSchema = z.object({
  reference: z.string().min(1, 'Référence requise'),
  name: z.string().min(1, 'Nom requis'),
  description: z.string().optional(),
  client_name: z.string().optional(),
  city: z.string().optional(),
})

export default function ProjetsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)

  const { data: projets = [], isLoading } = useQuery({
    queryKey: ['projets', search],
    queryFn: () => projetsApi.list({ search: search || undefined }),
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjetCreate>({
    resolver: zodResolver(projetSchema),
  })

  const createMutation = useMutation({
    mutationFn: projetsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projets'] })
      setShowCreateModal(false)
      reset()
    },
  })

  const onSubmit = (data: ProjetCreate) => {
    createMutation.mutate(data)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projets</h1>
          <p className="text-gray-500">Gérez vos projets de construction</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
        >
          <Plus className="h-5 w-5" />
          Nouveau projet
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher un projet..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
        />
      </div>

      {/* Projects grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : projets.length === 0 ? (
        <div className="text-center py-12">
          <FolderKanban className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Aucun projet</h3>
          <p className="text-gray-500">
            Commencez par créer votre premier projet
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projets.map((projet) => (
            <Link
              key={projet.id}
              to={`/projets/${projet.id}`}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-500">{projet.reference}</p>
                  <h3 className="font-semibold text-gray-900">{projet.name}</h3>
                </div>
                <span
                  className={cn(
                    'px-2 py-1 text-xs rounded-full',
                    statusColors[projet.status]
                  )}
                >
                  {statusLabels[projet.status]}
                </span>
              </div>

              {projet.client_name && (
                <p className="text-sm text-gray-600 mb-2">
                  Client: {projet.client_name}
                </p>
              )}

              <div className="flex items-center gap-4 text-sm text-gray-500">
                {projet.city && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    {projet.city}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {formatDate(projet.created_at)}
                </span>
              </div>
            </Link>
          ))}
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
              <h2 className="text-lg font-semibold">Nouveau projet</h2>
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
                  Référence *
                </label>
                <input
                  {...register('reference')}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="PRJ-001"
                />
                {errors.reference && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.reference.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Nom du projet *
                </label>
                <input
                  {...register('name')}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="Résidence Les Jardins"
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.name.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Client
                </label>
                <input
                  {...register('client_name')}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="Nom du client"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Ville
                </label>
                <input
                  {...register('city')}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="Paris"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  {...register('description')}
                  rows={3}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
                  placeholder="Description du projet..."
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
