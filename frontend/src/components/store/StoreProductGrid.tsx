"use client";

import React from "react";
import { ArrowLeft, ArrowRight, SlidersHorizontal, PackageOpen } from "lucide-react";
import { PublicStoreProductItem } from "@/lib/api";
import StoreProductCard from "./StoreProductCard";

interface StoreProductGridProps {
  products: PublicStoreProductItem[];
  total: number;
  page: number;
  totalPages: number;
  sortBy: string;
  onSortChange: (sort: string) => void;
  onPageChange: (newPage: number) => void;
}

export default function StoreProductGrid({
  products,
  total,
  page,
  totalPages,
  sortBy,
  onSortChange,
  onPageChange,
}: StoreProductGridProps) {
  return (
    <div className="space-y-6">
      {/* Catalog Filter & Sorting Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-[#0c101c] border border-stone-800/90">
        <div className="flex items-center gap-2 text-xs text-stone-300 font-medium font-mono">
          <span>Affichage de</span>
          <span className="px-2 py-0.5 rounded-md bg-stone-900 text-amber-300 font-bold border border-stone-800">
            {products.length} sur {total}
          </span>
          <span>pièces d&apos;exception</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-xs text-stone-400 font-medium">Trier par :</span>
          </div>
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-stone-900 border border-stone-800 text-xs font-semibold text-stone-100 focus:outline-none focus:border-amber-400 cursor-pointer"
          >
            <option value="newest">Dernières créations</option>
            <option value="price_asc">Prix croissant</option>
            <option value="price_desc">Prix décroissant</option>
          </select>
        </div>
      </div>

      {/* Grid Content */}
      {products.length === 0 ? (
        <div className="py-20 rounded-3xl bg-[#0c101c]/50 border border-stone-800 text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-stone-900 text-stone-400 flex items-center justify-center mx-auto border border-stone-800">
            <PackageOpen className="w-8 h-8 text-amber-400/80" />
          </div>
          <div className="space-y-1">
            <h4 className="text-base font-serif font-bold text-stone-200">
              Aucune pièce disponible actuellement
            </h4>
            <p className="text-xs text-stone-400 max-w-sm mx-auto font-light">
              Cette Maison n&apos;a pas encore publié d&apos;articles actifs répondant à vos critères.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {products.map((product) => (
            <StoreProductCard key={product.id} product={product} />
          ))}
        </div>
      )}

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-6 border-t border-stone-800/80">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-stone-900 hover:bg-stone-800 text-stone-200 border border-stone-800 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-amber-400" />
            <span>Précédent</span>
          </button>

          <span className="text-xs text-stone-400 font-mono">
            Page <strong className="text-amber-300">{page}</strong> sur{" "}
            <strong className="text-stone-200">{totalPages}</strong>
          </span>

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-stone-900 hover:bg-stone-800 text-stone-200 border border-stone-800 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          >
            <span>Suivant</span>
            <ArrowRight className="w-3.5 h-3.5 text-amber-400" />
          </button>
        </div>
      )}
    </div>
  );
}
