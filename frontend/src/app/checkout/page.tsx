"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  PayPalScriptProvider,
  PayPalButtons
} from "@paypal/react-paypal-js";
import {
  ShoppingBag,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  ShieldCheck,
  CreditCard,
  XCircle,
  Package,
  RotateCcw
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
      setError(err instanceof Error ? err.message : "Failed to load cart");
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
      setError(err instanceof Error ? err.message : "Checkout failed");
    } finally {
      setIsReserving(false);
    }
  };

  // 1. Success confirmation view
  if (completedOrder) {
    return (
      <main className="min-h-screen py-16 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 sm:p-12 text-center space-y-6 shadow-2xl backdrop-blur-sm">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/30">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Payment Successful
            </span>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white">Order Confirmed!</h1>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              Your PayPal payment has been captured and inventory finalized with full transaction integrity.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-left space-y-2 max-w-md mx-auto text-sm">
            <div className="flex justify-between text-slate-400">
              <span>Order Number:</span>
              <span className="font-mono font-bold text-white">{completedOrder.order_number}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Amount Paid:</span>
              <span className="font-bold text-emerald-400">${completedOrder.amount} {completedOrder.currency}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Payment Status:</span>
              <span className="font-semibold text-emerald-400 uppercase">{completedOrder.status}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Order Status:</span>
              <span className="font-semibold text-white uppercase">{completedOrder.order_status}</span>
            </div>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href={`/orders/${completedOrder.order_id}`}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors shadow-lg shadow-indigo-600/30"
            >
              View Order
            </Link>
            <Link
              href="/"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm transition-colors"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      </main>
    );
  }

  // 2. Cancellation view
  if (isCancelled) {
    return (
      <main className="min-h-screen py-16 px-4 sm:px-6 lg:px-8 max-w-2xl mx-auto">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 sm:p-12 text-center space-y-6 shadow-2xl">
          <div className="w-16 h-16 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center mx-auto border border-amber-500/30">
            <XCircle className="w-10 h-10" />
          </div>

          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Payment Cancelled
            </span>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">Checkout was cancelled</h1>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              Your PayPal transaction was cancelled. The reserved inventory stock has been safely restored to available inventory.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 max-w-md mx-auto">
            <span>Order Status: </span>
            <strong className="text-red-400 uppercase">CANCELLED</strong>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => {
                setIsCancelled(false);
                setActiveOrder(null);
                loadCart();
              }}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Try Again</span>
            </button>
            <Link
              href="/"
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm transition-colors"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-5">
        <div>
          <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors mb-2">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Products</span>
          </Link>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Checkout</h1>
        </div>
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl">
          <ShieldCheck className="w-4 h-4" />
          <span>Real PayPal Sandbox</span>
        </div>
      </div>

      {/* Guest Warning */}
      {!user && (
        <div className="p-5 rounded-2xl bg-indigo-950/40 border border-indigo-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-white">Customer Account Required</p>
            <p className="text-xs text-indigo-300/80 mt-0.5">
              Sign in as a customer to checkout and authorize sandbox payments.
            </p>
          </div>
          <button
            onClick={quickCustomerLogin}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 whitespace-nowrap"
          >
            1-Click Customer Sign In
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Order Summary */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <ShoppingBag className="w-5 h-5 text-indigo-400" />
              Order Summary
            </h2>

            {loadingCart ? (
              <div className="py-8 text-center text-xs text-slate-500 animate-pulse">
                Loading cart items...
              </div>
            ) : !cart || cart.items.length === 0 ? (
              <div className="py-8 text-center space-y-3">
                <p className="text-sm text-slate-400">Your cart is empty.</p>
                <Link
                  href="/"
                  className="inline-block px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200"
                >
                  Browse Products
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-slate-800">
                {cart.items.map((item) => (
                  <div key={item.id} className="py-3.5 flex items-center justify-between text-sm">
                    <div className="space-y-0.5 pr-4">
                      <p className="font-semibold text-white">
                        {item.variant?.product?.name || "Fashion Product"}
                      </p>
                      <p className="text-xs text-slate-400 font-mono">
                        SKU: {item.variant?.sku || item.variant_id.slice(0, 8)}
                      </p>
                      <p className="text-xs text-slate-500">
                        Qty: {item.quantity} &times; ${item.unit_price}
                      </p>
                    </div>
                    <div className="text-right font-bold text-white">
                      ${item.line_total}
                    </div>
                  </div>
                ))}

                <div className="pt-4 space-y-2">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Subtotal</span>
                    <span>${cart.subtotal}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Estimated Shipping</span>
                    <span className="text-emerald-400 font-medium">FREE</span>
                  </div>
                  <div className="flex justify-between text-base font-extrabold text-white pt-2 border-t border-slate-800">
                    <span>Total</span>
                    <span className="text-indigo-400">${cart.subtotal} USD</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Payment & PayPal Sandbox */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm space-y-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-indigo-400" />
              Payment
            </h2>

            {/* Step 1: Initialize local checkout order if not yet created */}
            {!activeOrder ? (
              <div className="space-y-4">
                <p className="text-xs text-slate-400 leading-relaxed">
                  Proceeding will reserve your items in database inventory with row-level locking and initialize your order.
                </p>
                <button
                  onClick={handleStartCheckout}
                  disabled={!user || !cart || cart.items.length === 0 || isReserving}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 transition-all"
                >
                  {isReserving ? "Reserving Stock & Initializing..." : "Proceed to Payment"}
                </button>
              </div>
            ) : (
              /* Step 2: Order is PENDING_PAYMENT, render PayPal Sandbox */
              <div className="space-y-4">
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Order Ref:</span>
                    <span className="font-mono text-white font-semibold">{activeOrder.order_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Status:</span>
                    <span className="text-amber-400 font-semibold">{activeOrder.status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total to Pay:</span>
                    <span className="text-white font-bold">${activeOrder.total} USD</span>
                  </div>
                </div>

                {/* PayPal Client Check */}
                {!paypalClientId ? (
                  <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-2">
                    <p className="font-bold flex items-center gap-1.5">
                      <AlertCircle className="w-4 h-4 text-amber-400" />
                      PayPal Sandbox is not configured
                    </p>
                    <p className="text-amber-300/80 leading-relaxed">
                      Please set <code className="bg-black/40 px-1 py-0.5 rounded text-[11px]">NEXT_PUBLIC_PAYPAL_CLIENT_ID</code> in your frontend environment variables to render the official PayPal buttons.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
                      Pay with PayPal Sandbox
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
                            // Call server API to create PayPal order using authoritative DB order total
                            const resp = await api.createPayPalOrder(activeOrder.id);
                            return resp.paypal_order_id;
                          }}
                          onApprove={async (data) => {
                            // Server-side capture
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
                            setError("PayPal encountered an error. Please try again.");
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
