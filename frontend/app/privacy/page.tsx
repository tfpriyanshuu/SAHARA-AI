"use client";

import React from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  ShieldCheck,
  Lock,
  EyeOff,
  FileText,
  UserCheck,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ArrowRight
} from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#F8FAF7] flex flex-col text-slate-800">
      <Navbar />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-10">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <span className="px-3 py-1 bg-[#EAF5EF] text-[#173F35] text-xs font-extrabold rounded-full border border-emerald-200 uppercase tracking-wider">
            Safety, Compliance &amp; Ethics
          </span>
          <h1 className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight">
            Privacy Charter &amp; Non-Diagnostic Guardrails
          </h1>
          <p className="text-base text-slate-600 leading-relaxed">
            SaathiCare AI is purpose-built to preserve senior dignity, protect sensitive personal telemetry, and strictly support—never replace—human clinical professionals.
          </p>
        </div>

        {/* 1. Non-Diagnostic Charter */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-8 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">1. Strict Non-Diagnostic Decision Support</h2>
              <span className="text-xs font-semibold text-rose-600 uppercase">Mandatory System Constraint</span>
            </div>
          </div>

          <p className="text-sm text-slate-600 leading-relaxed">
            SaathiCare AI is not a medical device and does not diagnose disease. All machine learning outputs represent statistical trajectory deviations from a senior&apos;s personal baseline, never clinical diagnoses.
          </p>

          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-xs space-y-2">
            <span className="font-bold text-slate-800 uppercase block">Automated Output Safety Filter</span>
            <p className="text-slate-600">
              Every system string (explanations, suggested questions, family summaries) passes through a multi-lingual blocklist that intercepts and replaces medical disease terms (e.g. pneumonia, COPD, heart attack, stroke, dementia) with neutral trajectory descriptors (&ldquo;respiratory variation&rdquo;, &ldquo;mobility drift&rdquo;).
            </p>
          </div>
        </div>

        {/* 2. Role-Based Access Isolation */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-8 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#EAF5EF] text-[#173F35] flex items-center justify-center">
              <Lock className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">2. Enforced Role-Based Access Isolation</h2>
              <span className="text-xs font-semibold text-[#278C78] uppercase">Zero Data Leaks Across Boundaries</span>
            </div>
          </div>

          <p className="text-sm text-slate-600 leading-relaxed">
            Access control is enforced at the database query layer, not merely in the frontend user interface:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <strong className="text-slate-900 block mb-1">Care Coordinators:</strong>
              <p className="text-slate-600">
                Authorized only to view seniors explicitly assigned to their triage queue. Unauthorized queries return HTTP 403 Forbidden.
              </p>
            </div>
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <strong className="text-slate-900 block mb-1">Operations Managers:</strong>
              <p className="text-slate-600">
                View national and city-wide performance metrics, alert velocity, and response SLAs. Confidential call transcripts and free-text notes are completely redacted.
              </p>
            </div>
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <strong className="text-slate-900 block mb-1">Family Members:</strong>
              <p className="text-slate-600">
                Access is strictly restricted to their verified elderly relative with consent-governed notifications.
              </p>
            </div>
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <strong className="text-slate-900 block mb-1">Senior Citizens:</strong>
              <p className="text-slate-600">
                Simplified, dignified personal portal with today&apos;s routine, medication check-offs, and coordinator contact.
              </p>
            </div>
          </div>
        </div>

        {/* 3. Consent & Audit Trail */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-8 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <UserCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">3. Consent Gating &amp; Immutable Audit Trail</h2>
              <span className="text-xs font-semibold text-indigo-600 uppercase">HIPAA / DPDP Act Compliant Architecture</span>
            </div>
          </div>

          <p className="text-sm text-slate-600 leading-relaxed">
            Every access to a senior record, vital observation ingestion, or alert resolution creates an immutable audit record logging the timestamp, operator identity, user role, and resource accessed.
          </p>

          <p className="text-sm text-slate-600 leading-relaxed">
            Family notifications are strictly gated by the <code className="text-emerald-800 bg-emerald-50 px-1.5 py-0.5 rounded font-mono text-xs">family_consent</code> toggle. When consent is paused, acute alerts are suppressed and only weekly non-alarming routine aggregates are shared.
          </p>
        </div>

        {/* Return Button */}
        <div className="text-center pt-4">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#173F35] text-white rounded-xl font-bold text-sm hover:bg-[#278C78] transition shadow"
          >
            Return to Homepage &rarr;
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
}

