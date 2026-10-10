"use client";

import React from "react";
import Link from "next/link";
import { ShieldAlert, RefreshCw, ArrowLeft, Lock } from "lucide-react";
import AdminNav from "@/components/AdminNav";
import { useAuth } from "@/context/AuthContext";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-400">
        <div className="text-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-400 mx-auto" />
          <p className="text-sm font-medium text-stone-300">Verifying administrator authorization...</p>
        </div>
      </div>
    );
  }

  if (!user || user.role !== "ADMIN") {
    return (
      <main className="min-h-screen bg-slate-950 flex items-center justify-center py-16 px-4">
        <div className="max-w-md w-full text-center space-y-6 bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-amber-500/10 border border-amber-500/25 flex items-center justify-center text-amber-400">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h1 className="text-xl font-bold text-white tracking-tight">
              Administrator Access Required
            </h1>
            <p className="text-xs text-slate-400 leading-relaxed">
              This area is strictly restricted to platform administrators with the{" "}
              <span className="font-semibold text-amber-300">ADMIN</span> role.
              Your current session role is{" "}
              <span className="font-semibold text-slate-300">
                {user ? user.role : "UNAUTHENTICATED"}
              </span>
              .
            </p>
          </div>

          <div className="pt-3 flex flex-col gap-2.5">
            <Link
              href="/"
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white transition-all flex items-center justify-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to Marketplace</span>
            </Link>
          </div>

          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-center gap-1.5 text-[11px] text-slate-500">
            <Lock className="w-3.5 h-3.5" />
            <span>Strict server-side RBAC validation enforced on all operations</span>
          </div>
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <AdminNav />
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </div>
    </div>
  );
}
