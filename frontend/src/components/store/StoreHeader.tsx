import React from "react";
import { Store as StoreIcon, Calendar, Package } from "lucide-react";
import { PublicStore } from "@/lib/api";
import VerificationBadge from "./VerificationBadge";

interface StoreHeaderProps {
  store: PublicStore;
}

export default function StoreHeader({ store }: StoreHeaderProps) {
  const memberDate = new Date(store.created_at).toLocaleDateString("fr-FR", {
    month: "long",
    year: "numeric",
  });

  return (
    <div className="relative rounded-3xl overflow-hidden bg-[#0c101c] border border-stone-800/90 shadow-2xl">
      {/* Hero Banner */}
      <div className="h-56 sm:h-72 md:h-80 w-full relative overflow-hidden bg-gradient-to-r from-[#070a12] via-[#0f172a] to-[#070a12]">
        {store.banner_url ? (
          <img
            src={store.banner_url}
            alt={`${store.store_name} hero banner`}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-900/20 via-[#070a12] to-[#070a12]" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-[#0c101c] via-[#0c101c]/40 to-transparent pointer-events-none" />
      </div>

      {/* Boutique Identity Overlap Section */}
      <div className="px-6 sm:px-10 pb-8 pt-0 relative">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 -mt-16 sm:-mt-20">
          {/* Logo & Core Title */}
          <div className="flex flex-col sm:flex-row sm:items-end gap-5">
            <div className="w-28 h-28 sm:w-36 sm:h-36 rounded-3xl bg-[#070a12] border-4 border-[#0c101c] shadow-2xl overflow-hidden flex items-center justify-center relative shrink-0 z-10 group">
              {store.logo_url ? (
                <img
                  src={store.logo_url}
                  alt={`${store.store_name} boutique logo`}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-tr from-amber-500/20 via-stone-900 to-stone-950 flex items-center justify-center text-amber-300 border border-amber-500/30">
                  <StoreIcon className="w-12 h-12" />
                </div>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-serif font-bold text-stone-100 tracking-tight">
                  {store.store_name}
                </h1>
                {store.is_verified && <VerificationBadge size="md" />}
              </div>

              <div className="flex items-center gap-4 text-xs text-stone-400 font-medium flex-wrap font-mono">
                <span className="flex items-center gap-1.5">
                  <Package className="w-4 h-4 text-amber-400" />
                  <strong className="text-stone-200">{store.active_products_count}</strong> créations disponibles
                </span>
                <span className="w-1 h-1 rounded-full bg-stone-700" />
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-amber-400" />
                  <span>Partenaire Maison depuis {memberDate}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
