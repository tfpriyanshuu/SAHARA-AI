"use client";

import React from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  Brain,
  Activity,
  Shield,
  Clock,
  ArrowRight,
  TrendingDown,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  UserCheck
} from "lucide-react";

export default function HowItWorksPage() {
  return (
    <div className="min-h-screen bg-[#F8FAF7] flex flex-col text-slate-800">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        {/* Hero Section */}
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          <span className="px-3 py-1 bg-[#EAF5EF] text-[#173F35] text-xs font-extrabold rounded-full border border-emerald-200 uppercase tracking-wider">
            Architecture &amp; Methodology
          </span>
          <h1 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight">
            How SaathiCare AI Detects Decline Before Crisis
          </h1>
          <p className="text-lg text-slate-600 leading-relaxed">
            Traditional telehealth relies on rigid population thresholds that flag problems only when seniors are already in acute distress. SaathiCare AI models each senior&apos;s personal baseline to detect multi-signal trajectory drift 5 to 14 days in advance.
          </p>
        </div>

        {/* Section 1: The Three Core Questions */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-8 shadow-sm space-y-6">
          <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
            <UserCheck className="w-7 h-7 text-[#278C78]" />
            The 3 Fundamental Questions Every Morning
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-5 rounded-2xl bg-[#F8FAF7] border border-slate-200">
              <span className="w-8 h-8 rounded-xl bg-[#173F35] text-white flex items-center justify-center font-bold text-sm mb-3">
                1
              </span>
              <h3 className="font-extrabold text-slate-900 text-lg mb-1">WHO needs attention?</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Ranked triage list strictly capped at N=10 highest-risk seniors per coordinator shift to eliminate alert fatigue and focus care where it counts.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-[#F8FAF7] border border-slate-200">
              <span className="w-8 h-8 rounded-xl bg-[#278C78] text-white flex items-center justify-center font-bold text-sm mb-3">
                2
              </span>
              <h3 className="font-extrabold text-slate-900 text-lg mb-1">WHY is risk increasing?</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                SHAP-derived top-3 contributing signals showing exact deviations from the senior&apos;s own baseline (e.g. SpO2 96% &rarr; 91% over 4 days, 2 missed doses).
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-[#F8FAF7] border border-slate-200">
              <span className="w-8 h-8 rounded-xl bg-emerald-700 text-white flex items-center justify-center font-bold text-sm mb-3">
                3
              </span>
              <h3 className="font-extrabold text-slate-900 text-lg mb-1">WHAT should coordinator do?</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Structured 3-question telephone scripts and protocolized triage actions (medication reminder, phone check-in, family notification, doctor consultation).
              </p>
            </div>
          </div>
        </div>

        {/* Section 2: Personal Baseline Mathematics */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-8 shadow-sm space-y-6">
          <div className="space-y-2">
            <span className="text-xs font-bold text-[#278C78] uppercase tracking-wider">Statistical Rigor</span>
            <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
              <Activity className="w-7 h-7 text-[#278C78]" />
              Zero Population Cutoffs &bull; Lagged Rolling Baselines
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              Standard clinical alerts use population cutoffs like SpO2 &lt; 90% or BP &gt; 140. However, an 80-year-old with a normal SpO2 of 98% who drops to 92% is experiencing a massive physiological decline, yet population cutoffs never fire.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div className="p-6 rounded-2xl bg-emerald-50/50 border border-emerald-200 space-y-3">
              <h3 className="font-bold text-slate-900 text-base">Lagged Window [t-42, t-14]</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                To prevent <em>baseline contamination</em> (where ongoing gradual decline pollutes the baseline itself), our statistics window excludes the most recent 14 days and draws from historical days [t-42 to t-14].
              </p>
              <div className="p-3 bg-white rounded-xl border border-emerald-100 font-mono text-xs text-emerald-900">
                Baseline = Median(Signals[t-42 : t-14])
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-emerald-50/50 border border-emerald-200 space-y-3">
              <h3 className="font-bold text-slate-900 text-base">Robust Median Absolute Deviation</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Standard deviation is heavily distorted by sensor outliers and transient spikes. We compute robust dispersion using Median Absolute Deviation scaled to standard Gaussian units:
              </p>
              <div className="p-3 bg-white rounded-xl border border-emerald-100 font-mono text-xs text-emerald-900">
                &sigma;_robust = 1.4826 &times; Median(|x_i - Median(x)|)
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Negation-Aware Multilingual NLP */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-8 shadow-sm space-y-6">
          <div className="space-y-2">
            <span className="text-xs font-bold text-[#278C78] uppercase tracking-wider">Natural Language Processing</span>
            <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
              <Sparkles className="w-7 h-7 text-[#278C78]" />
              Code-Mixed Hindi-English Negation Extraction
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              Real-world call notes and senior recordings in India feature code-mixed Hinglish and colloquial Hindi. A naive keyword search for &ldquo;dard&rdquo; (pain) or &ldquo;chakkar&rdquo; (dizziness) generates constant false alarms when the senior actually said &ldquo;dard nahi hai&rdquo; (no pain).
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
              <span className="font-bold text-slate-800 text-sm block">10 Clinical Cues</span>
              <p className="text-slate-600">
                Breathing difficulty, fall, low appetite, missed medication, pain, confusion, sleep deterioration, loneliness, mood shifts, reduced activity.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
              <span className="font-bold text-slate-800 text-sm block">&plusmn;3 Token Negation Window</span>
              <p className="text-slate-600">
                Detects Hindi, English, and Hinglish negations (&ldquo;nahi&rdquo;, &ldquo;nahin&rdquo;, &ldquo;bilkul nahi&rdquo;, &ldquo;no&rdquo;, &ldquo;denied&rdquo;) within adjacent tokens.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
              <span className="font-bold text-slate-800 text-sm block">Non-Diagnostic Safety</span>
              <p className="text-slate-600">
                Zero diagnostic inference. Free text is parsed strictly into behavioral indicator frequencies for human coordinator review.
              </p>
            </div>
          </div>
        </div>

        {/* Call to action */}
        <div className="p-8 rounded-3xl bg-gradient-to-r from-[#173F35] to-[#278C78] text-white flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-md">
          <div>
            <h3 className="text-2xl font-bold">Ready to explore the live system?</h3>
            <p className="text-sm text-emerald-100 mt-1">
              Test all 4 roles in the interactive prototype with 200 longitudinal synthetic seniors.
            </p>
          </div>
          <Link
            href="/login"
            className="px-6 py-3.5 bg-white text-[#173F35] font-extrabold text-sm rounded-2xl hover:bg-emerald-50 transition shadow shrink-0"
          >
            Launch 1-Click Demo &rarr;
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
}

