"use client";

import React, { Suspense, useEffect, useState, useCallback, useTransition } from "react";
import Link from "next/link";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import {
  ShoppingBag,
  Sparkles,
  Check,
  Tag,
  Layers,
  AlertCircle,
  ArrowRight,
  Search,
  SlidersHorizontal,
  X,
  ChevronLeft,
  ChevronRight,
  Eye,
  RotateCcw,
  CheckCircle2,
  DollarSign,
  Package,
} from "lucide-react";
import {
  api,
  Product,
  ProductVariant,
  SearchFiltersResponse,
  SearchQueryParams,
} from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

function CatalogSearchContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, quickCustomerLogin, refreshCartCount, cartCount } = useAuth();
  const [, startTransition] = useTransition();

  // Search & Filter State from URL
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [categoryId, setCategoryId] = useState(searchParams.get("category_id") || "");
  const [brandId, setBrandId] = useState(searchParams.get("brand_id") || "");
  const [minPrice, setMinPrice] = useState(searchParams.get("min_price") || "");
  const [maxPrice, setMaxPrice] = useState(searchParams.get("max_price") || "");
  const [size, setSize] = useState(searchParams.get("size") || "");
  const [color, setColor] = useState(searchParams.get("color") || "");
  const [inStock, setInStock] = useState<boolean>(searchParams.get("in_stock") === "true");
  const [sort, setSort] = useState<
    "relevance" | "price_asc" | "price_desc" | "newest" | "oldest" | "name_asc" | "name_desc"
  >(
    (searchParams.get("sort") as any) ||
      (searchParams.get("q") ? "relevance" : "newest")
  );
  const [page, setPage] = useState<number>(parseInt(searchParams.get("page") || "1", 10));

  // Available Facets from API
  const [filterOptions, setFilterOptions] = useState<SearchFiltersResponse | null>(null);

  // Products Results & UI state
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mobile filters drawer
  const [showFiltersMobile, setShowFiltersMobile] = useState(false);

  // Product Detail Modal state
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Selected variant per product: { [productId]: variantId }
  const [selectedVariants, setSelectedVariants] = useState<Record<string, string>>({});
  const [addingId, setAddingId] = useState<string | null>(null);
  const [addedSuccessId, setAddedSuccessId] = useState<string | null>(null);

  // Sync state to URL
  const syncUrl = useCallback(
    (params: {
      q?: string;
      category_id?: string;
      brand_id?: string;
      min_price?: string;
      max_price?: string;
      size?: string;
      color?: string;
      in_stock?: boolean;
      sort?: string;
      page?: number;
    }) => {
      const sp = new URLSearchParams();
      if (params.q?.trim()) sp.set("q", params.q.trim());
      if (params.category_id) sp.set("category_id", params.category_id);
      if (params.brand_id) sp.set("brand_id", params.brand_id);
      if (params.min_price?.trim()) sp.set("min_price", params.min_price.trim());
      if (params.max_price?.trim()) sp.set("max_price", params.max_price.trim());
      if (params.size?.trim()) sp.set("size", params.size.trim());
      if (params.color?.trim()) sp.set("color", params.color.trim());
      if (params.in_stock) sp.set("in_stock", "true");
      if (params.sort && params.sort !== "newest") sp.set("sort", params.sort);
      if (params.page && params.page > 1) sp.set("page", String(params.page));

      const qs = sp.toString();
      const newUrl = qs ? `${pathname}?${qs}` : pathname;
      startTransition(() => {
        router.replace(newUrl, { scroll: false });
      });
    },
    [pathname, router]
  );

  // Fetch filter options once
  useEffect(() => {
    api
      .getSearchFilters()
      .then((opts) => setFilterOptions(opts))
      .catch((err) => console.error("Could not load filters", err));
  }, []);

  // Fetch search products on criteria change
  const executeSearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const searchPayload: SearchQueryParams = {
        q: query || undefined,
        category_id: categoryId || undefined,
        brand_id: brandId || undefined,
        min_price: minPrice ? parseFloat(minPrice) : undefined,
        max_price: maxPrice ? parseFloat(maxPrice) : undefined,
        size: size || undefined,
        color: color || undefined,
        in_stock: inStock ? true : undefined,
        sort: sort || undefined,
        page,
        page_size: 12,
      };

      const res = await api.searchProducts(searchPayload);
      setProducts(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
      setHasNext(res.has_next);
      setHasPrevious(res.has_previous);

      // Pre-select first active variant for each product
      const initialVariants: Record<string, string> = {};
      res.items.forEach((p) => {
        const active = (p.variants || []).filter((v) => v.is_active);
        if (active.length > 0) {
          initialVariants[p.id] = active[0].id;
        }
      });
      setSelectedVariants((prev) => ({ ...initialVariants, ...prev }));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load products");
    } finally {
      setLoading(false);
    }
  }, [query, categoryId, brandId, minPrice, maxPrice, size, color, inStock, sort, page]);

  useEffect(() => {
    executeSearch();
  }, [executeSearch]);

  // Handle Search Input submit
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    syncUrl({
      q: query,
      category_id: categoryId,
      brand_id: brandId,
      min_price: minPrice,
      max_price: maxPrice,
      size,
      color,
      in_stock: inStock,
      sort,
      page: 1,
    });
  };

  // Clear all filters
  const handleClearAll = () => {
    setQuery("");
    setCategoryId("");
    setBrandId("");
    setMinPrice("");
    setMaxPrice("");
    setSize("");
    setColor("");
    setInStock(false);
    setSort("newest");
    setPage(1);
    startTransition(() => {
      router.replace(pathname, { scroll: false });
    });
  };

  // Handle Add To Cart
  const handleAddToCart = async (product: Product, variantIdOverride?: string) => {
    const variantId = variantIdOverride || selectedVariants[product.id];
    if (!variantId) return;

    if (!user) {
      await quickCustomerLogin();
    }

    setAddingId(variantId);
    try {
      await api.addToCart(variantId, 1);
      await refreshCartCount();
      setAddedSuccessId(variantId);
      setTimeout(() => setAddedSuccessId(null), 2000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to add to cart");
    } finally {
      setAddingId(null);
    }
  };

  // Check if any filter is active
  const hasActiveFilters = Boolean(
    query ||
      categoryId ||
      brandId ||
      minPrice ||
      maxPrice ||
      size ||
      color ||
      inStock ||
      (sort && sort !== "newest")
  );

  // Return query string to pass to product detail page
  const currentQueryString = searchParams.toString();
  const returnToParam = currentQueryString ? `?returnTo=${encodeURIComponent(`/?${currentQueryString}`)}` : "";

  return (
    <main className="min-h-screen pb-24 text-slate-100">
      {/* Hero Header */}
      <section className="relative overflow-hidden border-b border-slate-800/80 bg-gradient-to-b from-slate-900/80 via-slate-950 to-slate-950 py-12 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(99,102,241,0.15),rgba(255,255,255,0))]"></div>
        <div className="relative max-w-7xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-sm">
            <Sparkles className="w-3.5 h-3.5" />
            Phase 7: Marketplace Search, Filtering & Discovery
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white">
            Discover Curated Fashion
          </h1>
          <p className="max-w-2xl mx-auto text-slate-400 text-sm sm:text-base leading-relaxed">
            Search multi-vendor collections with deterministic relevance, multi-attribute facets, and real-time stock availability.
          </p>

          {/* Quick Search Bar in Hero */}
          <form
            onSubmit={handleSearchSubmit}
            className="max-w-3xl mx-auto pt-4 flex flex-col sm:flex-row gap-2"
          >
            <div className="relative flex-1">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by title, brand, category, SKU, size, or color..."
                className="w-full pl-12 pr-10 py-3.5 rounded-2xl bg-slate-900/90 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all shadow-inner"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => {
                    setQuery("");
                    setPage(1);
                    syncUrl({
                      q: "",
                      category_id: categoryId,
                      brand_id: brandId,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <button
              type="submit"
              className="px-6 py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-lg shadow-indigo-600/20 active:scale-95 flex items-center justify-center gap-2"
            >
              <Search className="w-4 h-4" />
              <span>Search</span>
            </button>
          </form>
        </div>
      </section>

      {/* Main Discovery Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Top Controls Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFiltersMobile(!showFiltersMobile)}
              className="lg:hidden inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-200 hover:bg-slate-800 transition-colors"
            >
              <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
              <span>Filters {hasActiveFilters && "•"}</span>
            </button>
            <p className="text-sm text-slate-400">
              Showing <span className="font-semibold text-white">{products.length}</span> of{" "}
              <span className="font-semibold text-white">{total}</span> items
            </p>
          </div>

          <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
            {/* Sort Dropdown */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400 hidden sm:inline">Sort:</span>
              <select
                value={sort}
                onChange={(e) => {
                  const newSort = e.target.value as any;
                  setSort(newSort);
                  setPage(1);
                  syncUrl({
                    q: query,
                    category_id: categoryId,
                    brand_id: brandId,
                    min_price: minPrice,
                    max_price: maxPrice,
                    size,
                    color,
                    in_stock: inStock,
                    sort: newSort,
                    page: 1,
                  });
                }}
                className="bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
              >
                <option value="relevance">Relevance</option>
                <option value="newest">Newest Arrivals</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="name_asc">Name: A to Z</option>
                <option value="name_desc">Name: Z to A</option>
                <option value="oldest">Oldest</option>
              </select>
            </div>

            {cartCount > 0 && (
              <Link
                href="/checkout"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-xs shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02]"
              >
                <ShoppingBag className="w-3.5 h-3.5" />
                <span>Cart ({cartCount})</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            )}
          </div>
        </div>

        {/* Active Filter Badges */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-2 py-4 border-b border-slate-800/60">
            <span className="text-xs text-slate-400 font-medium mr-1">Active filters:</span>

            {query && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                <span>Keyword: &quot;{query}&quot;</span>
                <button
                  onClick={() => {
                    setQuery("");
                    setPage(1);
                    syncUrl({
                      q: "",
                      category_id: categoryId,
                      brand_id: brandId,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {categoryId && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-slate-800 text-slate-200 border border-slate-700">
                <span>
                  Category:{" "}
                  {filterOptions?.categories.find((c) => c.id === categoryId)?.name || categoryId}
                </span>
                <button
                  onClick={() => {
                    setCategoryId("");
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: "",
                      brand_id: brandId,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {brandId && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-slate-800 text-slate-200 border border-slate-700">
                <span>
                  Brand: {filterOptions?.brands.find((b) => b.id === brandId)?.name || brandId}
                </span>
                <button
                  onClick={() => {
                    setBrandId("");
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: categoryId,
                      brand_id: "",
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {(minPrice || maxPrice) && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-slate-800 text-slate-200 border border-slate-700">
                <span>
                  Price: ${minPrice || "0"} – ${maxPrice || "Any"}
                </span>
                <button
                  onClick={() => {
                    setMinPrice("");
                    setMaxPrice("");
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: categoryId,
                      brand_id: brandId,
                      min_price: "",
                      max_price: "",
                      size,
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {size && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-slate-800 text-slate-200 border border-slate-700">
                <span>Size: {size}</span>
                <button
                  onClick={() => {
                    setSize("");
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: categoryId,
                      brand_id: brandId,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size: "",
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {color && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-slate-800 text-slate-200 border border-slate-700">
                <span>Color: {color}</span>
                <button
                  onClick={() => {
                    setColor("");
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: categoryId,
                      brand_id: brandId,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color: "",
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {inStock && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                <span>In Stock Only</span>
                <button
                  onClick={() => {
                    setInStock(false);
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: categoryId,
                      brand_id: brandId,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color,
                      in_stock: false,
                      sort,
                      page: 1,
                    });
                  }}
                  className="hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            <button
              onClick={handleClearAll}
              className="text-xs text-indigo-400 hover:text-indigo-300 ml-2 font-medium underline underline-offset-2"
            >
              Clear all
            </button>
          </div>
        )}

        {/* Discovery Layout: Sidebar Filters + Products Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 pt-6">
          {/* Filters Sidebar */}
          <aside
            className={`lg:block ${
              showFiltersMobile
                ? "fixed inset-0 z-50 bg-slate-950/95 p-6 overflow-y-auto block"
                : "hidden"
            } space-y-6 lg:border-r lg:border-slate-800/80 lg:pr-6`}
          >
            {showFiltersMobile && (
              <div className="flex items-center justify-between pb-4 border-b border-slate-800 lg:hidden">
                <h3 className="text-lg font-bold text-white">Filter Catalog</h3>
                <button
                  onClick={() => setShowFiltersMobile(false)}
                  className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}

            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Discovery Filters
              </span>
              {hasActiveFilters && (
                <button
                  onClick={handleClearAll}
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Reset</span>
                </button>
              )}
            </div>

            {/* In-Stock Toggle */}
            <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between">
              <div>
                <label
                  htmlFor="in-stock-toggle"
                  className="text-xs font-semibold text-white block cursor-pointer"
                >
                  In Stock Only
                </label>
                <span className="text-[10px] text-slate-400">Hide out-of-stock items</span>
              </div>
              <input
                id="in-stock-toggle"
                type="checkbox"
                checked={inStock}
                onChange={(e) => {
                  const checked = e.target.checked;
                  setInStock(checked);
                  setPage(1);
                  syncUrl({
                    q: query,
                    category_id: categoryId,
                    brand_id: brandId,
                    min_price: minPrice,
                    max_price: maxPrice,
                    size,
                    color,
                    in_stock: checked,
                    sort,
                    page: 1,
                  });
                }}
                className="w-4 h-4 rounded text-indigo-600 bg-slate-800 border-slate-700 focus:ring-indigo-500 cursor-pointer"
              />
            </div>

            {/* Category Filter */}
            {filterOptions?.categories && filterOptions.categories.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 block">Category</label>
                <select
                  value={categoryId}
                  onChange={(e) => {
                    const val = e.target.value;
                    setCategoryId(val);
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: val,
                      brand_id: brandId,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="w-full bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">All Categories</option>
                  {filterOptions.categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Brand Filter */}
            {filterOptions?.brands && filterOptions.brands.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 block">Brand</label>
                <select
                  value={brandId}
                  onChange={(e) => {
                    const val = e.target.value;
                    setBrandId(val);
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: categoryId,
                      brand_id: val,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="w-full bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">All Brands</option>
                  {filterOptions.brands.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Price Range Filter */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 block">Price Range ($)</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  onBlur={() => {
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: categoryId,
                      brand_id: brandId,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="w-1/2 bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-slate-500 text-xs">–</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  onBlur={() => {
                    setPage(1);
                    syncUrl({
                      q: query,
                      category_id: categoryId,
                      brand_id: brandId,
                      min_price: minPrice,
                      max_price: maxPrice,
                      size,
                      color,
                      in_stock: inStock,
                      sort,
                      page: 1,
                    });
                  }}
                  className="w-1/2 bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Size Filter Pills */}
            {filterOptions?.sizes && filterOptions.sizes.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 block">Size</label>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    onClick={() => {
                      setSize("");
                      setPage(1);
                      syncUrl({
                        q: query,
                        category_id: categoryId,
                        brand_id: brandId,
                        min_price: minPrice,
                        max_price: maxPrice,
                        size: "",
                        color,
                        in_stock: inStock,
                        sort,
                        page: 1,
                      });
                    }}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                      !size
                        ? "bg-indigo-600 border-indigo-500 text-white"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    All
                  </button>
                  {filterOptions.sizes.map((s) => {
                    const isSelected = size.toLowerCase() === s.toLowerCase();
                    return (
                      <button
                        key={s}
                        onClick={() => {
                          const newSize = isSelected ? "" : s;
                          setSize(newSize);
                          setPage(1);
                          syncUrl({
                            q: query,
                            category_id: categoryId,
                            brand_id: brandId,
                            min_price: minPrice,
                            max_price: maxPrice,
                            size: newSize,
                            color,
                            in_stock: inStock,
                            sort,
                            page: 1,
                          });
                        }}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                          isSelected
                            ? "bg-indigo-600 border-indigo-500 text-white shadow-sm"
                            : "bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700"
                        }`}
                      >
                        {s}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Color Filter Pills */}
            {filterOptions?.colors && filterOptions.colors.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 block">Color</label>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    onClick={() => {
                      setColor("");
                      setPage(1);
                      syncUrl({
                        q: query,
                        category_id: categoryId,
                        brand_id: brandId,
                        min_price: minPrice,
                        max_price: maxPrice,
                        size,
                        color: "",
                        in_stock: inStock,
                        sort,
                        page: 1,
                      });
                    }}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                      !color
                        ? "bg-indigo-600 border-indigo-500 text-white"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    All
                  </button>
                  {filterOptions.colors.map((c) => {
                    const isSelected = color.toLowerCase() === c.toLowerCase();
                    return (
                      <button
                        key={c}
                        onClick={() => {
                          const newColor = isSelected ? "" : c;
                          setColor(newColor);
                          setPage(1);
                          syncUrl({
                            q: query,
                            category_id: categoryId,
                            brand_id: brandId,
                            min_price: minPrice,
                            max_price: maxPrice,
                            size,
                            color: newColor,
                            in_stock: inStock,
                            sort,
                            page: 1,
                          });
                        }}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                          isSelected
                            ? "bg-indigo-600 border-indigo-500 text-white shadow-sm"
                            : "bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700"
                        }`}
                      >
                        {c}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {showFiltersMobile && (
              <button
                onClick={() => setShowFiltersMobile(false)}
                className="w-full mt-4 py-3 rounded-xl bg-indigo-600 text-white font-semibold text-xs"
              >
                Apply Filters
              </button>
            )}
          </aside>

          {/* Results Grid & Pagination Container */}
          <div className="lg:col-span-3 space-y-8">
            {/* Loading / Error States */}
            {loading && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="h-96 rounded-2xl bg-slate-900/50 border border-slate-800" />
                ))}
              </div>
            )}

            {error && (
              <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-300 text-sm flex items-start gap-4">
                <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-white">Could not fetch catalog products</p>
                  <p className="text-xs text-red-300/80 mt-1">{error}</p>
                  <button
                    onClick={executeSearch}
                    className="mt-3 px-3 py-1.5 rounded-lg bg-red-500/20 text-red-200 text-xs font-medium hover:bg-red-500/30"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}

            {/* Empty Catalog Notice */}
            {!loading && !error && products.length === 0 && (
              <div className="text-center py-20 px-4 rounded-3xl bg-slate-900/30 border border-slate-800 max-w-lg mx-auto space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto">
                  <Search className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white">No products match your criteria</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Try adjusting or clearing some of your filters or searching with different keywords.
                </p>
                {hasActiveFilters && (
                  <button
                    onClick={handleClearAll}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Clear all filters</span>
                  </button>
                )}
              </div>
            )}

            {/* Product Cards Grid */}
            {!loading && !error && products.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map((product) => {
                  const activeVariants = (product.variants || []).filter((v) => v.is_active);
                  const currentVariantId = selectedVariants[product.id] || (activeVariants[0]?.id ?? "");
                  const currentVariant = activeVariants.find((v) => v.id === currentVariantId) || activeVariants[0];
                  const isAdding = addingId === currentVariant?.id;
                  const isAdded = addedSuccessId === currentVariant?.id;
                  const inStockFlag = currentVariant?.is_in_stock ?? product.is_in_stock;

                  return (
                    <div
                      key={product.id}
                      className="group flex flex-col justify-between rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all p-5 hover:shadow-xl hover:shadow-indigo-950/20 backdrop-blur-sm relative"
                    >
                      <div>
                        {/* Visual / Thumbnail Banner */}
                        <div className="w-full h-48 rounded-xl bg-gradient-to-tr from-slate-800 via-indigo-950/40 to-slate-800 border border-slate-800/80 flex flex-col justify-between p-4 relative overflow-hidden group-hover:border-indigo-500/30 transition-colors">
                          {(() => {
                            const hero = (product.media || []).find((m) => m.is_primary) || product.media?.[0];
                            if (!hero?.url) return null;
                            return (
                              <img
                                src={hero.url}
                                alt={hero.alt_text || product.name}
                                className="absolute inset-0 w-full h-full object-cover z-0 group-hover:scale-105 transition-transform duration-300"
                                onError={(e) => {
                                  e.currentTarget.style.display = "none";
                                }}
                              />
                            );
                          })()}
                          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/30 to-transparent pointer-events-none z-5"></div>

                          <div className="flex items-center justify-between z-10">
                            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-black/60 text-slate-300 backdrop-blur border border-white/10">
                              {product.brand?.name || "Originals"}
                            </span>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                                inStockFlag
                                  ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                                  : "bg-amber-500/20 text-amber-300 border-amber-500/30"
                              }`}
                            >
                              {inStockFlag ? "In Stock" : "Out of Stock"}
                            </span>
                          </div>

                          <div className="z-10">
                            <p className="text-xl font-black text-white group-hover:text-indigo-200 transition-colors">
                              ${currentVariant ? currentVariant.price : product.base_price}
                            </p>
                            <span className="text-[11px] text-slate-400">USD Authorized</span>
                          </div>

                          {/* Quick View Button on Image */}
                          <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 p-4">
                            <button
                              onClick={() => setSelectedProduct(product)}
                              className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md flex items-center gap-1.5 transition-transform active:scale-95"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              <span>Quick View</span>
                            </button>
                            <Link
                              href={`/products/${product.id}${returnToParam}`}
                              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold shadow-md flex items-center gap-1.5 transition-transform active:scale-95"
                            >
                              <span>Details</span>
                              <ArrowRight className="w-3 h-3" />
                            </Link>
                          </div>
                        </div>

                        {/* Product Meta */}
                        <div className="mt-4 space-y-1.5">
                          <div className="flex items-center gap-2 text-xs text-indigo-400 font-medium">
                            <Tag className="w-3.5 h-3.5" />
                            <span>{product.category?.name || "Fashion"}</span>
                          </div>
                          <Link
                            href={`/products/${product.id}${returnToParam}`}
                            className="text-base font-bold text-white hover:text-indigo-300 transition-colors line-clamp-1 block"
                          >
                            {product.name}
                          </Link>
                          {product.description && (
                            <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                              {product.description}
                            </p>
                          )}
                        </div>

                        {/* Variant Selector */}
                        {activeVariants.length > 0 && (
                          <div className="mt-4 space-y-1.5">
                            <label className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                              Variants ({activeVariants.length})
                            </label>
                            <div className="flex flex-wrap gap-1.5">
                              {activeVariants.map((v) => {
                                const isSelected = v.id === currentVariantId;
                                return (
                                  <button
                                    key={v.id}
                                    onClick={() =>
                                      setSelectedVariants((prev) => ({
                                        ...prev,
                                        [product.id]: v.id,
                                      }))
                                    }
                                    className={`px-2 py-0.5 rounded-lg text-xs font-medium border transition-colors ${
                                      isSelected
                                        ? "bg-indigo-600 border-indigo-500 text-white shadow-sm"
                                        : "bg-slate-800/80 border-slate-700/60 text-slate-300 hover:border-slate-600"
                                    }`}
                                  >
                                    {v.size || v.color
                                      ? `${v.size || ""} ${v.color || ""}`.trim()
                                      : v.sku}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Stock & Action Footer */}
                      <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between gap-3">
                        <div className="text-xs">
                          <span className="text-slate-400 block text-[10px] uppercase">
                            Status
                          </span>
                          <span
                            className={`font-semibold text-xs ${
                              inStockFlag ? "text-emerald-400" : "text-amber-400"
                            }`}
                          >
                            {inStockFlag ? "In Stock" : "Out of Stock"}
                          </span>
                        </div>

                        <button
                          onClick={() => handleAddToCart(product)}
                          disabled={isAdding || !currentVariant}
                          className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all shadow-md ${
                            isAdded
                              ? "bg-emerald-600 text-white"
                              : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20 active:scale-95"
                          }`}
                        >
                          {isAdded ? (
                            <>
                              <Check className="w-4 h-4" />
                              <span>Added</span>
                            </>
                          ) : (
                            <>
                              <ShoppingBag className="w-4 h-4" />
                              <span>{isAdding ? "Adding..." : "Add to Cart"}</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Pagination Controls */}
            {!loading && totalPages > 1 && (
              <div className="pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4">
                <span className="text-xs text-slate-400">
                  Page <span className="font-semibold text-white">{page}</span> of{" "}
                  <span className="font-semibold text-white">{totalPages}</span>
                </span>

                <div className="flex items-center gap-2">
                  <button
                    disabled={!hasPrevious}
                    onClick={() => {
                      const newPage = page - 1;
                      setPage(newPage);
                      syncUrl({
                        q: query,
                        category_id: categoryId,
                        brand_id: brandId,
                        min_price: minPrice,
                        max_price: maxPrice,
                        size,
                        color,
                        in_stock: inStock,
                        sort,
                        page: newPage,
                      });
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-medium border ${
                      hasPrevious
                        ? "bg-slate-900 border-slate-800 text-white hover:bg-slate-800"
                        : "bg-slate-900/40 border-slate-800/40 text-slate-600 cursor-not-allowed"
                    }`}
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span>Previous</span>
                  </button>

                  {/* Page number buttons */}
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
                    .map((p, idx, arr) => (
                      <React.Fragment key={p}>
                        {idx > 0 && arr[idx - 1] !== p - 1 && (
                          <span className="text-slate-600 px-1 text-xs">...</span>
                        )}
                        <button
                          onClick={() => {
                            setPage(p);
                            syncUrl({
                              q: query,
                              category_id: categoryId,
                              brand_id: brandId,
                              min_price: minPrice,
                              max_price: maxPrice,
                              size,
                              color,
                              in_stock: inStock,
                              sort,
                              page: p,
                            });
                            window.scrollTo({ top: 0, behavior: "smooth" });
                          }}
                          className={`w-8 h-8 rounded-xl text-xs font-semibold transition-colors ${
                            p === page
                              ? "bg-indigo-600 text-white"
                              : "bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800"
                          }`}
                        >
                          {p}
                        </button>
                      </React.Fragment>
                    ))}

                  <button
                    disabled={!hasNext}
                    onClick={() => {
                      const newPage = page + 1;
                      setPage(newPage);
                      syncUrl({
                        q: query,
                        category_id: categoryId,
                        brand_id: brandId,
                        min_price: minPrice,
                        max_price: maxPrice,
                        size,
                        color,
                        in_stock: inStock,
                        sort,
                        page: newPage,
                      });
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-medium border ${
                      hasNext
                        ? "bg-slate-900 border-slate-800 text-white hover:bg-slate-800"
                        : "bg-slate-900/40 border-slate-800/40 text-slate-600 cursor-not-allowed"
                    }`}
                  >
                    <span>Next</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Product Detail Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setSelectedProduct(null)}
              className="absolute top-5 right-5 p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {selectedProduct.brand?.name || "Originals"}
                </span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs text-slate-400">{selectedProduct.category?.name || "Fashion"}</span>
              </div>
              <h2 className="text-2xl font-black text-white">{selectedProduct.name}</h2>
              <p className="text-2xl font-black text-indigo-300">
                ${selectedProduct.base_price} <span className="text-xs font-normal text-slate-400">USD</span>
              </p>
            </div>

            {selectedProduct.description && (
              <div className="space-y-1">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Description</h4>
                <p className="text-sm text-slate-300 leading-relaxed">{selectedProduct.description}</p>
              </div>
            )}

            {/* Active Variants in Modal */}
            {selectedProduct.variants && selectedProduct.variants.filter((v) => v.is_active).length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Select Variant SKU
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {selectedProduct.variants
                    .filter((v) => v.is_active)
                    .map((v) => {
                      const isSel = selectedVariants[selectedProduct.id] === v.id;
                      return (
                        <button
                          key={v.id}
                          onClick={() =>
                            setSelectedVariants((prev) => ({
                              ...prev,
                              [selectedProduct.id]: v.id,
                            }))
                          }
                          className={`p-2.5 rounded-xl border text-left text-xs transition-colors ${
                            isSel
                              ? "bg-indigo-600/20 border-indigo-500 text-white"
                              : "bg-slate-800/60 border-slate-700/60 text-slate-300 hover:border-slate-600"
                          }`}
                        >
                          <p className="font-semibold">{v.sku}</p>
                          <p className="text-[11px] text-slate-400">
                            {v.size || v.color ? `${v.size || ""} • ${v.color || ""}` : `$${v.price}`}
                          </p>
                          <span
                            className={`inline-block mt-1 text-[10px] font-medium ${
                              v.is_in_stock ? "text-emerald-400" : "text-amber-400"
                            }`}
                          >
                            {v.is_in_stock ? "In Stock" : "Out of Stock"}
                          </span>
                        </button>
                      );
                    })}
                </div>
              </div>
            )}

            {/* Modal Actions */}
            <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
              <Link
                href={`/products/${selectedProduct.id}${returnToParam}`}
                className="text-xs text-indigo-400 hover:text-indigo-300 underline underline-offset-2 flex items-center gap-1"
              >
                <span>Open full product page</span>
                <ArrowRight className="w-3 h-3" />
              </Link>

              <button
                onClick={() => {
                  handleAddToCart(selectedProduct);
                  setSelectedProduct(null);
                }}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2"
              >
                <ShoppingBag className="w-4 h-4" />
                <span>Add to Cart</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

export default function CatalogPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center text-slate-400 text-sm">
          Loading discovery catalog...
        </div>
      }
    >
      <CatalogSearchContent />
    </Suspense>
  );
}
