"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Mic,
  Square,
  Phone,
  PhoneOff,
  PhoneIncoming,
  Volume2,
  VolumeX,
  Heart,
  Pill,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Sparkles,
  Bot,
  User,
  ShieldAlert,
  ChevronDown,
  Download,
  Share2,
  Info,
  Check,
  X,
  Activity,
  ArrowRight,
  Bell
} from "lucide-react";

export default function SaharaDedicatedMobileApp() {
  // Navigation Tabs: 'checkin' | 'direct_call' | 'medicines' | 'sos'
  const [activeTab, setActiveTab] = useState<"checkin" | "direct_call" | "medicines" | "sos">("checkin");
  const [lang, setLang] = useState<"hi" | "en">("hi");

  // 1:30 PM Medicine Reminder Notification State
  const [med130Taken, setMed130Taken] = useState<boolean>(false);
  const [showMed130Modal, setShowMed130Modal] = useState<boolean>(false);

  // Seniors Data & Active Senior (Default: Harshit Thakur)
  const [seniorsList, setSeniorsList] = useState<any[]>([]);
  const [selectedSeniorId, setSelectedSeniorId] = useState<string>("SEN_001");
  const [selectedSenior, setSelectedSenior] = useState<any>({
    id: "SEN_001",
    full_name: "Harshit Thakur",
    age: 72,
    city: "Indore",
    coordinator_name: "Anvesha Sharma"
  });
  const [showSeniorPicker, setShowSeniorPicker] = useState<boolean>(false);

  // PWA Install State & Modal
  const [pwaPrompt, setPwaPrompt] = useState<any>(null);
  const [pwaInstalled, setPwaInstalled] = useState<boolean>(false);
  const [showInstallGuide, setShowInstallGuide] = useState<boolean>(false);

  // ====================================================================
  // WEBRTC DIRECT APP-TO-APP CALL STATE (Instagram / Snapchat style)
  // ====================================================================
  const [directCallState, setDirectCallState] = useState<"idle" | "incoming" | "calling" | "connected">("idle");
  const [directCallId, setDirectCallId] = useState<string>("");
  const [directCallerName, setDirectCallerName] = useState<string>("");
  const [directCallDuration, setDirectCallDuration] = useState<number>(0);
  const [isMicMuted, setIsMicMuted] = useState<boolean>(false);

  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const localAudioStreamRef = useRef<MediaStream | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const incomingOfferRef = useRef<any>(null);
  const directCallIdRef = useRef<string>("");
  const directCallTimerRef = useRef<any>(null);
  const ringtoneIntervalRef = useRef<any>(null);
  const ringbackIntervalRef = useRef<any>(null);

  // ====================================================================
  // CONVERSATIONAL AI CHECK-IN STATE (Sahara 5-Question Protocol)
  // ====================================================================
  const [aiCallActive, setAiCallActive] = useState<boolean>(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [accumulatedData, setAccumulatedData] = useState<any>({});
  const [agentSpeaking, setAgentSpeaking] = useState<boolean>(false);
  const [conversationHistory, setConversationHistory] = useState<Array<{ sender: "ai" | "senior"; text: string }>>([]);
  const [transcript, setTranscript] = useState<string>("");
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [sosTriggered, setSosTriggered] = useState<boolean>(false);

  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const silenceTimeoutRef = useRef<any>(null);
  const transcriptRef = useRef<string>("");
  const aiCallActiveRef = useRef<boolean>(false);
  const agentSpeakingRef = useRef<boolean>(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const currentStepIndexRef = useRef<number>(0);
  const accumulatedDataRef = useRef<any>({});
  const conversationHistoryRef = useRef<Array<{ sender: "ai" | "senior"; text: string }>>([]);
  const isSendingAnswerRef = useRef<boolean>(false);
  const lastAudioUrlRef = useRef<string>("");

  useEffect(() => {
    currentStepIndexRef.current = currentStepIndex;
  }, [currentStepIndex]);

  useEffect(() => {
    accumulatedDataRef.current = accumulatedData;
  }, [accumulatedData]);

  useEffect(() => {
    conversationHistoryRef.current = conversationHistory;
  }, [conversationHistory]);

  useEffect(() => {
    aiCallActiveRef.current = aiCallActive;
  }, [aiCallActive]);

  useEffect(() => {
    agentSpeakingRef.current = agentSpeaking;
  }, [agentSpeaking]);

  // Clean Hindi Speech for Web TTS so it never speaks "question mark"
  const cleanSpeechText = (text: string) => {
    return text
      .replace(/\?/g, "। ")
      .replace(/\!/g, "। ")
      .replace(/\*/g, "")
      .replace(/\"/g, "")
      .trim();
  };

  // Instant Full Stop: Stops all audio, browser TTS, recognition, and pending callbacks
  const stopAllAudioAndSession = () => {
    // 1. Immediately invalidate flags so callbacks ignore triggers
    aiCallActiveRef.current = false;
    agentSpeakingRef.current = false;
    setAiCallActive(false);
    setAgentSpeaking(false);
    setIsRecording(false);

    // 2. Clear any pending auto-submit / silence timers
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }

    // 3. Stop HTML5 audio player if running
    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
        currentAudioRef.current.onended = null;
        currentAudioRef.current.onerror = null;
        currentAudioRef.current.src = "";
      } catch (e) {}
      currentAudioRef.current = null;
    }

    // 4. Cancel browser SpeechSynthesis
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {}
    }

    // 5. Abort speech recognition immediately
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onresult = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.abort();
      } catch (e) {}
      recognitionRef.current = null;
    }

    setTranscript("");
    transcriptRef.current = "";
  };

  // Load Seniors from Backend
  useEffect(() => {
    async function loadSeniors() {
      try {
        const res = await fetch("/api/v1/seniors");
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setSeniorsList(data);
            const found = data.find((s: any) => s.id === "SEN_001") || data[0];
            setSelectedSenior(found);
            setSelectedSeniorId(found.id);
          }
        }
      } catch (err) {
        console.warn("Could not load dynamic seniors:", err);
      }
    }
    loadSeniors();
  }, []);

  // PWA Install Event Listener
  useEffect(() => {
    const handleBeforeInstall = (e: any) => {
      e.preventDefault();
      setPwaPrompt(e);
    };
    window.addEventListener("beforeinstallprompt", handleBeforeInstall);
    if (window.matchMedia("(display-mode: standalone)").matches) {
      setPwaInstalled(true);
    }
    return () => window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
  }, []);

  const triggerPwaInstall = () => {
    if (pwaPrompt) {
      pwaPrompt.prompt();
      pwaPrompt.userChoice.then((choice: any) => {
        if (choice.outcome === "accepted") setPwaInstalled(true);
        setPwaPrompt(null);
      });
    } else {
      setShowInstallGuide(true);
    }
  };

  // Audio Ringtones
  const startRingtone = () => {
    stopRingtone();
    const playChime = () => {
      try {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(587.33, ctx.currentTime);
        osc.frequency.setValueAtTime(880.00, ctx.currentTime + 0.2);
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 1.2);
      } catch (e) {}
    };
    playChime();
    ringtoneIntervalRef.current = setInterval(playChime, 2400);
  };

  const stopRingtone = () => {
    if (ringtoneIntervalRef.current) {
      clearInterval(ringtoneIntervalRef.current);
      ringtoneIntervalRef.current = null;
    }
  };

  const startRingback = () => {
    stopRingback();
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
    ringbackIntervalRef.current = setInterval(playTone, 2800);
  };

  const stopRingback = () => {
    if (ringbackIntervalRef.current) {
      clearInterval(ringbackIntervalRef.current);
      ringbackIntervalRef.current = null;
    }
  };

  // WebRTC Call Duration Timer
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

  // WebRTC PeerConnection Setup
  const createPeerConnection = (callId: string) => {
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
            senior_id: selectedSeniorId,
            candidate: event.candidate,
            sender_role: "senior"
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

  // Senior Calls Coordinator Directly (Instagram / Snapchat Style)
  const callCoordinatorDirectly = async () => {
    const newCallId = `call_${Date.now()}`;
    setDirectCallId(newCallId);
    directCallIdRef.current = newCallId;
    setDirectCallerName(`${selectedSenior?.coordinator_name || "अन्वेषा शर्मा"} (केयर दीदी)`);
    setDirectCallState("calling");
    startRingback();

    try {
      const pc = createPeerConnection(newCallId);
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
          caller_role: "senior",
          caller_name: `${selectedSenior?.full_name || "Harshit Thakur"} (वरिष्ठ नागरिक)`,
          senior_id: selectedSeniorId,
          sdp_offer: offer
        })
      });
    } catch (err) {
      console.warn("Direct call fallback:", err);
    }
  };

  // Senior Answers Direct Incoming Call
  const answerDirectCall = async () => {
    stopRingtone();
    try {
      const pc = createPeerConnection(directCallId);
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
            senior_id: selectedSeniorId,
            responder_name: selectedSenior?.full_name || "Harshit Thakur",
            sdp_answer: answer
          })
        });
      }
      setDirectCallState("connected");
    } catch (err) {
      console.warn("Direct call answer error:", err);
      setDirectCallState("connected");
    }
  };

  // Senior Ends Direct Call
  const endDirectCall = () => {
    stopRingtone();
    stopRingback();
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
        senior_id: selectedSeniorId,
        ended_by: "senior"
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

  // SSE Listener for Incoming In-App Calls from Coordinator
  useEffect(() => {
    let es: EventSource | null = null;
    try {
      es = new EventSource("/api/v1/stream");

      // Direct In-App Live Call from Coordinator
      es.addEventListener("direct_call_incoming", (e: any) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.senior_id === selectedSeniorId && payload.caller_role === "coordinator") {
            setDirectCallId(payload.call_id);
            directCallIdRef.current = payload.call_id;
            setDirectCallerName(payload.caller_name || "अन्वेषा शर्मा (केयर दीदी)");
            incomingOfferRef.current = payload.sdp_offer;
            setDirectCallState("incoming");
            startRingtone();
          }
        } catch (err) {}
      });

      // Coordinator Answered
      es.addEventListener("direct_call_answered", async (e: any) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.call_id === directCallIdRef.current && payload.sdp_answer && peerConnectionRef.current) {
            stopRingback();
            await peerConnectionRef.current.setRemoteDescription(new RTCSessionDescription(payload.sdp_answer));
            setDirectCallState("connected");
          }
        } catch (err) {}
      });

      // ICE exchange
      es.addEventListener("direct_call_ice", async (e: any) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.call_id === directCallIdRef.current && payload.candidate && peerConnectionRef.current) {
            await peerConnectionRef.current.addIceCandidate(new RTCIceCandidate(payload.candidate));
          }
        } catch (err) {}
      });

      // Hangup
      es.addEventListener("direct_call_hangup", (e: any) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.call_id === directCallIdRef.current) {
            stopRingtone();
            stopRingback();
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
    } catch (e) {
      console.warn("SSE error:", e);
    }

    return () => {
      if (es) es.close();
      stopRingtone();
      stopRingback();
    };
  }, [selectedSeniorId]);

  // Play audio from Sarvam AI with clean browser TTS fallback (Strict Single-Voice Guard)
  const playAgentSpeech = (text: string, audioUrl?: string | null, onEnd?: () => void) => {
    if (!aiCallActiveRef.current) return;

    // 1. Immediately kill any playing audio element to prevent overlapping voices
    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
        currentAudioRef.current.onended = null;
        currentAudioRef.current.onerror = null;
        currentAudioRef.current.src = "";
      } catch (e) {}
      currentAudioRef.current = null;
    }

    // 2. Cancel any pending speech synthesis immediately
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      try { window.speechSynthesis.cancel(); } catch (e) {}
    }

    setAgentSpeaking(true);
    agentSpeakingRef.current = true;
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (e) {}
    }

    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.playbackRate = 1.08;
      currentAudioRef.current = audio;

      audio.onended = () => {
        currentAudioRef.current = null;
        setAgentSpeaking(false);
        agentSpeakingRef.current = false;
        if (!aiCallActiveRef.current) return;
        if (onEnd) onEnd();
      };

      audio.onerror = () => {
        currentAudioRef.current = null;
        setAgentSpeaking(false);
        agentSpeakingRef.current = false;
        if (!aiCallActiveRef.current) return;
        speakBrowserTts(text, onEnd);
      };

      audio.play().catch(() => {
        currentAudioRef.current = null;
        if (!aiCallActiveRef.current) return;
        speakBrowserTts(text, onEnd);
      });
    } else {
      speakBrowserTts(text, () => {
        setAgentSpeaking(false);
        agentSpeakingRef.current = false;
        if (!aiCallActiveRef.current) return;
        if (onEnd) onEnd();
      });
    }
  };

  const speakBrowserTts = (text: string, onEnd?: () => void) => {
    if (!aiCallActiveRef.current) return;
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      if (onEnd && aiCallActiveRef.current) onEnd();
      return;
    }

    try {
      window.speechSynthesis.cancel();
    } catch (e) {}

    const utterance = new SpeechSynthesisUtterance(cleanSpeechText(text));
    utterance.lang = "hi-IN";
    utterance.rate = 1.05;
    const voices = window.speechSynthesis.getVoices();
    const hiVoice = voices.find((v) => v.lang.includes("hi") || v.lang.includes("IN"));
    if (hiVoice) utterance.voice = hiVoice;

    utterance.onend = () => {
      setAgentSpeaking(false);
      agentSpeakingRef.current = false;
      if (!aiCallActiveRef.current) return;
      if (onEnd) onEnd();
    };

    utterance.onerror = (e: any) => {
      setAgentSpeaking(false);
      agentSpeakingRef.current = false;
      // Do NOT trigger onEnd if canceled or session was ended
      if (!aiCallActiveRef.current || e.error === "canceled" || e.error === "interrupted") {
        return;
      }
      if (onEnd) onEnd();
    };

    window.speechSynthesis.speak(utterance);
  };

  // Hands-free Real Microphone Listening (Fine-Tuned Speech-to-Text)
  const startHandsfreeListening = async () => {
    if (!aiCallActiveRef.current || agentSpeakingRef.current) return;
    try {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognition) return;

      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
      }

      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.continuous = false; // Turn-based listening prevents ghost looping
      recognition.interimResults = true;
      recognition.lang = "hi-IN";

      recognition.onresult = (event: any) => {
        if (!aiCallActiveRef.current || agentSpeakingRef.current) return;
        let interim = "";
        let final = "";
        for (let i = 0; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        const spoken = (final || interim).trim();
        if (spoken) {
          transcriptRef.current = spoken;
          setTranscript(spoken);

          // Auto-submit after 1.5s pause
          if (silenceTimeoutRef.current) clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = setTimeout(() => {
            if (aiCallActiveRef.current && !agentSpeakingRef.current && transcriptRef.current.trim()) {
              sendSeniorAnswer();
            }
          }, 1500);
        }
      };

      recognition.onend = () => {
        setIsRecording(false);
        if (!aiCallActiveRef.current) return;
        if (!agentSpeakingRef.current) {
          if (transcriptRef.current.trim()) {
            sendSeniorAnswer();
          } else {
            // Keep listening if call is active and nothing was spoken yet
            try { recognition.start(); } catch (e) {}
          }
        }
      };

      recognition.onerror = (err: any) => {
        if (err.error === "no-speech" && aiCallActiveRef.current && !agentSpeakingRef.current) {
          try { recognition.start(); } catch (e) {}
        }
      };

      recognition.start();
      setIsRecording(true);
    } catch (e) {
      console.warn("Mic listen warning:", e);
    }
  };

  const stopHandsfreeListening = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (e) {}
      recognitionRef.current = null;
    }
    setIsRecording(false);
  };

  // Start Conversational AI Check-in Call
  const startAiCheckinCall = async () => {
    stopAllAudioAndSession();
    setAiCallActive(true);
    aiCallActiveRef.current = true;
    setCurrentStepIndex(0);
    currentStepIndexRef.current = 0;
    setAccumulatedData({});
    accumulatedDataRef.current = {};
    setConversationHistory([]);
    conversationHistoryRef.current = [];
    setTranscript("");
    transcriptRef.current = "";

    try {
      const res = await fetch("/api/v1/telephony/routine-step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          senior_id: selectedSeniorId,
          step_index: 0
        })
      });

      if (res.ok && aiCallActiveRef.current) {
        const data = await res.json();
        const nextIdx = data.next_step_index || 1;
        setCurrentStepIndex(nextIdx);
        currentStepIndexRef.current = nextIdx;
        accumulatedDataRef.current = data.accumulated || {};
        setAccumulatedData(data.accumulated || {});
        if (data.audio_url) lastAudioUrlRef.current = data.audio_url;

        const initialHistory = [{ sender: "ai" as const, text: data.agent_question }];
        setConversationHistory(initialHistory);
        conversationHistoryRef.current = initialHistory;

        playAgentSpeech(data.agent_question, data.audio_url, () => {
          if (!aiCallActiveRef.current) return;
          setTimeout(() => {
            if (!aiCallActiveRef.current) return;
            setTranscript("");
            transcriptRef.current = "";
            startHandsfreeListening();
          }, 300);
        });
      }
    } catch (e) {
      console.warn("AI checkin error:", e);
    }
  };

  // Send Senior Answer (Spoken or 1-Tap Digit)
  const sendSeniorAnswer = async (forcedDigit?: string) => {
    if (!aiCallActiveRef.current || isSendingAnswerRef.current) return;

    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    stopHandsfreeListening();

    const rawSpoken = transcriptRef.current.trim() || transcript.trim();
    if (!forcedDigit && !rawSpoken) {
      if (aiCallActiveRef.current && !agentSpeakingRef.current) {
        startHandsfreeListening();
      }
      return;
    }

    isSendingAnswerRef.current = true;

    const seniorAnswer = forcedDigit
      ? (forcedDigit === "1" ? "1 - अच्छा" : forcedDigit === "2" ? "2 - ठीक-ठाक" : "3 - अच्छा नहीं")
      : rawSpoken;

    const updatedHistory = [...conversationHistoryRef.current, { sender: "senior" as const, text: seniorAnswer }];
    setConversationHistory(updatedHistory);
    conversationHistoryRef.current = updatedHistory;
    setTranscript("");
    transcriptRef.current = "";

    try {
      const stepToSend = currentStepIndexRef.current || 1;
      const res = await fetch("/api/v1/telephony/routine-step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          senior_id: selectedSeniorId,
          step_index: stepToSend,
          user_reply: seniorAnswer,
          dtmf_digit: forcedDigit || undefined,
          accumulated: accumulatedDataRef.current
        })
      });

      if (res.ok && aiCallActiveRef.current) {
        const data = await res.json();
        const nextIdx = data.next_step_index || (stepToSend + 1);
        setCurrentStepIndex(nextIdx);
        currentStepIndexRef.current = nextIdx;
        accumulatedDataRef.current = data.accumulated || {};
        setAccumulatedData(data.accumulated || {});
        if (data.audio_url) lastAudioUrlRef.current = data.audio_url;

        const nextHistory = [...conversationHistoryRef.current, { sender: "ai" as const, text: data.agent_question }];
        setConversationHistory(nextHistory);
        conversationHistoryRef.current = nextHistory;

        playAgentSpeech(data.agent_question, data.audio_url, () => {
          isSendingAnswerRef.current = false;
          if (!aiCallActiveRef.current) return;
          if (data.is_emergency) {
            stopAllAudioAndSession();
            // Instantly save emergency call to coordinator
            fetch("/api/v1/telephony/save-completed-call", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                senior_id: selectedSeniorId,
                accumulated: data.accumulated || accumulatedDataRef.current,
                audio_url: data.audio_url || lastAudioUrlRef.current,
                is_emergency: true
              })
            }).catch(() => {});

            alert(
              lang === "hi"
                ? "🚨 आपातकालीन लक्षण दर्ज! अन्वेषा दीदी और आँचल जी को तुरंत सूचना भेज दी गई है।"
                : "🚨 Acute Symptoms Flagged! Care Coordinator Anvesha Sharma alerted immediately."
            );
          } else if (!data.is_complete) {
            setTimeout(() => {
              if (!aiCallActiveRef.current) return;
              setTranscript("");
              transcriptRef.current = "";
              startHandsfreeListening();
            }, 300);
          } else {
            stopAllAudioAndSession();
            // Save completed call with full dialogue transcript to coordinator
            fetch("/api/v1/telephony/save-completed-call", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                senior_id: selectedSeniorId,
                accumulated: data.accumulated || accumulatedDataRef.current,
                audio_url: data.audio_url || lastAudioUrlRef.current
              })
            }).catch(() => {});
          }
        });
      } else {
        isSendingAnswerRef.current = false;
      }
    } catch (e) {
      console.warn("Turn error:", e);
      isSendingAnswerRef.current = false;
    }
  };

  // Trigger Immediate SOS
  const handleTriggerSos = async () => {
    setSosTriggered(true);
    speakBrowserTts(
      lang === "hi"
        ? "दादाजी, आप बिल्कुल घबराइए मत। मैंने अन्वेषा दीदी, आपकी मम्मी आँचल मिश्रा और डॉक्टर को तुरंत अलर्ट भेज दिया है। आप आराम से बैठ जाइए।"
        : "Please remain calm. An emergency alert has been sent to Care Coordinator Anvesha Sharma and Mummy Anchal Mishra."
    );

    fetch("/api/v1/telephony/routine-step", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        senior_id: selectedSeniorId,
        step_index: 4,
        user_reply: "सीने में तेज दर्द है और बहुत चक्कर आ रहा है तुरंत मदद चाहिए"
      })
    }).catch(console.warn);

    setTimeout(() => {
      alert(
        lang === "hi"
          ? "🚨 SOS आपातकालीन अलर्ट दर्ज! अन्वेषा शर्मा (केयर कोऑर्डिनेटर) के डैशबोर्ड पर आपका नाम Rank #1 पर लाल रंग में फ्लैश हो रहा है।"
          : "🚨 Emergency SOS Recorded! Flashing at Priority #1 on Care Coordinator Anvesha Sharma's dashboard."
      );
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-[#F2F6F3] text-slate-900 flex justify-center selection:bg-emerald-100">
      {/* Remote Audio Player for WebRTC Call */}
      <audio ref={remoteAudioRef} autoPlay playsInline className="hidden" />

      {/* MOBILE APP CONTAINER - Strictly App Form Factor */}
      <div className="w-full max-w-md min-h-screen bg-white flex flex-col justify-between shadow-2xl relative border-x border-slate-200/80">
        
        {/* ======================================================== */}
        {/* TOP NATIVE APP BAR (Status, Persona, Live Indicators)    */}
        {/* ======================================================== */}
        <header className="sticky top-0 z-30 bg-[#173F35] text-white px-3.5 pt-3 pb-3 shadow-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Link
                href="/"
                className="bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-2 py-1.5 rounded-xl flex items-center gap-1 transition active:scale-95 border border-white/10 shrink-0"
                title={lang === "hi" ? "मुख्य पृष्ठ पर वापस जाएँ" : "Go to Home"}
              >
                <span>{lang === "hi" ? "← होम" : "← Home"}</span>
              </Link>
              <div className="w-7 h-7 rounded-full bg-emerald-500/20 border border-emerald-400 flex items-center justify-center shrink-0">
                <Heart className="w-3.5 h-3.5 text-emerald-300 fill-emerald-300" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-black text-sm tracking-wide text-white">SAHARA-AI</span>
                  <span className="bg-emerald-400/20 text-emerald-300 text-[9px] font-bold px-1.5 py-0.2 rounded-full border border-emerald-400/30">
                    {lang === "hi" ? "ऐप" : "App"}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[10px] text-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>{lang === "hi" ? "ऑनलाइन • सुरक्षित" : "Online · Secure"}</span>
                </div>
              </div>
            </div>

            {/* Install App Button / Language Switch */}
            <div className="flex items-center gap-1.5">
              {!pwaInstalled && (
                <button
                  onClick={triggerPwaInstall}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold px-2 py-1.5 rounded-xl flex items-center gap-1 shadow-sm transition active:scale-95"
                >
                  <Download className="w-3 h-3" />
                  <span>{lang === "hi" ? "ऐप इंस्टॉल" : "Install"}</span>
                </button>
              )}
              {/* Dual Language Switcher */}
              <div className="inline-flex rounded-xl bg-black/30 p-0.5 border border-white/20">
                <button
                  onClick={() => setLang("en")}
                  className={`px-2 py-1 text-[10px] font-bold rounded-lg transition ${
                    lang === "en" ? "bg-white text-slate-900 shadow-sm" : "text-white/70 hover:text-white"
                  }`}
                >
                  ENG
                </button>
                <button
                  onClick={() => setLang("hi")}
                  className={`px-2 py-1 text-[10px] font-bold rounded-lg transition ${
                    lang === "hi" ? "bg-emerald-500 text-slate-950 shadow-sm" : "text-white/70 hover:text-white"
                  }`}
                >
                  हिन्दी
                </button>
              </div>
            </div>
          </div>

          {/* Senior Profile Pill & Care Coordinator Notice */}
          <div className="mt-2.5 bg-black/20 rounded-xl p-2 flex items-center justify-between text-xs border border-white/10">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-[#278C78] text-white flex items-center justify-center font-bold text-xs">
                {selectedSenior?.full_name ? selectedSenior.full_name[0] : "H"}
              </div>
              <div>
                <p className="font-bold text-white text-xs leading-tight">
                  {selectedSenior?.full_name || "Harshit Thakur"} ({selectedSenior?.age || 72} {lang === "hi" ? "वर्ष" : "yrs"})
                </p>
                <p className="text-[10px] text-emerald-200 leading-tight">
                  {lang === "hi" ? "केयर दीदी:" : "Coordinator:"} {selectedSenior?.coordinator_name || "अन्वेषा शर्मा"}
                </p>
              </div>
            </div>

            {/* Senior Switcher Dropdown for judges/demo */}
            <button
              onClick={() => setShowSeniorPicker(!showSeniorPicker)}
              className="text-[10px] bg-white/15 hover:bg-white/25 px-2 py-1 rounded-lg font-semibold flex items-center gap-1 transition text-white"
            >
              <span>{lang === "hi" ? "बदलें" : "Switch"}</span>
              <ChevronDown className="w-3 h-3" />
            </button>
          </div>

          {/* Dropdown Menu for Seniors */}
          {showSeniorPicker && (
            <div className="mt-2 bg-slate-900 rounded-xl p-2 border border-slate-700 shadow-xl space-y-1">
              <p className="text-[10px] font-bold text-slate-400 px-2 uppercase">वरिष्ठ नागरिक चुनें:</p>
              {seniorsList.map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    setSelectedSenior(s);
                    setSelectedSeniorId(s.id);
                    setShowSeniorPicker(false);
                  }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-between transition ${
                    selectedSeniorId === s.id ? "bg-emerald-600 text-white" : "text-slate-200 hover:bg-slate-800"
                  }`}
                >
                  <span>{s.full_name} ({s.city})</span>
                  {selectedSeniorId === s.id && <Check className="w-3.5 h-3.5" />}
                </button>
              ))}
            </div>
          )}
        </header>

        {/* ======================================================== */}
        {/* MAIN BODY CONTENT ACCORDING TO ACTIVE TAB                */}
        {/* ======================================================== */}
        <main className="flex-1 overflow-y-auto px-4 py-4 pb-24 space-y-4">

          {/* TAB 1: CONVERSATIONAL AI CHECK-IN */}
          {activeTab === "checkin" && (
            <div className="space-y-4">

              {/* 1:30 PM Medicine Reminder Notification Card */}
              <div className={`p-4 rounded-3xl border transition-all ${med130Taken ? 'bg-emerald-50/90 border-emerald-300' : 'bg-gradient-to-r from-amber-50 to-orange-50 border-amber-300 shadow-sm'}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <span className={`p-2.5 rounded-2xl shrink-0 mt-0.5 ${med130Taken ? 'bg-emerald-200 text-emerald-800' : 'bg-amber-200 text-amber-900 animate-pulse'}`}>
                      <Pill className="w-5 h-5" />
                    </span>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[11px] font-black uppercase tracking-wider text-amber-900 bg-amber-200/80 px-2.5 py-0.5 rounded-full border border-amber-300">
                          ⏰ 1:30 PM दोपहर की दवाई
                        </span>
                        {med130Taken && (
                          <span className="text-[10px] font-extrabold bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                            <Check className="w-3 h-3" /> समय पर ली गई
                          </span>
                        )}
                      </div>
                      <h4 className="font-extrabold text-slate-900 text-sm mt-1">
                        {med130Taken ? "दोपहर 1:30 बजे की दवाई ली जा चुकी है" : "क्या आपने 1:30 बजे की दवाई ले ली?"}
                      </h4>
                      <p className="text-xs text-slate-600 mt-0.5 font-medium">
                        मेटफ़ॉर्मिन 500mg (शुगर) &bull; दोपहर के खाने के बाद
                      </p>
                    </div>
                  </div>
                </div>

                {!med130Taken ? (
                  <div className="mt-3 flex items-center gap-2">
                    <button
                      onClick={async () => {
                        setMed130Taken(true);
                        try {
                          await fetch("/api/v1/hardware/event", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                              senior_id: selectedSeniorId,
                              device_type: "pillbox",
                              event: "BOX_OPENED",
                              message: "Harshit Thakur verified 1:30 PM dose taken"
                            })
                          });
                        } catch (e) {}
                        playAgentSpeech("बहुत बढ़िया हर्षित जी! मैंने नोट कर लिया है कि आपने दोपहर की दवाई ले ली है।");
                      }}
                      className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-black text-xs flex items-center justify-center gap-1.5 shadow-sm active:scale-95 transition"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>✓ हाँ, मैंने दवा ले ली</span>
                    </button>
                    <button
                      onClick={() => {
                        playAgentSpeech("हर्षित जी, दोपहर के 1:30 बज गए हैं। आपकी शुगर की दवाई मेटफ़ॉर्मिन का समय हो गया है। कृपया खाना खाकर दवाई ले लीजिए।");
                        setShowMed130Modal(true);
                      }}
                      className="px-3.5 py-2.5 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 rounded-xl font-bold text-xs flex items-center gap-1.5 shadow-2xs active:scale-95 transition"
                      title="1:30 PM अलार्म टेस्ट करें"
                    >
                      <Bell className="w-3.5 h-3.5 text-amber-600" />
                      <span>अलर्ट टेस्ट</span>
                    </button>
                  </div>
                ) : (
                  <div className="mt-2 text-xs font-semibold text-emerald-700 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>कोऑर्डिनेटर अन्वेषा दीदी और स्मार्ट पिलबॉक्स में दर्ज हो गया है।</span>
                  </div>
                )}
              </div>
              {/* Hero Action Card */}
              <div className="bg-gradient-to-br from-[#173F35] to-[#205749] text-white p-5 rounded-3xl shadow-md space-y-3 text-center relative overflow-hidden">
                <div className="space-y-1">
                  <span className="inline-flex items-center gap-1 bg-emerald-400/20 text-emerald-300 text-[11px] font-bold px-2 py-0.5 rounded-full border border-emerald-400/30">
                    <Sparkles className="w-3 h-3" /> 10:00 AM दैनिक वॉइस चेक-इन
                  </span>
                  <h2 className="text-xl font-extrabold">
                    {aiCallActive ? "सहारा AI से बात हो रही है..." : "आज आप कैसा महसूस कर रहे हैं?"}
                  </h2>
                  <p className="text-xs text-emerald-100 max-w-xs mx-auto">
                    {aiCallActive
                      ? "सहारा AI आपकी आवाज़ सुन रही है। आप बोलते रहें, बटन दबाने की ज़रूरत नहीं है।"
                      : "कॉल शुरू करने के लिए नीचे हरा बटन दबाएँ। सहारा AI आपसे बोलकर हालचाल पूछेगी।"}
                  </p>
                </div>

                {/* Big Action Call Button */}
                <div className="pt-2 flex justify-center">
                  {!aiCallActive ? (
                    <button
                      onClick={startAiCheckinCall}
                      className="w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-base rounded-2xl shadow-xl flex items-center justify-center gap-2 transition active:scale-95"
                    >
                      <Phone className="w-5 h-5 fill-slate-950" />
                      <span>कॉल शुरू करें (Start Check-in)</span>
                    </button>
                  ) : (
                    <button
                      onClick={stopAllAudioAndSession}
                      className="w-full py-3.5 bg-rose-600 hover:bg-rose-500 text-white font-black text-sm rounded-2xl shadow-xl flex items-center justify-center gap-2 transition active:scale-95"
                    >
                      <PhoneOff className="w-4 h-4" />
                      <span>कॉल समाप्त करें (End Call)</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Prominent Live Speech Transcription Box */}
              {aiCallActive && (
                <div className="bg-emerald-50/90 border-2 border-emerald-300 rounded-2xl p-3.5 shadow-xs space-y-2 animate-in fade-in">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`w-2.5 h-2.5 rounded-full ${isRecording ? "bg-rose-500 animate-ping" : agentSpeaking ? "bg-blue-500" : "bg-emerald-500"}`}></span>
                      <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                        <Mic className="w-4 h-4 text-emerald-700" />
                        {agentSpeaking ? "सहारा AI बोल रही है (कृपया सुनें)..." : "आपकी आवाज़ (Live Voice Transcript):"}
                      </span>
                    </div>
                    {transcript && !agentSpeaking && (
                      <button
                        onClick={() => sendSeniorAnswer()}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[11px] rounded-xl shadow-xs transition active:scale-95"
                      >
                        उत्तर भेजें &rarr;
                      </button>
                    )}
                  </div>
                  <div className="bg-white p-3 rounded-xl border border-emerald-200 min-h-[46px] flex items-center">
                    <p className="text-sm font-bold text-slate-900 leading-relaxed">
                      {transcript ? (
                        <span>&ldquo;{transcript}&rdquo;</span>
                      ) : agentSpeaking ? (
                        <span className="text-blue-700 font-medium italic text-xs">सहारा AI का सवाल सुनिए...</span>
                      ) : (
                        <span className="text-slate-400 font-normal italic text-xs">
                          बोलिए, माइक आपकी आवाज़ पहचान रहा है... (जैसे: &ldquo;सब ठीक है, बस थोड़ा सा सिरदर्द है&rdquo;)
                        </span>
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* 1-Tap Quick Response Buttons for Seniors */}
              {aiCallActive && currentStepIndex <= 2 && (
                <div className="bg-emerald-50/70 border border-emerald-200 rounded-2xl p-3 space-y-2">
                  <p className="text-[11px] font-bold text-emerald-900 text-center">
                    आवाज़ के अलावा आप बटन दबाकर भी बता सकते हैं:
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => sendSeniorAnswer("1")}
                      className="py-2.5 bg-white hover:bg-emerald-100 border border-emerald-300 text-emerald-900 font-bold text-xs rounded-xl shadow-xs transition active:scale-95 text-center"
                    >
                      <span className="block text-base">🟢 1</span>
                      <span>अच्छा</span>
                    </button>
                    <button
                      onClick={() => sendSeniorAnswer("2")}
                      className="py-2.5 bg-white hover:bg-amber-100 border border-amber-300 text-amber-900 font-bold text-xs rounded-xl shadow-xs transition active:scale-95 text-center"
                    >
                      <span className="block text-base">🟡 2</span>
                      <span>ठीक-ठाक</span>
                    </button>
                    <button
                      onClick={() => sendSeniorAnswer("3")}
                      className="py-2.5 bg-white hover:bg-rose-100 border border-rose-300 text-rose-900 font-bold text-xs rounded-xl shadow-xs transition active:scale-95 text-center"
                    >
                      <span className="block text-base">🔴 3</span>
                      <span>अच्छा नहीं</span>
                    </button>
                  </div>
                </div>
              )}

              {/* WhatsApp-Style Clean Chat Log */}
              <div className="space-y-2.5 bg-slate-50 border border-slate-200/80 rounded-3xl p-4 min-h-[200px] max-h-[320px] overflow-y-auto">
                {conversationHistory.length === 0 ? (
                  <div className="text-center py-10 text-slate-400 text-xs">
                    बातचीत का विवरण यहाँ दिखेगा।
                  </div>
                ) : (
                  conversationHistory.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex items-start gap-2 ${msg.sender === "ai" ? "justify-start" : "justify-end"}`}
                    >
                      {msg.sender === "ai" && (
                        <div className="w-6 h-6 rounded-full bg-[#173F35] text-white flex items-center justify-center shrink-0 text-[10px] font-bold">
                          AI
                        </div>
                      )}
                      <div
                        className={`p-3 rounded-2xl max-w-[80%] text-xs font-medium leading-relaxed ${
                          msg.sender === "ai"
                            ? "bg-white border border-slate-200 text-slate-800 shadow-xs"
                            : "bg-[#173F35] text-white shadow-xs"
                        }`}
                      >
                        {msg.text}
                      </div>
                      {msg.sender === "senior" && (
                        <div className="w-6 h-6 rounded-full bg-[#278C78] text-white flex items-center justify-center shrink-0 text-[10px] font-bold">
                          {selectedSenior?.full_name ? selectedSenior.full_name[0] : "H"}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 2: DIRECT PHONE CALL & APP-TO-APP CALL TO ANVESHA SHARMA */}
          {activeTab === "direct_call" && (
            <div className="space-y-4">
              <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs text-center space-y-4">
                <div className="relative w-24 h-24 mx-auto">
                  <div className="w-24 h-24 rounded-full bg-emerald-100 border-4 border-emerald-500/20 flex items-center justify-center overflow-hidden shadow-inner">
                    <User className="w-12 h-12 text-emerald-800" />
                  </div>
                  <span className="absolute bottom-1 right-1 w-5 h-5 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center">
                    <Check className="w-3 h-3 text-white" />
                  </span>
                </div>

                <div className="space-y-1">
                  <h3 className="text-lg font-extrabold text-slate-900">
                    {selectedSenior?.coordinator_name || "अन्वेषा शर्मा"}
                  </h3>
                  <p className="text-xs font-semibold text-emerald-700 bg-emerald-50 inline-block px-2.5 py-0.5 rounded-full">
                    🟢 {lang === "hi" ? "केयर कोऑर्डिनेटर (उपलब्ध हैं)" : "Care Coordinator (Available)"}
                  </p>
                  <p className="text-xs text-slate-500 pt-1">
                    {lang === "hi"
                      ? "सीधे अपने मोबाइल के फ़ोन ऐप से कॉल मिलाएँ या मुफ़्त ऐप-टू-ऐप लाइव कॉल करें।"
                      : "Dial directly from your phone app or start a free in-app live WebRTC call."}
                  </p>
                </div>

                <div className="space-y-2.5 pt-2">
                  {/* Primary Direct Phone Call Button - Opens Mobile Dialer */}
                  <a
                    href="tel:+918267069623"
                    className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-sm rounded-2xl shadow-lg flex items-center justify-center gap-2 transition active:scale-95"
                  >
                    <Phone className="w-5 h-5 fill-white" />
                    <span>{lang === "hi" ? "अन्वेषा दीदी को फ़ोन मिलाएँ (8267069623)" : "Call Anvesha Sharma (8267069623)"}</span>
                  </a>

                  {/* Direct Phone Call to Mummy (Anchal Mishra) */}
                  <a
                    href="tel:+918957266841"
                    className="w-full py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-sm rounded-2xl shadow-md flex items-center justify-center gap-2 transition active:scale-95"
                  >
                    <Phone className="w-4 h-4 fill-white" />
                    <span>{lang === "hi" ? "मम्मी (आँचल मिश्रा) को फ़ोन मिलाएँ (8957266841)" : "Call Mummy (Anchal Mishra - 8957266841)"}</span>
                  </a>

                  {/* WebRTC In-App Call Button */}
                  <button
                    onClick={callCoordinatorDirectly}
                    className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs rounded-2xl shadow-sm flex items-center justify-center gap-2 transition active:scale-95"
                  >
                    <Sparkles className="w-4 h-4 text-emerald-400" />
                    <span>{lang === "hi" ? "ऐप-टू-ऐप लाइव कॉल (In-App Call)" : "In-App Live Call (WebRTC)"}</span>
                  </button>
                </div>
              </div>

              {/* Call Safeguards Info */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs text-slate-600 space-y-2">
                <div className="flex items-center gap-2 font-bold text-slate-800">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>{lang === "hi" ? "सीधी कॉल की सुविधा:" : "Direct Calling Features:"}</span>
                </div>
                <ul className="list-disc pl-5 space-y-1 text-[11px] text-slate-500">
                  <li>{lang === "hi" ? "बटन दबाते ही आपके मोबाइल का फ़ोन डायलर तुरंत खुल जाएगा।" : "Tapping opens your mobile phone dialer instantly."}</li>
                  <li>{lang === "hi" ? "अन्वेषा शर्मा (8267069623) और मम्मी आँचल मिश्रा (8957266841) से सीधा संपर्क।" : "Direct access to Anvesha Sharma (8267069623) and Mummy Anchal Mishra (8957266841)."}</li>
                  <li>{lang === "hi" ? "कंप्यूटर डैशबोर्ड पर भी लाइव कॉल बजती है।" : "Live incoming alerts ring on the coordinator computer dashboard."}</li>
                </ul>
              </div>
            </div>
          )}

          {/* TAB 3: MEDICINES & HEALTH TIMELINE */}
          {activeTab === "medicines" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-1">
                <h3 className="font-extrabold text-sm text-slate-900 flex items-center gap-2">
                  <Pill className="w-4 h-4 text-emerald-600" />
                  <span>{lang === "hi" ? "आज की निर्धारित दवाइयाँ" : "Scheduled Medications Today"}</span>
                </h3>
                <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                  {lang === "hi" ? "2 दवाइयाँ" : "2 Medicines"}
                </span>
              </div>

              {/* Medicine Card 1 */}
              <div className="bg-white border border-emerald-200 rounded-2xl p-4 shadow-xs flex items-center justify-between">
                <div className="space-y-1">
                  <span className="text-[10px] font-extrabold uppercase bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-md border border-emerald-200">
                    {lang === "hi" ? "🌅 सुबह 09:00 AM" : "🌅 Morning 09:00 AM"}
                  </span>
                  <h4 className="font-bold text-sm text-slate-900">Amlodipine 5mg ({lang === "hi" ? "बीपी की गोली" : "Blood Pressure"})</h4>
                  <p className="text-[11px] text-slate-500">{lang === "hi" ? "नाश्ते के बाद 1 गोली पानी के साथ" : "1 tablet after breakfast with water"}</p>
                </div>
                <div className="text-right">
                  <span className="inline-flex items-center gap-1 text-xs font-extrabold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-xl border border-emerald-200">
                    <Check className="w-3.5 h-3.5" /> {lang === "hi" ? "ले ली" : "Taken"}
                  </span>
                </div>
              </div>

              {/* Medicine Card 2 */}
              <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex items-center justify-between">
                <div className="space-y-1">
                  <span className="text-[10px] font-extrabold uppercase bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md border border-slate-200">
                    {lang === "hi" ? "🌙 रात 08:30 PM" : "🌙 Night 08:30 PM"}
                  </span>
                  <h4 className="font-bold text-sm text-slate-900">Metformin 500mg ({lang === "hi" ? "शुगर की गोली" : "Blood Sugar"})</h4>
                  <p className="text-[11px] text-slate-500">{lang === "hi" ? "रात के खाने के बाद 1 गोली" : "1 tablet after dinner"}</p>
                </div>
                <div className="text-right">
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-amber-800 bg-amber-50 px-2.5 py-1 rounded-xl border border-amber-200">
                    <Clock className="w-3.5 h-3.5" /> {lang === "hi" ? "शाम को" : "Due tonight"}
                  </span>
                </div>
              </div>

              {/* Hardware Pillbox Telemetry */}
              <div className="bg-emerald-50/70 border border-emerald-200 rounded-2xl p-3.5 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
                  <div>
                    <p className="font-bold text-emerald-950">{lang === "hi" ? "स्मार्ट पिल बॉक्स (Home Hub)" : "Smart Pill Dispenser (Home Hub)"}</p>
                    <p className="text-[10px] text-emerald-800">{lang === "hi" ? "आज सुबह 9:08 AM पर ढक्कन खोला गया" : "Dispenser lid opened at 9:08 AM today"}</p>
                  </div>
                </div>
                <span className="text-[10px] font-bold bg-white text-emerald-800 px-2 py-1 rounded-lg border border-emerald-200">
                  {lang === "hi" ? "सत्यापित ✅" : "Verified ✅"}
                </span>
              </div>
            </div>
          )}

          {/* TAB 4: EMERGENCY SOS & CAREGIVERS */}
          {activeTab === "sos" && (
            <div className="space-y-4 text-center">
              <div className="bg-rose-50 border-2 border-rose-300 rounded-3xl p-6 space-y-4">
                <div className="space-y-1">
                  <span className="inline-flex items-center gap-1 bg-rose-200 text-rose-900 text-xs font-black px-2.5 py-0.5 rounded-full">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-700" /> {lang === "hi" ? "तुरंत सहायता" : "Emergency Help"}
                  </span>
                  <h3 className="text-xl font-black text-rose-950">
                    {lang === "hi" ? "आपातकालीन सहायता बटन" : "Emergency SOS Button"}
                  </h3>
                  <p className="text-xs text-rose-800 max-w-xs mx-auto">
                    {lang === "hi"
                      ? "यदि चक्कर आ रहा हो, सीने में दर्द हो, गिर गए हों या कोई परेशानी हो, तो नीचे दिया गया लाल बटन दबाएँ।"
                      : "If experiencing dizziness, chest pain, a fall, or any acute distress, press the red SOS button."}
                  </p>
                </div>

                {/* Giant SOS Pulsing Button */}
                <div className="py-2 flex justify-center">
                  <button
                    onClick={handleTriggerSos}
                    className="w-44 h-44 rounded-full bg-rose-600 hover:bg-rose-700 text-white font-black text-lg shadow-2xl flex flex-col items-center justify-center gap-1 ring-8 ring-rose-200 animate-pulse active:scale-95 transition"
                  >
                    <AlertTriangle className="w-12 h-12 mb-1" />
                    <span>EMERGENCY</span>
                    <span className="text-xs font-bold tracking-wider">{lang === "hi" ? "मदद बुलाएँ" : "Call for Help"}</span>
                  </button>
                </div>

                {sosTriggered && (
                  <div className="p-3 bg-white rounded-xl border border-rose-300 text-rose-900 text-xs font-bold animate-bounce">
                    {lang === "hi"
                      ? "🚨 अलर्ट भेजा गया! अन्वेषा दीदी तुरंत संपर्क कर रही हैं।"
                      : "🚨 Emergency Alert Dispatched! Anvesha Sharma is contacting you immediately."}
                  </div>
                )}
              </div>

              {/* Direct Caregiver Phone Numbers */}
              <div className="space-y-2 text-left">
                <p className="text-xs font-bold text-slate-700">
                  {lang === "hi" ? "पारिवारिक व आपातकालीन संपर्क:" : "Family & Emergency Contacts:"}
                </p>
                <a
                  href="tel:+918267069623"
                  className="bg-white border border-slate-200 rounded-2xl p-3 flex items-center justify-between text-xs font-bold text-slate-900 hover:bg-slate-50 transition shadow-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center">
                      <Phone className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="font-bold">{lang === "hi" ? "अन्वेषा शर्मा (केयर कोऑर्डिनेटर)" : "Anvesha Sharma (Care Coordinator)"}</p>
                      <p className="text-[10px] text-slate-500 font-mono">+91 8267069623</p>
                    </div>
                  </div>
                  <span className="text-emerald-700 bg-emerald-50 px-2 py-1 rounded-lg">
                    {lang === "hi" ? "कॉल करें" : "Call"}
                  </span>
                </a>

                <a
                  href="tel:+918957266841"
                  className="bg-white border border-slate-200 rounded-2xl p-3 flex items-center justify-between text-xs font-bold text-slate-900 hover:bg-slate-50 transition shadow-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center">
                      <User className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="font-bold">{lang === "hi" ? "आँचल मिश्रा (मम्मी)" : "Anchal Mishra (Mummy)"}</p>
                      <p className="text-[10px] text-slate-500 font-mono">+91 8957266841</p>
                    </div>
                  </div>
                  <span className="text-blue-700 bg-blue-50 px-2 py-1 rounded-lg">
                    {lang === "hi" ? "कॉल करें" : "Call"}
                  </span>
                </a>

                <a
                  href="tel:108"
                  className="bg-rose-50 border border-rose-200 rounded-2xl p-3 flex items-center justify-between text-xs font-bold text-rose-950 hover:bg-rose-100 transition shadow-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-rose-600 text-white flex items-center justify-center">
                      <ShieldAlert className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="font-bold">{lang === "hi" ? "108 सरकारी एम्बुलेंस" : "108 National Ambulance"}</p>
                      <p className="text-[10px] text-rose-700">{lang === "hi" ? "राष्ट्रीय आपातकालीन सेवा" : "Emergency Medical Service"}</p>
                    </div>
                  </div>
                  <span className="text-rose-800 bg-white px-2 py-1 rounded-lg border border-rose-300">
                    {lang === "hi" ? "डायल 108" : "Dial 108"}
                  </span>
                </a>
              </div>
            </div>
          )}
        </main>

        {/* ======================================================== */}
        {/* NATIVE BOTTOM NAVIGATION BAR (Instagram / WhatsApp style) */}
        {/* ======================================================== */}
        <nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto z-40 bg-white/95 backdrop-blur-md border-t border-slate-200 px-2 py-2 flex items-center justify-around shadow-2xl">
          <button
            onClick={() => setActiveTab("checkin")}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-2xl transition ${
              activeTab === "checkin" ? "text-[#173F35] font-extrabold" : "text-slate-400 font-semibold"
            }`}
          >
            <Bot className={`w-5 h-5 ${activeTab === "checkin" ? "text-[#173F35] stroke-[2.5]" : ""}`} />
            <span className="text-[10px] mt-0.5">{lang === "hi" ? "दैनिक बात" : "Check-in"}</span>
          </button>

          <button
            onClick={() => setActiveTab("direct_call")}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-2xl transition ${
              activeTab === "direct_call" ? "text-emerald-700 font-extrabold" : "text-slate-400 font-semibold"
            }`}
          >
            <Phone className={`w-5 h-5 ${activeTab === "direct_call" ? "text-emerald-700 stroke-[2.5]" : ""}`} />
            <span className="text-[10px] mt-0.5">{lang === "hi" ? "अन्वेषा दीदी" : "Care Didi"}</span>
          </button>

          <button
            onClick={() => setActiveTab("medicines")}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-2xl transition ${
              activeTab === "medicines" ? "text-blue-700 font-extrabold" : "text-slate-400 font-semibold"
            }`}
          >
            <Pill className={`w-5 h-5 ${activeTab === "medicines" ? "text-blue-700 stroke-[2.5]" : ""}`} />
            <span className="text-[10px] mt-0.5">{lang === "hi" ? "दवाइयाँ" : "Medicines"}</span>
          </button>

          <button
            onClick={() => setActiveTab("sos")}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-2xl transition ${
              activeTab === "sos" ? "text-rose-600 font-extrabold" : "text-slate-400 font-semibold"
            }`}
          >
            <AlertTriangle className={`w-5 h-5 ${activeTab === "sos" ? "text-rose-600 stroke-[2.5]" : ""}`} />
            <span className="text-[10px] mt-0.5">{lang === "hi" ? "आपातकाल" : "SOS Help"}</span>
          </button>
        </nav>

        {/* ======================================================== */}
        {/* FULLSCREEN INCOMING CALL MODAL (Instagram / Snapchat)    */}
        {/* ======================================================== */}
        {directCallState === "incoming" && (
          <div className="fixed inset-0 z-50 bg-[#0E2620]/95 backdrop-blur-md flex flex-col justify-between items-center py-16 px-6 text-white text-center">
            {/* Top Branding */}
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-widest text-emerald-400 font-extrabold">
                {lang === "hi" ? "सहारा AI · सीधा इन-ऐप कॉल" : "Sahara AI · Direct In-App Call"}
              </span>
              <p className="text-xs text-slate-300">
                {lang === "hi" ? "रोज़ की बातचीत • अन्वेषा दीदी की तरफ़ से" : "Daily check-in · From Anvesha Didi"}
              </p>
            </div>

            {/* Center Avatar & Pulsing Rings */}
            <div className="relative my-8">
              <div className="absolute -inset-4 rounded-full bg-emerald-500/20 animate-ping"></div>
              <div className="absolute -inset-8 rounded-full bg-emerald-500/10 animate-pulse"></div>
              <div className="w-32 h-32 rounded-full bg-gradient-to-tr from-[#173F35] to-emerald-600 border-4 border-emerald-400/80 flex items-center justify-center shadow-2xl relative z-10">
                <User className="w-16 h-16 text-white" />
              </div>
              <div className="mt-4">
                <h2 className="text-2xl font-black text-white">{directCallerName || (lang === "hi" ? "अन्वेषा शर्मा" : "Anvesha Sharma")}</h2>
                <p className="text-sm font-semibold text-emerald-300 mt-1 flex items-center justify-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
                  <span>{lang === "hi" ? "कॉल आ रही है (Incoming Call)..." : "Incoming Call..."}</span>
                </p>
              </div>
            </div>

            {/* Bottom Buttons: Answer & Decline */}
            <div className="w-full max-w-xs grid grid-cols-2 gap-4">
              <button
                onClick={endDirectCall}
                className="py-4 bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-sm rounded-2xl shadow-xl flex flex-col items-center justify-center gap-1 active:scale-95 transition"
              >
                <PhoneOff className="w-6 h-6" />
                <span>{lang === "hi" ? "काटिए / Decline" : "Decline"}</span>
              </button>

              <button
                onClick={answerDirectCall}
                className="py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-sm rounded-2xl shadow-xl flex flex-col items-center justify-center gap-1 active:scale-95 transition animate-bounce"
              >
                <PhoneIncoming className="w-6 h-6 fill-slate-950" />
                <span>{lang === "hi" ? "उठाइए / Answer" : "Answer"}</span>
              </button>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* FULLSCREEN OUTGOING CALL MODAL (Calling Anvesha Didi)    */}
        {/* ======================================================== */}
        {directCallState === "calling" && (
          <div className="fixed inset-0 z-50 bg-[#0E2620]/95 backdrop-blur-md flex flex-col justify-between items-center py-16 px-6 text-white text-center">
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-widest text-emerald-400 font-extrabold">
                {lang === "hi" ? "सहारा AI · आउटगोइंग कॉल" : "Sahara AI · Outgoing Call"}
              </span>
              <p className="text-xs text-slate-300">
                {lang === "hi" ? "केयर कोऑर्डिनेटर से संपर्क हो रहा है" : "Connecting to Care Coordinator"}
              </p>
            </div>

            <div className="my-8">
              <div className="w-28 h-28 mx-auto rounded-full bg-emerald-700/60 border-4 border-emerald-400 flex items-center justify-center animate-pulse shadow-2xl">
                <User className="w-14 h-14 text-white" />
              </div>
              <h2 className="text-2xl font-black text-white mt-4">{directCallerName || (lang === "hi" ? "अन्वेषा शर्मा" : "Anvesha Sharma")}</h2>
              <p className="text-sm text-emerald-300 font-semibold mt-1">
                {lang === "hi" ? "घंटी बज रही है (Ringing)..." : "Ringing..."}
              </p>
            </div>

            <button
              onClick={endDirectCall}
              className="w-full max-w-xs py-4 bg-rose-600 hover:bg-rose-700 text-white font-black text-sm rounded-2xl shadow-xl flex items-center justify-center gap-2 active:scale-95 transition"
            >
              <PhoneOff className="w-5 h-5" />
              <span>{lang === "hi" ? "कॉल काटें (Cancel)" : "Cancel"}</span>
            </button>
          </div>
        )}

        {/* ======================================================== */}
        {/* FULLSCREEN CONNECTED LIVE CALL ROOM                      */}
        {/* ======================================================== */}
        {directCallState === "connected" && (
          <div className="fixed inset-0 z-50 bg-[#0A1D18] flex flex-col justify-between items-center py-12 px-6 text-white text-center">
            {/* Header */}
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 bg-emerald-500/20 text-emerald-300 text-xs font-bold px-3 py-1 rounded-full border border-emerald-400/30">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                <span>लाइव बातचीत जारी (Live WebRTC Audio)</span>
              </div>
              <h2 className="text-xl font-black text-white pt-2">{directCallerName}</h2>
              <p className="text-sm font-mono text-emerald-200">
                00:{directCallDuration < 10 ? `0${directCallDuration}` : directCallDuration}
              </p>
            </div>

            {/* Audio Wave Visualizer Simulation */}
            <div className="flex items-center justify-center gap-1.5 h-20 my-6">
              {[40, 65, 30, 85, 95, 45, 75, 55, 90, 60].map((h, i) => (
                <div
                  key={i}
                  style={{ height: `${h}%` }}
                  className="w-2 bg-emerald-400 rounded-full animate-pulse"
                ></div>
              ))}
            </div>

            {/* In-Call Controls */}
            <div className="w-full max-w-xs space-y-4">
              <div className="flex items-center justify-center gap-4">
                <button
                  onClick={toggleMicMute}
                  className={`p-4 rounded-full border transition active:scale-95 ${
                    isMicMuted
                      ? "bg-rose-600 text-white border-rose-500"
                      : "bg-white/10 text-white border-white/20 hover:bg-white/20"
                  }`}
                >
                  {isMicMuted ? <VolumeX className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                </button>
              </div>

              <button
                onClick={endDirectCall}
                className="w-full py-4 bg-rose-600 hover:bg-rose-700 text-white font-black text-base rounded-2xl shadow-xl flex items-center justify-center gap-2 active:scale-95 transition"
              >
                <PhoneOff className="w-5 h-5" />
                <span>कॉल समाप्त करें (End Call)</span>
              </button>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* PWA INSTALL STEP-BY-STEP MODAL GUIDE                     */}
        {/* ======================================================== */}
        {showInstallGuide && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-end sm:items-center justify-center p-4">
            <div className="bg-white w-full max-w-sm rounded-3xl p-5 space-y-4 shadow-2xl border border-slate-200">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-[#173F35] text-white flex items-center justify-center">
                    <Download className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div>
                    <h4 className="font-extrabold text-sm text-slate-900">ऐप अपने फ़ोन पर जोड़ें</h4>
                    <p className="text-[10px] text-slate-500">बिना ब्राउज़र असली ऐप की तरह चलाएँ</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowInstallGuide(false)}
                  className="p-1 rounded-full text-slate-400 hover:bg-slate-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Instructions for Android / Chrome */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3 space-y-1.5 text-xs">
                <span className="font-bold text-slate-800 text-xs">📱 Android (Google Chrome):</span>
                <ol className="list-decimal pl-5 space-y-1 text-[11px] text-slate-600">
                  <li>ऊपर दाईं ओर 3 डॉट्स (⋮) मेनू पर टैप करें।</li>
                  <li><strong>&lsquo;Add to Home screen&rsquo;</strong> या <strong>&lsquo;Install app&rsquo;</strong> चुनें।</li>
                  <li>&lsquo;Install&rsquo; पर टैप करें — ऐप होम स्क्रीन पर आ जाएगा।</li>
                </ol>
              </div>

              {/* Instructions for iPhone / Safari */}
              <div className="bg-emerald-50/70 border border-emerald-200 rounded-2xl p-3 space-y-1.5 text-xs">
                <span className="font-bold text-emerald-950 text-xs">🍏 iPhone (Safari Browser):</span>
                <ol className="list-decimal pl-5 space-y-1 text-[11px] text-emerald-900">
                  <li>नीचे बीच में स्थित <strong>Share बटन (वर्गाकार + तीर ⎋)</strong> पर टैप करें।</li>
                  <li>नीचे स्क्रॉल करके <strong>&lsquo;Add to Home Screen ➕&rsquo;</strong> चुनें।</li>
                  <li>ऊपर दाएँ &lsquo;Add&rsquo; दबाएँ — सहारा AI ऐप तैयार है!</li>
                </ol>
              </div>

              <button
                onClick={() => setShowInstallGuide(false)}
                className="w-full py-2.5 bg-[#173F35] text-white font-bold text-xs rounded-xl shadow-xs"
              >
                समझ गया (Close)
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

