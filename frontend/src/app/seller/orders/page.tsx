"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShoppingBag,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  Package,
  Layers,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
} from "lucide-react";
import SellerNav from "@/components/SellerNav";
import { api, SellerOrder } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function SellerOrdersPage() {
  const { user, loading: authLoading, quickSellerLogin } = useAuth();
  const [orders, setOrders] = useState<SellerOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [expandedOrderId, setExpandedOrderId] = useState<string | null>(null);

  const fetchOrders = async (status?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSellerOrders(status === "ALL" ? undefined : status);
      setOrders(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load seller orders");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && (user.role === "SELLER" || user.role === "ADMIN")) {
      fetchOrders(statusFilter);
    } else {
      setLoading(false);
    }
  }, [user, statusFilter]);

  // Auth Guard
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!user || (user.role !== "SELLER" && user.role !== "ADMIN")) {
    return (
      <main className="min-h-screen bg-slate-950 py-16 px-4">
        <div className="max-w-md mx-auto text-center space-y-6 bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <h1 className="text-xl font-bold text-white">Seller Access Required</h1>
          <p className="text-xs text-slate-400">
            Sign in as an authorized merchant to access your seller-scoped order data.
          </p>
          <button
            onClick={quickSellerLogin}
            className="w-full py-2.5 px-4 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2"
          >
            <Package className="w-4 h-4" />
            <span>Sign In as Demo Seller</span>
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 pb-20">
      <SellerNav />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-6">
        {/* Header & Filter Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Seller Order Stream
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Multi-vendor order fulfillment view showing only line items belonging to your catalog.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchOrders(statusFilter)}
              disabled={loading}
              className="p-2 rounded-lg text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors"
              title="Refresh orders"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {["ALL", "CONFIRMED", "PENDING_PAYMENT", "CANCELLED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                statusFilter === st
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-white"
              }`}
            >
              {st === "ALL"
                ? "All Orders"
                : st === "CONFIRMED"
                ? "Confirmed / Paid"
                : st === "PENDING_PAYMENT"
                ? "Pending Payment"
                : "Cancelled"}
            </button>
          ))}
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Orders List */}
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="h-28 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse"
              />
            ))}
          </div>
        ) : orders.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-4 shadow-xl">
            <div className="w-12 h-12 mx-auto rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <ShoppingBag className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">No matching orders</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              There are currently no orders containing items from your catalog with status &quot;{statusFilter}&quot;.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((ord) => {
              const isExpanded = expandedOrderId === ord.id;

              return (
                <div
                  key={ord.id}
                  className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-700/80 transition-colors shadow-lg"
                >
                  {/* Order Card Summary */}
                  <div className="p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 text-indigo-400 flex items-center justify-center flex-shrink-0">
                        <ShoppingBag className="w-5 h-5" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono font-bold text-sm text-white">
                            {ord.order_number}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              ord.status === "CONFIRMED"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : ord.status === "PENDING_PAYMENT"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-red-500/10 text-red-400 border border-red-500/20"
                            }`}
                          >
                            {ord.status}
                          </span>
                          {ord.payment_status && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                              Payment: {ord.payment_status}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400">
                          Date: {new Date(ord.created_at).toLocaleString()} &bull; Currency: {ord.currency}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 self-end md:self-center">
                      <div className="text-right">
                        <p className="text-xs text-slate-400">Your Sales Share</p>
                        <p className="text-base sm:text-lg font-black font-mono text-emerald-400">
                          ${Number(ord.seller_subtotal).toFixed(2)}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          {ord.seller_total_quantity} item(s) from your shop
                        </p>
                      </div>

                      <button
                        onClick={() =>
                          setExpandedOrderId(isExpanded ? null : ord.id)
                        }
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                      >
                        <Layers className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Items</span>
                        {isExpanded ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Items Table (Only Seller's Items) */}
                  {isExpanded && (
                    <div className="bg-slate-950/60 border-t border-slate-800/80 p-5 space-y-3">
                      <div className="text-xs font-bold text-slate-300 flex items-center justify-between">
                        <span>Items Purchased from Your Store (Historical Snapshot)</span>
                        <span className="text-[11px] font-normal text-slate-500">
                          Filtered to preserve customer privacy &amp; marketplace vendor isolation
                        </span>
                      </div>

                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs text-slate-300">
                          <thead className="text-[10px] uppercase font-semibold text-slate-400 border-b border-slate-800">
                            <tr>
                              <th className="py-2 px-3">Product Name</th>
                              <th className="py-2 px-3">SKU</th>
                              <th className="py-2 px-3">Variant</th>
                              <th className="py-2 px-3 text-right">Unit Price</th>
                              <th className="py-2 px-3 text-center">Qty</th>
                              <th className="py-2 px-3 text-right">Line Total</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60 font-mono">
                            {ord.items.map((item) => (
                              <tr key={item.id} className="hover:bg-slate-900/40">
                                <td className="py-2.5 px-3 font-sans font-semibold text-white">
                                  {item.product_name}
                                </td>
                                <td className="py-2.5 px-3 text-slate-400">
                                  {item.sku}
                                </td>
                                <td className="py-2.5 px-3 font-sans text-slate-300">
                                  {item.size || "-"}
                                  {item.color ? ` / ${item.color}` : ""}
                                </td>
                                <td className="py-2.5 px-3 text-right">
                                  ${Number(item.unit_price).toFixed(2)}
                                </td>
                                <td className="py-2.5 px-3 text-center font-bold text-white">
                                  {item.quantity}
                                </td>
                                <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                                  ${Number(item.line_total).toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
