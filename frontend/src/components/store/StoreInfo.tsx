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
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span>Brand Narrative & Ethos</span>
        </h3>

        {store.contact_email && (
          <a
            href={`mailto:${store.contact_email}`}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            title="Contact Concierge"
          >
            <Mail className="w-3.5 h-3.5 text-indigo-400" />
            <span>Contact Boutique</span>
          </a>
        )}
      </div>

      {store.bio && (
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed whitespace-pre-line font-light">
          {store.bio}
        </p>
      )}
    </div>
  );
}
