# MAISON — AI FASHION MARKETPLACE
# RAPPORT D'ASSURANCE QUALITÉ & STRATÉGIE DE TEST (QA)

> **Document :** `docs/handover/TESTING_AND_QA.md`  
> **Dernière exécution complète :** 10 Octobre 2026  
> **Taux de succès global :** 100 % des tests automatisés validés

---

## 1. Résultats Réels des Tests & Contrôles Automatisés

Tous les résultats ci-dessous proviennent d'exécutions effectives réalisées dans l'environnement du projet.

| Outil de Test | Commande Exécutée | Code Sortie | Résultat Réel | Durée / Remarques |
| :--- | :--- | :---: | :--- | :--- |
| **Pytest Backend** | `./.venv/bin/pytest backend/tests -q` | **0** | **255 passés**, 0 échec, 0 erreur | 702.65s (11m 42s) |
| **TypeScript Frontend** | `npx tsc --noEmit` | **0** | **0 erreur de typage** | ~1m 30s |
| **ESLint Frontend** | `npm run lint` | **0** | **0 erreur bloquante** (avertissements `<img>`) | ~3m 00s |
| **Git Diff Whitespace** | `git diff --check` | **0** | **0 erreur d'espace ou d'indentation** | < 1s |

---

## 2. Inventaire & Couverture de la Suite Pytest (Backend)

La suite de tests backend compte **15 fichiers de tests** couvrant l'ensemble des modules :

| Fichier de Test | Périmètre & Scénarios Vérifiés | Tests Validés |
| :--- | :--- | :---: |
| `test_admin_platform.py` | Modération des boutiques, audit des utilisateurs, garde d'auto-désactivation, KPIs dashboard | 24 |
| `test_auth.py` | Inscription, connexion, hachage Argon2id, expiration JWT, formats d'email invalides | 22 |
| `test_cart.py` | Ajout au panier, ajustement des quantités, isolation par utilisateur, calcul sous-total | 18 |
| `test_catalog.py` | Hiérarchie des catégories, marques facultatives, création et archivage de produits/variantes | 26 |
| `test_checkout.py` | Validation du panier, création d'ordre, calcul des montants, transition d'état de commande | 15 |
| `test_concurrency_postgres.py` | Verrouillage concurrentiel `SELECT FOR UPDATE`, protection contre l'overselling | 8 |
| `test_config.py` | Validation pydantic-settings, rejet des secrets JWT faibles en staging/production | 12 |
| `test_health.py` | Endpoints `/health` et `/api/v1/health`, disponibilité base de données et Redis | 6 |
| `test_inventory.py` | Niveaux de stock, alertes stock bas, décrémentation atomique, journal des transactions | 20 |
| `test_media_and_fulfillment.py` | Téléversement MinIO, validation Magic Bytes, partitionnement sous-commandes et tracking | 28 |
| `test_payments.py` | Initialisation PayPal, simulation de capture, annulation de paiement, webhooks | 19 |
| `test_search.py` | Moteur à facettes, filtres catégories/marques/prix, tri par prix/nouveauté, pagination | 21 |
| `test_security_hardening.py` | RBAC `require_roles`, protection contre l'élévation de privilèges, politiques CORS | 16 |
| `test_seller.py` | Espace créateur, gestion du catalogue vendeur, isolation des commandes marchands | 12 |
| `test_seller_storefront.py` | Création de boutique, slug unique, modération, visibilité publique des vitrines | 8 |
| **TOTAL** | **Couverture modulaire complète** | **255** |

---

## 3. Matrice des Scénarios de Tests Manuels Critiques

Pour valider l'expérience utilisateur et les parcours sans régression, suivez cette grille de vérification :

### Scénario 1 : Parcours Découverte & Client Privé (`CUSTOMER`)
1. **Accès Catalogue (`/`) :** Vérifier l'affichage du Hero éditorial, des 4 piliers d'excellence et des catégories.
2. **Recherche & Facettes :** Saisir un mot-clé, filtrer par catégorie ou tranche de prix, cocher « En stock ».
3. **Fiche Pièce (`/products/[id]`) :** Sélectionner une taille/couleur. Vérifier l'affichage dynamique du prix et du stock.
4. **Wishlist :** Cliquer sur le cœur pour ajouter aux favoris. Constater l'incrémentation du badge dans la Navbar.
5. **Panier Coulissant (`CartDrawer`) :** Ajouter un article au panier. Le volet s'ouvre, affiche le sous-total et permet d'ajuster la quantité (+ / -).
6. **Passage en Caisse (`/checkout`) :** Cliquer sur « Passer à la caisse ». Confirmer la sélection. L'ordre passe en `PENDING_PAYMENT` et réserve le stock.
7. **Paiement Sandbox :** Valider via le bouton PayPal. Vérifier la redirection vers l'écran de succès et la création de la commande.
8. **Consultation Commandes (`/orders`) :** Vérifier que la nouvelle commande apparaît avec ses colis et son statut `CONFIRMÉE`.

### Scénario 2 : Parcours Maison & Vendeur Créateur (`SELLER`)
1. **Connexion Vendeur :** Cliquer sur « Vendeur (Test) » dans la Navbar (`seller@example.com`).
2. **Espace Vendeur (`/seller/dashboard`) :** Vérifier le chargement des indicateurs et alertes de stock.
3. **Gestion Boutique (`/seller/settings`) :** Renseigner le nom de la boutique, le manifeste et téléverser un logo/bannière.
4. **Vitrine Publique (`/store/[slug]`) :** Ouvrir l'URL publique de la boutique. Vérifier l'affichage du logo, de la bannière et des pièces de la Maison.
5. **Expédition Colis (`/seller/orders`) :** Sélectionner une sous-commande en attente, renseigner le transporteur (ex: `DHL Express`) et le numéro de suivi, puis passer le statut en `SHIPPED`.

### Scénario 3 : Parcours Gouvernance & Administration (`ADMIN`)
1. **Connexion Administrateur :** Se connecter avec un compte ayant le rôle `ADMIN`.
2. **Tableau de Bord (`/admin/dashboard`) :** Vérifier l'affichage du GMV consolidé et de la liste des créateurs actifs.
3. **Modération des Boutiques (`/admin/stores`) :** Rechercher une boutique, modifier son statut (`APPROVED` / `SUSPENDED`) et lui accorder le badge certifié (`is_verified`).
4. **Gouvernance Utilisateurs (`/admin/users`) :** Vérifier que l'auto-désactivation du compte administrateur connecté est bloquée par l'interface et par le backend.
5. **Supervision Commandes (`/admin/orders`) :** Filtrer les commandes globales de la place de marché par statut.

---

## 4. Limites Actuelles de la Couverture de Test

* **Tests End-to-End (E2E) :** Le projet ne dispose pas encore de suite Playwright ou Cypress automatisée dans le dépôt. Les parcours complets sont validés manuellement ou par tests d'intégration API (`httpx.AsyncClient`).
* **Tests de Charge :** La concurrence sur la réservation de stock est couverte par `test_concurrency_postgres.py` avec 10 requêtes concurrentes, mais aucun test de charge à l'échelle (Locust ou k6) n'est pour l'instant configuré.
