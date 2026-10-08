"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Package, ArrowRight, Clock, CheckCircle2, XCircle, AlertCircle, ShoppingBag, Truck } from "lucide-react";
import { api, Order } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function OrdersHistoryPage() {
  const { user, token, quickCustomerLogin } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.getOrders();
      setOrders(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load orders");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [token]);

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "CONFIRMED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            CONFIRMED
          </span>
        );
      case "PROCESSING":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Clock className="w-3.5 h-3.5" />
            PROCESSING
          </span>
        );
      case "SHIPPED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Truck className="w-3.5 h-3.5" />
            SHIPPED
          </span>
        );
      case "DELIVERED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            DELIVERED
          </span>
        );
      case "PENDING_PAYMENT":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-3.5 h-3.5" />
            PENDING PAYMENT
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
            <XCircle className="w-3.5 h-3.5" />
            CANCELLED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">
            {status}
          </span>
        );
    }
  };

  return (
    <main className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Order History</h1>
          <p className="text-xs text-slate-400 mt-1">
            Review past purchases, payment outcomes, and order snapshots.
          </p>
        </div>

        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-200 self-start sm:self-auto"
        >
          <ShoppingBag className="w-4 h-4 text-indigo-400" />
          <span>Browse Products</span>
        </Link>
      </div>

      {!user && (
        <div className="p-6 rounded-2xl bg-indigo-950/40 border border-indigo-500/20 text-center space-y-3">
          <Package className="w-10 h-10 text-indigo-400 mx-auto" />
          <h3 className="text-base font-bold text-white">Sign in to view your orders</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Order history is isolated to your customer account.
          </p>
          <button
            onClick={quickCustomerLogin}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
          >
            1-Click Customer Sign In
          </button>
        </div>
      )}

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-2xl bg-slate-900/50 border border-slate-800 animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {user && !loading && !error && orders.length === 0 && (
        <div className="text-center py-16 px-4 rounded-3xl bg-slate-900/30 border border-slate-800 max-w-md mx-auto space-y-3">
          <Package className="w-10 h-10 text-slate-500 mx-auto" />
          <h3 className="text-base font-bold text-white">No orders found</h3>
          <p className="text-xs text-slate-400">
            You haven&apos;t placed any orders yet. Browse our fashion collection to get started.
          </p>
          <Link
            href="/"
            className="inline-block px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white"
          >
            Shop Now
          </Link>
        </div>
      )}

      {user && !loading && orders.length > 0 && (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-sm font-bold text-white">
                    {order.order_number}
                  </span>
                  {renderStatusBadge(order.status)}
                  {order.payment_status && (
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider bg-slate-800 text-slate-300">
                      Payment: {order.payment_status} ({order.payment_provider || "PAYPAL"})
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 flex flex-wrap items-center gap-2">
                  <span>Placed on {new Date(order.created_at).toLocaleDateString()}</span>
                  <span>&bull;</span>
                  <span>{order.items.length} {order.items.length === 1 ? "item" : "items"}</span>
                  {order.sub_orders && order.sub_orders.length > 0 && (
                    <>
                      <span>&bull;</span>
                      <span className="text-indigo-400 font-medium">
                        {order.sub_orders.length} {order.sub_orders.length === 1 ? "shipment" : "shipments"}
                      </span>
                    </>
                  )}
                </p>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-6 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800">
                <div className="text-right">
                  <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Total</span>
                  <span className="text-base font-extrabold text-white">
                    ${order.total} {order.currency}
                  </span>
                </div>

                <Link
                  href={`/orders/${order.id}`}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
                >
                  <span>Details</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
