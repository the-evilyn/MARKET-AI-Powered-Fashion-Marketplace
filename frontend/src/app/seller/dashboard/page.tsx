"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  DollarSign,
  Package,
  Boxes,
  ShoppingBag,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  ArrowRight,
  RefreshCw,
  ShieldAlert,
  Layers,
} from "lucide-react";
import SellerNav from "@/components/SellerNav";
import {
  api,
  Product,
  SellerDashboardKPIs,
  SellerInventoryItem,
  SellerOrder,
} from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function SellerDashboardPage() {
  const { user, loading: authLoading, quickSellerLogin } = useAuth();
  const [kpis, setKpis] = useState<SellerDashboardKPIs | null>(null);
  const [recentProducts, setRecentProducts] = useState<Product[]>([]);
  const [lowStockItems, setLowStockItems] = useState<SellerInventoryItem[]>([]);
  const [recentOrders, setRecentOrders] = useState<SellerOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpisData, productsData, inventoryData, ordersData] =
        await Promise.all([
          api.getSellerDashboard(),
          api.getSellerProducts(),
          api.getSellerInventory(true), // low stock only
          api.getSellerOrders(),
        ]);
      setKpis(kpisData);
      setRecentProducts(productsData.slice(0, 5));
      setLowStockItems(inventoryData.slice(0, 5));
      setRecentOrders(ordersData.slice(0, 5));
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load dashboard metrics"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && (user.role === "SELLER" || user.role === "ADMIN")) {
      fetchDashboardData();
    } else {
      setLoading(false);
    }
  }, [user]);

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
          <div className="space-y-2">
            <h1 className="text-xl font-bold text-white">Seller Access Required</h1>
            <p className="text-xs text-slate-400 leading-relaxed">
              This area is reserved for authenticated marketplace merchants and administrators.
            </p>
          </div>
          <div className="pt-2">
            <button
              onClick={quickSellerLogin}
              className="w-full py-2.5 px-4 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2"
            >
              <Package className="w-4 h-4" />
              <span>Sign In as Demo Seller</span>
            </button>
            <div className="mt-4">
              <Link
                href="/"
                className="text-xs text-slate-400 hover:text-white transition-colors"
              >
                &larr; Return to Marketplace Homepage
              </Link>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 pb-20">
      <SellerNav />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {/* Header Title & Refresh */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Seller Dashboard
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Real-time multi-vendor metrics, authoritative sales, and inventory reconciliation.
            </p>
          </div>
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 transition-colors w-fit"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh Data</span>
          </button>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading Skeleton */}
        {loading && !kpis ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
              <div
                key={n}
                className="h-28 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse p-5"
              />
            ))}
          </div>
        ) : kpis ? (
          /* Primary KPI Grid */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Sales */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 relative overflow-hidden group hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Confirmed Sales
                </span>
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                  <DollarSign className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl sm:text-3xl font-black text-white">
                ${Number(kpis.total_sales).toFixed(2)}
              </div>
              <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                <span>Excludes pending/cancelled orders</span>
              </p>
            </div>

            {/* Total Items Sold */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 relative overflow-hidden group hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Units Sold
                </span>
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                  <ShoppingBag className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl sm:text-3xl font-black text-white">
                {kpis.total_items_sold}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                From {kpis.confirmed_orders} confirmed orders
              </p>
            </div>

            {/* Products & Active */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 relative overflow-hidden group hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Catalog Listings
                </span>
                <div className="w-8 h-8 rounded-lg bg-violet-500/10 text-violet-400 flex items-center justify-center">
                  <Package className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl sm:text-3xl font-black text-white">
                {kpis.total_products}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                <span className="text-emerald-400 font-semibold">{kpis.active_products} active</span> listings
              </p>
            </div>

            {/* Total Variants & Inventory health */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 relative overflow-hidden group hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  SKU Variants
                </span>
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
                  <Layers className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl sm:text-3xl font-black text-white">
                {kpis.total_variants}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                {kpis.low_stock_variants > 0 ? (
                  <span className="text-amber-400 font-semibold">{kpis.low_stock_variants} low in stock</span>
                ) : (
                  <span className="text-slate-400">All inventory healthy</span>
                )}
              </p>
            </div>
          </div>
        ) : null}

        {/* Secondary KPI Row: Orders Status Breakdown & Inventory Alerts */}
        {kpis && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center flex-shrink-0">
                <ShoppingBag className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400">Total Orders</p>
                <p className="text-lg font-bold text-white">{kpis.total_orders}</p>
              </div>
            </div>

            <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center flex-shrink-0">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400">Confirmed Orders</p>
                <p className="text-lg font-bold text-emerald-400">{kpis.confirmed_orders}</p>
              </div>
            </div>

            <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center flex-shrink-0">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400">Pending Payment</p>
                <p className="text-lg font-bold text-amber-400">{kpis.pending_orders}</p>
              </div>
            </div>

            <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center flex-shrink-0">
                <XCircle className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-400">Cancelled Orders</p>
                <p className="text-lg font-bold text-slate-300">{kpis.cancelled_orders}</p>
              </div>
            </div>
          </div>
        )}

        {/* Content Section: Low Stock Warnings & Recent Orders */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Low Stock Alerts */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <h3 className="text-base font-bold text-white">Low Stock Warnings</h3>
              </div>
              <Link
                href="/seller/inventory"
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
              >
                <span>Manage Stock</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {lowStockItems.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No low stock alerts. All variants have sufficient inventory.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/80">
                {lowStockItems.map((item) => (
                  <div
                    key={item.id}
                    className="py-3 flex items-center justify-between gap-4 text-xs"
                  >
                    <div>
                      <p className="font-semibold text-white truncate max-w-[200px]">
                        {item.product_name}
                      </p>
                      <p className="text-slate-400 font-mono text-[11px]">
                        SKU: {item.sku} {item.size ? `(${item.size})` : ""}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        {item.quantity_available} left
                      </span>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        Threshold: {item.low_stock_threshold}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Seller Orders */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShoppingBag className="w-4 h-4 text-indigo-400" />
                <h3 className="text-base font-bold text-white">Recent Orders</h3>
              </div>
              <Link
                href="/seller/orders"
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
              >
                <span>View All Orders</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {recentOrders.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No orders containing your products yet.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/80">
                {recentOrders.map((ord) => (
                  <div
                    key={ord.id}
                    className="py-3 flex items-center justify-between gap-4 text-xs"
                  >
                    <div>
                      <p className="font-mono font-bold text-white">
                        {ord.order_number}
                      </p>
                      <p className="text-slate-400 text-[11px]">
                        {ord.items.length} item(s) &bull;{" "}
                        {new Date(ord.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-white">
                        ${Number(ord.seller_subtotal).toFixed(2)}
                      </p>
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          ord.status === "CONFIRMED"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : ord.status === "PENDING_PAYMENT"
                            ? "bg-amber-500/10 text-amber-400"
                            : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {ord.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Products Table Preview */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Package className="w-4 h-4 text-violet-400" />
              <h3 className="text-base font-bold text-white">Product Catalog Quick View</h3>
            </div>
            <Link
              href="/seller/products"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
            >
              <span>Manage Products</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {recentProducts.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-xs">
              No products found in your catalog.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Product</th>
                    <th className="py-2.5 px-4">Base Price</th>
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4">Variants</th>
                    <th className="py-2.5 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {recentProducts.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-medium text-white">{p.name}</td>
                      <td className="py-3 px-4 font-mono">${Number(p.base_price).toFixed(2)}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            p.status === "ACTIVE"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : p.status === "DRAFT"
                              ? "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                              : "bg-red-500/10 text-red-400 border border-red-500/20"
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {p.variants ? p.variants.length : 0} variant(s)
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          href="/seller/products"
                          className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                        >
                          Edit &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
