"use client";

import React from "react";
import Link from "next/link";
import { Sparkles, ArrowRight, Heart } from "lucide-react";
import { PublicStoreProductItem } from "@/lib/api";
import { useFavorites } from "@/context/FavoritesContext";

interface StoreProductCardProps {
  product: PublicStoreProductItem;
}

export default function StoreProductCard({ product }: StoreProductCardProps) {
  const { isFavorite, toggleFavorite } = useFavorites();
  const isFav = isFavorite(product.id);

  const formattedPrice = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: product.currency || "USD",
  }).format(parseFloat(product.base_price));

  return (
    <div className="group rounded-3xl bg-[#0c101c] border border-stone-800/90 overflow-hidden hover:border-amber-400/40 hover:shadow-2xl hover:shadow-amber-400/5 transition-all duration-300 flex flex-col justify-between relative">
      <div>
        {/* Media Container */}
        <div className="relative aspect-[4/5] w-full overflow-hidden bg-[#070a12] flex items-center justify-center">
          {product.primary_image_url ? (
            <img
              src={product.primary_image_url}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          ) : (
            <div className="text-center p-6 space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto border border-amber-500/20">
                <Sparkles className="w-6 h-6" />
              </div>
              <span className="text-[10px] text-stone-500 uppercase tracking-widest font-mono font-semibold block">
                Pièce d&apos;Exception
              </span>
            </div>
          )}

          {/* Wishlist button */}
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              toggleFavorite(product.id);
            }}
            className="absolute top-3 left-3 z-10 p-2 rounded-full bg-black/60 hover:bg-black/90 backdrop-blur-md border border-white/10 text-stone-300 hover:text-rose-400 transition-colors"
            title={isFav ? "Retirer des favoris" : "Ajouter aux favoris"}
          >
            <Heart className={`w-3.5 h-3.5 ${isFav ? "fill-rose-400 text-rose-400" : ""}`} />
          </button>

          {/* Stock Status Badge */}
          <div className="absolute top-3 right-3 z-10">
            <span
              className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full backdrop-blur-md border font-mono ${
                product.is_in_stock
                  ? "bg-black/60 text-emerald-400 border-emerald-500/30"
                  : "bg-black/60 text-amber-400 border-amber-500/30"
              }`}
            >
              {product.is_in_stock ? "En stock" : "Épuisé"}
            </span>
          </div>

          {/* Category Badge */}
          {product.category_name && (
            <div className="absolute bottom-3 left-3 z-10">
              <span className="text-[10px] font-semibold text-stone-200 px-2.5 py-1 rounded-full bg-black/70 backdrop-blur border border-white/10 font-mono">
                {product.category_name}
              </span>
            </div>
          )}
        </div>

        {/* Content Details */}
        <div className="p-5 space-y-2">
          {product.brand_name && (
            <p className="text-[10px] font-bold uppercase tracking-wider text-amber-400 font-mono">
              {product.brand_name}
            </p>
          )}

          <Link href={`/products/${product.id}`} className="block">
            <h4 className="text-sm font-serif font-bold text-stone-100 group-hover:text-amber-200 transition-colors line-clamp-1">
              {product.name}
            </h4>
          </Link>

          <div className="flex items-center justify-between pt-1">
            <p className="text-base font-bold text-amber-300 font-mono">{formattedPrice}</p>
            {product.variants_count > 1 && (
              <span className="text-[11px] text-stone-400 font-mono">
                {product.variants_count} variantes
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="px-5 pb-5 pt-0">
        <Link
          href={`/products/${product.id}`}
          className="w-full py-2.5 rounded-xl bg-stone-900 border border-stone-800 text-stone-200 group-hover:bg-amber-400 group-hover:text-stone-950 group-hover:border-amber-400 transition-all text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-1.5 shadow-sm"
        >
          <span>Découvrir la Pièce</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>
    </div>
  );
}
