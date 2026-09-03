import React from 'react';
import { Clock, ArrowRight, CheckCircle2 } from 'lucide-react';

interface TemporalClusterItem {
  window_seconds?: number;
  time_window_seconds?: number;
  customer_count?: number;
  transaction_count?: number;
  total_amount?: number;
  transactions?: Array<{
    customer_id?: string;
    transaction_id?: string;
    timestamp?: string;
    connected_customer?: string;
    target_tx_id?: string;
    target_tx_time?: string;
    time_diff?: number;
    other_tx_amount?: number;
  }>;
}

interface EvidenceTimelineProps {
  clusters?: TemporalClusterItem[];
}

export const EvidenceTimeline: React.FC<EvidenceTimelineProps> = ({ clusters = [] }) => {
  if (!clusters || clusters.length === 0) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="p-2 bg-slate-800 rounded-xl text-slate-400">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight">Temporal Coordination Timeline</h3>
            <p className="text-xs text-slate-400">Transaction timestamp correlation analysis</p>
          </div>
        </div>
        <div className="flex items-center gap-3 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl text-emerald-400 text-xs leading-relaxed">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>No rapid transaction clustering detected. Activity occurs over natural, organic intervals with no coordinated bursts.</span>
        </div>
      </div>
    );
  }

  // Find tightest cluster
  const tightest = clusters[0];
  const windowSec = tightest.window_seconds ?? tightest.time_window_seconds ?? 60;
  const txList = tightest.transactions || [];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-rose-500/10 rounded-xl text-rose-400 border border-rose-500/20">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight">Temporal Coordination Timeline</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Rapid transaction bursts across connected accounts within &lt; {windowSec}s window
            </p>
          </div>
        </div>
        <div className="px-3 py-1 bg-rose-500/10 border border-rose-500/30 rounded-full text-xs font-bold text-rose-300 font-mono">
          {tightest.total_amount != null 
            ? `₹${tightest.total_amount.toFixed(2)} Across ${tightest.customer_count ?? 0} Accounts` 
            : `${tightest.transaction_count ?? txList.length} Transactions Across ${tightest.customer_count ?? 0} Accounts`}
        </div>
      </div>

      <div className="space-y-2">
        {txList.slice(0, 8).map((tx, idx) => {
          const cId = tx.customer_id || tx.connected_customer || 'Connected Account';
          const txId = tx.transaction_id || tx.target_tx_id || `TX_${idx + 1}`;
          const timeStr = tx.timestamp || tx.target_tx_time || 'Synchronized Burst';
          
          return (
            <div
              key={idx}
              className="flex items-center justify-between p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs hover:border-slate-700 transition-all"
            >
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center font-mono text-[10px] text-slate-400 font-bold">
                  #{idx + 1}
                </span>
                <div>
                  <div className="font-mono text-slate-200 font-bold">{txId}</div>
                  <div className="text-[11px] text-slate-400">{timeStr}</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-md bg-rose-950/80 border border-rose-800/80 text-[10px] text-rose-300 font-mono font-medium">
                  {tx.time_diff != null ? `+${tx.time_diff}s offset` : `≤ ${windowSec}s window`}
                </span>
              </div>

              <div className="text-right">
                <div className="font-mono text-indigo-400 font-bold">{cId}</div>
                {tx.other_tx_amount != null && (
                  <div className="text-[11px] text-slate-400 font-mono">₹{tx.other_tx_amount.toFixed(2)}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
