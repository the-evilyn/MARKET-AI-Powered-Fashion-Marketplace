"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Store,
  Users,
  ShoppingBag,
  ArrowLeft,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function AdminNav() {
  const pathname = usePathname();
  const { user } = useAuth();

  const navItems = [
    {
      name: "Dashboard",
      href: "/admin/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Stores Moderation",
      href: "/admin/stores",
      icon: Store,
    },
    {
      name: "User Management",
      href: "/admin/users",
      icon: Users,
    },
    {
      name: "Global Orders",
      href: "/admin/orders",
      icon: ShoppingBag,
    },
  ];

  return (
    <aside className="w-full bg-slate-900/90 backdrop-blur-md border-b border-slate-800 text-slate-100 sticky top-16 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between py-3 gap-3">
          {/* Brand/Role Indicator & Return Link */}
          <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-start">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Marketplace</span>
            </Link>
            <div className="h-4 w-px bg-slate-800 hidden sm:block" />
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/25">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                <span>Admin Platform</span>
              </span>
              {user && (
                <span className="text-xs text-stone-400 hidden md:inline">
                  {user.email}
                </span>
              )}
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/admin/dashboard" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                    isActive
                      ? "bg-amber-500/15 text-amber-200 border border-amber-500/30 shadow-sm shadow-amber-500/10"
                      : "text-stone-400 hover:text-stone-100 hover:bg-slate-800/60"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </aside>
  );
}
