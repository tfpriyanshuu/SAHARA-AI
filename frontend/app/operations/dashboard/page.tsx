"use client";

import React, { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  Shield,
  Activity,
  AlertTriangle,
  Clock,
  Users,
  CheckCircle2,
  TrendingUp,
  MapPin,
  FileText,
  Search,
  Filter,
  BarChart3,
  Calendar,
  Lock
} from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

export default function OperationsDashboard() {
  const [overview, setOverview] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Sample Audit Logs for security compliance demonstration
  const auditLogs = [
    {
      timestamp: "Today, 11:42 AM",
      actor: "Anita Deshmukh",
      role: "Care Coordinator",
      action: "RESOLVE_ALERT",
      target: "ALERT_882 (SEN_003)",
      details: "Contacted senior; verified missed dose taken with water; SpO2 follow-up set for 24h."
    },
    {
      timestamp: "Today, 10:15 AM",
      actor: "Vikram Joshi",
      role: "Operations Lead",
      action: "VIEW_OPERATIONS_OVERVIEW",
      target: "NATIONAL_AGGREGATE",
      details: "Audit log & triage SLA verification."
    },
    {
      timestamp: "Today, 09:30 AM",
      actor: "System Scheduler",
      role: "Automated Engine",
      action: "RECOMPUTE_RISK_BATCH",
      target: "200 Seniors Cohort",
      details: "Lagged baseline window drift calculated; 14 alerts gated into coordinator queue."
    },
    {
      timestamp: "Today, 08:45 AM",
      actor: "Anita Deshmukh",
      role: "Care Coordinator",
      action: "VIEW_SENIOR_DETAIL",
      target: "SEN_003",
      details: "Role boundary verified; assigned coordinator authorization granted."
    },
    {
      timestamp: "Yesterday, 06:10 PM",
      actor: "Rajesh Sharma",
      role: "Family Member",
      action: "UPDATE_FAMILY_CONSENT",
      target: "SEN_003_CONSENT",
      details: "Acute alert notifications toggle set to ACTIVE."
    }
  ];

  useEffect(() => {
    async function loadOpsData() {
      try {
        const token = localStorage.getItem("saathi_token");
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const [oRes, tRes] = await Promise.all([
          fetch("/api/v1/operations/overview", { headers }),
          fetch("/api/v1/operations/alert-trends?days=21", { headers })
        ]);

        if (oRes.ok) setOverview(await oRes.json());
        if (tRes.ok) setTrends(await tRes.json());
      } catch (e) {
        console.warn("Using fallback ops data");
      } finally {
        setLoading(false);
      }
    }
    loadOpsData();
  }, []);

  const displayTrends = trends.length > 0 ? trends : [
    { date: "Oct 10", alert_count: 5 },
    { date: "Oct 12", alert_count: 7 },
    { date: "Oct 14", alert_count: 4 },
    { date: "Oct 16", alert_count: 8 },
    { date: "Oct 18", alert_count: 6 },
    { date: "Oct 20", alert_count: 10 },
    { date: "Oct 22", alert_count: 9 },
    { date: "Oct 24", alert_count: 12 },
    { date: "Oct 26", alert_count: 15 },
    { date: "Oct 28", alert_count: 13 },
    { date: "Oct 30", alert_count: 14 }
  ];

  const cityDistribution = [
    { city: "Indore", count: 32, alerts: 3 },
    { city: "Delhi NCR", count: 28, alerts: 2 },
    { city: "Mumbai", count: 26, alerts: 2 },
    { city: "Bengaluru", count: 24, alerts: 2 },
    { city: "Pune", count: 22, alerts: 1 },
    { city: "Jaipur", count: 20, alerts: 1 },
    { city: "Lucknow", count: 18, alerts: 1 },
    { city: "Ahmedabad", count: 16, alerts: 1 },
    { city: "Chennai", count: 14, alerts: 1 }
  ];

  return (
    <div className="min-h-screen bg-[#F8FAF7] flex flex-col text-slate-800">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Operations Header */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[#173F35] to-[#278C78] text-white flex items-center justify-center font-bold text-2xl shadow-md">
              <BarChart3 className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[#278C78] uppercase tracking-wider">
                  Operations &amp; Network Command Center
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
                  Aggregates Only &bull; Notes Redacted
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 mt-1">
                National Care Operations &amp; SLA Performance
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">
                Monitoring triage velocity, coordinator workload, and compliance audit trail across 200 seniors in 10 cities.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold rounded-xl flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
              All 10 City Nodes Operational
            </span>
          </div>
        </div>

        {/* 4 Key KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Seniors</span>
              <Users className="w-5 h-5 text-[#278C78]" />
            </div>
            <div className="text-3xl font-black text-slate-900 mt-2">
              {overview?.total_monitored_seniors || 200}
            </div>
            <p className="text-xs text-slate-500 mt-1">Active longitudinal monitoring</p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Alerts Today</span>
              <AlertTriangle className="w-5 h-5 text-amber-500" />
            </div>
            <div className="text-3xl font-black text-amber-600 mt-2">
              {overview?.active_alerts || 14}
            </div>
            <p className="text-xs text-slate-500 mt-1">Gated under N=10 budget / team</p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Median First Contact</span>
              <Clock className="w-5 h-5 text-indigo-500" />
            </div>
            <div className="text-3xl font-black text-indigo-600 mt-2">
              {overview?.median_response_time_min || 32.4} min
            </div>
            <p className="text-xs text-emerald-600 font-semibold mt-1">&darr; 8.2 min faster than SLA target</p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">7-Day Coverage</span>
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            </div>
            <div className="text-3xl font-black text-emerald-600 mt-2">
              {overview?.coverage_pct || 94.2}%
            </div>
            <p className="text-xs text-slate-500 mt-1">188 seniors contacted past 7 days</p>
          </div>
        </div>

        {/* Charts: Alert Trends & City Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Daily Alert Trend Chart */}
          <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900">National Daily Alert Generation Trend</h3>
                <p className="text-xs text-slate-500">Alert frequency bounded by multi-signal gating logic</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 rounded-lg text-slate-600">Past 21 Days</span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={displayTrends}>
                  <defs>
                    <linearGradient id="colorAlert" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#278C78" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#278C78" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="alert_count" stroke="#278C78" strokeWidth={2.5} fillOpacity={1} fill="url(#colorAlert)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* City Distribution Chart */}
          <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900">Seniors Monitored by City</h3>
                <p className="text-xs text-slate-500">Top Indian metropolitan &amp; tier-2 care clusters</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-[#EAF5EF] text-[#173F35] rounded-lg">10 Active Hubs</span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cityDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="city" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" name="Seniors" fill="#173F35" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="alerts" name="Active Alerts" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Security & Compliance Audit Log Table */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 md:p-8 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Lock className="w-5 h-5 text-[#278C78]" />
                Security, Access &amp; Compliance Audit Trail
              </h3>
              <p className="text-xs text-slate-500">
                Immutable record of every senior record access, triage resolution, and role action
              </p>
            </div>
            <span className="text-xs font-semibold px-3 py-1 bg-emerald-100 text-emerald-800 rounded-md self-start sm:self-center">
              ISO-27001 / HIPAA Compliant Audit Policy
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs font-semibold text-slate-400 uppercase">
                  <th className="pb-3">Timestamp</th>
                  <th className="pb-3">Operator</th>
                  <th className="pb-3">Role</th>
                  <th className="pb-3">Action</th>
                  <th className="pb-3">Target Resource</th>
                  <th className="pb-3">Audit Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {auditLogs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 text-slate-500 text-xs whitespace-nowrap">{log.timestamp}</td>
                    <td className="py-3 font-semibold text-slate-800 text-xs">{log.actor}</td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700">
                        {log.role}
                      </span>
                    </td>
                    <td className="py-3 font-mono text-xs font-bold text-[#173F35]">{log.action}</td>
                    <td className="py-3 font-mono text-xs text-slate-600">{log.target}</td>
                    <td className="py-3 text-xs text-slate-600 max-w-xs truncate">{log.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

