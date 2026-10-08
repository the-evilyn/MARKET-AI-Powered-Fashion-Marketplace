"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Store, RefreshCw, AlertCircle, ArrowLeft } from "lucide-react";
import SellerNav from "@/components/SellerNav";
import StoreSettingsForm from "@/components/seller/StoreSettingsForm";
import { api, SellerStoreProfile } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function SellerSettingsPage() {
  const { user, loading: authLoading, quickSellerLogin } = useAuth();
  const [profile, setProfile] = useState<SellerStoreProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSellerStoreProfile();
      setProfile(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load store profile.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && user?.role === "SELLER") {
      fetchProfile();
    } else if (!authLoading && !user) {
      setLoading(false);
    }
  }, [authLoading, user]);

  if (authLoading || (loading && user)) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <SellerNav />
        <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 animate-pulse">
          <div className="h-8 w-48 bg-slate-800 rounded-lg"></div>
          <div className="h-32 bg-slate-800 rounded-3xl"></div>
          <div className="h-96 bg-slate-800 rounded-3xl"></div>
        </main>
      </div>
    );
  }

  if (!user || user.role !== "SELLER") {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <SellerNav />
        <main className="max-w-md mx-auto px-4 py-24 text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/20">
            <Store className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Merchant Access Required</h1>
            <p className="text-xs text-slate-400 mt-2">
              You must be signed in with an active SELLER account to access store settings.
            </p>
          </div>
          <div className="pt-2">
            <button
              onClick={() => quickSellerLogin()}
              className="w-full py-3 px-4 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all"
            >
              Sign in as Verified Seller
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <SellerNav />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/seller/dashboard"
              className="text-xs font-semibold text-slate-400 hover:text-white transition-colors inline-flex items-center gap-1 group mb-2"
            >
              <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
              <span>Back to Dashboard</span>
            </Link>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-3">
            <span>Store Settings & Branding</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage your boutique identity, public URL slug, contact details, and editorial media.
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-medium flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
            <button
              onClick={fetchProfile}
              className="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-white text-xs font-semibold transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {profile && (
          <StoreSettingsForm
            initialProfile={profile}
            onProfileUpdated={(updated) => setProfile(updated)}
          />
        )}
      </main>
    </div>
  );
}
