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
  Sparkles,
  Store,
  Heart,
  RotateCcw,
} from "lucide-react";
import { api, Product, ProductVariant } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useFavorites } from "@/context/FavoritesContext";

function ProductDetailContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, quickCustomerLogin, refreshCartCount, openCart } = useAuth();
  const { isFavorite, toggleFavorite } = useFavorites();

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
        setError(err instanceof Error ? err.message : "Impossible de charger la pièce demandée");
      })
      .finally(() => setLoading(false));
  }, [productId]);

  const activeVariants = (product?.variants || []).filter((v) => v.is_active);
  const selectedVariant =
    activeVariants.find((v) => v.id === selectedVariantId) || activeVariants[0];

  const isFav = product ? isFavorite(product.id) : false;

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
      openCart();
      setTimeout(() => setIsAdded(false), 2500);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Échec de l'ajout au panier");
    } finally {
      setIsAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen py-16 max-w-6xl mx-auto px-4 sm:px-6 animate-pulse space-y-8">
        <div className="h-6 w-40 bg-stone-900 rounded-lg"></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          <div className="h-[460px] bg-stone-900 rounded-3xl border border-stone-800"></div>
          <div className="space-y-5">
            <div className="h-6 w-28 bg-stone-900 rounded-lg"></div>
            <div className="h-10 w-3/4 bg-stone-900 rounded-xl"></div>
            <div className="h-8 w-32 bg-stone-900 rounded-lg"></div>
            <div className="h-32 bg-stone-900 rounded-2xl"></div>
            <div className="h-28 bg-stone-900 rounded-2xl"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8" />
        </div>
        <div className="space-y-1">
          <h2 className="text-2xl font-serif font-bold text-stone-100">Pièce introuvable</h2>
          <p className="text-xs text-stone-400 max-w-md mx-auto">
            {error || "Cette création est actuellement indisponible ou a été archivée par la Maison."}
          </p>
        </div>
        <Link
          href={returnTo}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-stone-900 hover:bg-stone-800 border border-stone-800 text-xs font-semibold text-stone-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 text-amber-400" />
          <span>Retour aux collections</span>
        </Link>
      </div>
    );
  }

  const inStock = selectedVariant?.is_in_stock ?? product.is_in_stock ?? false;

  return (
    <main className="min-h-screen pb-24 text-stone-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Navigation Breadcrumb & Back Button */}
        <div className="flex items-center justify-between border-b border-stone-800/80 pb-4">
          <Link
            href={returnTo}
            className="inline-flex items-center gap-2 text-xs font-semibold text-stone-400 hover:text-amber-300 transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 text-amber-400 group-hover:-translate-x-1 transition-transform" />
            <span>Retour aux collections</span>
          </Link>

          <div className="flex items-center gap-2 text-xs text-stone-400">
            {product.brand && (
              <span className="px-3 py-1 rounded-full bg-[#0c101c] border border-stone-800 text-stone-300 font-medium">
                {product.brand.name}
              </span>
            )}
            {product.category && (
              <span className="px-3 py-1 rounded-full bg-amber-400/10 border border-amber-500/20 text-amber-300 font-medium">
                {product.category.name}
              </span>
            )}
          </div>
        </div>

        {/* Product Details Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-start">
          {/* Visual Showcase Card with Real Media Gallery */}
          <div className="space-y-4">
            <div className="rounded-3xl bg-gradient-to-tr from-[#0a0e18] via-[#0d1322] to-[#0a0e18] border border-stone-800/90 p-8 flex flex-col justify-between min-h-[460px] relative overflow-hidden shadow-2xl">
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
              <div className="absolute inset-0 bg-gradient-to-t from-[#070a12] via-[#070a12]/30 to-transparent pointer-events-none z-5" />

              <div className="flex items-center justify-between z-10">
                <span className="text-[11px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-full bg-black/60 text-stone-200 backdrop-blur border border-white/10 font-mono">
                  {product.brand?.name || "Maison Originals"}
                </span>
                <span
                  className={`text-[11px] font-semibold px-3 py-1.5 rounded-full border backdrop-blur ${
                    inStock
                      ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                      : "bg-amber-500/15 text-amber-300 border-amber-500/30"
                  }`}
                >
                  {inStock ? "Disponible immédiatement" : "Stock épuisé"}
                </span>
              </div>

              {(!product.media || product.media.length === 0) && (
                <div className="z-10 py-16 text-center">
                  <div className="w-20 h-20 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto mb-4 border border-amber-500/20 shadow-lg shadow-amber-500/5">
                    <Sparkles className="w-10 h-10" />
                  </div>
                  <p className="text-3xl font-serif font-black text-stone-100">{product.name}</p>
                  <p className="text-xs text-stone-400 mt-2 font-mono">
                    Création Authentifiée &amp; Certifiée
                  </p>
                </div>
              )}

              <div className="z-10 flex items-center justify-between border-t border-stone-800/80 pt-4 text-xs text-stone-400 bg-[#070a12]/80 backdrop-blur-md -mx-8 -mb-8 px-8 pb-6">
                <span className="flex items-center gap-1.5">
                  <Truck className="w-4 h-4 text-amber-400" />
                  <span>Livraison Haute Protection</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Paiement &amp; Authenticité 100%</span>
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
                    className={`relative w-20 h-20 rounded-2xl overflow-hidden border-2 transition-all shrink-0 ${
                      selectedMediaIndex === idx
                        ? "border-amber-400 shadow-lg shadow-amber-400/20 scale-105"
                        : "border-stone-800 hover:border-stone-700 opacity-60 hover:opacity-100"
                    }`}
                  >
                    <img
                      src={m.url}
                      alt={m.alt_text || `Vue ${idx + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Details & Purchase Panel */}
          <div className="space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold text-amber-400 uppercase tracking-wider font-mono">
                  <Tag className="w-3.5 h-3.5" />
                  <span>{product.category?.name || "Haute Couture"}</span>
                </div>

                {/* Wishlist toggle */}
                <button
                  onClick={() => toggleFavorite(product.id)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                    isFav
                      ? "bg-rose-500/20 border-rose-500/40 text-rose-300"
                      : "bg-stone-900 border-stone-800 text-stone-400 hover:text-rose-300 hover:border-rose-500/30"
                  }`}
                  title={isFav ? "Retirer des favoris" : "Ajouter aux favoris"}
                >
                  <Heart className={`w-3.5 h-3.5 ${isFav ? "fill-rose-400 text-rose-400" : ""}`} />
                  <span>{isFav ? "En Favoris" : "Ajouter aux Favoris"}</span>
                </button>
              </div>

              <h1 className="text-3xl sm:text-4xl font-serif font-black text-stone-100 tracking-tight">
                {product.name}
              </h1>

              <div className="flex items-baseline gap-3 pt-1">
                <span className="text-3xl sm:text-4xl font-bold font-mono text-amber-300">
                  ${selectedVariant ? selectedVariant.price : product.base_price}
                </span>
                <span className="text-xs text-stone-400 uppercase font-semibold font-mono">
                  {product.currency || "USD"}
                </span>
                {selectedVariant && (
                  <span className="text-xs text-stone-500 font-mono">
                    (SKU: {selectedVariant.sku})
                  </span>
                )}
              </div>
            </div>

            {product.description && (
              <div className="p-5 rounded-2xl bg-[#0c101c] border border-stone-800/80 space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400/90 font-mono">
                  Description &amp; Détails
                </h3>
                <p className="text-xs sm:text-sm text-stone-300 leading-relaxed font-light">
                  {product.description}
                </p>
              </div>
            )}

            {/* Variant Selector */}
            {activeVariants.length > 0 && (
              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-stone-300 block font-mono">
                  Variantes disponibles ({activeVariants.length})
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {activeVariants.map((v) => {
                    const isSelected = v.id === selectedVariant?.id;
                    return (
                      <button
                        key={v.id}
                        onClick={() => setSelectedVariantId(v.id)}
                        className={`p-3.5 rounded-2xl border text-left transition-all ${
                          isSelected
                            ? "bg-amber-400/10 border-amber-400/60 shadow-lg shadow-amber-400/10 ring-1 ring-amber-400/50"
                            : "bg-[#0c101c] border-stone-800/80 text-stone-300 hover:border-stone-700"
                        }`}
                      >
                        <p className="text-xs font-bold text-stone-100 truncate">{v.sku}</p>
                        <p className="text-[11px] text-stone-400 mt-0.5">
                          {v.size || v.color
                            ? `${v.size ? `T: ${v.size}` : ""}${v.size && v.color ? " • " : ""}${v.color || ""}`
                            : `$${v.price}`}
                        </p>
                        <div className="mt-2 flex items-center justify-between text-[11px] pt-1 border-t border-stone-800/50">
                          <span className="font-mono font-bold text-amber-300">${v.price}</span>
                          <span
                            className={
                              v.is_in_stock
                                ? "text-emerald-400 font-medium"
                                : "text-amber-400/80 font-medium"
                            }
                          >
                            {v.is_in_stock ? "En stock" : "Épuisé"}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Quantity & Add to Cart */}
            <div className="pt-4 border-t border-stone-800/80 space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center border border-stone-800 rounded-xl bg-[#0c101c] px-3 py-2">
                  <span className="text-xs text-stone-400 mr-3 font-mono">Quantité</span>
                  <select
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value, 10))}
                    className="bg-transparent text-xs font-bold text-amber-300 focus:outline-none cursor-pointer"
                  >
                    {[1, 2, 3, 4, 5].map((q) => (
                      <option key={q} value={q} className="bg-[#0c101c] text-stone-100">
                        {q}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={handleAddToCart}
                  disabled={isAdding || !selectedVariant || !inStock}
                  className={`flex-1 py-3.5 px-6 rounded-2xl text-xs font-bold tracking-wider uppercase transition-all shadow-xl flex items-center justify-center gap-2 ${
                    isAdded
                      ? "bg-emerald-500 text-stone-950 shadow-emerald-500/20"
                      : inStock
                      ? "bg-amber-400 hover:bg-amber-300 text-stone-950 shadow-amber-400/10 active:scale-98"
                      : "bg-stone-800 text-stone-500 cursor-not-allowed"
                  }`}
                >
                  {isAdded ? (
                    <>
                      <Check className="w-4 h-4" />
                      <span>Ajouté au Panier !</span>
                    </>
                  ) : (
                    <>
                      <ShoppingBag className="w-4 h-4" />
                      <span>
                        {isAdding
                          ? "Ajout en cours..."
                          : inStock
                          ? "Ajouter à la Sélection"
                          : "Pièce Indisponible"}
                      </span>
                    </>
                  )}
                </button>
              </div>

              <div className="p-4 rounded-2xl bg-[#0c101c]/60 border border-stone-800/80 flex items-center gap-3 text-xs text-stone-400">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  Réservation atomique des stocks garantie jusqu&apos;à la confirmation du paiement.
                </span>
              </div>

              {/* Boutique / Storefront Integration */}
              {product.store && (
                <div className="p-4 rounded-2xl bg-gradient-to-r from-[#0c101c] to-[#121828] border border-stone-800 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-stone-950 border border-stone-800 flex items-center justify-center overflow-hidden shrink-0">
                      {product.store.logo_url ? (
                        <img
                          src={product.store.logo_url}
                          alt={product.store.store_name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <Store className="w-5 h-5 text-amber-400" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-stone-100">
                          {product.store.store_name}
                        </span>
                        {product.store.is_verified && (
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        )}
                      </div>
                      <p className="text-[11px] text-stone-400">
                        Expédié directement par la Maison partenaire
                      </p>
                    </div>
                  </div>

                  <Link
                    href={`/store/${product.store.slug}`}
                    className="px-3.5 py-1.5 rounded-xl bg-amber-400/10 hover:bg-amber-400/20 border border-amber-500/20 text-amber-300 text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-1"
                  >
                    <span>Visiter la Boutique</span>
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
        <div className="min-h-screen flex items-center justify-center text-stone-400 text-sm">
          Chargement de la création...
        </div>
      }
    >
      <ProductDetailContent />
    </Suspense>
  );
}
