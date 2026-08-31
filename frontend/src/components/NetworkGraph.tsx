import React, { useMemo } from 'react';
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
import { Smartphone, Globe, Tag, User, ShieldAlert, Network } from 'lucide-react';
import { GraphResponse } from '../types';

interface NetworkGraphProps {
  graphData: GraphResponse;
}

export const NetworkGraph: React.FC<NetworkGraphProps> = ({ graphData }) => {
  // Convert API nodes to React Flow nodes with radial layout
  const { nodes, edges } = useMemo(() => {
    const rawNodes = graphData.nodes || [];
    const rawEdges = graphData.edges || [];

    const targetNode = rawNodes.find(n => n.data?.is_target) || rawNodes[0];
    const otherNodes = rawNodes.filter(n => n !== targetNode);

    // Place target node in center
    const centerX = 400;
    const centerY = 300;

    const flowNodes: Node[] = [];

    if (targetNode) {
      flowNodes.push({
        id: targetNode.id,
        position: { x: centerX, y: centerY },
        data: {
          label: (
            <div className="flex items-center gap-2 px-3 py-2 bg-slate-900 border-2 border-rose-500 rounded-xl shadow-xl shadow-rose-950/60 text-white">
              <div className="p-1.5 bg-rose-500/20 rounded-lg text-rose-400">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div className="text-left">
                <div className="text-xs font-bold text-rose-300">{targetNode.id}</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">Investigated Target</div>
              </div>
            </div>
          )
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });
    }

    // Separate infrastructure and neighbor customer nodes
    const infraNodes = otherNodes.filter(n => n.type !== 'customer');
    const customerNodes = otherNodes.filter(n => n.type === 'customer');

    // Place infrastructure nodes in an inner circle
    const innerRadius = 160;
    infraNodes.forEach((node, i) => {
      const angle = (i / Math.max(infraNodes.length, 1)) * 2 * Math.PI - Math.PI / 2;
      const x = centerX + innerRadius * Math.cos(angle);
      const y = centerY + innerRadius * Math.sin(angle);

      let icon = <Smartphone className="w-3.5 h-3.5 text-sky-400" />;
      let border = 'border-sky-500/40 bg-sky-950/30';
      let typeLabel = 'Device';

      if (node.type === 'ip') {
        icon = <Globe className="w-3.5 h-3.5 text-indigo-400" />;
        border = 'border-indigo-500/40 bg-indigo-950/30';
        typeLabel = 'IP';
      } else if (node.type === 'coupon') {
        icon = <Tag className="w-3.5 h-3.5 text-amber-400" />;
        border = 'border-amber-500/40 bg-amber-950/30';
        typeLabel = 'Coupon';
      }

      flowNodes.push({
        id: node.id,
        position: { x, y },
        data: {
          label: (
            <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border ${border} text-slate-200 text-xs shadow-md`}>
              {icon}
              <div className="text-left">
                <div className="font-mono text-[11px]">{node.id}</div>
                {node.data?.customer_count > 1 && (
                  <div className="text-[9px] text-slate-400 font-sans">{node.data.customer_count} users</div>
                )}
              </div>
            </div>
          )
        }
      });
    });

    // Place connected customer nodes in an outer circle
    const outerRadius = 270;
    customerNodes.forEach((node, i) => {
      const angle = (i / Math.max(customerNodes.length, 1)) * 2 * Math.PI - Math.PI / 2;
      const x = centerX + outerRadius * Math.cos(angle);
      const y = centerY + outerRadius * Math.sin(angle);

      const signalCount = node.data?.signal_count || 1;
      const isMulti = signalCount > 1;

      flowNodes.push({
        id: node.id,
        position: { x, y },
        data: {
          label: (
            <div className={`flex items-center gap-1 px-2 py-1 rounded-md border text-[11px] font-mono shadow-sm ${
              isMulti 
                ? 'bg-rose-950/50 border-rose-500/50 text-rose-200' 
                : 'bg-slate-900/90 border-slate-700 text-slate-300'
            }`}>
              <User className={`w-3 h-3 ${isMulti ? 'text-rose-400' : 'text-slate-400'}`} />
              <span>{node.id}</span>
              {isMulti && (
                <span className="ml-1 px-1 py-0.2 bg-rose-500/20 text-rose-300 text-[9px] rounded font-sans font-bold">
                  {signalCount}x
                </span>
              )}
            </div>
          )
        }
      });
    });

    // Build flow edges
    const flowEdges: Edge[] = rawEdges.map((e, idx) => {
      let stroke = '#475569';
      let strokeWidth = 1.5;

      if (e.type === 'USES_DEVICE') {
        stroke = '#0284c7';
      } else if (e.type === 'USES_IP') {
        stroke = '#6366f1';
      } else if (e.type === 'USED_COUPON') {
        stroke = '#d97706';
      } else if (e.type === 'REFERRED') {
        stroke = '#e11d48';
        strokeWidth = 2;
      }

      return {
        id: `e-${idx}-${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: e.type === 'REFERRED',
        style: { stroke, strokeWidth },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 12,
          height: 12,
          color: stroke,
        },
      };
    });

    return { nodes: flowNodes, edges: flowEdges };
  }, [graphData]);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      {/* Graph Header */}
      <div className="px-5 py-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-950/40">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
            <Network className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Investigation Neighborhood Graph</h3>
            <p className="text-xs text-slate-400">{graphData.prioritization_note}</p>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-rose-500"></span> Target
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-sky-500"></span> Device
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-indigo-500"></span> IP
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-amber-500"></span> Coupon
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-slate-400"></span> Neighbor
          </span>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="h-[460px] w-full bg-slate-950 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          fitViewOptions={{ padding: 0.25 }}
          minZoom={0.2}
          maxZoom={2}
          attributionPosition="bottom-right"
        >
          <Background color="#1e293b" gap={16} size={1} />
          <Controls className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg fill-slate-300" />
        </ReactFlow>
      </div>
    </div>
  );
};
