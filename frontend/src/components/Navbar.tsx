"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShoppingBag,
  Package,
  User as UserIcon,
  LogOut,
  Sparkles,
  CheckCircle2,
  ShieldCheck,
  Heart,
  ChevronDown,
  Menu,
  X,
} from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import { useFavorites } from "@/context/FavoritesContext";

export default function Navbar() {
  const { user, cartCount, quickCustomerLogin, quickSellerLogin, logout, login, openCart } = useAuth();
  const { favoritesCount } = useFavorites();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      setShowLoginModal(false);
    } catch (err: unknown) {
      setLoginError(err instanceof Error ? err.message : "Identifiants invalides");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-40 bg-[#070b14]/90 backdrop-blur-md border-b border-stone-800/80 text-stone-100 transition-all">
        {/* Top micro announcement bar */}
        <div className="bg-gradient-to-r from-[#0d1322] via-[#141b2d] to-[#0d1322] border-b border-stone-850 px-3 sm:px-4 py-1 text-center text-[10px] sm:text-[11px] text-stone-400 font-mono flex items-center justify-center gap-1.5 sm:gap-2 overflow-hidden">
          <Sparkles className="w-3 h-3 text-amber-400/90 shrink-0" />
          <span className="truncate max-w-[280px] sm:max-w-none">Maison — Haute Couture &amp; Créateurs Indépendants</span>
          <span className="hidden md:inline text-stone-600">•</span>
          <span className="hidden md:inline text-amber-300/80">Livraison express &amp; Authenticité certifiée</span>
        </div>

        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 sm:h-20">
            {/* Brand Monogram & Title */}
            <div className="flex items-center gap-2 sm:gap-8 min-w-0 shrink">
              <Link href="/" className="flex items-center gap-2 sm:gap-3 group shrink min-w-0">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-amber-400/20 via-amber-500/10 to-stone-900 border border-amber-400/30 flex items-center justify-center text-amber-300 shadow-lg shadow-amber-400/5 group-hover:border-amber-400/60 transition-all">
                  <span className="font-serif font-black text-base sm:text-lg tracking-widest text-amber-300">M</span>
                </div>
                <div>
                  <span className="font-serif text-lg sm:text-2xl font-bold tracking-[0.15em] sm:tracking-[0.2em] text-stone-100 group-hover:text-amber-200 transition-colors">
                    MAISON
                  </span>
                  <span className="hidden sm:block text-[9px] uppercase tracking-[0.25em] text-amber-400/90 font-mono -mt-0.5">
                    Haute Couture AI
                  </span>
                </div>
              </Link>

              {/* Navigation Links */}
              <nav className="hidden lg:flex items-center gap-1 text-xs">
                <Link
                  href="/"
                  className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                    pathname === "/"
                      ? "text-amber-300 bg-stone-900/80 border border-stone-800"
                      : "text-stone-300 hover:text-stone-100 hover:bg-stone-900/50"
                  }`}
                >
                  Collections
                </Link>
                <Link
                  href="/?sort=newest"
                  className="px-3 py-2 rounded-lg font-medium text-stone-300 hover:text-stone-100 hover:bg-stone-900/50 transition-colors"
                >
                  Nouveautés
                </Link>
                <Link
                  href="/orders"
                  className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                    pathname.startsWith("/orders")
                      ? "text-amber-300 bg-stone-900/80 border border-stone-800"
                      : "text-stone-300 hover:text-stone-100 hover:bg-stone-900/50"
                  }`}
                >
                  Mes Commandes
                </Link>

                {/* Seller Dashboard Link */}
                {user && (user.role === "SELLER" || user.role === "ADMIN") && (
                  <Link
                    href="/seller/dashboard"
                    className={`ml-2 px-3 py-1.5 rounded-lg font-semibold transition-all inline-flex items-center gap-1.5 text-xs ${
                      pathname.startsWith("/seller")
                        ? "bg-amber-400/20 text-amber-300 border border-amber-400/40"
                        : "text-amber-300/90 hover:text-amber-200 hover:bg-amber-400/10 border border-amber-500/20"
                    }`}
                  >
                    <Package className="w-3.5 h-3.5" />
                    <span>Espace Vendeur</span>
                  </Link>
                )}

                {/* Admin Platform Link */}
                {user && user.role === "ADMIN" && (
                  <Link
                    href="/admin/dashboard"
                    className={`ml-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all inline-flex items-center gap-1.5 text-xs ${
                      pathname.startsWith("/admin")
                        ? "bg-amber-500/30 text-amber-200 border border-amber-400/50"
                        : "text-amber-300 hover:text-amber-100 hover:bg-amber-500/20 border border-amber-500/30"
                    }`}
                  >
                    <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                    <span>Plateforme Admin</span>
                  </Link>
                )}
              </nav>
            </div>

              {/* Right section: Wishlist, Cart Drawer Trigger & Auth */}
            <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
              {/* Wishlist pill */}
              <Link
                href="/?favorites=true"
                className="relative p-2 sm:p-2.5 rounded-xl bg-stone-900/70 border border-stone-800 hover:border-stone-700 text-stone-300 hover:text-rose-300 transition-colors"
                title="Favoris & Wishlist"
              >
                <Heart className="w-4 h-4" />
                {favoritesCount > 0 && (
                  <span className="absolute -top-1 -right-1 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold text-stone-950 bg-rose-400 rounded-full">
                    {favoritesCount}
                  </span>
                )}
              </Link>

              {/* Cart Drawer Trigger Button */}
              <button
                type="button"
                onClick={openCart}
                className="relative inline-flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-4 py-2 rounded-xl text-xs font-semibold bg-[#111728] border border-amber-500/30 hover:border-amber-400/50 text-stone-100 hover:text-amber-200 transition-all shadow-md active:scale-95"
                title="Ouvrir le Panier"
              >
                <ShoppingBag className="w-4 h-4 text-amber-400" />
                <span className="hidden sm:inline font-mono">Panier</span>
                {cartCount > 0 && (
                  <span className="inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-black leading-none text-stone-950 bg-amber-400 rounded-full">
                    {cartCount}
                  </span>
                )}
              </button>

              {/* User Authentication Status */}
              {user ? (
                <div className="flex items-center gap-2 sm:gap-3 pl-2 sm:pl-3 border-l border-stone-800">
                  <div className="text-right hidden sm:block">
                    <p className="text-xs font-medium text-stone-100 truncate max-w-[130px]">
                      {user.first_name || user.email.split("@")[0]}
                    </p>
                    <span className="text-[10px] text-amber-400 font-mono uppercase font-semibold">
                      {user.role}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    className="p-2 text-stone-400 hover:text-rose-400 rounded-xl hover:bg-stone-900 transition-colors"
                    title="Déconnexion"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 sm:gap-2">
                  <button
                    onClick={quickCustomerLogin}
                    className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors"
                    title="Connexion Rapide Client (Test)"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Client</span>
                  </button>
                  <button
                    onClick={quickSellerLogin}
                    className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-violet-500/10 text-violet-400 border border-violet-500/20 hover:bg-violet-500/20 transition-colors"
                    title="Connexion Rapide Vendeur (Test)"
                  >
                    <Package className="w-3.5 h-3.5" />
                    <span>Vendeur</span>
                  </button>
                  <button
                    onClick={() => setShowLoginModal(true)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-400 hover:bg-amber-300 text-stone-950 transition-all shadow-md shadow-amber-400/10"
                  >
                    <UserIcon className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Connexion</span>
                  </button>
                </div>
              )}

              {/* Mobile Hamburger Button */}
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 text-stone-300 hover:text-white rounded-xl bg-stone-900/60 border border-stone-800 hover:border-stone-700 transition-colors"
                aria-label="Menu principal"
              >
                {mobileMenuOpen ? <X className="w-4 h-4 text-amber-400" /> : <Menu className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-stone-800/80 bg-[#070b14]/98 backdrop-blur-xl px-4 py-4 space-y-3 shadow-2xl">
            <nav className="flex flex-col space-y-1">
              <Link
                href="/"
                onClick={() => setMobileMenuOpen(false)}
                className={`px-3 py-2.5 rounded-xl font-medium text-xs transition-colors ${
                  pathname === "/"
                    ? "text-amber-300 bg-stone-900 border border-stone-800"
                    : "text-stone-300 hover:text-white hover:bg-stone-900/60"
                }`}
              >
                Collections
              </Link>
              <Link
                href="/?sort=newest"
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2.5 rounded-xl font-medium text-xs text-stone-300 hover:text-white hover:bg-stone-900/60 transition-colors"
              >
                Nouveautés
              </Link>
              <Link
                href="/orders"
                onClick={() => setMobileMenuOpen(false)}
                className={`px-3 py-2.5 rounded-xl font-medium text-xs transition-colors ${
                  pathname.startsWith("/orders")
                    ? "text-amber-300 bg-stone-900 border border-stone-800"
                    : "text-stone-300 hover:text-white hover:bg-stone-900/60"
                }`}
              >
                Mes Commandes
              </Link>
              {user && (user.role === "SELLER" || user.role === "ADMIN") && (
                <Link
                  href="/seller/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-3 py-2.5 rounded-xl font-semibold text-xs text-amber-300 bg-amber-400/10 border border-amber-400/30 flex items-center gap-2"
                >
                  <Package className="w-4 h-4 text-amber-400" />
                  <span>Espace Vendeur</span>
                </Link>
              )}
              {user && user.role === "ADMIN" && (
                <Link
                  href="/admin/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-3 py-2.5 rounded-xl font-semibold text-xs text-amber-200 bg-amber-500/20 border border-amber-400/40 flex items-center gap-2"
                >
                  <ShieldCheck className="w-4 h-4 text-amber-400" />
                  <span>Plateforme Admin</span>
                </Link>
              )}
            </nav>

            {user ? (
              <div className="pt-3 border-t border-stone-800/80 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-stone-200">
                    {user.first_name || user.email.split("@")[0]}
                  </p>
                  <span className="text-[10px] text-amber-400 font-mono uppercase">
                    {user.role}
                  </span>
                </div>
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-stone-900 border border-stone-800 text-stone-300 hover:text-rose-400 text-xs transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Déconnexion</span>
                </button>
              </div>
            ) : (
              <div className="pt-3 border-t border-stone-800/80 flex items-center gap-2">
                <button
                  onClick={() => {
                    quickCustomerLogin();
                    setMobileMenuOpen(false);
                  }}
                  className="flex-1 py-2 rounded-xl text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-center"
                >
                  Client (Test)
                </button>
                <button
                  onClick={() => {
                    quickSellerLogin();
                    setMobileMenuOpen(false);
                  }}
                  className="flex-1 py-2 rounded-xl text-xs font-medium bg-violet-500/10 text-violet-400 border border-violet-500/20 text-center"
                >
                  Vendeur (Test)
                </button>
              </div>
            )}
          </div>
        )}
      </header>

      {/* Manual Login Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0b101c] border border-stone-800 rounded-2xl p-6 max-w-sm w-full shadow-2xl relative">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="font-serif font-black text-lg text-amber-300">M</span>
                <h3 className="text-base font-serif font-medium text-stone-100">Connexion Maison</h3>
              </div>
              <button
                onClick={() => setShowLoginModal(false)}
                className="text-stone-400 hover:text-stone-100"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-stone-400 mb-4">
              Accédez à votre espace privé et à vos commandes d&apos;exception.
            </p>

            {loginError && (
              <div className="p-3 mb-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {loginError}
              </div>
            )}

            <form onSubmit={handleManualLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-stone-300 mb-1">Adresse Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="votre.email@maison.luxury"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#070a12] border border-stone-800 text-xs text-white focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-stone-300 mb-1">Mot de passe</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#070a12] border border-stone-800 text-xs text-white focus:outline-none focus:border-amber-400"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowLoginModal(false)}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-stone-900 hover:bg-stone-800 text-xs font-medium text-stone-300"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 disabled:opacity-50 text-xs font-semibold text-stone-950 transition-colors"
                >
                  {submitting ? "Connexion..." : "Se connecter"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
