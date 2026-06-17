# ML360 Backend

Backend Django REST pour l'application de QCM ML360.

## Stack

- Django 6
- Django REST Framework
- PostgreSQL en cible principale
- SQLite en fallback local si les variables PostgreSQL ne sont pas definies

## Demarrage local

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py runserver
```

## Variables d'environnement

Configurer [backend/.env.example](c:/Users/KOURO/Desktop/ML%20360/backend/.env.example) puis creer `backend/.env`.

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

## Endpoints initiaux

- `GET /api/health/`
- `GET /api/categories/`
- `GET /api/quizzes/`
- `GET /api/quizzes/<slug>/`
- `POST /api/quizzes/<slug>/submit/`

## Donnees initiales

Les migrations initiales ajoutent les 4 categories de base:

- apprentissage supervise
- apprentissage non supervise
- apprentissage semi supervise
- apprentissage par renforcement

Chaque categorie contient 4 niveaux standards:

- Niveau 1: Apprentissage
- Niveau 2: Consolidation
- Niveau 3: Maitrise
- Niveau 4: Expert

## Generation de dataset JSON

Une commande Django permet de generer un dataset JSON strict pour une categorie supportee.

```powershell
..\.venv\Scripts\python manage.py generate_ml360_dataset --category apprentissage-supervise --output data\apprentissage-supervise.json
```

Categories actuellement supportees:

- `apprentissage-supervise`
- `apprentissage-non-supervise`
- `apprentissage-semi-supervise`
- `apprentissage-par-renforcement`

Le fichier d exemple pour la categorie supervisee est [c:\Users\KOURO\Desktop\ML 360\backend\data\apprentissage-supervise.json](c:/Users/KOURO/Desktop/ML%20360/backend/data/apprentissage-supervise.json).

Pour generer un quiz JSON strict pour un module precis:

```powershell
..\.venv\Scripts\python manage.py generate_ml360_module_quiz --category apprentissage-supervise --level Beginner --module "Fondamentaux du supervise" --output data\fondamentaux-du-supervise.json
```

Pour generer tous les modules de toutes les categories dans une arborescence dediee:

```powershell
..\.venv\Scripts\python manage.py generate_ml360_all_module_quizzes --output-dir data\modules
```

Pour importer un fichier JSON de module ou tout un dossier de modules dans la base:

```powershell
..\.venv\Scripts\python manage.py import_ml360_module_quizzes --input data\modules
```