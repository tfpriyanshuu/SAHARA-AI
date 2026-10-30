"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Shield, Lock, User, ArrowRight, CheckCircle2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const QUICK_ACCOUNTS = [
  {
    role: "coordinator",
    title: "Care Coordinator",
    name: "Anvesha Sharma (8267069623)",
    username: "coordinator1",
    password: "coord123",
    badgeColor: "bg-emerald-50 text-emerald-800 border-emerald-300"
  },
  {
    role: "senior",
    title: "Senior Citizen",
    name: "Harshit Thakur (9451818283)",
    username: "senior1",
    password: "senior123",
    badgeColor: "bg-blue-50 text-blue-800 border-blue-300"
  },
  {
    role: "family",
    title: "Family Member (Mummy)",
    name: "Anchal Mishra (8957266841)",
    username: "family1",
    password: "family123",
    badgeColor: "bg-amber-50 text-amber-800 border-amber-300"
  },
  {
    role: "ops_manager",
    title: "Operations Lead",
    name: "Vikram Joshi",
    username: "ops1",
    password: "ops123",
    badgeColor: "bg-purple-50 text-purple-800 border-purple-300"
  }
];

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent, customUser?: string, customPass?: string) => {
    if (e) e.preventDefault();
    setError(null);
    setLoading(true);

    const u = customUser || username;
    const p = customPass || password;

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: u, password: p }),
      });

      if (!res.ok) {
        throw new Error("Invalid username or password");
      }

      const data = await res.json();
      localStorage.setItem("saathi_token", data.access_token);
      localStorage.setItem("saathi_user", JSON.stringify(data.user));

      // Redirect by role
      const role = data.user.role;
      if (role === "coordinator") {
        window.location.href = "/coordinator/dashboard";
      } else if (role === "family") {
        window.location.href = "/family/dashboard";
      } else if (role === "senior") {
        window.location.href = "/senior/easy";
      } else if (role === "ops_manager") {
        window.location.href = "/operations/dashboard";
      } else {
        window.location.href = "/coordinator/dashboard";
      }
    } catch (err: any) {
      setError(err.message || "Failed to authenticate with backend server.");
      setLoading(false);
    }
  };

  const handleQuickSelect = (acc: typeof QUICK_ACCOUNTS[0]) => {
    setUsername(acc.username);
    setPassword(acc.password);
    handleLogin(null as any, acc.username, acc.password);
  };

  return (
    <div className="min-h-screen bg-[#F8FAF7] flex flex-col justify-between">
      <Navbar />

      <main className="max-w-md mx-auto px-4 py-16 w-full flex-1 flex flex-col justify-center">
        <div className="bg-white p-8 rounded-3xl border border-slate-200/90 shadow-lg space-y-6">
          
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="inline-flex p-3 bg-[#EAF5EF] text-[#173F35] rounded-2xl mb-1 shadow-2xs">
              <Shield className="w-8 h-8 text-[#278C78]" />
            </div>
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Sign in to Sahara AI
            </h2>
            <p className="text-xs text-slate-500 max-w-xs mx-auto">
              Secure geriatric telemetry, real-time voice triage &amp; longitudinal care coordination.
            </p>
          </div>

          {error && (
            <div className="bg-rose-50 text-rose-700 text-xs p-3 rounded-xl border border-rose-200">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Username</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. coordinator1"
                  className="w-full text-xs pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full text-xs pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#173F35] hover:bg-[#278C78] text-white text-xs font-bold py-3 rounded-xl transition-all shadow-md active:scale-95 flex items-center justify-center gap-2"
            >
              {loading ? "Signing in..." : "Sign In to Platform"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Clean 1-Tap Persona Switcher */}
          <div className="pt-4 border-t border-slate-100 space-y-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block text-center">
              Quick Role Selection
            </span>
            <div className="grid grid-cols-2 gap-2">
              {QUICK_ACCOUNTS.map((acc) => (
                <button
                  key={acc.role}
                  type="button"
                  onClick={() => handleQuickSelect(acc)}
                  className={`p-2.5 rounded-xl border text-left transition hover:scale-[1.02] shadow-2xs ${acc.badgeColor}`}
                >
                  <div className="font-bold text-xs">{acc.title}</div>
                  <div className="text-[10px] opacity-75">{acc.name}</div>
                </button>
              ))}
            </div>
          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}
