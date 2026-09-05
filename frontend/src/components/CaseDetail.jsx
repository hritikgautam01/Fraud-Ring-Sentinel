import React, { useState, useMemo } from 'react';
import { 
  ShieldCheck, AlertTriangle, FileText, Cpu, Network, Activity, 
  CheckCircle, HelpCircle, Lock, Sparkles, AlertOctagon, User, DollarSign, Clock,
  ZoomIn, ZoomOut, RefreshCw, Layers, TrendingUp, Repeat
} from 'lucide-react';

const NODE_COLORS = {
  USER: { bg: '#0284c7', text: '#ffffff', border: '#38bdf8' },
  IP: { bg: '#9333ea', text: '#ffffff', border: '#c084fc' },
  DEVICE: { bg: '#2563eb', text: '#ffffff', border: '#60a5fa' },
  CARD: { bg: '#d97706', text: '#ffffff', border: '#fbbf24' },
  MERCHANT: { bg: '#059669', text: '#ffffff', border: '#34d399' },
  UNKNOWN: { bg: '#64748b', text: '#ffffff', border: '#94a3b8' }
};

export default function CaseDetail({ caseData, reportData, subgraphData, loading }) {
  const [activeTab, setActiveTab] = useState('summary');
  const [selectedNode, setSelectedNode] = useState(null);

  // Simplistic Cycle & Ring Graph Layout Computation (MAX 8-10 Focused Nodes)
  const cycleGraphLayout = useMemo(() => {
    if (!subgraphData || !subgraphData.nodes || subgraphData.nodes.length === 0) {
      return { nodes: [], edges: [], hasCycle: false };
    }

    const rawNodes = subgraphData.nodes;
    const rawEdges = subgraphData.edges;

    // 1. Identify Target Seed User
    const seedNode = rawNodes.find(n => n.is_seed) || rawNodes[0];
    const seedId = seedNode.id;

    // 2. Find Direct Infrastructure Entities Connected to Seed User
    const directEdges = rawEdges.filter(e => e.source === seedId || e.target === seedId);
    const directInfraIds = new Set();
    directEdges.forEach(e => {
      const otherId = e.source === seedId ? e.target : e.source;
      const otherNode = rawNodes.find(n => n.id === otherId);
      if (otherNode && otherNode.type !== 'USER') {
        directInfraIds.add(otherId);
      }
    });

    // 3. Find Top Connected Peer Users Sharing Those Entities (Max 3 peer users to keep graph clean)
    const peerUserIds = new Set();
    rawEdges.forEach(e => {
      if (directInfraIds.has(e.source) || directInfraIds.has(e.target)) {
        const uId = directInfraIds.has(e.source) ? e.target : e.source;
        const uNode = rawNodes.find(n => n.id === uId);
        if (uNode && uNode.type === 'USER' && uId !== seedId && peerUserIds.size < 3) {
          peerUserIds.add(uId);
        }
      }
    });

    // Combine into compact node set (Seed User + Direct Infra + Peer Users)
    const compactNodeIds = new Set([seedId, ...directInfraIds, ...peerUserIds]);
    const compactNodes = rawNodes.filter(n => compactNodeIds.has(n.id));
    const compactEdges = rawEdges.filter(e => compactNodeIds.has(e.source) && compactNodeIds.has(e.target));

    // Position Nodes in a Clean Circular Ring Layout showing Cycles
    const width = 560;
    const height = 280;
    const centerX = width / 2;
    const centerY = height / 2;

    const radius = 105;

    // Put Target Seed User at Top Center
    const positionedNodes = compactNodes.map((node, idx) => {
      if (node.id === seedId) {
        return { ...node, x: centerX, y: centerY - 80 };
      }

      // Arrange remaining nodes evenly in a ring
      const nonSeedList = compactNodes.filter(n => n.id !== seedId);
      const nonSeedIdx = nonSeedList.findIndex(n => n.id === node.id);
      const angle = ((nonSeedIdx + 1) / (nonSeedList.length + 1)) * Math.PI * 2 - Math.PI / 2;

      return {
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    const nodeMap = new Map(positionedNodes.map(n => [n.id, n]));

    const layoutEdges = compactEdges.map(edge => ({
      ...edge,
      sourceNode: nodeMap.get(edge.source),
      targetNode: nodeMap.get(edge.target)
    })).filter(e => e.sourceNode && e.targetNode);

    const hasCycle = peerUserIds.size > 0 && directInfraIds.size > 0;

    return { nodes: positionedNodes, edges: layoutEdges, hasCycle };
  }, [subgraphData]);

  if (loading) {
    return (
      <div className="saas-card rounded-3xl p-12 text-center text-slate-500 space-y-3">
        <div className="w-8 h-8 border-3 border-[#FF7B42] border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm font-semibold text-[#1E2022]">Lazy-loading LLM Investigation Report...</p>
        <p className="text-xs text-slate-400">Retrieving graph topology & evidence synthesis contracts</p>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="saas-card rounded-3xl p-12 text-center text-slate-500 text-sm font-medium">
        Select a case from the triage queue to view full evidence synthesis.
      </div>
    );
  }

  const { decision, transaction_summary, ml_evidence, graph_evidence, behavioral_evidence, benign_evidence } = caseData;
  const report = reportData || {};

  return (
    <div key={caseData.case_id} className="space-y-6 animate-fade-in">

      {/* Case Header Card */}
      <div className="saas-card rounded-3xl p-6 space-y-5">
        
        {/* Top Title & Deterministic Badges */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-2xl font-extrabold text-[#1E2022] font-sans tracking-tight">{caseData.case_id}</h2>
              <span className="text-xs px-3 py-1 rounded-full bg-[#F8F7F4] text-slate-600 font-mono border border-slate-200/80 font-medium">
                Txn: {transaction_summary.target_transaction_id}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1.5 font-medium">
              Target User <span className="font-mono text-slate-800 font-semibold">{transaction_summary.target_user_id}</span> • 
              Amount <span className="font-mono text-[#059669] font-extrabold text-sm ml-1">${transaction_summary.amount.toFixed(2)}</span>
            </p>
          </div>

          {/* Action & Risk Score */}
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Deterministic Score</div>
              <div className="text-3xl font-extrabold font-mono text-[#1E2022] tracking-tight">
                {(decision.risk_score * 100).toFixed(1)}%
              </div>
            </div>
            
            <div className="flex flex-col items-end gap-1">
              <span className={`px-4 py-1.5 rounded-full text-xs font-extrabold shadow-xs ${
                decision.action === 'INVESTIGATE' 
                  ? 'bg-[#FFDFD0] text-[#D9531E] border border-[#FF7B42]/30' 
                  : decision.action === 'MONITOR'
                  ? 'bg-[#FEF08A] text-[#854D0E] border border-[#EAB308]/30'
                  : 'bg-[#A7F3D0] text-[#065F46] border border-[#10B981]/30'
              }`}>
                {decision.action}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                Threshold: {(decision.threshold_applied * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-3 border-t border-slate-100">
          <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
            <div className="text-slate-500 font-medium text-[11px]">Connected Users</div>
            <div className="text-base font-bold text-[#1E2022] font-mono mt-0.5">{transaction_summary.connected_users_count}</div>
          </div>

          <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
            <div className="text-slate-500 font-medium text-[11px]">Shared Devices</div>
            <div className="text-base font-bold text-[#1E2022] font-mono mt-0.5">{transaction_summary.connected_devices_count}</div>
          </div>

          <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
            <div className="text-slate-500 font-medium text-[11px]">Shared IPs</div>
            <div className="text-base font-bold text-[#1E2022] font-mono mt-0.5">{transaction_summary.connected_ips_count}</div>
          </div>

          <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
            <div className="text-slate-500 font-medium text-[11px]">Shared Cards</div>
            <div className="text-base font-bold text-[#1E2022] font-mono mt-0.5">{transaction_summary.connected_cards_count}</div>
          </div>
        </div>
      </div>

      {/* LLM Synthesis Card */}
      <div className="saas-card rounded-3xl p-6 border border-orange-200/80 bg-gradient-to-r from-[#FFFBF8] via-[#FFF8F3] to-[#FFFBF5] space-y-4 shadow-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-[#FF7B42]/10 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-[#FF7B42]" />
            </div>
            <h3 className="font-extrabold text-[#1E2022] text-base">LLM Investigator Synthesis</h3>
          </div>
          <span className="text-[11px] px-3 py-1 rounded-full bg-white text-[#FF7B42] border border-orange-200 font-semibold shadow-xs">
            Read-Only Explanation
          </span>
        </div>

        {/* Narrative Summary */}
        <div className="text-xs text-slate-700 leading-relaxed bg-white p-4 rounded-2xl border border-orange-100/80 shadow-xs font-medium">
          {report.investigation_summary || "Generating LLM synthesis report..."}
        </div>

        {/* Why Flagged Bullet Points */}
        {report.why_flagged && report.why_flagged.length > 0 && (
          <div>
            <h4 className="text-[11px] font-bold text-slate-400 mb-2 uppercase tracking-wider">Primary Risk Indicators:</h4>
            <ul className="space-y-2 text-xs text-slate-700">
              {report.why_flagged.map((item, i) => (
                <li key={i} className="flex items-start gap-2.5 bg-white p-3 rounded-xl border border-orange-100/60 shadow-xs font-medium">
                  <span className="w-2 h-2 rounded-full bg-[#FF7B42] mt-1.5 shrink-0"></span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Evidence Layers Tabs */}
      <div className="saas-card rounded-3xl p-6 space-y-5">
        
        {/* Navigation Bar */}
        <div className="flex border-b border-slate-100 bg-[#F8F7F4] p-1.5 rounded-2xl gap-1">
          <button
            onClick={() => setActiveTab('summary')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'summary'
                ? 'bg-[#1E2022] text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
            }`}
          >
            <Cpu className="w-4 h-4" />
            <span>ML Baseline Evidence</span>
          </button>

          <button
            onClick={() => setActiveTab('graph')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'graph'
                ? 'bg-[#1E2022] text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
            }`}
          >
            <Network className="w-4 h-4" />
            <span>Graph Ring Cycles</span>
          </button>

          <button
            onClick={() => setActiveTab('behavioral')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'behavioral'
                ? 'bg-[#1E2022] text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Behavioral Velocity</span>
          </button>
        </div>

        {/* Tab Content */}
        <div key={activeTab} className="text-xs space-y-4 animate-fade-in">
          
          {/* TAB 1: ML BASELINE */}
          {activeTab === 'summary' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#F8F7F4] p-4 rounded-2xl border border-slate-200/60">
                  <div className="text-slate-500 font-medium">Model Instance</div>
                  <div className="text-[#1E2022] font-extrabold font-mono text-sm mt-1">{ml_evidence.ml_model_name}</div>
                </div>

                <div className="bg-[#F8F7F4] p-4 rounded-2xl border border-slate-200/60">
                  <div className="text-slate-500 font-medium">Anomaly Score</div>
                  <div className="text-[#FF7B42] font-extrabold font-mono text-base mt-1">
                    {(ml_evidence.predicted_probability * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="p-4 bg-[#F8F7F4] rounded-2xl border border-slate-200/60 text-slate-700 font-medium leading-relaxed">
                {report.supporting_evidence?.ml_evidence || `ML predicted probability of ${(ml_evidence.predicted_probability*100).toFixed(1)}%`}
              </div>
            </div>
          )}

          {/* TAB 2: GRAPH INFRASTRUCTURE + RING & CYCLE TOPOLOGY DIAGRAM */}
          {activeTab === 'graph' && (
            <div className="space-y-4">
              
              {/* Data Figures Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
                  <div className="text-slate-500 font-medium text-[11px]">User / IP Ratio</div>
                  <div className="text-base font-extrabold text-[#1E2022] font-mono mt-0.5">{graph_evidence.user_to_ip_ratio}</div>
                </div>

                <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
                  <div className="text-slate-500 font-medium text-[11px]">User / Device Ratio</div>
                  <div className="text-base font-extrabold text-[#1E2022] font-mono mt-0.5">{graph_evidence.user_to_device_ratio}</div>
                </div>

                <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
                  <div className="text-slate-500 font-medium text-[11px]">Merchant Conc.</div>
                  <div className="text-base font-extrabold text-[#1E2022] font-mono mt-0.5">{(graph_evidence.merchant_concentration * 100).toFixed(0)}%</div>
                </div>
              </div>

              {/* Text Description */}
              <div className="p-4 bg-[#F8F7F4] rounded-2xl border border-slate-200/60 text-slate-700 font-medium">
                {report.supporting_evidence?.graph_evidence || `Infrastructure cluster contains ${graph_evidence.users_count} users across ${graph_evidence.ips_count} IPs.`}
              </div>

              {/* RING & CYCLE TOPOLOGY DIAGRAM */}
              <div className="border border-slate-800 rounded-2xl overflow-hidden bg-[#1E2022] text-white space-y-2 shadow-xs">
                <div className="p-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Repeat className="w-4 h-4 text-[#A7F3D0]" />
                    <span className="font-bold text-slate-100 text-xs">Infrastructure Sharing Cycle & Ring Diagram</span>
                  </div>
                  <span className={`text-[10px] font-mono font-bold px-3 py-1 rounded-full border ${
                    cycleGraphLayout.hasCycle 
                      ? 'bg-[#FFDFD0] text-[#D9531E] border-[#FF7B42]/40' 
                      : 'bg-[#A7F3D0] text-[#065F46] border-[#10B981]/40'
                  }`}>
                    {cycleGraphLayout.hasCycle ? '⚠️ Closed Infrastructure Ring Detected' : '✓ Normal Tree Topology'}
                  </span>
                </div>

                {/* Simplistic Ring SVG Render */}
                <div className="relative h-64 bg-[#1E2022] overflow-hidden flex items-center justify-center">
                  <svg className="w-full h-full" viewBox="0 0 560 280">
                    {/* Connection Edges */}
                    {cycleGraphLayout.edges.map((edge, i) => (
                      <g key={i}>
                        <line
                          x1={edge.sourceNode.x}
                          y1={edge.sourceNode.y}
                          x2={edge.targetNode.x}
                          y2={edge.targetNode.y}
                          stroke="#94a3b8"
                          strokeWidth="1.8"
                          strokeDasharray={edge.relation === 'USES' ? 'none' : '4,4'}
                          opacity="0.8"
                        />
                      </g>
                    ))}

                    {/* Nodes */}
                    {cycleGraphLayout.nodes.map((node) => {
                      const color = NODE_COLORS[node.type] || NODE_COLORS.UNKNOWN;
                      const isSeed = node.is_seed;

                      return (
                        <g
                          key={node.id}
                          transform={`translate(${node.x}, ${node.y})`}
                          onClick={() => setSelectedNode(node)}
                          className="cursor-pointer"
                        >
                          {/* Seed Pulse Indicator */}
                          {isSeed && (
                            <circle
                              r="20"
                              fill="none"
                              stroke="#38bdf8"
                              strokeWidth="2"
                              className="animate-ping"
                              opacity="0.6"
                            />
                          )}

                          <circle
                            r={isSeed ? "16" : "12"}
                            fill={color.bg}
                            stroke={color.border}
                            strokeWidth="2"
                            className="transition-transform hover:scale-125"
                          />

                          <text
                            y="24"
                            textAnchor="middle"
                            fill="#f8fafc"
                            fontSize="9"
                            fontWeight={isSeed ? "bold" : "normal"}
                            className="font-mono pointer-events-none"
                          >
                            {node.label}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                </div>

                {/* Ring Diagram Legend */}
                <div className="p-2.5 bg-slate-900/90 border-t border-slate-800 flex flex-wrap gap-3 text-[10px] justify-center text-slate-300 font-mono">
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#0284c7]"></span> Target User</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#9333ea]"></span> Shared IP</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#2563eb]"></span> Shared Device</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#d97706]"></span> Shared Card</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#059669]"></span> Merchant</span>
                </div>
              </div>

            </div>
          )}

          {/* TAB 3: BEHAVIORAL VELOCITY + VISUAL CHART */}
          {activeTab === 'behavioral' && (
            <div className="space-y-4">
              
              {/* Data Figures Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
                  <div className="text-slate-500 font-medium text-[11px]">Account Age</div>
                  <div className="text-base font-extrabold text-[#1E2022] font-mono mt-0.5">{behavioral_evidence.account_age_days} Days</div>
                </div>

                <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
                  <div className="text-slate-500 font-medium text-[11px]">Hourly Velocity</div>
                  <div className="text-base font-extrabold text-[#1E2022] font-mono mt-0.5">{behavioral_evidence.transactions_last_hour} txns/hr</div>
                </div>

                <div className="bg-[#F8F7F4] p-3 rounded-2xl border border-slate-200/60">
                  <div className="text-slate-500 font-medium text-[11px]">Failed Payments</div>
                  <div className="text-base font-extrabold text-[#1E2022] font-mono mt-0.5">{behavioral_evidence.failed_transactions} Declines</div>
                </div>
              </div>

              {/* Text Description */}
              <div className="p-4 bg-[#F8F7F4] rounded-2xl border border-slate-200/60 text-slate-700 font-medium">
                {report.supporting_evidence?.behavioral_evidence || `Account age ${behavioral_evidence.account_age_days} days with velocity ${behavioral_evidence.transactions_last_hour} txns/hr.`}
              </div>

              {/* VISUAL BEHAVIORAL VELOCITY CHART & TIMELINE */}
              <div className="border border-slate-200/80 rounded-2xl p-5 bg-[#F8F7F4] space-y-4">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#FF7B42]" />
                    <span className="font-bold text-[#1E2022] text-xs">Behavioral Velocity Chart & Maturity Gauge</span>
                  </div>
                  <span className="text-[10px] font-mono text-[#D9531E] bg-[#FFDFD0] px-2.5 py-0.5 rounded-full font-bold">
                    Real-time Metrics
                  </span>
                </div>

                {/* Velocity Bar Chart */}
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-[11px] mb-1.5 font-medium">
                      <span className="text-slate-700">Hourly Velocity ({behavioral_evidence.transactions_last_hour} txns/hr)</span>
                      <span className="text-slate-500 font-mono">Risk Threshold: 3.0 txns/hr</span>
                    </div>
                    <div className="h-4 bg-white rounded-lg overflow-hidden border border-slate-200 relative">
                      <div
                        className={`h-full transition-all rounded-lg ${
                          behavioral_evidence.transactions_last_hour >= 3 ? 'bg-[#FF7B42]' : 'bg-[#A7F3D0]'
                        }`}
                        style={{ width: `${Math.min(100, (behavioral_evidence.transactions_last_hour / 6) * 100)}%` }}
                      ></div>
                      <div className="absolute top-0 bottom-0 left-[50%] border-r-2 border-dashed border-rose-500" title="Threshold: 3 txns/hr"></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px] mb-1.5 font-medium">
                      <span className="text-slate-700">Daily Velocity ({behavioral_evidence.transactions_last_day} txns/day)</span>
                      <span className="text-slate-500 font-mono">Risk Threshold: 8.0 txns/day</span>
                    </div>
                    <div className="h-4 bg-white rounded-lg overflow-hidden border border-slate-200 relative">
                      <div
                        className={`h-full transition-all rounded-lg ${
                          behavioral_evidence.transactions_last_day >= 8 ? 'bg-[#FF7B42]' : 'bg-[#A7F3D0]'
                        }`}
                        style={{ width: `${Math.min(100, (behavioral_evidence.transactions_last_day / 15) * 100)}%` }}
                      ></div>
                      <div className="absolute top-0 bottom-0 left-[53%] border-r-2 border-dashed border-rose-500" title="Threshold: 8 txns/day"></div>
                    </div>
                  </div>
                </div>

                {/* Account Age Maturity Timeline Bar */}
                <div className="pt-3 border-t border-slate-200">
                  <div className="flex justify-between text-[11px] mb-1.5 font-medium">
                    <span className="text-slate-700">Account Maturity ({behavioral_evidence.account_age_days} Days Old)</span>
                    <span className="text-slate-500 font-mono">
                      {behavioral_evidence.account_age_days >= 30 ? '✓ Seasoned (≥30d)' : '⚠️ New Account (<30d)'}
                    </span>
                  </div>
                  <div className="h-3 bg-white rounded-lg overflow-hidden border border-slate-200 relative">
                    <div
                      className={`h-full transition-all rounded-lg ${
                        behavioral_evidence.account_age_days >= 30 ? 'bg-[#A7F3D0]' : 'bg-[#FEF08A]'
                      }`}
                      style={{ width: `${Math.min(100, (behavioral_evidence.account_age_days / 60) * 100)}%` }}
                    ></div>
                    <div className="absolute top-0 bottom-0 left-[50%] border-r border-slate-400" title="30-Day Benchmark"></div>
                  </div>
                </div>
              </div>

            </div>
          )}

        </div>
      </div>

      {/* Guardrail Banner: GRAPH CONNECTION != FRAUD */}
      <div className="saas-card rounded-3xl p-5 border border-orange-200 bg-[#FFF5F2] space-y-2">
        <div className="flex items-center gap-2 text-[#D9531E] font-bold text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 text-[#FF7B42]" />
          <span>GRAPH CONNECTION != FRAUD — Benign Context & Limitations</span>
        </div>

        <div className="text-xs text-slate-700 space-y-2 pt-1">
          <p className="bg-white p-3 rounded-xl border border-orange-100 shadow-xs">
            <strong className="text-[#1E2022]">Benign Considerations:</strong> {report.benign_considerations || "No benign network pattern detected."}
          </p>
          <p className="bg-white p-3 rounded-xl border border-orange-100 shadow-xs">
            <strong className="text-[#1E2022]">Limitations:</strong> {report.limitations || "Graph connectivity alone is contextual evidence and does not establish fraudulent intent."}
          </p>
        </div>
      </div>

      {/* Analyst Action Panel */}
      <div className="saas-card rounded-3xl p-5 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 font-extrabold text-[#1E2022]">
            <ShieldCheck className="w-4 h-4 text-[#059669]" />
            <span>Human Analyst Guidance</span>
          </div>
          <span className="font-mono text-slate-500 font-semibold text-[11px]">Action: {decision.action}</span>
        </div>
        <p className="text-xs text-slate-700 bg-[#F8F7F4] p-4 rounded-2xl border border-slate-200/60 leading-relaxed font-medium">
          {report.analyst_recommendation || "Review connected entities before final action."}
        </p>
      </div>

    </div>
  );
}

