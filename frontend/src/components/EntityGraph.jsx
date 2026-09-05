import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Network, ZoomIn, ZoomOut, RefreshCw, Info, Eye, ShieldAlert } from 'lucide-react';

const NODE_COLORS = {
  USER: { bg: '#0284c7', text: '#ffffff', border: '#0284c7' },
  IP: { bg: '#9333ea', text: '#ffffff', border: '#9333ea' },
  DEVICE: { bg: '#2563eb', text: '#ffffff', border: '#2563eb' },
  CARD: { bg: '#d97706', text: '#ffffff', border: '#d97706' },
  MERCHANT: { bg: '#059669', text: '#ffffff', border: '#059669' },
  TRANSACTION: { bg: '#64748b', text: '#ffffff', border: '#64748b' },
  UNKNOWN: { bg: '#64748b', text: '#ffffff', border: '#64748b' }
};

export default function EntityGraph({ subgraphData, loading }) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [showTransactionNodes, setShowTransactionNodes] = useState(false);
  const [activeFilters, setActiveFilters] = useState({
    USER: true, IP: true, DEVICE: true, CARD: true, MERCHANT: true
  });

  const svgRef = useRef(null);

  // Compute Layout Positions (Spacious, Un-cluttered Concentric Topology)
  const layout = useMemo(() => {
    if (!subgraphData || !subgraphData.nodes) return { nodes: [], edges: [] };

    const rawNodes = subgraphData.nodes;
    const rawEdges = subgraphData.edges;

    // Filter transaction nodes unless explicitly toggled on for ultra-clean view
    const filteredRawNodes = rawNodes.filter(n => {
      if (n.type === 'TRANSACTION' && !showTransactionNodes) return false;
      return activeFilters[n.type] !== false;
    });

    const activeNodeIds = new Set(filteredRawNodes.map(n => n.id));

    const filteredNodes = filteredRawNodes;
    const filteredEdges = rawEdges.filter(e => activeNodeIds.has(e.source) && activeNodeIds.has(e.target));

    const width = 800;
    const height = 520;
    const centerX = width / 2;
    const centerY = height / 2;

    // Define well-spaced concentric radii & angular offsets per entity type
    const typeOffsets = {
      USER: { radius: 220, startAngle: 0 },
      IP: { radius: 105, startAngle: Math.PI / 6 },
      DEVICE: { radius: 155, startAngle: Math.PI / 4 },
      CARD: { radius: 195, startAngle: Math.PI / 3 },
      MERCHANT: { radius: 245, startAngle: Math.PI / 2 },
      TRANSACTION: { radius: 130, startAngle: 0 }
    };

    // Position nodes with spacious distribution around central seed user
    const positionedNodes = filteredNodes.map((node) => {
      if (node.is_seed) {
        return { ...node, x: centerX, y: centerY };
      }

      const typeConfig = typeOffsets[node.type] || { radius: 180, startAngle: 0 };
      const typeList = filteredNodes.filter(n => !n.is_seed && n.type === node.type);
      const indexInType = typeList.findIndex(n => n.id === node.id);
      const totalInType = typeList.length;

      // Distribute nodes evenly around 360 degrees with type-specific angular offset
      const angleStep = (2 * Math.PI) / Math.max(1, totalInType);
      const angle = typeConfig.startAngle + indexInType * angleStep;

      // Alternate radius slightly per index to prevent stacking
      const radius = typeConfig.radius + (indexInType % 2 === 0 ? 14 : -14);

      return {
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    const nodeMap = new Map(positionedNodes.map(n => [n.id, n]));

    const layoutEdges = filteredEdges.map(edge => ({
      ...edge,
      sourceNode: nodeMap.get(edge.source),
      targetNode: nodeMap.get(edge.target)
    })).filter(e => e.sourceNode && e.targetNode);

    return { nodes: positionedNodes, edges: layoutEdges };
  }, [subgraphData, activeFilters, showTransactionNodes]);

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleZoom = (delta) => {
    setZoom(prev => Math.max(0.5, Math.min(2.5, prev + delta)));
  };

  const resetTransform = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelectedNode(null);
  };

  const toggleFilter = (type) => {
    setActiveFilters(prev => ({ ...prev, [type]: !prev[type] }));
  };

  if (loading) {
    return (
      <div className="saas-card rounded-3xl p-12 text-center text-slate-500 space-y-3">
        <div className="w-8 h-8 border-3 border-[#FF7B42] border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm font-semibold text-[#1E2022]">Extracting Entity Graph Subgraph...</p>
      </div>
    );
  }

  if (!subgraphData || !subgraphData.nodes || subgraphData.nodes.length === 0) {
    return (
      <div className="saas-card rounded-3xl p-12 text-center text-slate-500 text-sm font-medium">
        Select a case from the triage queue to visualize entity cluster relationships.
      </div>
    );
  }

  return (
    <div className="saas-card rounded-3xl overflow-hidden flex flex-col h-full space-y-0 shadow-[0_10px_30px_rgba(0,0,0,0.04)] animate-fade-in">

      {/* Header & Controls Bar */}
      <div className="p-5 border-b border-slate-100 bg-[#F8F7F4] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-[#FF7B42]/10 flex items-center justify-center">
            <Network className="w-4 h-4 text-[#FF7B42]" />
          </div>
          <h3 className="font-extrabold text-[#1E2022] text-base">Entity Infrastructure Graph</h3>
          <span className="text-xs px-3 py-1 rounded-full bg-white text-slate-700 border border-slate-200/80 font-mono shadow-xs font-semibold">
            {layout.nodes.length} Nodes • {layout.edges.length} Edges
          </span>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowTransactionNodes(!showTransactionNodes)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all ${
              showTransactionNodes
                ? 'bg-[#1E2022] text-white border-[#1E2022]'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50 shadow-xs'
            }`}
          >
            {showTransactionNodes ? '✓ Transactions Shown' : '+ Show Transactions'}
          </button>

          <div className="flex items-center gap-1 bg-white p-1 rounded-full border border-slate-200 text-xs shadow-xs">
            <button
              onClick={() => handleZoom(0.2)}
              className="p-1.5 hover:bg-slate-100 text-slate-700 rounded-full transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleZoom(-0.2)}
              className="p-1.5 hover:bg-slate-100 text-slate-700 rounded-full transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={resetTransform}
              className="p-1.5 hover:bg-slate-100 text-slate-700 rounded-full transition-colors"
              title="Reset View"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Filter Toggles Bar */}
      <div className="bg-white px-5 py-3 border-b border-slate-100 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-slate-400 font-medium">Entity Filter:</span>
        {['USER', 'IP', 'DEVICE', 'CARD', 'MERCHANT'].map(type => {
          const active = activeFilters[type];
          const color = NODE_COLORS[type];
          return (
            <button
              key={type}
              onClick={() => toggleFilter(type)}
              className={`px-3 py-1 rounded-full font-semibold border text-xs transition-all ${
                active
                  ? 'border-transparent text-slate-900 bg-[#F8F7F4] shadow-xs'
                  : 'border-slate-200 text-slate-400 bg-white'
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full inline-block mr-1.5" style={{ backgroundColor: color.bg }}></span>
              {type}
            </button>
          );
        })}
      </div>

      {/* Visual Canvas Area */}
      <div
        className="relative flex-1 bg-[#FAF9F6] min-h-[500px] overflow-hidden cursor-grab active:cursor-grabbing select-none"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          ref={svgRef}
          className="w-full h-full min-h-[500px]"
          viewBox="0 0 800 520"
        >
          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>

            {/* Edges */}
            {layout.edges.map((edge, i) => (
              <g key={i}>
                <line
                  x1={edge.sourceNode.x}
                  y1={edge.sourceNode.y}
                  x2={edge.targetNode.x}
                  y2={edge.targetNode.y}
                  stroke="#CBD5E1"
                  strokeWidth="1.4"
                  strokeDasharray={edge.relation === 'USES' ? 'none' : '4,4'}
                  opacity="0.75"
                />
              </g>
            ))}

            {/* Nodes */}
            {layout.nodes.map((node) => {
              const color = NODE_COLORS[node.type] || NODE_COLORS.UNKNOWN;
              const isSelected = selectedNode?.id === node.id;
              const isSeed = node.is_seed;

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedNode(node);
                  }}
                  className="cursor-pointer group"
                >
                  {/* Seed Node Pulse Ring */}
                  {isSeed && (
                    <circle
                      r="24"
                      fill="none"
                      stroke="#FF7B42"
                      strokeWidth="2"
                      className="animate-ping"
                      opacity="0.5"
                    />
                  )}

                  {/* Node Circle */}
                  <circle
                    r={isSeed ? "18" : (node.type === 'TRANSACTION' ? "7" : "13")}
                    fill={color.bg}
                    stroke={isSelected ? '#1E2022' : color.border}
                    strokeWidth={isSelected ? "3.5" : "2"}
                    className="transition-all hover:scale-125 shadow-sm"
                  />

                  {/* Crisp Node Label with Text Outline Halo for Perfect Legibility */}
                  {node.type !== 'TRANSACTION' && (
                    <text
                      y={isSeed ? "32" : "26"}
                      textAnchor="middle"
                      fill="#1E2022"
                      stroke="#FFFFFF"
                      strokeWidth="3"
                      paintOrder="stroke fill"
                      fontSize="10"
                      fontWeight={isSeed ? "bold" : "600"}
                      className="pointer-events-none font-sans tracking-tight"
                    >
                      {node.label}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>

        {/* Selected Node Inspector Drawer */}
        {selectedNode && (
          <div className="absolute bottom-4 right-4 bg-white p-4 rounded-2xl border border-slate-200/80 text-xs w-64 shadow-xl space-y-2 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between text-[#1E2022] font-bold">
              <span className="font-mono text-[#FF7B42]">{selectedNode.label}</span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-slate-700 font-bold"
              >
                ✕
              </button>
            </div>
            <div className="text-slate-500 text-[11px]">Entity Type: <span className="text-slate-900 font-mono font-bold">{selectedNode.type}</span></div>
            <div className="text-slate-500 text-[11px]">Raw Identifier: <span className="text-slate-900 font-mono">{selectedNode.raw_id}</span></div>
            {selectedNode.is_seed && (
              <div className="text-[#FF7B42] text-[10px] font-bold mt-1 bg-orange-50 px-2.5 py-1 rounded-full border border-orange-200 inline-block">
                ★ Target Transaction Seed User
              </div>
            )}
          </div>
        )}
      </div>

      {/* Guardrail Metadata Notice Footer */}
      <div className="bg-[#F8F7F4] p-3 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between font-medium">
        <div className="flex items-center gap-1.5 text-[#D9531E] font-semibold">
          <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-[#FF7B42]" />
          <span>GRAPH CONNECTION != FRAUD</span>
        </div>
        <span className="text-slate-500 hidden sm:inline">Infrastructure topology shows shared connections, not confirmed fraud intent.</span>
      </div>

    </div>
  );
}
