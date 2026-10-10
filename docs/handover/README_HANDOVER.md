# MAISON — AI FASHION MARKETPLACE
# DOSSIER DE PASSATION TECHNIQUE & GUIDE DE PRISE EN MAIN (HANDOVER)

> **Document :** `docs/handover/README_HANDOVER.md`  
> **Date de passation :** 10 Octobre 2026  
> **Statut global du projet :** Socle Marketplace opérationnel, Design Dark Luxury Haute Couture déployé, 255/255 tests backend validés, vérifications TypeScript et ESLint conformes.  
> **Dépôt officiel :** [https://github.com/the-evilyn/MARKET-AI-Powered-Fashion-Marketplace](https://github.com/the-evilyn/MARKET-AI-Powered-Fashion-Marketplace)

---

## 1. Bienvenue & Objectif de ce Dossier

Ce dossier technique a été rédigé avec rigueur pour permettre à tout nouvel ingénieur, architecte logiciel ou tech lead de **reprendre immédiatement le projet Maison sans perte de contexte, sans hypothèses erronées et sans refaire le travail déjà accompli**.

Le projet **Maison — AI-Powered Fashion Marketplace** est une plateforme e-commerce multi-vendeurs d'exception dédiée à la Haute Couture et aux créateurs indépendants, architecturée autour :
1. D'un backend **FastAPI** en monolythe modulaire asynchrone (Python 3.12, SQLAlchemy 2.0 async, PostgreSQL 16, Redis 7, MinIO S3, PayPal Sandbox).
2. D'un frontend **Next.js 15 (App Router)** avec TypeScript strict et Tailwind CSS, incarnant une direction artistique « Dark Luxury » (fonds charbon `#070a12`, surfaces `#0c101c`, typographie ivoire et accents champagne-or).

---

## 2. Synthèse de l'État Réel du Projet à la Passation

| Domaine | État Vérifié | Détails et Preuves |
| :--- | :--- | :--- |
| **Branche Git** | `main` | Synchronisée sur `origin/main` au commit `68f5db1` |
| **Dernier Commit** | `68f5db1` | `feat(ui): redesign luxury marketplace homepage, navbar, footer, cart drawer, and favorites` |
| **Arbre de travail local** | 13 fichiers modifiés (préservés) | Harmonisations Dark Luxury sur le checkout, le détail produit, les commandes et la boutique vendeur |
| **Backend Tests (pytest)** | **255 / 255 réussis** (100 %) | Exécution `pytest backend/tests` en 11m42s sans aucun échec |
| **Frontend TypeScript** | **0 erreur** (`tsc --noEmit`) | Compilation stricte validée |
| **Frontend Linting** | **0 erreur** (`next lint`) | Seuls des avertissements sur les balises `<img>` standards subsistent |
| **Serveurs locaux actifs** | Opérationnels | FastAPI sur `http://127.0.0.1:8000`, Next.js sur `http://localhost:3001` |
| **Migrations Alembic** | Versions 0001 à 0008 | Schémas users, catalog, inventory, cart, orders, payments, sub_orders, stores |
| **Implémentation IA** | Dépendances prêtes, modèle vectoriel en attente | `pgvector` configuré dans Docker et requirements ; pas encore d'embeddings générés en base |
| **CI/CD Cloud** | Absent en local | Aucun répertoire `.github/workflows` actuellement sous Git |

---

## 3. Ordre de Lecture Recommandé (Parcours 5 Minutes)

Pour appréhender le système en moins de 5 minutes, suivez cet ordre précis :

```
1. README_HANDOVER.md (ce document) ───────────────► Vue d'ensemble et état actuel
2. PROJECT_OVERVIEW.md ────────────────────────────► Vision métier, personas et périmètre
3. ARCHITECTURE.md ────────────────────────────────► Monolythe modulaire, modèles et flux
4. SETUP_AND_EXECUTION.md ─────────────────────────► Lancement local et commandes vérifiées
5. API_REFERENCE.md & DATABASE_REFERENCE.md ───────► Spécifications des interfaces et données
6. KNOWN_ISSUES_AND_NEXT_STEPS.md ─────────────────► Backlog priorisé pour la suite du dev
```

---

## 4. Index Exhaustif des Documents de Passation

Tous les documents sont situés dans le répertoire [`docs/handover/`](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/) :

1. [**`README_HANDOVER.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/README_HANDOVER.md) — Point d'entrée principal, synthèse et cartographie de reprise.
2. [**`PROJECT_OVERVIEW.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/PROJECT_OVERVIEW.md) — Vision produit, rôles (Customer, Seller, Admin), séparation client/serveur et scope fonctionnel.
3. [**`ARCHITECTURE.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/ARCHITECTURE.md) — Architecture logicielle détaillée, diagrammes C4 et séquences Mermaid (Auth, Checkout multi-vendeurs).
4. [**`API_REFERENCE.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/API_REFERENCE.md) — Référence exhaustive des endpoints FastAPI (`/api/v1/*`), rôles requis et payloads.
5. [**`DATABASE_REFERENCE.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/DATABASE_REFERENCE.md) — Schéma relationnel complet, modèles SQLAlchemy, contraintes d'intégrité, migrations Alembic et diagramme ERD.
6. [**`SETUP_AND_EXECUTION.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/SETUP_AND_EXECUTION.md) — Guide d'installation, configuration d'environnement sans fuite de secrets, commandes de démarrage et health checks.
7. [**`TESTING_AND_QA.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/TESTING_AND_QA.md) — Rapport d'assurance qualité : 255 tests pytest, vérifications TypeScript/ESLint, matrice de tests manuels.
8. [**`AI_STATUS_AND_ROADMAP.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/AI_STATUS_AND_ROADMAP.md) — État réel des fonctionnalités IA, analyse de `pgvector`, et roadmap d'implémentation (recommandation par similarité visuelle/textuelle).
9. [**`DEVOPS_AND_DEPLOYMENT.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/DEVOPS_AND_DEPLOYMENT.md) — Docker, Docker Compose, services MinIO/Redis/PostgreSQL, lacunes CI/CD et plan de déploiement sécurisé.
10. [**`SECURITY_AUDIT.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/SECURITY_AUDIT.md) — Audit de sécurité approfondi : Argon2id, JWT, RBAC, webhooks PayPal, upload média, matrice des risques et remédiations.
11. [**`KNOWN_ISSUES_AND_NEXT_STEPS.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/KNOWN_ISSUES_AND_NEXT_STEPS.md) — Backlog priorisé (BLOQUANT, IMPORTANT, OPTIONNEL) avec IDs uniques et critères d'acceptation.
12. [**`GIT_HISTORY_AND_HANDOVER.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/GIT_HISTORY_AND_HANDOVER.md) — Historique Git vérifié, jalons franchis, modifications locales préservées et consignes de versionnage.
13. [**`GLOSSARY.md`**](file:///mnt/c/projects/AI%20Fashion%20Marketplace/docs/handover/GLOSSARY.md) — Glossaire bilingue métier et technique définissant les termes clés du domaine.

---

## 5. Les Premières Actions pour Reprendre le Travail

Pour relancer l'environnement de développement sans incident :

### Étape 1 : Vérifier l'état Git local
```bash
cd "/mnt/c/projects/AI Fashion Marketplace"
git status -sb
```
> **Important :** Ne lancez pas `git reset` ni `git checkout .`. 13 fichiers contiennent des améliorations Dark Luxury prêtes à être revues et commitées après votre prise de connaissance.

### Étape 2 : Démarrer l'infrastructure conteneurisée (si éteinte)
```bash
docker compose up -d postgres redis minio minio-init
```

### Étape 3 : Démarrer le Backend FastAPI
```bash
# Terminal 1
PYTHONPATH=backend ./.venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Health Check :* `curl http://127.0.0.1:8000/api/v1/health`

### Étape 4 : Démarrer le Frontend Next.js
```bash
# Terminal 2
cd frontend
npm run dev -- -p 3001
```
*Application publique :* Ouvrez votre navigateur sur `http://localhost:3001`

---

## 6. Avertissements Critiques & Pièges Connus

1. **Intégrité de la Base de Données :**
   - Ne jamais réinitialiser (`drop database`) ni dégrader les migrations sans précaution.
   - Les commandes et sous-commandes sont liées par des contraintes `ON DELETE RESTRICT` et des checks de non-négativité.
2. **Paiement PayPal Sandbox :**
   - La capture de paiement et la libération de stock s'effectuent côté serveur. Ne contournez pas l'API backend en manipulant le state client.
3. **Absence de fausses données :**
   - La marketplace repose exclusivement sur des produits réels créés via le catalogue. Ne codez pas de fausses évaluations (reviews fictives avec 5 étoiles) ni de faux pourcentages de réduction inventés.
4. **Vérification systématique avant commit :**
   - Toujours exécuter `npx tsc --noEmit` et `git diff --check` avant tout nouveau commit.
