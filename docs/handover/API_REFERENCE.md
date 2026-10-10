# MAISON — AI FASHION MARKETPLACE
# RÉFÉRENCE DE L'API REST (FASTAPI V1)

> **Document :** `docs/handover/API_REFERENCE.md`  
> **Base URL :** `http://127.0.0.1:8000/api/v1`  
> **Format :** JSON (RFC 8259) • **Authentification :** En-tête HTTP `Authorization: Bearer <JWT>`

---

## 1. Diagnostics & Disponibilité Système (`/health`)

| Méthode | Route | Description | Auth / Rôle | Fichier Source |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Diagnostic de santé simplifié (statut, base de données, cache) | Public | `backend/app/modules/health/routes.py` |
| `GET` | `/api/v1/health` | Diagnostic détaillé (PostgreSQL, Redis, MinIO S3) | Public | `backend/app/modules/health/routes.py` |

---

## 2. Authentification & Sessions (`/auth`)

| Méthode | Route | Description | Auth / Rôle | Corps de Requête | Réponse / Modèle | Fichier Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Inscription d'un nouvel utilisateur (`CUSTOMER` ou `SELLER`) | Public | `UserRegisterRequest` (`email`, `password`, `first_name`, `last_name`, `role`) | `UserResponse` (HTTP 201) | `backend/app/modules/auth/routes.py` |
| `POST` | `/api/v1/auth/login` | Connexion par identifiants et génération de token JWT | Public | `UserLoginRequest` (`email`, `password`) | `TokenResponse` (`access_token`, `token_type: "bearer"`) | `backend/app/modules/auth/routes.py` |
| `GET` | `/api/v1/auth/me` | Informations de session de l'utilisateur authentifié | Requis (Tous rôles) | Aucun | `UserResponse` | `backend/app/modules/auth/routes.py` |

---

## 3. Profil Utilisateur (`/users`)

| Méthode | Route | Description | Auth / Rôle | Corps de Requête | Réponse / Modèle | Fichier Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users/me` | Consultation du profil personnel | Requis (Tous rôles) | Aucun | `UserResponse` | `backend/app/modules/users/routes.py` |
| `PATCH` | `/api/v1/users/me` | Mise à jour des coordonnées personnelles | Requis (Tous rôles) | `UserUpdateRequest` (`first_name`, `last_name`) | `UserResponse` | `backend/app/modules/users/routes.py` |

---

## 4. Catalogue : Marques, Catégories, Produits (`/brands`, `/categories`, `/products`)

| Méthode | Route | Description | Auth / Rôle | Corps de Requête / Paramètres | Réponse | Fichier Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/brands` | Liste des marques de créateurs | Public | `page`, `page_size` | `List[BrandResponse]` | `app/modules/catalog/routes/brands.py` |
| `POST` | `/api/v1/brands` | Enregistrement d'une nouvelle marque | `SELLER` ou `ADMIN` | `BrandCreate` (`name`, `description`, `website_url`) | `BrandResponse` | `app/modules/catalog/routes/brands.py` |
| `GET` | `/api/v1/categories` | Arborescence taxonomique des collections | Public | `parent_id` (optionnel) | `List[CategoryResponse]` | `app/modules/catalog/routes/categories.py` |
| `POST` | `/api/v1/categories` | Création d'une catégorie | `ADMIN` uniquement | `CategoryCreate` (`name`, `slug`, `parent_id`) | `CategoryResponse` | `app/modules/catalog/routes/categories.py` |
| `GET` | `/api/v1/products` | Consultation des pièces actives | Public | `category_id`, `brand_id`, `status`, pagination | `List[ProductResponse]` | `app/modules/catalog/routes/products.py` |
| `POST` | `/api/v1/products` | Publication d'une pièce par un créateur | `SELLER` uniquement | `ProductCreate` (nom, prix, variantes, marque) | `ProductResponse` | `app/modules/catalog/routes/products.py` |
| `GET` | `/api/v1/products/{id}` | Détail complet d'une pièce avec variantes | Public | `{id}` (UUID) | `ProductResponse` | `app/modules/catalog/routes/products.py` |
| `PATCH` | `/api/v1/products/{id}` | Mise à jour d'une pièce | Propriétaire `SELLER` | `ProductUpdate` | `ProductResponse` | `app/modules/catalog/routes/products.py` |
| `POST` | `/api/v1/products/{id}/media` | Téléversement d'image ou lookbook | Propriétaire `SELLER` | Multipart Form Data (`file`, `media_type`) | `ProductMediaResponse` | `app/modules/catalog/routes/products.py` |

---

## 5. Moteur de Recherche & Découverte (`/search`)

| Méthode | Route | Description | Auth / Rôle | Paramètres de Requête (Query) | Réponse | Fichier Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/search/products` | Recherche multicritère avec facettes | Public | `q`, `category_id`, `brand_id`, `min_price`, `max_price`, `size`, `color`, `in_stock`, `sort`, `page`, `page_size` | `SearchProductsResponse` (`items`, `total`, `total_pages`, `has_next`) | `backend/app/modules/search/routes.py` |
| `GET` | `/api/v1/search/filters` | Agrégat des options et filtres disponibles | Public | Aucun | `SearchFilterOptionsResponse` (catégories, marques, tailles, couleurs, min/max prix) | `backend/app/modules/search/routes.py` |

---

## 6. Panier d'Achat (`/cart`)

| Méthode | Route | Description | Auth / Rôle | Corps de Requête | Réponse | Fichier Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/cart` | Consultation du panier de l'utilisateur | `CUSTOMER` requis | Aucun | `CartResponse` (`items`, `subtotal`, `currency`) | `backend/app/modules/cart/routes.py` |
| `POST` | `/api/v1/cart/items` | Ajout d'une variante de pièce au panier | `CUSTOMER` requis | `AddToCartRequest` (`variant_id`, `quantity`) | `CartResponse` | `backend/app/modules/cart/routes.py` |
| `PATCH` | `/api/v1/cart/items/{item_id}` | Ajustement de quantité d'un article | `CUSTOMER` requis | `UpdateCartItemRequest` (`quantity`) | `CartResponse` | `backend/app/modules/cart/routes.py` |
| `DELETE` | `/api/v1/cart/items/{item_id}` | Suppression d'un article du panier | `CUSTOMER` requis | Aucun | `CartResponse` | `backend/app/modules/cart/routes.py` |
| `DELETE` | `/api/v1/cart` | Vidage complet du panier | `CUSTOMER` requis | Aucun | `CartResponse` | `backend/app/modules/cart/routes.py` |

---

## 7. Commandes & Sous-Commandes (`/orders`)

| Méthode | Route | Description | Auth / Rôle | Corps / Paramètres | Réponse | Fichier Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/orders/checkout` | Réservation atomique de stock & création de commande | `CUSTOMER` requis | Aucun | `OrderResponse` (`id`, `order_number`, `status: PENDING_PAYMENT`, `sub_orders`) | `backend/app/modules/orders/routes.py` |
| `GET` | `/api/v1/orders` | Historique personnel des commandes du client | `CUSTOMER` requis | Pagination | `List[OrderResponse]` | `backend/app/modules/orders/routes.py` |
| `GET` | `/api/v1/orders/{id}` | Détail d'une commande client (colis, tracking) | Propriétaire `CUSTOMER` | `{id}` | `OrderResponse` | `backend/app/modules/orders/routes.py` |
| `POST` | `/api/v1/orders/{id}/cancel` | Annulation & restitution du stock réservé | Propriétaire `CUSTOMER` | `{id}` | `OrderResponse` | `backend/app/modules/orders/routes.py` |
| `GET` | `/api/v1/orders/admin/orders` | Supervision administrative de toutes les commandes | `ADMIN` requis | Pagination, statut, client | `List[OrderResponse]` | `backend/app/modules/orders/routes.py` |
| `GET` | `/api/v1/orders/admin/orders/{order_id}` | Détail de commande pour audit administrateur | `ADMIN` requis | `{order_id}` | `OrderResponse` | `backend/app/modules/orders/routes.py` |

---

## 8. Passerelle de Paiement PayPal Sandbox (`/payments`)

| Méthode | Route | Description | Auth / Rôle | Corps de Requête | Réponse | Fichier Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/payments/paypal/create-order` | Initialisation de la transaction PayPal pour un `order_id` | `CUSTOMER` requis | `CreatePayPalOrderRequest` (`order_id`) | `PayPalOrderResponse` (`paypal_order_id`) | `backend/app/modules/payments/routes.py` |
| `POST` | `/api/v1/payments/paypal/capture-order` | Capture côté serveur & décrémentation finale de stock | `CUSTOMER` requis | `CapturePayPalOrderRequest` (`paypal_order_id`) | `PayPalCaptureResponse` (`order_id`, `status: COMPLETED`) | `backend/app/modules/payments/routes.py` |
| `POST` | `/api/v1/payments/paypal/cancel-order` | Annulation transactionnelle PayPal & restauration de stock | `CUSTOMER` requis | `CancelPayPalOrderRequest` (`paypal_order_id`) | `Dict[str, str]` | `backend/app/modules/payments/routes.py` |
| `POST` | `/api/v1/payments/paypal/webhook` | Réception asynchrone des événements de paiement PayPal | Signature PayPal | Payload webhook brut | `Dict[str, str]` (HTTP 200) | `backend/app/modules/payments/routes.py` |

---

## 9. Espace Vendeur & Boutiques Publiques (`/seller`, `/stores`)

| Méthode | Route | Description | Auth / Rôle | Corps / Paramètres | Réponse | Fichier Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/seller/dashboard` | Métriques de vente, alertes de stock faible du créateur | `SELLER` requis | Aucun | `SellerDashboardResponse` | `backend/app/modules/seller/routes.py` |
| `GET` | `/api/v1/seller/products` | Gestion des pièces du créateur connecté | `SELLER` requis | Pagination, statut | `List[ProductResponse]` | `backend/app/modules/seller/routes.py` |
| `GET` | `/api/v1/seller/inventory` | Vue tabulaire des niveaux de stock par SKU | `SELLER` requis | Pagination | `List[InventoryItemResponse]` | `backend/app/modules/seller/routes.py` |
| `GET` | `/api/v1/seller/orders` | Sous-commandes (`SubOrder`) assignées au vendeur | `SELLER` requis | Pagination | `List[SellerOrderResponse]` | `backend/app/modules/seller/routes.py` |
| `PATCH` | `/api/v1/seller/orders/{order_id}/fulfillment` | Mise à jour de l'expédition (transporteur, tracking) | `SELLER` assigné | `SellerFulfillmentRequest` (`status`, `carrier`, `tracking_number`) | `SellerOrderResponse` | `backend/app/modules/seller/routes.py` |
| `GET` | `/api/v1/seller/store` | Récupération du profil de boutique du vendeur | `SELLER` requis | Aucun | `SellerStoreResponse` | `backend/app/modules/seller/routes.py` |
| `POST` | `/api/v1/seller/store` | Création de la boutique (nom, slug, bio) | `SELLER` requis | `StoreCreateRequest` | `SellerStoreResponse` | `backend/app/modules/seller/routes.py` |
| `PATCH` | `/api/v1/seller/store` | Modification du profil de boutique | `SELLER` requis | `StoreUpdateRequest` | `SellerStoreResponse` | `backend/app/modules/seller/routes.py` |
| `POST` | `/api/v1/seller/store/media` | Téléversement logo ou bannière de boutique | `SELLER` requis | Multipart (`file`, `asset_type: logo|banner`) | `StoreMediaResponse` | `backend/app/modules/seller/routes.py` |
| `GET` | `/api/v1/stores/{slug}` | Consultation publique d'une vitrine de créateur | Public | `{slug}` | `PublicStoreResponse` | `backend/app/modules/stores/routes.py` |
| `GET` | `/api/v1/stores/{slug}/products` | Catalogue public paginé d'une boutique | Public | `sort_by`, `page`, `page_size` | `PublicStoreProductsResponse` | `backend/app/modules/stores/routes.py` |

---

## 10. Plateforme d'Administration & Modération (`/admin`)

| Méthode | Route | Description | Auth / Rôle | Corps / Paramètres | Réponse | Fichier Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/dashboard` | Tour de contrôle globale (GMV, volumes, boutiques) | `ADMIN` requis | Aucun | `AdminDashboardResponse` | `backend/app/modules/admin/routes.py` |
| `GET` | `/api/v1/admin/stores` | Liste des boutiques avec filtres de modération | `ADMIN` requis | `status`, `is_verified`, `q`, pagination | `AdminStoreListResponse` | `backend/app/modules/admin/routes.py` |
| `GET` | `/api/v1/admin/stores/{store_id}` | Détail d'une boutique pour audit | `ADMIN` requis | `{store_id}` | `AdminStoreDetailResponse` | `backend/app/modules/admin/routes.py` |
| `PATCH` | `/api/v1/admin/stores/{store_id}/moderation` | Modération du statut ou du badge certifié | `ADMIN` requis | `AdminStoreModerationUpdate` (`status`, `is_verified`) | `AdminStoreDetailResponse` | `backend/app/modules/admin/routes.py` |
| `GET` | `/api/v1/admin/users` | Gestion administrative des utilisateurs | `ADMIN` requis | `role`, `is_active`, `q`, pagination | `AdminUserListResponse` | `backend/app/modules/admin/routes.py` |
| `GET` | `/api/v1/admin/users/{user_id}` | Profil détaillé d'un utilisateur et boutique liée | `ADMIN` requis | `{user_id}` | `AdminUserDetailResponse` | `backend/app/modules/admin/routes.py` |
| `PATCH` | `/api/v1/admin/users/{user_id}/status` | Activation / suspension d'un compte (avec garde) | `ADMIN` requis | `AdminUserStatusUpdate` (`is_active`) | `AdminUserSummaryResponse` | `backend/app/modules/admin/routes.py` |
