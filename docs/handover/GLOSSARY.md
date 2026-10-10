# MAISON — AI FASHION MARKETPLACE
# GLOSSAIRE TECHNIQUE & MÉTIER (TERMINOLOGIE)

> **Document :** `docs/handover/GLOSSARY.md`  
> **Portée :** Définitions claires des concepts clés utilisés dans le code source et la documentation

---

## 1. Terminologie Métier & Produit

* **Marketplace (Place de Marché) :** Plateforme e-commerce intermédiaire mettant en relation des acheteurs finaux (clients privés) et de multiples vendeurs indépendants (Maisons de mode, créateurs).
* **Multi-Vendor (Multi-Vendeurs) :** Architecture métier dans laquelle une commande globale peut contenir des articles provenant de créateurs distincts, nécessitant un partitionnement des expéditions et des règlements.
* **Storefront (Vitrine Boutique) :** Page publique personnalisée (`/store/[slug]`) accordée à une Maison partenaire pour exposer son identité de marque (bannière, logo, biographie) et ses créations exclusives.
* **Sub-Order (Sous-Commande) :** Partitionnement d'une commande globale assignée à un vendeur unique. Permet à chaque créateur d'expédier son colis de manière autonome avec son propre transporteur et numéro de suivi.
* **Dark Luxury :** Ligne directrice visuelle de la plateforme Maison caractérisée par des surfaces charbon sombres (`#070a12`, `#0c101c`), une typographie serif ivoire, des contrastes feutrés et de délicats accents or champagne (`amber-300`, `amber-400`).
* **Maison Certifiée (`is_verified`) :** Statut de confiance accordé par l'administration à un créateur dont l'authenticité des pièces et les normes éthiques ont été validées.

---

## 2. Terminologie Architecture & Backend

* **Monolythe Modulaire :** Modèle d'architecture logicielle regroupant l'ensemble du code dans un même binaire/processus déployable (FastAPI), tout en organisant les domaines métiers en modules strictement étanches (`modules/auth`, `modules/catalog`, etc.).
* **RBAC (Role-Based Access Control) :** Contrôle d'accès basé sur les rôles (`CUSTOMER`, `SELLER`, `ADMIN`), appliqué au niveau des routes par la dépendance `require_roles`.
* **JWT (JSON Web Token) :** Standard ouvert (RFC 7519) définissant un format compact et autonome pour transmettre des informations de session sécurisées signées cryptographiquement (HS256).
* **Argon2id :** Algorithme hybride de hachage de mots de passe résistant aux attaques par canal auxiliaire et aux calculs accélérés sur GPU/ASIC, recommandé par l'OWASP.
* **ORM (Object-Relational Mapping) :** Couche logicielle (SQLAlchemy 2.0 asynchrone) établissant une correspondance entre les classes Python et les tables relationnelles de la base de données.
* **Alembic :** Outil de gestion des migrations de base de données pour SQLAlchemy permettant d'appliquer et de versionner de manière incrémentale les évolutions de schéma SQL.
* **SELECT FOR UPDATE (Verrouillage de ligne) :** Clause SQL verrouillant les lignes sélectionnées lors d'une transaction, garantissant l'atomicité de la réservation de stock et éliminant tout risque de survente (overselling).
* **Magic Bytes (Nombres Magiques) :** Séquence d'octets située au tout début d'un fichier permettant d'identifier de manière infaillible son format réel (ex: `\xFF\xD8\xFF` pour un JPEG), indépendamment de l'extension déclarée.

---

## 3. Terminologie Intelligence Artificielle & Vectorielle

* **`pgvector` :** Extension open-source pour PostgreSQL permettant de stocker, indexer et interroger des vecteurs d'embeddings directement dans la base de données relationnelle.
* **Embeddings (Plongements Vectoriels) :** Représentations numériques denses sous forme de tableaux de nombres flottants (ex: dimension 384 ou 512), traduisant le sens d'un texte ou d'une image dans un espace sémantique continu.
* **Cosine Similarity (Similarité Cosinus) :** Mesure mathématique évaluant la proximité de deux vecteurs d'embeddings (opérateur `<=>` dans pgvector). Deux vêtements au style similaire auront une distance cosinus très faible.
* **Semantic Search (Recherche Sémantique) :** Moteur de recherche capable de comprendre l'intention et le contexte stylistique d'une requête libre (ex: *"robe fluide pour soirée d'été"*), au-delà de la stricte correspondance exacte de mots-clés.
* **Multimodal AI :** Modèle d'intelligence artificielle (ex: CLIP) capable de traiter et de mettre en correspondance simultanément du texte et des images dans le même espace vectoriel.

---

## 4. Terminologie DevOps & Infrastructure

* **Conteneurisation (Docker) :** Mécanisme d'isolation logicielle empaquetant une application et ses dépendances dans une image légère et reproductible.
* **Docker Compose :** Outil d'orchestration multi-conteneurs local permettant de lancer en une seule commande l'application, sa base PostgreSQL, son cache Redis et son stockage S3 MinIO.
* **CI/CD (Continuous Integration / Continuous Deployment) :** Pratique automatisant les tests, la vérification de conformité de code et le déploiement sur les environnements cibles.
* **Webhook :** Mécanisme de rappel HTTP par lequel un service externe (ex: PayPal) notifie le backend de la survenue d'un événement asynchrone (ex: `PAYMENT.CAPTURE.COMPLETED`).
