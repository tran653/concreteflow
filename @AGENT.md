# ConcreteFlow - Instructions de Build

## Setup du Projet

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
```

## Lancer l'Application

### Backend
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm run dev
# App: http://localhost:3000
```

## Tests

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm run lint
```

## Migrations DB

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Key Learnings

- SQLite en dev, PostgreSQL en prod
- Calculs Eurocode dans `app/services/calculs/`
- Imports DXF avec `ezdxf`
- State: Zustand, Data fetching: TanStack Query
