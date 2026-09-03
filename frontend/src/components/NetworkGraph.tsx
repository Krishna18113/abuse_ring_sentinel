import React, { useState, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  MarkerType,
  Position
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  Smartphone, 
  Globe, 
  Tag, 
  User, 
  ShieldAlert, 
  Network, 
  Layers, 
  Filter, 
  ChevronRight,
  Sparkles,
  CheckCircle2,
  Users,
  Info,
  ExternalLink,
  X,
  Share2,
  Clock,
  Check,
  AlertCircle
} from 'lucide-react';
import { 
  GraphResponse, 
  MultiSignalConnection, 
  SharedDevice, 
  SharedIP, 
  CouponCoordination, 
  ReferralConnections, 
  TemporalCluster,
  SignalStrength
} from '../types';
import { useNavigate } from 'react-router-dom';

interface NetworkGraphProps {
  graphData: GraphResponse;
  multiSignalConnections?: MultiSignalConnection[];
  signals?: {
    shared_devices?: SharedDevice[];
    shared_ips?: SharedIP[];
    coupon_coordination?: CouponCoordination[];
    referral_connections?: ReferralConnections;
    temporal_clusters?: TemporalCluster[];
  };
  strengths?: {
    shared_device?: SignalStrength;
    shared_ip?: SignalStrength;
    coupon_coordination?: SignalStrength;
    referral_coordination?: SignalStrength;
    temporal_coordination?: SignalStrength;
  };
}

export const NetworkGraph: React.FC<NetworkGraphProps> = ({ 
  graphData, 
  multiSignalConnections = [],
  signals,
  strengths
}) => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'graph' | 'tree'>('graph');
  const [activeFilter, setActiveFilter] = useState<'PRIORITY' | 'ALL' | 'DEVICE' | 'IP' | 'COUPON'>('PRIORITY');
  
  // Interactive Selection / Focus state
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  // Map of multi-signal overlaps for fast lookup
  const multiSignalMap = useMemo(() => {
    const map: Record<string, MultiSignalConnection> = {};
    multiSignalConnections.forEach(m => {
      map[m.connected_customer] = m;
    });
    return map;
  }, [multiSignalConnections]);

  // Compute active focus ID (hovered has transient priority, selected has locked priority)
  const focusNodeId = hoveredNodeId || selectedNodeId;

  // Hierarchical layout engine
  const { nodes, edges, hubBreakdown, activeCustomerInfo, targetId } = useMemo(() => {
    const rawNodes = graphData.nodes || [];
    const rawEdges = graphData.edges || [];

    const targetNode = rawNodes.find(n => n.data?.is_target) || rawNodes[0];
    const target_id = targetNode?.id || graphData.customer_id;
    const otherNodes = rawNodes.filter(n => n.id !== target_id);

    // Multi-signal customer IDs
    const multiCustomerIds = new Set(
      otherNodes
        .filter(n => n.type === 'customer' && ((n.data?.signal_count || 1) > 1 || multiSignalMap[n.id]))
        .map(n => n.id)
    );

    // 1. Filter Nodes based on active filter
    let visibleNodes = otherNodes;
    if (activeFilter === 'PRIORITY') {
      // Default: Target + Infrastructure Hubs + Multi-Signal Accounts (2x+)
      if (multiCustomerIds.size > 0) {
        visibleNodes = otherNodes.filter(n => n.type !== 'customer' || multiCustomerIds.has(n.id));
      } else {
        const topCustomers = otherNodes.filter(n => n.type === 'customer').slice(0, 6);
        const topIds = new Set(topCustomers.map(n => n.id));
        visibleNodes = otherNodes.filter(n => n.type !== 'customer' || topIds.has(n.id));
      }
    } else if (activeFilter === 'DEVICE') {
      const devEdges = rawEdges.filter(e => e.type === 'USES_DEVICE');
      const devNodeIds = new Set<string>();
      devEdges.forEach(e => { devNodeIds.add(e.source); devNodeIds.add(e.target); });
      visibleNodes = otherNodes.filter(n => devNodeIds.has(n.id));
    } else if (activeFilter === 'IP') {
      const ipEdges = rawEdges.filter(e => e.type === 'USES_IP');
      const ipNodeIds = new Set<string>();
      ipEdges.forEach(e => { ipNodeIds.add(e.source); ipNodeIds.add(e.target); });
      visibleNodes = otherNodes.filter(n => ipNodeIds.has(n.id));
    } else if (activeFilter === 'COUPON') {
      const couponEdges = rawEdges.filter(e => e.type === 'USED_COUPON');
      const couponNodeIds = new Set<string>();
      couponEdges.forEach(e => { couponNodeIds.add(e.source); couponNodeIds.add(e.target); });
      visibleNodes = otherNodes.filter(n => couponNodeIds.has(n.id));
    }

    const visibleNodeIds = new Set<string>([target_id, ...visibleNodes.map(n => n.id)]);
    const visibleEdges = rawEdges.filter(e => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target));

    // Determine paths for active focus highlighting
    const highlightedNodeIds = new Set<string>();
    const highlightedEdgeIds = new Set<string>();

    if (focusNodeId) {
      highlightedNodeIds.add(focusNodeId);
      highlightedNodeIds.add(target_id);

      // Find direct connected edges
      visibleEdges.forEach((e, idx) => {
        const edgeId = `e-${idx}-${e.source}-${e.target}`;
        if (e.source === focusNodeId || e.target === focusNodeId) {
          highlightedEdgeIds.add(edgeId);
          highlightedNodeIds.add(e.source);
          highlightedNodeIds.add(e.target);
        }
      });

      // Also highlight intermediate paths connecting target through hubs to the focused customer
      visibleEdges.forEach((e, idx) => {
        const edgeId = `e-${idx}-${e.source}-${e.target}`;
        if (highlightedNodeIds.has(e.source) && highlightedNodeIds.has(e.target)) {
          highlightedEdgeIds.add(edgeId);
        }
      });
    }

    // 2. Deterministic Hierarchical Layout Positions
    const flowNodes: Node[] = [];
    const canvasWidth = 860;
    const centerX = canvasWidth / 2;

    // TIER 1: Target Customer (Top Anchor: Y = 40)
    if (targetNode) {
      const isTargetDimmed = focusNodeId != null && !highlightedNodeIds.has(target_id);
      flowNodes.push({
        id: target_id,
        position: { x: centerX - 95, y: 40 },
        data: {
          label: (
            <div 
              onClick={() => setSelectedNodeId(target_id)}
              className={`flex items-center gap-2.5 px-4 py-3 bg-slate-900 border-2 border-rose-500 rounded-2xl shadow-2xl shadow-rose-950/80 text-white min-w-[190px] cursor-pointer transition-all duration-300 ${
                isTargetDimmed ? 'opacity-25 scale-95' : 'opacity-100 scale-100 ring-2 ring-rose-500/40'
              }`}
            >
              <div className="p-2 bg-rose-500/20 rounded-xl text-rose-400 flex-shrink-0">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div className="text-left">
                <div className="text-xs font-mono font-extrabold text-rose-200">{target_id}</div>
                <div className="text-[9px] text-slate-400 font-sans font-bold uppercase tracking-wider">Investigated Account</div>
              </div>
            </div>
          )
        },
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      });
    }

    // Categorize visible nodes into Level 2 (Hubs) and Level 3 (Customers)
    const infraNodes = visibleNodes.filter(n => n.type !== 'customer');
    const customerNodes = visibleNodes.filter(n => n.type === 'customer');

    // Group infrastructure by type for distinct horizontal lanes
    const deviceHubs = infraNodes.filter(n => n.type === 'device');
    const ipHubs = infraNodes.filter(n => n.type === 'ip');
    const couponHubs = infraNodes.filter(n => n.type === 'coupon');
    const allHubs = [...deviceHubs, ...ipHubs, ...couponHubs];

    // TIER 2: Infrastructure Hubs (Middle: Y = 190)
    const hubSpacing = canvasWidth / Math.max(allHubs.length + 1, 2);
    allHubs.forEach((node, i) => {
      const x = (i + 1) * hubSpacing - 75;
      const y = 190;

      let icon = <Smartphone className="w-4 h-4 text-sky-400" />;
      let border = 'border-sky-500/50 bg-sky-950/80 text-sky-200';
      let badge = 'bg-sky-500/20 text-sky-300';
      let typeLabel = 'Device';

      if (node.type === 'ip') {
        icon = <Globe className="w-4 h-4 text-indigo-400" />;
        border = 'border-indigo-500/50 bg-indigo-950/80 text-indigo-200';
        badge = 'bg-indigo-500/20 text-indigo-300';
        typeLabel = 'Network IP';
      } else if (node.type === 'coupon') {
        icon = <Tag className="w-4 h-4 text-amber-400" />;
        border = 'border-amber-500/50 bg-amber-950/80 text-amber-200';
        badge = 'bg-amber-500/20 text-amber-300';
        typeLabel = 'Coupon';
      }

      const isDimmed = focusNodeId != null && !highlightedNodeIds.has(node.id);
      const isFocused = focusNodeId === node.id || (focusNodeId != null && highlightedNodeIds.has(node.id));

      flowNodes.push({
        id: node.id,
        position: { x, y },
        data: {
          label: (
            <div 
              onMouseEnter={() => setHoveredNodeId(node.id)}
              onMouseLeave={() => setHoveredNodeId(null)}
              onClick={() => setSelectedNodeId(node.id === selectedNodeId ? null : node.id)}
              className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border ${border} text-xs shadow-lg backdrop-blur-md cursor-pointer transition-all duration-300 min-w-[155px] ${
                isDimmed ? 'opacity-20 scale-95' : 'opacity-100 scale-100'
              } ${isFocused ? 'ring-2 ring-indigo-400/60 shadow-indigo-950/80' : ''}`}
            >
              <div className="p-1.5 rounded-lg bg-slate-900/90">{icon}</div>
              <div className="text-left">
                <div className="font-mono text-[11px] font-bold">{node.id}</div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className={`text-[9px] px-1.5 py-0.2 rounded font-sans font-medium ${badge}`}>
                    {typeLabel}
                  </span>
                  {node.data?.customer_count > 1 && (
                    <span className="text-[9px] text-slate-400 font-mono">
                      {node.data.customer_count} users
                    </span>
                  )}
                </div>
              </div>
            </div>
          )
        },
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      });
    });

    // TIER 3: Connected Accounts (Bottom: Y = 360 & Y = 430)
    const sortedCustomers = [...customerNodes].sort((a, b) => {
      const aSig = multiSignalMap[a.id]?.signal_count || a.data?.signal_count || 1;
      const bSig = multiSignalMap[b.id]?.signal_count || b.data?.signal_count || 1;
      return bSig - aSig;
    });

    const maxPerRow = 5;
    sortedCustomers.forEach((node, i) => {
      const rowIndex = Math.floor(i / maxPerRow);
      const colIndex = i % maxPerRow;
      const itemsInThisRow = Math.min(sortedCustomers.length - rowIndex * maxPerRow, maxPerRow);
      const rowSpacing = canvasWidth / Math.max(itemsInThisRow + 1, 2);

      const x = (colIndex + 1) * rowSpacing - 65;
      const y = 360 + rowIndex * 70;

      const multiInfo = multiSignalMap[node.id];
      const signalCount = multiInfo?.signal_count || node.data?.signal_count || 1;
      
      let prominenceClass = 'bg-slate-900/90 border-slate-700 text-slate-300';
      let badgeClass = 'bg-slate-800 text-slate-400';
      let badgeText = '1 Signal';

      if (signalCount >= 3) {
        prominenceClass = 'bg-rose-950/90 border-rose-500/80 text-rose-100 ring-2 ring-rose-500/40 shadow-rose-950/80';
        badgeClass = 'bg-rose-500/30 text-rose-300 font-bold';
        badgeText = `${signalCount}x Signals`;
      } else if (signalCount === 2) {
        prominenceClass = 'bg-amber-950/80 border-amber-500/70 text-amber-100 ring-1 ring-amber-500/30 shadow-amber-950/60';
        badgeClass = 'bg-amber-500/30 text-amber-300 font-bold';
        badgeText = '2x Signals';
      }

      const isDimmed = focusNodeId != null && !highlightedNodeIds.has(node.id);
      const isFocused = focusNodeId === node.id || (focusNodeId != null && highlightedNodeIds.has(node.id));

      flowNodes.push({
        id: node.id,
        position: { x, y },
        data: {
          label: (
            <div 
              onMouseEnter={() => setHoveredNodeId(node.id)}
              onMouseLeave={() => setHoveredNodeId(null)}
              onClick={() => setSelectedNodeId(node.id === selectedNodeId ? null : node.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[11px] font-mono shadow-md cursor-pointer transition-all duration-300 min-w-[130px] ${prominenceClass} ${
                isDimmed ? 'opacity-20 scale-95' : 'opacity-100 scale-100'
              } ${isFocused ? 'scale-105 ring-2 ring-white/80' : ''}`}
            >
              <User className={`w-3.5 h-3.5 flex-shrink-0 ${signalCount > 1 ? 'text-rose-400' : 'text-slate-400'}`} />
              <div className="text-left flex-1 min-w-0">
                <div className="font-bold truncate">{node.id}</div>
                <div className="text-[9px] mt-0.5">
                  <span className={`px-1.5 py-0.2 rounded font-sans ${badgeClass}`}>
                    {badgeText}
                  </span>
                </div>
              </div>
            </div>
          )
        },
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      });
    });

    // 3. Build Flow Edges with subtle default opacity and bright focus glow
    const flowEdges: Edge[] = visibleEdges.map((e, idx) => {
      const edgeId = `e-${idx}-${e.source}-${e.target}`;
      const isEdgeHighlighted = highlightedEdgeIds.has(edgeId);
      const isAnyFocused = focusNodeId != null;

      let stroke = '#64748b';
      let strokeWidth = 1.5;

      if (e.type === 'USES_DEVICE') {
        stroke = '#38bdf8';
      } else if (e.type === 'USES_IP') {
        stroke = '#818cf8';
      } else if (e.type === 'USED_COUPON') {
        stroke = '#fbbf24';
      } else if (e.type === 'REFERRED') {
        stroke = '#fb7185';
      }

      let opacity = 0.35;
      if (isAnyFocused) {
        if (isEdgeHighlighted) {
          opacity = 1.0;
          strokeWidth = 2.5;
        } else {
          opacity = 0.08;
        }
      }

      return {
        id: edgeId,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: isEdgeHighlighted || e.type === 'REFERRED',
        style: { stroke, strokeWidth, opacity, transition: 'all 0.3s ease' },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 8,
          height: 8,
          color: stroke,
        },
      };
    });

    // Active customer details for side drawer
    const activeCust = selectedNodeId && selectedNodeId !== target_id
      ? {
          id: selectedNodeId,
          multi: multiSignalMap[selectedNodeId],
          node: otherNodes.find(n => n.id === selectedNodeId),
          connectedEdges: rawEdges.filter(e => e.source === selectedNodeId || e.target === selectedNodeId),
        }
      : null;

    const breakdown = {
      devices: deviceHubs,
      ips: ipHubs,
      coupons: couponHubs,
      multiCustomers: sortedCustomers.filter(n => (multiSignalMap[n.id]?.signal_count || n.data?.signal_count || 1) > 1),
    };

    return { 
      nodes: flowNodes, 
      edges: flowEdges, 
      hubBreakdown: breakdown,
      activeCustomerInfo: activeCust,
      targetId: target_id
    };
  }, [graphData, multiSignalConnections, activeFilter, focusNodeId, selectedNodeId, multiSignalMap]);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
      
      {/* 1. Header with Mode Switcher and Connections Count */}
      <div className="px-6 py-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-950/60">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400 border border-indigo-500/20">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h3 className="text-base font-bold text-white tracking-tight">Investigation Evidence Network</h3>
              <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono border border-slate-700 font-semibold">
                Showing {nodes.length - 1} of {graphData.total_connections_count} Connections
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Target Account ➔ Shared Infrastructure Hubs ➔ Connected Accounts
            </p>
          </div>
        </div>

        {/* View Mode Switcher: Evidence Map vs Evidence Summary */}
        <div className="flex items-center p-1 bg-slate-950 border border-slate-800 rounded-xl">
          <button
            onClick={() => { setViewMode('graph'); setSelectedNodeId(null); }}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'graph' 
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-950/50' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>Evidence Map</span>
          </button>
          <button
            onClick={() => { setViewMode('tree'); setSelectedNodeId(null); }}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'tree' 
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-950/50' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Evidence Summary</span>
          </button>
        </div>
      </div>

      {/* 2. Deterministic "Why This Account Was Flagged" Banner */}
      <div className="px-6 py-3 bg-gradient-to-r from-slate-950 via-indigo-950/20 to-slate-950 border-b border-slate-800/80 text-xs flex items-start gap-3">
        <Info className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
        <div className="text-slate-300 leading-relaxed">
          <strong className="text-white">Why this account was flagged: </strong>
          {hubBreakdown.multiCustomers.length > 0 ? (
            <span>
              Found <strong className="text-rose-400 font-semibold">{hubBreakdown.multiCustomers.length} connected accounts</strong> sharing multiple independent infrastructure and promotional signals. Multi-signal overlaps indicate potential coordinated activity and warrant human review.
            </span>
          ) : (
            <span>
              Account exhibits isolated organic activity with no high-density multi-signal hardware or promotional clustering.
            </span>
          )}
        </div>
      </div>

      {/* 3. Progressive Disclosure Filter Bar */}
      <div className="px-6 py-2.5 bg-slate-950/80 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1.5 text-slate-400 font-medium">
          <Filter className="w-3.5 h-3.5" />
          <span>Evidence Scope:</span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => { setActiveFilter('PRIORITY'); setSelectedNodeId(null); }}
            className={`flex items-center gap-1 px-3 py-1 rounded-lg text-[11px] font-semibold transition-all ${
              activeFilter === 'PRIORITY' 
                ? 'bg-rose-600 text-white shadow-md shadow-rose-950/50 ring-1 ring-rose-400/40' 
                : 'bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3 h-3 text-amber-300" />
            <span>Priority Evidence (2x+)</span>
          </button>

          <button
            onClick={() => { setActiveFilter('ALL'); setSelectedNodeId(null); }}
            className={`px-3 py-1 rounded-lg text-[11px] font-medium transition-colors ${
              activeFilter === 'ALL' 
                ? 'bg-slate-700 text-white font-semibold' 
                : 'bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            All Connections ({graphData.total_connections_count})
          </button>

          <button
            onClick={() => { setActiveFilter('DEVICE'); setSelectedNodeId(null); }}
            className={`flex items-center gap-1 px-3 py-1 rounded-lg text-[11px] font-medium transition-colors ${
              activeFilter === 'DEVICE' 
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold' 
                : 'bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-sky-300'
            }`}
          >
            <Smartphone className="w-3 h-3 text-sky-400" />
            <span>Devices</span>
          </button>

          <button
            onClick={() => { setActiveFilter('IP'); setSelectedNodeId(null); }}
            className={`flex items-center gap-1 px-3 py-1 rounded-lg text-[11px] font-medium transition-colors ${
              activeFilter === 'IP' 
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 font-semibold' 
                : 'bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-indigo-300'
            }`}
          >
            <Globe className="w-3 h-3 text-indigo-400" />
            <span>IPs</span>
          </button>

          <button
            onClick={() => { setActiveFilter('COUPON'); setSelectedNodeId(null); }}
            className={`flex items-center gap-1 px-3 py-1 rounded-lg text-[11px] font-medium transition-colors ${
              activeFilter === 'COUPON' 
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 font-semibold' 
                : 'bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-amber-300'
            }`}
          >
            <Tag className="w-3 h-3 text-amber-400" />
            <span>Coupons</span>
          </button>
        </div>
      </div>

      {/* 4. Main Canvas & Side Evidence Inspector */}
      {viewMode === 'graph' ? (
        <div className="h-[500px] w-full bg-slate-950 relative flex overflow-hidden">
          
          {/* React Flow Graph Area */}
          <div className="flex-1 h-full relative" onClick={() => setSelectedNodeId(null)}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              fitView
              fitViewOptions={{ padding: 0.15 }}
              minZoom={0.2}
              maxZoom={2}
              attributionPosition="bottom-right"
            >
              <Background color="#1e293b" gap={20} size={1} />
              <Controls className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg fill-slate-300" />
            </ReactFlow>

            <div className="absolute bottom-3 left-4 pointer-events-none text-[11px] text-slate-500 font-sans">
              💡 Tip: Click any customer node to inspect shared signals and isolate its connection path.
            </div>
          </div>

          {/* Side Evidence Inspector Drawer */}
          {activeCustomerInfo && (
            <div className="w-80 border-l border-slate-800 bg-slate-900/95 backdrop-blur-md p-5 flex flex-col justify-between shadow-2xl z-10 animate-in slide-in-from-right duration-200">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div>
                    <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Connected Account</div>
                    <div className="text-sm font-bold text-white font-mono mt-0.5">{activeCustomerInfo.id}</div>
                  </div>
                  <button 
                    onClick={() => setSelectedNodeId(null)}
                    className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Connection Strength */}
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Connection Strength</div>
                  <div className="mt-1 flex items-center gap-2">
                    <span className={`px-2.5 py-1 rounded-md text-xs font-bold font-mono ${
                      (activeCustomerInfo.multi?.signal_count || 1) >= 2
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                        : 'bg-slate-800 text-slate-300'
                    }`}>
                      {activeCustomerInfo.multi?.signal_count || 1} Shared Independent Signals
                    </span>
                  </div>
                </div>

                {/* Overlapping Signals Breakdown */}
                <div className="space-y-2">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Evidence Breakdown:</div>
                  <div className="space-y-1.5">
                    {activeCustomerInfo.multi?.signals ? (
                      activeCustomerInfo.multi.signals.map((sig, idx) => (
                        <div key={idx} className="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs flex items-center gap-2 text-slate-200">
                          <CheckCircle2 className="w-4 h-4 text-rose-400 flex-shrink-0" />
                          <span className="capitalize">{sig.replace('_', ' ')}</span>
                        </div>
                      ))
                    ) : (
                      activeCustomerInfo.connectedEdges.map((e, idx) => (
                        <div key={idx} className="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs flex items-center gap-2 text-slate-200">
                          <CheckCircle2 className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                          <span>{e.type.replace('_', ' ')}: <strong className="font-mono text-white">{e.target === activeCustomerInfo.id ? e.source : e.target}</strong></span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="p-3 bg-slate-950/70 border border-slate-800/90 rounded-xl text-[11px] text-slate-400 leading-relaxed">
                  <strong className="text-slate-300 block mb-0.5">Why this matters:</strong>
                  This account shares multiple independent infrastructure signals with the investigated customer. Independent overlap significantly elevates the likelihood of coordinated abuse.
                </div>
              </div>

              {/* Deep Dive Action */}
              <button
                onClick={() => navigate(`/customers/${activeCustomerInfo.id}`)}
                className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-950/50 transition-colors"
              >
                <span>Investigate Account {activeCustomerInfo.id}</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

        </div>
      ) : (
        /* 5. Evidence Summary (Comprehensive 6-Section Merchant Breakdown) */
        <div className="p-6 bg-slate-950/60 min-h-[460px] space-y-6">
          
          <div className="p-4 bg-indigo-950/30 border border-indigo-500/30 rounded-xl text-xs text-indigo-300 flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white block mb-0.5">Structured Evidence Breakdown:</strong>
              This view organizes all observable relationships into 6 operational categories: Hardware, Network, Promotions, Referrals, Coordinated Timing, and Multi-Signal Overlaps.
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            
            {/* 1. Hardware Category */}
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-sky-500/10 rounded-lg text-sky-400 border border-sky-500/20">
                    <Smartphone className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">Hardware Infrastructure</h4>
                    <p className="text-[10px] text-slate-400">{signals?.shared_devices?.length || 0} Shared Device Nodes</p>
                  </div>
                </div>
                <span className={`text-[9px] px-2 py-0.5 rounded font-bold ${
                  strengths?.shared_device?.detected ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'
                }`}>
                  {strengths?.shared_device?.detected ? `${strengths.shared_device.strength} STRENGTH` : 'NORMAL'}
                </span>
              </div>

              {signals?.shared_devices && signals.shared_devices.length > 0 ? (
                <div className="space-y-2">
                  {signals.shared_devices.map((d, i) => (
                    <div key={i} className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-xs">
                      <div className="flex items-center justify-between font-mono font-bold text-sky-300 mb-1">
                        <span>Device: {d.device_id}</span>
                        <span className="text-[10px] text-rose-400 font-sans">{d.customer_count} accounts</span>
                      </div>
                      <p className="text-[11px] text-slate-400">{d.transaction_count} total transactions originated from this exact physical device.</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 py-3">Dedicated hardware fingerprint. No shared devices detected.</p>
              )}
            </div>

            {/* 2. Network Category */}
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
                    <Globe className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">Network Infrastructure</h4>
                    <p className="text-[10px] text-slate-400">{signals?.shared_ips?.length || 0} Shared IP Nodes</p>
                  </div>
                </div>
                <span className={`text-[9px] px-2 py-0.5 rounded font-bold ${
                  strengths?.shared_ip?.detected ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'
                }`}>
                  {strengths?.shared_ip?.detected ? `${strengths.shared_ip.strength} STRENGTH` : 'NORMAL'}
                </span>
              </div>

              {signals?.shared_ips && signals.shared_ips.length > 0 ? (
                <div className="space-y-2">
                  {signals.shared_ips.map((ip, i) => (
                    <div key={i} className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-xs">
                      <div className="flex items-center justify-between font-mono font-bold text-indigo-300 mb-1">
                        <span>IP: {ip.ip_address}</span>
                        <span className="text-[10px] text-amber-400 font-sans">{ip.customer_count} accounts</span>
                      </div>
                      <p className="text-[11px] text-slate-400">Co-located gateway connecting clustered accounts during active sessions.</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 py-3">Isolated network IP. No multi-account clustering.</p>
              )}
            </div>

            {/* 3. Promotions Category */}
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-amber-500/10 rounded-lg text-amber-400 border border-amber-500/20">
                    <Tag className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">Promotional Campaigns</h4>
                    <p className="text-[10px] text-slate-400">{signals?.coupon_coordination?.length || 0} Campaigns</p>
                  </div>
                </div>
                <span className={`text-[9px] px-2 py-0.5 rounded font-bold ${
                  strengths?.coupon_coordination?.detected ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'
                }`}>
                  {strengths?.coupon_coordination?.detected ? `${strengths.coupon_coordination.strength} STRENGTH` : 'NORMAL'}
                </span>
              </div>

              {signals?.coupon_coordination && signals.coupon_coordination.length > 0 ? (
                <div className="space-y-2">
                  {signals.coupon_coordination.map((c, i) => (
                    <div key={i} className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-xs">
                      <div className="flex items-center justify-between font-mono font-bold text-amber-300 mb-1">
                        <span>{c.coupon_id}</span>
                        <span className="text-[10px] text-slate-400 font-sans">{c.customer_count} users</span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        {c.shared_device_count > 0 ? `${c.shared_device_count} device overlaps detected on this promotion.` : 'Coupon redeemed within normal promotional thresholds.'}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 py-3">No promotional coupon redemptions recorded.</p>
              )}
            </div>

            {/* 4. Referral Activity Category */}
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-rose-500/10 rounded-lg text-rose-400 border border-rose-500/20">
                    <Share2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">Referral Relationships</h4>
                    <p className="text-[10px] text-slate-400">Component Size: {signals?.referral_connections?.referral_component_size ?? 0}</p>
                  </div>
                </div>
                <span className={`text-[9px] px-2 py-0.5 rounded font-bold ${
                  strengths?.referral_coordination?.detected ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'
                }`}>
                  {strengths?.referral_coordination?.detected ? `${strengths.referral_coordination.strength} STRENGTH` : 'NORMAL'}
                </span>
              </div>

              <div className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-xs space-y-1 text-slate-300">
                <div>Referrer ID: <span className="font-mono font-bold text-white">{signals?.referral_connections?.referrer_id || 'None (Organic)'}</span></div>
                <div>Downline Referrals: <strong className="text-slate-200">{signals?.referral_connections?.referral_out_degree ?? 0}</strong></div>
                <div>Connected Referral Cluster: <strong className="text-indigo-400">{signals?.referral_connections?.referral_component_size ?? 0}</strong> accounts</div>
              </div>
            </div>

            {/* 5. Coordinated Timing Category */}
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-emerald-500/10 rounded-lg text-emerald-400 border border-emerald-500/20">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">Coordinated Timing</h4>
                    <p className="text-[10px] text-slate-400">{signals?.temporal_clusters?.length || 0} Synchronized Bursts</p>
                  </div>
                </div>
                <span className={`text-[9px] px-2 py-0.5 rounded font-bold ${
                  strengths?.temporal_coordination?.detected ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'
                }`}>
                  {strengths?.temporal_coordination?.detected ? `${strengths.temporal_coordination.strength} STRENGTH` : 'NORMAL'}
                </span>
              </div>

              {signals?.temporal_clusters && signals.temporal_clusters.length > 0 ? (
                <div className="space-y-2">
                  {signals.temporal_clusters.slice(0, 2).map((tc, i) => (
                    <div key={i} className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-xs">
                      <div className="flex items-center justify-between text-emerald-300 font-bold mb-1">
                        <span>Window: &lt; {tc.time_window_seconds}s</span>
                        <span className="text-[10px] text-rose-400">{tc.customer_count} accounts</span>
                      </div>
                      <p className="text-[11px] text-slate-400">{tc.transaction_count} transactions fired in rapid sequence.</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 py-3">Organic transaction cadence. No burst coordination detected.</p>
              )}
            </div>

            {/* 6. Multi-Signal Overlaps Category */}
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-rose-500/10 rounded-lg text-rose-400 border border-rose-500/20">
                    <Users className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">Multi-Signal Overlaps</h4>
                    <p className="text-[10px] text-rose-400">{multiSignalConnections.length} Priority Overlaps</p>
                  </div>
                </div>
                <span className="text-[9px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold">
                  HIGH PRIORITY
                </span>
              </div>

              {multiSignalConnections.length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {multiSignalConnections.map((mc, idx) => (
                    <div
                      key={idx}
                      onClick={() => navigate(`/customers/${mc.connected_customer}`)}
                      className="p-2.5 bg-slate-950/80 border border-rose-500/30 hover:border-rose-500 rounded-lg text-xs cursor-pointer transition-all flex items-center justify-between"
                    >
                      <div>
                        <div className="font-mono font-bold text-rose-300">{mc.connected_customer}</div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          {mc.signal_count}x Signals: {mc.signals.join(' + ')}
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-500" />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 py-3">No accounts share 2+ independent signals.</p>
              )}
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
