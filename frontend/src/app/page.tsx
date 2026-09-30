"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShoppingBag,
  Sparkles,
  Check,
  Tag,
  Layers,
  AlertCircle,
  ArrowRight,
  TrendingUp,
  ShieldCheck
} from "lucide-react";
import { api, Product, ProductVariant } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function CatalogPage() {
  const { user, quickCustomerLogin, refreshCartCount, cartCount } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected variant map: { [productId]: variantId }
  const [selectedVariants, setSelectedVariants] = useState<Record<string, string>>({});
  const [addingId, setAddingId] = useState<string | null>(null);
  const [addedSuccessId, setAddedSuccessId] = useState<string | null>(null);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getProducts();
      setProducts(data);
      // Pre-select first variant for each product
      const initialVariants: Record<string, string> = {};
      data.forEach((p) => {
        if (p.variants && p.variants.length > 0) {
          initialVariants[p.id] = p.variants[0].id;
        }
      });
      setSelectedVariants(initialVariants);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load products");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleAddToCart = async (product: Product) => {
    const variantId = selectedVariants[product.id];
    if (!variantId) return;

    if (!user) {
      await quickCustomerLogin();
    }

    setAddingId(variantId);
    try {
      await api.addToCart(variantId, 1);
      await refreshCartCount();
      setAddedSuccessId(variantId);
      setTimeout(() => setAddedSuccessId(null), 2000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to add to cart");
    } finally {
      setAddingId(null);
    }
  };

  return (
    <main className="min-h-screen pb-20">
      {/* Hero Header */}
      <section className="relative overflow-hidden border-b border-slate-800/80 bg-gradient-to-b from-slate-900/60 via-slate-950 to-slate-950 py-16 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.15),rgba(255,255,255,0))]"></div>
        <div className="relative max-w-7xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-sm">
            <Sparkles className="w-3.5 h-3.5" />
            Phase 5: Real PayPal Sandbox Integration & Inventory Lifecycle
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white">
            Curated Fashion Marketplace
          </h1>
          <p className="max-w-2xl mx-auto text-slate-400 text-sm sm:text-base leading-relaxed">
            Experience end-to-end atomic checkout with stock reservation, PayPal Sandbox payment capture, and automated inventory reconciliation.
          </p>

          <div className="pt-4 flex flex-wrap items-center justify-center gap-4 text-xs text-slate-300">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Row-Level Locked Stock
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800">
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              PayPal Sandbox Verified
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800">
              <Layers className="w-4 h-4 text-violet-400" />
              Modular Monolith Backend
            </span>
          </div>
        </div>
      </section>

      {/* Main Catalog Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">Active Listings</h2>
            <p className="text-xs text-slate-400 mt-1">
              Select a size/color variant and add to cart to test the full payment lifecycle.
            </p>
          </div>

          {cartCount > 0 && (
            <Link
              href="/checkout"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-sm shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02]"
            >
              <ShoppingBag className="w-4 h-4" />
              <span>Checkout ({cartCount} {cartCount === 1 ? "item" : "items"})</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>

        {/* Loading / Error States */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-96 rounded-2xl bg-slate-900/50 border border-slate-800" />
            ))}
          </div>
        )}

        {error && (
          <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-300 text-sm flex items-start gap-4">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-white">Could not fetch catalog products</p>
              <p className="text-xs text-red-300/80 mt-1">{error}</p>
              <button
                onClick={fetchProducts}
                className="mt-3 px-3 py-1.5 rounded-lg bg-red-500/20 text-red-200 text-xs font-medium hover:bg-red-500/30"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Empty Catalog Notice */}
        {!loading && !error && products.length === 0 && (
          <div className="text-center py-16 px-4 rounded-3xl bg-slate-900/30 border border-slate-800 max-w-lg mx-auto space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto">
              <ShoppingBag className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white">No active products in catalog yet</h3>
            <p className="text-xs text-slate-400">
              Run database seeds or create products via the seller catalog API to browse fashion variants.
            </p>
          </div>
        )}

        {/* Product Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((product) => {
            const activeVariants = (product.variants || []).filter((v) => v.is_active);
            const currentVariantId = selectedVariants[product.id] || (activeVariants[0]?.id ?? "");
            const currentVariant = activeVariants.find((v) => v.id === currentVariantId) || activeVariants[0];
            const isAdding = addingId === currentVariant?.id;
            const isAdded = addedSuccessId === currentVariant?.id;
            const availableStock = currentVariant?.inventory?.quantity_available ?? 0;

            return (
              <div
                key={product.id}
                className="group flex flex-col justify-between rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all p-5 hover:shadow-xl hover:shadow-indigo-950/20 backdrop-blur-sm"
              >
                <div>
                  {/* Visual / Thumbnail fallback banner */}
                  <div className="w-full h-48 rounded-xl bg-gradient-to-tr from-slate-800 via-indigo-950/40 to-slate-800 border border-slate-800/80 flex flex-col justify-between p-4 relative overflow-hidden group-hover:border-indigo-500/30 transition-colors">
                    <div className="flex items-center justify-between z-10">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-black/60 text-slate-300 backdrop-blur border border-white/10">
                        {product.brand?.name || "Originals"}
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        Active Listing
                      </span>
                    </div>

                    <div className="z-10">
                      <p className="text-xl font-black text-white group-hover:text-indigo-200 transition-colors">
                        ${currentVariant ? currentVariant.price : product.base_price}
                      </p>
                      <span className="text-[11px] text-slate-400">USD Authorized</span>
                    </div>

                    {/* Subtle aesthetic backdrop blur element */}
                    <div className="absolute -bottom-8 -right-8 w-32 h-32 bg-indigo-600/10 rounded-full blur-2xl group-hover:bg-indigo-600/20 transition-all"></div>
                  </div>

                  {/* Product Details */}
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center gap-2 text-xs text-indigo-400 font-medium">
                      <Tag className="w-3.5 h-3.5" />
                      <span>{product.category?.name || "Fashion"}</span>
                    </div>
                    <h3 className="text-base font-bold text-white line-clamp-1">{product.name}</h3>
                    {product.description && (
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {product.description}
                      </p>
                    )}
                  </div>

                  {/* Variant Selector */}
                  {activeVariants.length > 0 && (
                    <div className="mt-4 space-y-1.5">
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                        Select Variant ({activeVariants.length})
                      </label>
                      <div className="flex flex-wrap gap-1.5">
                        {activeVariants.map((v) => {
                          const isSelected = v.id === currentVariantId;
                          return (
                            <button
                              key={v.id}
                              onClick={() =>
                                setSelectedVariants((prev) => ({ ...prev, [product.id]: v.id }))
                              }
                              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                                isSelected
                                  ? "bg-indigo-600 border-indigo-500 text-white shadow-sm"
                                  : "bg-slate-800/80 border-slate-700/60 text-slate-300 hover:border-slate-600"
                              }`}
                            >
                              {v.size || v.color ? `${v.size || ""} ${v.color || ""}`.trim() : v.sku}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                {/* Stock & Action Bar */}
                <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between gap-3">
                  <div className="text-xs">
                    <span className="text-slate-400 block text-[10px] uppercase">Availability</span>
                    <span className="font-semibold text-emerald-400">
                      {availableStock > 0 ? `${availableStock} in stock` : "Available"}
                    </span>
                  </div>

                  <button
                    onClick={() => handleAddToCart(product)}
                    disabled={isAdding}
                    className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all shadow-md ${
                      isAdded
                        ? "bg-emerald-600 text-white"
                        : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20 active:scale-95"
                    }`}
                  >
                    {isAdded ? (
                      <>
                        <Check className="w-4 h-4" />
                        <span>Added</span>
                      </>
                    ) : (
                      <>
                        <ShoppingBag className="w-4 h-4" />
                        <span>{isAdding ? "Adding..." : "Add to Cart"}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
