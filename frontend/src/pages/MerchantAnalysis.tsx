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
  Terminal,
  RefreshCw,
  Clock
} from 'lucide-react';

import { 
  fetchSampleDatasets, 
  uploadMerchantDataset, 
  validateMerchantPayload 
} from '../services/api';
import { DatasetValidationResult, SampleDatasetItem } from '../types';

export const MerchantAnalysis: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<DatasetValidationResult | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: sampleDatasets } = useQuery({
    queryKey: ['sample-datasets'],
    queryFn: fetchSampleDatasets,
  });

  const handleFile = (file: File) => {
    setSelectedFile(file);
    setError(null);
    setValidationResult(null);
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

  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) return;
    setAnalyzing(true);
    setError(null);

    try {
      const res = await uploadMerchantDataset(selectedFile);
      setValidationResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze merchant dataset');
    } finally {
      setAnalyzing(false);
    }
  };

  const loadSampleDataset = async (sample: SampleDatasetItem) => {
    setAnalyzing(true);
    setError(null);
    setValidationResult(null);
    setSelectedFile(null);

    try {
      // Parse sample content and create a Blob file
      const blob = new Blob([sample.content], { 
        type: sample.file_format === 'json' ? 'application/json' : 'text/csv' 
      });
      const file = new File([blob], `${sample.dataset_id}.${sample.file_format}`, {
        type: sample.file_format === 'json' ? 'application/json' : 'text/csv'
      });
      setSelectedFile(file);
      const res = await uploadMerchantDataset(file);
      setValidationResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load sample dataset');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6 pb-16">
      
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
                Ingest, validate, and inspect external merchant customer & checkout transaction batches without altering reference demo data.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Honest Architectural Boundary Notice */}
      <div className="p-4 bg-slate-900/90 border border-indigo-500/30 rounded-2xl flex items-start gap-3 text-xs leading-relaxed text-slate-300">
        <Info className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-indigo-200">Architectural Boundary & Session Isolation</div>
          <p className="text-slate-400">
            Uploaded merchant datasets are validated and analyzed inside a dedicated session workspace. 
            The production graph database and seeded demonstration profiles (<span className="text-slate-200 font-mono">C_00003</span>, <span className="text-slate-200 font-mono">C_46046</span>) remain 100% untouched and deterministic.
            Sentinel strictly enforces anti-leakage guards to prevent target label contamination.
          </p>
        </div>
      </div>

      {/* 3. 1-Click Sample Dataset Bar for Judges */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span>Quick Evaluation Samples for Judges (1-Click Load & Validate):</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {sampleDatasets?.map((s) => {
            const isHostile = s.dataset_id.includes('hostile');
            const isRing = s.dataset_id.includes('promo');

            return (
              <button
                key={s.dataset_id}
                onClick={() => loadSampleDataset(s)}
                disabled={analyzing}
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
                <div className="text-[10px] text-slate-500 mt-2 font-mono">
                  {s.record_count} Records • Click to Validate →
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
            <h3 className="text-sm font-bold text-white tracking-tight">Upload External Merchant Batch</h3>
            <p className="text-xs text-slate-400 mt-0.5">Supports CSV, JSON (array of transactions), or JSONL formats (up to 5,000 records)</p>
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

          <div className="w-12 h-12 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto text-slate-400 mb-3 group-hover:scale-105 transition-transform">
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
              disabled={analyzing}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-950/50 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
              <span>{analyzing ? 'Validating Dataset...' : 'Validate & Analyze Dataset'}</span>
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

      {/* 5. Validation Dossier & Results */}
      {validationResult && (
        <div className="space-y-6 animate-in fade-in duration-300">
          
          {/* Status Header */}
          <div className={`p-5 rounded-2xl border ${
            validationResult.valid 
              ? 'bg-emerald-500/5 border-emerald-500/30' 
              : 'bg-rose-500/5 border-rose-500/30'
          }`}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                {validationResult.valid ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-6 h-6 text-rose-400" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className={`text-base font-bold ${validationResult.valid ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {validationResult.valid ? 'Dataset Schema Validated & Ready for Graph Analysis' : 'Dataset Rejected: Security or Schema Violations'}
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 uppercase">
                      {validationResult.file_format} format
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 font-mono">
                    Session ID: {validationResult.session_id} • File: {validationResult.filename}
                  </p>
                </div>
              </div>

              <div className="text-right">
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold font-mono ${
                  validationResult.valid ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}>
                  {validationResult.valid ? 'PASSED VALIDATION' : 'VALIDATION FAILED'}
                </span>
              </div>
            </div>
          </div>

          {/* Validation Errors & Security Guards */}
          {validationResult.errors.length > 0 && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-rose-400">
                <ShieldAlert className="w-4 h-4" />
                <span>Validation Errors & Policy Rejections:</span>
              </div>
              <ul className="space-y-1.5 pl-6 list-disc text-xs text-rose-300">
                {validationResult.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings & Graph Topology Signals */}
          {validationResult.warnings.length > 0 && (
            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-400">
                <AlertTriangle className="w-4 h-4" />
                <span>Observed Graph Topology Warnings & Data Quality Notes:</span>
              </div>
              <ul className="space-y-1.5 pl-6 list-disc text-xs text-amber-300">
                {validationResult.warnings.map((warn, i) => (
                  <li key={i}>{warn}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 6 Entity Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-semibold uppercase">Customers</span>
                <Users className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {validationResult.summary.customer_count.toLocaleString()}
              </div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-semibold uppercase">Transactions</span>
                <CreditCard className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {validationResult.summary.transaction_count.toLocaleString()}
              </div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-semibold uppercase">Devices</span>
                <Smartphone className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {validationResult.summary.unique_devices_count.toLocaleString()}
              </div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-semibold uppercase">IP Gateways</span>
                <Globe className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {validationResult.summary.unique_ips_count.toLocaleString()}
              </div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-semibold uppercase">Coupons</span>
                <Tag className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {validationResult.summary.unique_coupons_count.toLocaleString()}
              </div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-semibold uppercase">Total Volume</span>
                <span className="text-xs font-mono text-slate-400">INR</span>
              </div>
              <div className="text-lg font-bold font-mono text-white mt-1">
                ₹{validationResult.summary.total_volume_inr.toLocaleString()}
              </div>
            </div>
          </div>

          {/* Schema Compatibility Analysis */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Schema Field Compatibility Mapping
              </h4>
              <span className="text-[11px] text-slate-400 font-mono">
                {validationResult.schema_analysis.detected_fields.length} detected fields
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {validationResult.schema_analysis.detected_fields.map((field) => (
                <span
                  key={field}
                  className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-700 text-xs font-mono text-indigo-300 font-semibold"
                >
                  ✓ {field}
                </span>
              ))}
              {validationResult.schema_analysis.missing_optional_fields.map((field) => (
                <span
                  key={field}
                  className="px-2.5 py-1 rounded-lg bg-slate-950/60 border border-slate-800 text-xs font-mono text-slate-500"
                >
                  ○ {field} (optional omitted)
                </span>
              ))}
            </div>
          </div>

          {/* Data Preview Table */}
          {validationResult.preview_rows.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Validated Record Preview (Top 5 Records)
              </h4>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950/80 text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Customer</th>
                      <th className="py-2.5 px-3">Transaction</th>
                      <th className="py-2.5 px-3">Amount</th>
                      <th className="py-2.5 px-3">Timestamp</th>
                      <th className="py-2.5 px-3">Device ID</th>
                      <th className="py-2.5 px-3">IP Address</th>
                      <th className="py-2.5 px-3">Coupon</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {validationResult.preview_rows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-950/50 transition-colors">
                        <td className="py-2.5 px-3 font-bold text-indigo-400">{row.customer_id}</td>
                        <td className="py-2.5 px-3 text-slate-300">{row.transaction_id}</td>
                        <td className="py-2.5 px-3 text-emerald-400">₹{parseFloat(row.amount).toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-slate-400">{row.timestamp}</td>
                        <td className="py-2.5 px-3 text-amber-300">{row.device_id || '—'}</td>
                        <td className="py-2.5 px-3 text-sky-300">{row.ip_address || '—'}</td>
                        <td className="py-2.5 px-3 text-purple-300">{row.coupon_code || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Next Steps: Graph Construction & Inductive Scoring Explanation */}
          <div className="p-5 bg-indigo-950/20 border border-indigo-500/30 rounded-2xl space-y-2.5 text-xs text-slate-300">
            <div className="flex items-center gap-2 font-bold text-indigo-300">
              <Database className="w-4 h-4" />
              <span>Next Phase Pipeline: Normalization, Graph Ingestion & Inductive Risk Screening</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Once validated, external merchant batches proceed through Sentinel's three-stage pipeline:
              <br />
              <strong className="text-slate-200">1. Graph Projection:</strong> Constructs heterogeneous nodes (<code className="text-indigo-300">Customer</code>, <code className="text-sky-300">Device</code>, <code className="text-emerald-300">IP</code>, <code className="text-amber-300">Coupon</code>) in an isolated session namespace.
              <br />
              <strong className="text-slate-200">2. Inductive Feature Mapping:</strong> Computes temporal burst density, device sharing degree, and referral trees according to the frozen schema space.
              <br />
              <strong className="text-slate-200">3. GraphSAGE Inference:</strong> Generates coordination probabilities without contaminating the main reference dataset.
            </p>
          </div>

        </div>
      )}

    </div>
  );
};
