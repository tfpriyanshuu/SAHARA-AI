"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  Heart,
  Pill,
  Shield,
  Activity,
  Phone,
  Clock,
  Wifi,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Sliders,
  Sparkles,
  User,
  Home
} from "lucide-react";

export default function FamilyDashboard() {
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [consentActive, setConsentActive] = useState(true);

  // Exact 4-person contact setup requested by user
  const SENIOR_NAME = "Harshit Thakur";
  const SENIOR_PHONE = "9451818283";
  const COORDINATOR_NAME = "Anvesha Sharma";
  const COORDINATOR_PHONE = "8267069623";
  const FAMILY_USER_NAME = "Anchal Mishra (Mummy)";
  const FAMILY_PHONE = "8957266841";

  useEffect(() => {
    async function loadSummary() {
      try {
        const token = localStorage.getItem("saathi_token");
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch("/api/v1/family/weekly-summary", { headers });
        if (res.ok) {
          const data = await res.json();
          setSummary(data);
          setConsentActive(data.family_consent);
        } else {
          // Robust demo fallback with user-specified persona
          setSummary({
            senior_id: "SEN_001",
            senior_name: SENIOR_NAME,
            city: "Indore",
            status_badge: "NEEDS_ATTENTION",
            status_text_en: "Mild respiratory and medicine adherence variations noted over past 3 days. Care Coordinator is actively monitoring.",
            status_text_hi: "पिछले 3 दिनों में सांस और दवा लेने के समय में थोड़ा बदलाव देखा गया है। केयर कोऑर्डिनेटर नियमित ध्यान दे रही हैं।",
            avg_spo2: 91.2,
            med_adherence_pct: 88,
            routine_stability: "Mild Shift",
            coordinator_name: COORDINATOR_NAME,
            coordinator_phone: COORDINATOR_PHONE,
            family_consent: true,
            serious_alert: {
              active: true,
              level: "URGENT",
              message: "SpO2 reading dropped below personal baseline for 3 consecutive days. Anvesha Sharma has scheduled a clinical follow-up."
            }
          });
        }
      } catch (e) {
        console.warn("Using fallback family summary data");
      } finally {
        setLoading(false);
      }
    }
    loadSummary();
  }, []);

  const t = {
    en: {
      familyPortal: "SAHARA-AI FAMILY HUB",
      loggedInAs: "Logged in as",
      linkedSenior: "Linked Senior",
      coordinator: "Care Coordinator",
      callSenior: `📞 Call Harshit (+91 ${SENIOR_PHONE})`,
      callCoordinator: `📞 Call Coordinator Anvesha (+91 ${COORDINATOR_PHONE})`,
      manageConsent: "Privacy Settings",
      evalHeading: "Weekly Wellbeing Assessment (Oct 23 - Oct 30, 2026)",
      routineStable: "Daily Routine and Biomarkers Stable",
      routineChanged: "Mild Routine Indicator Changes Observed",
      activeFollowUp: "Active Coordinator Supervision",
      medAdherence: "Medication Adherence",
      medDetail: "2 doses delayed this week",
      avgSpo2: "Average Blood Oxygen (SpO2)",
      spo2Detail: "Personal Baseline: 96.2% (-5%)",
      dailyActivity: "Daily Activity & Sleep",
      activityDetail: "2,100 steps · 7.1 hours restful sleep",
      iotHeading: "Connected Home Hub & Safety Telemetry",
      iotSubtitle: "Real-time operating status of home medical sensors",
      allOnline: "All 4 Devices Online",
      supportTitle: "Have a question about Harshit Thakur's health?",
      supportText: "Care Coordinator Anvesha Sharma conducts daily telephone reviews and coordinates doctor visits whenever biomarker shifts are detected.",
      callAnveshaCta: `Call Anvesha Sharma (${COORDINATOR_PHONE})`,
      location: "Location",
      power: "Power",
      synced: "Synced",
      devices: [
        {
          name: "Smart Pill Dispenser (Home Hub)",
          location: "Dining Table",
          battery: "94%",
          lastSync: "12 mins ago",
          status: "Normal",
          details: "Morning and evening compartments verified. Next dose at 08:00 PM."
        },
        {
          name: "Fall-Detection Radar",
          location: "Living Room & Restroom Entry",
          battery: "AC Powered",
          lastSync: "3 mins ago",
          status: "Active",
          details: "Zero falls detected. Micro-movement confirms healthy room pacing."
        },
        {
          name: "Sleep & Respiration Sensor Pad",
          location: "Bed Mattress (Scheme 54)",
          battery: "AC Powered",
          lastSync: "Today, 07:15 AM",
          status: "Normal",
          details: "Recorded 4 brief awakenings last night. Respiration rhythm normal."
        },
        {
          name: "Smart Magnetic Door Sensor",
          location: "Main Front Gate",
          battery: "88%",
          lastSync: "Today, 10:30 AM",
          status: "Secure",
          details: "Front door opened once for grocery delivery. Senior safely inside."
        }
      ]
    },
    hi: {
      familyPortal: "सहारा-AI परिवार पोर्टल",
      loggedInAs: "परिवार सदस्य",
      linkedSenior: "वरिष्ठ नागरिक",
      coordinator: "केयर कोऑर्डिनेटर",
      callSenior: `📞 हर्षित जी को कॉल करें (${SENIOR_PHONE})`,
      callCoordinator: `📞 अन्वेषा दीदी को कॉल करें (${COORDINATOR_PHONE})`,
      manageConsent: "गोपनीयता सेटिंग्स",
      evalHeading: "साप्ताहिक स्वास्थ्य मूल्यांकन (23 अक्टूबर - 30 अक्टूबर, 2026)",
      routineStable: "दैनिक दिनचर्या और स्वास्थ्य संकेतक स्थिर",
      routineChanged: "दिनचर्या संकेतकों में हल्का बदलाव दर्ज",
      activeFollowUp: "कोऑर्डिनेटर द्वारा सक्रिय निगरानी",
      medAdherence: "दवा समयबद्धता",
      medDetail: "इस सप्ताह 2 खुराक में देरी हुई",
      avgSpo2: "औसत ऑक्सीजन स्तर (SpO2)",
      spo2Detail: "सामान्य बेसलाइन: 96.2% (-5%)",
      dailyActivity: "दैनिक हलचल एवं नींद",
      activityDetail: "2,100 कदम · 7.1 घंटे आरामदायक नींद",
      iotHeading: "स्मार्ट होम हब और सुरक्षा उपकरण",
      iotSubtitle: "घर में लगे स्वास्थ्य और सुरक्षा उपकरणों की वास्तविक स्थिति",
      allOnline: "सभी 4 उपकरण सक्रिय हैं",
      supportTitle: "हर्षित ठाकुर जी की सेहत के बारे में कोई सवाल है?",
      supportText: "केयर कोऑर्डिनेटर अन्वेषा शर्मा रोज़ाना फ़ोन पर बातचीत करती हैं और स्वास्थ्य में बदलाव होने पर तुरंत डॉक्टर से परामर्श कराती हैं।",
      callAnveshaCta: `अन्वेषा शर्मा को कॉल करें (${COORDINATOR_PHONE})`,
      location: "स्थान",
      power: "बैटरी",
      synced: "सिंक हुआ",
      devices: [
        {
          name: "स्मार्ट पिल बॉक्स (होम हब)",
          location: "डाइनिंग टेबल",
          battery: "94%",
          lastSync: "12 मिनट पहले",
          status: "सामान्य",
          details: "सुबह और शाम के खाने के बाद की दवाइयाँ सत्यापित। अगली खुराक रात 08:00 बजे।"
        },
        {
          name: "गिरने की पहचान वाला रडार",
          location: "लिविंग रूम और वॉशरूम प्रवेश",
          battery: "बिजली संचालित",
          lastSync: "3 मिनट पहले",
          status: "सक्रिय",
          details: "कोई गिरावट दर्ज नहीं हुई। कमरे में चलना-फिरना सामान्य पाया गया।"
        },
        {
          name: "नींद व श्वास गति पैड",
          location: "बिस्तर (स्कीम 54)",
          battery: "बिजली संचालित",
          lastSync: "आज सुबह 07:15 बजे",
          status: "सामान्य",
          details: "रात में सामान्य नींद दर्ज हुई। सांस की गति नियमित है।"
        },
        {
          name: "स्मार्ट मुख्य द्वार सेंसर",
          location: "मुख्य प्रवेश द्वार",
          battery: "88%",
          lastSync: "आज सुबह 10:30 बजे",
          status: "सुरक्षित",
          details: "सामान लेने हेतु एक बार दरवाज़ा खुला। वरिष्ठ नागरिक घर में सुरक्षित हैं।"
        }
      ]
    }
  }[lang];

  return (
    <div className="min-h-screen bg-[#F8FAF7] flex flex-col text-slate-800">
      <Navbar />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Top Header with Strict Language Switcher and Real Call Action */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[#173F35] to-[#278C78] text-white flex items-center justify-center font-bold text-2xl shadow-md">
              H
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-bold text-[#278C78] uppercase tracking-wider">
                  {t.familyPortal} &bull; Indore
                </span>
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                  {t.loggedInAs}: <strong>{FAMILY_USER_NAME}</strong>
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 mt-1">
                {SENIOR_NAME} (72 yrs)
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">
                {t.coordinator}: <strong>{COORDINATOR_NAME}</strong> ({COORDINATOR_PHONE})
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            {/* Pure Language Switcher Toggle */}
            <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200 self-start sm:self-center">
              <button
                onClick={() => setLang("en")}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition ${
                  lang === "en" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-900"
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLang("hi")}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition ${
                  lang === "hi" ? "bg-emerald-600 text-white shadow-sm" : "text-slate-500 hover:text-slate-900"
                }`}
              >
                हिन्दी
              </button>
            </div>

            {/* Direct Phone Call to Senior (Opens native dialer on mobile phone) */}
            <a
              href={`tel:+91${SENIOR_PHONE}`}
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold text-xs transition shadow-sm flex items-center justify-center gap-2 active:scale-95"
              title="Open phone dialer to call Harshit Thakur directly"
            >
              <Phone className="w-4 h-4 fill-white" />
              <span>{t.callSenior}</span>
            </a>

            {/* Direct Phone Call to Coordinator (Opens native dialer on mobile phone) */}
            <a
              href={`tel:+91${COORDINATOR_PHONE}`}
              className="px-4 py-2.5 bg-[#173F35] hover:bg-[#205749] text-white rounded-xl font-bold text-xs transition shadow-sm flex items-center justify-center gap-2 active:scale-95"
              title="Open phone dialer to call Anvesha Sharma directly"
            >
              <Phone className="w-4 h-4 text-emerald-400" />
              <span>{t.callCoordinator}</span>
            </a>
          </div>
        </div>

        {/* Weekly Wellbeing Evaluation Card */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                {t.evalHeading}
              </span>
              <h2 className="text-xl md:text-2xl font-bold text-slate-900 mt-1">
                {summary?.status_badge === "NEEDS_ATTENTION" ? (
                  <span className="text-amber-700 flex items-center gap-2">
                    <AlertTriangle className="w-6 h-6 text-amber-500" />
                    {t.routineChanged}
                  </span>
                ) : (
                  <span className="text-emerald-700 flex items-center gap-2">
                    <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                    {t.routineStable}
                  </span>
                )}
              </h2>
            </div>

            <span className="px-3 py-1 bg-amber-50 border border-amber-200 text-amber-800 text-xs font-bold rounded-full self-start sm:self-center">
              {t.activeFollowUp}
            </span>
          </div>

          <p className="text-base text-slate-700 leading-relaxed bg-[#F8FAF7] p-5 rounded-2xl border border-slate-100">
            {lang === "en" ? summary?.status_text_en : summary?.status_text_hi}
          </p>

          {/* 3 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                <Pill className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase">{t.medAdherence}</span>
                <div className="text-2xl font-black text-slate-900 mt-0.5">{summary?.med_adherence_pct || 88}%</div>
                <span className="text-xs text-amber-600 font-semibold">{t.medDetail}</span>
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
                <Heart className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase">{t.avgSpo2}</span>
                <div className="text-2xl font-black text-slate-900 mt-0.5">{summary?.avg_spo2 || 91.2}%</div>
                <span className="text-xs text-rose-600 font-semibold">{t.spo2Detail}</span>
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                <Activity className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase">{t.dailyActivity}</span>
                <div className="text-2xl font-black text-slate-900 mt-0.5">2,100 steps</div>
                <span className="text-xs text-slate-500 font-semibold">{t.activityDetail}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Connected Smart Hardware / IoT Device Hub */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                <Cpu className="w-6 h-6 text-[#278C78]" />
                {t.iotHeading}
              </h3>
              <p className="text-sm text-slate-500 mt-0.5">
                {t.iotSubtitle}
              </p>
            </div>
            <span className="text-xs font-semibold px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full flex items-center gap-1.5 self-start sm:self-center">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              {t.allOnline}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {t.devices.map((dev: any, idx: number) => (
              <div key={idx} className="p-5 rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-white transition shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Wifi className="w-4 h-4 text-emerald-600" />
                    <h4 className="font-bold text-slate-900 text-sm">{dev.name}</h4>
                  </div>
                  <span className="text-[11px] font-bold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded">
                    {dev.status}
                  </span>
                </div>

                <p className="text-xs text-slate-600">{dev.details}</p>

                <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-400">
                  <span>{t.location}: <strong className="text-slate-600">{dev.location}</strong></span>
                  <span>{t.power}: <strong className="text-slate-600">{dev.battery}</strong></span>
                  <span>{t.synced}: <strong className="text-slate-600">{dev.lastSync}</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Care Coordinator Contact & Reassurance */}
        <div className="bg-gradient-to-r from-[#173F35] to-[#278C78] rounded-3xl p-6 md:p-8 text-white shadow-md flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <span className="text-xs uppercase tracking-wider text-emerald-300 font-bold">
              SAHARA-AI &bull; Human-in-the-Loop Support
            </span>
            <h3 className="text-2xl font-bold">{t.supportTitle}</h3>
            <p className="text-sm text-emerald-100 max-w-xl">
              {t.supportText}
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <a
              href={`tel:+91${COORDINATOR_PHONE}`}
              className="px-6 py-3.5 bg-white text-[#173F35] font-extrabold rounded-2xl shadow hover:bg-emerald-50 transition flex items-center gap-2 active:scale-95"
            >
              <Phone className="w-4 h-4 text-[#278C78]" />
              <span>{t.callAnveshaCta}</span>
            </a>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
