"use client";

import React, { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  Heart,
  Pill,
  CheckCircle2,
  Phone,
  AlertTriangle,
  Mic,
  Calendar,
  Smile,
  Meh,
  Frown,
  Languages,
  Clock,
  Shield,
  HelpCircle,
  Bell
} from "lucide-react";

export default function SeniorDashboard() {
  const [userName, setUserName] = useState("Harshit Thakur");
  const [lang, setLang] = useState<"hi" | "en">("hi");
  const [medsDone, setMedsDone] = useState<{ [key: string]: boolean }>({
    med1: true,
    med2: false,
    med3: false
  });
  const [checkinStatus, setCheckinStatus] = useState<string | null>(null);
  const [showSosModal, setShowSosModal] = useState(false);
  const [sosSent, setSosSent] = useState(false);

  React.useEffect(() => {
    try {
      const u = localStorage.getItem("saathi_user");
      if (u) {
        const parsed = JSON.parse(u);
        if (parsed.full_name) setUserName(parsed.full_name);
      }
    } catch {}
  }, []);

  const toggleMed = (id: string) => {
    setMedsDone((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleQuickCheckin = (status: string) => {
    setCheckinStatus(status);
  };

  const triggerSos = () => {
    setSosSent(true);
    setTimeout(() => {
      setShowSosModal(false);
      setSosSent(false);
    }, 4000);
  };

  return (
    <div className="min-h-screen bg-[#F8FAF7] flex flex-col text-slate-900 text-lg">
      <Navbar />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8 space-y-8">
        {/* Senior Welcome Banner & Language Selector */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-[#173F35] to-[#278C78] text-white flex items-center justify-center font-bold text-3xl shadow-md">
              {userName.charAt(0) || "H"}
            </div>
            <div>
              <span className="text-sm font-semibold uppercase tracking-wider text-[#278C78]">
                {lang === "hi" ? "साथीकेयर वरिष्ठ पोर्टल" : "SaathiCare Senior Citizen Portal"}
              </span>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 mt-1">
                {lang === "hi" ? `नमस्ते, ${userName.split(" ")[0]} जी! 🙏` : `Hello, ${userName.split(" ")[0]} Ji! 🙏`}
              </h1>
              <p className="text-base text-slate-600 mt-1">
                {lang === "hi"
                  ? "आज शुक्रवार है। आपकी सेहत की देखभाल के लिए हम हमेशा आपके साथ हैं।"
                  : "Today is Friday. We are always by your side for your health and peace of mind."}
              </p>
            </div>
          </div>

          {/* Language Switcher Button */}
          <div className="flex items-center gap-2 bg-slate-100 p-1.5 rounded-2xl shrink-0 self-start sm:self-center">
            <button
              onClick={() => setLang("hi")}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                lang === "hi" ? "bg-white text-[#173F35] shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              🇮🇳 हिंदी
            </button>
            <button
              onClick={() => setLang("en")}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                lang === "en" ? "bg-white text-[#173F35] shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              English
            </button>
          </div>
        </div>

        {/* ONE-BUTTON EASY VOICE APP BANNER */}
        <Link
          href="/senior/easy"
          className="group block p-6 bg-gradient-to-r from-[#173F35] to-[#278C78] text-white rounded-3xl shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-white/15 backdrop-blur-md flex items-center justify-center shrink-0 border border-white/20">
                <Mic className="w-8 h-8 text-emerald-300 animate-pulse" />
              </div>
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-300">
                  {lang === "hi" ? "नया: सिर्फ 1 बटन वाला आसान आवाज़ साथी" : "Dedicated: One-Button Easy Voice App"}
                </span>
                <h3 className="text-xl sm:text-2xl font-black mt-0.5">
                  {lang === "hi" ? "🎙️ बोलकर अपनी बात बताएं (One-Button Voice App)" : "🎙️ Speak Your Daily Update (One-Button App)"}
                </h3>
                <p className="text-xs text-emerald-100 mt-1">
                  {lang === "hi"
                    ? "सिर्फ एक बटन दबाएं और बोलें। आवाज़ और ट्रांसक्रिप्ट सीधे अन्वेषा जी (कोऑर्डिनेटर) के डैशबोर्ड पर पहुँचेगी।"
                    : "Tap one giant button, speak naturally in Hindi/English, and reach Anvesha ji instantly."}
                </p>
              </div>
            </div>
            <div className="px-5 py-3 bg-white text-[#173F35] font-extrabold text-sm rounded-2xl shadow-sm shrink-0 self-start sm:self-center group-hover:bg-emerald-50 transition">
              {lang === "hi" ? "आवाज़ ऐप खोलें &rarr;" : "Open Easy Voice App &rarr;"}
            </div>
          </div>
        </Link>

        {/* 1-Tap Daily Wellbeing Check-in */}
        <div className="bg-gradient-to-br from-[#EAF5EF] to-white rounded-3xl border border-emerald-200/70 p-6 md:p-8 shadow-sm">
          <h2 className="text-xl md:text-2xl font-bold text-[#173F35] mb-2 flex items-center gap-3">
            <Heart className="w-7 h-7 text-[#278C78]" />
            {lang === "hi" ? "आज आप कैसा महसूस कर रहे हैं?" : "How are you feeling today?"}
          </h2>
          <p className="text-base text-slate-600 mb-6">
            {lang === "hi"
              ? "बस एक बटन दबाकर हमें बताइए। आपका जवाब सीधे आपकी केयर कोऑर्डिनेटर अन्वेषा जी तक पहुंच जाएगा।"
              : "Just tap an option below. Your response goes directly to your Care Coordinator, Anvesha ji."}
          </p>

          {checkinStatus && (
            <div className="mb-6 p-4 bg-emerald-100/80 border border-emerald-300 text-emerald-900 font-bold rounded-2xl flex items-center gap-3">
              <CheckCircle2 className="w-6 h-6 text-emerald-700 shrink-0" />
              <span>
                {lang === "hi"
                  ? "धन्यवाद! आपका जवाब रिकॉर्ड हो गया है। अन्वेषा जी आपकी सेहत पर नजर रखे हुए हैं।"
                  : "Thank you! Your response is recorded. Anvesha ji is keeping watch on your wellbeing."}
              </span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <button
              onClick={() => handleQuickCheckin("good")}
              className={`p-5 rounded-2xl border-2 text-center transition-all flex flex-col items-center gap-3 ${
                checkinStatus === "good"
                  ? "border-emerald-600 bg-emerald-50 shadow-md ring-2 ring-emerald-400"
                  : "border-slate-200 bg-white hover:border-emerald-400 hover:bg-emerald-50/40"
              }`}
            >
              <Smile className="w-12 h-12 text-emerald-600" />
              <span className="font-extrabold text-slate-900 text-lg">
                {lang === "hi" ? "मैं बिल्कुल ठीक हूँ" : "I feel great"}
              </span>
              <span className="text-xs text-slate-500 font-medium">
                {lang === "hi" ? "कोई समस्या या दर्द नहीं" : "No pain or issues"}
              </span>
            </button>

            <button
              onClick={() => handleQuickCheckin("slight")}
              className={`p-5 rounded-2xl border-2 text-center transition-all flex flex-col items-center gap-3 ${
                checkinStatus === "slight"
                  ? "border-amber-600 bg-amber-50 shadow-md ring-2 ring-amber-400"
                  : "border-slate-200 bg-white hover:border-amber-400 hover:bg-amber-50/40"
              }`}
            >
              <Meh className="w-12 h-12 text-amber-600" />
              <span className="font-extrabold text-slate-900 text-lg">
                {lang === "hi" ? "थोड़ी परेशानी है" : "Slight discomfort"}
              </span>
              <span className="text-xs text-slate-500 font-medium">
                {lang === "hi" ? "थकान या कम भूख" : "Fatigue or low appetite"}
              </span>
            </button>

            <button
              onClick={() => handleQuickCheckin("need_talk")}
              className={`p-5 rounded-2xl border-2 text-center transition-all flex flex-col items-center gap-3 ${
                checkinStatus === "need_talk"
                  ? "border-indigo-600 bg-indigo-50 shadow-md ring-2 ring-indigo-400"
                  : "border-slate-200 bg-white hover:border-indigo-400 hover:bg-indigo-50/40"
              }`}
            >
              <Phone className="w-12 h-12 text-indigo-600" />
              <span className="font-extrabold text-slate-900 text-lg">
                {lang === "hi" ? "बात करनी है" : "Want to talk"}
              </span>
              <span className="text-xs text-slate-500 font-medium">
                {lang === "hi" ? "अन्वेषा जी आज कॉल करेंगी" : "Request a phone call"}
              </span>
            </button>
          </div>

          <div className="mt-6 pt-5 border-t border-emerald-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <span className="text-sm text-slate-600">
              {lang === "hi" ? "बोलकर अपनी बात बताना चाहते हैं?" : "Prefer speaking your daily update?"}
            </span>
            <Link
              href="/senior/check-in"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-[#173F35] text-white rounded-2xl font-bold text-base hover:bg-[#278C78] transition shadow-md"
            >
              <Mic className="w-5 h-5 text-emerald-400" />
              {lang === "hi" ? "🎙️ आवाज़ में चेक-इन करें" : "🎙️ Voice Check-in"}
            </Link>
          </div>
        </div>

        {/* Daily Medicine & Routine Checklist */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl md:text-2xl font-bold text-slate-900 flex items-center gap-3">
                <Pill className="w-7 h-7 text-emerald-600" />
                {lang === "hi" ? "आज की दवाइयां" : "Today's Medicines"}
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                {lang === "hi" ? "दवाई लेने के बाद बटन दबाकर टिक करें" : "Tap to check off after taking your medicine"}
              </p>
            </div>
            <span className="text-sm font-bold px-3 py-1 bg-emerald-50 text-emerald-800 rounded-full border border-emerald-200">
              {Object.values(medsDone).filter(Boolean).length}/3 {lang === "hi" ? "पूरी हुईं" : "Taken"}
            </span>
          </div>

          <div className="space-y-4">
            {[
              {
                id: "med1",
                nameHi: "एम्लोडिपिन 5mg (सुबह)",
                nameEn: "Amlodipine 5mg (Morning)",
                descHi: "ब्लड प्रेशर के लिए &bull; नाश्ते के बाद गुनगुने पानी से",
                descEn: "For BP &bull; After breakfast with warm water",
                time: "08:00 AM"
              },
              {
                id: "med2",
                nameHi: "मेटफॉर्मिन 500mg (दोपहर)",
                nameEn: "Metformin 500mg (Lunch)",
                descHi: "शुगर नियंत्रण के लिए &bull; दोपहर के भोजन के साथ",
                descEn: "For Sugar &bull; With afternoon lunch",
                time: "01:30 PM"
              },
              {
                id: "med3",
                nameHi: "एटोरवास्टेटिन 10mg (रात)",
                nameEn: "Atorvastatin 10mg (Night)",
                descHi: "हार्ट और कोलेस्ट्रॉल के लिए &bull; रात को सोने से पहले",
                descEn: "Cardiovascular health &bull; Before sleep",
                time: "09:00 PM"
              }
            ].map((med) => {
              const done = medsDone[med.id];
              return (
                <div
                  key={med.id}
                  onClick={() => toggleMed(med.id)}
                  className={`cursor-pointer p-5 rounded-2xl border-2 transition-all flex items-center justify-between gap-4 ${
                    done
                      ? "bg-emerald-50/70 border-emerald-300 text-slate-700"
                      : "bg-white border-slate-200 hover:border-slate-400"
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-8 h-8 rounded-xl border-2 flex items-center justify-center transition-all ${
                        done ? "bg-emerald-600 border-emerald-600 text-white" : "border-slate-300 bg-white"
                      }`}
                    >
                      {done && <CheckCircle2 className="w-5 h-5" />}
                    </div>
                    <div>
                      <h3 className={`text-lg font-bold ${done ? "line-through text-slate-500" : "text-slate-900"}`}>
                        {lang === "hi" ? med.nameHi : med.nameEn}
                      </h3>
                      <p className="text-sm text-slate-500 mt-0.5">{lang === "hi" ? med.descHi : med.descEn}</p>
                    </div>
                  </div>
                  <span className="text-sm font-semibold text-slate-600 bg-slate-100 px-3 py-1 rounded-xl shrink-0">
                    {med.time}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Assigned Coordinator Contact Card */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-[#EAF5EF] border border-[#278C78]/30 flex items-center justify-center text-[#173F35] font-black text-2xl">
              अ
            </div>
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                {lang === "hi" ? "आपकी केयर साथी" : "Your Dedicated Care Saathi"}
              </span>
              <h3 className="text-xl font-extrabold text-slate-900 mt-0.5">
                {lang === "hi" ? "अन्वेषा शर्मा" : "Anvesha Sharma"}
              </h3>
              <p className="text-sm text-slate-600">
                {lang === "hi"
                  ? "कोई भी परेशानी होने पर कभी भी बेझिझक कॉल करें।"
                  : "Feel free to call anytime if you feel unwell or need help."}
              </p>
            </div>
          </div>

          <a
            href="tel:+919826011234"
            className="px-6 py-3.5 bg-[#278C78] text-white rounded-2xl font-bold text-base hover:bg-[#1f7262] transition shadow-md flex items-center justify-center gap-2 shrink-0"
          >
            <Phone className="w-5 h-5" />
            {lang === "hi" ? "अन्वेषा जी को कॉल करें" : "Call Anvesha Ji"}
          </a>
        </div>

        {/* Big Emergency SOS Button */}
        <div className="pt-4">
          <button
            onClick={() => setShowSosModal(true)}
            className="w-full py-5 px-6 bg-rose-600 hover:bg-rose-700 text-white rounded-3xl font-black text-xl md:text-2xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-3 border-2 border-rose-700 active:scale-[0.99]"
          >
            <AlertTriangle className="w-8 h-8 animate-pulse" />
            {lang === "hi" ? "🚨 आपातकालीन मदद (SOS)" : "🚨 Emergency SOS Assistance"}
          </button>
          <p className="text-center text-xs text-slate-500 mt-2 font-medium">
            {lang === "hi"
              ? "दबाने पर तुरंत आपके बेटे राजेश जी और केयर कोऑर्डिनेटर अन्वेषा जी को इमरजेंसी अलर्ट जाएगा।"
              : "Pressing this immediately alerts your family (Rajesh ji) and Coordinator Anvesha ji."}
          </p>
        </div>
      </main>

      {/* SOS Confirmation Modal */}
      {showSosModal && (
        <div className="fixed inset-0 bg-slate-900/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8 shadow-2xl text-center border-4 border-rose-500 space-y-6">
            <div className="w-20 h-20 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
              <AlertTriangle className="w-12 h-12" />
            </div>

            {sosSent ? (
              <div className="space-y-3">
                <h3 className="text-2xl font-black text-slate-900">
                  {lang === "hi" ? "मदद रास्ते में है!" : "Help is on the way!"}
                </h3>
                <p className="text-sm text-slate-600">
                  {lang === "hi"
                    ? "आपके परिवार और कोऑर्डिनेटर अन्वेषा जी को तुरंत सूचना भेज दी गई है। फोन अपने पास रखें।"
                    : "Immediate notification sent to your family and Coordinator Anvesha ji. Keep your phone near you."}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <h3 className="text-2xl font-black text-slate-900">
                  {lang === "hi" ? "क्या आपको तुरंत मदद चाहिए?" : "Do you need urgent help?"}
                </h3>
                <p className="text-sm text-slate-600">
                  {lang === "hi"
                    ? "यह बटन दबाने पर आपकी कोऑर्डिनेटर और परिवार को आपातकालीन सूचना भेजी जाएगी।"
                    : "This will immediately notify your designated Care Coordinator and emergency family contact."}
                </p>

                <div className="flex flex-col gap-3 pt-2">
                  <button
                    onClick={triggerSos}
                    className="w-full py-4 bg-rose-600 text-white rounded-2xl font-extrabold text-lg shadow-md hover:bg-rose-700 transition"
                  >
                    {lang === "hi" ? "हाँ, तुरंत कॉल भेजें" : "Yes, Dispatch Urgent Alert"}
                  </button>
                  <button
                    onClick={() => setShowSosModal(false)}
                    className="w-full py-3 bg-slate-100 text-slate-700 rounded-2xl font-bold text-base hover:bg-slate-200 transition"
                  >
                    {lang === "hi" ? "नहीं, गलती से दब गया" : "Cancel (Pressed by mistake)"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}

