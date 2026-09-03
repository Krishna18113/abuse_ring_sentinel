import React, { useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  Users, 
  CreditCard, 
  Smartphone, 
  Globe, 
  Tag, 
  Info, 
  Sparkles, 
  ArrowRight,
  Database,
  RefreshCw,
  Clock,
  Layers,
  Activity,
  ChevronRight,
  Check,
  AlertOctagon,
  Eye,
  X
} from 'lucide-react';

import { 
  fetchSampleDatasets, 
  uploadMerchantDataset, 
  analyzeMerchantSession,
  investigateSessionCustomer
} from '../services/api';
import { 
  DatasetValidationResult, 
  SampleDatasetItem, 
  SessionAnalysisReport,
  SessionInvestigationResponse,
  SessionCustomerRisk
} from '../types';

export const MerchantAnalysis: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [validating, setValidating] = useState(false);
  const [analyzingGraph, setAnalyzingGraph] = useState(false);
  const [investigatingCustomer, setInvestigatingCustomer] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [validationResult, setValidationResult] = useState<DatasetValidationResult | null>(null);
  const [analysisReport, setAnalysisReport] = useState<SessionAnalysisReport | null>(null);
  const [selectedCustomerInvestigation, setSelectedCustomerInvestigation] = useState<SessionInvestigationResponse | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const { data: sampleDatasets } = useQuery({
    queryKey: ['sample-datasets'],
    queryFn: fetchSampleDatasets,
  });

  const handleFile = (file: File) => {
    setSelectedFile(file);
    setError(null);
    setValidationResult(null);
    setAnalysisReport(null);
    setSelectedCustomerInvestigation(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const runFullPipeline = async (file: File) => {
    setValidating(true);
    setError(null);
    setAnalysisReport(null);
    setSelectedCustomerInvestigation(null);

    try {
      const valRes = await uploadMerchantDataset(file);
      setValidationResult(valRes);

      if (valRes.valid) {
        setAnalyzingGraph(true);
        const report = await analyzeMerchantSession(valRes.session_id);
        setAnalysisReport(report);

        // Auto-select top risky customer for preview if present
        if (report.customer_risks.length > 0) {
          const topCust = report.customer_risks[0];
          const inv = await investigateSessionCustomer(valRes.session_id, topCust.customer_id);
          setSelectedCustomerInvestigation(inv);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to process merchant dataset');
    } finally {
      setValidating(false);
      setAnalyzingGraph(false);
    }
  };

  const handleUploadAndAnalyze = () => {
    if (selectedFile) {
      runFullPipeline(selectedFile);
    }
  };

  const loadSampleDataset = async (sample: SampleDatasetItem) => {
    const blob = new Blob([sample.content], { 
      type: sample.file_format === 'json' ? 'application/json' : 'text/csv' 
    });
    const file = new File([blob], `${sample.dataset_id}.${sample.file_format}`, {
      type: sample.file_format === 'json' ? 'application/json' : 'text/csv'
    });
    setSelectedFile(file);
    await runFullPipeline(file);
  };

  const handleSelectCustomer = async (cid: string) => {
    if (!validationResult) return;
    setInvestigatingCustomer(true);
    try {
      const inv = await investigateSessionCustomer(validationResult.session_id, cid);
      setSelectedCustomerInvestigation(inv);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve customer investigation');
    } finally {
      setInvestigatingCustomer(false);
    }
  };

  return (
    <div className="space-y-6 pb-20">
      
      {/* 1. Header & Identity */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">
                  Merchant Dataset Analysis Workspace
                </h1>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                  Isolated Workspace
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Upload external customer & transaction batches to detect coordinated abuse rings, extract graph topologies, and generate evidence dossiers.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Honest Architectural Boundary Notice */}
      <div className="p-4 bg-slate-900/90 border border-indigo-500/30 rounded-2xl flex items-start gap-3 text-xs leading-relaxed text-slate-300 shadow-sm">
        <Info className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-indigo-200">Session Workspace Isolation & Dataset Safety</div>
          <p className="text-slate-400">
            Uploaded merchant datasets are parsed, clustered, and investigated inside an isolated session namespace. 
            The production graph database and seeded reference profiles (<span className="text-slate-200 font-mono">C_00003</span>, <span className="text-slate-200 font-mono">C_46046</span>) remain 100% untouched and deterministic.
            Sentinel strictly enforces anti-leakage guards to block target label injection.
          </p>
        </div>
      </div>

      {/* 3. 1-Click Sample Dataset Bar for Judges */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span>Quick Evaluation Samples for Judges (1-Click Upload, Graph Analysis & Evidence Extraction):</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {sampleDatasets?.map((s) => {
            const isHostile = s.dataset_id.includes('hostile');
            const isRing = s.dataset_id.includes('promo');

            return (
              <button
                key={s.dataset_id}
                onClick={() => loadSampleDataset(s)}
                disabled={validating || analyzingGraph}
                className={`p-3.5 text-left rounded-xl border transition-all disabled:opacity-50 ${
                  isHostile 
                    ? 'bg-rose-950/20 border-rose-800/40 hover:border-rose-600 hover:bg-rose-950/40' 
                    : isRing 
                    ? 'bg-amber-950/20 border-amber-800/40 hover:border-amber-600 hover:bg-amber-950/40' 
                    : 'bg-slate-950/60 border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-bold ${
                    isHostile ? 'text-rose-400' : isRing ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    {s.name}
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase font-semibold">
                    {s.file_format}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed line-clamp-2">
                  {s.description}
                </p>
                <div className="text-[10px] text-indigo-400 font-semibold mt-2 font-mono flex items-center gap-1">
                  <span>{s.record_count} Records • Click to Run Graph Analysis →</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Interactive Upload & Dropzone */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight">Upload Custom Merchant Dataset</h3>
            <p className="text-xs text-slate-400 mt-0.5">Supports CSV, JSON, or JSONL files (up to 5,000 records)</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">Max 10 MB</span>
        </div>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
            dragActive 
              ? 'border-indigo-500 bg-indigo-500/10' 
              : 'border-slate-800 hover:border-slate-700 bg-slate-950/40 hover:bg-slate-950/60'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.json,.jsonl,.ndjson"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            className="hidden"
          />

          <div className="w-12 h-12 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto text-slate-400 mb-3">
            <FileText className="w-6 h-6 text-indigo-400" />
          </div>

          <div className="text-xs font-bold text-white">
            {selectedFile ? selectedFile.name : 'Click to select or drag & drop merchant transaction batch'}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Required columns: <code className="text-indigo-300">customer_id</code>, <code className="text-indigo-300">transaction_id</code>, <code className="text-indigo-300">amount</code>, <code className="text-indigo-300">timestamp</code>. Optional: <code className="text-slate-300">device_id</code>, <code className="text-slate-300">ip_address</code>, <code className="text-slate-300">coupon_code</code>.
          </p>
        </div>

        {selectedFile && (
          <div className="flex items-center justify-between p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-indigo-300 font-bold">{selectedFile.name}</span>
              <span className="text-[11px] text-slate-500 font-mono">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
            </div>

            <button
              onClick={handleUploadAndAnalyze}
              disabled={validating || analyzingGraph}
              className="flex items-center gap-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-950/50 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${validating || analyzingGraph ? 'animate-spin' : ''}`} />
              <span>{validating ? 'Validating Schema...' : analyzingGraph ? 'Analyzing Graph Topology...' : 'Run Graph Risk Analysis'}</span>
            </button>
          </div>
        )}

        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-400 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* 5. Validation Dossier & Security Rejection Alert */}
      {validationResult && !validationResult.valid && (
        <div className="p-5 rounded-2xl border bg-rose-500/10 border-rose-500/30 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center gap-3 text-rose-400 font-bold text-sm">
            <ShieldAlert className="w-5 h-5" />
            <span>Security Policy Violation / Schema Rejection</span>
          </div>
          <ul className="pl-6 list-disc text-xs text-rose-300 space-y-1">
            {validationResult.errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 6. Active Graph Analysis Results Section */}
      {analysisReport && (
        <div ref={resultsRef} className="space-y-6 animate-in fade-in slide-in-from-top-4 duration-300">
          
          {/* Section Banner */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-slate-900 border border-indigo-500/30 rounded-2xl">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white tracking-tight">
                  Graph Risk Intelligence Dossier
                </h2>
                <p className="text-xs text-slate-400">
                  Evaluated {analysisReport.total_customers} accounts across shared hardware, network gateways, and promotional campaigns.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-bold font-mono">
                {analysisReport.reviews_required} Reviews Required
              </span>
              <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold font-mono">
                {analysisReport.detected_clusters.length} Coordinated Rings Detected
              </span>
            </div>
          </div>

          {/* 6.1 Detected Abuse Rings / Clusters Cards */}
          {analysisReport.detected_clusters.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Detected Coordinated Abuse Rings ({analysisReport.detected_clusters.length})
                </h3>
                <span className="text-[11px] text-slate-500 font-mono">Connected Component Subgraphs</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {analysisReport.detected_clusters.map((ring) => (
                  <div 
                    key={ring.cluster_id} 
                    className="p-5 bg-slate-900/90 border border-rose-500/40 rounded-2xl space-y-3 shadow-lg shadow-rose-950/10"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
                        <span className="text-sm font-bold text-white font-mono">{ring.cluster_id}</span>
                        <span className="px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 font-bold text-[10px] font-mono">
                          {ring.risk_level} RISK
                        </span>
                      </div>
                      <span className="text-xs font-mono font-bold text-rose-400">
                        {ring.customer_count} Coordinated Accounts
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {ring.summary}
                    </p>

                    <div className="space-y-1.5 pt-1">
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        Ring Infrastructure Overlaps:
                      </div>
                      <div className="flex flex-wrap gap-1.5 text-xs font-mono">
                        {ring.shared_devices.map((d) => (
                          <span key={d} className="px-2 py-0.5 rounded bg-sky-950/80 border border-sky-800/80 text-sky-300 text-[11px]">
                            📱 {d}
                          </span>
                        ))}
                        {ring.shared_ips.map((ip) => (
                          <span key={ip} className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800/80 text-emerald-300 text-[11px]">
                            🌐 {ip}
                          </span>
                        ))}
                        {ring.shared_coupons.map((c) => (
                          <span key={c} className="px-2 py-0.5 rounded bg-amber-950/80 border border-amber-800/80 text-amber-300 text-[11px]">
                            🎟️ {c}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-800 flex flex-wrap gap-1.5 items-center">
                      <span className="text-[10px] text-slate-400 font-semibold mr-1">Member Accounts:</span>
                      {ring.customer_ids.map((cid) => (
                        <button
                          key={cid}
                          onClick={() => handleSelectCustomer(cid)}
                          className="px-2 py-0.5 rounded-lg bg-slate-800 hover:bg-indigo-600 text-slate-200 hover:text-white font-mono text-xs transition-colors"
                        >
                          {cid}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-center gap-3 text-xs text-emerald-300">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
              <span>Clean Topology: No multi-account hardware or network infrastructure clusters detected in this dataset.</span>
            </div>
          )}

          {/* 6.2 Customer Risk Queue for this Uploaded Batch */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-white tracking-tight">
                  Session Customer Risk Queue ({analysisReport.customer_risks.length} Accounts)
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Ranked by inductive multi-signal graph coordination probability
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950 text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Customer ID</th>
                    <th className="py-3 px-4">Risk Probability</th>
                    <th className="py-3 px-4">Risk Tier</th>
                    <th className="py-3 px-4">Decision Status</th>
                    <th className="py-3 px-4">Graph Evidence Signals</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {analysisReport.customer_risks.map((cust) => {
                    const isSelected = selectedCustomerInvestigation?.customer_id === cust.customer_id;

                    return (
                      <tr 
                        key={cust.customer_id}
                        className={`transition-colors ${
                          isSelected ? 'bg-indigo-950/40 border-l-2 border-indigo-500' : 'hover:bg-slate-950/60'
                        }`}
                      >
                        <td className="py-3 px-4 font-mono font-bold text-indigo-300">
                          {cust.customer_id}
                        </td>

                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-white text-xs w-12">
                              {(cust.risk_probability * 100).toFixed(1)}%
                            </span>
                            <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                              <div 
                                className={`h-full rounded-full ${
                                  cust.risk_level === 'HIGH' ? 'bg-rose-500' :
                                  cust.risk_level === 'MEDIUM' ? 'bg-amber-500' : 'bg-emerald-500'
                                }`}
                                style={{ width: `${cust.risk_probability * 100}%` }}
                              />
                            </div>
                          </div>
                        </td>

                        <td className="py-3 px-4 font-mono font-bold">
                          <span className={`px-2 py-0.5 rounded text-[11px] ${
                            cust.risk_level === 'HIGH' ? 'bg-rose-500/20 text-rose-300' :
                            cust.risk_level === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-400'
                          }`}>
                            {cust.risk_level}
                          </span>
                        </td>

                        <td className="py-3 px-4">
                          {cust.review_required ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-rose-500/20 text-rose-300 font-semibold text-[11px]">
                              <AlertOctagon className="w-3 h-3" />
                              Review Required
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 font-semibold text-[11px]">
                              <Check className="w-3 h-3" />
                              Routine
                            </span>
                          )}
                        </td>

                        <td className="py-3 px-4">
                          <div className="max-w-md text-xs text-slate-300 leading-snug">
                            {cust.primary_flag_reason}
                          </div>
                        </td>

                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleSelectCustomer(cust.customer_id)}
                            disabled={investigatingCustomer}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors shadow-sm"
                          >
                            <span>Inspect Graph</span>
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 6.3 Deep-Dive Customer Investigation Dossier & Visual Evidence Graph */}
          {selectedCustomerInvestigation && (
            <div className="bg-slate-900 border border-indigo-500/40 rounded-2xl p-6 space-y-6 shadow-2xl animate-in slide-in-from-top-4 duration-300">
              
              {/* Investigation Header */}
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center font-mono">
                    <span className="text-[10px] uppercase text-slate-400 font-bold">SCORE</span>
                    <span className={`text-base font-extrabold ${
                      selectedCustomerInvestigation.risk_level === 'HIGH' ? 'text-rose-400' :
                      selectedCustomerInvestigation.risk_level === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {(selectedCustomerInvestigation.risk_probability * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-white font-mono">
                        {selectedCustomerInvestigation.customer_id}
                      </h3>
                      <span className={`px-2 py-0.5 rounded-md font-mono text-xs font-bold ${
                        selectedCustomerInvestigation.risk_level === 'HIGH' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                        selectedCustomerInvestigation.risk_level === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                        'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}>
                        {selectedCustomerInvestigation.risk_level} RISK
                      </span>
                      {selectedCustomerInvestigation.review_required ? (
                        <span className="px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-bold">
                          Review Required (≥ 60%)
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-bold">
                          Routine Account
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-300 mt-0.5">
                      {selectedCustomerInvestigation.primary_reason}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedCustomerInvestigation(null)}
                  className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Visual Evidence Graph Subgraph Canvas */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Interactive Evidence Network Subgraph
                  </h4>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {selectedCustomerInvestigation.graph.displayed_nodes_count} Nodes • {selectedCustomerInvestigation.graph.edges.length} Relationships
                  </span>
                </div>

                <div className="p-6 bg-slate-950/90 border border-slate-800 rounded-2xl relative min-h-[320px] flex flex-col justify-between overflow-hidden">
                  
                  {/* Legend */}
                  <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono pb-4 border-b border-slate-800/80">
                    <span className="flex items-center gap-1 text-rose-400 font-bold">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Investigated Target
                    </span>
                    <span className="flex items-center gap-1 text-sky-400">
                      <span className="w-2.5 h-2.5 rounded-md bg-sky-500"></span> Hardware Device
                    </span>
                    <span className="flex items-center gap-1 text-emerald-400">
                      <span className="w-2.5 h-2.5 rounded-md bg-emerald-500"></span> Network IP
                    </span>
                    <span className="flex items-center gap-1 text-amber-400">
                      <span className="w-2.5 h-2.5 rounded-md bg-amber-500"></span> Promo Coupon
                    </span>
                    <span className="flex items-center gap-1 text-indigo-300">
                      <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> Connected Peer Accounts
                    </span>
                  </div>

                  {/* Hierarchical 3-Tier Visual Layout */}
                  <div className="py-6 space-y-8 text-center">
                    
                    {/* Tier 1: Target Node */}
                    <div>
                      <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-gradient-to-r from-rose-950 to-indigo-950 border-2 border-rose-500 text-white font-mono font-bold text-sm shadow-xl shadow-rose-950/50">
                        <span>🎯 {selectedCustomerInvestigation.customer_id}</span>
                        <span className="text-xs px-2 py-0.5 rounded bg-rose-500/30 text-rose-200">Target</span>
                      </div>
                    </div>

                    {/* Connecting arrows indicator */}
                    <div className="text-xs text-slate-500 font-mono">
                      │ connects to shared infrastructure hubs │
                    </div>

                    {/* Tier 2: Infrastructure Hubs */}
                    <div className="flex flex-wrap items-center justify-center gap-4">
                      {selectedCustomerInvestigation.graph.nodes
                        .filter((n) => n.type !== 'target' && n.type !== 'customer')
                        .map((hub) => (
                          <div
                            key={hub.id}
                            className={`px-4 py-2 rounded-xl font-mono text-xs font-bold border shadow-md ${
                              hub.type === 'device' 
                                ? 'bg-sky-950/70 border-sky-500/60 text-sky-300' 
                                : hub.type === 'ip' 
                                ? 'bg-emerald-950/70 border-emerald-500/60 text-emerald-300' 
                                : 'bg-amber-950/70 border-amber-500/60 text-amber-300'
                            }`}
                          >
                            {hub.type === 'device' ? '📱 ' : hub.type === 'ip' ? '🌐 ' : '🎟️ '}
                            {hub.id}
                          </div>
                        ))}
                    </div>

                    {/* Connecting arrows indicator */}
                    <div className="text-xs text-slate-500 font-mono">
                      │ shared by connected peer accounts │
                    </div>

                    {/* Tier 3: Connected Customers */}
                    <div className="flex flex-wrap items-center justify-center gap-2.5">
                      {selectedCustomerInvestigation.graph.nodes
                        .filter((n) => n.type === 'customer')
                        .map((peer) => (
                          <div
                            key={peer.id}
                            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-indigo-500/40 font-mono text-xs text-indigo-300 flex items-center gap-1.5 shadow-sm"
                          >
                            <span className="font-bold">{peer.id}</span>
                            {peer.data.signal_count >= 2 && (
                              <span className="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 text-[10px] font-bold">
                                {peer.data.signal_count}x Signals
                              </span>
                            )}
                          </div>
                        ))}
                    </div>

                  </div>

                  <div className="text-[11px] text-slate-500 font-mono text-center pt-2 border-t border-slate-900">
                    Deterministic graph topology extracted from session batch relationships.
                  </div>
                </div>
              </div>

              {/* Evidence-Grounded Narrative Dossier */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
                  <div className="text-xs font-bold text-white uppercase tracking-wider">
                    Observable Evidence Details
                  </div>
                  <ul className="space-y-1.5 pl-5 list-disc text-xs text-slate-300">
                    {selectedCustomerInvestigation.explanation.observed_evidence.map((ev, i) => (
                      <li key={i}>{ev}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
                  <div className="text-xs font-bold text-white uppercase tracking-wider">
                    Recommended Operational Action
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {selectedCustomerInvestigation.explanation.recommended_action}
                  </p>
                  <div className="flex items-center gap-2 pt-2">
                    <span className="px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-mono text-[11px]">
                      Session Analysis Status: Complete
                    </span>
                  </div>
                </div>
              </div>

            </div>
          )}

        </div>
      )}

    </div>
  );
};
