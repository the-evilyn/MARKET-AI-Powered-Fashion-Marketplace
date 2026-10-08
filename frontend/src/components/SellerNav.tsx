"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  Boxes,
  ShoppingBag,
  ArrowLeft,
  Sparkles,
  Store,
  Settings,
  ExternalLink,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";

export default function SellerNav() {
  const pathname = usePathname();
  const { user } = useAuth();
  const [storeSlug, setStoreSlug] = useState<string | null>(null);

  useEffect(() => {
    if (user?.role === "SELLER") {
      api
        .getSellerStoreProfile()
        .then((profile) => {
          if (profile?.slug) setStoreSlug(profile.slug);
        })
        .catch(() => {
          // Fallback gracefully
        });
    }
  }, [user]);

  const navItems = [
    {
      name: "Dashboard",
      href: "/seller/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Products",
      href: "/seller/products",
      icon: Package,
    },
    {
      name: "Inventory",
      href: "/seller/inventory",
      icon: Boxes,
    },
    {
      name: "Orders",
      href: "/seller/orders",
      icon: ShoppingBag,
    },
    {
      name: "Store Settings",
      href: "/seller/settings",
      icon: Settings,
    },
  ];

  return (
    <div className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-16 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between py-3 gap-3">
          {/* Seller Store Badge & Breadcrumb */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/20">
              <Store className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-white tracking-tight">
                  Seller Merchant Hub
                </h2>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {user?.role === "ADMIN" ? "Admin Mode" : "Active Merchant"}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                {user?.email || "Authenticated Merchant"}
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto pb-1 sm:pb-0">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                      : "text-slate-400 hover:text-white hover:bg-slate-800/80"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}

            {storeSlug && (
              <Link
                href={`/store/${storeSlug}`}
                target="_blank"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/30 transition-all ml-1"
                title="View My Public Storefront"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>View My Public Store</span>
              </Link>
            )}

            <Link
              href="/"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 ml-auto sm:ml-2 border border-slate-800"
              title="Return to Public Customer Marketplace"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Customer Store</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
