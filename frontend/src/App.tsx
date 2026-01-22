import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

// Layout
import MainLayout from '@/components/layout/MainLayout'

// Pages
import LoginPage from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'
import DashboardPage from '@/pages/dashboard/DashboardPage'
import ProjetsPage from '@/pages/projets/ProjetsPage'
import ProjetDetailPage from '@/pages/projets/ProjetDetailPage'
import CalculsPage from '@/pages/calculs/CalculsPage'
import CalculEditorPage from '@/pages/calculs/CalculEditorPage'
import ReglagesPage from '@/pages/reglages/ReglagesPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="projets" element={<ProjetsPage />} />
        <Route path="projets/:id" element={<ProjetDetailPage />} />
        <Route path="calculs" element={<CalculsPage />} />
        <Route path="calculs/:id" element={<CalculEditorPage />} />
        <Route path="reglages" element={<ReglagesPage />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
