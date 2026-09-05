import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import CaseQueue from './components/CaseQueue';
import CaseDetail from './components/CaseDetail';
import EntityGraph from './components/EntityGraph';

export default function App() {
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [caseDetailData, setCaseDetailData] = useState(null);
  const [subgraphData, setSubgraphData] = useState(null);

  const [loadingCases, setLoadingCases] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingSubgraph, setLoadingSubgraph] = useState(false);

  // 1. Fetch Triage Cases Summary List (relative path via Vite Proxy)
  useEffect(() => {
    async function loadCases() {
      try {
        setLoadingCases(true);
        const res = await fetch('/api/cases?sort_by=risk_score&order=desc');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setCases(data);

        // Auto-select top risk case
        if (data.length > 0) {
          setSelectedCaseId(data[0].case_id);
        }
      } catch (err) {
        console.error('Failed to load triage cases:', err);
      } finally {
        setLoadingCases(false);
      }
    }
    loadCases();
  }, []);

  // 2. Fetch Case Detail (On-Demand LLM Lazy Load) & Subgraph when selectedCaseId changes
  useEffect(() => {
    if (!selectedCaseId) return;

    // Fetch Detail
    async function loadCaseDetail() {
      try {
        setLoadingDetail(true);
        const res = await fetch(`/api/cases/${selectedCaseId}`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setCaseDetailData(data);
      } catch (err) {
        console.error(`Failed to load case detail for ${selectedCaseId}:`, err);
      } finally {
        setLoadingDetail(false);
      }
    }

    // Fetch Subgraph
    async function loadSubgraph() {
      try {
        setLoadingSubgraph(true);
        const res = await fetch(`/api/cases/${selectedCaseId}/subgraph`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setSubgraphData(data);
      } catch (err) {
        console.error(`Failed to load subgraph for ${selectedCaseId}:`, err);
      } finally {
        setLoadingSubgraph(false);
      }
    }

    loadCaseDetail();
    loadSubgraph();
  }, [selectedCaseId]);

  return (
    <div className="min-h-screen bg-[#F8F7F4] text-[#1E2022] flex flex-col font-sans antialiased">
      
      {/* Top Navigation Header */}
      <Header />

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Dashboard Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column: Triage Queue Table (5 Cols) */}
          <div className="lg:col-span-5 h-[calc(100vh-140px)] min-h-[600px] sticky top-24">
            <CaseQueue
              cases={cases}
              selectedCaseId={selectedCaseId}
              onSelectCase={setSelectedCaseId}
              loading={loadingCases}
            />
          </div>

          {/* Right Column: Case Detail & Entity Graph (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            
            {/* Case Detail Synthesis */}
            <CaseDetail
              caseData={caseDetailData?.case}
              reportData={caseDetailData?.report}
              subgraphData={subgraphData}
              loading={loadingDetail}
            />

            {/* Entity Infrastructure Graph */}
            <EntityGraph
              subgraphData={subgraphData}
              loading={loadingSubgraph}
            />

          </div>

        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200/80 bg-white py-4 text-center text-xs text-slate-500 font-medium">
        Fraud Ring Sentinel — Coordinated Payment Abuse Intelligence • Built for Razorpay AI Buildathon 2026
      </footer>

    </div>
  );
}

