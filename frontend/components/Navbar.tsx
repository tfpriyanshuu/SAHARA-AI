"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Shield, User, LogOut, Activity, Menu, X } from "lucide-react";

export default function Navbar() {
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("saathi_user");
    if (stored) {
      try {
        setCurrentUser(JSON.parse(stored));
      } catch (e) {}
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("saathi_token");
    localStorage.removeItem("saathi_user");
    setCurrentUser(null);
    window.location.href = "/";
  };

  return (
    <nav className="sticky top-0 z-50 bg-[#173F35]/95 backdrop-blur-md text-white border-b border-[#278C78]/30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Wordmark */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-[#278C78] flex items-center justify-center text-white shadow-xs">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="font-black text-xl tracking-wider text-white">
                SAHARA-AI
              </span>
              <span className="text-[10px] text-emerald-200 block -mt-0.5 font-medium">
                Care Before Crisis &bull; वरिष्ठ नागरिक स्वास्थ्य सहारा
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-emerald-100">
            <Link href="/#problem" className="hover:text-white transition-colors">The Challenge</Link>
            <Link href="/#how-it-works" className="hover:text-white transition-colors">How It Works</Link>
            <Link href="/#features" className="hover:text-white transition-colors">Features</Link>
            <Link href="/#impact" className="hover:text-white transition-colors">Our Impact</Link>
            <Link href="/#safety" className="hover:text-white transition-colors">Safety & Privacy</Link>
          </div>

          {/* Right Action / Auth Buttons */}
          <div className="hidden md:flex items-center gap-3">
            {currentUser ? (
              <div className="flex items-center gap-3">
                <Link
                  href={
                    currentUser.role === "coordinator" ? "/coordinator/dashboard" :
                    currentUser.role === "family" ? "/family/dashboard" :
                    currentUser.role === "ops_manager" ? "/operations/dashboard" : "/senior/dashboard"
                  }
                  className="bg-[#278C78] hover:bg-[#1F6F5F] text-white text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition-colors shadow-xs"
                >
                  <Activity className="w-3.5 h-3.5" />
                  Dashboard ({currentUser.role})
                </Link>
                <button
                  onClick={handleLogout}
                  className="text-emerald-200 hover:text-white text-xs p-2 rounded-lg hover:bg-white/10"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="text-white hover:text-emerald-200 text-xs font-semibold px-3 py-2 rounded-lg hover:bg-white/5 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/login"
                  className="bg-[#278C78] hover:bg-[#1F6F5F] text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors shadow-xs"
                >
                  Explore Demo
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="p-2 rounded-md text-emerald-200 hover:text-white hover:bg-white/10"
            >
              {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {menuOpen && (
        <div className="md:hidden bg-[#173F35] border-t border-[#278C78]/30 px-4 pt-2 pb-4 space-y-2 text-sm">
          <Link href="/#problem" onClick={() => setMenuOpen(false)} className="block py-1.5 text-emerald-100 hover:text-white">The Challenge</Link>
          <Link href="/#how-it-works" onClick={() => setMenuOpen(false)} className="block py-1.5 text-emerald-100 hover:text-white">How It Works</Link>
          <Link href="/#features" onClick={() => setMenuOpen(false)} className="block py-1.5 text-emerald-100 hover:text-white">Features</Link>
          <Link href="/#safety" onClick={() => setMenuOpen(false)} className="block py-1.5 text-emerald-100 hover:text-white">Safety & Privacy</Link>
          <div className="pt-2 border-t border-emerald-800">
            <Link href="/login" onClick={() => setMenuOpen(false)} className="block w-full text-center bg-[#278C78] py-2 rounded-lg text-white font-semibold">
              Explore Live Demo
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}

