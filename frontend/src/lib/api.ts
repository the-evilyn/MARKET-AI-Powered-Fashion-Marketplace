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
  name: string;
  slug: string;
  description?: string;
  base_price: string;
  status: "DRAFT" | "ACTIVE" | "ARCHIVED";
  brand?: { id: string; name: string };
  category?: { id: string; name: string };
  variants: ProductVariant[];
  media?: { id: string; url: string; alt_text?: string; is_primary: boolean }[];
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
  variant_id?: string;
  product_name: string;
  sku: string;
  unit_price: string;
  quantity: number;
  line_total: string;
  created_at: string;
}

export interface Order {
  id: string;
  customer_id: string;
  order_number: string;
  status: "PENDING_PAYMENT" | "CONFIRMED" | "CANCELLED";
  subtotal: string;
  total: string;
  currency: string;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
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
  async login(formData: URLSearchParams | { username: string; password: string }) {
    const body = new URLSearchParams();
    if (formData instanceof URLSearchParams) {
      formData.forEach((val, key) => body.append(key, val));
    } else {
      body.append("username", formData.username);
      body.append("password", formData.password);
    }

    const res = await fetch(`${API_BASE_URL}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.detail || "Authentication failed");
    }
    return res.json(); // { access_token, token_type }
  },

  async register(data: { email: string; password: string; first_name?: string; last_name?: string; role?: string }) {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getMe(): Promise<User> {
    return request<User>("/auth/me");
  },

  // Products
  async getProducts(): Promise<Product[]> {
    return request<Product[]>("/products");
  },

  async getProduct(id: string): Promise<Product> {
    return request<Product>(`/products/${id}`);
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
};
