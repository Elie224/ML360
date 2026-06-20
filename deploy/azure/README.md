# ML360 - Preparation Deploiement Azure (Compte Etudiant)

## Architecture recommandee (credits etudiants)

- Backend API Django sur Azure App Service Linux
- Frontend React/Vite sur Azure Storage Static Website
- Base de donnees:
  - Option rapide demo: SQLite (pas ideal long terme)
  - Option production: Azure Database for PostgreSQL Flexible Server

## Prerequis

- Azure CLI installe
- Node.js LTS installe
- Python 3.12 installe
- Connexion Azure active: az login

## 1) Deployer le backend (App Service)

Script:

deploy/azure/deploy-backend-appservice.ps1

Parametres principaux:

- SubscriptionId
- ResourceGroup
- Location
- PlanName
- WebAppName
- DjangoSecretKey
- FrontendOrigin

Exemple PowerShell:

powershell -ExecutionPolicy Bypass -File deploy/azure/deploy-backend-appservice.ps1 \
  -SubscriptionId "<subscription-id>" \
  -ResourceGroup "rg-ml360" \
  -Location "francecentral" \
  -PlanName "asp-ml360" \
  -WebAppName "ml360-api-<suffixe-unique>" \
  -DjangoSecretKey "<secret-fort>" \
  -FrontendOrigin "https://<frontend-url>"

Healthcheck attendu:

https://<webapp-name>.azurewebsites.net/api/health/

## 2) Initialiser les quiz en base (une fois)

Apres deploiement, executer dans l'environnement App Service:

- python manage.py import_ml360_module_quizzes --input data/modules --validation-mode strict

Tu peux le faire via console SSH App Service dans le portail Azure.

## 3) Deployer le frontend (Storage Static Website)

Script:

deploy/azure/deploy-frontend-storage.ps1

Parametres principaux:

- SubscriptionId
- ResourceGroup
- Location
- StorageAccountName (doit etre globalement unique, minuscules/chiffres)
- BackendApiBaseUrl (ex: https://ml360-api-xxxx.azurewebsites.net/api)

Exemple PowerShell:

powershell -ExecutionPolicy Bypass -File deploy/azure/deploy-frontend-storage.ps1 \
  -SubscriptionId "<subscription-id>" \
  -ResourceGroup "rg-ml360" \
  -Location "francecentral" \
  -StorageAccountName "ml360front<suffixe>" \
  -BackendApiBaseUrl "https://<webapp-name>.azurewebsites.net/api"

## 4) Variables backend importantes

Configurer dans App Service:

- DJANGO_SECRET_KEY
- DJANGO_DEBUG=False
- DJANGO_ALLOWED_HOSTS=<webapp>.azurewebsites.net
- DJANGO_CSRF_TRUSTED_ORIGINS=https://<webapp>.azurewebsites.net
- CORS_ALLOWED_ORIGINS=https://<frontend-host>

Si PostgreSQL est active:

- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_HOST
- POSTGRES_PORT

## 5) Verification finale

- Frontend charge la page d'accueil
- Appel API categories OK
- Ouverture d'un quiz OK
- Soumission d'un quiz OK

## Notes compte etudiant

- Sur compte etudiant, surveille le cout App Service B1 et PostgreSQL
- Pour demo courte duree, tu peux commencer sans PostgreSQL
- Pour usage reel, passe a PostgreSQL (SQLite ne convient pas pour un trafic multi-instance)
