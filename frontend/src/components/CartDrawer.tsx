"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  X,
  ShoppingBag,
  Trash2,
  Plus,
  Minus,
  ArrowRight,
  ShieldCheck,
  Truck,
  Sparkles,
  Loader2,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api, Cart, CartItem } from "@/lib/api";

export default function CartDrawer() {
  const router = useRouter();
  const { isCartOpen, closeCart, user, refreshCartCount, quickCustomerLogin } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchCart = useCallback(async () => {
    if (!user) {
      setCart(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCart();
      setCart(data);
    } catch (err: unknown) {
      console.error("Failed to load cart in drawer", err);
      setError(err instanceof Error ? err.message : "Erreur de chargement du panier");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (isCartOpen) {
      fetchCart();
    }
  }, [isCartOpen, fetchCart]);

  const handleUpdateQuantity = async (itemId: string, newQty: number) => {
    if (newQty < 1) {
      await handleRemoveItem(itemId);
      return;
    }
    setUpdatingId(itemId);
    try {
      await api.updateCartItem(itemId, newQty);
      await fetchCart();
      await refreshCartCount();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Échec de la mise à jour");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    setUpdatingId(itemId);
    try {
      await api.removeFromCart(itemId);
      await fetchCart();
      await refreshCartCount();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Échec de la suppression");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleCheckoutClick = () => {
    closeCart();
    router.push("/checkout");
  };

  if (!isCartOpen) return null;

  const items = cart?.items || [];
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity"
        onClick={closeCart}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-[#090d16] border-l border-stone-800/80 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-stone-800/80 flex items-center justify-between bg-[#0b101c]/80">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                <ShoppingBag className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-base font-serif font-medium tracking-wide text-stone-100">
                  Votre Sélection
                </h2>
                <p className="text-[11px] text-stone-400">
                  {itemCount} {itemCount > 1 ? "articles" : "article"} dans le panier
                </p>
              </div>
            </div>
            <button
              onClick={closeCart}
              className="p-2 rounded-xl text-stone-400 hover:text-stone-100 hover:bg-stone-800/60 transition-colors"
              aria-label="Fermer le panier"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {loading && !cart ? (
              <div className="h-64 flex flex-col items-center justify-center text-stone-400 gap-3">
                <Loader2 className="w-6 h-6 animate-spin text-amber-400" />
                <span className="text-xs">Chargement de votre panier...</span>
              </div>
            ) : error ? (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {error}
              </div>
            ) : !user ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="w-16 h-16 rounded-full bg-stone-900 border border-stone-800 flex items-center justify-center text-amber-400">
                  <ShoppingBag className="w-7 h-7" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-base font-serif text-stone-200">Connexion requise</h3>
                  <p className="text-xs text-stone-400 max-w-xs leading-relaxed">
                    Connectez-vous pour retrouver votre sélection sauvegardée et finaliser vos commandes en toute sécurité.
                  </p>
                </div>
                <div className="flex flex-col gap-2 w-full max-w-xs pt-2">
                  <button
                    onClick={async () => {
                      await quickCustomerLogin();
                    }}
                    className="w-full py-2.5 px-4 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 text-xs font-semibold tracking-wider uppercase transition-all shadow-lg shadow-amber-400/10 flex items-center justify-center gap-2"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Connexion Client Démo</span>
                  </button>
                  <button
                    onClick={closeCart}
                    className="w-full py-2 px-4 rounded-xl bg-stone-900 hover:bg-stone-800 text-stone-400 text-xs transition-colors"
                  >
                    Explorer en visiteur
                  </button>
                </div>
              </div>
            ) : items.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="w-16 h-16 rounded-full bg-stone-900 border border-stone-800 flex items-center justify-center text-stone-500">
                  <ShoppingBag className="w-7 h-7" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-base font-serif text-stone-200">Votre panier est vide</h3>
                  <p className="text-xs text-stone-400 max-w-xs leading-relaxed">
                    Découvrez nos créations exclusives et ajoutez vos pièces favorites à votre sélection.
                  </p>
                </div>
                <button
                  onClick={closeCart}
                  className="mt-2 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 text-xs font-semibold tracking-wider uppercase transition-all shadow-lg shadow-amber-400/10"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Explorer les collections</span>
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {items.map((item: CartItem) => {
                  const isUpdating = updatingId === item.id;
                  const unitPrice = parseFloat(item.unit_price || "0");
                  const lineTotal = (unitPrice * item.quantity).toFixed(2);

                  return (
                    <div
                      key={item.id}
                      className="p-4 rounded-xl bg-[#0e1320] border border-stone-800/80 hover:border-stone-700/80 transition-all flex flex-col gap-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-xs font-semibold text-stone-100 truncate">
                            {item.product_name || `Pièce de créateur`}
                          </h4>
                          <div className="flex items-center gap-2 mt-1 text-[11px] text-stone-400">
                            {item.size && (
                              <span className="px-1.5 py-0.5 rounded bg-stone-800/80 border border-stone-700/60 text-stone-300">
                                T: {item.size}
                              </span>
                            )}
                            {item.color && (
                              <span className="px-1.5 py-0.5 rounded bg-stone-800/80 border border-stone-700/60 text-stone-300">
                                {item.color}
                              </span>
                            )}
                            <span className="font-mono text-[10px] text-stone-500 truncate">
                              {item.sku}
                            </span>
                          </div>
                        </div>

                        <button
                          onClick={() => handleRemoveItem(item.id)}
                          disabled={isUpdating}
                          className="text-stone-500 hover:text-rose-400 transition-colors p-1"
                          title="Supprimer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-stone-800/50">
                        {/* Quantity Controls */}
                        <div className="flex items-center gap-2 bg-[#090d16] border border-stone-800 rounded-lg p-1">
                          <button
                            onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                            disabled={isUpdating || item.quantity <= 1}
                            className="w-6 h-6 rounded flex items-center justify-center text-stone-400 hover:text-stone-100 hover:bg-stone-800 disabled:opacity-30 transition-colors"
                          >
                            <Minus className="w-3 h-3" />
                          </button>
                          <span className="text-xs font-semibold text-stone-200 min-w-5 text-center">
                            {isUpdating ? "..." : item.quantity}
                          </span>
                          <button
                            onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                            disabled={isUpdating}
                            className="w-6 h-6 rounded flex items-center justify-center text-stone-400 hover:text-stone-100 hover:bg-stone-800 transition-colors"
                          >
                            <Plus className="w-3 h-3" />
                          </button>
                        </div>

                        {/* Price */}
                        <div className="text-right">
                          <div className="text-xs font-bold text-amber-300 font-mono">
                            ${lineTotal}
                          </div>
                          {item.quantity > 1 && (
                            <div className="text-[10px] text-stone-500">
                              (${unitPrice.toFixed(2)} / unité)
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer with Summary & Checkout */}
          {items.length > 0 && (
            <div className="p-6 border-t border-stone-800/80 bg-[#0b101c]/90 space-y-4">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs text-stone-400">
                  <span>Sous-total estimé</span>
                  <span className="font-mono text-stone-200">${cart?.subtotal || "0.00"}</span>
                </div>
                <div className="flex items-center justify-between text-sm font-semibold text-stone-100 pt-1 border-t border-stone-800/60">
                  <span className="font-serif">Total de la sélection</span>
                  <span className="font-mono text-amber-300 text-base">
                    ${cart?.subtotal || "0.00"}{" "}
                    <span className="text-[10px] font-normal text-stone-400">USD</span>
                  </span>
                </div>
                <p className="text-[10px] text-stone-500 pt-0.5">
                  Frais de port et taxes vérifiés lors de la finalisation.
                </p>
              </div>

              <div className="space-y-2">
                <button
                  onClick={handleCheckoutClick}
                  className="w-full py-3.5 px-4 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 font-semibold text-xs tracking-wider uppercase transition-all shadow-lg shadow-amber-400/10 flex items-center justify-center gap-2 active:scale-[0.99]"
                >
                  <span>Passer à la caisse</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
                <button
                  onClick={closeCart}
                  className="w-full py-2.5 px-4 rounded-xl bg-stone-900 hover:bg-stone-800/80 text-stone-300 text-xs font-medium transition-colors"
                >
                  Continuer mes achats
                </button>
              </div>

              {/* Guarantees */}
              <div className="pt-3 border-t border-stone-800/60 grid grid-cols-2 gap-2 text-[10px] text-stone-400">
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-amber-400/80 shrink-0" />
                  <span>Pièces 100% certifiées</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Truck className="w-3.5 h-3.5 text-amber-400/80 shrink-0" />
                  <span>Livraison sécurisée</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
