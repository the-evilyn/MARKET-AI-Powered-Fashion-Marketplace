"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  ShieldCheck,
  Package,
  ArrowRight,
  CheckCircle2,
  Lock,
} from "lucide-react";

export default function Footer() {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
      setEmail("");
    }
  };

  return (
    <footer className="bg-[#050810] border-t border-stone-800/80 text-stone-300 relative z-10">
      {/* Upper Newsletter & VIP Club Banner */}
      <div className="border-b border-stone-850 bg-gradient-to-b from-[#090e1a]/40 to-transparent py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-1 text-center md:text-left">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-400/10 border border-amber-400/20 text-amber-300 text-[10px] uppercase font-semibold tracking-widest">
              <Sparkles className="w-3 h-3" />
              <span>Cercle Privé Maison</span>
            </div>
            <h3 className="text-xl sm:text-2xl font-serif font-light text-stone-100 tracking-wide">
              Accédez aux lancements et ventes privées
            </h3>
            <p className="text-xs text-stone-400 max-w-xl">
              Recevez les invitations exclusives pour nos capsules de créateurs et nos collections en édition limitée.
            </p>
          </div>

          <form onSubmit={handleSubscribe} className="w-full md:w-auto flex flex-col sm:flex-row gap-2 max-w-md">
            {subscribed ? (
              <div className="flex items-center gap-2 px-5 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Bienvenue dans le Cercle Privé Maison.</span>
              </div>
            ) : (
              <>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="votre.adresse@prestige.com"
                  className="px-4 py-3 rounded-xl bg-stone-900/90 border border-stone-800 text-stone-100 placeholder-stone-500 text-xs focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 min-w-[260px]"
                />
                <button
                  type="submit"
                  className="px-5 py-3 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 font-semibold text-xs tracking-wider uppercase transition-all shadow-lg shadow-amber-400/10 flex items-center justify-center gap-2 shrink-0 active:scale-95"
                >
                  <span>Rejoindre</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </>
            )}
          </form>
        </div>
      </div>

      {/* Main Multi-Column Directory */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10">
          {/* Brand & Manifesto */}
          <div className="lg:col-span-2 space-y-4">
            <Link href="/" className="inline-block">
              <span className="font-serif text-2xl font-semibold tracking-[0.25em] text-stone-100 hover:text-amber-200 transition-colors">
                MAISON
              </span>
              <span className="block text-[9px] uppercase tracking-[0.3em] text-amber-400/90 font-mono mt-0.5">
                AI FASHION MARKETPLACE
              </span>
            </Link>
            <p className="text-xs text-stone-400 leading-relaxed max-w-sm">
              Plateforme d&apos;exception reliant les créateurs indépendants, maisons de couture émergentes et amateurs de luxe. Découverte assistée par IA, traçabilité et transactions sécurisées.
            </p>
            <div className="flex items-center gap-3 pt-2 text-stone-500 text-xs">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-amber-400/80" />
                <span className="text-[11px] text-stone-400">Paiements Chiffrés</span>
              </div>
              <span>•</span>
              <div className="flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-amber-400/80" />
                <span className="text-[11px] text-stone-400">PayPal Sandbox</span>
              </div>
            </div>
          </div>

          {/* Univers & Collections */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-widest text-amber-300/90 font-semibold">
              Collections
            </h4>
            <ul className="space-y-2 text-xs text-stone-400">
              <li>
                <Link href="/?sort=newest" className="hover:text-stone-100 transition-colors">
                  Dernières Arrivées
                </Link>
              </li>
              <li>
                <Link href="/?sort=relevance" className="hover:text-stone-100 transition-colors">
                  Sélection Curatée
                </Link>
              </li>
              <li>
                <Link href="/?in_stock=true" className="hover:text-stone-100 transition-colors">
                  Pièces Disponibles
                </Link>
              </li>
              <li>
                <Link href="/orders" className="hover:text-stone-100 transition-colors">
                  Mes Commandes
                </Link>
              </li>
            </ul>
          </div>

          {/* Conciergerie & Services */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-widest text-amber-300/90 font-semibold">
              Conciergerie
            </h4>
            <ul className="space-y-2 text-xs text-stone-400">
              <li>
                <Link href="/orders" className="hover:text-stone-100 transition-colors">
                  Suivi des Commandes
                </Link>
              </li>
              <li>
                <Link href="/checkout" className="hover:text-stone-100 transition-colors">
                  Finalisation d&apos;Achat
                </Link>
              </li>
              <li>
                <span className="text-stone-500 cursor-not-allowed">
                  Guide des Tailles & Matières
                </span>
              </li>
              <li>
                <span className="text-stone-500 cursor-not-allowed">
                  Politique de Retours (14 Jours)
                </span>
              </li>
            </ul>
          </div>

          {/* Espace Créateurs & Plateforme */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-widest text-amber-300/90 font-semibold">
              Gouvernance
            </h4>
            <ul className="space-y-2 text-xs text-stone-400">
              <li>
                <Link
                  href="/seller/dashboard"
                  className="inline-flex items-center gap-1.5 hover:text-stone-100 transition-colors"
                >
                  <Package className="w-3.5 h-3.5 text-amber-400" />
                  <span>Portail Vendeur</span>
                </Link>
              </li>
              <li>
                <Link
                  href="/admin/dashboard"
                  className="inline-flex items-center gap-1.5 hover:text-stone-100 transition-colors"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                  <span>Supervision Admin</span>
                </Link>
              </li>
              <li>
                <Link href="/admin/stores" className="hover:text-stone-100 transition-colors">
                  Modération des Boutiques
                </Link>
              </li>
              <li>
                <Link href="/admin/users" className="hover:text-stone-100 transition-colors">
                  Gouvernance Utilisateurs
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Legal & Attribution Bar */}
        <div className="mt-12 pt-8 border-t border-stone-850 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-stone-500">
          <div>
            © {new Date().getFullYear()} Maison — AI-Powered Fashion Marketplace. Tous droits réservés.
          </div>
          <div className="flex items-center gap-4">
            <span>Devise : USD ($)</span>
            <span>•</span>
            <span>Paris — Milan — Londres — New York</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
