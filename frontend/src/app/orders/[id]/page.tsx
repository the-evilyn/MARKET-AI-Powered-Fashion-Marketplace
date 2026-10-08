"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Package,
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
  CreditCard,
  Receipt,
  Truck
} from "lucide-react";
import { api, Order } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function OrderDetailPage() {
  const params = useParams();
  const orderId = params?.id as string;
  const { user, token } = useAuth();

  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrder = async () => {
      if (!orderId || !token) return;
      setLoading(true);
      setError(null);
      try {
        const data = await api.getOrder(orderId);
        setOrder(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load order details");
      } finally {
        setLoading(false);
      }
    };
    fetchOrder();
  }, [orderId, token]);

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "CONFIRMED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-4 h-4" />
            CONFIRMED
          </span>
        );
      case "PROCESSING":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Clock className="w-4 h-4" />
            PROCESSING
          </span>
        );
      case "SHIPPED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Truck className="w-4 h-4" />
            SHIPPED
          </span>
        );
      case "DELIVERED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-4 h-4" />
            DELIVERED
          </span>
        );
      case "PENDING_PAYMENT":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-4 h-4" />
            PENDING PAYMENT
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/20">
            <XCircle className="w-4 h-4" />
            CANCELLED
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-300">
            {status}
          </span>
        );
    }
  };

  return (
    <main className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-8">
      {/* Navigation */}
      <div>
        <Link
          href="/orders"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to All Orders</span>
        </Link>
      </div>

      {loading && (
        <div className="h-72 rounded-2xl bg-slate-900/50 border border-slate-800 animate-pulse" />
      )}

      {error && (
        <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-white">Order not found</p>
            <p className="text-xs text-red-300/80 mt-1">{error}</p>
          </div>
        </div>
      )}

      {order && !loading && (
        <div className="space-y-6">
          {/* Header Card */}
          <div className="p-6 sm:p-8 rounded-3xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-indigo-400" />
                <h1 className="text-xl sm:text-2xl font-mono font-extrabold text-white">
                  {order.order_number}
                </h1>
              </div>
              <p className="text-xs text-slate-400">
                Created on {new Date(order.created_at).toLocaleString()}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {renderStatusBadge(order.status)}
              {order.payment_status && (
                <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                  {order.payment_provider || "PAYPAL"}: {order.payment_status}
                </span>
              )}
            </div>
          </div>

          {/* Multi-Vendor Packages / Sub-Orders Section */}
          {order.sub_orders && order.sub_orders.length > 0 ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Package className="w-5 h-5 text-indigo-400" />
                  Shipment Packages ({order.sub_orders.length})
                </h2>
                <span className="text-xs text-slate-400">
                  Items fulfilled individually by each seller
                </span>
              </div>

              <div className="space-y-4">
                {order.sub_orders.map((subOrder, idx) => {
                  const subItems = order.items.filter(
                    (it) => it.sub_order_id === subOrder.id || it.seller_id === subOrder.seller_id
                  );
                  return (
                    <div
                      key={subOrder.id}
                      className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm space-y-4"
                    >
                      {/* Sub-Order Header */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                              Package {idx + 1}
                            </span>
                            <span className="font-mono text-xs font-semibold text-white">
                              {subOrder.sub_order_number}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 font-mono">
                            Seller ID: {subOrder.seller_id}
                          </p>
                        </div>

                        <div className="flex items-center gap-2">
                          {renderStatusBadge(subOrder.status)}
                        </div>
                      </div>

                      {/* Tracking / Carrier Banner */}
                      {(subOrder.carrier || subOrder.tracking_number) && (
                        <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/20 flex flex-wrap items-center justify-between gap-2 text-xs">
                          <div className="flex items-center gap-2 text-indigo-300">
                            <Truck className="w-4 h-4 text-indigo-400" />
                            <span>
                              Carrier: <strong className="text-white">{subOrder.carrier || "Standard Delivery"}</strong>
                            </span>
                          </div>
                          {subOrder.tracking_number && (
                            <div className="text-slate-300">
                              Tracking #:{" "}
                              <span className="font-mono font-bold text-white bg-slate-800/80 px-2 py-0.5 rounded">
                                {subOrder.tracking_number}
                              </span>
                            </div>
                          )}
                          {subOrder.shipped_at && (
                            <span className="text-[11px] text-slate-400">
                              Shipped on {new Date(subOrder.shipped_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Package Items */}
                      <div className="divide-y divide-slate-800/60">
                        {subItems.length > 0 ? (
                          subItems.map((item) => (
                            <div key={item.id} className="py-3 flex items-center justify-between text-sm">
                              <div className="space-y-0.5 pr-4">
                                <p className="font-semibold text-white">{item.product_name}</p>
                                <p className="text-xs font-mono text-slate-400">SKU: {item.sku}</p>
                                <p className="text-xs text-slate-500">
                                  Qty: {item.quantity} &times; ${item.unit_price}
                                </p>
                              </div>
                              <div className="text-right font-bold text-white">
                                ${item.line_total}
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="py-2 text-xs text-slate-500">
                            {order.items.length} item(s) in this order
                          </div>
                        )}
                      </div>

                      {/* Sub-order subtotal */}
                      <div className="pt-3 border-t border-slate-800/60 flex justify-between text-xs text-slate-400">
                        <span>Package Subtotal</span>
                        <span className="font-bold text-white">${subOrder.total}</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Order Financial Breakdown */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 backdrop-blur-sm">
                <div className="space-y-2 max-w-xs ml-auto text-sm">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Subtotal</span>
                    <span>${order.subtotal}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Shipping</span>
                    <span className="text-emerald-400 font-semibold">FREE</span>
                  </div>
                  <div className="flex justify-between text-lg font-black text-white pt-2 border-t border-slate-800">
                    <span>Total</span>
                    <span className="text-indigo-400">${order.total} {order.currency}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Fallback Flat Line Items Table */
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 backdrop-blur-sm space-y-4">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Package className="w-4 h-4 text-indigo-400" />
                Purchased Items Snapshot
              </h2>

              <div className="divide-y divide-slate-800/80">
                {order.items.map((item) => (
                  <div key={item.id} className="py-4 flex items-center justify-between text-sm">
                    <div className="space-y-1 pr-4">
                      <p className="font-bold text-white">{item.product_name}</p>
                      <p className="text-xs font-mono text-slate-400">SKU: {item.sku}</p>
                      <p className="text-xs text-slate-500">
                        Qty: {item.quantity} &times; ${item.unit_price}
                      </p>
                    </div>
                    <div className="text-right font-extrabold text-white">
                      ${item.line_total}
                    </div>
                  </div>
                ))}
              </div>

              {/* Financial Breakdown */}
              <div className="pt-6 border-t border-slate-800 space-y-2 max-w-xs ml-auto text-sm">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Subtotal</span>
                  <span>${order.subtotal}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Shipping</span>
                  <span className="text-emerald-400 font-semibold">FREE</span>
                </div>
                <div className="flex justify-between text-lg font-black text-white pt-2 border-t border-slate-800">
                  <span>Total</span>
                  <span className="text-indigo-400">${order.total} {order.currency}</span>
                </div>
              </div>
            </div>
          )}

          {/* Payment Information Card */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 text-xs text-slate-400 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CreditCard className="w-5 h-5 text-indigo-400" />
              <div>
                <p className="font-semibold text-slate-200">Payment Gateway</p>
                <p className="text-slate-400">
                  Provider: <span className="font-medium text-white">{order.payment_provider || "PAYPAL"}</span> &bull; Status: <span className="font-medium text-white">{order.payment_status || "PENDING"}</span>
                </p>
              </div>
            </div>

            <Link
              href="/"
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs transition-colors"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      )}
    </main>
  );
}
