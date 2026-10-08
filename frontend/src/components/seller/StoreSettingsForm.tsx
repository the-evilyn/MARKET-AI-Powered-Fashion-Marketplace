"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Store,
  Upload,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  Mail,
  Phone,
  FileText,
  Sparkles,
} from "lucide-react";
import { api, SellerStoreProfile, SellerStoreProfileUpdate } from "@/lib/api";

interface StoreSettingsFormProps {
  initialProfile: SellerStoreProfile;
  onProfileUpdated?: (profile: SellerStoreProfile) => void;
}

export default function StoreSettingsForm({
  initialProfile,
  onProfileUpdated,
}: StoreSettingsFormProps) {
  const [profile, setProfile] = useState<SellerStoreProfile>(initialProfile);
  const [storeName, setStoreName] = useState(initialProfile.store_name);
  const [slug, setSlug] = useState(initialProfile.slug);
  const [bio, setBio] = useState(initialProfile.bio || "");
  const [contactEmail, setContactEmail] = useState(initialProfile.contact_email || "");
  const [contactPhone, setContactPhone] = useState(initialProfile.contact_phone || "");

  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingBanner, setUploadingBanner] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const logoInputRef = useRef<HTMLInputElement>(null);
  const bannerInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setProfile(initialProfile);
    setStoreName(initialProfile.store_name);
    setSlug(initialProfile.slug);
    setBio(initialProfile.bio || "");
    setContactEmail(initialProfile.contact_email || "");
    setContactPhone(initialProfile.contact_phone || "");
  }, [initialProfile]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    const updatePayload: SellerStoreProfileUpdate = {
      store_name: storeName.trim(),
      slug: slug.trim().toLowerCase(),
      bio: bio.trim() || undefined,
      contact_email: contactEmail.trim() || undefined,
      contact_phone: contactPhone.trim() || undefined,
    };

    try {
      const updated = await api.updateSellerStoreProfile(updatePayload);
      setProfile(updated);
      setStoreName(updated.store_name);
      setSlug(updated.slug);
      setBio(updated.bio || "");
      setContactEmail(updated.contact_email || "");
      setContactPhone(updated.contact_phone || "");
      setSuccessMessage("Store settings saved successfully!");
      if (onProfileUpdated) onProfileUpdated(updated);
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to save store settings.");
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setErrorMessage("Logo file exceeds the 5MB size limit.");
      return;
    }

    setUploadingLogo(true);
    setErrorMessage(null);
    try {
      const res = await api.uploadSellerStoreLogo(file);
      setProfile((prev) => ({ ...prev, logo_url: res.url }));
      setSuccessMessage("Logo updated successfully!");
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to upload logo.");
    } finally {
      setUploadingLogo(false);
      if (logoInputRef.current) logoInputRef.current.value = "";
    }
  };

  const handleBannerUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage("Banner file exceeds the 10MB size limit.");
      return;
    }

    setUploadingBanner(true);
    setErrorMessage(null);
    try {
      const res = await api.uploadSellerStoreBanner(file);
      setProfile((prev) => ({ ...prev, banner_url: res.url }));
      setSuccessMessage("Banner updated successfully!");
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to upload banner.");
    } finally {
      setUploadingBanner(false);
      if (bannerInputRef.current) bannerInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-8">
      {/* Overview & Quick Actions Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 relative overflow-hidden shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative z-10">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-600/30 overflow-hidden border border-white/10 shrink-0">
              {profile.logo_url ? (
                <img
                  src={profile.logo_url}
                  alt={profile.store_name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Store className="w-8 h-8" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-xl font-extrabold text-white tracking-tight">
                  {profile.store_name}
                </h2>
                {profile.is_verified && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Verified Designer
                  </span>
                )}
                <span
                  className={`text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                    profile.status === "ACTIVE"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : profile.status === "PENDING"
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                      : "bg-red-500/10 text-red-400 border-red-500/20"
                  }`}
                >
                  {profile.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                <span>Public URL:</span>
                <code className="text-indigo-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                  /store/{profile.slug}
                </code>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href={`/store/${profile.slug}`}
              target="_blank"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <ExternalLink className="w-4 h-4" />
              <span>View Public Storefront</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-medium flex items-center gap-3 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400" />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-medium flex items-center gap-3 animate-fade-in">
          <AlertCircle className="w-5 h-5 shrink-0 text-red-400" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Store Branding Assets (MinIO) */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>Storefront Visual Assets</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Upload your high-resolution banner and boutique logo to create a premium editorial feel.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          {/* Banner Upload Box */}
          <div className="md:col-span-2 space-y-3">
            <label className="text-xs font-semibold text-slate-300 block">
              Store Hero Banner (16:9 or panoramic, max 10MB)
            </label>
            <div className="h-44 sm:h-52 w-full rounded-2xl bg-slate-950 border border-slate-800 relative overflow-hidden group flex items-center justify-center">
              {profile.banner_url ? (
                <img
                  src={profile.banner_url}
                  alt="Store banner"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-center p-6 space-y-2">
                  <ImageIcon className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-xs text-slate-500">No banner uploaded yet.</p>
                </div>
              )}
              <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-sm">
                <button
                  type="button"
                  onClick={() => bannerInputRef.current?.click()}
                  disabled={uploadingBanner}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-white text-slate-950 hover:bg-slate-200 transition-all flex items-center gap-2 shadow-lg"
                >
                  {uploadingBanner ? (
                    <RefreshCw className="w-4 h-4 animate-spin text-slate-950" />
                  ) : (
                    <Upload className="w-4 h-4 text-slate-950" />
                  )}
                  <span>{uploadingBanner ? "Uploading..." : "Change Banner"}</span>
                </button>
              </div>
            </div>
            <input
              ref={bannerInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleBannerUpload}
              className="hidden"
            />
          </div>

          {/* Logo Upload Box */}
          <div className="space-y-3">
            <label className="text-xs font-semibold text-slate-300 block">
              Store Logo / Avatar (Square, max 5MB)
            </label>
            <div className="h-44 sm:h-52 w-full rounded-2xl bg-slate-950 border border-slate-800 relative overflow-hidden group flex items-center justify-center">
              {profile.logo_url ? (
                <img
                  src={profile.logo_url}
                  alt="Store logo"
                  className="w-28 h-28 rounded-full object-cover border-2 border-indigo-500/30 shadow-lg"
                />
              ) : (
                <div className="text-center p-4 space-y-2">
                  <Store className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-xs text-slate-500">No logo uploaded.</p>
                </div>
              )}
              <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-sm">
                <button
                  type="button"
                  onClick={() => logoInputRef.current?.click()}
                  disabled={uploadingLogo}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-white text-slate-950 hover:bg-slate-200 transition-all flex items-center gap-2 shadow-lg"
                >
                  {uploadingLogo ? (
                    <RefreshCw className="w-4 h-4 animate-spin text-slate-950" />
                  ) : (
                    <Upload className="w-4 h-4 text-slate-950" />
                  )}
                  <span>{uploadingLogo ? "Uploading..." : "Change Logo"}</span>
                </button>
              </div>
            </div>
            <input
              ref={logoInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleLogoUpload}
              className="hidden"
            />
          </div>
        </div>
      </div>

      {/* Store Identity & Narrative Form */}
      <form onSubmit={handleSaveProfile} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            <span>Store Information & Narrative</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Configure how your brand appears across marketplace search and product cards.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* Store Name */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">
              Store Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              required
              value={storeName}
              onChange={(e) => setStoreName(e.target.value)}
              placeholder="e.g. Atelier Sartoriale"
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Store Slug */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">
              Store Slug (URL Identifier) <span className="text-red-400">*</span>
            </label>
            <div className="flex items-center rounded-xl bg-slate-950 border border-slate-800 overflow-hidden focus-within:border-indigo-500 transition-colors">
              <span className="text-xs text-slate-500 px-3 select-none">/store/</span>
              <input
                type="text"
                required
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="atelier-sartoriale"
                className="w-full py-3 pr-4 bg-transparent text-white text-xs placeholder:text-slate-600 focus:outline-none"
              />
            </div>
            <p className="text-[11px] text-slate-500">
              Only lowercase letters, numbers, and hyphens (3-120 chars).
            </p>
          </div>

          {/* Contact Email */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5 text-slate-400" />
              <span>Public Business Email (Optional)</span>
            </label>
            <input
              type="email"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
              placeholder="concierge@brand.com"
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
            />
            <p className="text-[11px] text-slate-500">
              Shown to customers for inquiries. Your private login email is never disclosed.
            </p>
          </div>

          {/* Contact Phone */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Phone className="w-3.5 h-3.5 text-slate-400" />
              <span>Business Phone (Optional)</span>
            </label>
            <input
              type="text"
              value={contactPhone}
              onChange={(e) => setContactPhone(e.target.value)}
              placeholder="+33 1 40 20 50 00"
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
        </div>

        {/* Brand Bio Narrative */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300">
            Brand Bio & Narrative (Optional)
          </label>
          <textarea
            rows={4}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="Tell your brand's heritage, sustainability ethos, and craftsmanship narrative..."
            className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-colors resize-y"
          />
        </div>

        {/* Submit Action */}
        <div className="flex items-center justify-end pt-4 border-t border-slate-800">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-3 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
            <span>{saving ? "Saving Changes..." : "Save Store Settings"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
