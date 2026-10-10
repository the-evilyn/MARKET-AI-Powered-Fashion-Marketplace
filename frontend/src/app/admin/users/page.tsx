"use client";

import React, { useEffect, useState } from "react";
import {
  Users,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Filter,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  UserX,
} from "lucide-react";
import { api, AdminUserSummary } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function AdminUsersPage() {
  const { user: currentAdmin } = useAuth();
  const [users, setUsers] = useState<AdminUserSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [roleFilter, setRoleFilter] = useState<string>("ALL");
  const [activeFilter, setActiveFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Status Change Modal state
  const [selectedUser, setSelectedUser] = useState<AdminUserSummary | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminUsers({
        role: roleFilter === "ALL" ? undefined : roleFilter,
        is_active:
          activeFilter === "ALL"
            ? undefined
            : activeFilter === "ACTIVE",
        q: searchQuery.trim() || undefined,
        page,
        page_size: 15,
      });
      setUsers(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, roleFilter, activeFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleToggleUserStatus = async () => {
    if (!selectedUser) return;
    setSubmitting(true);
    setActionSuccess(null);
    setError(null);
    try {
      const targetActive = !selectedUser.is_active;
      await api.updateAdminUserStatus(selectedUser.id, targetActive);
      setActionSuccess(
        `User '${selectedUser.email}' account ${targetActive ? "activated" : "deactivated"} successfully.`
      );
      setSelectedUser(null);
      await fetchUsers();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update user status");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Users className="w-6 h-6 text-amber-400" />
            <span>User Management & Governance</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Supervise registered accounts, enforce compliance, and manage activation states.
          </p>
        </div>
        <button
          onClick={fetchUsers}
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

      {/* Search & Filters */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by email, first name, or last name..."
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
            <span>Role:</span>
            <select
              value={roleFilter}
              onChange={(e) => {
                setRoleFilter(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-stone-200 focus:outline-none focus:border-amber-500/50"
            >
              <option value="ALL">All Roles</option>
              <option value="CUSTOMER">CUSTOMER</option>
              <option value="SELLER">SELLER</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Status:</span>
            <select
              value={activeFilter}
              onChange={(e) => {
                setActiveFilter(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-stone-200 focus:outline-none focus:border-amber-500/50"
            >
              <option value="ALL">All Accounts</option>
              <option value="ACTIVE">Active Only</option>
              <option value="INACTIVE">Inactive Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-2xl bg-slate-900/40 border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">User</th>
                <th className="px-4 py-3.5">Email</th>
                <th className="px-4 py-3.5">Role</th>
                <th className="px-4 py-3.5">Account State</th>
                <th className="px-4 py-3.5">Registered</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading && users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto text-amber-400 mb-2" />
                    <span>Loading users...</span>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                    No users match your current filters.
                  </td>
                </tr>
              ) : (
                users.map((u) => {
                  const isSelf = currentAdmin && currentAdmin.id === u.id;
                  let roleBadge = "bg-slate-800 text-slate-400 border-slate-700";
                  if (u.role === "ADMIN")
                    roleBadge = "bg-amber-500/15 text-amber-300 border-amber-500/30";
                  else if (u.role === "SELLER")
                    roleBadge = "bg-violet-500/10 text-violet-400 border-violet-500/20";
                  else if (u.role === "CUSTOMER")
                    roleBadge = "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";

                  return (
                    <tr key={u.id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-white font-bold text-xs">
                            {u.first_name ? u.first_name[0].toUpperCase() : "U"}
                          </div>
                          <div>
                            <p className="font-bold text-white flex items-center gap-1.5">
                              <span>
                                {u.first_name} {u.last_name}
                              </span>
                              {isSelf && (
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-300 border border-amber-500/25 font-semibold">
                                  You
                                </span>
                              )}
                            </p>
                            <span className="text-[10px] text-slate-400 font-mono">
                              ID: {u.id.slice(0, 8)}...
                            </span>
                          </div>
                        </div>
                      </td>

                      <td className="px-4 py-4 text-slate-300 font-mono text-[11px]">
                        {u.email}
                      </td>

                      <td className="px-4 py-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${roleBadge}`}
                        >
                          {u.role}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Active</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Inactive</span>
                          </span>
                        )}
                      </td>

                      <td className="px-4 py-4 text-slate-400 text-[11px]">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>

                      <td className="px-5 py-4 text-right">
                        {isSelf ? (
                          <span className="text-[11px] text-amber-300/80 italic pr-2">
                            Self (Protected)
                          </span>
                        ) : (
                          <button
                            onClick={() => setSelectedUser(u)}
                            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all border ${
                              u.is_active
                                ? "bg-rose-500/10 text-rose-400 border-rose-500/20 hover:bg-rose-500/20"
                                : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20"
                            }`}
                          >
                            {u.is_active ? "Deactivate" : "Activate"}
                          </button>
                        )}
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
              Showing {users.length} of {total} {total === 1 ? "user" : "users"}
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
      {selectedUser && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  selectedUser.is_active
                    ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    : "bg-amber-500/10 text-amber-300 border border-amber-500/25"
                }`}
              >
                {selectedUser.is_active ? (
                  <UserX className="w-5 h-5" />
                ) : (
                  <UserCheck className="w-5 h-5 text-amber-400" />
                )}
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">
                  {selectedUser.is_active ? "Deactivate Account" : "Activate Account"}
                </h3>
                <p className="text-xs text-slate-400">{selectedUser.email}</p>
              </div>
            </div>

            <div className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
              <p>
                Are you sure you want to{" "}
                <span className="font-bold text-white">
                  {selectedUser.is_active ? "disable" : "enable"}
                </span>{" "}
                access for {selectedUser.first_name} {selectedUser.last_name}?
              </p>
              {selectedUser.is_active ? (
                <p className="text-rose-400 font-medium">
                  ⚠️ Deactivating this account will immediately lock out the user and prevent authentication across the entire marketplace.
                </p>
              ) : (
                <p className="text-amber-300">
                  Activating will restore standard access permissions based on role ({selectedUser.role}).
                </p>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setSelectedUser(null)}
                disabled={submitting}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleToggleUserStatus}
                disabled={submitting}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all shadow-md ${
                  selectedUser.is_active
                    ? "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/30"
                    : "bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold shadow-amber-500/20"
                }`}
              >
                {submitting ? "Processing..." : selectedUser.is_active ? "Confirm Deactivation" : "Confirm Activation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
