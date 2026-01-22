// Norme types
export type NormeType = 'EC2' | 'ACI318' | 'BAEL91' | 'BS8110' | 'CSA_A23'

export interface NormeInfo {
  code: string
  display_name: string
  region: string
  implemented: boolean
  classes_beton?: string[]
  classes_acier?: string[]
  coefficients?: {
    gamma_c: number
    gamma_s: number
    gamma_g: number
    gamma_q: number
  }
}

export const NORME_LABELS: Record<NormeType, string> = {
  'EC2': 'Eurocode 2 (Europe)',
  'ACI318': 'ACI 318 (USA)',
  'BAEL91': 'BAEL 91 (France)',
  'BS8110': 'BS 8110 (UK)',
  'CSA_A23': 'CSA A23.3 (Canada)',
}

export const NORME_FLAGS: Record<NormeType, string> = {
  'EC2': '🇪🇺',
  'ACI318': '🇺🇸',
  'BAEL91': '🇫🇷',
  'BS8110': '🇬🇧',
  'CSA_A23': '🇨🇦',
}

// User & Auth types
export interface User {
  id: string
  tenant_id: string
  email: string
  first_name?: string
  last_name?: string
  phone?: string
  role: UserRole
  is_active: boolean
  is_superuser: boolean
  created_at: string
  last_login?: string
}

export type UserRole = 'admin' | 'engineer' | 'technician' | 'viewer'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
  company_name: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

// Projet types
export interface Projet {
  id: string
  tenant_id: string
  reference: string
  name: string
  description?: string
  client_name?: string
  client_contact?: string
  client_phone?: string
  client_email?: string
  address?: string
  city?: string
  postal_code?: string
  country: string
  status: ProjetStatus
  norme: NormeType
  date_start?: string
  date_delivery?: string
  created_at: string
  updated_at: string
}

export type ProjetStatus = 'draft' | 'in_study' | 'validated' | 'in_production' | 'delivered' | 'archived'

export interface ProjetCreate {
  reference: string
  name: string
  description?: string
  client_name?: string
  client_contact?: string
  client_phone?: string
  client_email?: string
  address?: string
  city?: string
  postal_code?: string
  country?: string
  norme?: NormeType
  date_start?: string
  date_delivery?: string
}

// Calcul types
export interface Calcul {
  id: string
  projet_id: string
  plan_id?: string
  name: string
  type_produit: TypeProduit
  norme: NormeType
  parametres: CalculParametres
  resultats: CalculResultats
  status: CalculStatus
  error_message?: string
  created_at: string
  updated_at: string
  computed_at?: string
}

export type TypeProduit = 'poutrelle' | 'predalle' | 'dalle_alveolaire' | 'poutre' | 'dalle_pleine' | 'plancher_poutrelles_hourdis'

export type CalculStatus = 'draft' | 'pending' | 'computing' | 'completed' | 'error' | 'validated'

export interface CalculParametres {
  cahier_portees_id?: string  // Pour plancher poutrelles-hourdis
  geometrie: {
    portee?: number
    largeur?: number
    hauteur?: number
    enrobage?: number
    entraxe_souhaite?: number  // Pour plancher poutrelles-hourdis
    hauteur_hourdis?: number   // Pour plancher poutrelles-hourdis
    fabricant_id?: string      // Pour plancher poutrelles-hourdis
    type_poutrelle?: 'precontrainte' | 'treillis'  // Type de poutrelle
  }
  charges: {
    permanentes?: number
    exploitation?: number
    cloisons?: number
  }
  materiaux: {
    classe_beton?: string
    classe_acier?: string
    type_acier_precontrainte?: string
  }
  conditions: {
    classe_exposition?: string
    duree_vie?: number
    classe_feu?: string
    optimisation?: 'economique' | 'minimal_hauteur' | 'maximal_reserve'  // Pour plancher
  }
}

export interface CalculResultats {
  verification_ok?: boolean  // Pour plancher poutrelles-hourdis
  message?: string           // Pour plancher poutrelles-hourdis
  nombre_candidates?: number // Pour plancher poutrelles-hourdis
  flexion?: {
    moment_elu_kNm?: number
    moment_els_kNm?: number
    as_final_cm2?: number
    verification_ok?: boolean
    message?: string
  }
  fleche?: {
    fleche_totale_mm?: number
    fleche_limite_mm?: number
    verification_ok?: boolean
    message?: string
  }
  effort_tranchant?: {
    effort_tranchant_kN?: number
    as_transversal_cm2_m?: number
    verification_ok?: boolean
    message?: string
  }
  ferraillage?: {
    armatures_inferieures?: { designation?: string }
    armatures_superieures?: { designation?: string }
    armatures_transversales?: { designation?: string }
    resume?: string
  }
  summary?: {
    verification_globale?: string
    norme_utilisee?: string
    message?: string
  }
  // Pour plancher poutrelles-hourdis
  poutrelle?: {
    reference?: string
    hauteur_hourdis_cm?: number
    entraxe_cm?: number
    epaisseur_table_cm?: number
    hauteur_totale_cm?: number
  }
  verification?: {
    portee_demandee_m?: number
    portee_limite_m?: number
    charge_utilisee_kg_m2?: number
    ratio_utilisation_pct?: number
    reserve_portee_m?: number
  }
  alternatives?: Array<{
    reference: string
    hauteur_hourdis_cm: number
    entraxe_cm: number
    portee_limite_m: number
    ratio_utilisation_pct: number
    hauteur_totale_cm: number
  }>
  charges?: {
    permanentes_kN_m2?: number
    exploitation_kN_m2?: number
    totale_kg_m2?: number
    calcul_kg_m2?: number
  }
}

export interface CalculCreate {
  projet_id: string
  plan_id?: string
  name: string
  type_produit: TypeProduit
  norme?: NormeType
  parametres?: CalculParametres
}

// Fabricant types
export interface Fabricant {
  id: string
  tenant_id: string
  nom: string
  code: string
  description?: string
  adresse?: string
  telephone?: string
  email?: string
  site_web?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface FabricantCreate {
  nom: string
  code: string
  description?: string
  adresse?: string
  telephone?: string
  email?: string
  site_web?: string
}

// Cahier de portées types
export type TypePoutrelle = 'precontrainte' | 'treillis'

export interface CahierPortees {
  id: string
  fabricant_id: string
  type_poutrelle: TypePoutrelle
  nom: string
  version?: string
  fichier_original?: string
  date_validite?: string
  notes?: string
  created_at: string
  updated_at: string
  imported_at?: string
}

export interface LigneCahierPortees {
  id: string
  cahier_id: string
  reference_poutrelle: string
  hauteur_hourdis_cm: number
  entraxe_cm: number
  epaisseur_table_cm: number
  portees_limites: Record<string, number>
  hauteur_totale_cm?: number
  poids_lineique_kg_m?: number
  notes?: string
  created_at: string
}

export interface ImportCahierResult {
  cahier_id: string
  lignes_importees: number
  lignes_ignorees: number
  avertissements: string[]
}

export interface CahierStats {
  cahier_id: string
  nom: string
  total_lignes: number
  nb_poutrelles_uniques: number
  hauteurs_hourdis_disponibles: number[]
  entraxes_disponibles: number[]
}
