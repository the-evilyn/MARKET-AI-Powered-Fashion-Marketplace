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
  Truck,
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
        setError(err instanceof Error ? err.message : "Impossible de charger les détails de la commande");
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
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
            <CheckCircle2 className="w-4 h-4" />
            CONFIRMÉE
          </span>
        );
      case "PROCESSING":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono">
            <Clock className="w-4 h-4" />
            EN PRÉPARATION
          </span>
        );
      case "SHIPPED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-400/20 text-amber-200 border border-amber-400/40 font-mono">
            <Truck className="w-4 h-4" />
            EXPÉDIÉE
          </span>
        );
      case "DELIVERED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono">
            <CheckCircle2 className="w-4 h-4" />
            LIVRÉE
          </span>
        );
      case "PENDING_PAYMENT":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
            <Clock className="w-4 h-4" />
            EN ATTENTE
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono">
            <XCircle className="w-4 h-4" />
            ANNULÉE
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-stone-900 text-stone-300 font-mono">
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
          className="inline-flex items-center gap-1.5 text-xs text-stone-400 hover:text-amber-300 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5 text-amber-400" />
          <span>Retour à toutes les commandes</span>
        </Link>
      </div>

      {loading && (
        <div className="h-72 rounded-3xl bg-stone-900/50 border border-stone-800 animate-pulse" />
      )}

      {error && (
        <div className="p-6 rounded-3xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-stone-100">Commande introuvable</p>
            <p className="text-xs text-rose-300/80 mt-1">{error}</p>
          </div>
        </div>
      )}

      {order && !loading && (
        <div className="space-y-6">
          {/* Header Card */}
          <div className="p-6 sm:p-8 rounded-3xl bg-[#0c101c] border border-stone-800/90 backdrop-blur-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-amber-400" />
                <h1 className="text-xl sm:text-2xl font-mono font-bold text-stone-100">
                  {order.order_number}
                </h1>
              </div>
              <p className="text-xs text-stone-400 font-mono">
                Enregistrée le {new Date(order.created_at).toLocaleString("fr-FR")}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {renderStatusBadge(order.status)}
              {order.payment_status && (
                <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-stone-900 text-stone-300 border border-stone-800 font-mono">
                  {order.payment_provider || "PAYPAL"} : {order.payment_status}
                </span>
              )}
            </div>
          </div>

          {/* Multi-Vendor Packages / Sub-Orders Section */}
          {order.sub_orders && order.sub_orders.length > 0 ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-serif font-bold text-stone-100 flex items-center gap-2">
                  <Package className="w-5 h-5 text-amber-400" />
                  <span>Expéditions Multi-Créateurs ({order.sub_orders.length})</span>
                </h2>
                <span className="text-xs text-stone-400 font-mono">
                  Prise en charge individuelle par chaque Maison
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
                      className="bg-[#0c101c] border border-stone-800/90 rounded-3xl p-6 backdrop-blur-sm space-y-4 shadow-md"
                    >
                      {/* Sub-Order Header */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-stone-800/80">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-400/10 text-amber-300 border border-amber-500/20 font-mono">
                              Colis {idx + 1}
                            </span>
                            <span className="font-mono text-xs font-semibold text-stone-100">
                              {subOrder.sub_order_number}
                            </span>
                          </div>
                          <p className="text-[11px] text-stone-400 font-mono">
                            Maison Vendeur ID : {subOrder.seller_id}
                          </p>
                        </div>

                        <div className="flex items-center gap-2">
                          {renderStatusBadge(subOrder.status)}
                        </div>
                      </div>

                      {/* Tracking / Carrier Banner */}
                      {(subOrder.carrier || subOrder.tracking_number) && (
                        <div className="p-3.5 rounded-xl bg-[#070a12] border border-amber-500/20 flex flex-wrap items-center justify-between gap-2 text-xs">
                          <div className="flex items-center gap-2 text-amber-300">
                            <Truck className="w-4 h-4 text-amber-400" />
                            <span>
                              Transporteur : <strong className="text-stone-100">{subOrder.carrier || "Livraison Express Haute Couture"}</strong>
                            </span>
                          </div>
                          {subOrder.tracking_number && (
                            <div className="text-stone-300 font-mono">
                              N° de suivi :{" "}
                              <span className="font-bold text-amber-300 bg-stone-900 px-2 py-0.5 rounded border border-stone-800">
                                {subOrder.tracking_number}
                              </span>
                            </div>
                          )}
                          {subOrder.shipped_at && (
                            <span className="text-[11px] text-stone-400 font-mono">
                              Expédié le {new Date(subOrder.shipped_at).toLocaleDateString("fr-FR")}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Package Items */}
                      <div className="divide-y divide-stone-800/60">
                        {subItems.length > 0 ? (
                          subItems.map((item) => (
                            <div key={item.id} className="py-3 flex items-center justify-between text-xs">
                              <div className="space-y-0.5 pr-4">
                                <p className="font-semibold text-stone-100">{item.product_name}</p>
                                <p className="text-[11px] font-mono text-stone-400">SKU : {item.sku}</p>
                                <p className="text-[11px] text-stone-500 font-mono">
                                  Qté : {item.quantity} &times; ${item.unit_price}
                                </p>
                              </div>
                              <div className="text-right font-bold text-amber-300 font-mono text-sm">
                                ${item.line_total}
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="py-2 text-xs text-stone-500">
                            {order.items.length} article(s) dans cette commande
                          </div>
                        )}
                      </div>

                      {/* Sub-order subtotal */}
                      <div className="pt-3 border-t border-stone-800/60 flex justify-between text-xs text-stone-400 font-mono">
                        <span>Sous-total du colis</span>
                        <span className="font-bold text-amber-300">${subOrder.total}</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Order Financial Breakdown */}
              <div className="bg-[#0c101c] border border-stone-800/90 rounded-3xl p-6 sm:p-8 backdrop-blur-sm shadow-xl">
                <div className="space-y-2 max-w-xs ml-auto text-xs font-mono">
                  <div className="flex justify-between text-stone-400">
                    <span>Sous-total</span>
                    <span className="text-stone-200">${order.subtotal}</span>
                  </div>
                  <div className="flex justify-between text-stone-400">
                    <span>Livraison Haute Protection</span>
                    <span className="text-emerald-400 font-semibold">OFFERTE</span>
                  </div>
                  <div className="flex justify-between text-base font-bold text-stone-100 pt-2 border-t border-stone-800">
                    <span className="font-serif">Total de la commande</span>
                    <span className="text-amber-300">${order.total} {order.currency}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Fallback Flat Line Items Table */
            <div className="bg-[#0c101c] border border-stone-800/90 rounded-3xl p-6 sm:p-8 backdrop-blur-sm space-y-4 shadow-xl">
              <h2 className="text-base font-serif font-bold text-stone-100 flex items-center gap-2">
                <Package className="w-4 h-4 text-amber-400" />
                <span>Pièces Achetées</span>
              </h2>

              <div className="divide-y divide-stone-800/80">
                {order.items.map((item) => (
                  <div key={item.id} className="py-4 flex items-center justify-between text-xs">
                    <div className="space-y-1 pr-4">
                      <p className="font-bold text-stone-100">{item.product_name}</p>
                      <p className="text-[11px] font-mono text-stone-400">SKU : {item.sku}</p>
                      <p className="text-[11px] text-stone-500 font-mono">
                        Qté : {item.quantity} &times; ${item.unit_price}
                      </p>
                    </div>
                    <div className="text-right font-bold text-amber-300 font-mono text-sm">
                      ${item.line_total}
                    </div>
                  </div>
                ))}
              </div>

              {/* Financial Breakdown */}
              <div className="pt-6 border-t border-stone-800 space-y-2 max-w-xs ml-auto text-xs font-mono">
                <div className="flex justify-between text-stone-400">
                  <span>Sous-total</span>
                  <span className="text-stone-200">${order.subtotal}</span>
                </div>
                <div className="flex justify-between text-stone-400">
                  <span>Livraison Haute Protection</span>
                  <span className="text-emerald-400 font-semibold">OFFERTE</span>
                </div>
                <div className="flex justify-between text-base font-bold text-stone-100 pt-2 border-t border-stone-800">
                  <span className="font-serif">Total</span>
                  <span className="text-amber-300">${order.total} {order.currency}</span>
                </div>
              </div>
            </div>
          )}

          {/* Payment Information Card */}
          <div className="bg-[#0c101c]/60 border border-stone-800/80 rounded-2xl p-6 text-xs text-stone-400 flex items-center justify-between shadow-md">
            <div className="flex items-center gap-3">
              <CreditCard className="w-5 h-5 text-amber-400" />
              <div>
                <p className="font-semibold text-stone-200 font-serif">Passerelle de Paiement</p>
                <p className="text-stone-400 font-mono text-[11px]">
                  Fournisseur : <span className="text-stone-100">{order.payment_provider || "PAYPAL"}</span> &bull; Statut : <span className="text-stone-100">{order.payment_status || "PENDING"}</span>
                </p>
              </div>
            </div>

            <Link
              href="/"
              className="px-4 py-2 rounded-xl bg-stone-900 hover:bg-stone-800 text-stone-200 font-semibold text-xs transition-colors border border-stone-800"
            >
              Continuer les Achats
            </Link>
          </div>
        </div>
      )}
    </main>
  );
}
