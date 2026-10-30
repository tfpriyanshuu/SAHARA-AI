# SAHARA-AI (सहारा-AI) — AI Geriatric Early Warning & Care Coordination Platform

> **"Every Signal Matters. Every Senior Matters."**  
> *भारत का पहला AI-सक्षम एल्डर-केयर प्लेटफ़ॉर्म — देसी बोलियों में वॉइस चेक-इन, स्मार्ट पिलबॉक्स और व्यक्तिगत बेसलाइन ड्रिफ्ट से अचानक बीमारी बिगड़ने से 11 दिन पहले ही केयर टीम को सतर्क करता है।*

[![Next.js](https://img.shields.io/badge/Next.js-16_App_Router-black?style=flat&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python_3.11-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-saathicare.db-003B57?style=flat&logo=sqlite)](https://sqlite.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=flat&logo=tailwind-css)](https://tailwindcss.com/)

---

## 🌟 Executive Summary

**SAHARA-AI** is a human-in-the-loop healthcare decision-support and proactive tele-monitoring platform designed for Care Coordinators, elderly citizens living independently, and their families. Instead of relying on crude population averages that only trigger after a medical crisis has occurred, SAHARA-AI tracks each senior's **personal physiological and behavioral baseline** across continuous signals:

1. **Daily Indic Conversational Voice Check-Ins:** Automated AI voice calls in authentic Hindi & local dialects with real-time speech recognition, natural clinical dialogue, and immediate cue extraction.
2. **Prioritized Care Coordinator Queue:** Ranked daily priority triage strictly budgeted to eliminate alert fatigue.
3. **Smart Home Hub & IoT Telemetry:** Connected pill dispensers, mmWave fall-detection radars, respiration mattress pads, and front door safety sensors.
4. **Direct Dual-Channel Communication:** Direct mobile dialer integration (`tel:`) + in-app WebRTC real-time voice calls between Senior, Family, and Care Coordinator.
5. **Strict Language Isolation:** 100% pure English or pure Hindi interface toggles without mixed Hinglish jargon.

---

## 🚀 Quickstart Guide

### Prerequisites
- Node.js 18+ (tested on Node 20 / 24)
- Python 3.10+ (tested on Python 3.11)

### 1. Start the Backend API (FastAPI)
```bash
cd backend
# Create or activate virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start FastAPI server on port 8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Backend Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

### 2. Start the Frontend (Next.js App Router)
```bash
cd frontend
npm install
npm run dev
```
- **Web Platform:** [http://localhost:3000](http://localhost:3000)
- **Senior Mobile PWA:** [http://localhost:3000/app](http://localhost:3000/app)

---

## 🔑 Demo Personas & Credentials

On the **Login Screen** (`http://localhost:3000/login`), click any role card to automatically authenticate into the dedicated workflow:

| Role | Real Name | Mobile Number | Username | Password | Dedicated View |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Care Coordinator** | **Anvesha Sharma** | `+91 8267069623` | `anvesha` / `coordinator1` | `coord123` | `/coordinator/dashboard` |
| **Senior Citizen** | **Harshit Thakur** | `+91 9451818283` | `harshit` / `senior1` | `senior123` | `/app` or `/senior/easy` |
| **Family Member** | **Anchal Mishra (Mummy)** | `+91 8957266841` | `anchal` / `family1` | `family123` | `/family/dashboard` |
| **Operations Lead** | **Priyanshu Singh** | — | `ops1` | `ops123` | `/operations/dashboard` |

---

## 🗺️ Key Routes & Architecture

| Route | View | Description |
| :--- | :--- | :--- |
| `/` | **Landing Page** | Clean hero showcasing senior home health, clinical value proposition, and impact metrics |
| `/app` | **Senior Mobile App (PWA)** | 1-Tap Daily Voice Check-in, Direct dialer to Anvesha Didi & Mummy, Medicine checklist, SOS |
| `/coordinator/dashboard` | **Coordinator Command Center** | Priority care queue, real-time status, progressive detail drawer, language switch (`EN / HI`) |
| `/coordinator/seniors/[id]` | **Senior 360 Deep-Dive** | 90-day baseline charts, longitudinal biomarker drift, call timeline, audio recordings |
| `/family/dashboard` | **Family Portal** | Weekly wellbeing evaluation, IoT hardware sensor health, direct contact cards |
| `/login` | **Persona Sign-In** | 1-click quick authentication into any of the 4 stakeholder views |

---

## 🛡️ Privacy & Compliance
- **Consent Isolation:** Family users receive high-level weekly summaries and alerts only with explicit consent.
- **Role-Based Access Control:** Coordinators only access seniors assigned within their operating jurisdiction.
- **Hardware Telemetry Protection:** IoT sensor logs are cryptographically bound and timestamped.
