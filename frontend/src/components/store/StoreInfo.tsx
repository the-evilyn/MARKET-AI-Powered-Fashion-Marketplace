import React from "react";
import { Mail, Sparkles } from "lucide-react";
import { PublicStore } from "@/lib/api";

interface StoreInfoProps {
  store: PublicStore;
}

export default function StoreInfo({ store }: StoreInfoProps) {
  if (!store.bio && !store.contact_email) {
    return null;
  }

  return (
    <div className="bg-[#0c101c] border border-stone-800/90 rounded-3xl p-6 sm:p-8 space-y-5 shadow-xl">
      <div className="flex items-center justify-between border-b border-stone-800/80 pb-4">
        <h3 className="text-xs font-bold text-amber-400 uppercase tracking-widest flex items-center gap-2 font-mono">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span>Manifesto &amp; Univers du Créateur</span>
        </h3>

        {store.contact_email && (
          <a
            href={`mailto:${store.contact_email}`}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-stone-900 hover:bg-stone-800 text-stone-200 border border-stone-800 hover:border-amber-400/40 transition-colors"
            title="Contacter la conciergerie de la Maison"
          >
            <Mail className="w-3.5 h-3.5 text-amber-400" />
            <span>Contacter la Maison</span>
          </a>
        )}
      </div>

      {store.bio && (
        <p className="text-xs sm:text-sm text-stone-300 leading-relaxed whitespace-pre-line font-light">
          {store.bio}
        </p>
      )}
    </div>
  );
}
