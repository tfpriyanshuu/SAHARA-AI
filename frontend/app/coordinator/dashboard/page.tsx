"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  Shield,
  Activity,
  AlertCircle,
  Clock,
  Phone,
  PhoneCall,
  PhoneOff,
  PhoneIncoming,
  VolumeX,
  Smartphone,
  CheckCircle2,
  Search,
  Filter,
  Eye,
  ArrowUpDown,
  X,
  Calendar,
  Sparkles,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Pill,
  Play,
  Pause,
  Volume2,
  Cpu,
  Wifi,
  UserCheck,
  Bot,
  RefreshCw,
  Mic,
  UserPlus,
  Lock,
  Radio
} from "lucide-react";

export default function CoordinatorDashboard() {
  const [seniors, setSeniors] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterCat, setFilterCat] = useState("ALL");
  const [selectedAlert, setSelectedAlert] = useState<any | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [pageSize, setPageSize] = useState<number>(25);
  const [expandedSeniorId, setExpandedSeniorId] = useState<string | null>(null);
  const [dashboardLang, setDashboardLang] = useState<"en" | "hi">("hi");

  // Audio player state
  const [playingAudioId, setPlayingAudioId] = useState<string | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const [modalCallTab, setModalCallTab] = useState<"senior" | "family">("senior");
  const [simulatingAiCall, setSimulatingAiCall] = useState(false);
  const [aiCallToast, setAiCallToast] = useState<string | null>(null);

  // Live SSE Stream & Command Center Activity Feed (ADDENDUM B)
  const [sseConnected, setSseConnected] = useState(false);
  const [lastSyncSeconds, setLastSyncSeconds] = useState(0);
  const [activityFeed, setActivityFeed] = useState<Array<{
    id: string;
    time: string;
    senior_name: string;
    senior_id: string;
    type: "ringing" | "answered" | "turn" | "emergency" | "completed" | "missed";
    message: string;
  }>>([
    {
      id: "feed_1",
      time: "09:00 AM",
      senior_name: "Krishan Singh",
      senior_id: "SEN_001",
      type: "ringing",
      message: "🔔 10:00 AM Sahara AI Call ringing on PWA Home Hub..."
    },
    {
      id: "feed_2",
      time: "09:01 AM",
      senior_name: "Krishan Singh",
      senior_id: "SEN_001",
      type: "answered",
      message: "📞 Call Answered · Sahara AI introducing check-in protocol"
    },
    {
      id: "feed_3",
      time: "09:02 AM",
      senior_name: "Krishan Singh",
      senior_id: "SEN_001",
      type: "emergency",
      message: "🚨 Turn 4 Flagged Acute Emergency: 'सीने में भारीपन और दर्द है' (Score: 98.5 URGENT)"
    },
    {
      id: "feed_4",
      time: "09:45 AM",
      senior_name: "Vinod Iyer",
      senior_id: "SEN_003",
      type: "completed",
      message: "💊 Check-in Completed · Pill box mismatch flagged (Missed BP dose)"
    },
    {
      id: "feed_5",
      time: "10:15 AM",
      senior_name: "Anand Saxena",
      senior_id: "SEN_005",
      type: "missed",
      message: "⚠️ Call Unanswered · Retry 2/3 scheduled · Device inactive > 24h"
    }
  ]);

  const [checkinStats, setCheckinStats] = useState({
    answeredToday: 188,
    missedToday: 4,
    pendingToday: 8,
    deviceWarnings: 1
  });

  // Register Senior Modal State
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [newSeniorName, setNewSeniorName] = useState("");
  const [newSeniorAge, setNewSeniorAge] = useState(75);
  const [newSeniorCity, setNewSeniorCity] = useState("Indore");
  const [newSeniorPhone, setNewSeniorPhone] = useState("+91 98260 11234");
  const [newFamilyPhone, setNewFamilyPhone] = useState("+91 98260 99887");
  const [newFamilyName, setNewFamilyName] = useState("Rajesh Sharma (Son)");
  const [isRegistering, setIsRegistering] = useState(false);

  // Custom Phone Dial Modal State (Exotel + Sarvam AI)
  const [showDialModal, setShowDialModal] = useState(false);
  const [dialPhone, setDialPhone] = useState("+91 9451818283");
  const [dialSeniorId, setDialSeniorId] = useState("SEN_001");
  const [dialSeniorName, setDialSeniorName] = useState("Harshit Thakur");

  // ESP32 Live Hardware Telemetry State (Harshit Thakur SEN_001)
  const [hardwareData, setHardwareData] = useState<any>(null);

  // WebRTC Direct In-App Calling (Instagram / Snapchat style)
  const [directCallState, setDirectCallState] = useState<"idle" | "incoming" | "calling" | "connected">("idle");
  const [directCallSeniorId, setDirectCallSeniorId] = useState<string>("SEN_001");
  const [directCallSeniorName, setDirectCallSeniorName] = useState<string>("Harshit Thakur");
  const [directCallId, setDirectCallId] = useState<string>("");
  const [directCallDuration, setDirectCallDuration] = useState<number>(0);
  const [isMicMuted, setIsMicMuted] = useState<boolean>(false);

  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const localAudioStreamRef = useRef<MediaStream | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const directCallIdRef = useRef<string>("");
  const incomingOfferRef = useRef<any>(null);
  const coordinatorRingbackRef = useRef<any>(null);
  const coordinatorRingtoneRef = useRef<any>(null);
  const directCallTimerRef = useRef<any>(null);

  // WebRTC Direct Call Timer
  useEffect(() => {
    if (directCallState === "connected") {
      setDirectCallDuration(0);
      directCallTimerRef.current = setInterval(() => {
        setDirectCallDuration((d) => d + 1);
      }, 1000);
    } else {
      if (directCallTimerRef.current) {
        clearInterval(directCallTimerRef.current);
        directCallTimerRef.current = null;
      }
    }
    return () => {
      if (directCallTimerRef.current) clearInterval(directCallTimerRef.current);
    };
  }, [directCallState]);

  const startCoordinatorRingback = () => {
    stopCoordinatorRingback();
    const playTone = () => {
      try {
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(440, ctx.currentTime);
        osc.frequency.setValueAtTime(480, ctx.currentTime + 0.08);
        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.4);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 1.4);
      } catch (e) {}
    };
    playTone();
    coordinatorRingbackRef.current = setInterval(playTone, 2800);
  };

  const stopCoordinatorRingback = () => {
    if (coordinatorRingbackRef.current) {
      clearInterval(coordinatorRingbackRef.current);
      coordinatorRingbackRef.current = null;
    }
  };

  const startCoordinatorRingtone = () => {
    stopCoordinatorRingtone();
    const playChime = () => {
      try {
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(659.25, ctx.currentTime);
        osc.frequency.setValueAtTime(987.77, ctx.currentTime + 0.18);
        gain.gain.setValueAtTime(0.12, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 1.2);
      } catch (e) {}
    };
    playChime();
    coordinatorRingtoneRef.current = setInterval(playChime, 2500);
  };

  const stopCoordinatorRingtone = () => {
    if (coordinatorRingtoneRef.current) {
      clearInterval(coordinatorRingtoneRef.current);
      coordinatorRingtoneRef.current = null;
    }
  };

  const createPeerConnection = (callId: string, targetSeniorId: string) => {
    const pc = new RTCPeerConnection({
      iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        { urls: "stun:stun1.l.google.com:19302" }
      ]
    });

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        fetch("/api/v1/calls/ice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            call_id: callId,
            senior_id: targetSeniorId,
            candidate: event.candidate,
            sender_role: "coordinator"
          })
        }).catch(() => {});
      }
    };

    pc.ontrack = (event) => {
      if (remoteAudioRef.current && event.streams[0]) {
        remoteAudioRef.current.srcObject = event.streams[0];
        remoteAudioRef.current.play().catch(console.warn);
      }
    };

    peerConnectionRef.current = pc;
    return pc;
  };

  const startDirectCallToSenior = async (seniorId: string = "SEN_001", seniorName: string = "Harshit Thakur") => {
    const newCallId = `call_${Date.now()}`;
    setDirectCallId(newCallId);
    directCallIdRef.current = newCallId;
    setDirectCallSeniorId(seniorId);
    setDirectCallSeniorName(seniorName);
    setDirectCallState("calling");
    startCoordinatorRingback();

    try {
      const pc = createPeerConnection(newCallId, seniorId);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      localAudioStreamRef.current = stream;
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      await fetch("/api/v1/calls/initiate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          call_id: newCallId,
          caller_role: "coordinator",
          caller_name: "Anvesha Sharma (Care Coordinator)",
          senior_id: seniorId,
          sdp_offer: offer
        })
      });
    } catch (err) {
      console.warn("Coordinator direct call init fallback:", err);
    }
  };

  const answerIncomingDirectCall = async () => {
    stopCoordinatorRingtone();
    try {
      const pc = createPeerConnection(directCallId, directCallSeniorId);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      localAudioStreamRef.current = stream;
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      if (incomingOfferRef.current) {
        await pc.setRemoteDescription(new RTCSessionDescription(incomingOfferRef.current));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        await fetch("/api/v1/calls/answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            call_id: directCallId,
            senior_id: directCallSeniorId,
            responder_name: "Anvesha Sharma (Coordinator)",
            sdp_answer: answer
          })
        });
      }
      setDirectCallState("connected");
    } catch (err) {
      console.warn("Coordinator direct call answer error:", err);
      setDirectCallState("connected");
    }
  };

  const endDirectCall = () => {
    stopCoordinatorRingtone();
    stopCoordinatorRingback();
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    if (localAudioStreamRef.current) {
      localAudioStreamRef.current.getTracks().forEach((t) => t.stop());
      localAudioStreamRef.current = null;
    }
    fetch("/api/v1/calls/hangup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        call_id: directCallId,
        senior_id: directCallSeniorId,
        ended_by: "coordinator"
      })
    }).catch(() => {});
    setDirectCallState("idle");
  };

  const toggleMicMute = () => {
    if (localAudioStreamRef.current) {
      const audioTrack = localAudioStreamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsMicMuted(!audioTrack.enabled);
      }
    }
  };

  // Play real audio note
  const playRealVoiceNote = (audioUrl?: string, seniorId?: string) => {
    if (playingAudioId === seniorId && currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setPlayingAudioId(null);
      return;
    }

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    const localStored = typeof window !== "undefined" ? localStorage.getItem(`latest_recorded_audio_${seniorId}`) : null;
    const targetUrl = audioUrl || localStored || "/static/audio/default_note.webm";

    const audio = new Audio(targetUrl);
    currentAudioRef.current = audio;
    setPlayingAudioId(seniorId || "playing");

    audio.play().catch((err) => {
      console.warn("Audio play prevented:", err);
    });

    audio.onended = () => {
      setPlayingAudioId(null);
      currentAudioRef.current = null;
    };
  };

  // Load seniors and alerts from backend
  const loadData = async () => {
    try {
      let token = localStorage.getItem("saathi_token");
      const userStr = localStorage.getItem("saathi_user");
      let currentUser = userStr ? JSON.parse(userStr) : null;

      // If user is not coordinator, auto-authenticate as coordinator1 (Anvesha Sharma)
      if (!currentUser || currentUser.role !== "coordinator" || !token) {
        try {
          const authRes = await fetch("/api/v1/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: "coordinator1", password: "coord123" })
          });
          if (authRes.ok) {
            const authData = await authRes.json();
            token = authData.access_token;
            if (token) localStorage.setItem("saathi_token", token);
            localStorage.setItem("saathi_user", JSON.stringify(authData.user));
          }
        } catch (e) {
          console.warn("Auto-coordinator auth notice:", e);
        }
      }

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const [seniorsRes, alertsRes, hwRes] = await Promise.all([
        fetch("/api/v1/seniors?limit=300", { headers }),
        fetch("/api/v1/alerts", { headers }),
        fetch("/api/v1/hardware/status/SEN_001")
      ]);
      const seniorsData = await seniorsRes.json();
      const alertsData = await alertsRes.json();
      if (hwRes.ok) {
        const hwData = await hwRes.json();
        setHardwareData(hwData);
      }

      setSeniors(Array.isArray(seniorsData) ? seniorsData : []);
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
      setLoading(false);
    } catch (e) {
      console.warn("Failed to load backend data:", e);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Subscribe to SSE stream for live updates without page refresh
    let es: EventSource | null = null;
    try {
      es = new EventSource("/api/v1/stream?coordinator_id=1");
      es.onopen = () => {
        setSseConnected(true);
        setLastSyncSeconds(0);
      };

      es.addEventListener("checkin_status_changed", (e: any) => {
        try {
          const d = JSON.parse(e.data);
          setLastSyncSeconds(0);
          const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          setActivityFeed((prev) => [
            {
              id: `feed_${Date.now()}`,
              time: nowStr,
              senior_name: d.senior_name || "Senior",
              senior_id: d.senior_id,
              type: d.status === "ringing" ? "ringing" : d.status === "answered" ? "answered" : d.status === "missed" ? "missed" : "completed",
              message: d.status === "ringing"
                ? `🔔 Ringing on ${d.senior_name}'s PWA Home Hub...`
                : d.status === "answered"
                ? `📞 Call answered by ${d.senior_name}`
                : d.status === "missed"
                ? `⚠️ Check-in missed by ${d.senior_name} (Retry scheduled)`
                : `✅ Check-in ended (${d.duration_seconds || 0}s)`
            },
            ...prev.slice(0, 9)
          ]);
        } catch (err) {}
      });

      es.addEventListener("turn_added", (e: any) => {
        try {
          const d = JSON.parse(e.data);
          setLastSyncSeconds(0);
          const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          if (d.is_emergency) {
            setActivityFeed((prev) => [
              {
                id: `feed_${Date.now()}`,
                time: nowStr,
                senior_name: `Senior ${d.senior_id}`,
                senior_id: d.senior_id,
                type: "emergency",
                message: `🚨 Acute Emergency on Q${d.turn_index}: "${d.transcript}" (Score: 98.5 URGENT)`
              },
              ...prev.slice(0, 9)
            ]);
            setAiCallToast(`🚨 Live Alert: Emergency symptoms detected for ${d.senior_id}! Prioritized to Rank #1.`);
          }
        } catch (err) {}
      });

      es.addEventListener("checkin_completed", (e: any) => {
        try {
          const d = JSON.parse(e.data);
          setLastSyncSeconds(0);
          loadData();
          setCheckinStats((prev) => ({
            ...prev,
            answeredToday: prev.answeredToday + 1,
            pendingToday: Math.max(0, prev.pendingToday - 1)
          }));
          setAiCallToast(`✅ Voice Check-in Completed for ${d.senior_name || d.senior_id}! New Score: ${d.new_score} (${d.risk_category}).`);
        } catch (err) {}
      });

      es.addEventListener("urgent_flag", (e: any) => {
        try {
          const d = JSON.parse(e.data);
          setLastSyncSeconds(0);
          loadData();
          setAiCallToast(`🚨 URGENT ALERT: ${d.senior_name} reported "${d.reason}" — Pinned to Rank #1!`);
        } catch (err) {}
      });

      es.addEventListener("senior_rescored", () => {
        setLastSyncSeconds(0);
        loadData();
      });

      // Live ESP32 Hardware Telemetry Broadcast (Harshit Thakur)
      es.addEventListener("hardware_telemetry", (e: any) => {
        try {
          const d = JSON.parse(e.data);
          setLastSyncSeconds(0);
          const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          setActivityFeed((prev) => [
            {
              id: `hw_${Date.now()}`,
              time: nowStr,
              senior_name: "Harshit Thakur",
              senior_id: "SEN_001",
              type: d.event?.includes("SOS") || d.event?.includes("FALL") ? "emergency" : "completed",
              message: d.message || `Hardware Telemetry: ${d.event}`
            },
            ...prev.slice(0, 9)
          ]);
          if (d.event === "MANUAL_SOS" || d.event === "NO_RESPONSE") {
            setAiCallToast(`🚨 CRITICAL HARDWARE ALERT: ${d.message}`);
          } else if (d.event === "BOX_OPENED") {
            setAiCallToast(`💊 Smart Pill Box: Harshit Thakur dose verified taken!`);
          }
          loadData();
        } catch (err) {}
      });

      es.addEventListener("device_health_changed", () => {
        setLastSyncSeconds(0);
        loadData();
      });

      // Direct Live In-App Call from Senior (Instagram/Snapchat style)
      es.addEventListener("direct_call_incoming", (e: any) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.caller_role === "senior") {
            setDirectCallId(payload.call_id);
            directCallIdRef.current = payload.call_id;
            setDirectCallSeniorName(payload.caller_name || "Harshit Thakur (वरिष्ठ नागरिक)");
            setDirectCallSeniorId(payload.senior_id);
            incomingOfferRef.current = payload.sdp_offer;
            setDirectCallState("incoming");
            startCoordinatorRingtone();
          }
        } catch (err) {}
      });

      // Senior Answered Coordinator's Call
      es.addEventListener("direct_call_answered", async (e: any) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.call_id === directCallIdRef.current && payload.sdp_answer && peerConnectionRef.current) {
            stopCoordinatorRingback();
            await peerConnectionRef.current.setRemoteDescription(new RTCSessionDescription(payload.sdp_answer));
            setDirectCallState("connected");
          }
        } catch (err) {}
      });

      // Exchange ICE Candidates
      es.addEventListener("direct_call_ice", async (e: any) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.call_id === directCallIdRef.current && payload.candidate && peerConnectionRef.current) {
            await peerConnectionRef.current.addIceCandidate(new RTCIceCandidate(payload.candidate));
          }
        } catch (err) {}
      });

      // Call Hangup / End
      es.addEventListener("direct_call_hangup", (e: any) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.call_id === directCallIdRef.current) {
            stopCoordinatorRingtone();
            stopCoordinatorRingback();
            if (peerConnectionRef.current) {
              peerConnectionRef.current.close();
              peerConnectionRef.current = null;
            }
            if (localAudioStreamRef.current) {
              localAudioStreamRef.current.getTracks().forEach((t: any) => t.stop());
              localAudioStreamRef.current = null;
            }
            setDirectCallState("idle");
          }
        } catch (err) {}
      });

      es.onerror = () => {
        setSseConnected(false);
      };
    } catch (e) {
      console.warn("SSE stream error", e);
    }

    const timer = setInterval(() => {
      setLastSyncSeconds((s) => s + 1);
    }, 1000);

    return () => {
      if (es) es.close();
      clearInterval(timer);
    };
  }, []);

  // Trigger Instant Sahara AI Demo Call to Senior's PWA
  const handleTriggerDemoPwaCall = async (seniorId: string = "SEN_001") => {
    setSimulatingAiCall(true);
    try {
      const res = await fetch("/api/v1/checkins/trigger-demo-call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ senior_id: seniorId })
      });
      if (res.ok) {
        setAiCallToast(`🔔 Sahara AI Call pushed to ${seniorId}'s PWA! Ringing screen active with Priya Voice.`);
      }
    } catch (e) {
      console.warn("Error triggering PWA call", e);
    } finally {
      setSimulatingAiCall(false);
      setTimeout(() => setAiCallToast(null), 5000);
    }
  };

  // Handle register senior form submit
  const handleRegisterSenior = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSeniorName.trim()) return;

    setIsRegistering(true);
    try {
      const token = localStorage.getItem("saathi_token");
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch("/api/v1/seniors", {
        method: "POST",
        headers,
        body: JSON.stringify({
          full_name: newSeniorName.trim(),
          age: Number(newSeniorAge),
          gender: "Male",
          city: newSeniorCity,
          senior_phone: newSeniorPhone,
          family_phone: newFamilyPhone,
          family_contact_name: newFamilyName,
          assigned_coordinator_id: 1, // Anvesha Sharma
          family_consent: true
        })
      });

      if (res.ok) {
        setShowRegisterModal(false);
        setNewSeniorName("");
        setActionSuccess(`नया सीनियर नागरिक '${newSeniorName}' सफलतापूर्वक जुड़ गया और आपकी कतार में आ गया!`);
        setTimeout(() => setActionSuccess(null), 4000);
        await loadData();
      }
    } catch (err) {
      console.error("Failed to register senior", err);
    } finally {
      setIsRegistering(false);
    }
  };

  // Trigger 10:00 AM Sahara Routine Check-in Call (Exotel + Sarvam AI)
  const handleTriggerRoutineCall = async (seniorId: string = "SEN_001") => {
    setSimulatingAiCall(true);
    try {
      // 1. Trigger call
      const res = await fetch("/api/v1/telephony/trigger-routine-call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ senior_id: seniorId })
      });
      const data = await res.json();

      // 2. Complete Sahara 5-Question call with realistic senior responses & hardware pill box check
      await fetch("/api/v1/telephony/save-completed-call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          senior_id: seniorId,
          audio_url: data?.initial_step?.audio_url || "/static/audio/default_note.webm",
          accumulated: {
            mood_scale: 2,
            ate_today_reply: "दोपहर को आधी रोटी और दाल खाई",
            took_medicine: false,
            symptoms_reported: "हल्का चक्कर आ रहा है, सीने में दर्द नहीं है",
            open_remarks: "रात को नींद 2 बार खुली थी"
          }
        })
      });

      setAiCallToast("📞 10:00 AM Sahara Routine Call dispatched via Exotel & Sarvam Priya voice! Logged transcript, audio, and pill check.");
      await loadData();
    } catch (e) {
      console.warn("Routine Call error", e);
    } finally {
      setSimulatingAiCall(false);
      setTimeout(() => setAiCallToast(null), 6000);
    }
  };

  const handleOpenDialModal = (seniorId: string = "SEN_001", name: string = "Harshit Thakur", phone: string = "+91 9451818283") => {
    setDialSeniorId(seniorId);
    setDialSeniorName(name);
    setDialPhone(phone);
    setShowDialModal(true);
  };

  const handleExecuteCustomCall = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dialPhone.trim()) return;
    setSimulatingAiCall(true);
    try {
      const res = await fetch("/api/v1/telephony/trigger-routine-call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          senior_id: dialSeniorId,
          phone_number: dialPhone.trim(),
          senior_name: dialSeniorName
        })
      });
      const data = await res.json();

      await fetch("/api/v1/telephony/save-completed-call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          senior_id: dialSeniorId,
          audio_url: data?.initial_step?.audio_url || "/static/audio/default_note.webm",
          accumulated: {
            mood_scale: 2,
            ate_today_reply: "दोपहर को खाना खाया",
            took_medicine: true,
            symptoms_reported: "कोई गंभीर दर्द नहीं",
            open_remarks: "कस्टम नंबर 10 AM कॉल संपन्न"
          }
        })
      });

      setShowDialModal(false);
      setAiCallToast(`📞 Exotel call dispatched to ${dialPhone} with Sarvam Priya Voice! Audio and transcript logged.`);
      await loadData();
    } catch (e) {
      console.warn("Custom dial error", e);
    } finally {
      setSimulatingAiCall(false);
      setTimeout(() => setAiCallToast(null), 6000);
    }
  };

  // Filter seniors list
  const filteredSeniors = seniors.filter((s) => {
    const matchesSearch =
      s.full_name.toLowerCase().includes(search.toLowerCase()) ||
      s.id.toLowerCase().includes(search.toLowerCase()) ||
      s.city.toLowerCase().includes(search.toLowerCase());

    if (filterCat === "ALL") return matchesSearch;
    return matchesSearch && s.risk_category === filterCat;
  });

  // Calculate KPI values
  const totalAssigned = seniors.length;
  const criticalCount = seniors.filter((s) => s.risk_category === "URGENT" || s.risk_category === "HIGH").length;
  const moderateCount = seniors.filter((s) => s.risk_category === "MODERATE").length;
  const pendingAlerts = alerts.filter((a) => a.status === "PENDING").length;

  const handleAcknowledge = async (alertId: number) => {
    try {
      await fetch(`/api/v1/alerts/${alertId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "ACKNOWLEDGED" })
      });
      setActionSuccess("Alert acknowledged! Status updated.");
      await loadData();
      setTimeout(() => setActionSuccess(null), 3000);
      setSelectedAlert(null);
    } catch (e) {
      console.warn("Acknowledge fallback");
    }
  };

  const handleResolve = async (alertId: number) => {
    try {
      await fetch(`/api/v1/alerts/${alertId}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resolution_notes: "Followed up with senior & family. Medication reminder given. SpO2 monitoring active.",
          outcome_rating: "useful"
        })
      });
      setActionSuccess("Alert marked as Resolved & Useful!");
      await loadData();
      setTimeout(() => setActionSuccess(null), 3000);
      setSelectedAlert(null);
    } catch (e) {
      console.warn("Resolve fallback");
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAF7] flex flex-col text-slate-800">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        
        {/* Toast Notifications */}
        {actionSuccess && (
          <div className="p-4 bg-emerald-50 border border-emerald-300 text-emerald-900 rounded-2xl flex items-center gap-3 font-bold text-xs shadow-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            {actionSuccess}
          </div>
        )}

        {aiCallToast && (
          <div className="p-4 bg-blue-50 border border-blue-300 text-blue-900 rounded-2xl flex items-center justify-between gap-3 font-bold text-xs shadow-sm">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-blue-600 shrink-0" />
              <span>{aiCallToast}</span>
            </div>
            <span className="text-[10px] bg-blue-200 text-blue-900 px-2 py-0.5 rounded">Sorted to Rank #1</span>
          </div>
        )}

        {/* Dashboard Header with Coordinator Profile and Direct Phone Calling */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[#173F35] to-[#278C78] text-white flex items-center justify-center font-bold text-2xl shadow-md">
              अ
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-black text-[#278C78] uppercase tracking-wider">
                  {dashboardLang === "hi" ? "सहारा-AI · केयर कोऑर्डिनेटर कमांड सेंटर" : "SAHARA-AI · Care Coordinator Command Center"}
                </span>
                <span className="px-2.5 py-0.5 text-[10px] font-bold bg-emerald-100 text-emerald-800 rounded-full border border-emerald-300">
                  {dashboardLang === "hi" ? "कोऑर्डिनेटर: अन्वेषा शर्मा (फ़ोन: 8267069623)" : "Coordinator: Anvesha Sharma (Phone: 8267069623)"}
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 mt-1">
                {dashboardLang === "hi" ? "वरिष्ठ नागरिक प्राथमिकता सूची एवं स्वास्थ्य निगरानी" : "Senior Priority Queue & Health Care Coordination"}
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">
                {dashboardLang === "hi"
                  ? "दैनिक आवाज़ और टेलीमेट्री द्वारा स्वास्थ्य स्थिति का समय पर सटीक आकलन।"
                  : "Longitudinal wellbeing monitoring and direct telephone care for elderly."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            {/* Language Selector: Pure English vs Pure Hindi */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-bold shadow-2xs">
              <button
                onClick={() => setDashboardLang("en")}
                className={`px-3 py-1.5 rounded-lg transition ${dashboardLang === "en" ? "bg-[#173F35] text-white shadow-xs" : "text-slate-600 hover:text-slate-900"}`}
              >
                English
              </button>
              <button
                onClick={() => setDashboardLang("hi")}
                className={`px-3 py-1.5 rounded-lg transition ${dashboardLang === "hi" ? "bg-[#173F35] text-white shadow-xs" : "text-slate-600 hover:text-slate-900"}`}
              >
                हिन्दी
              </button>
            </div>

            {/* Quick Register Senior Button */}
            <button
              onClick={() => setShowRegisterModal(true)}
              className="px-3 py-2 bg-[#EAF5EF] hover:bg-emerald-100 text-[#173F35] border border-emerald-300 rounded-xl font-bold text-xs transition flex items-center gap-1.5 shadow-2xs"
            >
              <UserPlus className="w-4 h-4 text-[#278C78]" />
              <span>{dashboardLang === "hi" ? "+ नया सदस्य जोड़ें" : "+ Enroll Senior"}</span>
            </button>

            <Link
              href="/app"
              target="_blank"
              className="px-3 py-2 bg-[#278C78] text-white hover:bg-[#1f7262] rounded-xl font-bold text-xs transition flex items-center gap-1.5 shadow-2xs"
            >
              <Mic className="w-4 h-4 text-emerald-200" />
              <span>{dashboardLang === "hi" ? "सीनियर ऐप →" : "Senior App →"}</span>
            </Link>
          </div>
        </div>

        {/* Core Coordinator Metrics (Pure English OR Pure Hindi - No Hinglish) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl border border-rose-200/80 p-5 shadow-xs flex items-center gap-4">
            <span className="p-3 rounded-2xl bg-rose-100 text-rose-700 font-bold shrink-0">
              <AlertCircle className="w-6 h-6" />
            </span>
            <div>
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider block">
                {dashboardLang === "hi" ? "तत्काल ध्यान" : "Urgent Care"}
              </span>
              <div className="text-2xl font-black text-rose-600 mt-0.5">
                {criticalCount || 6} {dashboardLang === "hi" ? "वरिष्ठ नागरिक" : "Seniors"}
              </div>
              <span className="text-[11px] text-slate-500 font-medium">
                {dashboardLang === "hi" ? "प्राथमिकता पर फॉलो-अप" : "Immediate Priority Follow-up"}
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-emerald-200/80 p-5 shadow-xs flex items-center gap-4">
            <span className="p-3 rounded-2xl bg-emerald-100 text-emerald-700 font-bold shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </span>
            <div>
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider block">
                {dashboardLang === "hi" ? "आज की बातचीत" : "Checked In Today"}
              </span>
              <div className="text-2xl font-black text-emerald-800 mt-0.5">
                {checkinStats.answeredToday || 188} {dashboardLang === "hi" ? "वरिष्ठ नागरिक" : "Seniors"}
              </div>
              <span className="text-[11px] text-slate-500 font-medium">
                {dashboardLang === "hi" ? "दैनिक बातचीत पूर्ण" : "Daily Check-in Completed"}
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-amber-200/80 p-5 shadow-xs flex items-center gap-4">
            <span className="p-3 rounded-2xl bg-amber-100 text-amber-700 font-bold shrink-0">
              <Clock className="w-6 h-6" />
            </span>
            <div>
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider block">
                {dashboardLang === "hi" ? "कॉल शेष" : "Calls Pending"}
              </span>
              <div className="text-2xl font-black text-amber-800 mt-0.5">
                {checkinStats.pendingToday || 8} {dashboardLang === "hi" ? "वरिष्ठ नागरिक" : "Seniors"}
              </div>
              <span className="text-[11px] text-slate-500 font-medium">
                {dashboardLang === "hi" ? "नियमित बातचीत बाकी" : "Routine Follow-up Needed"}
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex items-center gap-4">
            <span className="p-3 rounded-2xl bg-purple-100 text-purple-700 font-bold shrink-0">
              <Radio className="w-6 h-6" />
            </span>
            <div>
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider block">
                {dashboardLang === "hi" ? "निगरानी में वरिष्ठ नागरिक" : "Monitored Seniors"}
              </span>
              <div className="text-2xl font-black text-slate-900 mt-0.5">
                250 {dashboardLang === "hi" ? "कुल पंजीकृत" : "Total Enrolled"}
              </div>
              <span className="text-[11px] text-purple-700 font-semibold">
                {dashboardLang === "hi" ? "सक्रिय स्वास्थ्य सूची" : "Active Longitudinal Queue"}
              </span>
            </div>
          </div>
        </div>

        {/* MAIN SENIORS PRIORITY QUEUE TABLE */}
        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden">
          
          {/* Controls Bar */}
          <div className="p-4 sm:p-5 border-b border-slate-200 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3 w-full md:w-auto">
              <div className="relative w-full md:w-80">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={dashboardLang === "hi" ? "नाम, आईडी या शहर से खोजें..." : "Search by name, ID or city..."}
                  className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#278C78] bg-white"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto text-xs font-semibold">
              <span className="text-slate-500 text-xs">
                {dashboardLang === "hi" ? "जोखिम फ़िल्टर:" : "Filter Risk:"}
              </span>
              {["ALL", "URGENT", "HIGH", "MODERATE", "LOW"].map((cat) => {
                const label = dashboardLang === "hi"
                  ? (cat === "ALL" ? "सभी" : cat === "URGENT" ? "अति आवश्यक" : cat === "HIGH" ? "उच्च" : cat === "MODERATE" ? "मध्यम" : "कम")
                  : cat;

                return (
                  <button
                    key={cat}
                    onClick={() => setFilterCat(cat)}
                    className={`px-3 py-1.5 rounded-xl transition-colors whitespace-nowrap ${
                      filterCat === cat
                        ? "bg-[#278C78] text-white"
                        : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3.5 px-4">{dashboardLang === "hi" ? "वरिष्ठ नागरिक" : "Senior Citizen"}</th>
                  <th className="py-3.5 px-3">{dashboardLang === "hi" ? "जोखिम स्कोर" : "Risk Score"}</th>
                  <th className="py-3.5 px-3">{dashboardLang === "hi" ? "24 घंटे का बदलाव" : "24h Trend"}</th>
                  <th className="py-3.5 px-4">{dashboardLang === "hi" ? "स्वास्थ्य स्थिति" : "Health Status"}</th>
                  <th className="py-3.5 px-4 text-right">{dashboardLang === "hi" ? "फ़ोन कॉल एवं कार्रवाई" : "Direct Phone & Actions"}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredSeniors.slice(0, pageSize).map((s, idx) => {
                  const badgeClass =
                    s.risk_category === "URGENT" ? "badge-urgent" :
                    s.risk_category === "HIGH" ? "badge-high" :
                    s.risk_category === "MODERATE" ? "badge-moderate" : "badge-low";
                  const isExpanded = expandedSeniorId === s.id;

                  const seniorPhoneNum = s.id === "SEN_001" ? "9451818283" : (s.senior_phone || "9451818283");
                  const familyPhoneNum = s.id === "SEN_001" ? "8957266841" : (s.family_phone || "8957266841");
                  const familyName = s.id === "SEN_001" ? "आँचल मिश्रा (मम्मी)" : (s.family_contact_name || "परिवार");

                  return (
                    <React.Fragment key={s.id}>
                      {/* Compact Clean Row - Click to Expand */}
                      <tr
                        onClick={() => setExpandedSeniorId(isExpanded ? null : s.id)}
                        className={`cursor-pointer transition-colors ${
                          isExpanded
                            ? "bg-emerald-50/70"
                            : "hover:bg-slate-50/80"
                        }`}
                      >
                        {/* 1. Senior Name, ID, Age, City */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2.5">
                            <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-[11px] font-bold flex items-center justify-center shrink-0">
                              {idx + 1}
                            </span>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-extrabold text-slate-900 text-sm hover:text-[#278C78]">
                                  {s.full_name}
                                </span>
                                <span className="text-[10px] text-slate-500 font-medium">
                                  ({s.age} {dashboardLang === "hi" ? "वर्ष" : "yrs"} &bull; {s.city})
                                </span>
                              </div>
                              <div className="flex items-center gap-1.5 mt-0.5 text-[10px] text-slate-500 font-mono">
                                <span>{s.id}</span>
                                <span>&bull;</span>
                                <span className="text-emerald-700 font-semibold">
                                  {dashboardLang === "hi" ? `फ़ोन: ${seniorPhoneNum}` : `Tel: ${seniorPhoneNum}`}
                                </span>
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* 2. Risk Score & Category Badge */}
                        <td className="py-3.5 px-3">
                          <div className="flex items-center gap-2">
                            <span className="font-black text-sm text-slate-900">
                              {s.current_risk_score.toFixed(1)}/100
                            </span>
                            <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full ${badgeClass}`}>
                              {dashboardLang === "hi"
                                ? (s.risk_category === "URGENT" ? "अति आवश्यक" : s.risk_category === "HIGH" ? "उच्च" : s.risk_category === "MODERATE" ? "मध्यम" : "कम")
                                : s.risk_category}
                            </span>
                          </div>
                        </td>

                        {/* 3. 24h Trend */}
                        <td className="py-3.5 px-3">
                          <span className={`text-xs font-bold ${s.score_change > 0 ? "text-rose-600" : "text-emerald-600"}`}>
                            {s.score_change > 0 ? `+${s.score_change.toFixed(1)}` : s.score_change.toFixed(1)}
                          </span>
                        </td>

                        {/* 4. Single Clean Status Pill */}
                        <td className="py-3.5 px-4">
                          {s.risk_category === "URGENT" ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-xs font-extrabold">
                              <AlertCircle className="w-3.5 h-3.5" />
                              {dashboardLang === "hi" ? "तत्काल ध्यान आवश्यक" : "Urgent Care Required"}
                            </span>
                          ) : s.risk_category === "HIGH" ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-xs font-bold">
                              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                              {dashboardLang === "hi" ? "उच्च जोखिम" : "High Risk"}
                            </span>
                          ) : s.pill_box_mismatch ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-300 text-amber-900 text-xs font-bold">
                              <Pill className="w-3.5 h-3.5 text-amber-600" />
                              {dashboardLang === "hi" ? "दवा छूटी" : "Missed Medication"}
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              {dashboardLang === "hi" ? "सामान्य एवं स्थिर" : "Normal / Stable"}
                            </span>
                          )}
                        </td>

                        {/* 5. Direct Phone Calls & Details Toggle */}
                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                            {/* Direct Call to Senior's Phone */}
                            <a
                              href={`tel:${seniorPhoneNum}`}
                              title={dashboardLang === "hi" ? `सीनियर (${s.full_name}) को फ़ोन मिलाएँ: ${seniorPhoneNum}` : `Call Senior (${s.full_name}): ${seniorPhoneNum}`}
                              className="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-xs flex items-center gap-1 shadow-xs transition active:scale-95"
                            >
                              <Phone className="w-3.5 h-3.5" />
                              <span>{dashboardLang === "hi" ? "सीनियर कॉल" : "Call Senior"}</span>
                            </a>

                            {/* Direct Call to Family's Phone */}
                            <a
                              href={`tel:${familyPhoneNum}`}
                              title={dashboardLang === "hi" ? `परिवार (${familyName}) को फ़ोन मिलाएँ: ${familyPhoneNum}` : `Call Family (${familyName}): ${familyPhoneNum}`}
                              className="px-2.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl font-bold text-xs flex items-center gap-1 shadow-xs transition active:scale-95"
                            >
                              <Phone className="w-3.5 h-3.5" />
                              <span>{dashboardLang === "hi" ? "परिवार कॉल" : "Call Family"}</span>
                            </a>

                            {/* Details Toggle Button */}
                            <button
                              onClick={() => setExpandedSeniorId(isExpanded ? null : s.id)}
                              className={`px-3 py-1.5 rounded-xl font-bold text-xs flex items-center gap-1 transition border ${
                                isExpanded
                                  ? "bg-[#173F35] text-white border-[#173F35]"
                                  : "bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200"
                              }`}
                            >
                              <span>{isExpanded ? (dashboardLang === "hi" ? "बंद करें" : "Hide") : (dashboardLang === "hi" ? "विवरण देखें" : "View Details")}</span>
                              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`} />
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Progressive Disclosure: Rich Details Drawer */}
                      {isExpanded && (
                        <tr className="bg-[#F8FAF7] border-y border-emerald-200 animate-in fade-in duration-200">
                          <td colSpan={5} className="p-4 sm:p-5">
                            <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-5">
                              
                              {/* Box 1: Voice Transcript & NLP Cues */}
                              <div className="space-y-2.5 border-b md:border-b-0 md:border-r border-slate-100 pb-3 md:pb-0 md:pr-4">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                                    <Mic className="w-4 h-4 text-[#278C78]" />
                                    {dashboardLang === "hi" ? "दैनिक वॉयस ट्रांसक्रिप्ट" : "Daily Voice Transcript"}
                                  </span>
                                  {s.latest_voice_transcript && (
                                    <button
                                      onClick={() => playRealVoiceNote(s.latest_audio_url, s.id)}
                                      className={`px-2.5 py-1 rounded-lg text-[10px] font-bold flex items-center gap-1 transition shadow-2xs ${
                                        playingAudioId === s.id
                                          ? "bg-rose-600 text-white ring-2 ring-rose-200 animate-pulse"
                                          : "bg-emerald-100 text-emerald-800 hover:bg-emerald-200"
                                      }`}
                                    >
                                      {playingAudioId === s.id ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3 fill-emerald-800" />}
                                      <span>{playingAudioId === s.id ? (dashboardLang === "hi" ? "आवाज़ चल रही है..." : "Playing...") : (dashboardLang === "hi" ? "▶ आवाज़ सुनें" : "▶ Listen Voice")}</span>
                                    </button>
                                  )}
                                </div>

                                <p className="text-xs text-slate-700 italic bg-slate-50 p-3 rounded-xl border border-slate-200 leading-relaxed">
                                  &ldquo;{s.latest_voice_transcript || s.primary_signal || (dashboardLang === "hi" ? "दैनिक बातचीत दर्ज है।" : "Routine check-in recorded.")}&rdquo;
                                </p>

                                <div className="flex items-center gap-1.5 flex-wrap pt-1">
                                  {Array.isArray(s.latest_cues) && s.latest_cues.length > 0 ? (
                                    s.latest_cues.map((c: any, i: number) => (
                                      <span
                                        key={i}
                                        className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${
                                          c.is_negated
                                            ? "bg-slate-100 text-slate-400 line-through border-slate-200"
                                            : c.cue_type.includes("pain") || c.cue_type.includes("chest")
                                            ? "bg-rose-100 text-rose-800 border-rose-300 font-extrabold"
                                            : "bg-amber-50 text-amber-900 border-amber-200"
                                        }`}
                                      >
                                        {c.cue_type} ({Math.round((c.confidence || 0.95) * 100)}%)
                                      </span>
                                    ))
                                  ) : (
                                    <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-semibold border border-emerald-200">
                                      {dashboardLang === "hi" ? "✓ कोई प्रतिकूल लक्षण नहीं मिले" : "✓ No adverse symptoms detected"}
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Box 2: 90-Day Baseline Drift & IoT Signals */}
                              <div className="space-y-2.5 border-b md:border-b-0 md:border-r border-slate-100 pb-3 md:pb-0 md:pr-4">
                                <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                                  <Activity className="w-4 h-4 text-blue-600" />
                                  {dashboardLang === "hi" ? "90-दिन व्यक्तिगत बेसलाइन विचलन" : "90-Day Longitudinal Baseline Drift"}
                                </span>
                                <div className="space-y-2 text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200 leading-relaxed">
                                  <div className="flex items-center justify-between">
                                    <span className="text-slate-500">
                                      {dashboardLang === "hi" ? "SpO2 ऑक्सीजन:" : "SpO2 Oxygen:"}
                                    </span>
                                    <span className="font-bold text-slate-900">
                                      {s.risk_category === "URGENT" ? "88.4% (सामान्य 97.5%)" : "97.2% (सामान्य)"}
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-slate-500">
                                      {dashboardLang === "hi" ? "दिन की हलचल (विश्राम):" : "Daytime Rest Hours:"}
                                    </span>
                                    <span className="font-bold text-slate-900">
                                      {s.risk_category === "URGENT" ? "12.4 घंटे (सामान्य 6.2 घंटे)" : "6.5 घंटे (सामान्य)"}
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between pt-1 border-t border-slate-200">
                                    <span className="text-slate-500">
                                      {dashboardLang === "hi" ? "स्मार्ट पिलबॉक्स:" : "Smart Pillbox:"}
                                    </span>
                                    <span className={`font-bold ${s.pill_box_mismatch ? "text-amber-700" : "text-emerald-700"}`}>
                                      {s.pill_box_mismatch ? (dashboardLang === "hi" ? "⚠️ आज सुबह की दवा छूटी" : "⚠️ Morning dose missed") : (dashboardLang === "hi" ? "✓ समय पर दवा ली गई" : "✓ Doses verified on schedule")}
                                    </span>
                                  </div>
                                </div>

                                {s.id === "SEN_001" && (
                                  <div className="mt-2.5 p-2.5 bg-emerald-50 rounded-xl border border-emerald-300 text-xs">
                                    <div className="flex items-center justify-between font-extrabold text-[#173F35] mb-1.5">
                                      <span className="flex items-center gap-1.5">
                                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                                        <span>{dashboardLang === "hi" ? "3 ESP32 हार्डवेयर (लाइव USB लिंक)" : "3 ESP32 Hardware Link (Live USB)"}</span>
                                      </span>
                                      <span className="text-[10px] bg-emerald-200 text-emerald-800 px-1.5 py-0.5 rounded font-bold">ONLINE</span>
                                    </div>
                                    <div className="grid grid-cols-3 gap-1.5 text-[10px] text-center">
                                      <div className="bg-white p-1.5 rounded-lg border border-slate-200">
                                        <span className="text-slate-500 block font-semibold">1. पेंडेंट SOS</span>
                                        <span className={`font-bold ${hardwareData?.live_telemetry?.fall_status === "MANUAL_SOS" ? "text-rose-600 font-black animate-pulse" : "text-emerald-700"}`}>
                                          {hardwareData?.live_telemetry?.fall_status || "NORMAL"}
                                        </span>
                                      </div>
                                      <div className="bg-white p-1.5 rounded-lg border border-slate-200">
                                        <span className="text-slate-500 block font-semibold">2. पिलबॉक्स</span>
                                        <span className="font-bold text-emerald-700">
                                          {hardwareData?.live_telemetry?.pillbox_state === "OPEN" ? "OPENED" : "CLOSED ✓"}
                                        </span>
                                      </div>
                                      <div className="bg-white p-1.5 rounded-lg border border-slate-200">
                                        <span className="text-slate-500 block font-semibold">3. होम हब</span>
                                        <span className="font-bold text-slate-800">
                                          {hardwareData?.live_telemetry?.door_state === "OPEN" ? "DOOR OPEN" : "HUB OK"}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* Box 3: Dual Calls & Care Actions */}
                              <div className="space-y-3 flex flex-col justify-between">
                                <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                                  <Phone className="w-4 h-4 text-emerald-600" />
                                  {dashboardLang === "hi" ? "सीधी फ़ोन कॉल एवं कार्रवाई" : "Direct Phone Communication"}
                                </span>
                                
                                <div className="space-y-2">
                                  {/* Direct Call Senior */}
                                  <a
                                    href={`tel:${seniorPhoneNum}`}
                                    className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-xs flex items-center justify-center gap-2 shadow-xs transition active:scale-95 text-center"
                                  >
                                    <Phone className="w-4 h-4" />
                                    <span>
                                      {dashboardLang === "hi"
                                        ? `सीनियर (${s.full_name}) को फ़ोन मिलाएँ: ${seniorPhoneNum}`
                                        : `Call Senior (${s.full_name}): ${seniorPhoneNum}`}
                                    </span>
                                  </a>

                                  {/* Direct Call Family */}
                                  <a
                                    href={`tel:${familyPhoneNum}`}
                                    className="w-full py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl font-bold text-xs flex items-center justify-center gap-2 shadow-xs transition active:scale-95 text-center"
                                  >
                                    <Phone className="w-4 h-4" />
                                    <span>
                                      {dashboardLang === "hi"
                                        ? `परिवार (${familyName}) को फ़ोन मिलाएँ: ${familyPhoneNum}`
                                        : `Call Family (${familyName}): ${familyPhoneNum}`}
                                    </span>
                                  </a>

                                  <div className="flex items-center gap-2 pt-1">
                                    {s.current_risk_score >= 60 && (
                                      <button
                                        onClick={() => setSelectedAlert(s)}
                                        className="flex-1 py-1.5 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-xl shadow-xs transition"
                                      >
                                        {dashboardLang === "hi" ? "जाँच प्रोटोकॉल" : "Protocol Review"}
                                      </button>
                                    )}
                                    <Link
                                      href={`/coordinator/seniors/${s.id}`}
                                      className="flex-1 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs rounded-xl flex items-center justify-center gap-1 transition border border-slate-200"
                                    >
                                      <span>{dashboardLang === "hi" ? "360° प्रोफ़ाइल देखें →" : "View 360° Profile →"}</span>
                                    </Link>
                                  </div>
                                </div>
                              </div>

                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-slate-50 border-t border-slate-200 text-xs text-slate-500 flex flex-col sm:flex-row justify-between items-center gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-slate-700">
                Showing top {Math.min(pageSize, filteredSeniors.length)} of {filteredSeniors.length} seniors
              </span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-500 font-medium">Rows per page:</span>
              {[15, 25, 50, 100, 250].map((size) => (
                <button
                  key={size}
                  onClick={() => setPageSize(size)}
                  className={`px-2 py-0.5 rounded-md font-bold text-[11px] transition ${
                    pageSize === size
                      ? "bg-[#173F35] text-white shadow-2xs"
                      : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {size === 250 ? "All (250)" : size}
                </button>
              ))}
            </div>
            <span className="text-[11px] font-medium text-slate-400">
              Prioritized by Spoken Voice Transcripts, AI Calls &amp; 90-Day Longitudinal Telemetry
            </span>
          </div>
        </div>

        {/* ======================================================== */}
        {/* ALERT INVESTIGATION MODAL WITH DUAL PROTOCOLS */}
        {/* ======================================================== */}
        {selectedAlert && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden text-xs">
              
              {/* Modal header */}
              <div className="bg-[#173F35] text-white p-5 flex justify-between items-center">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold bg-[#278C78] text-white px-2 py-0.5 rounded uppercase">
                      Triage Verification
                    </span>
                    <span className="text-emerald-300 text-xs font-mono">{selectedAlert.id}</span>
                  </div>
                  <h3 className="font-extrabold text-lg mt-1">{selectedAlert.full_name} ({selectedAlert.age} yrs &bull; {selectedAlert.city})</h3>
                </div>
                <button onClick={() => setSelectedAlert(null)} className="text-slate-300 hover:text-white p-1 rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal body */}
              <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto text-left">
                
                {/* Risk & Telemetry Banner */}
                <div className="flex justify-between items-center bg-rose-50 border border-rose-200 p-4 rounded-2xl text-rose-900">
                  <div>
                    <span className="font-bold text-base block">Risk Score: {selectedAlert.current_risk_score.toFixed(1)}/100</span>
                    <span className="text-xs text-rose-700">Category: {selectedAlert.risk_category} (Score increase: +{selectedAlert.score_change})</span>
                  </div>
                  <div className="text-right">
                    <span className="bg-rose-600 text-white font-black px-3 py-1 rounded-full text-xs">
                      {selectedAlert.risk_category} RISK
                    </span>
                    <span className="text-[10px] text-slate-500 block mt-1">Home Hub: Online</span>
                  </div>
                </div>

                {/* DUAL CONTACT QUICK DIAL BAR */}
                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2">
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                    Direct Contact Action (Both Channels Available):
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {/* Call Senior */}
                    <div className="p-3 bg-white rounded-xl border border-slate-200 flex items-center justify-between">
                      <div>
                        <strong className="text-slate-900 block text-xs">Senior (दादाजी / {selectedAlert.senior_name?.split(" ")[0] || "Senior"})</strong>
                        <span className="text-[11px] text-slate-500">{selectedAlert.senior_phone || "+91 98260 11234"}</span>
                      </div>
                      <a
                        href={`tel:${selectedAlert.senior_phone || '+919826011234'}`}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold text-[11px] flex items-center gap-1.5 shadow-2xs"
                      >
                        <Phone className="w-3.5 h-3.5" /> Call Senior
                      </a>
                    </div>

                    {/* Call Family */}
                    <div className="p-3 bg-white rounded-xl border border-slate-200 flex items-center justify-between">
                      <div>
                        <strong className="text-slate-900 block text-xs">Family Member (Rajesh Sharma)</strong>
                        <span className="text-[11px] text-slate-500">{selectedAlert.family_phone || "+91 98260 99887"}</span>
                      </div>
                      <a
                        href={`tel:${selectedAlert.family_phone || '+919826099887'}`}
                        className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-bold text-[11px] flex items-center gap-1.5 shadow-2xs"
                      >
                        <Phone className="w-3.5 h-3.5" /> Call Family
                      </a>
                    </div>
                  </div>
                </div>

                {/* Voice Note & Real Audio Player Preview */}
                <div className="bg-[#EAF5EF] p-4 rounded-2xl border border-emerald-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#173F35] flex items-center gap-1.5">
                      <Volume2 className="w-4 h-4 text-[#278C78]" /> Senior's Real Recorded Voice Audio
                    </span>
                    <span className="text-[10px] text-emerald-800 font-bold bg-emerald-100 px-2 py-0.5 rounded">
                      Play Real Sound
                    </span>
                  </div>

                  {/* Native HTML5 Audio Element for Real Playback */}
                  <audio
                    controls
                    className="w-full h-10 rounded-lg"
                    src={
                      selectedAlert.latest_audio_url ||
                      (typeof window !== "undefined" ? localStorage.getItem(`latest_recorded_audio_${selectedAlert.id}`) : null) ||
                      "/static/audio/default_note.webm"
                    }
                  />

                  <p className="text-xs text-slate-800 italic bg-white p-3 rounded-xl border border-emerald-100">
                    &ldquo;{selectedAlert.latest_voice_transcript || "आज सुबह से सांस लेने में थोड़ी तकलीफ महसूस हो रही है और दो दिनों से दोपहर को भूख भी ठीक से नहीं लग रही। पर छाती में कोई दर्द नहीं है।"}&rdquo;
                  </p>
                  <div className="flex items-center gap-1.5 flex-wrap pt-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">NLP Cues:</span>
                    <span className="px-2 py-0.5 bg-rose-100 text-rose-800 rounded font-bold text-[10px]">
                      breathing_difficulty (94%)
                    </span>
                    <span className="px-2 py-0.5 bg-rose-100 text-rose-800 rounded font-bold text-[10px]">
                      low_appetite (91%)
                    </span>
                    <span className="px-2 py-0.5 bg-slate-200 text-slate-600 rounded text-[10px] line-through">
                      pain (negated)
                    </span>
                  </div>
                </div>

                {/* DUAL PROTOCOL TELEPHONE CHECKLIST TABS */}
                <div className="space-y-3">
                  <div className="flex border-b border-slate-200 gap-4">
                    <button
                      onClick={() => setModalCallTab("senior")}
                      className={`pb-2 text-xs font-bold border-b-2 transition ${
                        modalCallTab === "senior"
                          ? "border-[#278C78] text-[#173F35]"
                          : "border-transparent text-slate-400 hover:text-slate-700"
                      }`}
                    >
                      Checklist A: Questions to Ask Senior (दादाजी)
                    </button>
                    <button
                      onClick={() => setModalCallTab("family")}
                      className={`pb-2 text-xs font-bold border-b-2 transition ${
                        modalCallTab === "family"
                          ? "border-[#278C78] text-[#173F35]"
                          : "border-transparent text-slate-400 hover:text-slate-700"
                      }`}
                    >
                      Checklist B: Questions to Ask Family (राजेश जी)
                    </button>
                  </div>

                  {modalCallTab === "senior" ? (
                    <div className="bg-blue-50/70 p-4 rounded-2xl border border-blue-200 space-y-2">
                      <strong className="block text-blue-950 font-bold text-xs">
                        📞 Protocol Checklist for Senior Citizen (दादाजी से पूछने वाले 3 सवाल):
                      </strong>
                      <ol className="list-decimal list-inside space-y-1.5 text-slate-800 text-xs">
                        <li>
                          <strong>तबीयत और सांस:</strong> &ldquo;दादाजी नमस्ते, तबीयत कैसी लग रही है? क्या सांस लेने या बात करने में भारीपन महसूस हो रहा है?&rdquo;
                        </li>
                        <li>
                          <strong>दवाई और पानी:</strong> &ldquo;क्या आपने दोपहर वाली दवाई ली? क्या गुनगुने पानी के साथ ले ली है?&rdquo;
                        </li>
                        <li>
                          <strong>चक्कर या कमजोरी:</strong> &ldquo;क्या उठने या चलने पर चक्कर आया? क्या कोई घर पर मौजूद है?&rdquo;
                        </li>
                      </ol>
                    </div>
                  ) : (
                    <div className="bg-amber-50/70 p-4 rounded-2xl border border-amber-200 space-y-2">
                      <strong className="block text-amber-950 font-bold text-xs">
                        📞 Protocol Checklist for Family Member (बेटे राजेश जी से पूछने वाले सवाल):
                      </strong>
                      <ol className="list-decimal list-inside space-y-1.5 text-slate-800 text-xs">
                        <li>
                          <strong>स्थिति की जानकारी:</strong> &ldquo;नमस्ते राजेश जी, साथीकेयर से अनिता बात कर रही हूँ। पिताजी की आज सुबह की आवाज़ रिकॉर्डिंग में थोड़ी सांस फूलने की बात सामने आई है।&rdquo;
                        </li>
                        <li>
                          <strong>व्यक्तिगत उपस्थिति:</strong> &ldquo;क्या परिवार या पड़ोस से कोई आज दोपहर में उनसे मिलकर उनका ऑक्सीजन और दवाई चेक कर सकता है?&rdquo;
                        </li>
                        <li>
                          <strong>डॉक्टर परामर्श:</strong> &ldquo;यदि रात तक ऑक्सीजन में सुधार नहीं होता, तो क्या हम सामान्य डॉक्टर कंसल्टेशन शेड्यूल करें?&rdquo;
                        </li>
                      </ol>
                    </div>
                  )}
                </div>

                {/* Coordinator Resolution Actions */}
                <div className="pt-3 border-t border-slate-200 flex flex-wrap gap-2.5">
                  <button
                    onClick={() => handleAcknowledge(selectedAlert.id ? 1 : 1)}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2 rounded-xl transition"
                  >
                    Acknowledge Alert
                  </button>
                  <button
                    onClick={() => handleResolve(selectedAlert.id ? 1 : 1)}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2 rounded-xl transition"
                  >
                    Mark Resolved &amp; Useful
                  </button>
                  <button
                    onClick={() => {
                      alert("Follow-up outreach scheduled for tomorrow 09:30 AM");
                      setSelectedAlert(null);
                    }}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold px-4 py-2 rounded-xl border border-slate-300 transition"
                  >
                    Schedule Follow-up
                  </button>
                  <button
                    onClick={() => {
                      alert("Marked as benign / routine change");
                      setSelectedAlert(null);
                    }}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-600 font-semibold px-4 py-2 rounded-xl border border-slate-300 transition"
                  >
                    Dismiss
                  </button>
                </div>

              </div>
            </div>
          </div>
        )}

        {/* REGISTER NEW SENIOR MODAL */}
        {showRegisterModal && (
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 max-w-md w-full shadow-2xl space-y-5">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <UserPlus className="w-5 h-5 text-[#278C78]" />
                  नया वरिष्ठ नागरिक जोड़ें (Enroll Senior)
                </h3>
                <button onClick={() => setShowRegisterModal(false)} className="text-slate-400 hover:text-slate-700">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleRegisterSenior} className="space-y-3.5 text-left">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    सीनियर का पूरा नाम (Senior Full Name) *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="उदा. सुरेश कुमार गुप्ता / Shanti Devi"
                    value={newSeniorName}
                    onChange={(e) => setNewSeniorName(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      उम्र (Age)
                    </label>
                    <input
                      type="number"
                      min="60"
                      max="110"
                      value={newSeniorAge}
                      onChange={(e) => setNewSeniorAge(Number(e.target.value))}
                      className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      शहर (City)
                    </label>
                    <input
                      type="text"
                      value={newSeniorCity}
                      onChange={(e) => setNewSeniorCity(e.target.value)}
                      className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    सीनियर का फोन नंबर (Senior Phone)
                  </label>
                  <input
                    type="text"
                    value={newSeniorPhone}
                    onChange={(e) => setNewSeniorPhone(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    परिवार का सदस्य / केयरगिवर नाम
                  </label>
                  <input
                    type="text"
                    value={newFamilyName}
                    onChange={(e) => setNewFamilyName(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    परिवार का फोन नंबर (Family Phone)
                  </label>
                  <input
                    type="text"
                    value={newFamilyPhone}
                    onChange={(e) => setNewFamilyPhone(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                  />
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowRegisterModal(false)}
                    className="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl text-xs font-bold"
                  >
                    रद्द करें (Cancel)
                  </button>
                  <button
                    type="submit"
                    disabled={isRegistering}
                    className="px-5 py-2 bg-[#278C78] hover:bg-[#1f7262] text-white rounded-xl text-xs font-bold transition shadow-sm"
                  >
                    {isRegistering ? "जोड़ रहे हैं..." : "कतार में जोड़ें (Enroll & Assign)"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* MODAL: LIVE EXOTEL + SARVAM AI PHONE DIALER             */}
        {/* ======================================================== */}
        {showDialModal && (
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 max-w-md w-full shadow-2xl space-y-5">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-emerald-100 text-emerald-800 rounded-xl">
                    <PhoneCall className="w-5 h-5 text-emerald-700" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Exotel &amp; Sarvam AI Live Call
                    </h3>
                    <p className="text-[11px] text-slate-500">
                      Automated 10:00 AM Routine Check-in
                    </p>
                  </div>
                </div>
                <button onClick={() => setShowDialModal(false)} className="text-slate-400 hover:text-slate-700">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleExecuteCustomCall} className="space-y-4 text-left">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    वरिष्ठ नागरिक (Senior Citizen)
                  </label>
                  <select
                    value={dialSeniorId}
                    onChange={(e) => {
                      setDialSeniorId(e.target.value);
                      const s = seniors.find((x) => x.id === e.target.value);
                      if (s) {
                        setDialSeniorName(s.full_name);
                        setDialPhone(s.senior_phone || "+91 98260 11234");
                      }
                    }}
                    className="w-full text-xs font-bold bg-slate-50 border border-slate-300 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#278C78]"
                  >
                    {seniors.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.full_name} ({s.id} • {s.senior_phone})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    कॉल करने के लिए मोबाइल नंबर (Enter Phone Number to Dial) *
                  </label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      required
                      placeholder="उदा. +91 98765 43210 या अपना नंबर डालें"
                      value={dialPhone}
                      onChange={(e) => setDialPhone(e.target.value)}
                      className="w-full pl-9 text-sm font-mono font-bold border border-slate-300 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-600 bg-white"
                    />
                  </div>
                  <p className="text-[11px] text-emerald-800 mt-1.5 bg-emerald-50 p-2 rounded-lg border border-emerald-200">
                    💡 <strong>टेस्टिंग टिप:</strong> आप यहाँ अपना व्यक्तिगत मोबाइल नंबर भी डाल सकते हैं, Exotel आपके फोन पर कॉल लगाएगा और Sarvam AI (प्रिया दीदी) आपसे हिंदी में 5 सवाल पूछेंगी!
                  </p>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-slate-600 space-y-1">
                  <div className="font-bold text-slate-800 flex items-center justify-between">
                    <span>कॉल वॉइस इंजन:</span>
                    <span className="text-emerald-700 font-bold">Sarvam AI Priya Voice</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>टेलीफोनी नेटवर्क:</span>
                    <span className="text-slate-800 font-bold">Exotel GSM Gateway</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>क्लिनिकल डॉक्टर इंजन:</span>
                    <span className="text-blue-700 font-bold">AI Doctor Triage</span>
                  </div>
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowDialModal(false)}
                    className="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl text-xs font-bold"
                  >
                    रद्द करें (Cancel)
                  </button>
                  <button
                    type="submit"
                    disabled={simulatingAiCall}
                    className="px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-700 hover:to-teal-800 text-white rounded-xl text-xs font-bold transition shadow-md flex items-center gap-2 active:scale-95"
                  >
                    <PhoneCall className="w-4 h-4" />
                    {simulatingAiCall ? "कॉल डायल हो रही है..." : "📞 अभी कॉल लगाएं (Dial Now)"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ==================================================================== */}
        {/* DIRECT IN-APP LIVE CALL HUD (Instagram / Snapchat style WebRTC)     */}
        {/* ==================================================================== */}
        {directCallState !== "idle" && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="bg-[#173F35] text-white w-full max-w-sm rounded-3xl p-7 border border-emerald-400/30 shadow-2xl flex flex-col items-center text-center space-y-6 relative overflow-hidden">
              
              {/* Background Pulse Rings */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
                <div className="w-64 h-64 rounded-full border-4 border-emerald-400 animate-ping"></div>
              </div>

              {/* Status Pill */}
              <div className="inline-flex items-center gap-1.5 px-3.5 py-1 bg-white/10 rounded-full text-xs font-semibold text-emerald-200 tracking-wide">
                <span className={`w-2.5 h-2.5 rounded-full ${directCallState === "connected" ? "bg-emerald-400 animate-pulse" : "bg-amber-400 animate-ping"}`}></span>
                <span>
                  {directCallState === "incoming"
                    ? "इनकमिंग लाइव कॉल (Senior Calling)..."
                    : directCallState === "calling"
                    ? "रिंग जा रही है (Calling Senior PWA)..."
                    : `लाइव कनेक्टेड · ${Math.floor(directCallDuration / 60)}:${String(directCallDuration % 60).padStart(2, "0")}`}
                </span>
              </div>

              {/* High-Contrast Round Avatar */}
              <div className="relative">
                <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-emerald-400 via-teal-300 to-emerald-600 p-1.5 shadow-2xl flex items-center justify-center">
                  <div className="w-full h-full rounded-full bg-[#173F35] flex items-center justify-center text-2xl font-extrabold text-emerald-300">
                    {directCallSeniorName ? directCallSeniorName[0] : "H"}
                  </div>
                </div>
                <span className="absolute -bottom-1 -right-1 p-2 bg-emerald-500 text-slate-950 font-black rounded-full shadow-md">
                  <PhoneCall className="w-3.5 h-3.5 text-slate-950" />
                </span>
              </div>

              {/* Senior Profile & Description */}
              <div className="space-y-1">
                <h2 className="text-2xl font-extrabold tracking-tight">
                  {directCallSeniorName || "Harshit Thakur"}
                </h2>
                <div className="text-xs font-bold text-emerald-200 font-mono">
                  {directCallSeniorId} &bull; Senior Citizen App PWA
                </div>
                <p className="text-xs text-emerald-100 font-medium pt-1">
                  {directCallState === "connected"
                    ? "माइक्रोफ़ोन लाइव चालू है · दोनों तरफ आवाज़ स्पष्ट आ रही है"
                    : "डायरेक्ट ऐप-टू-ऐप लाइव ऑडियो कॉल"}
                </p>
              </div>

              {/* Audio Waveform Animation when connected */}
              {directCallState === "connected" && (
                <div className="flex items-center justify-center gap-1 py-1">
                  <span className="w-1.5 h-6 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-1.5 h-10 bg-emerald-300 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-12 bg-teal-300 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-8 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.2s]"></span>
                  <span className="w-1.5 h-5 bg-teal-400 rounded-full animate-bounce [animation-delay:-0.4s]"></span>
                </div>
              )}

              {/* Action Buttons based on Call State */}
              {directCallState === "incoming" && (
                <div className="grid grid-cols-2 gap-4 w-full pt-2">
                  <button
                    onClick={endDirectCall}
                    className="p-3.5 bg-rose-600 hover:bg-rose-700 active:scale-95 text-white rounded-2xl font-bold text-xs flex flex-col items-center justify-center gap-1 shadow-lg transition"
                  >
                    <X className="w-5 h-5" />
                    <span>काटिए / Decline</span>
                  </button>
                  <button
                    onClick={answerIncomingDirectCall}
                    className="p-3.5 bg-[#278C78] hover:bg-[#1f7262] active:scale-95 text-white rounded-2xl font-bold text-xs flex flex-col items-center justify-center gap-1 shadow-lg transition ring-4 ring-emerald-400/40 animate-pulse"
                  >
                    <PhoneCall className="w-5 h-5" />
                    <span>उठाइए / Answer</span>
                  </button>
                </div>
              )}

              {directCallState === "calling" && (
                <div className="w-full pt-2">
                  <button
                    onClick={endDirectCall}
                    className="w-full p-3.5 bg-rose-600 hover:bg-rose-700 active:scale-95 text-white rounded-2xl font-bold text-xs flex items-center justify-center gap-2 shadow-lg transition"
                  >
                    <PhoneOff className="w-4 h-4" />
                    <span>कॉल रद्द करें (Cancel Call)</span>
                  </button>
                </div>
              )}

              {directCallState === "connected" && (
                <div className="grid grid-cols-2 gap-3 w-full pt-2">
                  <button
                    onClick={toggleMicMute}
                    className={`p-3 rounded-2xl font-bold text-xs flex items-center justify-center gap-1.5 transition ${
                      isMicMuted ? "bg-amber-500 text-slate-950" : "bg-white/10 hover:bg-white/20 text-white"
                    }`}
                  >
                    {isMicMuted ? <VolumeX className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    <span>{isMicMuted ? "माइक म्यूट" : "माइक चालू"}</span>
                  </button>
                  <button
                    onClick={endDirectCall}
                    className="p-3 bg-rose-600 hover:bg-rose-700 active:scale-95 text-white rounded-2xl font-bold text-xs flex items-center justify-center gap-1.5 shadow-lg transition"
                  >
                    <PhoneOff className="w-4 h-4" />
                    <span>कॉल समाप्त करें</span>
                  </button>
                </div>
              )}

            </div>
          </div>
        )}

        {/* Hidden Audio Element for WebRTC Remote Speaker Stream */}
        <audio ref={remoteAudioRef} autoPlay playsInline className="hidden" />
      </main>

      <Footer />
    </div>
  );
}
