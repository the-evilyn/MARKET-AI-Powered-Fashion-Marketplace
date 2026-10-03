"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Boxes,
  RefreshCw,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  SlidersHorizontal,
  X,
  ShieldAlert,
  Package,
} from "lucide-react";
import SellerNav from "@/components/SellerNav";
import { api, SellerInventoryItem } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function SellerInventoryPage() {
  const { user, loading: authLoading, quickSellerLogin } = useAuth();
  const [items, setItems] = useState<SellerInventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lowStockFilter, setLowStockFilter] = useState(false);

  // Stock Adjustment / Set Modal
  const [selectedItem, setSelectedItem] = useState<SellerInventoryItem | null>(null);
  const [actionType, setActionType] = useState<"ADJUST" | "SET">("ADJUST");
  const [adjustDelta, setAdjustDelta] = useState<number>(0);
  const [adjustReason, setAdjustReason] = useState<string>("");
  const [absoluteStock, setAbsoluteStock] = useState<number>(0);
  const [thresholdVal, setThresholdVal] = useState<number>(5);
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const fetchInventory = async (lowStock: boolean = lowStockFilter) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSellerInventory(lowStock);
      setItems(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load inventory records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && (user.role === "SELLER" || user.role === "ADMIN")) {
      fetchInventory(lowStockFilter);
    } else {
      setLoading(false);
    }
  }, [user, lowStockFilter]);

  const openAdjustModal = (item: SellerInventoryItem, type: "ADJUST" | "SET") => {
    setSelectedItem(item);
    setActionType(type);
    setAdjustDelta(0);
    setAdjustReason("");
    setAbsoluteStock(item.quantity_on_hand);
    setThresholdVal(item.low_stock_threshold);
    setModalError(null);
  };

  const handleStockUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem) return;
    setModalError(null);
    setSubmitting(true);
    try {
      if (actionType === "ADJUST") {
        if (adjustDelta === 0) {
          throw new Error("Adjustment delta cannot be 0");
        }
        await api.adjustSellerInventory(selectedItem.variant_id, {
          adjustment: adjustDelta,
          reason: adjustReason || undefined,
        });
      } else {
        await api.updateSellerInventory(selectedItem.variant_id, {
          quantity_on_hand: absoluteStock,
          low_stock_threshold: thresholdVal,
        });
      }
      setSelectedItem(null);
      await fetchInventory(lowStockFilter);
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err.message : "Stock update failed");
    } finally {
      setSubmitting(false);
    }
  };

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
            Sign in as an authorized merchant to access your inventory and stock levels.
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
        {/* Header and Filter Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Inventory &amp; Stock Levels
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Row-level locked inventory, reserved stock protection, and physical on-hand adjustments.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Low stock filter toggle */}
            <button
              onClick={() => setLowStockFilter(!lowStockFilter)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
                lowStockFilter
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                  : "bg-slate-900 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Low Stock Only</span>
            </button>

            <button
              onClick={() => fetchInventory(lowStockFilter)}
              disabled={loading}
              className="p-2 rounded-lg text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors"
              title="Refresh inventory"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Inventory Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-8 space-y-3">
              {[1, 2, 3, 4].map((n) => (
                <div
                  key={n}
                  className="h-14 rounded-xl bg-slate-800/40 animate-pulse"
                />
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="p-12 text-center space-y-4">
              <div className="w-12 h-12 mx-auto rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                <Boxes className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">No inventory items found</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                {lowStockFilter
                  ? "No variants are currently at or below the low stock threshold."
                  : "Create SKU variants for your products to begin tracking inventory."}
              </p>
              {lowStockFilter ? (
                <button
                  onClick={() => setLowStockFilter(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white"
                >
                  Clear Filter
                </button>
              ) : (
                <Link
                  href="/seller/products"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all"
                >
                  <span>Go to Products</span>
                </Link>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/70 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Product &amp; SKU</th>
                    <th className="py-3 px-4">Variant Info</th>
                    <th className="py-3 px-4 text-center">On Hand</th>
                    <th className="py-3 px-4 text-center">Reserved</th>
                    <th className="py-3 px-4 text-center">Available</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-right">Stock Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4 font-sans">
                        <p className="font-bold text-white truncate max-w-[220px]">
                          {item.product_name}
                        </p>
                        <p className="text-slate-400 font-mono text-[11px] mt-0.5">
                          SKU: {item.sku}
                        </p>
                      </td>
                      <td className="py-3.5 px-4 font-sans text-slate-300">
                        <span className="inline-block mr-2 font-semibold">
                          {item.size || "Standard"}
                        </span>
                        {item.color && (
                          <span className="text-slate-400 text-[11px]">
                            ({item.color})
                          </span>
                        )}
                        <p className="text-[11px] text-emerald-400 font-mono font-bold mt-0.5">
                          ${Number(item.price).toFixed(2)}
                        </p>
                      </td>
                      <td className="py-3.5 px-4 text-center font-bold text-white">
                        {item.quantity_on_hand}
                      </td>
                      <td className="py-3.5 px-4 text-center text-amber-400 font-semibold">
                        {item.quantity_reserved}
                      </td>
                      <td className="py-3.5 px-4 text-center font-bold">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-xs ${
                            item.quantity_available > item.low_stock_threshold
                              ? "bg-emerald-500/10 text-emerald-400 font-bold"
                              : item.quantity_available > 0
                              ? "bg-amber-500/10 text-amber-400 font-bold"
                              : "bg-red-500/10 text-red-400 font-bold"
                          }`}
                        >
                          {item.quantity_available}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center font-sans">
                        {item.is_low_stock && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            <AlertTriangle className="w-3 h-3" />
                            Low (th: {item.low_stock_threshold})
                          </span>
                        )}
                        {!item.is_in_stock && (
                          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
                            Out of Stock
                          </span>
                        )}
                        {item.is_in_stock && !item.is_low_stock && (
                          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-medium text-slate-500">
                            Healthy
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-right font-sans">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => openAdjustModal(item, "ADJUST")}
                            className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600 hover:text-white transition-colors"
                          >
                            +/- Adjust
                          </button>
                          <button
                            onClick={() => openAdjustModal(item, "SET")}
                            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                            title="Set absolute stock quantity or threshold"
                          >
                            <SlidersHorizontal className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Stock Adjustment / Set Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl relative">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">
                  {actionType === "ADJUST" ? "Adjust Stock Quantity" : "Set Absolute Stock Level"}
                </h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  SKU: {selectedItem.sku} &bull; {selectedItem.product_name}
                </p>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current State Indicator */}
            <div className="grid grid-cols-3 gap-2 bg-slate-950 p-3 rounded-xl border border-slate-800 text-center font-mono text-xs">
              <div>
                <span className="text-slate-500 block text-[10px]">ON HAND</span>
                <span className="font-bold text-white text-sm">
                  {selectedItem.quantity_on_hand}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">RESERVED</span>
                <span className="font-bold text-amber-400 text-sm">
                  {selectedItem.quantity_reserved}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">AVAILABLE</span>
                <span className="font-bold text-emerald-400 text-sm">
                  {selectedItem.quantity_available}
                </span>
              </div>
            </div>

            {modalError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                {modalError}
              </div>
            )}

            <form onSubmit={handleStockUpdate} className="space-y-4">
              {actionType === "ADJUST" ? (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Adjustment Delta (+/- integer)
                    </label>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setAdjustDelta((prev) => prev - 1)}
                        className="px-3 py-2 rounded-xl bg-slate-800 text-slate-200 hover:bg-slate-700 font-bold"
                      >
                        -
                      </button>
                      <input
                        type="number"
                        required
                        value={adjustDelta}
                        onChange={(e) => setAdjustDelta(parseInt(e.target.value) || 0)}
                        placeholder="e.g. 10 or -5"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-mono text-center text-white focus:outline-none focus:border-indigo-500"
                      />
                      <button
                        type="button"
                        onClick={() => setAdjustDelta((prev) => prev + 1)}
                        className="px-3 py-2 rounded-xl bg-slate-800 text-slate-200 hover:bg-slate-700 font-bold"
                      >
                        +
                      </button>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Resulting on-hand:{" "}
                      <span className="font-bold text-white font-mono">
                        {selectedItem.quantity_on_hand + adjustDelta}
                      </span>{" "}
                      (must remain &ge; reserved: {selectedItem.quantity_reserved})
                    </p>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Reason / Note (Optional)
                    </label>
                    <input
                      type="text"
                      value={adjustReason}
                      onChange={(e) => setAdjustReason(e.target.value)}
                      placeholder="e.g. Supplier delivery, inventory correction"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Quantity On Hand * (cannot be less than reserved: {selectedItem.quantity_reserved})
                    </label>
                    <input
                      type="number"
                      min={selectedItem.quantity_reserved}
                      required
                      value={absoluteStock}
                      onChange={(e) => setAbsoluteStock(parseInt(e.target.value) || 0)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-mono text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Low Stock Threshold
                    </label>
                    <input
                      type="number"
                      min="0"
                      required
                      value={thresholdVal}
                      onChange={(e) => setThresholdVal(parseInt(e.target.value) || 0)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-mono text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </>
              )}

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedItem(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
                >
                  {submitting ? "Updating..." : "Save Stock"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
