"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Store,
  ShieldCheck,
  ShieldAlert,
  Search,
  ExternalLink,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Filter,
} from "lucide-react";
import { api, AdminStoreSummary } from "@/lib/api";

export default function AdminStoresPage() {
  const [stores, setStores] = useState<AdminStoreSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [verifiedFilter, setVerifiedFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Moderation Modal state
  const [selectedStore, setSelectedStore] = useState<AdminStoreSummary | null>(null);
  const [modalMode, setModalMode] = useState<"VERIFICATION" | "STATUS" | null>(null);
  const [pendingStatus, setPendingStatus] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  const fetchStores = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminStores({
        status: statusFilter === "ALL" ? undefined : statusFilter,
        is_verified:
          verifiedFilter === "ALL"
            ? undefined
            : verifiedFilter === "VERIFIED",
        q: searchQuery.trim() || undefined,
        page,
        page_size: 15,
      });
      setStores(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load stores");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStores();
  }, [page, statusFilter, verifiedFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchStores();
  };

  const handleToggleVerification = async (store: AdminStoreSummary) => {
    setSubmitting(true);
    setActionSuccess(null);
    setError(null);
    try {
      const targetVerified = !store.is_verified;
      await api.moderateAdminStore(store.id, { is_verified: targetVerified });
      setActionSuccess(
        `Store '${store.store_name}' verification badge ${targetVerified ? "granted" : "revoked"} successfully.`
      );
      setSelectedStore(null);
      setModalMode(null);
      await fetchStores();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update verification");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!selectedStore || !pendingStatus) return;
    setSubmitting(true);
    setActionSuccess(null);
    setError(null);
    try {
      await api.moderateAdminStore(selectedStore.id, {
        status: pendingStatus as "PENDING" | "ACTIVE" | "SUSPENDED" | "REJECTED",
      });
      setActionSuccess(
        `Store '${selectedStore.store_name}' status updated to ${pendingStatus}.`
      );
      setSelectedStore(null);
      setModalMode(null);
      await fetchStores();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update store status");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Store className="w-6 h-6 text-amber-400" />
            <span>Storefront Moderation & Governance</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Review multi-vendor storefronts, grant trusted verification badges, and manage compliance status.
          </p>
        </div>
        <button
          onClick={fetchStores}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 border border-slate-800 hover:border-amber-500/30 text-stone-200 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-amber-400" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Notifications */}
      {actionSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-slate-400 hover:text-white">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

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

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by store name, slug, or merchant email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-stone-100 placeholder-slate-500 focus:outline-none focus:border-amber-500/50 transition-colors"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-amber-500 hover:bg-amber-400 text-slate-950 transition-all shadow-sm shadow-amber-500/20"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-stone-200 focus:outline-none focus:border-amber-500/50"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="PENDING">PENDING</option>
              <option value="SUSPENDED">SUSPENDED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Badge:</span>
            <select
              value={verifiedFilter}
              onChange={(e) => {
                setVerifiedFilter(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-stone-200 focus:outline-none focus:border-amber-500/50"
            >
              <option value="ALL">All</option>
              <option value="VERIFIED">Verified Only</option>
              <option value="UNVERIFIED">Unverified Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table Section */}
      <div className="rounded-2xl bg-slate-900/40 border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Storefront</th>
                <th className="px-4 py-3.5">Merchant</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5">Verification</th>
                <th className="px-4 py-3.5">Created</th>
                <th className="px-5 py-3.5 text-right">Moderation Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading && stores.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto text-amber-400 mb-2" />
                    <span>Loading storefronts...</span>
                  </td>
                </tr>
              ) : stores.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                    No stores match your current filters.
                  </td>
                </tr>
              ) : (
                stores.map((s) => {
                  let statusBadge = "bg-slate-800 text-slate-400 border-slate-700";
                  if (s.status === "ACTIVE")
                    statusBadge = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
                  else if (s.status === "PENDING")
                    statusBadge = "bg-amber-500/10 text-amber-400 border-amber-500/20";
                  else if (s.status === "SUSPENDED")
                    statusBadge = "bg-rose-500/10 text-rose-400 border-rose-500/20";
                  else if (s.status === "REJECTED")
                    statusBadge = "bg-slate-700/30 text-slate-400 border-slate-700";

                  return (
                    <tr key={s.id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2.5">
                          {s.logo_url ? (
                            <img
                              src={s.logo_url}
                              alt={s.store_name}
                              className="w-8 h-8 rounded-full object-cover border border-slate-700"
                            />
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 font-bold text-xs">
                              {s.store_name.slice(0, 2).toUpperCase()}
                            </div>
                          )}
                          <div>
                            <p className="font-bold text-white flex items-center gap-1.5">
                              <span>{s.store_name}</span>
                              {s.status === "ACTIVE" && (
                                <Link
                                  href={`/store/${s.slug}`}
                                  target="_blank"
                                  className="text-slate-500 hover:text-white"
                                  title="View Public Storefront"
                                >
                                  <ExternalLink className="w-3 h-3" />
                                </Link>
                              )}
                            </p>
                            <span className="text-[11px] text-slate-400 font-mono">
                              /{s.slug}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td className="px-4 py-4 text-slate-300">
                        <p className="font-medium text-white">{s.seller_name || "Merchant"}</p>
                        <p className="text-[11px] text-slate-400">{s.seller_email || s.contact_email || "—"}</p>
                      </td>

                      <td className="px-4 py-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${statusBadge}`}
                        >
                          {s.status}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        {s.is_verified ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-300">
                            <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                            <span>Verified</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] text-slate-500">
                            <span>Standard</span>
                          </span>
                        )}
                      </td>

                      <td className="px-4 py-4 text-slate-400 text-[11px]">
                        {new Date(s.created_at).toLocaleDateString()}
                      </td>

                      <td className="px-5 py-4 text-right space-x-2">
                        {/* Toggle Badge */}
                        <button
                          onClick={() => {
                            setSelectedStore(s);
                            setModalMode("VERIFICATION");
                          }}
                          className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                            s.is_verified
                              ? "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
                              : "bg-amber-500/10 text-amber-300 border-amber-500/25 hover:bg-amber-500/20"
                          }`}
                        >
                          {s.is_verified ? "Revoke Badge" : "Grant Badge"}
                        </button>

                        {/* Status Moderation */}
                        <button
                          onClick={() => {
                            setSelectedStore(s);
                            setPendingStatus(s.status === "ACTIVE" ? "SUSPENDED" : "ACTIVE");
                            setModalMode("STATUS");
                          }}
                          className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                            s.status === "ACTIVE"
                              ? "bg-rose-500/10 text-rose-400 border-rose-500/20 hover:bg-rose-500/20"
                              : "bg-indigo-500/10 text-indigo-400 border-indigo-500/20 hover:bg-indigo-500/20"
                          }`}
                        >
                          {s.status === "ACTIVE" ? "Suspend" : "Activate"}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {total > 0 && (
          <div className="px-5 py-3.5 bg-slate-900/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {stores.length} of {total} {total === 1 ? "store" : "stores"}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || loading}
                className="px-2.5 py-1 rounded bg-slate-800 text-white disabled:opacity-40"
              >
                Previous
              </button>
              <span>
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || loading}
                className="px-2.5 py-1 rounded bg-slate-800 text-white disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {selectedStore && modalMode && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  modalMode === "STATUS"
                    ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    : "bg-amber-500/10 text-amber-300 border border-amber-500/25"
                }`}
              >
                {modalMode === "STATUS" ? (
                  <AlertTriangle className="w-5 h-5" />
                ) : (
                  <ShieldCheck className="w-5 h-5 text-amber-400" />
                )}
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">
                  {modalMode === "STATUS"
                    ? `Update Store Status: ${pendingStatus}`
                    : `${selectedStore.is_verified ? "Revoke" : "Grant"} Verified Badge`}
                </h3>
                <p className="text-xs text-slate-400">{selectedStore.store_name}</p>
              </div>
            </div>

            <div className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
              {modalMode === "STATUS" ? (
                <>
                  <p>
                    Are you sure you want to transition this store from{" "}
                    <span className="font-bold text-white">{selectedStore.status}</span> to{" "}
                    <span className="font-bold text-white">{pendingStatus}</span>?
                  </p>
                  {pendingStatus === "SUSPENDED" && (
                    <p className="text-rose-400 font-medium">
                      ⚠️ Suspending this store will immediately hide it from public search and return HTTP 404 on its public storefront.
                    </p>
                  )}
                </>
              ) : (
                <p>
                  {selectedStore.is_verified
                    ? "Revoking the badge removes the verified trust indicator from this store across the marketplace."
                    : "Granting the badge displays the verified trust indicator next to the store name and on product pages."}
                </p>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  setSelectedStore(null);
                  setModalMode(null);
                }}
                disabled={submitting}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={
                  modalMode === "STATUS"
                    ? handleUpdateStatus
                    : () => handleToggleVerification(selectedStore)
                }
                disabled={submitting}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all shadow-md ${
                  modalMode === "STATUS"
                    ? "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/30"
                    : "bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold shadow-amber-500/20"
                }`}
              >
                {submitting ? "Processing..." : "Confirm Action"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
