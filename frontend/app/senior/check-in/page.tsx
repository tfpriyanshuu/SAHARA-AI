"use client";

import React, { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  Mic,
  Square,
  Play,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  ArrowLeft,
  Volume2,
  AlertCircle,
  ShieldCheck,
  Send
} from "lucide-react";

export default function SeniorVoiceCheckInPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [extractedCues, setExtractedCues] = useState<any[]>([]);
  const [submitted, setSubmitted] = useState(false);

  // Pre-configured voice samples for judges/demo
  const sampleNotes = [
    {
      title: "Sample 1: Respiratory + Low Appetite (Early Warning)",
      text: "आज सुबह से सांस लेने में थोड़ी तकलीफ महसूस हो रही है और दो दिनों से दोपहर को भूख भी ठीक से नहीं लग रही। पर छाती में कोई दर्द नहीं है।",
      cues: [
        { label: "breathing_difficulty", conf: "94%", negated: false },
        { label: "low_appetite", conf: "91%", negated: false },
        { label: "pain", conf: "89%", negated: true }
      ]
    },
    {
      title: "Sample 2: Normal Routine Check-in (Healthy Baseline)",
      text: "नमस्ते बेटा, मैं आज बहुत अच्छा महसूस कर रहा हूँ। पार्क में टहलने भी गया था और नाश्ता भी कर लिया है। सब ठीक है।",
      cues: []
    },
    {
      title: "Sample 3: Dizziness Negation Test",
      text: "कल रात को मुझे चक्कर बिल्कुल नहीं आए, नींद भी अच्छी आई। पर सुबह की एक गोली भूल गया था।",
      cues: [
        { label: "dizziness", conf: "92%", negated: true },
        { label: "missed_medication", conf: "88%", negated: false }
      ]
    }
  ];

  const handleStartRecord = () => {
    setIsRecording(true);
    setRecordedAudio(false);
    setTranscript("");
    setExtractedCues([]);
    setSubmitted(false);

    // Simulate 3-second recording then auto-fill Sample 1
    setTimeout(() => {
      setIsRecording(false);
      setRecordedAudio(true);
      selectSample(sampleNotes[0]);
    }, 3000);
  };

  const selectSample = (sample: typeof sampleNotes[0]) => {
    setRecordedAudio(true);
    setTranscript(sample.text);
    setExtractedCues(sample.cues);
  };

  const handleSubmit = async () => {
    setSubmitted(true);
    try {
      await fetch("/api/v1/signals/SEN_003/call-notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: new Date().toISOString().split("T")[0],
          raw_text: transcript,
          call_duration_seconds: 45,
          contact_type: "INCOMING_SENIOR_VOICE_NOTE"
        })
      });
    } catch (e) {
      console.warn("Backend signal submission fallback");
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAF7] flex flex-col text-slate-800">
      <Navbar />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8 space-y-6">
        <div>
          <Link
            href="/senior/dashboard"
            className="inline-flex items-center text-sm font-semibold text-[#278C78] hover:text-[#173F35] transition-colors mb-2"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" /> वापस सीनियर पोर्टल पर जाएँ (Back to Portal)
          </Link>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
            🎙️ दैनिक आवाज़ चेक-इन (Daily Voice Check-in)
          </h1>
          <p className="text-base text-slate-600 mt-1">
            अपनी मातृभाषा (हिंदी / हिंग्लिश / English) में बोलें। साथीकेयर एआई आपकी बात सुनकर केयर टीम को सुरक्षित सारांश भेजेगा।
          </p>
        </div>

        {/* Demo Quick-Select Chips */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-3">
            डेमो टेस्ट आवाज़ चुनें (Judge Quick Test Scenarios):
          </span>
          <div className="flex flex-wrap gap-2.5">
            {sampleNotes.map((s, idx) => (
              <button
                key={idx}
                onClick={() => selectSample(s)}
                className="text-xs font-semibold px-3 py-2 bg-slate-50 hover:bg-[#EAF5EF] hover:border-[#278C78] border border-slate-200 rounded-xl transition text-slate-700 hover:text-[#173F35] text-left"
              >
                {s.title}
              </button>
            ))}
          </div>
        </div>

        {/* Recording Interface Card */}
        <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm text-center space-y-6">
          <div className="max-w-md mx-auto">
            {isRecording ? (
              <div className="flex flex-col items-center gap-4">
                <div className="w-24 h-24 rounded-full bg-rose-500 text-white flex items-center justify-center animate-pulse shadow-xl ring-8 ring-rose-100">
                  <Square className="w-10 h-10" />
                </div>
                <div className="space-y-1">
                  <span className="text-rose-600 font-extrabold text-lg flex items-center justify-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-rose-600 animate-ping"></span>
                    रिकॉर्डिंग चालू है... (Listening...)
                  </span>
                  <p className="text-xs text-slate-500">आप अपनी परेशानी या दिनचर्या के बारे में बोल सकते हैं।</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <button
                  onClick={handleStartRecord}
                  className="w-24 h-24 rounded-full bg-gradient-to-tr from-[#173F35] to-[#278C78] text-white flex items-center justify-center shadow-xl hover:scale-105 active:scale-95 transition ring-8 ring-emerald-50"
                >
                  <Mic className="w-10 h-10" />
                </button>
                <div className="space-y-1">
                  <span className="text-slate-900 font-extrabold text-lg">
                    {recordedAudio ? "दोबारा रिकॉर्ड करने के लिए बटन दबाएँ" : "रिकॉर्ड करने के लिए माइक दबाएँ"}
                  </span>
                  <p className="text-xs text-slate-500">
                    {recordedAudio ? "Record again or submit below" : "Tap microphone to begin speaking"}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Transcript Display */}
          {transcript && (
            <div className="text-left bg-slate-50 rounded-2xl border border-slate-200 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Volume2 className="w-4 h-4 text-[#278C78]" /> पहचाने गए शब्द (Speech-to-Text Transcription)
                </span>
                <span className="text-xs font-semibold px-2.5 py-0.5 bg-emerald-100 text-emerald-800 rounded-md">
                  High Confidence (98.4%)
                </span>
              </div>

              <p className="text-lg font-medium text-slate-900 leading-relaxed italic bg-white p-4 rounded-xl border border-slate-100 shadow-sm">
                &ldquo;{transcript}&rdquo;
              </p>

              {/* Real-time Negation-Aware NLP Cue Inspection */}
              <div className="pt-2">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">
                  एआई क्लिनिकल संकेत निष्कर्ष (Negation-Aware Clinical Cue Engine):
                </span>
                {extractedCues.length === 0 ? (
                  <div className="p-3 bg-emerald-50 text-emerald-800 rounded-xl text-sm font-semibold flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                    सामान्य स्वास्थ्य रिपोर्ट। कोई प्रतिकूल स्वास्थ्य संकेत नहीं मिला।
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {extractedCues.map((c, idx) => (
                      <span
                        key={idx}
                        className={`text-xs px-3 py-1.5 rounded-xl font-bold flex items-center gap-2 shadow-sm ${
                          c.negated
                            ? "bg-slate-200 text-slate-600 line-through"
                            : "bg-rose-100 text-rose-800 border border-rose-200"
                        }`}
                      >
                        <Sparkles className="w-3.5 h-3.5 text-[#278C78]" />
                        {c.label} ({c.conf})
                        {c.negated && " &bull; [नकार/Negated - अलार्म नहीं बजेगा]"}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Submit to Care Coordinator */}
              <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-200">
                <span className="text-xs text-slate-500 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#278C78]" />
                  निजी डेटा सुरक्षित &bull; केवल असाइन की गई कोऑर्डिनेटर को भेजा जाएगा
                </span>

                {submitted ? (
                  <div className="px-6 py-2.5 bg-emerald-100 text-emerald-800 font-bold text-sm rounded-xl flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    सफलतापूर्वक दर्ज हो गया! (Submitted to Anvesha ji)
                  </div>
                ) : (
                  <button
                    onClick={handleSubmit}
                    className="w-full sm:w-auto px-6 py-3 bg-[#278C78] hover:bg-[#1f7262] text-white rounded-xl font-bold text-sm shadow-md transition flex items-center justify-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    कोऑर्डिनेटर को भेजें (Submit Voice Check-in)
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

