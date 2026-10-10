# MAISON — AI FASHION MARKETPLACE
# GUIDE D'INSTALLATION, CONFIGURATION & EXÉCUTION LOCALE

> **Document :** `docs/handover/SETUP_AND_EXECUTION.md`  
> **Destinataire :** Développeur repreneur, Tech Lead, DevOps  
> **Objectif :** Démarrer l'ensemble de la pile technique locale en moins de 10 minutes

---

## 1. Prérequis & Versions Recommandées

| Outil / Runtime | Version Minimale | Rôle |
| :--- | :--- | :--- |
| **Python** | `3.12+` | Exécution du backend FastAPI et des migrations Alembic |
| **Node.js** | `18.18+` (recommandé `20.x`) | Exécution du frontend Next.js 15 |
| **npm** | `9.x+` ou `10.x+` | Gestionnaire de dépendances frontend |
| **Docker & Docker Compose** | `24.x+` / `v2.x+` | Conteneurisation de PostgreSQL 16 (pgvector), Redis 7 et MinIO |
| **Git** | `2.40+` | Gestion de versions et inspection de l'arbre de travail |

---

## 2. Configuration des Variables d'Environnement

Le projet utilise un modèle de configuration `.env.example` à la racine.

### Étape 1 : Créer le fichier local `.env`
```bash
cd "/mnt/c/projects/AI Fashion Marketplace"
cp .env.example .env
```

### Étape 2 : Revue des Variables Critiques (Sans divulguer de secrets réels)

| Variable | Environnement | Description & Contrainte de Sécurité |
| :--- | :--- | :--- |
| `APP_ENV` | Tous | `development`, `staging`, ou `production` |
| `DATABASE_URL` | Backend | URL asynchrone SQLAlchemy : `postgresql+asyncpg://user:pass@localhost:5432/fashion_marketplace` |
| `REDIS_URL` | Backend | URL de connexion au broker Redis : `redis://localhost:6379/0` |
| `JWT_SECRET` | Backend | **Obligation de sécurité :** En staging/production, doit comporter au moins 32 caractères non triviaux. Le backend refuse de démarrer avec la clé par défaut en environnement sécurisé. |
| `MINIO_ENDPOINT` | Backend | Hôte MinIO : `localhost:9000` en local |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | Backend | Identifiants d'accès S3 local (ex: `minioadmin` en local) |
| `MINIO_BUCKET` | Backend | Nom du compartiment de stockage d'images (défaut : `fashion-media`) |
| `CORS_ORIGINS` | Backend | Tableau JSON d'origines autorisées (ex: `["http://localhost:3000","http://localhost:3001"]`) |
| `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` | Backend | Identifiants Sandbox PayPal pour l'API REST v2 (optionnels hors tests de paiement) |
| `NEXT_PUBLIC_API_URL` | Frontend | URL racine de l'API backend consommée par le navigateur : `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_PAYPAL_CLIENT_ID` | Frontend | Identifiant public PayPal pour instancier les boutons interactifs |

---

## 3. Lancement des Services d'Infrastructure (Docker)

Démarrez les services de persistance en arrière-plan :

```bash
# À la racine du projet
docker compose up -d postgres redis minio minio-init
```

Vérifiez que les conteneurs sont sains (`healthy`) :
```bash
docker compose ps
```
* `fashion-postgres` (PostgreSQL 16 + pgvector) : port `5432`
* `fashion-redis` (Redis 7) : port `6379`
* `fashion-minio` (MinIO Object Storage) : API sur `9000`, Console web sur `9001`
* `fashion-minio-init` : Crée automatiquement le bucket `fashion-media` et termine (`Exited 0`)

---

## 4. Initialisation & Démarrage du Backend FastAPI

### Étape 1 : Créer et activer l'environnement virtuel Python
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Étape 2 : Installer les dépendances backend
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Étape 3 : Appliquer les migrations de base de données
```bash
alembic -c backend/alembic.ini upgrade head
```

### Étape 4 : Lancer le serveur d'API (Uvicorn)
```bash
PYTHONPATH=backend ./.venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

* **URL de base :** `http://127.0.0.1:8000`
* **Health Check :** `curl http://127.0.0.1:8000/api/v1/health`
* **Documentation Swagger interactive :** `http://127.0.0.1:8000/docs` (active en développement)

---

## 5. Initialisation & Démarrage du Frontend Next.js

Ouvrez un second terminal.

### Étape 1 : Naviguer dans le dossier frontend et installer les paquets
```bash
cd "/mnt/c/projects/AI Fashion Marketplace/frontend"
npm install
```

### Étape 2 : Démarrer le serveur de développement Next.js sur le port 3001
```bash
npm run dev -- -p 3001
```

* **Accès public :** Ouvrez votre navigateur sur `http://localhost:3001`
* **Comptes de test intégrés :** La Navbar propose deux boutons de connexion instantanée 1-clic :
  - **Client (Test)** : `customer@example.com` / `Customer123!` (rôle `CUSTOMER`)
  - **Vendeur (Test)** : `seller@example.com` / `Seller123!` (rôle `SELLER`)

---

## 6. Résolution des Problèmes Courants (Troubleshooting)

### Problème 1 : Conflit de port sur le port 3000
* **Cause :** Un autre service Next.js ou React occupe le port par défaut 3000.
* **Solution :** Lancez toujours le frontend avec l'argument explicite `-p 3001` (`npm run dev -- -p 3001`). Le fichier `.env` et les règles CORS sont configurés pour accepter le port 3001.

### Problème 2 : Erreur de connexion `asyncpg` au démarrage du backend
* **Message :** `ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 5432)`
* **Solution :** Le conteneur PostgreSQL n'est pas encore démarré ou n'est pas prêt. Lancez `docker compose up -d postgres` et attendez que `docker compose ps` indique `(healthy)`.

### Problème 3 : Erreur d'upload média sur MinIO
* **Message :** `NoSuchBucket: The specified bucket does not exist`
* **Solution :** Le conteneur d'initialisation MinIO ne s'est pas exécuté. Lancez `docker compose up minio-init` pour créer le bucket `fashion-media` et appliquer la politique de lecture publique.

### Problème 4 : Le backend refuse de démarrer avec `ValueError: Insecure default JWT signing key`
* **Cause :** `APP_ENV` est réglé sur `production` ou `staging`, mais `JWT_SECRET` utilise une clé par défaut.
* **Solution :** Modifiez `.env` pour définir `APP_ENV=development` en local, ou générez une clé aléatoire forte de 64 caractères : `openssl rand -hex 32`.
