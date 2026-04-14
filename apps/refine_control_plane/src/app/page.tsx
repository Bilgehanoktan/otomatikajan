"use client";

import { useList } from "@refinedev/core";
import { Activity, ShieldCheck, Terminal, Cpu, Clock, CheckCircle } from "lucide-react";

export default function ControlPlaneDashboard() {
  const { query: { data, isLoading, isError } } = useList({
    resource: "workflows",
  });

  const workflows = data?.data ?? [];

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-[#66fcf1]/10 rounded-xl backdrop-blur-md border border-[#66fcf1]/20 shadow-[0_0_15px_rgba(102,252,241,0.2)]">
            <Cpu className="w-8 h-8 text-[#66fcf1]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#c5c6c7]">
              Sovereign AGI
            </h1>
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">Control Plane</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="px-4 py-2 flex items-center gap-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
            Ops Online
          </div>
          <button className="px-5 py-2 bg-gradient-to-r from-[#1f2833] to-[#0b0c10] border border-[#45a29e]/30 rounded-full hover:border-[#66fcf1]/50 transition-all text-[#c5c6c7] text-sm hover:text-white shadow-lg">
            System Settings
          </button>
        </div>
      </header>

      {/* STATS ROW */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <StatCard title="Active Workflows" value={workflows.filter(w => w.status === 'running').length.toString()} icon={<Activity className="text-[#66fcf1]" />} />
        <StatCard title="Completed" value={workflows.filter(w => w.status === 'completed').length.toString()} icon={<CheckCircle className="text-green-400" />} />
        <StatCard title="Total Instances" value={workflows.length.toString()} icon={<Terminal className="text-purple-400" />} />
        <StatCard title="System Health" value="100%" icon={<ShieldCheck className="text-blue-400" />} />
      </div>

      {/* WORKFLOWS SECTION */}
      <section className="glass-panel rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-[#1f2833] flex justify-between items-center bg-gradient-to-b from-transparent to-[#0b0c10]/40">
          <h2 className="text-xl font-semibold text-white">Active Runs</h2>
        </div>
        
        <div className="p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-2 border-[#66fcf1] border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : isError ? (
            <div className="text-red-400 p-4 rounded-lg bg-red-400/10 border border-red-400/20 text-center">
              Failed to connect to the Workflow API.
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {workflows.length === 0 ? (
                <div className="text-center py-10 text-[#45a29e]">No workflows currently active.</div>
              ) : (
                workflows.map((wf: any) => (
                  <div key={wf.id} className="group p-5 rounded-xl border border-[#1f2833] bg-[#0b0c10] hover:bg-[#1f2833]/50 transition-all cursor-pointer">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-[#1f2833] rounded-lg">
                          <Activity className="w-5 h-5 text-[#66fcf1]" />
                        </div>
                        <div>
                          <h3 className="text-white font-medium">{wf.workflow_type || "Unknown Type"}</h3>
                          <div className="flex items-center gap-3 mt-1 text-xs text-[#45a29e]">
                            <span>ID: {wf.id.substring(0,8)}</span>
                            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> Updated: {new Date().toLocaleTimeString()}</span>
                          </div>
                        </div>
                      </div>
                      <div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold capitalize
                          ${wf.status === 'completed' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 
                            wf.status === 'failed' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                            'bg-[#66fcf1]/10 text-[#66fcf1] border border-[#66fcf1]/20'}`}>
                          {wf.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function StatCard({ title, value, icon }: { title: string, value: string, icon: React.ReactNode }) {
  return (
    <div className="glass-panel p-6 rounded-2xl border border-[#1f2833] bg-gradient-to-br from-[#1f2833]/30 to-[#0b0c10]/80 backdrop-blur-xl hover:border-[#45a29e]/40 transition-colors shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-[#c5c6c7] font-medium text-sm">{title}</h3>
        <div className="p-2 bg-[#0b0c10] rounded-lg border border-[#1f2833]">{icon}</div>
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  );
}
