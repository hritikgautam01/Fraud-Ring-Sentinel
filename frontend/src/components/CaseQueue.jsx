import React, { useState, useMemo } from 'react';
import { Search, ArrowUpDown, Filter, Shield, AlertCircle, Clock, Users, ArrowUpRight } from 'lucide-react';

export default function CaseQueue({ cases, selectedCaseId, onSelectCase, loading }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [actionFilter, setActionFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('risk_score');
  const [sortOrder, setSortOrder] = useState('desc');

  // Filter and Sort Cases locally
  const filteredCases = useMemo(() => {
    return cases.filter(c => {
      const matchSearch = 
        c.case_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.user_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.target_transaction_id.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchRisk = riskFilter === 'ALL' || c.risk_level === riskFilter;
      const matchAction = actionFilter === 'ALL' || c.action === actionFilter;

      return matchSearch && matchRisk && matchAction;
    }).sort((a, b) => {
      let valA = a[sortBy] ?? 0;
      let valB = b[sortBy] ?? 0;

      if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }

      if (sortOrder === 'asc') {
        return valA > valB ? 1 : -1;
      }
      return valA < valB ? 1 : -1;
    });
  }, [cases, searchTerm, riskFilter, actionFilter, sortBy, sortOrder]);

  // Risk Level Badge Styling (Signature Pastel Palette)
  const getRiskBadge = (level) => {
    switch (level) {
      case 'CRITICAL':
      case 'HIGH':
        return 'bg-[#FFDFD0] text-[#D9531E] border-[#FF7B42]/30';
      case 'MEDIUM':
        return 'bg-[#FEF08A] text-[#854D0E] border-[#EAB308]/30';
      case 'LOW':
      default:
        return 'bg-[#A7F3D0] text-[#065F46] border-[#10B981]/30';
    }
  };

  // Action Badge Styling
  const getActionBadge = (action) => {
    switch (action) {
      case 'INVESTIGATE':
        return 'bg-[#FF7B42] text-white shadow-xs';
      case 'MONITOR':
        return 'bg-[#FEF08A] text-[#854D0E]';
      case 'ALLOW':
      default:
        return 'bg-[#A7F3D0] text-[#065F46]';
    }
  };

  return (
    <div className="saas-card rounded-3xl border border-slate-100/80 bg-white overflow-hidden flex flex-col h-full shadow-[0_10px_30px_rgba(0,0,0,0.04)]">
      
      {/* Header & Controls Bar */}
      <div className="p-5 border-b border-slate-100 bg-[#F8F7F4] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-[#FF7B42]/10 flex items-center justify-center">
              <Shield className="w-4 h-4 text-[#FF7B42]" />
            </div>
            <h2 className="font-extrabold text-[#1E2022] text-base">Analyst Triage Queue</h2>
            <span className="text-xs px-3 py-1 rounded-full bg-white text-slate-700 border border-slate-200/80 font-mono shadow-xs font-semibold">
              {filteredCases.length} Cases
            </span>
          </div>
        </div>

        {/* Filters Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
          
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search Case / User..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-full text-[#1E2022] placeholder-slate-400 focus:outline-none focus:border-[#FF7B42] shadow-xs font-medium"
            />
          </div>

          {/* Risk Filter */}
          <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-full px-3 py-1.5 shadow-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-transparent text-[#1E2022] w-full focus:outline-none cursor-pointer font-medium"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>

          {/* Sort Control */}
          <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-full px-3 py-1.5 shadow-xs">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field);
                setSortOrder(order);
              }}
              className="bg-transparent text-[#1E2022] w-full focus:outline-none cursor-pointer font-medium"
            >
              <option value="risk_score-desc">Highest Risk Score</option>
              <option value="risk_score-asc">Lowest Risk Score</option>
              <option value="amount-desc">Highest Amount ($)</option>
              <option value="connected_users_count-desc">Largest Cluster</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-y-auto flex-1 max-h-[600px]">
        {loading ? (
          <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
            <div className="w-5 h-5 border-2 border-[#FF7B42] border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm font-semibold">Loading Triage Cases...</span>
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm font-medium">
            No matching investigation cases found.
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-[#F8F7F4] text-slate-500 border-b border-slate-200/80 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-4">Case ID</th>
                <th className="py-3 px-3">User & Amount</th>
                <th className="py-3 px-3">Risk Score</th>
                <th className="py-3 px-3">Risk Level</th>
                <th className="py-3 px-3">Action</th>
                <th className="py-3 px-3">Primary Signal</th>
                <th className="py-3 px-4 text-right">Cluster</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredCases.map((c) => {
                const isSelected = c.case_id === selectedCaseId;
                return (
                  <tr
                    key={c.case_id}
                    onClick={() => onSelectCase(c.case_id)}
                    className={`cursor-pointer transition-colors hover:bg-slate-50/80 ${
                      isSelected ? 'bg-orange-50/60 border-l-4 border-l-[#FF7B42]' : ''
                    }`}
                  >
                    {/* Case ID */}
                    <td className="py-3.5 px-4 font-mono font-extrabold text-[#1E2022]">
                      <div className="flex items-center gap-1.5">
                        <span>{c.case_id}</span>
                        {c.is_benign_pattern && (
                          <span className="text-[10px] px-2 py-0.5 bg-[#A7F3D0] text-[#065F46] rounded-full font-bold">
                            BENIGN
                          </span>
                        )}
                      </div>
                    </td>

                    {/* User & Amount */}
                    <td className="py-3.5 px-3">
                      <div className="font-mono text-[#1E2022] font-bold">{c.user_id}</div>
                      <div className="text-slate-500 font-semibold">${c.amount.toFixed(2)}</div>
                    </td>

                    {/* Risk Score */}
                    <td className="py-3.5 px-3">
                      <div className="font-mono font-extrabold text-[#1E2022] text-sm">
                        {(c.risk_score * 100).toFixed(1)}%
                      </div>
                      <div className="w-16 h-1.5 bg-slate-200 rounded-full mt-1 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            c.risk_score >= 0.75
                              ? 'bg-[#FF7B42]'
                              : c.risk_score >= 0.45
                              ? 'bg-[#FEF08A]'
                              : 'bg-[#A7F3D0]'
                          }`}
                          style={{ width: `${Math.min(100, c.risk_score * 100)}%` }}
                        ></div>
                      </div>
                    </td>

                    {/* Risk Level Badge */}
                    <td className="py-3.5 px-3">
                      <span className={`inline-flex px-2.5 py-0.5 rounded-full border text-[10px] font-extrabold ${getRiskBadge(c.risk_level)}`}>
                        {c.risk_level}
                      </span>
                    </td>

                    {/* Action Badge */}
                    <td className="py-3.5 px-3">
                      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-extrabold ${getActionBadge(c.action)}`}>
                        {c.action}
                      </span>
                    </td>

                    {/* Primary Driver Signal */}
                    <td className="py-3.5 px-3 text-slate-600 font-mono text-[11px] font-medium">
                      {c.primary_driver}
                    </td>

                    {/* Cluster Users Count */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="inline-flex items-center gap-1 text-slate-700 font-mono font-bold">
                        <Users className="w-3.5 h-3.5 text-slate-400" />
                        <span>{c.connected_users_count}</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

