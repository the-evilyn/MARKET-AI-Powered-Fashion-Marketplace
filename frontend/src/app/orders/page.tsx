"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Package, ArrowRight, Clock, CheckCircle2, XCircle, AlertCircle, ShoppingBag, Truck, Sparkles } from "lucide-react";
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
      setError(err instanceof Error ? err.message : "Impossible de charger les commandes");
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
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5" />
            CONFIRMÉE
          </span>
        );
      case "PROCESSING":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono">
            <Clock className="w-3.5 h-3.5" />
            EN PRÉPARATION
          </span>
        );
      case "SHIPPED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-400/20 text-amber-200 border border-amber-400/40 font-mono">
            <Truck className="w-3.5 h-3.5" />
            EXPÉDIÉE
          </span>
        );
      case "DELIVERED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5" />
            LIVRÉE
          </span>
        );
      case "PENDING_PAYMENT":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
            <Clock className="w-3.5 h-3.5" />
            EN ATTENTE
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono">
            <XCircle className="w-3.5 h-3.5" />
            ANNULÉE
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-stone-900 text-stone-300 font-mono">
            {status}
          </span>
        );
    }
  };

  return (
    <main className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-stone-800/80 pb-5">
        <div>
          <h1 className="text-3xl font-serif font-bold text-stone-100 tracking-tight">
            Historique des Commandes
          </h1>
          <p className="text-xs text-stone-400 mt-1 font-light">
            Retrouvez l&apos;ensemble de vos acquisitions et le suivi de vos expéditions.
          </p>
        </div>

        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#0c101c] border border-stone-800 hover:border-amber-400/40 text-xs font-semibold text-stone-200 self-start sm:self-auto transition-colors"
        >
          <ShoppingBag className="w-4 h-4 text-amber-400" />
          <span>Explorer les Collections</span>
        </Link>
      </div>

      {!user && (
        <div className="p-8 rounded-3xl bg-[#0c101c] border border-amber-500/20 text-center space-y-4 shadow-xl">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto border border-amber-500/20">
            <Package className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-serif font-bold text-stone-100">
              Connexion requise pour consulter vos commandes
            </h3>
            <p className="text-xs text-stone-400 max-w-sm mx-auto font-light">
              L&apos;historique de vos pièces d&apos;exception est strictement sécurisé sur votre espace privé.
            </p>
          </div>
          <button
            onClick={quickCustomerLogin}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 text-xs font-bold uppercase tracking-wider shadow-lg shadow-amber-400/10 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Connexion Client Démo</span>
          </button>
        </div>
      )}

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-2xl bg-stone-900/50 border border-stone-800 animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-3">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {user && !loading && !error && orders.length === 0 && (
        <div className="text-center py-16 px-6 rounded-3xl bg-[#0c101c] border border-stone-800 max-w-md mx-auto space-y-4 shadow-xl">
          <div className="w-16 h-16 rounded-2xl bg-stone-900 text-stone-500 flex items-center justify-center mx-auto border border-stone-800">
            <Package className="w-8 h-8 text-amber-400/70" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-serif font-bold text-stone-100">
              Aucune commande enregistrée
            </h3>
            <p className="text-xs text-stone-400 font-light">
              Vous n&apos;avez pas encore passé de commande. Découvrez les dernières créations de nos Maisons partenaires.
            </p>
          </div>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 text-xs font-bold uppercase tracking-wider shadow-lg shadow-amber-400/10 transition-all"
          >
            <span>Découvrir la Boutique</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {user && !loading && orders.length > 0 && (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="p-5 rounded-2xl bg-[#0c101c] border border-stone-800/90 hover:border-amber-400/40 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-md"
            >
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-sm font-bold text-stone-100">
                    {order.order_number}
                  </span>
                  {renderStatusBadge(order.status)}
                  {order.payment_status && (
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider bg-stone-900 text-stone-300 border border-stone-800 font-mono">
                      Paiement : {order.payment_status} ({order.payment_provider || "PAYPAL"})
                    </span>
                  )}
                </div>
                <p className="text-xs text-stone-400 flex flex-wrap items-center gap-2 font-mono">
                  <span>Commandé le {new Date(order.created_at).toLocaleDateString("fr-FR")}</span>
                  <span>&bull;</span>
                  <span>{order.items.length} {order.items.length === 1 ? "article" : "articles"}</span>
                  {order.sub_orders && order.sub_orders.length > 0 && (
                    <>
                      <span>&bull;</span>
                      <span className="text-amber-300 font-medium">
                        {order.sub_orders.length} {order.sub_orders.length === 1 ? "colis" : "colis"}
                      </span>
                    </>
                  )}
                </p>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-6 pt-2 sm:pt-0 border-t sm:border-t-0 border-stone-800/80">
                <div className="text-right">
                  <span className="text-[10px] uppercase tracking-wider text-stone-400 block font-mono">Total</span>
                  <span className="text-base font-extrabold text-amber-300 font-mono">
                    ${order.total} {order.currency}
                  </span>
                </div>

                <Link
                  href={`/orders/${order.id}`}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-stone-900 hover:bg-stone-800 text-xs font-semibold text-stone-200 border border-stone-800 hover:border-amber-400/40 transition-colors"
                >
                  <span>Détails</span>
                  <ArrowRight className="w-3.5 h-3.5 text-amber-400" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
