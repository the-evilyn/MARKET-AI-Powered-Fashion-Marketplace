"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Package,
  Plus,
  Edit2,
  Trash2,
  Archive,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Layers,
  ChevronDown,
  ChevronUp,
  X,
  ShieldAlert,
  Image as ImageIcon,
  Upload,
} from "lucide-react";
import SellerNav from "@/components/SellerNav";
import { api, Product, ProductVariant } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function SellerProductsPage() {
  const { user, loading: authLoading, quickSellerLogin } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Expanded product ID for variants view
  const [expandedProductId, setExpandedProductId] = useState<string | null>(null);

  // Product Modal State
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [prodName, setProdName] = useState("");
  const [prodPrice, setProdPrice] = useState("");
  const [prodStatus, setProdStatus] = useState<"DRAFT" | "ACTIVE" | "ARCHIVED">("DRAFT");
  const [prodDesc, setProdDesc] = useState("");
  const [modalSubmitting, setModalSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Variant Modal State
  const [showVariantModal, setShowVariantModal] = useState(false);
  const [targetProductId, setTargetProductId] = useState<string | null>(null);
  const [editingVariant, setEditingVariant] = useState<ProductVariant | null>(null);
  const [varSku, setVarSku] = useState("");
  const [varPrice, setVarPrice] = useState("");
  const [varComparePrice, setVarComparePrice] = useState("");
  const [varColor, setVarColor] = useState("");
  const [varSize, setVarSize] = useState("");
  const [varSubmitting, setVarSubmitting] = useState(false);
  const [varError, setVarError] = useState<string | null>(null);

  // Media Modal State
  const [showMediaModal, setShowMediaModal] = useState(false);
  const [mediaProduct, setMediaProduct] = useState<Product | null>(null);
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [mediaAlt, setMediaAlt] = useState("");
  const [mediaIsPrimary, setMediaIsPrimary] = useState(false);
  const [mediaUploading, setMediaUploading] = useState(false);
  const [mediaError, setMediaError] = useState<string | null>(null);

  const openMediaModal = (p: Product) => {
    setMediaProduct(p);
    setMediaFile(null);
    setMediaAlt("");
    setMediaIsPrimary(false);
    setMediaError(null);
    setShowMediaModal(true);
  };

  const handleUploadMedia = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mediaProduct || !mediaFile) return;
    setMediaError(null);
    setMediaUploading(true);
    try {
      await api.uploadProductMedia(mediaProduct.id, mediaFile, {
        alt_text: mediaAlt.trim() || undefined,
        is_primary: mediaIsPrimary,
      });
      setMediaFile(null);
      setMediaAlt("");
      setMediaIsPrimary(false);
      await fetchProducts();
      const updated = await api.getProduct(mediaProduct.id);
      setMediaProduct(updated);
    } catch (err: unknown) {
      setMediaError(err instanceof Error ? err.message : "Failed to upload image");
    } finally {
      setMediaUploading(false);
    }
  };

  const handleDeleteMedia = async (mediaId: string) => {
    if (!mediaProduct) return;
    if (!confirm("Are you sure you want to remove this media image?")) return;
    try {
      await api.deleteProductMedia(mediaProduct.id, mediaId);
      await fetchProducts();
      const updated = await api.getProduct(mediaProduct.id);
      setMediaProduct(updated);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete media");
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSellerProducts();
      setProducts(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load products");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && (user.role === "SELLER" || user.role === "ADMIN")) {
      fetchProducts();
    } else {
      setLoading(false);
    }
  }, [user]);

  const openCreateProductModal = () => {
    setEditingProduct(null);
    setProdName("");
    setProdPrice("");
    setProdStatus("DRAFT");
    setProdDesc("");
    setModalError(null);
    setShowProductModal(true);
  };

  const openEditProductModal = (p: Product) => {
    setEditingProduct(p);
    setProdName(p.name);
    setProdPrice(p.base_price);
    setProdStatus(p.status);
    setProdDesc(p.description || "");
    setModalError(null);
    setShowProductModal(true);
  };

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setModalSubmitting(true);
    try {
      if (editingProduct) {
        await api.updateSellerProduct(editingProduct.id, {
          name: prodName,
          base_price: prodPrice,
          status: prodStatus,
          description: prodDesc,
        });
      } else {
        await api.createSellerProduct({
          name: prodName,
          base_price: prodPrice,
          status: prodStatus,
          description: prodDesc,
        });
      }
      setShowProductModal(false);
      await fetchProducts();
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err.message : "Failed to save product");
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleDeleteOrArchiveProduct = async (product: Product) => {
    const confirmMsg =
      product.status === "ACTIVE"
        ? `Are you sure you want to delete/archive "${product.name}"? If it has previous order history, it will be safely archived.`
        : `Delete "${product.name}"?`;
    if (!confirm(confirmMsg)) return;

    try {
      await api.deleteSellerProduct(product.id);
      await fetchProducts();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Delete failed");
    }
  };

  // Variant Modal Handlers
  const openAddVariantModal = (productId: string) => {
    setTargetProductId(productId);
    setEditingVariant(null);
    setVarSku("");
    setVarPrice("");
    setVarComparePrice("");
    setVarColor("");
    setVarSize("");
    setVarError(null);
    setShowVariantModal(true);
  };

  const openEditVariantModal = (productId: string, v: ProductVariant) => {
    setTargetProductId(productId);
    setEditingVariant(v);
    setVarSku(v.sku);
    setVarPrice(v.price);
    setVarComparePrice(v.compare_at_price || "");
    setVarColor(v.color || "");
    setVarSize(v.size || "");
    setVarError(null);
    setShowVariantModal(true);
  };

  const handleSaveVariant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetProductId) return;
    setVarError(null);
    setVarSubmitting(true);
    try {
      if (editingVariant) {
        await api.updateSellerVariant(targetProductId, editingVariant.id, {
          sku: varSku,
          price: varPrice,
          compare_at_price: varComparePrice ? varComparePrice : undefined,
          color: varColor,
          size: varSize,
        });
      } else {
        await api.createSellerVariant(targetProductId, {
          sku: varSku,
          price: varPrice,
          compare_at_price: varComparePrice ? varComparePrice : undefined,
          color: varColor,
          size: varSize,
        });
      }
      setShowVariantModal(false);
      await fetchProducts();
    } catch (err: unknown) {
      setVarError(err instanceof Error ? err.message : "Failed to save variant");
    } finally {
      setVarSubmitting(false);
    }
  };

  const handleDeleteVariant = async (productId: string, variantId: string) => {
    if (!confirm("Are you sure you want to remove/deactivate this variant?")) return;
    try {
      await api.deleteSellerVariant(productId, variantId);
      await fetchProducts();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete variant");
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
            Sign in as an authorized merchant to manage your product listings.
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
        {/* Header & Add Button */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Product Management
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Create and manage listings, SKUs, sizes, colors, and catalog visibility.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchProducts}
              disabled={loading}
              className="p-2 rounded-lg text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors"
              title="Refresh listings"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={openCreateProductModal}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/30"
            >
              <Plus className="w-4 h-4" />
              <span>Add New Product</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Product List */}
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="h-24 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse"
              />
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <Package className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">No products found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              You have not created any products yet. Click &quot;Add New Product&quot; to publish your first garment.
            </p>
            <button
              onClick={openCreateProductModal}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Add First Product</span>
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {products.map((p) => {
              const isExpanded = expandedProductId === p.id;
              const variants = p.variants || [];

              return (
                <div
                  key={p.id}
                  className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden transition-colors hover:border-slate-700/80"
                >
                  {/* Product Card Header */}
                  <div className="p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 text-indigo-400 flex items-center justify-center flex-shrink-0 font-bold text-sm">
                        <Package className="w-5 h-5" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-base font-bold text-white">{p.name}</h3>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              p.status === "ACTIVE"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : p.status === "DRAFT"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-red-500/10 text-red-400 border border-red-500/20"
                            }`}
                          >
                            {p.status}
                          </span>
                          {!p.is_active && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">
                              Inactive
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 font-mono">
                          Slug: {p.slug} &bull; Base Price: ${Number(p.base_price).toFixed(2)}
                        </p>
                        {p.description && (
                          <p className="text-xs text-slate-400 line-clamp-1 max-w-xl">
                            {p.description}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 self-end md:self-center">
                      <button
                        onClick={() => openMediaModal(p)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/20 transition-colors"
                        title="Manage product media assets"
                      >
                        <ImageIcon className="w-3.5 h-3.5 text-indigo-400" />
                        <span>{(p.media || []).length} Media</span>
                      </button>

                      <button
                        onClick={() =>
                          setExpandedProductId(isExpanded ? null : p.id)
                        }
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                      >
                        <Layers className="w-3.5 h-3.5 text-indigo-400" />
                        <span>{variants.length} Variants</span>
                        {isExpanded ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </button>

                      <button
                        onClick={() => openEditProductModal(p)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                        title="Edit product"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => handleDeleteOrArchiveProduct(p)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
                        title="Delete or Archive product"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Expanded Variants Accordion */}
                  {isExpanded && (
                    <div className="bg-slate-950/60 border-t border-slate-800/80 p-5 space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
                          <Layers className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Purchasable SKU Variants for {p.name}</span>
                        </div>
                        <button
                          onClick={() => openAddVariantModal(p.id)}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600 hover:text-white transition-colors"
                        >
                          <Plus className="w-3.5 h-3.5" />
                          <span>Add SKU Variant</span>
                        </button>
                      </div>

                      {variants.length === 0 ? (
                        <div className="py-6 text-center text-slate-500 text-xs">
                          No SKU variants yet. Add size/color variants to make this product purchasable.
                        </div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs text-slate-300">
                            <thead className="text-[10px] uppercase font-semibold text-slate-400 border-b border-slate-800">
                              <tr>
                                <th className="py-2 px-3">SKU</th>
                                <th className="py-2 px-3">Color</th>
                                <th className="py-2 px-3">Size</th>
                                <th className="py-2 px-3">Price</th>
                                <th className="py-2 px-3">Compare At</th>
                                <th className="py-2 px-3">Stock Available</th>
                                <th className="py-2 px-3 text-right">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60 font-mono">
                              {variants.map((v) => {
                                const onHand = v.inventory?.quantity_on_hand ?? 0;
                                const reserved = v.inventory?.quantity_reserved ?? 0;
                                const available = Math.max(0, onHand - reserved);

                                return (
                                  <tr
                                    key={v.id}
                                    className="hover:bg-slate-900/40 transition-colors"
                                  >
                                    <td className="py-2.5 px-3 font-bold text-white">
                                      {v.sku}
                                    </td>
                                    <td className="py-2.5 px-3 font-sans">
                                      {v.color || "-"}
                                    </td>
                                    <td className="py-2.5 px-3 font-sans">
                                      {v.size || "-"}
                                    </td>
                                    <td className="py-2.5 px-3 text-emerald-400 font-bold">
                                      ${Number(v.price).toFixed(2)}
                                    </td>
                                    <td className="py-2.5 px-3 text-slate-500">
                                      {v.compare_at_price
                                        ? `$${Number(v.compare_at_price).toFixed(2)}`
                                        : "-"}
                                    </td>
                                    <td className="py-2.5 px-3 font-sans">
                                      <span
                                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                                          available > 5
                                            ? "bg-emerald-500/10 text-emerald-400"
                                            : available > 0
                                            ? "bg-amber-500/10 text-amber-400"
                                            : "bg-red-500/10 text-red-400"
                                        }`}
                                      >
                                        {available} in stock
                                      </span>
                                    </td>
                                    <td className="py-2.5 px-3 text-right font-sans">
                                      <div className="flex items-center justify-end gap-1">
                                        <button
                                          onClick={() => openEditVariantModal(p.id, v)}
                                          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
                                          title="Edit variant"
                                        >
                                          <Edit2 className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                          onClick={() => handleDeleteVariant(p.id, v.id)}
                                          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-red-400"
                                          title="Delete variant"
                                        >
                                          <Trash2 className="w-3.5 h-3.5" />
                                        </button>
                                      </div>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Product Modal (Create / Edit) */}
      {showProductModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl relative">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">
                {editingProduct ? "Edit Product Listing" : "Create New Product"}
              </h3>
              <button
                onClick={() => setShowProductModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                {modalError}
              </div>
            )}

            <form onSubmit={handleSaveProduct} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Product Name *
                </label>
                <input
                  type="text"
                  required
                  value={prodName}
                  onChange={(e) => setProdName(e.target.value)}
                  placeholder="e.g. Silk Evening Dress"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Base Price (USD) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={prodPrice}
                    onChange={(e) => setProdPrice(e.target.value)}
                    placeholder="120.00"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Listing Status *
                  </label>
                  <select
                    value={prodStatus}
                    onChange={(e) =>
                      setProdStatus(e.target.value as "DRAFT" | "ACTIVE" | "ARCHIVED")
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="DRAFT">DRAFT (Hidden)</option>
                    <option value="ACTIVE">ACTIVE (Published)</option>
                    <option value="ARCHIVED">ARCHIVED (Discontinued)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={prodDesc}
                  onChange={(e) => setProdDesc(e.target.value)}
                  placeholder="Describe material, cut, design details..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowProductModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalSubmitting}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
                >
                  {modalSubmitting ? "Saving..." : editingProduct ? "Save Changes" : "Create Product"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Variant Modal (Create / Edit) */}
      {showVariantModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl relative">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">
                {editingVariant ? "Edit Variant SKU" : "Add New SKU Variant"}
              </h3>
              <button
                onClick={() => setShowVariantModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {varError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                {varError}
              </div>
            )}

            <form onSubmit={handleSaveVariant} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Merchant SKU Code *
                </label>
                <input
                  type="text"
                  required
                  value={varSku}
                  onChange={(e) => setVarSku(e.target.value)}
                  placeholder="e.g. SLK-DRS-RED-S"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Color
                  </label>
                  <input
                    type="text"
                    value={varColor}
                    onChange={(e) => setVarColor(e.target.value)}
                    placeholder="e.g. Crimson Red"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Size
                  </label>
                  <input
                    type="text"
                    value={varSize}
                    onChange={(e) => setVarSize(e.target.value)}
                    placeholder="e.g. S, M, L, 38, 40"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Selling Price *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={varPrice}
                    onChange={(e) => setVarPrice(e.target.value)}
                    placeholder="120.00"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Compare At Price
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={varComparePrice}
                    onChange={(e) => setVarComparePrice(e.target.value)}
                    placeholder="150.00"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowVariantModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={varSubmitting}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
                >
                  {varSubmitting ? "Saving..." : editingVariant ? "Update Variant" : "Add Variant"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Product Media Management Modal */}
      {showMediaModal && mediaProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <ImageIcon className="w-5 h-5 text-indigo-400" />
                  <span>Media Gallery for {mediaProduct.name}</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Upload high-resolution JPEG, PNG, or WebP images to MinIO storage.
                </p>
              </div>
              <button
                onClick={() => setShowMediaModal(false)}
                className="p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {mediaError && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{mediaError}</span>
              </div>
            )}

            {/* Current Media Assets Grid */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Uploaded Images ({(mediaProduct.media || []).length})
              </h3>
              {(mediaProduct.media || []).length === 0 ? (
                <div className="p-6 rounded-2xl bg-slate-950/60 border border-dashed border-slate-800 text-center text-slate-500 text-xs">
                  No images uploaded yet. Use the form below to upload your first image.
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {mediaProduct.media?.map((m) => (
                    <div
                      key={m.id}
                      className="group relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 aspect-square flex flex-col justify-between"
                    >
                      <img
                        src={m.url}
                        alt={m.alt_text || "Product image"}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute top-2 left-2 z-10">
                        {m.is_primary && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-600 text-white shadow">
                            Primary
                          </span>
                        )}
                      </div>
                      <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center p-2">
                        <button
                          type="button"
                          onClick={() => handleDeleteMedia(m.id)}
                          className="p-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-semibold shadow flex items-center gap-1.5 transition-transform active:scale-95"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>Delete</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Upload New Image Form */}
            <form onSubmit={handleUploadMedia} className="space-y-4 pt-4 border-t border-slate-800">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Upload className="w-4 h-4 text-indigo-400" />
                <span>Upload New Image</span>
              </h3>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Select File (JPEG, PNG, WebP &le; 10MB) *
                  </label>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    required
                    onChange={(e) => setMediaFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600/20 file:text-indigo-300 hover:file:bg-indigo-600/30 cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Alt Text (Optional)
                  </label>
                  <input
                    type="text"
                    value={mediaAlt}
                    onChange={(e) => setMediaAlt(e.target.value)}
                    placeholder="E.g. Front view of classic merino knit"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_primary_checkbox"
                    checked={mediaIsPrimary}
                    onChange={(e) => setMediaIsPrimary(e.target.checked)}
                    className="rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-0"
                  />
                  <label htmlFor="is_primary_checkbox" className="text-xs text-slate-300 cursor-pointer">
                    Set as Primary Hero Image
                  </label>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowMediaModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={mediaUploading || !mediaFile}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50 flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  <span>{mediaUploading ? "Uploading to MinIO..." : "Upload Image"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
