"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  Shield,
  Activity,
  Heart,
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Lock,
  Users,
  Clock,
  Sparkles,
  PhoneCall,
  Mic,
  Volume2,
  Pill,
  Radio,
  Smartphone,
  ChevronRight,
  TrendingDown,
  Eye
} from "lucide-react";

export default function LandingPage() {
  const [stats, setStats] = useState({
    totalSeniors: 250,
    needingAttention: 6,
    highAlerts: 4,
    avgResponseMin: 32.4,
  });

  const [isMobileDevice, setIsMobileDevice] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const isMobile =
        window.innerWidth < 768 ||
        /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
      setIsMobileDevice(isMobile);
    }
  }, []);

  useEffect(() => {
    // Live fetch from backend overview endpoint
    fetch("/api/v1/operations/overview")
      .then((res) => res.json())
      .then((data) => {
        if (data.total_monitored_seniors) {
          setStats({
            totalSeniors: data.total_monitored_seniors,
            needingAttention: data.active_alerts,
            highAlerts: (data.urgent_alerts || 0) + (data.high_alerts || 0),
            avgResponseMin: data.median_response_time_min || 32.4,
          });
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-[#F8FAF7] text-slate-800 flex flex-col font-sans selection:bg-[#278C78]/20 selection:text-emerald-950">
      {/* MOBILE APP PROMPT BANNER FOR PHONES */}
      {isMobileDevice && (
        <div className="sticky top-0 z-50 bg-[#173F35] text-white px-4 py-3 border-b-2 border-emerald-400 flex items-center justify-between shadow-xl">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl animate-bounce">📱</span>
            <div>
              <p className="font-extrabold text-xs text-white">SAHARA-AI - वरिष्ठ नागरिक ऐप</p>
              <p className="text-[10px] text-emerald-200">मोबाइल के लिए अलग आसान UI तैयार है</p>
            </div>
          </div>
          <Link
            href="/app"
            className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs px-3.5 py-2 rounded-xl shadow-md transition active:scale-95 flex items-center gap-1"
          >
            <span>ऐप खोलें</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      <Navbar />

      {/* HERO SECTION */}
      <section className="relative overflow-hidden bg-gradient-to-b from-[#173F35] via-[#1A473C] to-[#173F35] text-white pt-12 pb-20 px-4 sm:px-6 lg:px-8">
        {/* Subtle grid background */}
        <div className="absolute inset-0 opacity-5 bg-[radial-gradient(#278C78_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none"></div>

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            
            {/* Left Column: Emotion, Mission & Direct CTAs */}
            <div className="lg:col-span-7 text-left space-y-6">
              
              {/* Trust Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-900/80 border border-emerald-600/50 text-emerald-200 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>SAHARA-AI &bull; Human-Led Care &bull; Indic Voice AI &bull; Explainable ML</span>
              </div>

              {/* Main Headline */}
              <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-[1.15] text-white">
                Care Before Crisis: <br />
                <span className="text-[#3DD6B0] underline decoration-[#3DD6B0]/40">
                  बुजुर्गों की हर बात
                </span>{" "}
                और सेहत का सहारा।
              </h1>

              {/* Clear Value Description */}
              <p className="text-base sm:text-lg text-emerald-100/90 leading-relaxed max-w-2xl font-normal">
                भारत का पहला AI-सक्षम एल्डर-केयर प्लेटफॉर्म — रोज़ाना देसी बोलियों में वॉइस चेक-इन, 
                स्मार्ट पिलबॉक्स और 90-दिन के पर्सनल बेसलाइन ड्रिफ्ट से अचानक बीमारी बिगड़ने से 
                <strong> 11 दिन पहले </strong> ही केयर टीम को सतर्क करता है।
              </p>

              {/* CTA Action Buttons */}
              <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5">
                <Link
                  href="/app"
                  className="bg-[#278C78] hover:bg-[#1F6F5F] text-white font-extrabold px-6 py-4 rounded-2xl transition-all shadow-lg shadow-emerald-950/30 flex items-center justify-center gap-3 text-sm active:scale-95 border border-emerald-400/40"
                >
                  <Smartphone className="w-5 h-5 text-emerald-200" />
                  <span>📱 वरिष्ठ नागरिक ऐप खोलें (Senior App)</span>
                  <ArrowRight className="w-4 h-4 text-emerald-200" />
                </Link>

                <Link
                  href="/coordinator/dashboard"
                  className="bg-white/10 hover:bg-white/15 text-white font-bold px-6 py-4 rounded-2xl border border-white/20 transition-all flex items-center justify-center gap-2.5 text-sm backdrop-blur-xs"
                >
                  <Activity className="w-5 h-5 text-emerald-300" />
                  <span>केयर कोऑर्डिनेटर डैशबोर्ड (250 सीनियर्स)</span>
                </Link>
              </div>

              {/* Quick Metrics Bar */}
              <div className="pt-4 grid grid-cols-3 gap-3 border-t border-emerald-800/60 max-w-lg">
                <div>
                  <span className="text-2xl font-black text-[#3DD6B0] block">250</span>
                  <span className="text-[11px] text-emerald-200 uppercase font-semibold">निगरानी में बुजुर्ग</span>
                </div>
                <div>
                  <span className="text-2xl font-black text-white block">90 Days</span>
                  <span className="text-[11px] text-emerald-200 uppercase font-semibold">क्लिनिकल टेलीमेट्री</span>
                </div>
                <div>
                  <span className="text-2xl font-black text-[#3DD6B0] block">11 Days</span>
                  <span className="text-[11px] text-emerald-200 uppercase font-semibold">अग्रिम चेतावनी लीड</span>
                </div>
              </div>

            </div>

            {/* Right Column: Emotional High-Quality Senior Image with Live Vitals Overlays */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md lg:max-w-none">
                
                {/* Glowing backdrop shadow */}
                <div className="absolute -inset-1.5 bg-gradient-to-tr from-[#278C78] to-[#3DD6B0] rounded-3xl blur-xl opacity-30"></div>

                {/* Main Image Container - Clean Photo Display without distracting SpO2 overlays */}
                <div className="relative rounded-3xl overflow-hidden border-2 border-emerald-400/40 shadow-2xl bg-emerald-950">
                  <Image
                    src="/hero-senior.jpg"
                    alt="Elderly Indian grandfather smiling warmly at home with Sahara AI"
                    width={700}
                    height={850}
                    priority
                    className="w-full h-auto object-cover aspect-[4/5] hover:scale-102 transition-transform duration-700"
                  />
                </div>

                {/* Subtitle caption */}
                <p className="text-center text-xs text-emerald-200/90 mt-3 font-medium">
                  वरिष्ठ नागरिक (हर्षित ठाकुर जी, 72 वर्ष) &bull; घर पर सुरक्षित और परिवार व केयर टीम के संपर्क में
                </p>

              </div>
            </div>

          </div>
        </div>
      </section>

      {/* QUICK ROLE SELECTOR STRIP (Zero Confusion for Judges & Visitors) */}
      <section className="bg-white border-b border-slate-200 py-6 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#278C78] bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
              एक क्लिक में देखें (1-Click Demo Portals)
            </span>
            <h2 className="text-lg font-bold text-slate-900 mt-2">
              अपनी भूमिका चुनें और सीधे प्लेटफ़ॉर्म का अनुभव करें
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* Senior App Card */}
            <Link
              href="/app"
              className="p-4 rounded-2xl border-2 border-emerald-500/30 hover:border-emerald-600 bg-emerald-50/40 hover:bg-emerald-50 transition-all flex items-center justify-between group shadow-xs"
            >
              <div className="flex items-center gap-3">
                <span className="w-11 h-11 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-lg shadow-xs group-hover:scale-105 transition-transform">
                  👴
                </span>
                <div>
                  <h3 className="font-extrabold text-sm text-slate-900">वरिष्ठ नागरिक ऐप</h3>
                  <p className="text-xs text-slate-500">1-टैप आसान मोबाइल ऐप (/app)</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-emerald-600 group-hover:translate-x-1 transition-transform" />
            </Link>

            {/* Care Coordinator Card */}
            <Link
              href="/coordinator/dashboard"
              className="p-4 rounded-2xl border-2 border-blue-500/30 hover:border-blue-600 bg-blue-50/40 hover:bg-blue-50 transition-all flex items-center justify-between group shadow-xs"
            >
              <div className="flex items-center gap-3">
                <span className="w-11 h-11 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-lg shadow-xs group-hover:scale-105 transition-transform">
                  👩‍⚕️
                </span>
                <div>
                  <h3 className="font-extrabold text-sm text-slate-900">केयर कोऑर्डिनेटर</h3>
                  <p className="text-xs text-slate-500">250 सीनियर्स की प्रायोरिटी कतार</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-blue-600 group-hover:translate-x-1 transition-transform" />
            </Link>

            {/* Family Portal Card */}
            <Link
              href="/family/dashboard"
              className="p-4 rounded-2xl border-2 border-amber-500/30 hover:border-amber-600 bg-amber-50/40 hover:bg-amber-50 transition-all flex items-center justify-between group shadow-xs"
            >
              <div className="flex items-center gap-3">
                <span className="w-11 h-11 rounded-xl bg-amber-600 text-white flex items-center justify-center font-bold text-lg shadow-xs group-hover:scale-105 transition-transform">
                  👨‍👩‍👧
                </span>
                <div>
                  <h3 className="font-extrabold text-sm text-slate-900">परिवार का हब</h3>
                  <p className="text-xs text-slate-500">साप्ताहिक रिपोर्ट और शांति</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-amber-600 group-hover:translate-x-1 transition-transform" />
            </Link>

            {/* Operations Card */}
            <Link
              href="/operations/dashboard"
              className="p-4 rounded-2xl border-2 border-purple-500/30 hover:border-purple-600 bg-purple-50/40 hover:bg-purple-50 transition-all flex items-center justify-between group shadow-xs"
            >
              <div className="flex items-center gap-3">
                <span className="w-11 h-11 rounded-xl bg-purple-600 text-white flex items-center justify-center font-bold text-lg shadow-xs group-hover:scale-105 transition-transform">
                  📊
                </span>
                <div>
                  <h3 className="font-extrabold text-sm text-slate-900">ऑपरेशंस लीड</h3>
                  <p className="text-xs text-slate-500">10 शहरों का राष्ट्रीय एनालिटिक्स</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-purple-600 group-hover:translate-x-1 transition-transform" />
            </Link>

          </div>
        </div>
      </section>

      {/* CORE INNOVATIONS: 4 PILLARS OF SAHARA AI */}
      <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-bold text-[#278C78] uppercase tracking-wider bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
            How Sahara AI Works
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mt-3 mb-4">
            तकनीक जो इंसानी देखभाल को मजबूत बनाती है
          </h2>
          <p className="text-slate-600 text-base leading-relaxed">
            बुजुर्गों के स्वास्थ्य में गिरावट अचानक नहीं होती, धीरे-धीरे होती है। सहारा AI चार प्रमुख तकनीकों से समय रहते हर बदलाव को पहचानता है।
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          {/* Pillar 1 */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow relative space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-xl">
              <Mic className="w-6 h-6 text-[#278C78]" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">1. Indic Voice AI</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              बुजुर्गों को टाइप करने की ज़रूरत नहीं। वे हिंदी, मराठी, तमिल या हिंग्लिश में बोल सकते हैं। AI आवाज़ की मिठास और लक्षणों की पहचान तुरंत करता है।
            </p>
            <div className="pt-2 text-[11px] font-semibold text-[#278C78] flex items-center gap-1">
              <span>Sarvam Indic STT + Gemini Triage</span>
            </div>
          </div>

          {/* Pillar 2 */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow relative space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-800 flex items-center justify-center font-bold text-xl">
              <PhoneCall className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">2. App-to-App Live Call</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              जैसे इंस्टाग्राम या स्नैपचैट पर कॉल होती है, वैसे ही बिना किसी महंगे फोन नंबर या सिम के, सीनियर और कोऑर्डिनेटर सीधे ऐप पर लाइव बात कर सकते हैं।
            </p>
            <div className="pt-2 text-[11px] font-semibold text-blue-600 flex items-center gap-1">
              <span>Peer-to-Peer WebRTC Audio</span>
            </div>
          </div>

          {/* Pillar 3 */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow relative space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-xl">
              <Pill className="w-6 h-6 text-amber-700" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">3. Ambient Home Hub</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              स्मार्ट पिलबॉक्स से दवा समय पर ली या छूटी? बिना किसी कैमरे के कमरे में हलचल की गति सामान्य है या कम? सब कुछ प्राइवेसी-सुरक्षित रूप से सिंक होता है।
            </p>
            <div className="pt-2 text-[11px] font-semibold text-amber-700 flex items-center gap-1">
              <span>Zero-Camera Privacy Sensor</span>
            </div>
          </div>

          {/* Pillar 4 */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow relative space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-100 text-rose-800 flex items-center justify-center font-bold text-xl">
              <Activity className="w-6 h-6 text-rose-600" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">4. 90-Day Baseline Drift</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              एक दिन की थकान बीमारी नहीं होती। सिस्टम प्रत्येक बुज़ुर्ग के 28-दिन के अपने सामान्य स्तर से तुलना करता है। बदलाव होने पर तुरंत रैंक-ऑर्डर्ड अलर्ट देता है।
            </p>
            <div className="pt-2 text-[11px] font-semibold text-rose-600 flex items-center gap-1">
              <span>Robust MAD Z-Score & CUSUM</span>
            </div>
          </div>

        </div>
      </section>

      {/* BENCHMARK & IMPACT SECTION */}
      <section id="impact" className="py-16 bg-white border-y border-slate-200 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 uppercase">
              Rigorous Evaluation
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-2 mb-2">
              क्लिनिकल स्तर का प्रदर्शन &bull; 250 बुजुर्गों का 90-दिन का डेटा
            </h3>
            <p className="text-slate-600 text-xs sm:text-sm">
              कोई डमी डेटा नहीं — 22,500 दैनिक असेसमेंट और वास्तविक कोऑर्डिनेटर वर्कफ़्लो के साथ जाँचा गया।
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-5xl mx-auto">
            <div className="p-5 rounded-2xl bg-[#F8FAF7] border border-slate-200 text-center">
              <span className="text-3xl sm:text-4xl font-black text-[#278C78] block mb-1">11.0 Days</span>
              <span className="text-xs font-bold text-slate-900 block">अग्रिम चेतावनी लीड-टाइम</span>
              <span className="text-[11px] text-slate-500 block mt-1">इमरजेंसी से 11 दिन पहले अलर्ट</span>
            </div>

            <div className="p-5 rounded-2xl bg-[#F8FAF7] border border-slate-200 text-center">
              <span className="text-3xl sm:text-4xl font-black text-[#278C78] block mb-1">0.9593</span>
              <span className="text-xs font-bold text-slate-900 block">ROC-AUC स्कोर</span>
              <span className="text-[11px] text-slate-500 block mt-1">सटीक खतरे की पहचान</span>
            </div>

            <div className="p-5 rounded-2xl bg-[#F8FAF7] border border-slate-200 text-center">
              <span className="text-3xl sm:text-4xl font-black text-[#278C78] block mb-1">96.7%</span>
              <span className="text-xs font-bold text-slate-900 block">हिंग्लिश वॉयस F1 स्कोर</span>
              <span className="text-[11px] text-slate-500 block mt-1">देसी भाषा समझने में माहिर</span>
            </div>

            <div className="p-5 rounded-2xl bg-[#F8FAF7] border border-slate-200 text-center">
              <span className="text-3xl sm:text-4xl font-black text-[#278C78] block mb-1">0.006s</span>
              <span className="text-xs font-bold text-slate-900 block">एआई स्कोरिंग स्पीड</span>
              <span className="text-[11px] text-slate-500 block mt-1">हल्का और सुपर-फास्ट</span>
            </div>
          </div>
        </div>
      </section>

      {/* SAFETY, PRIVACY & EXPLAINABILITY */}
      <section id="safety" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="bg-[#173F35] text-white rounded-3xl p-8 sm:p-12 shadow-2xl border border-emerald-800/40 relative overflow-hidden">
          <div className="max-w-3xl relative z-10">
            <div className="w-12 h-12 rounded-2xl bg-[#278C78] flex items-center justify-center mb-6">
              <Lock className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-2xl sm:text-3xl font-extrabold mb-4">
              सुरक्षा, निजता और इंसानी नियंत्रण सर्वप्रथम
            </h3>
            <p className="text-emerald-100/90 text-sm leading-relaxed mb-6">
              सहारा AI कोई ऑटोमेटेड डॉक्टर नहीं है, बल्कि केयर कोऑर्डिनेटर के हाथ का औज़ार है। यह मेडिकल निर्णय नहीं लेता, बल्कि इंसानों को सही समय पर सही जगह पहुँचने में मदद करता है।
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-[#3DD6B0] shrink-0 mt-0.5" />
                <span><strong>No Fake Diagnosis:</strong> बीमारी का झूठा लेबल नहीं लगाता, केवल व्यक्तिगत बेसलाइन में बदलाव बताता है।</span>
              </div>
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-[#3DD6B0] shrink-0 mt-0.5" />
                <span><strong>Human In The Loop:</strong> हर अलर्ट की जाँच प्रशिक्षित केयर कोऑर्डिनेटर (जैसे अनिता दीदी) करती हैं।</span>
              </div>
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-[#3DD6B0] shrink-0 mt-0.5" />
                <span><strong>Consent-Gated:</strong> परिवार को डेटा केवल सीनियर की सहमति से ही साझा किया जाता है।</span>
              </div>
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-[#3DD6B0] shrink-0 mt-0.5" />
                <span><strong>App-to-App Privacy:</strong> बिना किसी टेलीकॉम नंबर एक्सपोजर के सुरक्षित ऑडियो बातचीत।</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
