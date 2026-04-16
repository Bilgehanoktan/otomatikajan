"use client";

import { useList, useUpdate } from "@refinedev/core";
import { CheckSquare, XSquare, Cpu, Clock, AlertCircle } from "lucide-react";

export default function ApprovalsPage() {
  const { query: { data, isLoading, isError, refetch } } = useList({
    resource: "approvals",
    filters: [
      {
        field: "status",
        operator: "eq",
        value: "pending",
      },
    ],
  });

  const { mutate: updateApproval } = useUpdate();

  const handleDecision = (id: string, status: "approved" | "rejected") => {
    updateApproval({
       resource: "approvals",
       id,
       values: { status, comment: `Actioned via Control Plane at ${new Date().toISOString()}` },
    }, {
       onSuccess: () => refetch(),
    });
  };

  const requests = data?.data ?? [];

  return (
    <div className="min-h-screen p-8 background-gradient bg-[#0b0c10]">
      {/* HEADER */}
      <header className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-[#66fcf1]/10 rounded-xl backdrop-blur-md border border-[#66fcf1]/20 shadow-[0_0_15px_rgba(102,252,241,0.2)]">
            <CheckSquare className="w-8 h-8 text-[#66fcf1]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#c5c6c7]">
              Pending Approvals
            </h1>
            <p className="text-[#45a29e] tracking-widest text-sm font-medium uppercase mt-1">Operational Governance / L3-L4 Gates</p>
          </div>
        </div>
      </header>

      {/* CONTENT */}
      <section className="glass-panel rounded-2xl border border-[#1f2833] bg-[#0b0c10]/60 backdrop-blur-xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-[#1f2833] flex justify-between items-center bg-gradient-to-b from-transparent to-[#0b0c10]/40">
          <h2 className="text-xl font-semibold text-white">Manual Intervention Required</h2>
        </div>
        
        <div className="p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-2 border-[#66fcf1] border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : isError ? (
            <div className="text-red-400 p-4 rounded-lg bg-red-400/10 border border-red-400/20 text-center">
              Failed to load approval requests.
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {requests.length === 0 ? (
                <div className="text-center py-20 flex flex-col items-center gap-4">
                  <div className="p-4 bg-white/5 rounded-full">
                    <CheckSquare className="w-12 h-12 text-[#45a29e] opacity-20" />
                  </div>
                  <div className="text-[#45a29e] font-medium italic">All gates clear. No pending approvals.</div>
                </div>
              ) : (
                requests.map((req: any) => (
                  <div key={req.id} className="group p-6 rounded-xl border border-[#1f2833] bg-[#0b0c10] hover:bg-[#1f2833]/50 transition-all">
                    <div className="flex flex-col md:flex-row justify-between gap-6">
                      <div className="flex items-start gap-4">
                        <div className="p-2 bg-[#1f2833] rounded-lg mt-1">
                          <AlertCircle className={`w-5 h-5 ${req.request_type === 'budget' ? 'text-yellow-400' : 'text-[#66fcf1]'}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-3">
                            <h3 className="text-white font-semibold text-lg uppercase tracking-tight">{req.request_type} GATE</h3>
                            <span className="px-2 py-0.5 rounded bg-white/5 text-[10px] text-gray-500 font-mono">ID: {String(req.id).substring(0,8) || 'N/A'}</span>
                          </div>
                          <p className="text-[#c5c6c7] mt-2 max-w-2xl leading-relaxed">{req.reason}</p>
                          
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6">
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase text-gray-500 font-bold mb-1">Project ID</span>
                              <span className="text-xs text-[#66fcf1] font-mono">{String(req.project_id).substring(0,13) || 'N/A'}...</span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase text-gray-500 font-bold mb-1">Step</span>
                              <span className="text-xs text-white">{req.step_id || "Global"}</span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase text-gray-500 font-bold mb-1">Requested At</span>
                              <div className="flex items-center gap-1 text-xs text-gray-400">
                                <Clock className="w-3 h-3" />
                                <span>{new Date(req.created_at).toLocaleString()}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex md:flex-col justify-end items-center gap-3">
                        <button 
                          onClick={() => handleDecision(req.id, "approved")}
                          className="flex items-center gap-2 px-6 py-2.5 bg-[#66fcf1] text-black font-bold rounded-lg hover:bg-[#45a29e] transition-all shadow-[0_0_15px_rgba(102,252,241,0.2)]"
                        >
                          <CheckSquare size={18} />
                          Approve
                        </button>
                        <button 
                          onClick={() => handleDecision(req.id, "rejected")}
                          className="flex items-center gap-2 px-6 py-2.5 bg-red-500/10 text-red-400 border border-red-500/20 font-bold rounded-lg hover:bg-red-500/20 transition-all"
                        >
                          <XSquare size={18} />
                          Reject
                        </button>
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
