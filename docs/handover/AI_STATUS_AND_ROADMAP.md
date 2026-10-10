# MAISON — AI FASHION MARKETPLACE
# ÉTAT DE L'INTELLIGENCE ARTIFICIELLE & FEUILLE DE ROUTE (ROADMAP)

> **Document :** `docs/handover/AI_STATUS_AND_ROADMAP.md`  
> **Diagnostic :** Audit factuel de l'existant & plan d'implémentation progressif

---

## 1. Audit Sincère & Factuel de l'Existant IA

Une analyse rigoureuse du code source et de l'infrastructure démontre la situation exacte suivante :

| Composant IA / Vectoriel | Statut Réel | Preuve dans le Code Source |
| :--- | :--- | :--- |
| **Extension `pgvector` (Docker)** | **Configuré & Vérifié** | `docker-compose.yml` (`pgvector/pgvector:pg16`) et `infrastructure/docker/init-db.sql` |
| **Dépendance Python `pgvector`** | **Installé & Vérifié** | `backend/requirements.txt` (`pgvector>=0.3.0`) et `backend/pyproject.toml` |
| **Colonnes Vectorielles en Base** | **Non Implémenté** | Aucun type `Vector()` n'existe actuellement dans les modèles SQLAlchemy (`models.py`) |
| **Génération d'Embeddings** | **Non Implémenté** | Aucune bibliothèque d'inférence (Sentence-Transformers, PyTorch, OpenAI) n'est instanciée |
| **Recherche Sémantique / Similarité** | **Non Implémenté** | Le moteur de recherche (`PostgresSearchProvider`) fonctionne par `ILIKE` et filtres SQL classiques |
| **Recommandations & Personnalisation** | **Non Implémenté** | Aucun algorithme de filtrage collaboratif ou de recommandation par contenu n'est présent |
| **Chatbot / LLM Styliste Personnel** | **Non Implémenté** | Aucune intégration d'API LLM (OpenAI, Anthropic, Gemini) n'est configurée |

> **Conclusion de l'audit :** L'infrastructure de données est **prête à accueillir les vecteurs** (`pgvector` est actif dans PostgreSQL), mais **aucune logique IA applicative n'a encore été écrite**.

---

## 2. Matrice de Classification des Fonctionnalités IA

```
Fonctionnalités IA
├── 🟢 Prêtes au niveau infrastructure :
│    ├── Conteneur pgvector PostgreSQL 16
│    └── Pilote Python pgvector
│
├── 🟡 Préparées architecturalement :
│    └── SearchProvider (Protocol dans app/modules/search/providers.py)
│         Permet de brancher un VectorSearchProvider sans modifier l'API existante.
│
└── 🔴 À implémenter :
     ├── Pipeline d'ingestion et vectorisation des pièces de mode
     ├── Recherche sémantique vectorielle (requête textuelle ➔ vecteur ➔ cosinus)
     ├── Recommandation de pièces similaires (Visual / Textual Similarity)
     └── Assistant styliste personnel IA
```

---

## 3. Feuille de Route IA Recommandée (Roadmap par Étapes)

Pour introduire l'IA de manière élégante, démontrable et sans coût d'infrastructure excessif, nous recommandons le plan en trois phases suivant :

### Phase 1 (Priorité Immédiate) : Recherche Sémantique & Similarité Textuelle
* **Objectif :** Permettre aux clients de chercher avec des descriptions stylistiques libres (ex: *"tenue de soirée chic minimaliste pour cocktail d'été"*) plutôt que de stricts mots-clés.
* **Technologie recommandée :** Modèle open-source léger `sentence-transformers/all-MiniLM-L6-v2` (dimension 384) ou `paraphrase-multilingual-MiniLM-L12-v2` (multilingue français/anglais).
* **Travail requis :**
  1. Ajouter `sentence-transformers` et `torch` (CPU) dans `requirements.txt`.
  2. Créer la migration Alembic `0009_add_product_embeddings.py` ajoutant `embedding = Column(Vector(384), nullable=True)` à la table `products`.
  3. Implémenter un worker ou hook synchrone lors de la création/mise à jour d'un produit (`ProductService`) pour vectoriser `name + " " + description`.
  4. Créer `VectorSearchProvider` implémentant le protocole existant `SearchProvider` avec l'opérateur de distance cosinus `<=>` de pgvector.
  5. Exposer l'endpoint `GET /api/v1/search/semantic?q=...`.
* **Budget externe :** **0 $** (100 % local, exécution CPU).

### Phase 2 (Moyen Terme) : Recommandation « Pièces Similaires » (Visual AI)
* **Objectif :** Afficher sous chaque fiche produit (`/products/[id]`) un carrousel « Dans le même esprit » basé sur les caractéristiques visuelles des créations.
* **Technologie recommandée :** Modèle multimodal CLIP (`openai/clip-vit-base-patch32` dimension 512).
* **Travail requis :**
  1. Vectoriser l'image principale de chaque pièce (`ProductMedia`) lors de l'upload sur MinIO.
  2. Requête pgvector : trouver les $k$ produits les plus proches via `ORDER BY embedding <=> :target_embedding LIMIT 4`.
  3. Composant frontend Next.js sur `/products/[id]`.

### Phase 3 (Perspective Future) : Le Concierge Haute Couture (LLM Stylist)
* **Objectif :** Un conseiller de vente IA en temps réel capable d'assister le client dans la composition d'une silhouette complète (robe, souliers, accessoires) parmi les créateurs de la marketplace.
* **Technologie :** Modèle LLM via API (Google Gemini 1.5 Flash ou Claude 3.5 Sonnet) couplé à une recherche vectorielle augmentée (RAG) sur le catalogue de la Maison.
* **Budget externe :** Coût par token API à l'usage.

---

## 4. Consignes Strictes pour le Repreneur

* **Ne pas ajouter de dépendance lourde inutilement :** Ne chargez pas de modèles de plusieurs gigaoctets si un modèle de 80 Mo (`all-MiniLM-L6-v2`) suffit pour le proof-of-concept.
* **Ne pas bloquer la transaction d'écriture :** La génération de vecteurs doit se faire en tâche de fond (FastAPI `BackgroundTasks` ou worker Celery/Redis) pour ne pas ralentir la création de produits par les créateurs.
* **Préserver le moteur de recherche SQL actuel :** La recherche sémantique doit compléter, et non détruire, la recherche par facettes actuelle qui fonctionne à 100 %.
