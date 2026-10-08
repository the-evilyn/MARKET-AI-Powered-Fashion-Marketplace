// Frontend API Client for AI Fashion Marketplace

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface User {
  id: string;
  email: string;
  role: "CUSTOMER" | "SELLER" | "ADMIN";
  first_name?: string;
  last_name?: string;
}

export interface ProductVariant {
  id: string;
  product_id: string;
  sku: string;
  price: string;
  compare_at_price?: string;
  size?: string;
  color?: string;
  is_active: boolean;
  is_in_stock?: boolean;
  inventory?: {
    quantity_on_hand: number;
    quantity_reserved: number;
    quantity_available: number;
    is_in_stock: boolean;
    is_low_stock: boolean;
  };
}

export interface Product {
  id: string;
  seller_id?: string;
  name: string;
  slug: string;
  description?: string;
  base_price: string;
  currency?: string;
  status: "DRAFT" | "ACTIVE" | "ARCHIVED";
  is_active?: boolean;
  brand?: { id: string; name: string; slug?: string };
  category?: { id: string; name: string; slug?: string };
  variants: ProductVariant[];
  media?: { id: string; url: string; alt_text?: string; is_primary: boolean }[];
  is_in_stock?: boolean;
}

export interface SearchFilterOption {
  id: string;
  name: string;
  slug: string;
}

export interface SearchFiltersResponse {
  categories: SearchFilterOption[];
  brands: SearchFilterOption[];
  sizes: string[];
  colors: string[];
  min_price: string | number;
  max_price: string | number;
}

export interface SearchProductsResponse {
  items: Product[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface SearchQueryParams {
  q?: string;
  category_id?: string;
  brand_id?: string;
  min_price?: number | string;
  max_price?: number | string;
  size?: string;
  color?: string;
  in_stock?: boolean;
  sort?: "relevance" | "price_asc" | "price_desc" | "newest" | "oldest" | "name_asc" | "name_desc";
  page?: number;
  page_size?: number;
}

export interface CartItem {
  id: string;
  cart_id: string;
  variant_id: string;
  quantity: number;
  unit_price: string;
  line_total: string;
  variant?: {
    sku: string;
    price: string;
    product?: {
      name: string;
    };
  };
}

export interface Cart {
  id: string;
  customer_id: string;
  status: string;
  subtotal: string;
  items: CartItem[];
}

export interface OrderItem {
  id: string;
  order_id: string;
  sub_order_id?: string;
  seller_id?: string;
  variant_id?: string;
  product_name: string;
  sku: string;
  unit_price: string;
  quantity: number;
  line_total: string;
  created_at: string;
}

export interface SubOrder {
  id: string;
  order_id: string;
  seller_id: string;
  sub_order_number: string;
  status: "PENDING_PAYMENT" | "CONFIRMED" | "PROCESSING" | "SHIPPED" | "DELIVERED" | "CANCELLED" | string;
  subtotal: string;
  shipping_amount: string;
  total: string;
  currency: string;
  carrier?: string | null;
  tracking_number?: string | null;
  shipped_at?: string | null;
  delivered_at?: string | null;
  created_at: string;
  updated_at: string;
  items?: OrderItem[];
}

export interface Order {
  id: string;
  customer_id: string;
  order_number: string;
  status: "PENDING_PAYMENT" | "CONFIRMED" | "PROCESSING" | "SHIPPED" | "DELIVERED" | "CANCELLED" | string;
  subtotal: string;
  total: string;
  currency: string;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
  sub_orders?: SubOrder[];
  payment_status?: string | null;
  payment_provider?: string | null;
}

export interface PayPalCreateOrderResponse {
  payment_id: string;
  paypal_order_id: string;
  amount: string;
  currency: string;
  provider: string;
}

export interface PayPalCaptureResponse {
  payment_id: string;
  order_id: string;
  order_number: string;
  status: string;
  order_status: string;
  provider_order_id: string;
  provider_payment_id?: string;
  amount: string;
  currency: string;
}

export interface PayPalCancelResponse {
  payment_id: string;
  order_id: string;
  order_number: string;
  status: string;
  order_status: string;
}

export interface SellerDashboardKPIs {
  total_products: number;
  active_products: number;
  total_variants: number;
  low_stock_variants: number;
  out_of_stock_variants: number;
  total_orders: number;
  pending_orders: number;
  confirmed_orders: number;
  cancelled_orders: number;
  total_sales: string | number;
  total_items_sold: number;
}

export interface SellerInventoryItem {
  id: string;
  variant_id: string;
  product_id: string;
  product_name: string;
  sku: string;
  color?: string;
  size?: string;
  price: string;
  compare_at_price?: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  low_stock_threshold: number;
  is_in_stock: boolean;
  is_low_stock: boolean;
  is_active: boolean;
  updated_at: string;
}

export interface SellerOrderItem {
  id: string;
  order_id: string;
  variant_id?: string;
  product_name: string;
  sku: string;
  color?: string;
  size?: string;
  unit_price: string;
  quantity: number;
  line_total: string;
  created_at: string;
}

export interface SellerOrder {
  id: string;
  order_number: string;
  sub_order_id?: string | null;
  sub_order_number?: string | null;
  created_at: string;
  status: "PENDING_PAYMENT" | "CONFIRMED" | "PROCESSING" | "SHIPPED" | "DELIVERED" | "CANCELLED" | string;
  currency: string;
  seller_subtotal: string;
  seller_total_quantity: number;
  payment_status?: string | null;
  carrier?: string | null;
  tracking_number?: string | null;
  shipped_at?: string | null;
  delivered_at?: string | null;
  items: SellerOrderItem[];
}

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const message = errorData?.detail || `HTTP Error ${response.status}: ${response.statusText}`;
    throw new Error(message);
  }

  return response.json();
}

export const api = {
  // Auth
  async login(formData: URLSearchParams | { email?: string; username?: string; password: string }) {
    let email = "";
    let password = "";
    if (formData instanceof URLSearchParams) {
      email = formData.get("email") || formData.get("username") || "";
      password = formData.get("password") || "";
    } else {
      email = formData.email || formData.username || "";
      password = formData.password || "";
    }

    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.detail || err?.message || "Authentication failed");
    }
    const data = await res.json();
    if (data.access_token && typeof window !== "undefined") {
      localStorage.setItem("token", data.access_token);
    }
    return data; // { access_token, refresh_token, token_type, expires_in }
  },

  async register(data: { email: string; password: string; first_name?: string; last_name?: string; role?: string }) {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.detail || err?.message || "Registration failed");
    }
    const tokenData = await res.json();
    if (tokenData.access_token && typeof window !== "undefined") {
      localStorage.setItem("token", tokenData.access_token);
    }
    return tokenData;
  },

  async getMe(): Promise<User> {
    return request<User>("/users/me");
  },

  // Media Management
  async uploadProductMedia(
    productId: string,
    file: File,
    options?: { alt_text?: string; sort_order?: number; is_primary?: boolean }
  ) {
    const token = getStoredToken();
    const formData = new FormData();
    formData.append("file", file);
    if (options?.alt_text) formData.append("alt_text", options.alt_text);
    if (options?.sort_order !== undefined) formData.append("sort_order", String(options.sort_order));
    if (options?.is_primary !== undefined) formData.append("is_primary", String(options.is_primary));

    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE_URL}/products/${productId}/media/upload`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.detail || err?.message || "Failed to upload image");
    }
    return res.json();
  },

  async deleteProductMedia(productId: string, mediaId: string) {
    return request(`/products/${productId}/media/${mediaId}`, {
      method: "DELETE",
    });
  },

  // Seller Fulfillment
  async updateSellerFulfillment(
    orderId: string,
    data: { status?: string; carrier?: string; tracking_number?: string }
  ): Promise<SellerOrder> {
    return request<SellerOrder>(`/seller/orders/${orderId}/fulfillment`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  // Products
  async getProducts(): Promise<Product[]> {
    return request<Product[]>("/products");
  },

  async getProduct(id: string): Promise<Product> {
    return request<Product>(`/products/${id}`);
  },

  // Discovery & Search
  async searchProducts(params: SearchQueryParams = {}): Promise<SearchProductsResponse> {
    const searchParams = new URLSearchParams();
    if (params.q?.trim()) searchParams.set("q", params.q.trim());
    if (params.category_id) searchParams.set("category_id", params.category_id);
    if (params.brand_id) searchParams.set("brand_id", params.brand_id);
    if (params.min_price !== undefined && params.min_price !== "") searchParams.set("min_price", String(params.min_price));
    if (params.max_price !== undefined && params.max_price !== "") searchParams.set("max_price", String(params.max_price));
    if (params.size?.trim()) searchParams.set("size", params.size.trim());
    if (params.color?.trim()) searchParams.set("color", params.color.trim());
    if (params.in_stock !== undefined && params.in_stock !== null) searchParams.set("in_stock", String(params.in_stock));
    if (params.sort) searchParams.set("sort", params.sort);
    if (params.page) searchParams.set("page", String(params.page));
    if (params.page_size) searchParams.set("page_size", String(params.page_size));

    const qs = searchParams.toString();
    return request<SearchProductsResponse>(`/search/products${qs ? `?${qs}` : ""}`);
  },

  async getSearchFilters(): Promise<SearchFiltersResponse> {
    return request<SearchFiltersResponse>("/search/filters");
  },

  // Cart
  async getCart(): Promise<Cart> {
    return request<Cart>("/cart");
  },

  async addToCart(variantId: string, quantity: number = 1): Promise<CartItem> {
    return request<CartItem>("/cart/items", {
      method: "POST",
      body: JSON.stringify({ variant_id: variantId, quantity }),
    });
  },

  async removeFromCart(itemId: string): Promise<void> {
    return request<void>(`/cart/items/${itemId}`, {
      method: "DELETE",
    });
  },

  async clearCart(): Promise<void> {
    return request<void>("/cart", {
      method: "DELETE",
    });
  },

  // Checkout
  async checkout(): Promise<Order> {
    return request<Order>("/checkout", {
      method: "POST",
    });
  },

  // Payments
  async createPayPalOrder(orderId: string): Promise<PayPalCreateOrderResponse> {
    return request<PayPalCreateOrderResponse>("/payments/paypal/create-order", {
      method: "POST",
      body: JSON.stringify({ order_id: orderId }),
    });
  },

  async capturePayPalPayment(paypalOrderId: string): Promise<PayPalCaptureResponse> {
    return request<PayPalCaptureResponse>("/payments/paypal/capture", {
      method: "POST",
      body: JSON.stringify({ paypal_order_id: paypalOrderId }),
    });
  },

  async cancelPayPalPayment(paypalOrderId: string): Promise<PayPalCancelResponse> {
    return request<PayPalCancelResponse>("/payments/paypal/cancel", {
      method: "POST",
      body: JSON.stringify({ paypal_order_id: paypalOrderId }),
    });
  },

  // Orders
  async getOrders(): Promise<Order[]> {
    return request<Order[]>("/orders");
  },

  async getOrder(orderId: string): Promise<Order> {
    return request<Order>(`/orders/${orderId}`);
  },

  // Seller Operations
  async getSellerDashboard(): Promise<SellerDashboardKPIs> {
    return request<SellerDashboardKPIs>("/seller/dashboard");
  },

  async getSellerProducts(params?: { status?: string; is_active?: boolean }): Promise<Product[]> {
    const q = new URLSearchParams();
    if (params?.status) q.append("status", params.status);
    if (params?.is_active !== undefined) q.append("is_active", String(params.is_active));
    const qs = q.toString() ? `?${q.toString()}` : "";
    return request<Product[]>(`/seller/products${qs}`);
  },

  async getSellerProduct(id: string): Promise<Product> {
    return request<Product>(`/seller/products/${id}`);
  },

  async createSellerProduct(data: {
    name: string;
    base_price: string;
    slug?: string;
    description?: string;
    status?: string;
    brand_id?: string;
    category_id?: string;
  }): Promise<Product> {
    return request<Product>("/seller/products", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateSellerProduct(
    id: string,
    data: {
      name?: string;
      base_price?: string;
      description?: string;
      status?: string;
      is_active?: boolean;
    }
  ): Promise<Product> {
    return request<Product>(`/seller/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async deleteSellerProduct(id: string): Promise<void> {
    const token = getStoredToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE_URL}/seller/products/${id}`, {
      method: "DELETE",
      headers,
    });
    if (!res.ok && res.status !== 204) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.detail || `Delete failed with status ${res.status}`);
    }
  },

  async createSellerVariant(
    productId: string,
    data: {
      sku: string;
      price: string;
      compare_at_price?: string;
      color?: string;
      size?: string;
      is_active?: boolean;
    }
  ): Promise<ProductVariant> {
    return request<ProductVariant>(`/seller/products/${productId}/variants`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateSellerVariant(
    productId: string,
    variantId: string,
    data: {
      sku?: string;
      price?: string;
      compare_at_price?: string;
      color?: string;
      size?: string;
      is_active?: boolean;
    }
  ): Promise<ProductVariant> {
    return request<ProductVariant>(`/seller/products/${productId}/variants/${variantId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async deleteSellerVariant(productId: string, variantId: string): Promise<void> {
    const token = getStoredToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE_URL}/seller/products/${productId}/variants/${variantId}`, {
      method: "DELETE",
      headers,
    });
    if (!res.ok && res.status !== 204) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.detail || `Delete failed with status ${res.status}`);
    }
  },

  async getSellerInventory(lowStockOnly: boolean = false): Promise<SellerInventoryItem[]> {
    const qs = lowStockOnly ? "?low_stock_only=true" : "";
    return request<SellerInventoryItem[]>(`/seller/inventory${qs}`);
  },

  async updateSellerInventory(
    variantId: string,
    data: { quantity_on_hand?: number; low_stock_threshold?: number }
  ): Promise<SellerInventoryItem> {
    return request<SellerInventoryItem>(`/seller/inventory/${variantId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async adjustSellerInventory(
    variantId: string,
    data: { adjustment: number; reason?: string }
  ): Promise<SellerInventoryItem> {
    return request<SellerInventoryItem>(`/seller/inventory/${variantId}/adjust`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getSellerOrders(status?: string): Promise<SellerOrder[]> {
    const qs = status ? `?status=${status}` : "";
    return request<SellerOrder[]>(`/seller/orders${qs}`);
  },

  async getSellerOrder(orderId: string): Promise<SellerOrder> {
    return request<SellerOrder>(`/seller/orders/${orderId}`);
  },
};
