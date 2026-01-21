import axios from 'axios'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
  Projet,
  ProjetCreate,
  Calcul,
  CalculCreate,
} from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post('/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<LoginResponse> => {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  getMe: async (): Promise<User> => {
    const response = await api.get('/auth/me')
    return response.data
  },

  changePassword: async (data: { current_password: string; new_password: string }) => {
    const response = await api.post('/auth/change-password', data)
    return response.data
  },
}

// Projets API
export const projetsApi = {
  list: async (params?: { status?: string; search?: string }): Promise<Projet[]> => {
    const response = await api.get('/projets', { params })
    return response.data
  },

  get: async (id: string): Promise<Projet> => {
    const response = await api.get(`/projets/${id}`)
    return response.data
  },

  create: async (data: ProjetCreate): Promise<Projet> => {
    const response = await api.post('/projets', data)
    return response.data
  },

  update: async (id: string, data: Partial<ProjetCreate>): Promise<Projet> => {
    const response = await api.put(`/projets/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/projets/${id}`)
  },

  getStats: async (id: string) => {
    const response = await api.get(`/projets/${id}/stats`)
    return response.data
  },
}

// Calculs API
export const calculsApi = {
  list: async (params?: { projet_id?: string; status?: string }): Promise<Calcul[]> => {
    const response = await api.get('/calculs', { params })
    return response.data
  },

  get: async (id: string): Promise<Calcul> => {
    const response = await api.get(`/calculs/${id}`)
    return response.data
  },

  create: async (data: CalculCreate): Promise<Calcul> => {
    const response = await api.post('/calculs', data)
    return response.data
  },

  update: async (id: string, data: Partial<CalculCreate>): Promise<Calcul> => {
    const response = await api.put(`/calculs/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/calculs/${id}`)
  },

  run: async (id: string, force = false): Promise<Calcul> => {
    const response = await api.post(`/calculs/${id}/run`, { force })
    return response.data
  },

  getResults: async (id: string) => {
    const response = await api.get(`/calculs/${id}/results`)
    return response.data
  },

  importPdf: async (file: File, useOcr = false): Promise<PdfExtractionResult> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post(`/calculs/import-pdf?use_ocr=${useOcr}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

// PDF Extraction types
export interface ExtractedValue {
  value: number | string
  confidence: number
  source: string
}

export interface PdfExtractionResult {
  success: boolean
  filename: string
  extraction_confidence: number
  data: {
    portees: (ExtractedValue | null)[]
    poutrelles: (ExtractedValue | null)[]
    charges_permanentes: (ExtractedValue | null)[]
    charges_exploitation: (ExtractedValue | null)[]
    entre_axes: (ExtractedValue | null)[]
    epaisseur_dalle: ExtractedValue | null
    type_hourdis: ExtractedValue | null
  }
  raw_text_preview: string | null
  tables_found: number
  message: string
}

// Plans API
export const plansApi = {
  list: async (projetId: string) => {
    const response = await api.get(`/plans/projet/${projetId}`)
    return response.data
  },

  get: async (id: string) => {
    const response = await api.get(`/plans/${id}`)
    return response.data
  },

  getGeometry: async (id: string) => {
    const response = await api.get(`/plans/${id}/geometry`)
    return response.data
  },

  uploadDxf: async (projetId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post(`/plans/upload-dxf/${projetId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/plans/${id}`)
  },
}

// Exports API
export const exportsApi = {
  downloadCalculPdf: async (calculId: string): Promise<Blob> => {
    const response = await api.get(`/exports/calcul/${calculId}/pdf`, {
      responseType: 'blob',
    })
    return response.data
  },

  downloadCalculExcel: async (calculId: string): Promise<Blob> => {
    const response = await api.get(`/exports/calcul/${calculId}/excel`, {
      responseType: 'blob',
    })
    return response.data
  },

  downloadNomenclature: async (projetId: string): Promise<Blob> => {
    const response = await api.get(`/exports/projet/${projetId}/nomenclature`, {
      responseType: 'blob',
    })
    return response.data
  },

  downloadQuantitatif: async (projetId: string): Promise<Blob> => {
    const response = await api.get(`/exports/projet/${projetId}/quantitatif`, {
      responseType: 'blob',
    })
    return response.data
  },

  downloadPlanDePose: async (calculId: string): Promise<Blob> => {
    const response = await api.get(`/exports/calcul/${calculId}/plan-de-pose`, {
      responseType: 'blob',
    })
    return response.data
  },
}

// Utility function to trigger download
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export default api
