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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900 border border-slate-800">
        <div className="flex items-center gap-2 text-xs text-slate-300 font-semibold">
          <span>Showing</span>
          <span className="px-2 py-0.5 rounded-md bg-slate-950 text-indigo-400 font-bold border border-slate-800">
            {products.length} of {total}
          </span>
          <span>exclusive pieces</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs text-slate-400 font-medium">Sort by:</span>
          </div>
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-semibold text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="newest">Latest Arrivals</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
          </select>
        </div>
      </div>

      {/* Grid Content */}
      {products.length === 0 ? (
        <div className="py-20 rounded-3xl bg-slate-900/50 border border-slate-800 text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
            <PackageOpen className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h4 className="text-base font-bold text-white">No active pieces available</h4>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              This designer has not published any active items matching current criteria. Check back soon for new arrivals!
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
        <div className="flex items-center justify-between pt-6 border-t border-slate-800/80">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Previous</span>
          </button>

          <span className="text-xs text-slate-400 font-semibold">
            Page <strong className="text-white">{page}</strong> of <strong className="text-white">{totalPages}</strong>
          </span>

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          >
            <span>Next</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
