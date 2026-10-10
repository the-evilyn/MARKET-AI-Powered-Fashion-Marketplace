# MAISON — AI FASHION MARKETPLACE
# AUDIT DE SÉCURITÉ & MATRICE DE GOUVERNANCE

> **Document :** `docs/handover/SECURITY_AUDIT.md`  
> **Méthodologie :** Analyse statique de code, revue des flux d'authentification et conformité OWASP Top 10  
> **Date de l'audit :** 10 Octobre 2026

---

## 1. Synthèse de la Posture de Sécurité

La plateforme Maison met en œuvre des mécanismes de protection robustes pour garantir la sécurité des transactions et des identités :
* **Mots de passe :** Hachés avec l'algorithme de pointe **Argon2id** (`argon2-cffi`), avec coût mémoire et temps configurés selon les recommandations OWASP.
* **Jetons de session :** Jetons cryptographiques **JWT (RFC 7519)** signés en **HS256** avec validation obligatoire de la robustesse de la clé secrète en environnement de production et staging.
* **Contrôle d'accès (RBAC) :** Cloisonnement strict des rôles (`CUSTOMER`, `SELLER`, `ADMIN`) appliqué par la dépendance `require_roles` sur chaque route sensible.
* **Gouvernance des administrateurs :** Protection contre l'auto-désactivation du compte administrateur connecté et interdiction de désactiver le dernier administrateur actif du système.
* **Intégrité des fichiers téléversés :** Double vérification du type MIME et de la signature binaire (**Magic Bytes**) pour contrer les uploads malveillants.
* **Réservation transactionnelle :** Verrous de base de données `SELECT FOR UPDATE` évitant les conditions de course (Race Conditions) sur les stocks.

---

## 2. Revue Détaillée par Vecteur de Sécurité

### 2.1 Hachage des Mots de Passe & Authentification
* **Implémentation :** `backend/app/core/security.py` via `argon2.PasswordHasher()`.
* **Points forts :**
  - Argon2id est résistant aux attaques par dictionnaires et par GPU/ASIC.
  - Aucune empreinte en clair n'est stockée ni renvoyée dans les réponses API.
  - Lors de la connexion, les erreurs d'authentification renvoient un code unifié HTTP 401 avec le message `"Invalid email or password"` afin d'empêcher l'énumération des comptes existants.

### 2.2 Gestion des Jetons JWT & Validation des Secrets
* **Implémentation :** `backend/app/core/config.py` et `backend/app/core/security.py`.
* **Garde-fou durci (Commit `fccbc05`) :**
  - En environnement `production` ou `staging`, le backend valide au démarrage via Pydantic (`validate_jwt_secret_safety`) que `JWT_SECRET` :
    1. N'est pas vide.
    2. Ne figure pas dans la liste des clés par défaut triviales (`"super_secret_jwt_signing_key_replace_in_production_min32chars"`, `"secret"`, `"admin"`, etc.).
    3. Comporte une longueur minimale de 32 caractères.
  - Tout démarrage avec une clé faible en production échoue immédiatement (`ValueError`).

### 2.3 Contrôle d'Accès Basé sur les Rôles (RBAC)
* **Implémentation :** `backend/app/modules/auth/dependencies.py` (`require_roles`).
* **Vérification :**
  - Un utilisateur non authentifié reçoit `401 Unauthorized`.
  - Un utilisateur authentifié dont le rôle ne correspond pas à l'opération requise reçoit `403 Forbidden`.
  - Les routes `/api/v1/admin/*` exigent strictement `UserRole.ADMIN`.
  - Les routes d'expédition `/api/v1/seller/*` vérifient que le vendeur connecté est bien le propriétaire de la ressource demandée (`sub_order.seller_id == current_user.id`).

### 2.4 Protection des Uploads Médias (MinIO S3)
* **Implémentation :** `backend/app/modules/catalog/routes/products.py` et `backend/app/modules/seller/routes.py`.
* **Vérification :**
  - Types MIME autorisés restreints : `image/jpeg`, `image/png`, `image/webp`.
  - Taille maximale par fichier limitée (10 Mo).
  - Validation de la signature binaire (Magic Bytes) : les 4 premiers octets du flux sont inspectés avant tout envoi sur MinIO (ex: `\xFF\xD8\xFF` pour JPEG, `\x89PNG\r\n\x1a\n` pour PNG, `RIFF....WEBP` pour WebP).
  - Tout fichier exécutable déguisé avec une extension `.jpg` est rejeté par HTTP 400.

### 2.5 Validation des Paiements & Webhooks PayPal
* **Implémentation :** `backend/app/modules/payments/service.py` et `backend/app/core/config.py`.
* **Sécurité :**
  - La capture des fonds est effectuée côté serveur par le backend via l'API PayPal REST v2, et non par le navigateur client.
  - La décrémentation des stocks n'est exécutée que lorsque PayPal confirme le statut `COMPLETED`.
  - En production/staging, la variable `PAYPAL_WEBHOOK_ID` est requise pour valider cryptographiquement la signature des webhooks PayPal.

---

## 3. Matrice des Risques & Vulnérabilités Identifiées

| ID | Domaine | Gravité | Vulnérabilité / Constat | Preuve / Fichier | Statut Vérifié | Remédiation Recommandée |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- |
| **SEC-01** | **Secret Management** | **Moyen** | Clé JWT par défaut présente dans `.env.example` | `.env.example` L34 | Vérifié | Documenté : la validation Pydantic bloque le démarrage en production. S'assurer que le fichier `.env` réel sur le serveur de prod utilise une clé aléatoire. |
| **SEC-02** | **Rate Limiting** | **Moyen** | Absence de limitation de débit sur `/api/v1/auth/login` | `backend/app/modules/auth/routes.py` | Vérifié | Implémenter un limiteur de requêtes (ex: `slowapi` ou Redis token-bucket) limitant à 5 tentatives par minute par IP. |
| **SEC-03** | **CORS Configuration** | **Faible** | `allow_headers=["*"]` et `allow_methods=["*"]` dans FastAPI | `backend/app/main.py` L48 | Vérifié | Restreindre explicitement aux méthodes HTTP nécessaires (`GET`, `POST`, `PATCH`, `DELETE`) en production. |
| **SEC-04** | **Refresh Tokens** | **Faible** | Seuls les access tokens sont utilisés côté frontend | `frontend/src/context/AuthContext.tsx` | Vérifié | Le modèle backend supporte les refresh tokens, mais le frontend stocke uniquement l'access token dans `localStorage`. Migrer vers des cookies `HttpOnly; SameSite=Strict` pour éliminer le risque d'exfiltration par faille XSS. |
| **SEC-05** | **Content Security Policy** | **Faible** | Absence d'en-têtes CSP stricts dans `next.config.ts` | `frontend/next.config.ts` | Vérifié | Ajouter les en-têtes HTTP de sécurité (`Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`). |

---

## 4. Recommandations de Déploiement en Production

1. **Génération d'une Clé Secrète de Production :**
   ```bash
   openssl rand -hex 64
   ```
2. **Configuration HTTPS Stricte :**
   - Terminaison TLS 1.3 avec redirection automatique HTTP ➔ HTTPS.
3. **Isolation Réseau :**
   - Les ports 5432 (Postgres), 6379 (Redis) et 9000 (MinIO API) ne doivent **jamais** être exposés sur l'Internet public. Seul le reverse proxy (port 443) doit router vers FastAPI et Next.js.
