"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  Store,
  ShoppingBag,
  ShieldCheck,
  Clock,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
  Package,
} from "lucide-react";
import { api, AdminDashboardKPIs } from "@/lib/api";

export default function AdminDashboardPage() {
  const [kpis, setKpis] = useState<AdminDashboardKPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAdminDashboard();
      setKpis(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load admin metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Marketplace Supervision Dashboard
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Global metrics, seller compliance status, and real-time revenue analytics.
          </p>
        </div>
        <button
          onClick={fetchDashboard}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-900 border border-slate-800 hover:border-amber-500/30 text-stone-200 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-amber-400" : ""}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <ShieldAlert className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchDashboard}
            className="text-xs font-semibold underline hover:text-white"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeletons */}
      {loading && !kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-900 rounded-2xl border border-slate-800" />
          ))}
        </div>
      )}

      {/* KPI Cards Grid */}
      {kpis && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Users */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Total Accounts</span>
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                  <Users className="w-4 h-4" />
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{kpis.total_users}</p>
                <p className="text-[11px] text-emerald-400 font-medium mt-1">
                  {kpis.active_users} active accounts
                </p>
              </div>
            </div>

            {/* Total Sellers */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Merchants</span>
                <div className="w-8 h-8 rounded-lg bg-violet-500/10 text-violet-400 flex items-center justify-center">
                  <Package className="w-4 h-4" />
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{kpis.total_sellers}</p>
                <p className="text-[11px] text-violet-400 font-medium mt-1">
                  {kpis.active_sellers} active sellers
                </p>
              </div>
            </div>

            {/* Total Stores */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Storefronts</span>
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                  <Store className="w-4 h-4" />
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{kpis.total_stores}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[11px] text-emerald-400 font-medium">
                    {kpis.verified_stores} verified
                  </span>
                  {kpis.stores_awaiting_review > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">
                      {kpis.stores_awaiting_review} pending
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Total Orders */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Total Orders</span>
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-300 flex items-center justify-center">
                  <ShoppingBag className="w-4 h-4" />
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{kpis.total_orders}</p>
                <p className="text-[11px] text-amber-300/80 font-medium mt-1">
                  {kpis.total_paid_orders} paid orders
                </p>
              </div>
            </div>
          </div>

          {/* Revenue by Currency Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-900/90 border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                  <DollarSign className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Paid Revenue by Currency</h3>
                  <p className="text-[11px] text-slate-400">
                    Aggregated strictly from completed payments with zero currency conflation.
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-semibold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/25">
                Authoritative
              </span>
            </div>

            {kpis.sales_by_currency.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-2">
                No confirmed payment captures recorded yet.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pt-2">
                {kpis.sales_by_currency.map((sc) => (
                  <div
                    key={sc.currency}
                    className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between"
                  >
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 tracking-wider">
                        {sc.currency}
                      </span>
                      <p className="text-xl font-black text-white mt-0.5">
                        {Number(sc.total_sales).toFixed(2)} {sc.currency}
                      </p>
                    </div>
                    <span className="text-[11px] text-slate-400 font-medium">
                      {sc.order_count} {sc.order_count === 1 ? "order" : "orders"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Orders by Lifecycle Status */}
          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              <span>Order Lifecycle Status Breakdown</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {Object.entries(kpis.orders_by_status).map(([statusKey, count]) => {
                let colorClass = "text-slate-300 bg-slate-800/40 border-slate-700/50";
                if (statusKey === "CONFIRMED")
                  colorClass = "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
                else if (statusKey === "PROCESSING")
                  colorClass = "text-indigo-400 bg-indigo-500/10 border-indigo-500/20";
                else if (statusKey === "SHIPPED")
                  colorClass = "text-violet-400 bg-violet-500/10 border-violet-500/20";
                else if (statusKey === "DELIVERED")
                  colorClass = "text-cyan-400 bg-cyan-500/10 border-cyan-500/20";
                else if (statusKey === "PENDING_PAYMENT")
                  colorClass = "text-amber-400 bg-amber-500/10 border-amber-500/20";
                else if (statusKey === "CANCELLED")
                  colorClass = "text-rose-400 bg-rose-500/10 border-rose-500/20";

                return (
                  <div
                    key={statusKey}
                    className={`p-3 rounded-xl border text-center space-y-1 ${colorClass}`}
                  >
                    <span className="text-[10px] font-semibold uppercase tracking-wider block">
                      {statusKey.replace("_", " ")}
                    </span>
                    <p className="text-lg font-bold">{count}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Cards Hub */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <Link
              href="/admin/stores"
              className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-amber-500/40 hover:bg-slate-900/80 transition-all group space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-300 flex items-center justify-center">
                  <Store className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-amber-300 group-hover:translate-x-1 transition-all" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white group-hover:text-amber-300 transition-colors">
                  Store Moderation
                </h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Review seller storefronts, approve badges (`is_verified`), or suspend non-compliant merchants.
                </p>
              </div>
            </Link>

            <Link
              href="/admin/users"
              className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900/80 transition-all group space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                  <Users className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white group-hover:text-indigo-400 transition-colors">
                  User Management
                </h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Audit accounts across customers, merchants, and administrators. Manage activation states safely.
                </p>
              </div>
            </Link>

            <Link
              href="/admin/orders"
              className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-violet-500/50 hover:bg-slate-900/80 transition-all group space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-lg bg-violet-500/10 text-violet-400 flex items-center justify-center">
                  <ShoppingBag className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-violet-400 group-hover:translate-x-1 transition-all" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white group-hover:text-violet-400 transition-colors">
                  Global Orders Supervision
                </h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Track marketplace orders, payment records, and vendor fulfillment status across all merchants.
                </p>
              </div>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
