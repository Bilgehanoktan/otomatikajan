"use client";

import { useList } from "@refinedev/core";
import { FileText, User, Tag, Clock, ChevronRight } from "lucide-react";

export default function AuditPage() {
  const { query: { data, isLoading, isError } } = useList({
    resource: "workflows", 
  });

  const logs = data?.data ?? [];

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 rounded-xl backdrop-blur-md border border-purple-500/20 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
            <FileText className="w-8 h-8 text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#c5c6c7]">
              System Audit Trail
            </h1>
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">Immutable Governance Logs</p>
          </div>
        </div>
      </header>

      {/* AUDIT LOG TABLE */}
      <section className="glass-panel rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-[#1f2833] flex justify-between items-center bg-gradient-to-b from-transparent to-[#0b0c10]/40">
          <h2 className="text-xl font-semibold text-white">Event Stream</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#1f2833] bg-white/5">
                <th className="p-4 text-[10px] uppercase text-gray-400 font-bold tracking-widest">Timestamp</th>
                <th className="p-4 text-[10px] uppercase text-gray-400 font-bold tracking-widest">Event Type</th>
                <th className="p-4 text-[10px] uppercase text-gray-400 font-bold tracking-widest">Resource</th>
                <th className="p-4 text-[10px] uppercase text-gray-400 font-bold tracking-widest">Actor</th>
                <th className="p-4 text-[10px] uppercase text-gray-400 font-bold tracking-widest text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="p-20 text-center">
                    <div className="w-6 h-6 border-2 border-[#66fcf1] border-t-transparent rounded-full animate-spin mx-auto"></div>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-20 text-center text-gray-500 italic">No events recorded in this cycle.</td>
                </tr>
              ) : (
                logs.map((log: any) => (
                  <tr key={log.id} className="border-b border-[#1f2833] hover:bg-white/5 transition-colors group">
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <Clock size={12} className="text-[#45a29e]" />
                        {new Date(log.created_at).toLocaleString()}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Tag size={12} className="text-[#66fcf1]" />
                        <span className="text-white text-xs font-semibold uppercase tracking-tighter">
                          {log.status === 'completed' ? 'WORKFLOW_SYNC' : 'SYSTEM_MUTATION'}
                        </span>
                      </div>
                    </td>
                    <td className="p-4 text-xs font-mono text-[#45a29e]">
                       {log.id.substring(0,18)}...
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-xs text-white">
                        <div className="w-5 h-5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center text-[8px] font-bold">A</div>
                        Architect
                      </div>
                    </td>
                    <td className="p-4 text-right">
                       <button className="p-1 px-2 rounded bg-white/5 border border-white/10 text-[#66fcf1] hover:bg-[#66fcf1] hover:text-black transition-all">
                          <ChevronRight size={14} />
                       </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
