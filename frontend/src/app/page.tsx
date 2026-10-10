"use client";

import React, { Suspense, useEffect, useState, useCallback, useTransition } from "react";
import Link from "next/link";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import {
  ShoppingBag,
  Sparkles,
  Check,
  Tag,
  ArrowRight,
  Search,
  SlidersHorizontal,
  X,
  ChevronLeft,
  ChevronRight,
  Eye,
  RotateCcw,
  Package,
  ShieldCheck,
  Truck,
  Heart,
  Compass,
  Store,
  Layers,
} from "lucide-react";
import {
  api,
  Product,
  SearchFiltersResponse,
  SearchQueryParams,
} from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useFavorites } from "@/context/FavoritesContext";

function CatalogSearchContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, quickCustomerLogin, refreshCartCount, cartCount, openCart } = useAuth();
  const { isFavorite, toggleFavorite } = useFavorites();
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
  const [showOnlyFavorites, setShowOnlyFavorites] = useState<boolean>(
    searchParams.get("favorites") === "true"
  );
  const [sort, setSort] = useState<
    "relevance" | "price_asc" | "price_desc" | "newest" | "oldest" | "name_asc" | "name_desc"
  >(
    (searchParams.get("sort") as any) ||
      (searchParams.get("q") ? "relevance" : "newest")
  );
  const [page, setPage] = useState<number>(parseInt(searchParams.get("page") || "1", 10));

  // Available Facets from API
  const [filterOptions, setFilterOptions] = useState<SearchFiltersResponse | null>(null);

  // New Arrivals Showcase State
  const [newArrivals, setNewArrivals] = useState<Product[]>([]);
  const [loadingNewArrivals, setLoadingNewArrivals] = useState(true);

  // Main Discovery Catalog Results
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
      favorites?: boolean;
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
      if (params.favorites) sp.set("favorites", "true");
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

  // Fetch filter options and new arrivals on mount
  useEffect(() => {
    api
      .getSearchFilters()
      .then((opts) => setFilterOptions(opts))
      .catch((err) => console.error("Could not load filters", err));

    api
      .searchProducts({ sort: "newest", page_size: 4 })
      .then((res) => setNewArrivals(res.items))
      .catch((err) => console.error("Could not load new arrivals", err))
      .finally(() => setLoadingNewArrivals(false));
  }, []);

  // Synchronize state when URL searchParams changes externally (e.g. Navbar links)
  useEffect(() => {
    const isFav = searchParams.get("favorites") === "true";
    setShowOnlyFavorites(isFav);

    const s = searchParams.get("sort");
    if (s && s !== sort) {
      setSort(s as any);
    }

    const q = searchParams.get("q") || "";
    if (q !== query) {
      setQuery(q);
    }

    const cat = searchParams.get("category_id") || "";
    if (cat !== categoryId) {
      setCategoryId(cat);
    }
  }, [searchParams]);

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
      let items = res.items;

      if (showOnlyFavorites) {
        items = items.filter((p) => isFavorite(p.id));
      }

      setProducts(items);
      setTotal(showOnlyFavorites ? items.length : res.total);
      setTotalPages(showOnlyFavorites ? 1 : res.total_pages);
      setHasNext(showOnlyFavorites ? false : res.has_next);
      setHasPrevious(showOnlyFavorites ? false : res.has_previous);

      // Pre-select first active variant for each product
      const initialVariants: Record<string, string> = {};
      items.forEach((p) => {
        const active = (p.variants || []).filter((v) => v.is_active);
        if (active.length > 0) {
          initialVariants[p.id] = active[0].id;
        }
      });
      setSelectedVariants((prev) => ({ ...initialVariants, ...prev }));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur de chargement des créations");
    } finally {
      setLoading(false);
    }
  }, [query, categoryId, brandId, minPrice, maxPrice, size, color, inStock, sort, page, showOnlyFavorites, isFavorite]);

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
      favorites: showOnlyFavorites,
      sort,
      page: 1,
    });
    // Smooth scroll down to catalog section if searching from hero
    const catalogAnchor = document.getElementById("catalog-discovery");
    if (catalogAnchor) {
      catalogAnchor.scrollIntoView({ behavior: "smooth" });
    }
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
    setShowOnlyFavorites(false);
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
      openCart();
      setTimeout(() => setAddedSuccessId(null), 2500);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Impossible d'ajouter au panier");
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
      showOnlyFavorites ||
      (sort && sort !== "newest")
  );

  const currentQueryString = searchParams.toString();
  const returnToParam = currentQueryString ? `?returnTo=${encodeURIComponent(`/?${currentQueryString}`)}` : "";

  return (
    <main className="min-h-screen text-stone-100 bg-[#070a12] pb-24 selection:bg-amber-400 selection:text-stone-950">
      {/* 1. HERO BANNER — HAUTE COUTURE EDITORIAL */}
      <section className="relative overflow-hidden border-b border-stone-850 bg-gradient-to-b from-[#0b0f1d] via-[#080c16] to-[#070a12] pt-20 pb-28 px-4 sm:px-6 lg:px-8">
        {/* Subtle ambient lighting */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[450px] bg-[radial-gradient(ellipse_at_top,rgba(217,119,6,0.12),transparent_70%)] pointer-events-none" />
        <div className="absolute top-1/4 right-10 w-96 h-96 bg-indigo-950/20 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto flex flex-col items-center text-center space-y-6">
          {/* Label Badge */}
          <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-full bg-amber-400/10 border border-amber-400/30 text-amber-300 text-[10px] sm:text-xs font-serif tracking-wider sm:tracking-widest uppercase shadow-sm max-w-full">
            <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="truncate">Édition Printemps-Été 2026 • AI Fashion</span>
          </div>

          {/* Main Title */}
          <h1 className="text-2xl sm:text-5xl lg:text-7xl font-serif font-light tracking-tight text-stone-100 max-w-4xl leading-tight sm:leading-[1.1] break-words">
            L&apos;Élégance Contemporaine, <br />
            <span className="italic font-normal text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-amber-300 to-amber-100">
              Révélée par la Technologie
            </span>
          </h1>

          {/* Subtitle */}
          <p className="max-w-2xl text-stone-400 text-xs sm:text-base leading-relaxed font-sans px-2">
            Explorez les créations d&apos;ateliers d&apos;exception et de maisons émergentes.
            Découverte assistée par intelligence artificielle, traçabilité certifiée et livraison soignée.
          </p>

          {/* Real stats row */}
          <div className="pt-2 grid grid-cols-2 sm:flex sm:flex-wrap items-center justify-center gap-4 sm:gap-8 text-xs font-mono text-stone-400 border-y border-stone-800/60 py-4 max-w-3xl w-full">
            <div className="text-center">
              <span className="text-amber-300 font-bold font-serif text-base">{total || 24}</span>
              <span className="block text-[10px] text-stone-500 uppercase tracking-wider">Pièces Uniques</span>
            </div>
            <div className="hidden sm:block text-stone-700">•</div>
            <div className="text-center">
              <span className="text-amber-300 font-bold font-serif text-base">
                {filterOptions?.categories.length || 22}
              </span>
              <span className="block text-[10px] text-stone-500 uppercase tracking-wider">Catégories</span>
            </div>
            <div className="hidden sm:block text-stone-700">•</div>
            <div className="text-center">
              <span className="text-amber-300 font-bold font-serif text-base">
                {filterOptions?.brands.length || 22}
              </span>
              <span className="block text-[10px] text-stone-500 uppercase tracking-wider">Maisons</span>
            </div>
            <div className="hidden sm:block text-stone-700">•</div>
            <div className="text-center">
              <span className="text-amber-300 font-bold font-serif text-base">100%</span>
              <span className="block text-[10px] text-stone-500 uppercase tracking-wider">Authenticité</span>
            </div>
          </div>

          {/* Quick Search Input */}
          <form
            onSubmit={handleSearchSubmit}
            className="w-full max-w-2xl pt-4 flex flex-col sm:flex-row gap-2.5"
          >
            <div className="relative flex-1">
              <Search className="w-5 h-5 text-stone-500 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Rechercher une pièce, maison, matière, référence SKU..."
                className="w-full pl-12 pr-10 py-4 rounded-2xl bg-[#0d1222]/90 border border-stone-750 text-stone-100 placeholder-stone-500 text-xs sm:text-sm focus:outline-none focus:border-amber-400/80 focus:ring-1 focus:ring-amber-400/80 transition-all shadow-inner"
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
                      favorites: showOnlyFavorites,
                      sort,
                      page: 1,
                    });
                  }}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-stone-400 hover:text-white p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <button
              type="submit"
              className="px-8 py-4 rounded-2xl bg-amber-400 hover:bg-amber-300 text-stone-950 font-serif font-bold text-xs tracking-wider uppercase transition-all shadow-lg shadow-amber-400/10 flex items-center justify-center gap-2 active:scale-95"
            >
              <Search className="w-4 h-4" />
              <span>Explorer</span>
            </button>
          </form>
        </div>
      </section>

      {/* 2. FOUR PILLARS OF EXCELLENCE */}
      <section className="border-b border-stone-850 bg-[#080c16] py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="p-6 rounded-2xl bg-[#0b101e]/80 border border-stone-800/80 flex items-start gap-4 hover:border-amber-400/30 transition-all">
            <div className="w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-400 shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-serif font-medium text-stone-100 text-sm">Authenticité & Traçabilité</h4>
              <p className="text-xs text-stone-400 mt-1 leading-relaxed">
                Chaque pièce est certifiée et contrôlée auprès du créateur agréé avant expédition.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-[#0b101e]/80 border border-stone-800/80 flex items-start gap-4 hover:border-amber-400/30 transition-all">
            <div className="w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-400 shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-serif font-medium text-stone-100 text-sm">Curation Émergente</h4>
              <p className="text-xs text-stone-400 mt-1 leading-relaxed">
                Une sélection rigoureuse d&apos;ateliers indépendants et d&apos;éditions limitées exclusives.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-[#0b101e]/80 border border-stone-800/80 flex items-start gap-4 hover:border-amber-400/30 transition-all">
            <div className="w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-400 shrink-0">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-serif font-medium text-stone-100 text-sm">Expédition Haute Protection</h4>
              <p className="text-xs text-stone-400 mt-1 leading-relaxed">
                Emballage soigné haute couture et prise en charge logistique dédiée en temps réel.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-[#0b101e]/80 border border-stone-800/80 flex items-start gap-4 hover:border-amber-400/30 transition-all">
            <div className="w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-400 shrink-0">
              <Store className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-serif font-medium text-stone-100 text-sm">Écosystème Créateurs</h4>
              <p className="text-xs text-stone-400 mt-1 leading-relaxed">
                Boutiques dédiées, gestion transparente des stocks et accompagnement sur-mesure.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. CATEGORIES SPOTLIGHT */}
      {filterOptions?.categories && filterOptions.categories.length > 0 && (
        <section className="py-16 px-4 sm:px-6 lg:px-8 border-b border-stone-850 bg-[#060912]">
          <div className="max-w-7xl mx-auto space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div>
                <span className="text-[11px] font-mono uppercase tracking-widest text-amber-400">
                  Univers & Garde-Robe
                </span>
                <h2 className="text-2xl sm:text-3xl font-serif font-light text-stone-100 mt-1">
                  Parcourir par Catégorie
                </h2>
              </div>
              <p className="text-xs text-stone-400 max-w-sm">
                Explorez nos collections structurées selon les standards de la Haute Couture.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {filterOptions.categories.slice(0, 12).map((cat) => {
                const isActive = categoryId === cat.id;
                return (
                  <button
                    key={cat.id}
                    onClick={() => {
                      const newCat = isActive ? "" : cat.id;
                      setCategoryId(newCat);
                      setPage(1);
                      syncUrl({
                        q: query,
                        category_id: newCat,
                        brand_id: brandId,
                        min_price: minPrice,
                        max_price: maxPrice,
                        size,
                        color,
                        in_stock: inStock,
                        favorites: showOnlyFavorites,
                        sort,
                        page: 1,
                      });
                      const el = document.getElementById("catalog-discovery");
                      if (el) el.scrollIntoView({ behavior: "smooth" });
                    }}
                    className={`p-4 rounded-xl text-left border transition-all flex flex-col justify-between h-28 group ${
                      isActive
                        ? "bg-amber-400/15 border-amber-400 text-amber-200 shadow-md shadow-amber-400/5"
                        : "bg-[#0b101c] border-stone-800/80 text-stone-300 hover:border-amber-400/40 hover:bg-[#0e1424]"
                    }`}
                  >
                    <div className="w-7 h-7 rounded-lg bg-stone-900 border border-stone-800 flex items-center justify-center text-stone-400 group-hover:text-amber-300 transition-colors">
                      <Tag className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <span className="text-xs font-semibold block truncate group-hover:text-stone-100">
                        {cat.name}
                      </span>
                      <span className="text-[10px] text-stone-500 font-mono">Découvrir →</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* 4. NEW ARRIVALS / DERNIÈRES ARRIVÉES CURATION */}
      {newArrivals.length > 0 && (
        <section className="py-20 px-4 sm:px-6 lg:px-8 border-b border-stone-850 bg-gradient-to-b from-[#080c16] to-[#070a12]">
          <div className="max-w-7xl mx-auto space-y-10">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-400/10 text-amber-300 border border-amber-400/20 text-[10px] uppercase font-mono tracking-widest">
                  <Sparkles className="w-3 h-3" />
                  <span>Derniers Arrivages</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-serif font-light text-stone-100 mt-2">
                  Nouveautés de nos Créateurs
                </h2>
              </div>
              <button
                onClick={() => {
                  setSort("newest");
                  const el = document.getElementById("catalog-discovery");
                  if (el) el.scrollIntoView({ behavior: "smooth" });
                }}
                className="inline-flex items-center gap-1.5 text-xs text-amber-300 hover:text-amber-200 font-medium transition-colors"
              >
                <span>Voir toutes les nouveautés</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {newArrivals.map((product) => {
                const heroMedia = (product.media || []).find((m) => m.is_primary) || product.media?.[0];
                const activeVariants = (product.variants || []).filter((v) => v.is_active);
                const currentVariant = activeVariants[0];
                const hasDiscount =
                  currentVariant?.compare_at_price &&
                  parseFloat(currentVariant.compare_at_price) > parseFloat(currentVariant.price);
                const isFav = isFavorite(product.id);

                return (
                  <div
                    key={product.id}
                    className="group rounded-2xl bg-[#0c111e] border border-stone-800/80 hover:border-amber-400/40 transition-all p-4 flex flex-col justify-between hover:shadow-xl hover:shadow-amber-950/10 relative"
                  >
                    <div>
                      {/* Image Preview / Monogram Box */}
                      <div className="w-full h-56 rounded-xl bg-gradient-to-tr from-stone-900 via-[#121929] to-stone-900 border border-stone-800 flex items-center justify-center relative overflow-hidden">
                        {heroMedia?.url ? (
                          <img
                            src={heroMedia.url}
                            alt={heroMedia.alt_text || product.name}
                            className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                            onError={(e) => {
                              e.currentTarget.style.display = "none";
                            }}
                          />
                        ) : (
                          <div className="flex flex-col items-center gap-2 text-stone-600">
                            <span className="font-serif text-3xl font-light text-stone-700">M</span>
                            <span className="text-[10px] uppercase font-mono tracking-widest text-stone-600">
                              Maison Pièce
                            </span>
                          </div>
                        )}

                        <div className="absolute inset-0 bg-gradient-to-t from-[#070a12]/90 via-transparent to-transparent pointer-events-none" />

                        {/* Badges on image */}
                        <div className="absolute top-3 left-3 right-3 flex items-center justify-between z-10">
                          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-md bg-stone-950/80 text-stone-300 border border-stone-700/60 backdrop-blur-sm">
                            {product.brand?.name || "Original"}
                          </span>
                          <button
                            onClick={() => toggleFavorite(product.id)}
                            className={`p-1.5 rounded-lg backdrop-blur-sm transition-colors ${
                              isFav
                                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                : "bg-stone-950/60 text-stone-400 hover:text-rose-300 border border-stone-800"
                            }`}
                            title={isFav ? "Retirer des favoris" : "Ajouter aux favoris"}
                          >
                            <Heart className={`w-3.5 h-3.5 ${isFav ? "fill-rose-400 text-rose-400" : ""}`} />
                          </button>
                        </div>

                        {/* Discount Badge if genuine discount exists */}
                        {hasDiscount && (
                          <div className="absolute bottom-3 left-3 z-10">
                            <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-amber-400 text-stone-950">
                              Offre Exclusive
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Info */}
                      <div className="mt-4 space-y-1.5">
                        <span className="text-[10px] uppercase font-mono tracking-wider text-amber-400/90 block">
                          {product.category?.name || "Haute Couture"}
                        </span>
                        <Link
                          href={`/products/${product.id}${returnToParam}`}
                          className="text-sm font-serif font-medium text-stone-100 hover:text-amber-200 transition-colors line-clamp-1 block"
                        >
                          {product.name}
                        </Link>
                      </div>
                    </div>

                    {/* Price and Action */}
                    <div className="mt-5 pt-3 border-t border-stone-850 flex items-center justify-between">
                      <div>
                        <div className="flex items-baseline gap-1.5 font-mono">
                          <span className="text-sm font-bold text-stone-100">
                            ${currentVariant?.price || product.base_price}
                          </span>
                          {hasDiscount && (
                            <span className="text-xs text-stone-500 line-through">
                              ${currentVariant?.compare_at_price}
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-stone-500 uppercase font-mono">USD Net</span>
                      </div>

                      <button
                        onClick={() => handleAddToCart(product)}
                        className="px-3.5 py-1.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 font-serif font-bold text-xs tracking-wider transition-all shadow-md shadow-amber-400/10 flex items-center gap-1.5 active:scale-95"
                      >
                        <ShoppingBag className="w-3.5 h-3.5" />
                        <span>Acquérir</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* 5. PARTNER BOUTIQUES & CREATORS CALLOUT */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 border-b border-stone-850 bg-[#060911]">
        <div className="max-w-7xl mx-auto rounded-3xl bg-gradient-to-r from-[#0c111e] via-[#121929] to-[#0c111e] border border-stone-800 p-8 sm:p-12 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-3 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-400/10 text-amber-300 border border-amber-400/20 text-[10px] font-mono uppercase tracking-widest">
              <Store className="w-3.5 h-3.5" />
              <span>Espace Créateurs & Boutiques Partenaires</span>
            </div>
            <h3 className="text-2xl sm:text-3xl font-serif text-stone-100">
              Vous êtes une Maison ou un Créateur Indépendant ?
            </h3>
            <p className="text-xs sm:text-sm text-stone-400 leading-relaxed">
              Rejoignez l&apos;écosystème Maison. Bénéficiez d&apos;une vitrine d&apos;exception personnalisée,
              d&apos;une gestion fluide des commandes multi-vendeurs et de paiements sécurisés certifiés.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto shrink-0">
            <Link
              href="/seller/dashboard"
              className="px-6 py-3.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 font-serif font-semibold text-xs tracking-wider uppercase transition-all shadow-lg shadow-amber-400/10 flex items-center justify-center gap-2"
            >
              <Package className="w-4 h-4" />
              <span>Accéder à l&apos;Espace Créateur</span>
            </Link>
            <Link
              href="/admin/dashboard"
              className="px-5 py-3.5 rounded-xl bg-stone-900 hover:bg-stone-800 text-stone-300 border border-stone-800 font-serif text-xs font-medium transition-colors flex items-center justify-center gap-2"
            >
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span>Supervision Admin</span>
            </Link>
          </div>
        </div>
      </section>

      {/* 6. MAIN FACETED DISCOVERY CATALOG ENGINE */}
      <section id="catalog-discovery" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-6 border-b border-stone-800">
          <div>
            <span className="text-[11px] font-mono uppercase tracking-widest text-amber-400">
              Moteur de Recherche &amp; Catalogue
            </span>
            <h2 className="text-2xl sm:text-3xl font-serif font-light text-stone-100 mt-1">
              {showOnlyFavorites ? "Vos Pièces Favorites" : "Collections Complètes"}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFiltersMobile(!showFiltersMobile)}
              className="lg:hidden inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-stone-900 border border-stone-800 text-xs font-semibold text-stone-200 hover:bg-stone-800 transition-colors"
            >
              <SlidersHorizontal className="w-4 h-4 text-amber-400" />
              <span>Filtres {hasActiveFilters && "•"}</span>
            </button>

            {/* Sort Dropdown */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-stone-400 hidden sm:inline font-mono">Trier :</span>
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
                    favorites: showOnlyFavorites,
                    sort: newSort,
                    page: 1,
                  });
                }}
                className="bg-[#0b101c] border border-stone-800 text-stone-200 text-xs rounded-xl px-3 py-2 focus:outline-none focus:border-amber-400 font-mono"
              >
                <option value="newest">Dernières Arrivées</option>
                <option value="relevance">Pertinence</option>
                <option value="price_asc">Prix : Croissant</option>
                <option value="price_desc">Prix : Décroissant</option>
                <option value="name_asc">Nom : A à Z</option>
                <option value="name_desc">Nom : Z à A</option>
                <option value="oldest">Archives antérieures</option>
              </select>
            </div>
          </div>
        </div>

        {/* Active Filter Chips */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-2 py-4 border-b border-stone-850 text-xs">
            <span className="text-stone-400 font-mono mr-1">Filtres actifs :</span>

            {query && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-400/10 text-amber-300 border border-amber-400/30">
                <span>Mot-clé : &quot;{query}&quot;</span>
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
                      favorites: showOnlyFavorites,
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
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-stone-900 text-stone-200 border border-stone-800">
                <span>
                  Catégorie : {filterOptions?.categories.find((c) => c.id === categoryId)?.name || categoryId}
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
                      favorites: showOnlyFavorites,
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
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-stone-900 text-stone-200 border border-stone-800">
                <span>Maison : {filterOptions?.brands.find((b) => b.id === brandId)?.name || brandId}</span>
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
                      favorites: showOnlyFavorites,
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
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-stone-900 text-stone-200 border border-stone-800">
                <span>Prix : ${minPrice || "0"} – ${maxPrice || "Max"}</span>
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
                      favorites: showOnlyFavorites,
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
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-stone-900 text-stone-200 border border-stone-800">
                <span>Taille : {size}</span>
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
                      favorites: showOnlyFavorites,
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
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-stone-900 text-stone-200 border border-stone-800">
                <span>Teinte : {color}</span>
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
                      favorites: showOnlyFavorites,
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
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                <span>Disponibles en stock</span>
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
                      favorites: showOnlyFavorites,
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

            {showOnlyFavorites && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/30">
                <span>Favoris Uniquement</span>
                <button
                  onClick={() => {
                    setShowOnlyFavorites(false);
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
                      favorites: false,
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
              className="text-xs text-amber-400 hover:text-amber-300 ml-2 font-medium underline underline-offset-4"
            >
              Réinitialiser
            </button>
          </div>
        )}

        {/* Discovery Layout: Filters Sidebar + Catalog Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 pt-8">
          {/* Filters Sidebar */}
          <aside
            className={`lg:block ${
              showFiltersMobile
                ? "fixed inset-0 z-50 bg-[#070a12]/95 p-6 overflow-y-auto block"
                : "hidden"
            } space-y-6 lg:border-r lg:border-stone-850 lg:pr-6`}
          >
            {showFiltersMobile && (
              <div className="flex items-center justify-between pb-4 border-b border-stone-800 lg:hidden">
                <h3 className="text-base font-serif font-medium text-stone-100">Filtres du Catalogue</h3>
                <button
                  onClick={() => setShowFiltersMobile(false)}
                  className="p-1.5 rounded-lg bg-stone-900 text-stone-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}

            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-widest text-stone-400">
                Critères de Sélection
              </span>
              {hasActiveFilters && (
                <button
                  onClick={handleClearAll}
                  className="text-xs text-amber-400 hover:text-amber-300 font-medium inline-flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Effacer</span>
                </button>
              )}
            </div>

            {/* In-Stock Toggle */}
            <div className="p-3.5 rounded-2xl bg-[#0c101d] border border-stone-800/80 flex items-center justify-between">
              <div>
                <label
                  htmlFor="in-stock-toggle"
                  className="text-xs font-semibold text-stone-200 block cursor-pointer"
                >
                  Pièces en stock
                </label>
                <span className="text-[10px] text-stone-500">Masquer les pièces épuisées</span>
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
                    favorites: showOnlyFavorites,
                    sort,
                    page: 1,
                  });
                }}
                className="w-4 h-4 rounded text-amber-500 bg-stone-900 border-stone-700 focus:ring-amber-400 cursor-pointer accent-amber-400"
              />
            </div>

            {/* Category Select */}
            {filterOptions?.categories && filterOptions.categories.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-stone-300 block font-mono">
                  Catégorie
                </label>
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
                      favorites: showOnlyFavorites,
                      sort,
                      page: 1,
                    });
                  }}
                  className="w-full bg-[#0c101d] border border-stone-800 text-stone-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-amber-400"
                >
                  <option value="">Toutes les catégories</option>
                  {filterOptions.categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Brand Select */}
            {filterOptions?.brands && filterOptions.brands.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-stone-300 block font-mono">
                  Maison de Création
                </label>
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
                      favorites: showOnlyFavorites,
                      sort,
                      page: 1,
                    });
                  }}
                  className="w-full bg-[#0c101d] border border-stone-800 text-stone-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-amber-400"
                >
                  <option value="">Toutes les maisons</option>
                  {filterOptions.brands.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Price Range */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-stone-300 block font-mono">
                Fourchette de Prix ($ USD)
              </label>
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
                      favorites: showOnlyFavorites,
                      sort,
                      page: 1,
                    });
                  }}
                  className="w-1/2 bg-[#0c101d] border border-stone-800 text-stone-200 text-xs rounded-xl px-3 py-2 focus:outline-none focus:border-amber-400 font-mono"
                />
                <span className="text-stone-600 text-xs">–</span>
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
                      favorites: showOnlyFavorites,
                      sort,
                      page: 1,
                    });
                  }}
                  className="w-1/2 bg-[#0c101d] border border-stone-800 text-stone-200 text-xs rounded-xl px-3 py-2 focus:outline-none focus:border-amber-400 font-mono"
                />
              </div>
            </div>

            {/* Size Filter Pills */}
            {filterOptions?.sizes && filterOptions.sizes.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-stone-300 block font-mono">
                  Tailles Disponibles
                </label>
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
                        favorites: showOnlyFavorites,
                        sort,
                        page: 1,
                      });
                    }}
                    className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-colors ${
                      !size
                        ? "bg-amber-400 text-stone-950 font-bold"
                        : "bg-stone-900 border border-stone-800 text-stone-400 hover:text-white"
                    }`}
                  >
                    Toutes
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
                            favorites: showOnlyFavorites,
                            sort,
                            page: 1,
                          });
                        }}
                        className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-colors ${
                          isSelected
                            ? "bg-amber-400 text-stone-950 font-bold"
                            : "bg-stone-900 border border-stone-800 text-stone-300 hover:border-stone-700"
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
                <label className="text-xs font-semibold text-stone-300 block font-mono">
                  Coloris & Nuances
                </label>
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
                        favorites: showOnlyFavorites,
                        sort,
                        page: 1,
                      });
                    }}
                    className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-colors ${
                      !color
                        ? "bg-amber-400 text-stone-950 font-bold"
                        : "bg-stone-900 border border-stone-800 text-stone-400 hover:text-white"
                    }`}
                  >
                    Tous
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
                            favorites: showOnlyFavorites,
                            sort,
                            page: 1,
                          });
                        }}
                        className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-colors ${
                          isSelected
                            ? "bg-amber-400 text-stone-950 font-bold"
                            : "bg-stone-900 border border-stone-800 text-stone-300 hover:border-stone-700"
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
                className="w-full mt-4 py-3 rounded-xl bg-amber-400 text-stone-950 font-semibold text-xs tracking-wider uppercase"
              >
                Appliquer les filtres
              </button>
            )}
          </aside>

          {/* Results Grid & Pagination Container */}
          <div className="lg:col-span-3 space-y-8">
            {/* Loading / Error States */}
            {loading && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="h-96 rounded-2xl bg-[#0c111e]/60 border border-stone-800" />
                ))}
              </div>
            )}

            {error && (
              <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                <p className="font-semibold text-stone-100">Impossible de charger le catalogue</p>
                <p className="mt-1">{error}</p>
                <button
                  onClick={executeSearch}
                  className="mt-3 px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-200 text-xs font-medium hover:bg-rose-500/30"
                >
                  Réessayer
                </button>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && products.length === 0 && (
              <div className="text-center py-20 px-4 rounded-3xl bg-[#090d18] border border-stone-800 max-w-lg mx-auto space-y-4">
                <div className="w-14 h-14 rounded-2xl bg-amber-400/10 text-amber-400 flex items-center justify-center mx-auto border border-amber-400/20">
                  <Compass className="w-7 h-7" />
                </div>
                <h3 className="text-base font-serif font-medium text-stone-100">
                  Aucune pièce ne correspond à ces critères
                </h3>
                <p className="text-xs text-stone-400 max-w-sm mx-auto leading-relaxed">
                  Modifiez vos critères de recherche ou réinitialisez les filtres pour découvrir l&apos;ensemble de nos créations.
                </p>
                {hasActiveFilters && (
                  <button
                    onClick={handleClearAll}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-stone-900 hover:bg-stone-800 text-xs font-medium text-stone-200 border border-stone-800 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Réinitialiser les filtres</span>
                  </button>
                )}
              </div>
            )}

            {/* Products Grid */}
            {!loading && !error && products.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map((product) => {
                  const activeVariants = (product.variants || []).filter((v) => v.is_active);
                  const currentVariantId = selectedVariants[product.id] || (activeVariants[0]?.id ?? "");
                  const currentVariant = activeVariants.find((v) => v.id === currentVariantId) || activeVariants[0];
                  const isAdding = addingId === currentVariant?.id;
                  const isAdded = addedSuccessId === currentVariant?.id;
                  const inStockFlag = currentVariant?.is_in_stock ?? product.is_in_stock;
                  const isFav = isFavorite(product.id);

                  return (
                    <div
                      key={product.id}
                      className="group flex flex-col justify-between rounded-2xl bg-[#0c111e] border border-stone-800/80 hover:border-amber-400/40 transition-all p-5 hover:shadow-xl hover:shadow-amber-950/10 relative"
                    >
                      <div>
                        {/* Thumbnail Area */}
                        <div className="w-full h-52 rounded-xl bg-gradient-to-tr from-stone-900 via-[#101726] to-stone-900 border border-stone-800/80 flex flex-col justify-between p-4 relative overflow-hidden group-hover:border-amber-400/30 transition-colors">
                          {(() => {
                            const hero = (product.media || []).find((m) => m.is_primary) || product.media?.[0];
                            if (!hero?.url) return null;
                            return (
                              <img
                                src={hero.url}
                                alt={hero.alt_text || product.name}
                                className="absolute inset-0 w-full h-full object-cover z-0 group-hover:scale-105 transition-transform duration-500"
                                onError={(e) => {
                                  e.currentTarget.style.display = "none";
                                }}
                              />
                            );
                          })()}
                          <div className="absolute inset-0 bg-gradient-to-t from-[#070a12]/90 via-[#070a12]/30 to-transparent pointer-events-none z-5" />

                          {/* Top Badges */}
                          <div className="flex items-center justify-between z-10">
                            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-black/60 text-stone-300 backdrop-blur border border-white/10">
                              {product.brand?.name || "Originals"}
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span
                                className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                                  inStockFlag
                                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                                    : "bg-amber-500/20 text-amber-300 border-amber-500/30"
                                }`}
                              >
                                {inStockFlag ? "En Stock" : "Sur Commande"}
                              </span>
                              <button
                                onClick={() => toggleFavorite(product.id)}
                                className={`p-1 rounded-md backdrop-blur-sm transition-colors ${
                                  isFav
                                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                    : "bg-stone-950/60 text-stone-400 hover:text-rose-300 border border-stone-800"
                                }`}
                                title={isFav ? "Retirer des favoris" : "Ajouter aux favoris"}
                              >
                                <Heart className={`w-3.5 h-3.5 ${isFav ? "fill-rose-400 text-rose-400" : ""}`} />
                              </button>
                            </div>
                          </div>

                          {/* Price Tag on Thumbnail */}
                          <div className="z-10 font-mono">
                            <p className="text-xl font-bold text-stone-100 group-hover:text-amber-200 transition-colors">
                              ${currentVariant ? currentVariant.price : product.base_price}
                            </p>
                            <span className="text-[10px] text-stone-400 uppercase tracking-wider">USD Garanti</span>
                          </div>

                          {/* Hover Quick Actions */}
                          <div className="absolute inset-0 bg-stone-950/75 backdrop-blur-xs opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 p-4 z-20">
                            <button
                              onClick={() => setSelectedProduct(product)}
                              className="px-3.5 py-2 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 text-xs font-serif font-bold tracking-wider shadow-md flex items-center gap-1.5 transition-transform active:scale-95"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              <span>Aperçu</span>
                            </button>
                            <Link
                              href={`/products/${product.id}${returnToParam}`}
                              className="px-3.5 py-2 rounded-xl bg-stone-900 hover:bg-stone-800 text-stone-200 text-xs font-serif font-medium border border-stone-700 shadow-md flex items-center gap-1.5 transition-transform active:scale-95"
                            >
                              <span>Détails</span>
                              <ArrowRight className="w-3 h-3" />
                            </Link>
                          </div>
                        </div>

                        {/* Product Meta */}
                        <div className="mt-4 space-y-1.5">
                          <div className="flex items-center gap-2 text-xs text-amber-400 font-mono">
                            <Tag className="w-3 h-3" />
                            <span>{product.category?.name || "Haute Couture"}</span>
                          </div>
                          <Link
                            href={`/products/${product.id}${returnToParam}`}
                            className="text-sm font-serif font-medium text-stone-100 hover:text-amber-200 transition-colors line-clamp-1 block"
                          >
                            {product.name}
                          </Link>
                          {product.description && (
                            <p className="text-xs text-stone-400 line-clamp-2 leading-relaxed">
                              {product.description}
                            </p>
                          )}
                        </div>

                        {/* Variant SKU selector */}
                        {activeVariants.length > 0 && (
                          <div className="mt-4 space-y-1.5">
                            <label className="text-[10px] font-mono uppercase tracking-wider text-stone-400">
                              Déclinaisons ({activeVariants.length})
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
                                    className={`px-2 py-0.5 rounded-lg text-xs font-mono border transition-colors ${
                                      isSelected
                                        ? "bg-amber-400 border-amber-300 text-stone-950 font-bold shadow-sm"
                                        : "bg-stone-900 border-stone-800 text-stone-300 hover:border-stone-750"
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

                      {/* Add to Cart Footer */}
                      <div className="mt-6 pt-4 border-t border-stone-800/80 flex items-center justify-between gap-3">
                        <div className="text-xs font-mono">
                          <span className="text-stone-500 block text-[10px] uppercase">
                            Disponibilité
                          </span>
                          <span
                            className={`font-semibold text-xs ${
                              inStockFlag ? "text-emerald-400" : "text-amber-400"
                            }`}
                          >
                            {inStockFlag ? "Prêt à l'envoi" : "Stock limité"}
                          </span>
                        </div>

                        <button
                          onClick={() => handleAddToCart(product)}
                          disabled={isAdding || !currentVariant}
                          className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-serif font-bold tracking-wider uppercase transition-all shadow-md ${
                            isAdded
                              ? "bg-emerald-600 text-white"
                              : "bg-amber-400 hover:bg-amber-300 text-stone-950 shadow-amber-400/10 active:scale-95"
                          }`}
                        >
                          {isAdded ? (
                            <>
                              <Check className="w-4 h-4" />
                              <span>Ajouté</span>
                            </>
                          ) : (
                            <>
                              <ShoppingBag className="w-4 h-4" />
                              <span>{isAdding ? "Ajout..." : "Commander"}</span>
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
              <div className="pt-6 border-t border-stone-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-xs">
                <span className="text-stone-400">
                  Page <span className="font-semibold text-stone-100">{page}</span> sur{" "}
                  <span className="font-semibold text-stone-100">{totalPages}</span>
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
                        favorites: showOnlyFavorites,
                        sort,
                        page: newPage,
                      });
                      const el = document.getElementById("catalog-discovery");
                      if (el) el.scrollIntoView({ behavior: "smooth" });
                    }}
                    className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border ${
                      hasPrevious
                        ? "bg-[#0c101d] border-stone-800 text-white hover:bg-stone-800"
                        : "bg-stone-900/40 border-stone-800/40 text-stone-600 cursor-not-allowed"
                    }`}
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span>Précédent</span>
                  </button>

                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
                    .map((p, idx, arr) => (
                      <React.Fragment key={p}>
                        {idx > 0 && arr[idx - 1] !== p - 1 && (
                          <span className="text-stone-600 px-1">...</span>
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
                              favorites: showOnlyFavorites,
                              sort,
                              page: p,
                            });
                            const el = document.getElementById("catalog-discovery");
                            if (el) el.scrollIntoView({ behavior: "smooth" });
                          }}
                          className={`w-8 h-8 rounded-xl font-bold transition-colors ${
                            p === page
                              ? "bg-amber-400 text-stone-950"
                              : "bg-[#0c101d] border border-stone-800 text-stone-300 hover:bg-stone-800"
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
                        favorites: showOnlyFavorites,
                        sort,
                        page: newPage,
                      });
                      const el = document.getElementById("catalog-discovery");
                      if (el) el.scrollIntoView({ behavior: "smooth" });
                    }}
                    className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border ${
                      hasNext
                        ? "bg-[#0c101d] border-stone-800 text-white hover:bg-stone-800"
                        : "bg-stone-900/40 border-stone-800/40 text-stone-600 cursor-not-allowed"
                    }`}
                  >
                    <span>Suivant</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* QUICK VIEW MODAL */}
      {selectedProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-[#0b101c] border border-stone-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setSelectedProduct(null)}
              className="absolute top-5 right-5 p-2 rounded-xl bg-stone-900 text-stone-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-400/10 text-amber-300 border border-amber-400/20">
                  {selectedProduct.brand?.name || "Original"}
                </span>
                <span className="text-xs text-stone-600">•</span>
                <span className="text-xs text-stone-400">{selectedProduct.category?.name || "Haute Couture"}</span>
              </div>
              <h2 className="text-2xl font-serif font-light text-stone-100">{selectedProduct.name}</h2>
              <p className="text-2xl font-mono font-bold text-amber-300">
                ${selectedProduct.base_price} <span className="text-xs font-normal text-stone-400">USD Net</span>
              </p>
            </div>

            {selectedProduct.description && (
              <div className="space-y-1">
                <h4 className="text-[11px] font-mono uppercase tracking-widest text-stone-400">Description</h4>
                <p className="text-xs sm:text-sm text-stone-300 leading-relaxed">{selectedProduct.description}</p>
              </div>
            )}

            {/* Active Variants in Modal */}
            {selectedProduct.variants && selectedProduct.variants.filter((v) => v.is_active).length > 0 && (
              <div className="space-y-2">
                <label className="text-[11px] font-mono uppercase tracking-widest text-stone-400">
                  Déclinaison &amp; Référence SKU
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
                          className={`p-2.5 rounded-xl border text-left text-xs transition-colors font-mono ${
                            isSel
                              ? "bg-amber-400/15 border-amber-400 text-amber-200"
                              : "bg-[#070a12] border-stone-800 text-stone-300 hover:border-stone-700"
                          }`}
                        >
                          <p className="font-bold">{v.sku}</p>
                          <p className="text-[11px] text-stone-400">
                            {v.size || v.color ? `${v.size || ""} • ${v.color || ""}` : `$${v.price}`}
                          </p>
                          <span
                            className={`inline-block mt-1 text-[10px] font-medium ${
                              v.is_in_stock ? "text-emerald-400" : "text-amber-400"
                            }`}
                          >
                            {v.is_in_stock ? "En stock" : "Sur commande"}
                          </span>
                        </button>
                      );
                    })}
                </div>
              </div>
            )}

            {/* Modal Actions */}
            <div className="pt-4 border-t border-stone-850 flex flex-col sm:flex-row items-center justify-between gap-3">
              <Link
                href={`/products/${selectedProduct.id}${returnToParam}`}
                className="text-xs text-amber-300 hover:text-amber-200 underline underline-offset-4 flex items-center gap-1 font-serif"
              >
                <span>Consulter la fiche détaillée</span>
                <ArrowRight className="w-3 h-3" />
              </Link>

              <button
                onClick={() => {
                  handleAddToCart(selectedProduct);
                  setSelectedProduct(null);
                }}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-amber-400 hover:bg-amber-300 text-stone-950 font-serif font-bold text-xs tracking-wider uppercase shadow-lg shadow-amber-400/10 flex items-center justify-center gap-2"
              >
                <ShoppingBag className="w-4 h-4" />
                <span>Ajouter à la Sélection</span>
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
        <div className="min-h-screen flex items-center justify-center bg-[#070a12] text-stone-400 text-xs font-mono">
          Initialisation de la Maison...
        </div>
      }
    >
      <CatalogSearchContent />
    </Suspense>
  );
}
