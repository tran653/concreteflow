import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { projetsApi, calculsApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import {
  FolderKanban,
  Calculator,
  CheckCircle,
  Clock,
  AlertCircle,
  Plus,
  ArrowRight,
} from 'lucide-react'
import { cn, statusLabels, statusColors, formatDate } from '@/lib/utils'

export default function DashboardPage() {
  const { user } = useAuthStore()

  const { data: projets = [] } = useQuery({
    queryKey: ['projets'],
    queryFn: () => projetsApi.list(),
  })

  const { data: calculs = [] } = useQuery({
    queryKey: ['calculs'],
    queryFn: () => calculsApi.list(),
  })

  const stats = {
    projets_total: projets.length,
    projets_en_cours: projets.filter((p) => p.status === 'in_study').length,
    calculs_total: calculs.length,
    calculs_ok: calculs.filter((c) => c.status === 'completed').length,
    calculs_error: calculs.filter((c) => c.status === 'error').length,
  }

  const recentProjets = projets.slice(0, 5)
  const recentCalculs = calculs.slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Bonjour, {user?.first_name}
        </h1>
        <p className="text-gray-500">
          Bienvenue sur ConcreteFlow - votre outil de calcul béton
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Projets</p>
              <p className="text-2xl font-bold">{stats.projets_total}</p>
            </div>
            <FolderKanban className="h-10 w-10 text-blue-500" />
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {stats.projets_en_cours} en cours
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Calculs</p>
              <p className="text-2xl font-bold">{stats.calculs_total}</p>
            </div>
            <Calculator className="h-10 w-10 text-purple-500" />
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {stats.calculs_ok} validés
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Conformes</p>
              <p className="text-2xl font-bold text-green-600">{stats.calculs_ok}</p>
            </div>
            <CheckCircle className="h-10 w-10 text-green-500" />
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Vérifications OK
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Erreurs</p>
              <p className="text-2xl font-bold text-red-600">{stats.calculs_error}</p>
            </div>
            <AlertCircle className="h-10 w-10 text-red-500" />
          </div>
          <p className="text-sm text-gray-500 mt-2">
            À vérifier
          </p>
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          to="/projets"
          className="bg-primary text-white rounded-lg shadow p-6 hover:bg-primary/90 transition-colors"
        >
          <div className="flex items-center gap-4">
            <Plus className="h-8 w-8" />
            <div>
              <h3 className="font-semibold">Nouveau projet</h3>
              <p className="text-sm text-white/80">
                Créer un nouveau projet de construction
              </p>
            </div>
          </div>
        </Link>

        <Link
          to="/calculs"
          className="bg-white border-2 border-primary text-primary rounded-lg shadow p-6 hover:bg-primary/5 transition-colors"
        >
          <div className="flex items-center gap-4">
            <Calculator className="h-8 w-8" />
            <div>
              <h3 className="font-semibold">Nouveau calcul</h3>
              <p className="text-sm text-gray-500">
                Lancer un calcul de structure béton
              </p>
            </div>
          </div>
        </Link>
      </div>

      {/* Recent items */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent projects */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Projets récents</h2>
            <Link
              to="/projets"
              className="text-sm text-primary hover:underline flex items-center gap-1"
            >
              Voir tout <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="divide-y">
            {recentProjets.length === 0 ? (
              <p className="p-4 text-gray-500 text-center">Aucun projet</p>
            ) : (
              recentProjets.map((projet) => (
                <Link
                  key={projet.id}
                  to={`/projets/${projet.id}`}
                  className="p-4 hover:bg-gray-50 flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-gray-900">{projet.name}</p>
                    <p className="text-sm text-gray-500">{projet.reference}</p>
                  </div>
                  <span
                    className={cn(
                      'px-2 py-1 text-xs rounded-full',
                      statusColors[projet.status]
                    )}
                  >
                    {statusLabels[projet.status]}
                  </span>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Recent calculations */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Calculs récents</h2>
            <Link
              to="/calculs"
              className="text-sm text-primary hover:underline flex items-center gap-1"
            >
              Voir tout <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="divide-y">
            {recentCalculs.length === 0 ? (
              <p className="p-4 text-gray-500 text-center">Aucun calcul</p>
            ) : (
              recentCalculs.map((calcul) => (
                <Link
                  key={calcul.id}
                  to={`/calculs/${calcul.id}`}
                  className="p-4 hover:bg-gray-50 flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-gray-900">{calcul.name}</p>
                    <p className="text-sm text-gray-500">
                      {formatDate(calcul.created_at)}
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
