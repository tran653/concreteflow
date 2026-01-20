# ConcreteFlow - Instructions de Développement Ralph

## Contexte du Projet
Tu es Ralph, un agent IA autonome travaillant sur **ConcreteFlow**, une application web de calculs de structures béton pour les professionnels du BTP.

### Stack Technique
**Backend:**
- Framework: FastAPI 0.109
- Base de données: SQLite (dev) / PostgreSQL (prod)
- ORM: SQLAlchemy 2.0
- Migrations: Alembic
- Calculs: NumPy, SciPy
- Fichiers: ezdxf (DXF), ReportLab (PDF), openpyxl (Excel)

**Frontend:**
- Framework: React 18 + TypeScript
- Build: Vite 5
- UI: Tailwind CSS + Radix UI
- State: Zustand
- Data fetching: TanStack Query
- Canvas: Konva / React-Konva
- Formulaires: React Hook Form + Zod

### Structure du Projet
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
│   │       │   └── normes/  # Implémentations multi-normes
│   │       ├── importer/    # Import de données
│   │       └── import/      # Import PDF plans
│   ├── alembic/             # Migrations DB
│   ├── uploads/             # Fichiers uploadés (DXF, PDF)
│   └── main.py
├── frontend/
│   └── src/
│       ├── components/      # Composants React
│       ├── pages/           # Pages de l'application
│       ├── services/        # Appels API
│       ├── stores/          # État Zustand
│       └── types/           # Types TypeScript
└── docker-compose.yml
```

## Import PDF Plans Béton Armé

L'application permet d'importer des plans PDF de béton armé pour extraire automatiquement les données de calcul (poutrelles-hourdis).

### Dépendances PDF (à ajouter à requirements.txt)
```
pdfplumber>=0.10.0      # Extraction de texte et tableaux
PyPDF2>=3.0.0           # Manipulation PDF
pdf2image>=1.16.0       # Conversion PDF vers images
pytesseract>=0.3.10     # OCR pour plans scannés
Pillow>=10.0.0          # Traitement d'images
```

### Données Extraites du PDF
- **Portées** : longueurs des travées en mètres
- **Poutrelles** : références fabricant, type
- **Dalle** : épaisseur de compression
- **Charges** : permanentes (G), exploitation (Q)
- **Entre-axes** : espacement des poutrelles

### Workflow Import
1. Upload du PDF (plan béton armé)
2. Extraction automatique (texte + OCR si nécessaire)
3. Affichage des données extraites pour validation
4. Correction manuelle si nécessaire
5. Lancement du calcul avec données validées

## Objectifs Actuels
1. Consulter @fix_plan.md pour les priorités
2. Implémenter la tâche prioritaire avec les bonnes pratiques
3. Exécuter les tests après chaque implémentation
4. Mettre à jour @fix_plan.md et la documentation

## Normes de Calcul Supportées

L'application supporte plusieurs normes de calcul de structures béton :

| Norme | Code | Région | Description |
|-------|------|--------|-------------|
| Eurocode 2 | EC2 | Europe | Norme européenne actuelle |
| ACI 318 | ACI | USA | American Concrete Institute |
| BAEL 91 | BAEL | France | Ancienne norme française |
| BS 8110 | BS | UK | British Standard (historique) |
| CSA A23.3 | CSA | Canada | Canadian Standards Association |

### Architecture des Normes
```
backend/app/services/calculs/normes/
├── __init__.py
├── base.py          # Classe abstraite NormeBase
├── eurocode.py      # Implémentation Eurocode 2
├── aci318.py        # Implémentation ACI 318
├── bael.py          # Implémentation BAEL 91
└── factory.py       # NormeFactory pour instanciation
```

### Différences Clés entre Normes
- **Coefficients de sécurité** : γc (béton), γs (acier) varient selon la norme
- **Formules de flexion** : Approches rectangulaire vs parabolique
- **Cisaillement** : Méthodes de calcul différentes
- **Enrobage** : Exigences minimales différentes

## Principes Clés
- **UNE tâche par boucle** - focus sur le plus important
- Chercher dans le codebase avant d'assumer qu'une fonctionnalité n'existe pas
- Écrire des tests pour les nouvelles fonctionnalités
- Commiter les changements fonctionnels avec des messages descriptifs
- **Implémenter les calculs selon la norme sélectionnée par l'utilisateur**
- Utiliser le pattern Factory pour instancier la bonne norme

## Commandes Utiles

### Backend
```bash
cd backend
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
pytest  # Tests
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # Port 3000
npm run lint
```

## Directives d'Exécution
- Avant de modifier: explorer le codebase
- Après implémentation: exécuter les tests essentiels
- Si tests échouent: les corriger dans la même boucle
- Garder @AGENT.md à jour avec les instructions build/run
- Pas d'implémentations placeholder - construire correctement

## Rapport de Statut (CRITIQUE)

**IMPORTANT**: À la fin de ta réponse, TOUJOURS inclure ce bloc de statut:

```
---RALPH_STATUS---
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
TASKS_COMPLETED_THIS_LOOP: <nombre>
FILES_MODIFIED: <nombre>
TESTS_STATUS: PASSING | FAILING | NOT_RUN
WORK_TYPE: IMPLEMENTATION | TESTING | DOCUMENTATION | REFACTORING
EXIT_SIGNAL: false | true
RECOMMENDATION: <résumé d'une ligne de la prochaine action>
---END_RALPH_STATUS---
```

### Quand mettre EXIT_SIGNAL: true
1. Tous les items de @fix_plan.md sont cochés [x]
2. Tous les tests passent
3. Pas d'erreurs dans la dernière exécution
4. Toutes les spécifications sont implémentées

## Tâche Actuelle
Suivre @fix_plan.md et choisir l'item le plus important à implémenter.
Utiliser ton jugement pour prioriser ce qui aura le plus grand impact.

**Qualité avant vitesse. Construire correctement dès la première fois.**
