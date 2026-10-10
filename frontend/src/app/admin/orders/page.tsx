"use client";

import React, { useEffect, useState } from "react";
import {
  ShoppingBag,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  Filter,
  ShieldAlert,
  CreditCard,
  Truck,
  Package,
  Layers,
  ChevronRight,
  X,
} from "lucide-react";
import { api, Order } from "@/lib/api";

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAdminOrders({
        status: statusFilter === "ALL" ? undefined : statusFilter,
        limit: 50,
      });
      setOrders(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load orders");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [statusFilter]);

  const filteredOrders = orders.filter((o) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      o.order_number.toLowerCase().includes(q) ||
      o.customer_id.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <ShoppingBag className="w-6 h-6 text-amber-400" />
            <span>Global Orders Supervision</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Cross-marketplace order monitoring, vendor fulfillment tracking, and payment validation.
          </p>
        </div>
        <button
          onClick={fetchOrders}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 border border-slate-800 hover:border-amber-500/30 text-stone-200 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-amber-400" : ""}`} />
          <span>Refresh Orders</span>
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-slate-400 hover:text-white">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Filters and Search Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by order number or customer ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-stone-100 placeholder-slate-500 focus:outline-none focus:border-amber-500/50 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-stone-200 focus:outline-none focus:border-amber-500/50"
            >
              <option value="ALL">All Statuses</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="PROCESSING">PROCESSING</option>
              <option value="SHIPPED">SHIPPED</option>
              <option value="DELIVERED">DELIVERED</option>
              <option value="PENDING_PAYMENT">PENDING_PAYMENT</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="rounded-2xl bg-slate-900/40 border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Order</th>
                <th className="px-4 py-3.5">Date</th>
                <th className="px-4 py-3.5">Total Amount</th>
                <th className="px-4 py-3.5">Order Status</th>
                <th className="px-4 py-3.5">Payment</th>
                <th className="px-4 py-3.5">Fulfillment</th>
                <th className="px-5 py-3.5 text-right">Inspection</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading && orders.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-slate-500">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto text-amber-400 mb-2" />
                    <span>Loading marketplace orders...</span>
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-slate-500">
                    No orders found matching the filter criteria.
                  </td>
                </tr>
              ) : (
                filteredOrders.map((o) => {
                  let statusBadge = "bg-slate-800 text-slate-400 border-slate-700";
                  if (o.status === "CONFIRMED")
                    statusBadge = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
                  else if (o.status === "PROCESSING")
                    statusBadge = "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
                  else if (o.status === "SHIPPED")
                    statusBadge = "bg-violet-500/10 text-violet-400 border-violet-500/20";
                  else if (o.status === "DELIVERED")
                    statusBadge = "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
                  else if (o.status === "PENDING_PAYMENT")
                    statusBadge = "bg-amber-500/10 text-amber-400 border-amber-500/20";
                  else if (o.status === "CANCELLED")
                    statusBadge = "bg-rose-500/10 text-rose-400 border-rose-500/20";

                  const subOrdersCount = o.sub_orders?.length || 0;

                  return (
                    <tr key={o.id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="px-5 py-4">
                        <p className="font-bold text-white font-mono">{o.order_number}</p>
                        <span className="text-[10px] text-slate-500 font-mono">
                          Customer: {o.customer_id.slice(0, 8)}...
                        </span>
                      </td>

                      <td className="px-4 py-4 text-slate-400 text-[11px]">
                        {new Date(o.created_at).toLocaleDateString()}
                      </td>

                      <td className="px-4 py-4">
                        <span className="font-bold text-white">
                          {Number(o.total).toFixed(2)} {o.currency}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${statusBadge}`}
                        >
                          {o.status}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        <div className="flex items-center gap-1.5">
                          <CreditCard className="w-3.5 h-3.5 text-slate-400" />
                          <span className="text-[11px] font-medium text-slate-300">
                            {o.payment_status || "PENDING"}
                          </span>
                        </div>
                      </td>

                      <td className="px-4 py-4 text-slate-300 text-[11px]">
                        <span className="inline-flex items-center gap-1">
                          <Layers className="w-3.5 h-3.5 text-slate-500" />
                          <span>
                            {subOrdersCount} {subOrdersCount === 1 ? "vendor package" : "vendor packages"}
                          </span>
                        </span>
                      </td>

                      <td className="px-5 py-4 text-right">
                        <button
                          onClick={() => setSelectedOrder(o)}
                          className="px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-stone-200 border border-slate-700 hover:border-amber-500/30 transition-all inline-flex items-center gap-1"
                        >
                          <span>Inspect</span>
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Orders Count Footer */}
        {orders.length > 0 && (
          <div className="px-5 py-3.5 bg-slate-900/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {filteredOrders.length} of {orders.length} loaded orders
            </span>
            <span className="text-[11px] text-slate-500 font-medium">
              Real-time platform supervision
            </span>
          </div>
        )}
      </div>

      {/* Order Detail Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white font-mono">
                    {selectedOrder.order_number}
                  </h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-slate-800 text-slate-300 border border-slate-700">
                    {selectedOrder.status}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Placed on {new Date(selectedOrder.created_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setSelectedOrder(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Financial & Payment Summary */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-500">
                  Financial Totals
                </span>
                <p className="text-lg font-bold text-white">
                  {Number(selectedOrder.total).toFixed(2)} {selectedOrder.currency}
                </p>
                <p className="text-[11px] text-slate-400">
                  Subtotal: {Number(selectedOrder.subtotal).toFixed(2)} {selectedOrder.currency}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-500">
                  Payment Gateway
                </span>
                <p className="text-sm font-bold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{selectedOrder.payment_status || "PENDING"}</span>
                </p>
                <p className="text-[11px] text-slate-400">
                  Provider: {selectedOrder.payment_provider || "PAYPAL"}
                </p>
              </div>
            </div>

            {/* Sub-Orders Fulfillment Breakdown */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Truck className="w-4 h-4 text-amber-400" />
                <span>Vendor Fulfillment Packages ({selectedOrder.sub_orders?.length || 0})</span>
              </h4>

              {(!selectedOrder.sub_orders || selectedOrder.sub_orders.length === 0) ? (
                <p className="text-xs text-slate-500 italic">No sub-order partitions found.</p>
              ) : (
                <div className="space-y-2">
                  {selectedOrder.sub_orders.map((so) => (
                    <div
                      key={so.id}
                      className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
                    >
                      <div>
                        <p className="font-bold text-white font-mono">{so.sub_order_number}</p>
                        <p className="text-[11px] text-slate-400">
                          Seller ID: <span className="font-mono text-slate-300">{so.seller_id.slice(0, 8)}...</span>
                        </p>
                        {so.tracking_number && (
                          <p className="text-[11px] text-indigo-400 mt-1">
                            Tracking: {so.carrier || "Carrier"} — {so.tracking_number}
                          </p>
                        )}
                      </div>
                      <div className="text-right sm:text-right">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                          {so.status}
                        </span>
                        <p className="font-bold text-white mt-1">
                          {Number(so.total).toFixed(2)} {so.currency}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Line Items Snapshot */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Package className="w-4 h-4 text-indigo-400" />
                <span>Line Items ({selectedOrder.items?.length || 0})</span>
              </h4>

              <div className="divide-y divide-slate-800/80 rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
                {(selectedOrder.items || []).map((it) => (
                  <div key={it.id} className="p-3 flex items-center justify-between text-xs">
                    <div>
                      <p className="font-bold text-white">{it.product_name}</p>
                      <p className="text-[10px] text-slate-400 font-mono">SKU: {it.sku}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-white">
                        {Number(it.line_total).toFixed(2)} {selectedOrder.currency}
                      </p>
                      <p className="text-[10px] text-slate-400">
                        {it.quantity} × {Number(it.unit_price).toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedOrder(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
