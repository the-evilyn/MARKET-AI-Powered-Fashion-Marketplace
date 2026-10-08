"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  ShoppingBag,
  ArrowLeft,
  Tag,
  ShieldCheck,
  Check,
  AlertCircle,
  Truck,
  RotateCcw,
  Sparkles,
  Store,
} from "lucide-react";
import { api, Product, ProductVariant } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

function ProductDetailContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, quickCustomerLogin, refreshCartCount } = useAuth();

  const productId = params?.id as string;
  const returnTo = searchParams.get("returnTo") || "/";

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedVariantId, setSelectedVariantId] = useState<string>("");
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number>(0);
  const [quantity, setQuantity] = useState<number>(1);
  const [isAdding, setIsAdding] = useState(false);
  const [isAdded, setIsAdded] = useState(false);

  useEffect(() => {
    if (!productId) return;
    setLoading(true);
    setError(null);
    api
      .getProduct(productId)
      .then((p) => {
        setProduct(p);
        const active = (p.variants || []).filter((v) => v.is_active);
        if (active.length > 0) {
          setSelectedVariantId(active[0].id);
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load product details");
      })
      .finally(() => setLoading(false));
  }, [productId]);

  const activeVariants = (product?.variants || []).filter((v) => v.is_active);
  const selectedVariant = activeVariants.find((v) => v.id === selectedVariantId) || activeVariants[0];

  const handleAddToCart = async () => {
    if (!selectedVariant) return;

    if (!user) {
      await quickCustomerLogin();
    }

    setIsAdding(true);
    try {
      await api.addToCart(selectedVariant.id, quantity);
      await refreshCartCount();
      setIsAdded(true);
      setTimeout(() => setIsAdded(false), 2500);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to add to cart");
    } finally {
      setIsAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen py-16 max-w-5xl mx-auto px-4 sm:px-6 animate-pulse space-y-6">
        <div className="h-8 w-40 bg-slate-800 rounded-lg"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="h-96 bg-slate-800 rounded-3xl"></div>
          <div className="space-y-4">
            <div className="h-10 bg-slate-800 rounded-xl"></div>
            <div className="h-6 w-32 bg-slate-800 rounded-lg"></div>
            <div className="h-24 bg-slate-800 rounded-xl"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen py-20 max-w-lg mx-auto px-4 text-center space-y-4">
        <div className="p-4 rounded-full bg-red-500/10 text-red-400 w-16 h-16 flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white">Product Not Found</h2>
        <p className="text-xs text-slate-400">{error || "This listing may be archived or unavailable."}</p>
        <Link
          href={returnTo}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Marketplace</span>
        </Link>
      </div>
    );
  }

  const inStock = selectedVariant?.is_in_stock ?? product.is_in_stock ?? false;

  return (
    <main className="min-h-screen pb-24 text-slate-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Navigation Breadcrumb & Back Button */}
        <div className="flex items-center justify-between">
          <Link
            href={returnTo}
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span>Back to Search Results</span>
          </Link>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            {product.brand && (
              <span className="px-2 py-0.5 rounded-full bg-slate-900 border border-slate-800">
                {product.brand.name}
              </span>
            )}
            {product.category && (
              <span className="px-2 py-0.5 rounded-full bg-slate-900 border border-slate-800">
                {product.category.name}
              </span>
            )}
          </div>
        </div>

        {/* Product Details Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-start">
          {/* Visual Showcase Card with Real Media Gallery */}
          <div className="space-y-4">
            <div className="rounded-3xl bg-gradient-to-tr from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-800 p-8 flex flex-col justify-between min-h-[420px] relative overflow-hidden shadow-2xl">
              {product.media && product.media[selectedMediaIndex]?.url && (
                <img
                  src={product.media[selectedMediaIndex].url}
                  alt={product.media[selectedMediaIndex].alt_text || product.name}
                  className="absolute inset-0 w-full h-full object-cover z-0"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/30 to-transparent pointer-events-none z-5"></div>

              <div className="flex items-center justify-between z-10">
                <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-black/60 text-slate-300 backdrop-blur border border-white/10">
                  {product.brand?.name || "Originals"}
                </span>
                <span
                  className={`text-xs font-semibold px-3 py-1 rounded-full border ${
                    inStock
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                      : "bg-amber-500/20 text-amber-300 border-amber-500/30"
                  }`}
                >
                  {inStock ? "In Stock" : "Out of Stock"}
                </span>
              </div>

              {(!product.media || product.media.length === 0) && (
                <div className="z-10 py-12 text-center">
                  <div className="w-20 h-20 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto mb-4 border border-indigo-500/20">
                    <Sparkles className="w-10 h-10" />
                  </div>
                  <p className="text-3xl font-black text-white">{product.name}</p>
                  <p className="text-xs text-slate-400 mt-2">Verified Authentic Multi-Vendor Fashion</p>
                </div>
              )}

              <div className="z-10 flex items-center justify-between border-t border-slate-800/80 pt-4 text-xs text-slate-400 bg-slate-950/40 backdrop-blur-xs -mx-8 -mb-8 px-8 pb-8">
                <span className="flex items-center gap-1.5">
                  <Truck className="w-4 h-4 text-indigo-400" />
                  Global Express Delivery
                </span>
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Secure Checkout
                </span>
              </div>
            </div>

            {/* Thumbnail Gallery Row */}
            {product.media && product.media.length > 1 && (
              <div className="flex items-center gap-3 overflow-x-auto pb-2">
                {product.media.map((m, idx) => (
                  <button
                    key={m.id || idx}
                    onClick={() => setSelectedMediaIndex(idx)}
                    className={`relative w-16 h-16 rounded-xl overflow-hidden border-2 transition-all flex-shrink-0 ${
                      selectedMediaIndex === idx
                        ? "border-indigo-500 shadow-md shadow-indigo-500/30 scale-105"
                        : "border-slate-800 hover:border-slate-700 opacity-70 hover:opacity-100"
                    }`}
                  >
                    <img
                      src={m.url}
                      alt={m.alt_text || `Thumbnail ${idx + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Details & Purchase Panel */}
          <div className="space-y-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-indigo-400">
                <Tag className="w-3.5 h-3.5" />
                <span>{product.category?.name || "Catalog"}</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                {product.name}
              </h1>
              <div className="flex items-baseline gap-3 pt-1">
                <span className="text-3xl font-black text-white">
                  ${selectedVariant ? selectedVariant.price : product.base_price}
                </span>
                <span className="text-xs text-slate-400 uppercase font-semibold">
                  {product.currency || "USD"}
                </span>
              </div>
            </div>

            {product.description && (
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Item Description
                </h3>
                <p className="text-sm text-slate-300 leading-relaxed">{product.description}</p>
              </div>
            )}

            {/* Variant Selector */}
            {activeVariants.length > 0 && (
              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                  Select Size & Color ({activeVariants.length} available)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {activeVariants.map((v) => {
                    const isSelected = v.id === selectedVariant?.id;
                    return (
                      <button
                        key={v.id}
                        onClick={() => setSelectedVariantId(v.id)}
                        className={`p-3 rounded-2xl border text-left transition-all ${
                          isSelected
                            ? "bg-indigo-600/20 border-indigo-500 shadow-md ring-1 ring-indigo-500"
                            : "bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700"
                        }`}
                      >
                        <p className="text-xs font-bold text-white">{v.sku}</p>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {v.size || v.color ? `${v.size || ""} • ${v.color || ""}` : `$${v.price}`}
                        </p>
                        <div className="mt-2 flex items-center justify-between text-[10px]">
                          <span className="font-semibold text-white">${v.price}</span>
                          <span
                            className={
                              v.is_in_stock ? "text-emerald-400 font-medium" : "text-amber-400 font-medium"
                            }
                          >
                            {v.is_in_stock ? "In Stock" : "Out"}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Quantity & Add to Cart */}
            <div className="pt-4 border-t border-slate-800 space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center border border-slate-800 rounded-xl bg-slate-900 px-3 py-2">
                  <span className="text-xs text-slate-400 mr-3">Qty</span>
                  <select
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value, 10))}
                    className="bg-transparent text-xs font-bold text-white focus:outline-none cursor-pointer"
                  >
                    {[1, 2, 3, 4, 5].map((q) => (
                      <option key={q} value={q} className="bg-slate-900 text-white">
                        {q}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={handleAddToCart}
                  disabled={isAdding || !selectedVariant}
                  className={`flex-1 py-3.5 px-6 rounded-2xl text-xs font-bold transition-all shadow-lg flex items-center justify-center gap-2 ${
                    isAdded
                      ? "bg-emerald-600 text-white shadow-emerald-600/20"
                      : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30 active:scale-95"
                  }`}
                >
                  {isAdded ? (
                    <>
                      <Check className="w-4 h-4" />
                      <span>Added to Bag!</span>
                    </>
                  ) : (
                    <>
                      <ShoppingBag className="w-4 h-4" />
                      <span>{isAdding ? "Adding..." : "Add to Cart"}</span>
                    </>
                  )}
                </button>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800/60 flex items-center gap-3 text-xs text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  Items in your bag are protected by atomic stock reservation during checkout.
                </span>
              </div>

              {/* Boutique / Storefront Integration */}
              {product.store && (
                <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 to-indigo-950/20 border border-slate-800 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center overflow-hidden shrink-0">
                      {product.store.logo_url ? (
                        <img
                          src={product.store.logo_url}
                          alt={product.store.store_name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <Store className="w-5 h-5 text-indigo-400" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-white">
                          {product.store.store_name}
                        </span>
                        {product.store.is_verified && (
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Dispatched directly from boutique
                      </p>
                    </div>
                  </div>

                  <Link
                    href={`/store/${product.store.slug}`}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600/10 hover:bg-indigo-600/20 border border-indigo-500/20 text-indigo-300 text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-1"
                  >
                    <span>Visit Boutique</span>
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function ProductDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center text-slate-400 text-sm">
          Loading product...
        </div>
      }
    >
      <ProductDetailContent />
    </Suspense>
  );
}
