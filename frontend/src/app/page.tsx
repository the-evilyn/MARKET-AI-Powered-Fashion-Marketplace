"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, AlertCircle, RefreshCw, Layers, Database, Cpu, HardDrive } from "lucide-react";

interface HealthData {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
}

interface ReadinessData {
  status: string;
  components: {
    database: string;
    redis: string;
    storage: string;
  };
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const checkStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthRes, readyRes] = await Promise.all([
        fetch(`${apiUrl}/health`, { cache: "no-store" }),
        fetch(`${apiUrl}/health/ready`, { cache: "no-store" }),
      ]);

      if (healthRes.ok) {
        const hData = await healthRes.json();
        setHealth(hData);
      } else {
        setError(`Backend health check failed: HTTP ${healthRes.status}`);
      }

      if (readyRes.ok) {
        const rData = await readyRes.json();
        setReadiness(rData);
      } else {
        const rData = await readyRes.json().catch(() => null);
        if (rData) setReadiness(rData);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unable to reach backend API";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 p-6 md:p-12 text-slate-100">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <header className="border-b border-slate-800 pb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-3">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Phase 0 Foundation Active
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
              AI Fashion Marketplace
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base">
              Modular Monolith Foundation &bull; Next.js &bull; FastAPI &bull; PostgreSQL &bull; Redis
            </p>
          </div>
          <button
            onClick={checkStatus}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800/50 text-white rounded-lg font-medium text-sm transition-colors shadow-lg shadow-indigo-600/20 self-start md:self-center"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Check Live Status
          </button>
        </header>

        {/* Backend Connectivity Status */}
        <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            Backend Connection Status
          </h2>

          {loading && (
            <div className="text-slate-400 text-sm py-4 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
              Probing backend health endpoints ({apiUrl})...
            </div>
          )}

          {error && !loading && (
            <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Backend endpoint not reachable yet</p>
                <p className="text-xs text-amber-300/80 mt-1">
                  Target: <code className="bg-black/30 px-1 py-0.5 rounded">{apiUrl}</code>. Ensure the FastAPI container or dev server is running.
                </p>
              </div>
            </div>
          )}

          {health && !loading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <span className="text-xs font-medium text-slate-400 uppercase">Service Status</span>
                <p className="text-lg font-semibold text-emerald-400 flex items-center gap-2 mt-1">
                  <CheckCircle2 className="w-5 h-5" />
                  {health.status.toUpperCase()}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <span className="text-xs font-medium text-slate-400 uppercase">API Version</span>
                <p className="text-lg font-semibold text-white mt-1">v{health.version}</p>
              </div>
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <span className="text-xs font-medium text-slate-400 uppercase">Environment</span>
                <p className="text-lg font-semibold text-white capitalize mt-1">{health.environment}</p>
              </div>
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <span className="text-xs font-medium text-slate-400 uppercase">Dependencies Readiness</span>
                <p className={`text-lg font-semibold mt-1 capitalize ${readiness?.status === "ready" ? "text-emerald-400" : "text-amber-400"}`}>
                  {readiness?.status || "Checking..."}
                </p>
              </div>
            </div>
          )}
        </section>

        {/* Infrastructure & Architecture Readiness Matrix */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-white">Phase 0 Architecture Verification</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white">PostgreSQL + pgvector</h3>
              <p className="text-xs text-slate-400">
                Primary relational storage with vector embeddings extension initialized for AI recommendations and search in future phases.
              </p>
              <div className="pt-2 flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${readiness?.components.database === "up" ? "bg-emerald-400" : "bg-slate-500"}`}></span>
                <span className="text-slate-300">Status: {readiness?.components.database || "Configured"}</span>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white">Redis 7 Cache</h3>
              <p className="text-xs text-slate-400">
                In-memory cache and session state broker with async connection pooling and ping diagnostics configured.
              </p>
              <div className="pt-2 flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${readiness?.components.redis === "up" ? "bg-emerald-400" : "bg-slate-500"}`}></span>
                <span className="text-slate-300">Status: {readiness?.components.redis || "Configured"}</span>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                <HardDrive className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white">MinIO Object Storage</h3>
              <p className="text-xs text-slate-400">
                S3-compatible asset store prepared for fashion imagery, model catalogs, and generated virtual try-on assets.
              </p>
              <div className="pt-2 flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${readiness?.components.storage === "up" ? "bg-emerald-400" : "bg-slate-500"}`}></span>
                <span className="text-slate-300">Status: {readiness?.components.storage || "Configured"}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Phase Boundary Notice */}
        <section className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/80 text-xs text-slate-400">
          <p className="font-medium text-slate-300 mb-1">Scope Compliance Notice (Phase 0)</p>
          <p>
            Marketplace business features (Catalog, Cart, Orders, Payments, Reviews, AI features) remain intentionally uninitialized until Phase 0 foundation review is approved.
          </p>
        </section>
      </div>
    </main>
  );
}
