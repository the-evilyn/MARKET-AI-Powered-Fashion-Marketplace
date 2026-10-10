# MAISON — AI FASHION MARKETPLACE
# BACKLOG TECHNIQUE & PROCHAINES ÉTAPES (PRIORISÉ)

> **Document :** `docs/handover/KNOWN_ISSUES_AND_NEXT_STEPS.md`  
> **Classification de Priorité :** `BLOQUANT` • `IMPORTANT` • `OPTIONNEL`

---

## 1. Vue d'Ensemble du Backlog de Reprise

Ce carnet de route classe avec précision les tâches restantes sur la base des preuves constatées dans le dépôt.

```
Périmètre Restant
├── 🛑 BLOQUANT :
│    └── Aucun bug bloquant à l'exécution locale (socle 100% opérationnel)
│
├── 🔶 IMPORTANT :
│    ├── [TASK-01] Valider et commiter les harmonisations Dark Luxury locales
│    ├── [TASK-02] Mettre en place le pipeline CI/CD GitHub Actions (.github/workflows)
│    ├── [TASK-03] Intégrer un service d'envoi d'emails transactionnels (Resend / SMTP)
│    └── [TASK-04] Implémenter la Phase 1 IA : Recherche Sémantique & Embeddings pgvector
│
└── 🔷 OPTIONNEL & DETTE TECHNIQUE :
     ├── [TASK-05] Optimiser les balises <img> vers next/image (ESLint warnings)
     ├── [TASK-06] Sécuriser le stockage des jetons JWT en cookies HttpOnly
     ├── [TASK-07] Mettre en place une suite de tests End-to-End Playwright
     └── [TASK-08] Module d'évaluation et avis clients authentifiés (Reviews)
```

---

## 2. Fiches Détaillées des Tâches Prioritaires

### `TASK-01` : Revue et Commit des Harmonisations Dark Luxury Locales
* **Priorité :** `IMPORTANT`
* **Statut actuel :** Implémenté localement, non commité (13 fichiers modifiés).
* **Fichiers concernés :**
  - `frontend/src/app/checkout/page.tsx`
  - `frontend/src/app/orders/page.tsx` et `[id]/page.tsx`
  - `frontend/src/app/products/[id]/page.tsx`
  - `frontend/src/app/store/[slug]/page.tsx`
  - `frontend/src/components/CartDrawer.tsx`
  - `frontend/src/components/Navbar.tsx`
  - `frontend/src/components/store/*`
* **Objectif :** Intégrer définitivement la palette Dark Luxury (charbon, ivoire, or champagne) et les libellés en français sur les pages produit, checkout, commandes et vitrines boutiques.
* **Critères d'acceptation :**
  - `git diff --check` retourne 0 erreur.
  - `npx tsc --noEmit` retourne 0 erreur de typage.
  - `git commit` avec le message `feat(ui): harmonize luxury styling across product detail, checkout, orders, and storefront`.
* **Effort estimé :** 15 minutes.
* **Prochaine action :** Obtenir l'accord explicite de l'utilisateur pour lancer `git commit` et `git push`.

---

### `TASK-02` : Création du Pipeline CI/CD GitHub Actions
* **Priorité :** `IMPORTANT`
* **Statut actuel :** Manquant (aucun répertoire `.github/workflows`).
* **Fichiers concernés :** `.github/workflows/ci.yml`.
* **Objectif :** Garantir que chaque commit et pull request valide automatiquement la suite de 255 tests pytest, le typage TypeScript et le linting.
* **Critères d'acceptation :**
  - Exécution d'un job backend avec conteneur PostgreSQL 16.
  - Exécution de `pytest backend/tests` réussie.
  - Exécution d'un job frontend avec `npx tsc --noEmit` et `npm run lint`.
* **Effort estimé :** 1 heure.

---

### `TASK-03` : Service de Notification & Emails Transactionnels
* **Priorité :** `IMPORTANT`
* **Statut actuel :** Non implémenté (les commandes sont créées sans envoi de mail).
* **Fichiers concernés :**
  - `backend/app/core/config.py` (variables SMTP / Resend API Key)
  - `backend/app/modules/orders/service.py` (hook de confirmation de commande)
* **Objectif :** Envoyer un email de confirmation de commande élégant au client et une notification d'expédition au créateur.
* **Critères d'acceptation :**
  - Réception d'un email formaté en HTML responsive contenant le récapitulatif de la commande et le numéro de commande.
* **Effort estimé :** 2 heures.

---

### `TASK-04` : Implémentation Phase 1 IA — Recherche Sémantique & pgvector
* **Priorité :** `IMPORTANT`
* **Statut actuel :** Infrastructure prête (pgvector actif), modèle et routes à implémenter.
* **Fichiers concernés :**
  - `backend/alembic/versions/0009_add_product_embeddings.py`
  - `backend/app/modules/catalog/models.py`
  - `backend/app/modules/search/providers.py`
  - `backend/app/modules/search/routes.py`
* **Objectif :** Générer des embeddings textuels pour chaque produit via un modèle léger (ex: `all-MiniLM-L6-v2`) et permettre la recherche par similarité cosinus (`<=>`).
* **Critères d'acceptation :**
  - Les requêtes sémantiques libres (ex: *"robe en soie pour cocktail"*) retournent les pièces pertinentes même sans correspondance exacte de mot-clé.
  - L'endpoint `GET /api/v1/search/semantic` répond en moins de 150 ms.
* **Effort estimé :** 4 heures.

---

### `TASK-05` : Optimisation des Balises Images Next.js (`next/image`)
* **Priorité :** `OPTIONNEL` (Dette technique)
* **Statut actuel :** Utilisation de balises standards `<img>` (générant des avertissements ESLint `@next/next/no-img-element`).
* **Fichiers concernés :** Composants de catalogue et pages de détail produit.
* **Objectif :** Remplacer les balises `<img>` par le composant `<Image />` de Next.js pour bénéficier de l'optimisation automatique de format (WebP/AVIF), du lazy-loading natif et d'un score Core Web Vitals (LCP) optimal.
* **Critères d'acceptation :**
  - `npm run lint` ne produit plus aucun avertissement.
* **Effort estimé :** 1 heure.

---

### `TASK-06` : Sécurisation des Jetons JWT en Cookies HttpOnly
* **Priorité :** `OPTIONNEL` (Renforcement de sécurité)
* **Statut actuel :** Le token est stocké dans `localStorage` par `AuthContext.tsx`.
* **Fichiers concernés :**
  - `backend/app/modules/auth/routes.py` (`set-cookie`)
  - `frontend/src/context/AuthContext.tsx`
* **Objectif :** Éliminer l'accès au jeton par JavaScript pour neutraliser le risque d'exfiltration en cas de faille XSS.
* **Effort estimé :** 2 heures.
