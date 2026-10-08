"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Store as StoreIcon, AlertCircle, ShoppingBag } from "lucide-react";
import {
  api,
  PublicStore,
  PublicStoreProductItem,
  PublicStoreProductsResponse,
} from "@/lib/api";
import StoreHeader from "@/components/store/StoreHeader";
import StoreInfo from "@/components/store/StoreInfo";
import StoreProductGrid from "@/components/store/StoreProductGrid";

export default function PublicStorePage() {
  const params = useParams();
  const slug = (params?.slug as string) || "";

  const [store, setStore] = useState<PublicStore | null>(null);
  const [products, setProducts] = useState<PublicStoreProductItem[]>([]);
  const [totalProducts, setTotalProducts] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [page, setPage] = useState<number>(1);
  const [sortBy, setSortBy] = useState<string>("newest");

  const [loading, setLoading] = useState(true);
  const [productsLoading, setProductsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch store metadata
  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);

    api
      .getPublicStore(slug)
      .then((data) => {
        setStore(data);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Store not found or currently unavailable.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [slug]);

  // 2. Fetch products whenever page or sorting changes
  useEffect(() => {
    if (!slug || !store) return;
    setProductsLoading(true);

    api
      .getPublicStoreProducts(slug, {
        sort_by: sortBy,
        page,
        page_size: 16,
      })
      .then((res: PublicStoreProductsResponse) => {
        setProducts(res.items);
        setTotalProducts(res.total);
        setTotalPages(res.total_pages);
      })
      .catch(() => {
        setProducts([]);
      })
      .finally(() => {
        setProductsLoading(false);
      });
  }, [slug, store, page, sortBy]);

  // Loading Skeleton State
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8 animate-pulse">
        <div className="h-6 w-32 bg-slate-900 rounded-lg" />
        <div className="h-72 bg-slate-900 rounded-3xl" />
        <div className="h-32 bg-slate-900 rounded-3xl" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((idx) => (
            <div key={idx} className="h-80 bg-slate-900 rounded-3xl" />
          ))}
        </div>
      </div>
    );
  }

  // 404 / Error State
  if (error || !store) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full p-8 rounded-3xl bg-slate-900 border border-slate-800 text-center space-y-6 shadow-2xl">
          <div className="w-16 h-16 rounded-2xl bg-red-500/10 text-red-400 flex items-center justify-center mx-auto border border-red-500/20">
            <StoreIcon className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-white tracking-tight">
              Boutique Currently Unavailable
            </h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              The storefront you requested is either suspended, undergoing curation, or does not exist.
            </p>
          </div>
          <div className="pt-2">
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all"
            >
              <ShoppingBag className="w-4 h-4" />
              <span>Explore Marketplace Catalog</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-1 transition-transform" />
            <span>Marketplace Catalog</span>
          </Link>

          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Exclusive Designer Storefront
          </span>
        </div>

        {/* Store Header */}
        <StoreHeader store={store} />

        {/* Store Info & Narrative */}
        <StoreInfo store={store} />

        {/* Product Catalog Grid */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
              <span>Boutique Collection</span>
            </h3>
          </div>

          {productsLoading ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 animate-pulse">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-80 bg-slate-900 rounded-3xl" />
              ))}
            </div>
          ) : (
            <StoreProductGrid
              products={products}
              total={totalProducts}
              page={page}
              totalPages={totalPages}
              sortBy={sortBy}
              onSortChange={(newSort) => {
                setSortBy(newSort);
                setPage(1);
              }}
              onPageChange={(newPage) => setPage(newPage)}
            />
          )}
        </section>
      </main>
    </div>
  );
}
