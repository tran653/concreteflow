# ConcreteFlow

Application web de calculs de structures béton pour les professionnels du BTP. ConcreteFlow permet de gérer des projets de construction, réaliser des calculs structurels conformes aux Eurocodes, et générer des rapports techniques.

## Fonctionnalités

### Implémentées

- **Authentification**
  - Inscription / Connexion utilisateur
  - Gestion des sessions JWT
  - Routes protégées

- **Gestion de projets**
  - Création et liste des projets
  - Détail d'un projet
  - Statuts de projet (brouillon, en cours, terminé)

- **Calculs structurels**
  - Éditeur de calculs
  - Plancher poutrelles-hourdis
  - Calculs de flexion
  - Calculs de flèche
  - Effort tranchant
  - Ferraillage
  - Conformité Eurocodes

- **Gestion des plans**
  - Import de fichiers DXF
  - Visualisation canvas (Konva)
  - Export des données

- **Administration**
  - Gestion des fabricants
  - Import de cahiers de portées

### En développement

- Dashboard avec statistiques
- Export PDF/Excel des calculs
- Multi-tenant complet
- Gestion des éléments de structure

## Stack technique

### Backend
- **Framework** : FastAPI 0.109
- **Base de données** : PostgreSQL 15 + SQLAlchemy 2.0
- **Cache** : Redis 7
- **Migrations** : Alembic
- **Calculs scientifiques** : NumPy, SciPy
- **Fichiers** : ezdxf (DXF), ReportLab (PDF), openpyxl (Excel)

### Frontend
- **Framework** : React 18 + TypeScript
- **Build** : Vite 5
- **UI** : Tailwind CSS + Radix UI
- **State** : Zustand
- **Data fetching** : TanStack Query
- **Canvas** : Konva / React-Konva
- **Formulaires** : React Hook Form + Zod

## Installation

### Prérequis
- Docker & Docker Compose
- Node.js 20+ (développement local)
- Python 3.11+ (développement local)

### Démarrage avec Docker

```bash
# Cloner le projet
git clone <repo-url>
cd concreteflow

# Copier la configuration
cp .env.example .env

# Lancer les services
docker-compose up -d

# L'application est accessible sur :
# - Frontend : http://localhost:3000
# - Backend API : http://localhost:8000
# - API Docs : http://localhost:8000/docs
```

### Développement local

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Structure du projet

```
concreteflow/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints API
│   │   ├── core/            # Config, DB, sécurité
│   │   ├── models/          # Modèles SQLAlchemy
│   │   ├── schemas/         # Schémas Pydantic
│   │   └── services/
│   │       ├── calculs/     # Moteurs de calcul
│   │       └── import/      # Import de données
│   ├── alembic/             # Migrations DB
│   ├── tests/
│   └── main.py
├── frontend/
│   └── src/
│       ├── components/      # Composants React
│       ├── pages/           # Pages de l'application
│       ├── services/        # Appels API
│       ├── stores/          # État Zustand
│       └── types/           # Types TypeScript
├── docker-compose.yml
└── .env.example
```

## Modèles de données

- **Tenant** : Multi-tenant (entreprises)
- **User** : Utilisateurs avec rôles
- **Projet** : Projets de construction
- **Plan** : Plans DXF associés aux projets
- **Calcul** : Calculs structurels
- **Element** : Éléments de structure
- **Fabricant** : Fabricants de matériaux
- **CahierPortees** : Données techniques des produits

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/login` | Connexion |
| `POST /api/v1/auth/register` | Inscription |
| `GET /api/v1/projets` | Liste des projets |
| `POST /api/v1/projets` | Créer un projet |
| `GET /api/v1/calculs` | Liste des calculs |
| `POST /api/v1/calculs` | Créer un calcul |
| `GET /api/v1/fabricants` | Liste des fabricants |
| `POST /api/v1/plans/upload` | Upload DXF |

## Configuration

Variables d'environnement (`.env`) :

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé secrète JWT |
| `DATABASE_URL` | URL PostgreSQL async |
| `REDIS_URL` | URL Redis |
| `DEBUG` | Mode debug |
| `CORS_ORIGINS` | Origines CORS autorisées |

## Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run lint
```

## Licence

Projet propriétaire - Tous droits réservés

---

**Version** : 0.1.0 (Développement)
