import React from 'react';
import { ShieldCheck, AlertTriangle, Database, Clock, ExternalLink, CheckCircle2 } from 'lucide-react';

export default function DataQualityPanel({ dataQuality, sources = [] }) {
  if (!dataQuality && (!sources || sources.length === 0)) return null;

  const status = dataQuality?.quality_status || 'VALID';
  const statusStyles =
    status === 'VALID'
      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
      : status === 'VALID_WITH_WARNINGS'
      ? 'bg-amber-50 text-amber-700 border-amber-200'
      : 'bg-rose-50 text-rose-700 border-rose-200';

  return (
    <div className="space-y-6">
      {dataQuality && (
        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Market Data Validation & Quality Checks</h3>
                <p className="text-xs text-slate-500">
                  Validated at {dataQuality.validated_at ? new Date(dataQuality.validated_at).toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>

            <span className={`text-xs font-bold px-3 py-1 rounded-full border ${statusStyles}`}>
              {status}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-[11px] font-semibold text-slate-400 uppercase block">Valid OHLCV Bars</span>
              <span className="text-lg font-extrabold text-slate-900">
                {dataQuality.valid_rows} <span className="text-xs font-medium text-slate-400">/ {dataQuality.total_raw_rows}</span>
              </span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-[11px] font-semibold text-slate-400 uppercase block">Duplicate Dates</span>
              <span className="text-lg font-extrabold text-slate-900">{dataQuality.duplicate_dates_removed}</span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-[11px] font-semibold text-slate-400 uppercase block">Missing Values</span>
              <span className="text-lg font-extrabold text-slate-900">{dataQuality.missing_values_count}</span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-[11px] font-semibold text-slate-400 uppercase block">Inconsistent Rows</span>
              <span className="text-lg font-extrabold text-slate-900">{dataQuality.inconsistent_rows_count}</span>
            </div>
          </div>

          {dataQuality.notes?.length > 0 && (
            <div className="space-y-1.5">
              {dataQuality.notes.map((n, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-slate-600">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                  <span>{n}</span>
                </div>
              ))}
            </div>
          )}

          {(dataQuality.missing_value_details?.length > 0 ||
            dataQuality.inconsistent_row_details?.length > 0 ||
            dataQuality.date_gaps?.length > 0) && (
            <div className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-800 space-y-1">
              <div className="font-bold flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                Validation Warnings
              </div>
              {dataQuality.missing_value_details?.map((d, i) => (
                <p key={`m-${i}`}>• {d}</p>
              ))}
              {dataQuality.inconsistent_row_details?.map((d, i) => (
                <p key={`i-${i}`}>• {d}</p>
              ))}
              {dataQuality.date_gaps?.length > 0 && (
                <p>• Trading calendar gaps (&gt;7d): {dataQuality.date_gaps.join(', ')}</p>
              )}
            </div>
          )}
        </div>
      )}

      {sources && sources.length > 0 && (
        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Data Sources & Provenance Timestamps</h3>
              <p className="text-xs text-slate-500">Verifiable source URLs, retrieval times, and integrity hashes</p>
            </div>
          </div>

          <div className="divide-y divide-slate-100">
            {sources.map((src, idx) => (
              <div key={idx} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono">
                      {src.source_type}
                    </span>
                    <span className="text-xs font-bold text-slate-800">{src.title}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Retrieved: {src.retrieved_at ? new Date(src.retrieved_at).toLocaleString() : 'N/A'}
                    </span>
                    {src.content_hash && (
                      <span className="font-mono text-[10px] text-slate-400">
                        SHA256: {src.content_hash.slice(0, 14)}…
                      </span>
                    )}
                  </div>
                </div>

                {src.source_url && (
                  <a
                    href={src.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700"
                  >
                    <span>Source</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

