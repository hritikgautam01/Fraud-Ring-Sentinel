import React, { useState } from 'react';
import { ShieldAlert, Cpu, Network, Zap, CheckCircle2, AlertTriangle, X, Info, Sliders, Layers } from 'lucide-react';

export default function Header() {
  const [activeModal, setActiveModal] = useState(null); // 'rf' | 'graph' | 'fusion' | null

  return (
    <>
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          
          {/* Left: Branding */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FF7B42] flex items-center justify-center shadow-md shadow-[#FF7B42]/20">
              <ShieldAlert className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-extrabold text-[#1E2022] tracking-tight">Fraud Ring Sentinel</h1>
                <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 bg-orange-50 text-[#FF7B42] border border-orange-200 rounded-full">
                  Track 02: AI Risk Manager
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">Coordinated Payment Abuse Intelligence & Investigation Platform</p>
            </div>
          </div>

          {/* Center/Right: Interactive Pipeline Model Buttons */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            
            {/* Button 1: RandomForest Baseline */}
            <button
              onClick={() => setActiveModal('rf')}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1E2022] text-white hover:bg-black transition-all cursor-pointer shadow-xs group"
              title="Click to view Random Forest model specs"
            >
              <Cpu className="w-3.5 h-3.5 text-blue-400 group-hover:scale-110 transition-transform" />
              <span className="font-semibold">RandomForest Baseline</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/20 text-white font-mono">40% Wt</span>
            </button>

            {/* Button 2: NetworkX Topology */}
            <button
              onClick={() => setActiveModal('graph')}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1E2022] text-white hover:bg-black transition-all cursor-pointer shadow-xs group"
              title="Click to view NetworkX graph topology specs"
            >
              <Network className="w-3.5 h-3.5 text-purple-400 group-hover:scale-110 transition-transform" />
              <span className="font-semibold">NetworkX Topology</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/20 text-white font-mono">35% Wt</span>
            </button>

            {/* Button 3: Fusion Risk Engine */}
            <button
              onClick={() => setActiveModal('fusion')}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1E2022] text-white hover:bg-black transition-all cursor-pointer shadow-xs group"
              title="Click to view Fusion Risk Engine weight matrix"
            >
              <Zap className="w-3.5 h-3.5 text-amber-400 group-hover:scale-110 transition-transform" />
              <span className="font-semibold">Fusion Risk Engine</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/20 text-white font-mono">Policy</span>
            </button>

            {/* System Status Indicator */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#A7F3D0] text-[#065F46] border border-[#10B981]/30 font-extrabold text-xs shadow-xs">
              <span className="w-2 h-2 rounded-full bg-[#059669] animate-pulse-subtle"></span>
              <span>SYSTEM ONLINE</span>
            </div>
          </div>
        </div>

        {/* Decision Authority Notice Bar */}
        <div className="bg-[#FFF5F2] border-t border-b border-orange-200/60 px-4 py-2 text-xs text-[#9A3412]">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 font-semibold">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-[#FF7B42]" />
              <span>Sole Decision Engine: Fusion Risk Engine (Deterministic Policy)</span>
            </div>
            <div className="hidden md:flex items-center gap-2 text-slate-600 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#059669] shrink-0" />
              <span>LLM Investigator acts strictly as explanation layer (Read-Only)</span>
            </div>
          </div>
        </div>
      </header>

      {/* Viewport-Centered Interactive Modal Overlay */}
      {activeModal && (
        <div 
          className="fixed inset-0 z-[999] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fade-in"
          onClick={() => setActiveModal(null)}
        >
          <div 
            className="bg-white w-full max-w-lg rounded-3xl border border-slate-200/80 shadow-2xl overflow-hidden my-auto max-h-[85vh] flex flex-col animate-pop-in"
            onClick={(e) => e.stopPropagation()}
          >
            
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-100 bg-[#F8F7F4] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2.5">
                {activeModal === 'rf' && <Cpu className="w-5 h-5 text-blue-600" />}
                {activeModal === 'graph' && <Network className="w-5 h-5 text-purple-600" />}
                {activeModal === 'fusion' && <Zap className="w-5 h-5 text-amber-600" />}
                <h3 className="font-extrabold text-[#1E2022] text-base">
                  {activeModal === 'rf' && 'RandomForest Baseline Model'}
                  {activeModal === 'graph' && 'NetworkX Graph Topology Engine'}
                  {activeModal === 'fusion' && 'Fusion Risk Engine & Weight Matrix'}
                </h3>
              </div>
              <button
                onClick={() => setActiveModal(null)}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-full hover:bg-slate-200/60 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 text-xs text-slate-700 space-y-4 overflow-y-auto flex-1">
              {activeModal === 'rf' && (
                <div className="space-y-3">
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-2xl text-slate-800">
                    <strong className="text-blue-950 font-bold">Single-Transaction ML Anomaly Predictor</strong>
                    <p className="text-slate-600 text-[11px] mt-1 font-medium leading-relaxed">
                      Supervised Random Forest trained on payment transactions to detect individual transaction anomalies.
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 font-mono text-[11px]">
                    <div className="bg-[#F8F7F4] p-3 rounded-xl border border-slate-200">
                      <span className="text-slate-500 font-sans block">Model Type</span>
                      <span className="text-blue-700 font-bold">RandomForest (100 trees)</span>
                    </div>
                    <div className="bg-[#F8F7F4] p-3 rounded-xl border border-slate-200">
                      <span className="text-slate-500 font-sans block">Fusion Weight</span>
                      <span className="text-blue-700 font-bold">40% of Total Score</span>
                    </div>
                  </div>

                  <div>
                    <span className="text-slate-500 font-bold uppercase text-[10px] block mb-1.5">Input Feature Vector (7 Features):</span>
                    <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
                      {['amount', 'account_age_days', 'transactions_last_hour', 'transactions_last_day', 'failed_transactions', 'unique_devices', 'unique_cards'].map(f => (
                        <span key={f} className="px-2.5 py-1 bg-[#F8F7F4] border border-slate-200 rounded-lg text-slate-700 font-semibold">{f}</span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeModal === 'graph' && (
                <div className="space-y-3">
                  <div className="p-4 bg-purple-50 border border-purple-200 rounded-2xl text-slate-800">
                    <strong className="text-purple-950 font-bold">Heterogeneous Infrastructure Network Graph</strong>
                    <p className="text-slate-600 text-[11px] mt-1 font-medium leading-relaxed">
                      Dynamic multi-entity graph builder discovering shared hardware devices, IP proxies, cards, and merchants.
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 font-mono text-[11px]">
                    <div className="bg-[#F8F7F4] p-3 rounded-xl border border-slate-200">
                      <span className="text-slate-500 font-sans block">Graph Schema</span>
                      <span className="text-purple-700 font-bold">NetworkX Multi-Entity</span>
                    </div>
                    <div className="bg-[#F8F7F4] p-3 rounded-xl border border-slate-200">
                      <span className="text-slate-500 font-sans block">Fusion Weight</span>
                      <span className="text-purple-700 font-bold">35% of Total Score</span>
                    </div>
                  </div>

                  <div>
                    <span className="text-slate-500 font-bold uppercase text-[10px] block mb-1.5">Entity Node Taxonomy:</span>
                    <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                      <span className="p-2 bg-sky-50 border border-sky-200 text-sky-800 font-semibold rounded-xl">USER (Accounts)</span>
                      <span className="p-2 bg-purple-50 border border-purple-200 text-purple-800 font-semibold rounded-xl">IP (IP Addresses)</span>
                      <span className="p-2 bg-blue-50 border border-blue-200 text-blue-800 font-semibold rounded-xl">DEVICE (Hardware)</span>
                      <span className="p-2 bg-amber-50 border border-amber-200 text-amber-800 font-semibold rounded-xl">CARD (Payment)</span>
                      <span className="p-2 bg-emerald-50 border border-emerald-200 text-emerald-800 font-semibold rounded-xl">MERCHANT (Sellers)</span>
                    </div>
                  </div>
                </div>
              )}

              {activeModal === 'fusion' && (
                <div className="space-y-3">
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-slate-800">
                    <strong className="text-amber-950 font-bold">Multi-Signal Fusion Risk Engine</strong>
                    <p className="text-slate-600 text-[11px] mt-1 font-medium leading-relaxed">
                      Combines single-transaction ML, graph cluster topology, and velocity signals into a unified risk score.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <span className="text-slate-500 font-bold uppercase text-[10px] block">Multi-Signal Weight Breakdown:</span>
                    
                    <div className="space-y-2 font-mono text-[11px]">
                      <div className="flex items-center justify-between bg-[#F8F7F4] p-3 rounded-xl border border-slate-200">
                        <span className="text-blue-700 font-bold">1. Transaction ML Anomaly Score</span>
                        <span className="text-slate-900 font-extrabold">40% Weight</span>
                      </div>

                      <div className="flex items-center justify-between bg-[#F8F7F4] p-3 rounded-xl border border-slate-200">
                        <span className="text-purple-700 font-bold">2. Graph Structural Risk</span>
                        <span className="text-slate-900 font-extrabold">35% Weight</span>
                      </div>

                      <div className="flex items-center justify-between bg-[#F8F7F4] p-3 rounded-xl border border-slate-200">
                        <span className="text-amber-700 font-bold">3. Behavioral Velocity & Age</span>
                        <span className="text-slate-900 font-extrabold">25% Weight</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-[#F8F7F4] rounded-2xl border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between font-mono text-[11px]">
                      <span className="text-slate-600 font-medium">Decision Threshold</span>
                      <span className="text-[#D9531E] font-bold">Combined Risk ≥ 0.45 (45%)</span>
                    </div>
                    <div className="flex items-center justify-between font-mono text-[11px]">
                      <span className="text-slate-600 font-medium">Benign Suppressor Factor</span>
                      <span className="text-[#059669] font-bold">0.25 (75% Risk Reduction)</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-100 bg-[#F8F7F4] flex justify-end shrink-0">
              <button
                onClick={() => setActiveModal(null)}
                className="px-5 py-2 bg-[#1E2022] hover:bg-black text-white rounded-full text-xs font-semibold transition-colors shadow-xs"
              >
                Close View
              </button>
            </div>

          </div>
        </div>
      )}
    </>
  );
}

