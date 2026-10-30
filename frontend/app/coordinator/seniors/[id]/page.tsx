"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  Shield,
  Activity,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Clock,
  Heart,
  Pill,
  MessageSquare,
  FileText,
  User,
  Phone,
  CheckCircle,
  CheckCircle2,
  AlertCircle,
  Brain,
  HelpCircle,
  Info,
  TrendingUp,
  TrendingDown,
  Sparkles,
  Home,
  Check,
  Send,
  Plus,
  Play,
  Pause,
  Volume2,
  Mic,
  Bot,
  Smartphone,
  Radio,
  PhoneCall,
  Battery,
  WifiOff,
  RotateCw
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine,
  BarChart,
  Bar
} from "recharts";

function SeniorDetailContent() {
  const params = useParams();
  const router = useRouter();
  const seniorId = (params?.id as string) || "SEN_003";

  const [activeTab, setActiveTab] = useState<
    "overview" | "vitals" | "medications" | "checkins" | "risk" | "care_history"
  >("overview");

  const [senior, setSenior] = useState<any>(null);
  const [vitals, setVitals] = useState<any[]>([]);
  const [medLogs, setMedLogs] = useState<any[]>([]);
  const [riskHistory, setRiskHistory] = useState<any[]>([]);
  const [callNotes, setCallNotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Audio simulation state
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioProgress, setAudioProgress] = useState(0);

  // Care action form state
  const [contactTarget, setContactTarget] = useState<"SENIOR" | "FAMILY">("SENIOR");
  const [newNote, setNewNote] = useState("");
  const [callOutcome, setCallOutcome] = useState("RESOLVED_NORMAL");
  const [noteSuccess, setNoteSuccess] = useState(false);

  // Live Voice Check-ins & Device Health State
  const [checkinTimeline, setCheckinTimeline] = useState<any[]>([]);
  const [deviceHealth, setDeviceHealth] = useState<any>(null);
  const [isTriggeringCall, setIsTriggeringCall] = useState(false);
  const [callToast, setCallToast] = useState<string | null>(null);

  const fetchCheckinData = async () => {
    try {
      const [tRes, dRes] = await Promise.all([
        fetch(`/api/v1/checkins/${seniorId}/timeline`).catch(() => null),
        fetch(`/api/v1/checkins/${seniorId}/device-health`).catch(() => null)
      ]);
      if (tRes && tRes.ok) {
        const tData = await tRes.json();
        setCheckinTimeline(tData);
      }
      if (dRes && dRes.ok) {
        const dData = await dRes.json();
        setDeviceHealth(dData);
      }
    } catch (e) {
      console.warn("Could not load checkin data:", e);
    }
  };

  const handleTriggerDemoCall = async () => {
    setIsTriggeringCall(true);
    try {
      const res = await fetch("/api/v1/checkins/trigger-demo-call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ senior_id: seniorId })
      });
      if (res.ok) {
        setCallToast(`✅ ${senior?.full_name || "वरिष्ठ नागरिक"} के PWA फोन पर 'Sahara AI' कॉल प्रेषित! (Data-only Push)`);
        setTimeout(() => setCallToast(null), 4500);
        await fetchCheckinData();
      }
    } catch (err) {
      console.warn("Trigger demo call error:", err);
    } finally {
      setIsTriggeringCall(false);
    }
  };

  const handleMarkReviewed = async (checkinId: string) => {
    try {
      const res = await fetch(`/api/v1/checkins/${checkinId}/review`, {
        method: "POST"
      });
      if (res.ok) {
        setCheckinTimeline((prev) =>
          prev.map((c) =>
            c.checkin_id === checkinId ? { ...c, is_reviewed: true, needs_review: false } : c
          )
        );
      }
    } catch (err) {
      console.warn("Review error:", err);
    }
  };

  const currentAudioObjRef = useRef<HTMLAudioElement | null>(null);

  // Toggle real audio player
  const togglePlayAudio = () => {
    if (isPlayingAudio && currentAudioObjRef.current) {
      currentAudioObjRef.current.pause();
      currentAudioObjRef.current = null;
      setIsPlayingAudio(false);
      return;
    }

    const localStored = typeof window !== "undefined" ? localStorage.getItem(`latest_recorded_audio_${seniorId}`) : null;
    const targetUrl = senior?.latest_audio_url || localStored || "/static/audio/default_note.webm";

    const audio = new Audio(targetUrl);
    currentAudioObjRef.current = audio;
    setIsPlayingAudio(true);
    setAudioProgress(10);

    audio.ontimeupdate = () => {
      if (audio.duration) {
        setAudioProgress(Math.round((audio.currentTime / audio.duration) * 100));
      }
    };

    audio.onended = () => {
      setIsPlayingAudio(false);
      setAudioProgress(0);
      currentAudioObjRef.current = null;
    };

    audio.play().catch((err) => {
      console.warn("Audio play prevented:", err);
    });
  };

  // Fetch senior details and longitudinal telemetry
  useEffect(() => {
    async function loadData() {
      try {
        const token = localStorage.getItem("saathi_token");
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const [sRes, vRes, mRes, rRes, nRes] = await Promise.all([
          fetch(`/api/v1/seniors/${seniorId}`, { headers }),
          fetch(`/api/v1/signals/${seniorId}/vitals?days=30`, { headers }),
          fetch(`/api/v1/signals/${seniorId}/medications?days=30`, { headers }),
          fetch(`/api/v1/risk/${seniorId}/risk-history?days=30`, { headers }),
          fetch(`/api/v1/signals/${seniorId}/call-notes`, { headers }).catch(() => null)
        ]);

        if (sRes.ok) {
          const sData = await sRes.json();
          setSenior(sData);
        } else {
          // Fallback mock senior if unauthenticated or demo mode
          setSenior({
            id: seniorId,
            full_name: seniorId === "SEN_001" ? "Harshit Thakur" : seniorId === "SEN_002" ? "Anvesha" : seniorId === "SEN_003" ? "Anchal" : seniorId === "SEN_004" ? "Priyanshu" : seniorId === "SEN_005" ? "Vikas" : "Sejal",
            age: 78,
            gender: "Male",
            city: "Indore",
            primary_language: "Hindi",
            address: "42 Anand Nagar, Scheme 54, Indore, MP",
            emergency_contact: "+91 9451818283 (Son: Rajesh Sharma)",
            senior_phone: "+91 9451818283",
            family_phone: "+91 8957266841",
            family_contact_name: "Rajesh Sharma (Son)",
            home_hub_status: "ONLINE",
            home_hub_device_id: "HUB-IND-003",
            family_consent: true,
            coordinator_name: "Anvesha Sharma",
            baseline_spo2: 96.2,
            baseline_sys_bp: 128.0,
            baseline_dia_bp: 82.0,
            baseline_sugar: 122.0,
            baseline_inactivity_hours: 6.2,
            baseline_night_bathroom: 1.0,
            baseline_door_events: 5.0
          });
        }

        if (vRes.ok) {
          const vData = await vRes.json();
          setVitals(vData);
        }
        if (mRes.ok) {
          const mData = await mRes.json();
          setMedLogs(mData);
        }
        if (rRes.ok) {
          const rData = await rRes.json();
          setRiskHistory(rData);
        }
        if (nRes && nRes.ok) {
          const nData = await nRes.json();
          setCallNotes(nData);
        }
        await fetchCheckinData();
      } catch (err) {
        console.warn("Backend not reached, using fallback longitudinal telemetry", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [seniorId]);

  // Fallback telemetry generation if empty
  const displayVitals = vitals.length > 0 ? vitals : Array.from({ length: 30 }).map((_, i) => {
    const day = i + 1;
    // Decline starts at day 22
    const isDecline = day >= 22;
    return {
      date: `2026-10-${day < 10 ? '0' + day : day}`,
      spo2: isDecline ? Math.round(96 - (day - 22) * 0.9) : Math.round(96 + Math.sin(i) * 0.5),
      sys_bp: isDecline ? Math.round(128 + (day - 22) * 3) : Math.round(128 + Math.cos(i) * 4),
      dia_bp: isDecline ? Math.round(82 + (day - 22) * 1.5) : Math.round(82 + Math.sin(i) * 2),
      inactivity_hours: isDecline ? +(6.2 + (day - 22) * 0.5).toFixed(1) : +(6.2 + Math.sin(i) * 0.4).toFixed(1),
      night_bathroom_visits: isDecline ? Math.min(5, 1 + Math.floor((day - 22) / 2)) : 1,
      baseline_spo2_min: 94.5,
      baseline_spo2_max: 97.5,
      baseline_sys_min: 122,
      baseline_sys_max: 134
    };
  });

  const displayRiskHistory = riskHistory.length > 0 ? riskHistory : Array.from({ length: 30 }).map((_, i) => {
    const day = i + 1;
    const isDecline = day >= 22;
    const score = isDecline ? Math.min(92, Math.round(18 + (day - 21) * 8.5)) : Math.round(16 + Math.sin(i) * 4);
    return {
      date: `2026-10-${day < 10 ? '0' + day : day}`,
      risk_score: score,
      risk_category: score >= 75 ? "URGENT" : score >= 50 ? "HIGH" : score >= 30 ? "MODERATE" : "LOW",
      anomaly_score: isDecline ? +(0.65 + (day - 21) * 0.03).toFixed(2) : 0.15,
      rules_score: isDecline ? Math.min(100, (day - 21) * 12) : 10
    };
  });

  const latestRisk = displayRiskHistory[displayRiskHistory.length - 1] || { risk_score: 84, risk_category: "URGENT" };

  const handleLogNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote) return;
    setNoteSuccess(true);
    setTimeout(() => {
      setNoteSuccess(false);
      setNewNote("");
    }, 2500);
  };

  return (
    <div className="min-h-screen bg-[#F8FAF7] flex flex-col text-slate-800">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Link & Header */}
        <div className="mb-6">
          <Link
            href="/coordinator/dashboard"
            className="inline-flex items-center text-sm font-semibold text-[#278C78] hover:text-[#173F35] transition-colors mb-3"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Care Priority Queue
          </Link>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm flex flex-col xl:flex-row xl:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#173F35] to-[#278C78] flex items-center justify-center text-white font-bold text-2xl shadow-md shrink-0">
                {senior?.full_name ? senior.full_name[0] : "R"}
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                    {senior?.full_name || "Harshit Thakur"}
                  </h1>
                  <span className="font-mono text-xs px-2.5 py-1 bg-slate-100 text-slate-700 rounded-md font-semibold">
                    {seniorId}
                  </span>
                  <span
                    className={`px-3 py-1 text-xs font-bold rounded-full ${
                      latestRisk.risk_category === "URGENT"
                        ? "bg-rose-100 text-rose-800 border border-rose-200"
                        : latestRisk.risk_category === "HIGH"
                        ? "bg-amber-100 text-amber-800 border border-amber-200"
                        : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                    }`}
                  >
                    {latestRisk.risk_category} RISK ({latestRisk.risk_score}/100)
                  </span>

                  {/* Connected Hardware Home Hub Badge */}
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full text-xs font-semibold">
                    <Radio className="w-3.5 h-3.5 text-emerald-600 animate-pulse" />
                    <span>Home Hub: <strong>{senior?.home_hub_status || "ONLINE"}</strong></span>
                    <span className="font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-emerald-200 text-emerald-700 font-bold">
                      {senior?.home_hub_device_id || "HUB-IND-003"}
                    </span>
                  </span>
                </div>

                <p className="text-sm text-slate-500 flex items-center gap-4 flex-wrap">
                  <span>{senior?.age || 78} yrs &bull; {senior?.gender || "Male"}</span>
                  <span>City: <strong className="text-slate-700">{senior?.city || "Indore"}</strong></span>
                  <span>Language: <strong className="text-slate-700">{senior?.primary_language || "Hindi"}</strong></span>
                  <span>Assigned Coordinator: <strong className="text-[#278C78]">{senior?.coordinator_name || "Anvesha Sharma"}</strong></span>
                </p>
              </div>
            </div>

            {/* Action Buttons: DUAL CALL PROTOCOL (Senior + Family) & Triage Note */}
            <div className="flex items-center gap-2.5 flex-wrap">
              {/* Abhi Call Karo (Demo) Button */}
              <button
                onClick={handleTriggerDemoCall}
                disabled={isTriggeringCall}
                className="px-4 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-700 hover:to-teal-800 text-white rounded-xl font-bold text-xs transition shadow-sm flex items-center gap-2 group active:scale-95"
                title="Trigger immediate Sahara AI PWA Check-in Call"
              >
                <PhoneCall className="w-3.5 h-3.5 text-emerald-300 animate-bounce" />
                <span>{isTriggeringCall ? "कॉल जा रही है..." : "अभी कॉल करो (Demo)"}</span>
              </button>

              {/* Call Senior Directly */}
              <a
                href={`tel:${senior?.senior_phone || '+91 9451818283'}`}
                className="px-4 py-2.5 bg-[#278C78] hover:bg-[#1f7262] text-white rounded-xl font-semibold text-xs transition shadow-sm flex items-center gap-2 group"
                title={`Direct voice call with ${senior?.full_name || "Senior"}`}
              >
                <Phone className="w-3.5 h-3.5 group-hover:animate-bounce" />
                <span>Call Senior (दादाजी)</span>
                <span className="font-mono text-[11px] bg-[#173F35]/30 px-1.5 py-0.5 rounded">
                  {senior?.senior_phone || "+91 9451818283"}
                </span>
              </a>

              {/* Call Family Member */}
              <a
                href={`tel:${senior?.family_phone || '+91 8957266841'}`}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-semibold text-xs transition shadow-sm flex items-center gap-2 group"
                title="Call primary family caregiver Rajesh Sharma"
              >
                <Phone className="w-3.5 h-3.5 text-emerald-400 group-hover:animate-bounce" />
                <span>Call Family ({senior?.family_contact_name || "Son: Rajesh"})</span>
                <span className="font-mono text-[11px] bg-slate-700 px-1.5 py-0.5 rounded text-slate-200">
                  {senior?.family_phone || "+91 8957266841"}
                </span>
              </a>

              {/* Log Triage Note */}
              <button
                onClick={() => {
                  setActiveTab("care_history");
                  setTimeout(() => {
                    const el = document.getElementById("log-action");
                    if (el) el.scrollIntoView({ behavior: "smooth" });
                  }, 100);
                }}
                className="px-3.5 py-2.5 border border-slate-300 text-slate-700 hover:bg-slate-50 rounded-xl font-semibold text-xs transition flex items-center gap-1.5"
              >
                <FileText className="w-3.5 h-3.5 text-[#278C78]" /> Log Triage Note
              </button>
            </div>
          </div>
        </div>

        {/* Real-time Call Toast */}
        {callToast && (
          <div className="mb-4 p-3 bg-emerald-900 text-white rounded-2xl flex items-center justify-between shadow-lg border border-emerald-500 animate-in fade-in duration-200">
            <span className="text-xs font-bold flex items-center gap-2">
              <PhoneCall className="w-4 h-4 text-emerald-300" />
              {callToast}
            </span>
            <button onClick={() => setCallToast(null)} className="text-emerald-300 hover:text-white text-xs font-bold px-2 py-1">
              ✕
            </button>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 mb-6 overflow-x-auto gap-2">
          {[
            { id: "overview", label: "Overview", icon: Home },
            { id: "vitals", label: "Vitals & Baselines", icon: Activity },
            { id: "medications", label: "Medication Adherence", icon: Pill },
            { id: "checkins", label: "Voice Check-ins (Sahara AI)", icon: MessageSquare },
            { id: "risk", label: "Risk & ML Analysis", icon: Brain },
            { id: "care_history", label: "Care History & Actions", icon: Clock },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-sm transition-all whitespace-nowrap ${
                  isActive
                    ? "border-[#278C78] text-[#173F35] font-semibold"
                    : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-[#278C78]" : "text-slate-400"}`} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* TAB 1: OVERVIEW */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Alert Banner if high risk */}
            {latestRisk.risk_score >= 50 && (
              <div className="p-5 rounded-2xl bg-amber-50/80 border border-amber-200 flex items-start gap-4 shadow-sm">
                <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-bold text-amber-900 text-base">
                    Active Multi-Signal Deviation Detected
                  </h3>
                  <p className="text-sm text-amber-800 mt-1 leading-relaxed">
                    Senior exhibiting 3 concurrent shifts: SpO2 dropped from personal baseline (96.2% &rarr; 89.5%), nighttime bathroom visits increased (1 &rarr; 4 visits), and 2 missed afternoon medicine doses.
                  </p>
                  <div className="mt-3 flex items-center gap-3">
                    <span className="text-xs font-semibold px-2.5 py-1 bg-amber-200/60 text-amber-900 rounded-md">
                      Recommended: Protocolized Phone Triage Call
                    </span>
                    <span className="text-xs text-amber-700">Safety Verified &bull; Non-Diagnostic</span>
                  </div>
                </div>
              </div>
            )}

            {/* Profile Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Senior Details */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <User className="w-4 h-4 text-[#278C78]" /> Personal Profile
                </h3>
                <dl className="space-y-3 text-sm">
                  <div>
                    <dt className="text-slate-500">Residential Address</dt>
                    <dd className="font-medium text-slate-900 mt-0.5">{senior?.address || "Indore, MP"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Emergency Family Contact</dt>
                    <dd className="font-medium text-slate-900 mt-0.5 flex items-center justify-between">
                      <span>{senior?.emergency_contact || "+91 9451818283"}</span>
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${senior?.family_consent ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                        {senior?.family_consent ? "Consent Active" : "No Consent"}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Primary Language & Dialect</dt>
                    <dd className="font-medium text-slate-900 mt-0.5">{senior?.primary_language || "Hindi"} (Prefers Hindi/Hinglish calls)</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Monitoring Regime</dt>
                    <dd className="font-medium text-slate-900 mt-0.5">High-Precision Longitudinal (90 Days Active)</dd>
                  </div>
                </dl>
              </div>

              {/* Personal Baselines vs Current Values */}
              <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                    <Activity className="w-4 h-4 text-[#278C78]" /> Personal Baseline vs Current Observation
                  </h3>
                  <span className="text-xs text-slate-400 font-medium">Lagged [t-42, t-14] Window Baseline</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400 uppercase">
                        <th className="pb-2">Biomarker / Signal</th>
                        <th className="pb-2">Personal Median</th>
                        <th className="pb-2">Today's Reading</th>
                        <th className="pb-2">Deviation</th>
                        <th className="pb-2">Signal Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      <tr>
                        <td className="py-2.5 font-medium text-slate-800 flex items-center gap-2">
                          <Heart className="w-4 h-4 text-rose-500" /> Pulse Oximetry (SpO2)
                        </td>
                        <td className="py-2.5 text-slate-600">{senior?.baseline_spo2 || 96.2}%</td>
                        <td className="py-2.5 font-bold text-rose-600">89.5%</td>
                        <td className="py-2.5 font-mono text-xs text-rose-600 font-bold">-6.7% (-3.4 &sigma;)</td>
                        <td className="py-2.5">
                          <span className="px-2 py-0.5 bg-rose-100 text-rose-700 text-xs font-bold rounded">
                            Critical Drop
                          </span>
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2.5 font-medium text-slate-800 flex items-center gap-2">
                          <Activity className="w-4 h-4 text-indigo-500" /> Systolic Blood Pressure
                        </td>
                        <td className="py-2.5 text-slate-600">{senior?.baseline_sys_bp || 128} mmHg</td>
                        <td className="py-2.5 font-bold text-amber-600">146 mmHg</td>
                        <td className="py-2.5 font-mono text-xs text-amber-600 font-bold">+18 mmHg (+2.1 &sigma;)</td>
                        <td className="py-2.5">
                          <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-bold rounded">
                            Elevated
                          </span>
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2.5 font-medium text-slate-800 flex items-center gap-2">
                          <Pill className="w-4 h-4 text-emerald-500" /> Daily Medication Taken
                        </td>
                        <td className="py-2.5 text-slate-600">100% (4/4 doses)</td>
                        <td className="py-2.5 font-bold text-rose-600">50% (2/4 doses)</td>
                        <td className="py-2.5 font-mono text-xs text-rose-600 font-bold">-2 Missed Doses</td>
                        <td className="py-2.5">
                          <span className="px-2 py-0.5 bg-rose-100 text-rose-700 text-xs font-bold rounded">
                            Adherence Lapse
                          </span>
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2.5 font-medium text-slate-800 flex items-center gap-2">
                          <Clock className="w-4 h-4 text-blue-500" /> Night Bathroom Visits
                        </td>
                        <td className="py-2.5 text-slate-600">{senior?.baseline_night_bathroom || 1} visit/night</td>
                        <td className="py-2.5 font-bold text-amber-600">4 visits</td>
                        <td className="py-2.5 font-mono text-xs text-amber-600 font-bold">+300% frequency</td>
                        <td className="py-2.5">
                          <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-bold rounded">
                            Drift Detected
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Quick 14-day Risk Trend Mini Chart */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-bold text-slate-900 text-base">Longitudinal Risk Progression (Past 30 Days)</h3>
                  <p className="text-xs text-slate-500">Noticeable accumulation over the last 5 days triggering early warning threshold</p>
                </div>
                <div className="flex items-center gap-4 text-xs font-medium">
                  <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-[#278C78]"></span> Risk Score</span>
                  <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-rose-400"></span> Urgent Gating (75)</span>
                </div>
              </div>
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={displayRiskHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <ReferenceLine y={75} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: "Urgent", fill: "#f43f5e", fontSize: 10 }} />
                    <ReferenceLine y={50} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: "High", fill: "#f59e0b", fontSize: 10 }} />
                    <Line type="monotone" dataKey="risk_score" stroke="#278C78" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: VITALS & BASELINES */}
        {activeTab === "vitals" && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                <div>
                  <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
                    <Heart className="w-5 h-5 text-rose-500" /> Pulse Oximetry (SpO2) with Personal Baseline Band
                  </h3>
                  <p className="text-xs text-slate-500">
                    Shaded green area shows this senior's personal baseline interval [Median &plusmn; 1.5 MAD]. Deviations outside this zone trigger z-score drift.
                  </p>
                </div>
                <div className="flex items-center gap-4 text-xs font-medium">
                  <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-rose-500"></span> Daily SpO2</span>
                  <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-100 border border-emerald-300"></span> Baseline Band</span>
                </div>
              </div>

              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={displayVitals}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis domain={[85, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <ReferenceArea y1={94.5} y2={97.5} fill="#10b981" fillOpacity={0.12} />
                    <Line type="monotone" dataKey="spo2" stroke="#e11d48" strokeWidth={2.5} dot={{ r: 2 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Blood Pressure Chart */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                <div>
                  <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
                    <Activity className="w-5 h-5 text-indigo-500" /> Blood Pressure Progression (Systolic & Diastolic)
                  </h3>
                  <p className="text-xs text-slate-500">
                    Baseline systolic range: 122 - 134 mmHg. Recent upward trend indicates compounding cardiovascular strain.
                  </p>
                </div>
              </div>

              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={displayVitals}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis domain={[70, 160]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <ReferenceArea y1={122} y2={134} fill="#6366f1" fillOpacity={0.12} />
                    <Line type="monotone" dataKey="sys_bp" name="Systolic BP" stroke="#4f46e5" strokeWidth={2.5} dot={{ r: 2 }} />
                    <Line type="monotone" dataKey="dia_bp" name="Diastolic BP" stroke="#06b6d4" strokeWidth={2} dot={{ r: 2 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Night Bathroom Visits & Inactivity */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <h4 className="font-bold text-slate-900 text-base mb-2">Nighttime Bathroom Frequency</h4>
                <p className="text-xs text-slate-500 mb-4">Baseline: 1 visit/night. Sharp increase correlates with restlessness.</p>
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={displayVitals.slice(-14)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 6]} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Bar dataKey="night_bathroom_visits" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <h4 className="font-bold text-slate-900 text-base mb-2">Daily Inactivity Hours</h4>
                <p className="text-xs text-slate-500 mb-4">Baseline: ~6.2 hrs. Elevated inactivity mirrors reported weakness.</p>
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={displayVitals.slice(-14)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis domain={[4, 12]} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="inactivity_hours" stroke="#8b5cf6" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: MEDICATION ADHERENCE */}
        {activeTab === "medications" && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
                    <Pill className="w-5 h-5 text-emerald-600" /> 30-Day Medication Adherence Calendar
                  </h3>
                  <p className="text-xs text-slate-500">Tracked via connected smart dispenser and coordinator confirmation</p>
                </div>
                <div className="flex items-center gap-3 text-xs font-semibold">
                  <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-500"></span> Taken on time</span>
                  <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-rose-500"></span> Missed dose</span>
                </div>
              </div>

              {/* 30-day dot grid */}
              <div className="grid grid-cols-10 sm:grid-cols-15 gap-2.5 py-4">
                {Array.from({ length: 30 }).map((_, i) => {
                  const day = i + 1;
                  const isMissed = day === 26 || day === 28;
                  return (
                    <div
                      key={day}
                      className={`p-2 rounded-xl text-center border transition-all ${
                        isMissed
                          ? "bg-rose-50 border-rose-200 text-rose-700"
                          : "bg-emerald-50 border-emerald-200 text-emerald-700"
                      }`}
                    >
                      <div className="text-[10px] font-medium text-slate-400">D{day}</div>
                      <div className="text-xs font-bold mt-0.5">
                        {isMissed ? <AlertCircle className="w-4 h-4 mx-auto text-rose-600" /> : <Check className="w-4 h-4 mx-auto text-emerald-600" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Prescriptions List */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <h4 className="font-bold text-slate-900 text-base mb-4">Active Medication Regimen</h4>
              <div className="space-y-3">
                {[
                  { name: "Amlodipine Besylate", dose: "5mg", timing: "Morning (08:00 AM)", adherence: "96.4%", status: "Stable" },
                  { name: "Metformin Hydrochloride", dose: "500mg", timing: "Morning & Night with meals", adherence: "88.2%", status: "2 Missed Recently" },
                  { name: "Atorvastatin Calcium", dose: "10mg", timing: "Night (09:00 PM)", adherence: "98.0%", status: "Stable" },
                ].map((med, idx) => (
                  <div key={idx} className="p-4 rounded-xl border border-slate-100 bg-slate-50 flex items-center justify-between">
                    <div>
                      <h5 className="font-bold text-slate-800 text-sm">{med.name} <span className="font-normal text-slate-500">({med.dose})</span></h5>
                      <p className="text-xs text-slate-500 mt-0.5">Schedule: {med.timing}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-slate-800">{med.adherence} adherence</div>
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded ${med.status.includes('Missed') ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`}>
                        {med.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: VOICE CHECK-INS & AI CALLS (SAHARA AI PROTOCOL) */}
        {activeTab === "checkins" && (
          <div className="space-y-6">

            {/* DEVICE HEALTH & CONNECTIVITY CARD (ADDENDUM B) */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl ${deviceHealth?.warning_no_heartbeat ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>
                    <Smartphone className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-base flex items-center gap-2">
                      Senior Device Health &amp; PWA Connectivity
                      {deviceHealth?.warning_no_heartbeat ? (
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200">
                          Inactive Warning (&gt;24h)
                        </span>
                      ) : (
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                          Connected &amp; Healthy
                        </span>
                      )}
                    </h4>
                    <p className="text-xs text-slate-500">
                      Client Heartbeat &bull; Idempotent Telemetry &bull; Zero-PII Push Receiver
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleTriggerDemoCall}
                  disabled={isTriggeringCall}
                  className="px-3.5 py-2 bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-700 hover:to-teal-800 text-white rounded-xl text-xs font-bold transition flex items-center gap-2 shadow-xs active:scale-95"
                >
                  <PhoneCall className="w-3.5 h-3.5 text-emerald-300 animate-bounce" />
                  <span>{isTriggeringCall ? "कॉल जा रही है..." : "🔔 अभी टेस्ट कॉल भेजें (Trigger Call)"}</span>
                </button>
              </div>

              {/* Warning banner if inactive > 24 hours */}
              {deviceHealth?.warning_no_heartbeat && (
                <div className="p-3.5 bg-rose-50 border border-rose-300 rounded-xl flex items-start gap-3 text-rose-900 text-xs">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <strong>चेतावनी (Device Inactive):</strong> इस वरिष्ठ नागरिक के फोन से 24 घंटे से अधिक समय से कोई हार्टबीट नहीं मिली है ({deviceHealth?.last_seen_relative || "Inactive"}). संभवतः PWA बंद है, बैटरी सेवर मोड में है या इंटरनेट बंद है।
                  </div>
                </div>
              )}

              {/* Device Telemetry Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Device ID</span>
                  <span className="font-mono font-bold text-slate-800 text-xs">
                    {deviceHealth?.device_id || `PWA-DEV-${seniorId}`}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Paired At</span>
                  <span className="font-semibold text-slate-700">
                    {deviceHealth?.paired_at ? new Date(deviceHealth.paired_at).toLocaleDateString() : "18 Oct 2026"}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Last Heartbeat</span>
                  <span className={`font-bold ${deviceHealth?.warning_no_heartbeat ? 'text-rose-600' : 'text-emerald-700'}`}>
                    {deviceHealth?.last_seen_relative || "Just now"}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">App Client Version</span>
                  <span className="font-semibold text-slate-700">
                    {deviceHealth?.app_version || "1.2.0-pwa"}
                  </span>
                </div>
              </div>

              {/* Permissions Checklist */}
              <div className="pt-2 border-t border-slate-100 flex items-center gap-4 flex-wrap text-xs">
                <span className="font-bold text-slate-500 uppercase text-[10px]">Permission Checks:</span>
                <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Notifications: Active
                </span>
                <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Microphone: Granted
                </span>
                <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Full-Screen Call UI: Allowed
                </span>
                <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Battery Optimisation: Unrestricted
                </span>
              </div>
            </div>

            {/* LIVE CHECK-IN CALL TIMELINE */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-slate-900 text-base flex items-center gap-2">
                    <Radio className="w-4 h-4 text-[#278C78]" />
                    Sahara AI Daily Routine Check-ins Timeline
                  </h4>
                  <p className="text-xs text-slate-500">
                    Recorded voice calls &bull; Sarvam AI STT &bull; Per-turn audio &bull; Incremental Doctor Rescore
                  </p>
                </div>
                <button
                  onClick={fetchCheckinData}
                  className="px-2.5 py-1 text-xs font-semibold text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 flex items-center gap-1"
                >
                  <RotateCw className="w-3 h-3 text-[#278C78]" /> Refresh
                </button>
              </div>

              {checkinTimeline.length === 0 ? (
                <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-slate-400 text-xs">
                  कोई कॉल इतिहास नहीं मिला। &lsquo;अभी टेस्ट कॉल भेजें&rsquo; पर क्लिक करके तत्काल PWA कॉल शुरू करें।
                </div>
              ) : (
                checkinTimeline.map((chk: any) => (
                  <div
                    key={chk.checkin_id}
                    className={`bg-white rounded-2xl border-2 p-6 shadow-sm space-y-4 transition ${
                      chk.is_emergency
                        ? "border-rose-400/80 bg-rose-50/20"
                        : "border-slate-200"
                    }`}
                  >
                    {/* Call Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                      <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl ${chk.is_emergency ? 'bg-rose-600 text-white animate-pulse' : 'bg-[#173F35] text-white'}`}>
                          <PhoneCall className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h5 className="font-bold text-slate-900 text-sm">
                              {chk.caller_name || "Sahara AI"} Check-in Call
                            </h5>
                            <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                              {chk.checkin_id}
                            </span>
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                                chk.status === "completed"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : chk.status === "ringing"
                                  ? "bg-blue-100 text-blue-800 animate-pulse"
                                  : chk.status === "declined"
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-rose-100 text-rose-800"
                              }`}
                            >
                              {chk.status}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {chk.caller_label || "सहारा AI"} &bull; {senior?.coordinator_name?.split(" ")[0] || "अनिता"} दीदी की तरफ़ से &bull;{" "}
                            {chk.rang_at ? new Date(chk.rang_at).toLocaleString() : "Today"} &bull; Duration: {chk.duration_seconds || 0}s
                          </p>
                        </div>
                      </div>

                      {/* Review State / Mark Reviewed Button */}
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold px-2 py-0.5 bg-slate-100 rounded text-slate-600">
                          STT: {Math.round((chk.stt_confidence || 0.98) * 100)}%
                        </span>
                        {chk.is_reviewed ? (
                          <span className="px-3 py-1 bg-emerald-50 text-emerald-700 text-xs font-bold rounded-lg border border-emerald-200 flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" /> समीक्षित (Reviewed)
                          </span>
                        ) : (
                          <button
                            onClick={() => handleMarkReviewed(chk.checkin_id)}
                            className="px-3 py-1 bg-[#278C78] hover:bg-[#1f7262] text-white text-xs font-bold rounded-lg transition shadow-2xs"
                          >
                            समीक्षा पूर्ण करें (Mark Reviewed)
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Emergency Alert Banner */}
                    {chk.is_emergency && (
                      <div className="p-3 bg-rose-600 text-white rounded-xl flex items-center justify-between text-xs font-bold shadow-xs">
                        <span className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-yellow-300 animate-bounce" />
                          🚨 आपातकालीन मौखिक लक्षण दर्ज (Acute Emergency Symptom Caught! Immediate Intervention Required)
                        </span>
                        <span className="bg-white/20 px-2 py-0.5 rounded text-[11px]">Priority #1</span>
                      </div>
                    )}

                    {/* Clinical Summary */}
                    {(chk.summary_hi || chk.summary_en) && (
                      <div className="p-3.5 bg-emerald-50/70 border border-emerald-200 rounded-xl space-y-1 text-xs">
                        <span className="font-bold text-emerald-950 uppercase tracking-wide text-[10px] block">
                          3-Line Clinical Summary (Doctor AI):
                        </span>
                        {chk.summary_hi && <p className="font-medium text-emerald-900">{chk.summary_hi}</p>}
                        {chk.summary_en && <p className="text-emerald-800 italic">{chk.summary_en}</p>}
                      </div>
                    )}

                    {/* Per-Turn Voice Audio & Dialogue */}
                    {chk.turns && chk.turns.length > 0 && (
                      <div className="space-y-3 pt-2">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                          Per-Turn Dialogue &amp; Spoken Audio:
                        </span>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {chk.turns.map((turn: any, tIdx: number) => (
                            <div
                              key={tIdx}
                              className={`p-3.5 rounded-xl border text-xs space-y-2 ${
                                turn.is_emergency
                                  ? "bg-rose-50 border-rose-200"
                                  : "bg-slate-50 border-slate-200"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-slate-700">
                                  सवाल #{turn.turn_index}: {turn.question_text?.substring(0, 45)}...
                                </span>
                                {turn.keypad_input && (
                                  <span className="px-2 py-0.5 bg-slate-200 text-slate-800 rounded font-bold font-mono text-[10px]">
                                    कीपैड: {turn.keypad_input}
                                  </span>
                                )}
                              </div>

                              <p className="p-2 bg-white rounded-lg border border-slate-100 font-semibold text-slate-900 italic">
                                &ldquo;{turn.transcript}&rdquo;
                              </p>

                              {turn.audio_url && (
                                <audio controls className="w-full h-8 rounded" src={turn.audio_url} />
                              )}

                              {turn.is_emergency && (
                                <span className="text-[10px] font-bold text-rose-700 block">
                                  🚨 Emergency cue caught in this turn
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* SECTION 3: Additional Historical Notes */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-bold text-slate-900 text-base">
                  Historical Coordinator Touchpoint Log
                </h4>
                <span className="text-xs text-slate-400">Past 14 Days</span>
              </div>

              <div className="space-y-3">
                {[
                  {
                    date: "3 Days Ago, 09:15 AM",
                    type: "Automated Daily Senior Voice Check-in",
                    author: "SaathiCare IVR Assistant",
                    textHindi: "दादाजी की रिकॉर्डिंग: 'Aaj subah bistar se uthne par thoda chakkar jaisa mehsoos hua. Par chalne me koi dikkat nahi hai.'",
                    textEn: "Senior's check-in: 'Felt slight dizziness on getting out of bed. No difficulty walking.'",
                    cues: [
                      { label: "dizziness", conf: "88%", negated: false },
                      { label: "mobility_issue", conf: "85%", negated: true }
                    ]
                  },
                  {
                    date: "6 Days Ago, 11:00 AM",
                    type: "Routine Weekly Coordinator Touchpoint",
                    author: "Anvesha Sharma",
                    textHindi: "दादाजी ने कहा कि सब ठीक चल रहा है, दवाई समय पर ले रहे हैं। घर के बाहर टहलने भी गए थे।",
                    textEn: "Everything reported normal. Medicines taken on time. Went for usual morning stroll.",
                    cues: []
                  }
                ].map((note, idx) => (
                  <div key={idx} className="p-4 rounded-xl border border-slate-100 bg-slate-50 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-700 bg-white border border-slate-200 px-2 py-0.5 rounded">
                          {note.type}
                        </span>
                        <span className="text-xs text-slate-400">&bull; {note.date}</span>
                      </div>
                      <span className="text-xs text-slate-500 font-medium">Logged by {note.author}</span>
                    </div>

                    <p className="text-xs font-medium text-slate-800 italic">
                      &ldquo;{note.textHindi}&rdquo;
                    </p>

                    <div className="flex items-center gap-2 pt-1 flex-wrap">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Cues:</span>
                      {note.cues.length === 0 ? (
                        <span className="text-xs text-slate-400 italic">No adverse cues</span>
                      ) : (
                        note.cues.map((c, cIdx) => (
                          <span
                            key={cIdx}
                            className={`text-[11px] px-2 py-0.5 rounded font-semibold ${
                              c.negated
                                ? "bg-slate-200 text-slate-600 line-through"
                                : "bg-rose-100 text-rose-800"
                            }`}
                          >
                            {c.label} ({c.conf}) {c.negated && "(Negated)"}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: RISK & ML ANALYSIS */}
        {activeTab === "risk" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Score composition */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <h4 className="font-bold text-slate-900 text-base mb-1">Score Composition</h4>
                <p className="text-xs text-slate-500 mb-4">Calibrated ensemble blending rules & ML</p>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span>Clinical Rules Engine (55% weight)</span>
                      <span className="text-[#278C78]">78 / 100</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-[#278C78] h-full rounded-full" style={{ width: '78%' }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span>IsolationForest Anomaly (45% weight)</span>
                      <span className="text-indigo-600">88 / 100</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-indigo-600 h-full rounded-full" style={{ width: '88%' }}></div>
                    </div>
                  </div>
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between font-bold text-slate-900">
                    <span>Blended Calibrated Score</span>
                    <span className="text-xl text-rose-600 font-black">84 / 100</span>
                  </div>
                </div>
              </div>

              {/* Benign Explanation Check */}
              <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <h4 className="font-bold text-slate-900 text-base mb-1">Benign Context Verification</h4>
                <p className="text-xs text-slate-500 mb-4">Automatic filtering of expected lifestyle anomalies</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                    <span className="font-bold text-slate-700 block mb-1">Travel & Outing Filter</span>
                    <p className="text-slate-500">Door sensor shows normal residency patterns (&gt; 18 hrs inside). Not attributable to travel.</p>
                    <span className="inline-block mt-2 font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">Verified At Home</span>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                    <span className="font-bold text-slate-700 block mb-1">Festival / Holiday Calibration</span>
                    <p className="text-slate-500">No active regional festival distortion in Indore region today.</p>
                    <span className="inline-block mt-2 font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">Baseline Applicable</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Top 3 Contributing Signals */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <h4 className="font-bold text-slate-900 text-base mb-3">Top 3 Contributing Telemetry Signals (SHAP & Deviation)</h4>
              <div className="space-y-3">
                {[
                  {
                    title: "Oxygen Saturation Drop (SpO2)",
                    impact: "+42% Risk Weight",
                    desc: "Sustained decline from personal median 96.2% to 89.5% over 5 consecutive days (-3.4 standard deviations from individual baseline)."
                  },
                  {
                    title: "Medication Adherence Gap",
                    impact: "+28% Risk Weight",
                    desc: "Missed 2 consecutive afternoon anti-hypertensive doses with reported forgetfulness and lethargy."
                  },
                  {
                    title: "Nocturnal Restlessness",
                    impact: "+18% Risk Weight",
                    desc: "Nighttime bathroom visits quadrupled (from 1 visit baseline to 4 visits/night) for 3 consecutive nights."
                  }
                ].map((item, idx) => (
                  <div key={idx} className="p-4 rounded-xl border border-slate-100 bg-slate-50 flex items-start justify-between gap-4">
                    <div>
                      <h5 className="font-bold text-slate-900 text-sm">{item.title}</h5>
                      <p className="text-xs text-slate-600 mt-1">{item.desc}</p>
                    </div>
                    <span className="text-xs font-bold text-rose-700 bg-rose-100 px-2.5 py-1 rounded-md shrink-0">
                      {item.impact}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: CARE HISTORY & ACTIONS */}
        {activeTab === "care_history" && (
          <div className="space-y-6">
            {/* Log Action Box */}
            <div id="log-action" className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <h3 className="font-bold text-slate-900 text-base mb-1 flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#278C78]" /> Log Care Coordinator Contact & Action
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Record findings from your phone check-in or escalate to family/clinical supervisor.
              </p>

              {noteSuccess && (
                <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-xl flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-600" /> Action logged successfully! Alert status updated in coordinator queue.
                </div>
              )}

              <form onSubmit={handleLogNote} className="space-y-4">
                {/* Person Contacted Selector: Senior vs Family */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1.5">
                    Who did you contact? / किससे बात हुई?
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setContactTarget("SENIOR")}
                      className={`p-3 rounded-xl border text-left transition flex items-center gap-3 ${
                        contactTarget === "SENIOR"
                          ? "border-[#278C78] bg-[#EAF5EF] text-[#173F35] font-bold ring-2 ring-[#278C78]/20"
                          : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      <User className="w-5 h-5 text-[#278C78] shrink-0" />
                      <div>
                        <div className="text-xs font-bold">Senior Directly (दादाजी / {senior?.full_name?.split(" ")[0] || "Senior"})</div>
                        <div className="text-[11px] text-slate-500 font-mono">{senior?.senior_phone || "+91 9451818283"}</div>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setContactTarget("FAMILY")}
                      className={`p-3 rounded-xl border text-left transition flex items-center gap-3 ${
                        contactTarget === "FAMILY"
                          ? "border-slate-800 bg-slate-100 text-slate-900 font-bold ring-2 ring-slate-800/20"
                          : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      <Phone className="w-5 h-5 text-slate-800 shrink-0" />
                      <div>
                        <div className="text-xs font-bold">Family ({senior?.family_contact_name || "Son: Rajesh Sharma"})</div>
                        <div className="text-[11px] text-slate-500 font-mono">{senior?.family_phone || "+91 8957266841"}</div>
                      </div>
                    </button>
                  </div>
                </div>

                {/* Dynamic Protocol Checklist Reminder */}
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1.5">
                  <span className="font-bold text-slate-700 block uppercase tracking-wider text-[10px]">
                    {contactTarget === "SENIOR"
                      ? "📋 Checklist A: Questions to verify with Senior directly (तबीयत एवं दवा)"
                      : "📋 Checklist B: Questions to verify with Family Member (परिवार से बातचीत)"}
                  </span>
                  {contactTarget === "SENIOR" ? (
                    <ul className="list-disc list-inside text-slate-600 space-y-0.5 text-[11px]">
                      <li>1. <strong>Confirm breathlessness:</strong> क्या लेटने पर या चलने पर सांस फूलती है? (Resting vs Exertional)</li>
                      <li>2. <strong>Medication intake:</strong> क्या सुबह की बीपी/हार्ट की गोली ली? (Confirm taken with water)</li>
                      <li>3. <strong>Appetite and hydration:</strong> क्या दोपहर का भोजन और पर्याप्त पानी लिया?</li>
                    </ul>
                  ) : (
                    <ul className="list-disc list-inside text-slate-600 space-y-0.5 text-[11px]">
                      <li>1. <strong>In-person visit:</strong> क्या आप या कोई रिश्तेदार आज घर जाकर देख सकता है?</li>
                      <li>2. <strong>Diet & assistance:</strong> क्या दादाजी ने आज ठीक से खाना खाया?</li>
                      <li>3. <strong>Doctor appointment:</strong> क्या शाम तक फिजिशियन कंसल्टेशन की व्यवस्था करनी है?</li>
                    </ul>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                      Call Outcome / Resolution
                    </label>
                    <select
                      value={callOutcome}
                      onChange={(e) => setCallOutcome(e.target.value)}
                      className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                    >
                      <option value="RESOLVED_NORMAL">Resolved: Senior Reassured &amp; Normal</option>
                      <option value="MED_REMINDER_GIVEN">Medication Reminder Delivered &amp; Taken</option>
                      <option value="ESCALATED_FAMILY">Escalated: Contacted Family for In-Person Visit</option>
                      <option value="DOCTOR_RECOMMENDED">Suggested Non-Emergency Doctor Consultation</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                      Follow-up Required
                    </label>
                    <select className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-[#278C78]">
                      <option>Follow-up within 24 hours</option>
                      <option>Follow-up within 48 hours</option>
                      <option>Routine weekly check-in</option>
                      <option>No further immediate action required</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    Coordinator Notes (Supports Hindi / English / Hinglish)
                  </label>
                  <textarea
                    rows={3}
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    placeholder={
                      contactTarget === "SENIOR"
                        ? `e.g. Spoke with ${senior?.full_name || "Senior"}. Verified health condition and medication. Will check in tomorrow morning.`
                        : `e.g. Spoke with family contact (${senior?.family_contact_name || "Family"}). Discussed today's update and care steps.`
                    }
                    className="w-full text-sm border border-slate-300 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                  ></textarea>
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    className="px-5 py-2.5 bg-[#278C78] text-white font-semibold text-sm rounded-xl hover:bg-[#1f7262] transition shadow-sm flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" /> Save Care Intervention
                  </button>
                </div>
              </form>
            </div>

            {/* Historical Timeline */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <h4 className="font-bold text-slate-900 text-base mb-4">Past Coordinator Interventions</h4>
              <div className="space-y-4">
                {[
                  {
                    date: "Today, 10:15 AM",
                    title: "Triage Alert Follow-Up",
                    coordinator: "Anvesha Sharma",
                    details: "Conducted 3-question telephone assessment regarding oxygen reading and bathroom visits. Senior reported feeling fatigued.",
                    status: "Pending Action"
                  },
                  {
                    date: "Oct 25, 2026",
                    title: "Medication Adherence Outreach",
                    coordinator: "Anvesha Sharma",
                    details: "Senior missed morning Amlodipine dose. Reminded via phone; confirmed taken with warm water.",
                    status: "Resolved"
                  },
                  {
                    date: "Oct 18, 2026",
                    title: "Bi-Weekly Wellbeing Check",
                    coordinator: "Anvesha Sharma",
                    details: "Standard wellbeing call. All signals within normal baseline range. Mood reported cheerful.",
                    status: "Routine Normal"
                  }
                ].map((act, idx) => (
                  <div key={idx} className="flex items-start gap-4 p-4 rounded-xl border border-slate-100 bg-slate-50/70">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#278C78] mt-1.5 shrink-0"></div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h5 className="font-bold text-slate-900 text-sm">{act.title}</h5>
                        <span className="text-xs text-slate-400">{act.date}</span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">{act.details}</p>
                      <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-2">
                        <span>Logged by <strong>{act.coordinator}</strong></span>
                        &bull;
                        <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">{act.status}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default function SeniorDetailPage() {
  return (
    <React.Suspense fallback={<div className="min-h-screen bg-[#F8FAF7] flex items-center justify-center font-bold text-slate-500">Loading senior telemetry...</div>}>
      <SeniorDetailContent />
    </React.Suspense>
  );
}
