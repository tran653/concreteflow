/**
 * Service API pour les fabricants et cahiers de portées.
 */
import api from './api'
import type {
  Fabricant,
  FabricantCreate,
  CahierPortees,
  LigneCahierPortees,
  ImportCahierResult,
  CahierStats
} from '@/types'

export const fabricantsApi = {
  // ==================== FABRICANTS ====================

  /**
   * Liste des fabricants du tenant.
   */
  list: async (activeOnly = true): Promise<Fabricant[]> => {
    const response = await api.get('/fabricants', {
      params: { active_only: activeOnly }
    })
    return response.data
  },

  /**
   * Récupère un fabricant par son ID.
   */
  get: async (id: string): Promise<Fabricant> => {
    const response = await api.get(`/fabricants/${id}`)
    return response.data
  },

  /**
   * Crée un nouveau fabricant.
   */
  create: async (data: FabricantCreate): Promise<Fabricant> => {
    const response = await api.post('/fabricants', data)
    return response.data
  },

  /**
   * Met à jour un fabricant.
   */
  update: async (id: string, data: Partial<FabricantCreate>): Promise<Fabricant> => {
    const response = await api.put(`/fabricants/${id}`, data)
    return response.data
  },

  /**
   * Supprime (désactive) un fabricant.
   */
  delete: async (id: string): Promise<void> => {
    await api.delete(`/fabricants/${id}`)
  },

  // ==================== CAHIERS DE PORTEES ====================

  /**
   * Liste des cahiers de portées d'un fabricant.
   */
  listCahiers: async (fabricantId: string): Promise<CahierPortees[]> => {
    const response = await api.get(`/fabricants/${fabricantId}/cahiers`)
    return response.data
  },

  /**
   * Récupère un cahier de portées par son ID.
   */
  getCahier: async (cahierId: string): Promise<CahierPortees> => {
    const response = await api.get(`/fabricants/cahiers/${cahierId}`)
    return response.data
  },

  /**
   * Importe un cahier de portées depuis un fichier Excel.
   */
  importCahier: async (
    fabricantId: string,
    file: File,
    nom?: string,
    version?: string
  ): Promise<ImportCahierResult> => {
    const formData = new FormData()
    formData.append('file', file)

    const params = new URLSearchParams()
    if (nom) params.append('nom', nom)
    if (version) params.append('version', version)

    const url = `/fabricants/${fabricantId}/cahiers/import${params.toString() ? '?' + params.toString() : ''}`

    const response = await api.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  /**
   * Supprime un cahier de portées.
   */
  deleteCahier: async (cahierId: string): Promise<void> => {
    await api.delete(`/fabricants/cahiers/${cahierId}`)
  },

  /**
   * Récupère les statistiques d'un cahier de portées.
   */
  getCahierStats: async (cahierId: string): Promise<CahierStats> => {
    const response = await api.get(`/fabricants/cahiers/${cahierId}/stats`)
    return response.data
  },

  // ==================== LIGNES CAHIER ====================

  /**
   * Liste les lignes d'un cahier de portées.
   */
  getLignesCahier: async (
    cahierId: string,
    filters?: { hauteur_hourdis?: number; entraxe?: number }
  ): Promise<LigneCahierPortees[]> => {
    const response = await api.get(`/fabricants/cahiers/${cahierId}/lignes`, {
      params: filters
    })
    return response.data
  }
}

export default fabricantsApi
