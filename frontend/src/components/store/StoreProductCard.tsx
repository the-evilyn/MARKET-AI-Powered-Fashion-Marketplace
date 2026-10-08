import React from "react";
import Link from "next/link";
import { Sparkles, ArrowRight } from "lucide-react";
import { PublicStoreProductItem } from "@/lib/api";

interface StoreProductCardProps {
  product: PublicStoreProductItem;
}

export default function StoreProductCard({ product }: StoreProductCardProps) {
  const formattedPrice = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: product.currency || "USD",
  }).format(parseFloat(product.base_price));

  return (
    <Link
      href={`/products/${product.id}`}
      className="group block rounded-3xl bg-slate-900 border border-slate-800 overflow-hidden hover:border-indigo-500/40 hover:shadow-2xl hover:shadow-indigo-500/10 transition-all duration-300 flex flex-col justify-between"
    >
      <div>
        {/* Media Container */}
        <div className="relative aspect-[4/5] w-full overflow-hidden bg-slate-950 flex items-center justify-center">
          {product.primary_image_url ? (
            <img
              src={product.primary_image_url}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          ) : (
            <div className="text-center p-6 space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto">
                <Sparkles className="w-6 h-6" />
              </div>
              <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold block">
                Exclusive Piece
              </span>
            </div>
          )}

          {/* Stock Status Badge */}
          <div className="absolute top-3 right-3 z-10">
            <span
              className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full backdrop-blur-md border ${
                product.is_in_stock
                  ? "bg-black/60 text-emerald-400 border-emerald-500/30"
                  : "bg-black/60 text-amber-400 border-amber-500/30"
              }`}
            >
              {product.is_in_stock ? "In Stock" : "Out of Stock"}
            </span>
          </div>

          {/* Category Badge */}
          {product.category_name && (
            <div className="absolute bottom-3 left-3 z-10">
              <span className="text-[10px] font-semibold text-slate-300 px-2.5 py-1 rounded-full bg-slate-950/80 backdrop-blur border border-white/10">
                {product.category_name}
              </span>
            </div>
          )}
        </div>

        {/* Content Details */}
        <div className="p-5 space-y-2">
          {product.brand_name && (
            <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
              {product.brand_name}
            </p>
          )}

          <h4 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors line-clamp-1">
            {product.name}
          </h4>

          <div className="flex items-center justify-between pt-1">
            <p className="text-sm font-extrabold text-white">{formattedPrice}</p>
            {product.variants_count > 1 && (
              <span className="text-[11px] text-slate-400">
                {product.variants_count} options
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="px-5 pb-5 pt-0">
        <div className="w-full py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 group-hover:bg-indigo-600 group-hover:text-white group-hover:border-indigo-600 transition-all text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm">
          <span>View Details</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </div>
      </div>
    </Link>
  );
}
