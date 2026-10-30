import React from "react";
import Link from "next/link";
import { Shield } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-[#173F35] text-emerald-100 border-t border-[#278C78]/20 pt-12 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          
          {/* Brand info */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-[#278C78] flex items-center justify-center text-white">
                <Shield className="w-4 h-4" />
              </div>
              <span className="font-bold text-lg text-white">Sahara AI (सहारा AI)</span>
            </div>
            <p className="text-xs text-emerald-300 leading-relaxed mb-4">
              AI-powered early warning decision-support platform for seniors living at home. Noticing small trajectory shifts before they become emergencies.
            </p>
            <span className="text-[11px] bg-emerald-900/80 text-emerald-200 px-2 py-1 rounded border border-emerald-700/50 block w-fit">
              Human-led care • Explainable AI
            </span>
          </div>

          {/* Product links */}
          <div>
            <h4 className="text-white font-semibold text-xs tracking-wider uppercase mb-3">Product</h4>
            <ul className="space-y-2 text-xs">
              <li><Link href="/coordinator/dashboard" className="hover:text-white">Care Coordinator Queue</Link></li>
              <li><Link href="/family/dashboard" className="hover:text-white">Family Wellbeing Hub</Link></li>
              <li><Link href="/senior/easy" className="hover:text-white">Senior Easy Voice App</Link></li>
              <li><Link href="/operations/dashboard" className="hover:text-white">Operations Management</Link></li>
            </ul>
          </div>

          {/* Technology & Safety */}
          <div>
            <h4 className="text-white font-semibold text-xs tracking-wider uppercase mb-3">Platform & Privacy</h4>
            <ul className="space-y-2 text-xs">
              <li><Link href="/how-it-works" className="hover:text-white">How Anomaly Scoring Works</Link></li>
              <li><Link href="/privacy" className="hover:text-white">Privacy & Consent Gating</Link></li>
              <li><span className="text-emerald-400">Zero Population Cutoffs</span></li>
              <li><span className="text-emerald-400">Non-Diagnostic Safety Protocol</span></li>
            </ul>
          </div>

          {/* Safety Disclaimer */}
          <div>
            <h4 className="text-white font-semibold text-xs tracking-wider uppercase mb-3">Important Notice</h4>
            <p className="text-[11px] text-emerald-300 leading-relaxed bg-emerald-950/60 p-3 rounded-lg border border-emerald-800/40">
              <strong>Decision-Support Prototype:</strong> Sahara AI flags behavioral and vital trajectory deviations from personal baselines. It does not provide medical diagnoses or replace licensed clinical judgment.
            </p>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-emerald-800/60 flex flex-col sm:flex-row justify-between items-center text-xs text-emerald-300 gap-2">
          <p>© 2026 Sahara AI (सहारा AI). All rights reserved.</p>
          <div className="flex gap-4">
            <Link href="/privacy" className="hover:text-white">Privacy</Link>
            <Link href="/how-it-works" className="hover:text-white">Architecture</Link>
            <Link href="/login" className="hover:text-white">Demo Login</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
