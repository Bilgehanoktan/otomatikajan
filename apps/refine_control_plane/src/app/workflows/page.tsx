"use client";

import { useList, useNavigation } from "@refinedev/core";
import { Activity, Clock, ChevronRight, PlayCircle, RotateCcw } from "lucide-react";

export default function WorkflowList() {
  const { query: { data, isLoading } } = useList({
    resource: "workflows",
  });
  const { show } = useNavigation();

  const workflows = data?.data ?? [];

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-10">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Active Workflows</h1>
          <p className="text-[#45a29e] text-sm mt-1">Real-time status of durable workflow instances</p>
        </div>
        <div className="flex gap-4">
          <button className="px-6 py-2.5 bg-[#66fcf1] text-black font-bold rounded-xl hover:shadow-[0_0_20px_rgba(102,252,241,0.4)] transition-all">
            New Project
          </button>
        </div>
      </div>

      <div className="glass-panel rounded-2xl border border-[#1f2833] bg-[#0b0c10]/40 backdrop-blur-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="px-6 py-4 text-xs font-semibold text-[#45a29e] uppercase tracking-wider text-center">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#45a29e] uppercase tracking-wider">Workflow Profile</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#45a29e] uppercase tracking-wider">Progress</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#45a29e] uppercase tracking-wider">Timeline</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#45a29e] uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center text-[#45a29e]">
                    <div className="flex justify-center">
                      <div className="w-6 h-6 border-2 border-[#66fcf1] border-t-transparent rounded-full animate-spin"></div>
                    </div>
                  </td>
                </tr>
              ) : workflows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center text-[#45a29e]">
                    No active workflows found.
                  </td>
                </tr>
              ) : (
                workflows.map((wf) => (
                  <tr 
                    key={wf.id} 
                    className="hover:bg-white/5 transition-colors cursor-pointer group"
                    onClick={() => wf.id && show("workflows", wf.id)}
                  >
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-flex items-center justify-center w-3 h-3 rounded-full 
                        ${wf.status === 'RUNNING' ? 'bg-[#66fcf1] animate-pulse shadow-[0_0_8px_#66fcf1]' : 
                          wf.status === 'COMPLETED' ? 'bg-green-400' : 
                          wf.status === 'FAILED' ? 'bg-red-400' : 'bg-gray-500'}`}
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-[#1f2833] flex items-center justify-center border border-white/5">
                          <Activity size={14} className="text-[#66fcf1]" />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-white uppercase tracking-tight">{wf.workflow_type || 'GENERAL_OPS'}</p>
                          <p className="text-[10px] text-[#45a29e] font-mono">ID: {String(wf.id).substring(0, 8) || 'N/A'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="w-full max-w-[120px]">
                        <div className="flex justify-between items-center mb-1 text-[10px] text-gray-400">
                           <span>Step {wf.current_step_index || 0}/{wf.steps?.length || 0}</span>
                        </div>
                        <div className="h-1.5 w-full bg-[#1f2833] rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-[#66fcf1] rounded-full" 
                            style={{ width: `${(wf.current_step_index || 0) / (wf.steps?.length || 1) * 100}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-[#c5c6c7] text-xs">
                       <div className="flex items-center gap-2">
                          <Clock size={12} className="text-[#45a29e]" />
                          <span>{wf.started_at ? new Date(wf.started_at).toLocaleTimeString() : 'N/A'}</span>
                       </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                         <button className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-[#66fcf1]">
                            <RotateCcw size={16} />
                         </button>
                         <button className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white">
                            <ChevronRight size={16} />
                         </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
