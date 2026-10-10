"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  PayPalScriptProvider,
  PayPalButtons,
} from "@paypal/react-paypal-js";
import {
  ShoppingBag,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  ShieldCheck,
  CreditCard,
  XCircle,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { api, Cart, Order, PayPalCaptureResponse } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function CheckoutPage() {
  const router = useRouter();
  const { user, token, quickCustomerLogin, refreshCartCount } = useAuth();

  const [cart, setCart] = useState<Cart | null>(null);
  const [loadingCart, setLoadingCart] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Order & Payment state
  const [activeOrder, setActiveOrder] = useState<Order | null>(null);
  const [isReserving, setIsReserving] = useState(false);
  const [completedOrder, setCompletedOrder] = useState<PayPalCaptureResponse | null>(null);
  const [isCancelled, setIsCancelled] = useState(false);

  const paypalClientId = process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID || "";

  const loadCart = async () => {
    if (!token) {
      setLoadingCart(false);
      return;
    }
    setLoadingCart(true);
    setError(null);
    try {
      const data = await api.getCart();
      setCart(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Impossible de charger le panier");
    } finally {
      setLoadingCart(false);
    }
  };

  useEffect(() => {
    loadCart();
  }, [token]);

  // Initiate checkout: create internal order & reserve stock
  const handleStartCheckout = async () => {
    setIsReserving(true);
    setError(null);
    try {
      const order = await api.checkout();
      setActiveOrder(order);
      await refreshCartCount();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Échec de l'initialisation de la commande");
    } finally {
      setIsReserving(false);
    }
  };

  // 1. Success confirmation view
  if (completedOrder) {
    return (
      <main className="min-h-[80vh] py-16 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto flex items-center justify-center">
        <div className="bg-[#0c101c] border border-stone-800/90 rounded-3xl p-8 sm:p-12 text-center space-y-6 shadow-2xl backdrop-blur-sm w-full">
          <div className="w-16 h-16 rounded-full bg-emerald-500/15 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/30">
            <CheckCircle2 className="w-9 h-9" />
          </div>

          <div className="space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider px-3.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              Paiement Confirmé avec Succès
            </span>
            <h1 className="text-3xl sm:text-4xl font-serif font-bold text-stone-100">
              Commande Enregistrée !
            </h1>
            <p className="text-stone-400 text-xs sm:text-sm max-w-md mx-auto font-light leading-relaxed">
              Votre transaction PayPal a été capturée et l&apos;inventaire alloué avec intégrité transactionnelle.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#070a12] border border-stone-800/80 text-left space-y-2.5 max-w-md mx-auto text-xs font-mono">
            <div className="flex justify-between text-stone-400">
              <span>Numéro de commande :</span>
              <span className="font-bold text-stone-100">{completedOrder.order_number}</span>
            </div>
            <div className="flex justify-between text-stone-400">
              <span>Montant réglé :</span>
              <span className="font-bold text-amber-300">${completedOrder.amount} {completedOrder.currency}</span>
            </div>
            <div className="flex justify-between text-stone-400">
              <span>Statut paiement :</span>
              <span className="font-semibold text-emerald-400 uppercase">{completedOrder.status}</span>
            </div>
            <div className="flex justify-between text-stone-400">
              <span>Statut commande :</span>
              <span className="font-semibold text-stone-200 uppercase">{completedOrder.order_status}</span>
            </div>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href={`/orders/${completedOrder.order_id}`}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-amber-400/10"
            >
              Consulter la Commande
            </Link>
            <Link
              href="/"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-stone-900 hover:bg-stone-800 text-stone-300 font-semibold text-xs transition-colors border border-stone-800"
            >
              Continuer les Achats
            </Link>
          </div>
        </div>
      </main>
    );
  }

  // 2. Cancellation view
  if (isCancelled) {
    return (
      <main className="min-h-[80vh] py-16 px-4 sm:px-6 lg:px-8 max-w-2xl mx-auto flex items-center justify-center">
        <div className="bg-[#0c101c] border border-stone-800/90 rounded-3xl p-8 sm:p-12 text-center space-y-6 shadow-2xl w-full">
          <div className="w-16 h-16 rounded-full bg-amber-500/15 text-amber-400 flex items-center justify-center mx-auto border border-amber-500/30">
            <XCircle className="w-9 h-9" />
          </div>

          <div className="space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider px-3.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
              Paiement Annulé
            </span>
            <h1 className="text-2xl sm:text-3xl font-serif font-bold text-stone-100">
              Le paiement a été interrompu
            </h1>
            <p className="text-stone-400 text-xs sm:text-sm max-w-md mx-auto font-light leading-relaxed">
              Votre transaction PayPal a été annulée. La réservation temporaire de stock a été restituée à l&apos;inventaire.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#070a12] border border-stone-800 text-xs text-stone-400 max-w-md mx-auto font-mono">
            <span>Statut commande : </span>
            <strong className="text-rose-400 uppercase">ANNULÉE</strong>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => {
                setIsCancelled(false);
                setActiveOrder(null);
                loadCart();
              }}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 font-bold text-xs uppercase tracking-wider transition-all shadow-md shadow-amber-400/10"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Réessayer le Paiement</span>
            </button>
            <Link
              href="/"
              className="px-5 py-2.5 rounded-xl bg-stone-900 hover:bg-stone-800 text-stone-300 font-semibold text-xs transition-colors border border-stone-800"
            >
              Retour aux Collections
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-stone-800/80 pb-5">
        <div>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs text-stone-400 hover:text-amber-300 transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-amber-400" />
            <span>Retour aux collections</span>
          </Link>
          <h1 className="text-3xl font-serif font-bold text-stone-100 tracking-tight">
            Finalisation de Commande
          </h1>
        </div>
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3.5 py-1.5 rounded-xl font-mono">
          <ShieldCheck className="w-4 h-4" />
          <span>PayPal Sandbox Sécurisé</span>
        </div>
      </div>

      {/* Guest Warning */}
      {!user && (
        <div className="p-5 rounded-2xl bg-[#0c101c] border border-amber-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <p className="text-sm font-serif font-bold text-stone-100">Compte Client Requis</p>
            <p className="text-xs text-stone-400 mt-0.5 font-light">
              Connectez-vous pour finaliser votre commande et autoriser le paiement.
            </p>
          </div>
          <button
            onClick={quickCustomerLogin}
            className="px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 text-xs font-bold uppercase tracking-wider shadow-md shadow-amber-400/10 whitespace-nowrap transition-all"
          >
            <span className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Connexion Client 1-Clic</span>
            </span>
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-3">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Order Summary */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-[#0c101c] border border-stone-800/90 rounded-2xl p-6 backdrop-blur-sm space-y-4 shadow-xl">
            <h2 className="text-base font-serif font-bold text-stone-100 flex items-center gap-2">
              <ShoppingBag className="w-4 h-4 text-amber-400" />
              <span>Récapitulatif de votre Sélection</span>
            </h2>

            {loadingCart ? (
              <div className="py-8 text-center text-xs text-stone-500 animate-pulse font-mono">
                Chargement des articles...
              </div>
            ) : !cart || cart.items.length === 0 ? (
              <div className="py-8 text-center space-y-3">
                <p className="text-xs text-stone-400">Votre sélection est vide.</p>
                <Link
                  href="/"
                  className="inline-block px-4 py-2 rounded-xl bg-stone-900 hover:bg-stone-800 text-xs font-semibold text-stone-200 border border-stone-800"
                >
                  Découvrir les Pièces
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-stone-800/80">
                {cart.items.map((item) => (
                  <div key={item.id} className="py-3.5 flex items-center justify-between text-xs">
                    <div className="space-y-0.5 pr-4">
                      <p className="font-semibold text-stone-100">
                        {item.variant?.product?.name || "Pièce de Créateur"}
                      </p>
                      <p className="text-[11px] text-stone-400 font-mono">
                        SKU : {item.variant?.sku || item.variant_id.slice(0, 8)}
                      </p>
                      <p className="text-[11px] text-stone-500 font-mono">
                        Qté : {item.quantity} &times; ${item.unit_price}
                      </p>
                    </div>
                    <div className="text-right font-bold text-amber-300 font-mono text-sm">
                      ${item.line_total}
                    </div>
                  </div>
                ))}

                <div className="pt-4 space-y-2 font-mono">
                  <div className="flex justify-between text-xs text-stone-400">
                    <span>Sous-total</span>
                    <span className="text-stone-200">${cart.subtotal}</span>
                  </div>
                  <div className="flex justify-between text-xs text-stone-400">
                    <span>Expédition Haute Protection</span>
                    <span className="text-emerald-400 font-medium">OFFERTE</span>
                  </div>
                  <div className="flex justify-between text-sm font-bold text-stone-100 pt-2 border-t border-stone-800">
                    <span className="font-serif">Total</span>
                    <span className="text-amber-300 text-base">${cart.subtotal} USD</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Payment & PayPal Sandbox */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-[#0c101c] border border-stone-800/90 rounded-2xl p-6 backdrop-blur-sm space-y-6 shadow-xl">
            <h2 className="text-base font-serif font-bold text-stone-100 flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-amber-400" />
              <span>Règlement Sécurisé</span>
            </h2>

            {/* Step 1: Initialize local checkout order if not yet created */}
            {!activeOrder ? (
              <div className="space-y-4">
                <p className="text-xs text-stone-400 leading-relaxed font-light">
                  En procédant, vos articles seront réservés dans la base de données avec verrouillage atomique et votre commande initialisée.
                </p>
                <button
                  onClick={handleStartCheckout}
                  disabled={!user || !cart || cart.items.length === 0 || isReserving}
                  className="w-full py-3.5 px-4 rounded-xl bg-amber-400 hover:bg-amber-300 disabled:opacity-50 text-stone-950 font-bold text-xs uppercase tracking-wider shadow-lg shadow-amber-400/10 transition-all"
                >
                  {isReserving ? "Réservation du Stock..." : "Confirmer la Sélection & Régler"}
                </button>
              </div>
            ) : (
              /* Step 2: Order is PENDING_PAYMENT, render PayPal Sandbox */
              <div className="space-y-4">
                <div className="p-3.5 rounded-xl bg-[#070a12] border border-stone-800 text-xs space-y-1 font-mono">
                  <div className="flex justify-between">
                    <span className="text-stone-400">Réf. Commande :</span>
                    <span className="text-stone-100 font-semibold">{activeOrder.order_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-400">Statut :</span>
                    <span className="text-amber-400 font-semibold">{activeOrder.status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-400">Montant à régler :</span>
                    <span className="text-amber-300 font-bold">${activeOrder.total} USD</span>
                  </div>
                </div>

                {/* PayPal Client Check */}
                {!paypalClientId ? (
                  <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-2">
                    <p className="font-bold flex items-center gap-1.5">
                      <AlertCircle className="w-4 h-4 text-amber-400" />
                      PayPal Sandbox non configuré
                    </p>
                    <p className="text-amber-300/80 leading-relaxed font-mono text-[11px]">
                      Veuillez configurer NEXT_PUBLIC_PAYPAL_CLIENT_ID dans les variables d&apos;environnement.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-[11px] text-stone-400 uppercase tracking-wider font-mono font-semibold">
                      Paiement via PayPal Sandbox
                    </p>
                    <div className="min-h-[120px] rounded-xl overflow-hidden">
                      <PayPalScriptProvider
                        options={{
                          clientId: paypalClientId,
                          currency: "USD",
                          intent: "capture",
                        }}
                      >
                        <PayPalButtons
                          style={{
                            layout: "vertical",
                            color: "gold",
                            shape: "rect",
                            label: "pay",
                          }}
                          createOrder={async () => {
                            const resp = await api.createPayPalOrder(activeOrder.id);
                            return resp.paypal_order_id;
                          }}
                          onApprove={async (data) => {
                            const captureResp = await api.capturePayPalPayment(data.orderID);
                            setCompletedOrder(captureResp);
                            await refreshCartCount();
                          }}
                          onCancel={async (data) => {
                            const orderId = (data as { orderID?: string })?.orderID;
                            if (orderId && typeof orderId === "string") {
                              await api.cancelPayPalPayment(orderId);
                            }
                            setIsCancelled(true);
                            await refreshCartCount();
                          }}
                          onError={(err) => {
                            console.error("PayPal JS SDK Error:", err);
                            setError("Une erreur est survenue lors de la transaction PayPal. Veuillez réessayer.");
                          }}
                        />
                      </PayPalScriptProvider>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
