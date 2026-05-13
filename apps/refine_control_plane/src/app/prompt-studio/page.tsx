"use client";

import React, { useState, useEffect } from "react";
import { useCustom, useTranslate } from "@refinedev/core";
import { useTranslations } from "next-intl";
import {
  Brain,
  Search,
  Save,
  RotateCcw,
  Sparkles,
  ShieldCheck,
  Terminal,
  Cpu,
  Zap,
  ChevronRight,
  Code2,
  FileText,
  Trash2,
  Plus
} from "lucide-react";
import { Button, Input, List, Card, Badge, Empty, Skeleton, message, Popconfirm, Tooltip, Tag } from "antd";

interface Agent {
  name: string;
  description: string;
  model: string | null;
  tool_groups: string[] | null;
  soul?: string;
}

export default function PromptStudioPage() {
  const t = useTranslations("prompt_studio");
  const translate = useTranslate();
  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(null);
  const [soulContent, setSoulContent] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const { query: agentsQuery } = useCustom<{ agents: Agent[] }>({
    url: `/api/v1/harness/agents`,
    method: "get",
  });
  const { data: agentsData, isLoading } = agentsQuery;

  const { query: selectedAgentQuery } = useCustom<Agent>({
    url: `/api/v1/harness/agents/${selectedAgentName}`,
    method: "get",
    queryOptions: {
      enabled: !!selectedAgentName,
    },
  });
  const { data: selectedAgentData, isLoading: isAgentLoading } = selectedAgentQuery;

  useEffect(() => {
    if (selectedAgentData?.data?.soul) {
      setSoulContent(selectedAgentData.data.soul);
    }
  }, [selectedAgentData]);

  const handleSave = async () => {
    if (!selectedAgentName) return;
    setIsSaving(true);
    try {
      const response = await fetch(`/api/v1/harness/agents/${selectedAgentName}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          soul: soulContent,
        }),
      });

      if (response.ok) {
        message.success(translate("notifications.success", "Başarıyla kaydedildi"));
      } else {
        message.error(translate("notifications.error", "Hata oluştu"));
      }
    } catch (error) {
      message.error("Bağlantı hatası");
    } finally {
      setIsSaving(false);
    }
  };

  const filteredAgents = agentsData?.data?.agents.filter(a => 
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    a.description.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="min-h-screen bg-[#060a12] text-white p-4 lg:p-12 font-sans selection:bg-[var(--primary)] selection:text-black">
      {/* Header Area */}
      <header className="mb-12 flex flex-col lg:flex-row lg:items-end justify-between gap-8">
        <div className="space-y-4">
          <div className="flex items-center gap-4 text-[var(--primary)] mb-2">
            <div className="p-3 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 shadow-[0_0_20px_rgba(102,252,241,0.1)]">
              <Brain size={28} className="animate-pulse" />
            </div>
            <div className="h-px w-12 bg-gradient-to-r from-[var(--primary)]/50 to-transparent" />
            <span className="text-[10px] font-black uppercase tracking-[0.5em] italic opacity-70">Sovereign AGI Core</span>
          </div>
          <h1 className="text-5xl lg:text-7xl font-black tracking-tighter italic uppercase text-white">
            Prompt <span className="text-[var(--primary)]">Studio</span>
          </h1>
          <p className="text-gray-500 max-w-2xl text-lg font-medium leading-relaxed italic border-l-4 border-white/5 pl-6">
            {translate("prompt_studio.subtitle", "Define agent personalities, behavioral guardrails, and mission parameters.")}
          </p>
        </div>

        <div className="flex gap-4">
            <Button 
              type="primary" 
              icon={<Plus size={18} />}
              className="h-14 px-8 rounded-2xl bg-[var(--primary)] text-black font-black uppercase tracking-widest border-none hover:scale-105 transition-transform"
            >
              {translate("buttons.create", "YENI AJAN")}
            </Button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Left: Agent List */}
        <aside className="lg:col-span-4 space-y-6">
          <div className="glass-panel p-6 rounded-[2.5rem] border-white/5 bg-white/[0.012] shadow-2xl">
            <div className="relative mb-6">
              <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-600" size={18} />
              <Input 
                placeholder={translate("buttons.search", "Ajan ara...")}
                className="w-full bg-black/40 border-white/5 rounded-2xl h-14 pl-16 text-white font-bold italic placeholder:text-gray-700 focus:border-[var(--primary)]/30 transition-all"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
              {isLoading ? (
                Array(5).fill(0).map((_, i) => <Skeleton key={i} active avatar paragraph={{ rows: 1 }} className="p-4" />)
              ) : filteredAgents.length > 0 ? (
                filteredAgents.map(agent => (
                  <div 
                    key={agent.name}
                    onClick={() => setSelectedAgentName(agent.name)}
                    className={`group p-6 rounded-[2rem] border transition-all cursor-pointer relative overflow-hidden ${
                      selectedAgentName === agent.name 
                        ? "bg-[var(--primary)]/10 border-[var(--primary)]/30 shadow-[0_0_30px_rgba(102,252,241,0.05)]" 
                        : "bg-white/[0.01] border-white/5 hover:border-white/10 hover:bg-white/[0.02]"
                    }`}
                  >
                    <div className="flex items-center gap-4 relative z-10">
                      <div className={`p-3 rounded-xl border transition-colors ${
                        selectedAgentName === agent.name ? "bg-[var(--primary)]/20 border-[var(--primary)]/30 text-[var(--primary)]" : "bg-black/40 border-white/5 text-gray-600"
                      }`}>
                        <Cpu size={20} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className={`text-sm font-black uppercase tracking-tight italic transition-colors ${
                            selectedAgentName === agent.name ? "text-[var(--primary)]" : "text-white"
                          }`}>{agent.name}</h4>
                          <ChevronRight size={14} className={`transition-transform ${selectedAgentName === agent.name ? "rotate-90 text-[var(--primary)]" : "text-gray-700"}`} />
                        </div>
                        <p className="text-[11px] text-gray-500 font-bold truncate pr-4 italic">{agent.description || "No description"}</p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <Empty description={false} className="py-20 opacity-20" />
              )}
            </div>
          </div>
        </aside>

        {/* Right: Editor */}
        <main className="lg:col-span-8">
          {selectedAgentName ? (
            <div className="glass-panel rounded-[3rem] border-white/5 bg-white/[0.012] shadow-2xl flex flex-col min-h-[700px] animate-in slide-in-from-right-10 duration-700">
              {/* Editor Header */}
              <div className="p-8 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-6">
                  <div className="p-4 bg-[var(--primary)]/10 rounded-2xl border border-[var(--primary)]/20 text-[var(--primary)] shadow-[0_0_20px_rgba(102,252,241,0.1)]">
                    <Code2 size={24} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-black text-white italic uppercase tracking-tighter">{selectedAgentName} SOUL</h2>
                    <div className="flex items-center gap-3 mt-1">
                       <Tag className="bg-white/5 border-white/10 text-gray-500 text-[9px] font-black uppercase tracking-widest px-2">v2.4.0</Tag>
                       <span className="text-[10px] text-green-500 font-black uppercase tracking-widest flex items-center gap-1.5">
                         <div className="w-1 h-1 rounded-full bg-green-500 animate-pulse" />
                         Active Runtime
                       </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <Tooltip title="Reset to Defaults">
                    <Button 
                      icon={<RotateCcw size={18} />} 
                      className="bg-white/5 border-white/10 text-gray-400 h-12 w-12 rounded-xl hover:text-white transition-colors"
                    />
                  </Tooltip>
                  <Button 
                    type="primary"
                    icon={isSaving ? <RotateCcw size={18} className="animate-spin" /> : <Save size={18} />}
                    onClick={handleSave}
                    loading={isSaving}
                    className="h-12 px-8 rounded-xl bg-[var(--primary)] text-black font-black uppercase tracking-widest border-none hover:scale-105 transition-transform"
                  >
                    DEPLOY SOUL
                  </Button>
                </div>
              </div>

              {/* Editor Content */}
              <div className="flex-1 p-0 relative group">
                {isAgentLoading ? (
                  <div className="p-12 space-y-8">
                    <Skeleton active paragraph={{ rows: 10 }} />
                  </div>
                ) : (
                  <textarea 
                    className="w-full h-full min-h-[500px] bg-transparent p-12 text-gray-300 font-mono text-sm leading-relaxed resize-none border-none outline-none selection:bg-[var(--primary)] selection:text-black placeholder:text-gray-800"
                    value={soulContent}
                    onChange={e => setSoulContent(e.target.value)}
                    placeholder="# MISSION PARAMETERS\nDefine your agent's soul here..."
                    spellCheck={false}
                  />
                )}
                
                {/* Floating Meta */}
                <div className="absolute bottom-8 right-8 flex items-center gap-6 text-[10px] font-black text-gray-700 uppercase tracking-widest italic opacity-40 group-hover:opacity-100 transition-opacity">
                   <div className="flex items-center gap-2">
                     <FileText size={12} />
                     <span>Markdown Format</span>
                   </div>
                   <div className="flex items-center gap-2">
                     <Zap size={12} />
                     <span>Token Efficient</span>
                   </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel rounded-[3rem] border-white/5 bg-white/[0.012] shadow-2xl h-[700px] flex flex-col items-center justify-center p-12 text-center">
               <div className="p-10 bg-white/5 rounded-full border border-white/5 mb-8 relative">
                  <div className="absolute inset-0 bg-[var(--primary)]/5 rounded-full blur-3xl animate-pulse" />
                  <Brain size={64} className="text-gray-700 relative z-10" />
               </div>
               <h3 className="text-xl font-black text-white uppercase italic tracking-widest mb-4">{translate("prompt_studio.editor.empty.title", "Select an Agent Soul")}</h3>
               <p className="text-gray-600 font-bold max-w-sm italic leading-relaxed">
                 {translate("prompt_studio.editor.empty.description", "Access the neural templates of your autonomous entities to calibrate their core decision logic.")}
               </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
