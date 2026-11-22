import React, { useState } from 'react';
import {
  FileText,
  FileCode,
  Globe,
  FileType,
  Download,
  X,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { api } from '../api/client';

export default function ExportModal({ sessionId, ticker, companyName, onClose }) {
  const [downloadingFormat, setDownloadingFormat] = useState(null);
  const [successFormat, setSuccessFormat] = useState(null);
  const [error, setError] = useState(null);

  const exportOptions = [
    {
      format: 'pdf',
      name: 'Executive PDF Report',
      extension: '.pdf',
      badge: 'PDF',
      icon: FileType,
      color: 'bg-rose-50/40 text-rose-800 border-rose-200/70 hover:border-rose-400',
      iconColor: 'text-rose-600',
    },
    {
      format: 'json',
      name: 'Structured JSON Dataset',
      extension: '.json',
      badge: 'JSON',
      icon: FileCode,
      color: 'bg-blue-50/40 text-blue-800 border-blue-200/70 hover:border-blue-400',
      iconColor: 'text-blue-600',
    },
    {
      format: 'html',
      name: 'Interactive HTML Dossier',
      extension: '.html',
      badge: 'HTML',
      icon: Globe,
      color: 'bg-emerald-50/40 text-emerald-800 border-emerald-200/70 hover:border-emerald-400',
      iconColor: 'text-emerald-600',
    },
    {
      format: 'markdown',
      name: 'Markdown Briefing Document',
      extension: '.md',
      badge: 'MD',
      icon: FileText,
      color: 'bg-purple-50/40 text-purple-800 border-purple-200/70 hover:border-purple-400',
      iconColor: 'text-purple-600',
    },
  ];

  const handleDownload = async (format) => {
    setError(null);
    setSuccessFormat(null);
    setDownloadingFormat(format);

    try {
      await api.downloadReport(sessionId, format, ticker);
      setSuccessFormat(format);
      setTimeout(() => {
        setSuccessFormat(null);
      }, 3000);
    } catch (err) {
      setError(err.message || `Failed to download ${format.toUpperCase()} report.`);
    } finally {
      setDownloadingFormat(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fadeIn">
      <div className="w-full max-w-xl bg-white rounded-[28px] shadow-2xl border border-gray-100 overflow-hidden">
        {/* Modal Header */}
        <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-gray-50/80 to-white">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-2xl bg-[#C5F500]/30 border border-[#C5F500]/40 text-[#111318] flex items-center justify-center shrink-0">
              <Download className="w-5 h-5 text-[#111318]" />
            </div>
            <div>
              <h2 className="text-lg font-black text-[#111318]">
                Export Research Report
              </h2>
              <p className="text-xs text-gray-500 font-medium">
                {companyName || ticker} ({ticker}) • Session #{sessionId}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-700 flex items-center justify-center transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 gap-3">
            {exportOptions.map((opt) => {
              const Icon = opt.icon;
              const isDownloading = downloadingFormat === opt.format;
              const isSuccess = successFormat === opt.format;

              return (
                <div
                  key={opt.format}
                  className={`p-4 rounded-2xl border transition-all flex items-center justify-between gap-4 ${opt.color}`}
                >
                  <div className="flex items-center gap-3.5">
                    <div className="p-2.5 rounded-xl bg-white shadow-xs shrink-0">
                      <Icon className={`w-5 h-5 ${opt.iconColor}`} />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-black text-sm text-[#111318]">
                        {opt.name}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white/90 border border-black/5 text-gray-700">
                        {opt.badge}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDownload(opt.format)}
                    disabled={isDownloading}
                    className="h-9 px-4 rounded-xl bg-[#17191F] hover:bg-black active:scale-95 text-white text-xs font-black flex items-center gap-2 transition shrink-0 cursor-pointer disabled:opacity-50 shadow-xs"
                  >
                    {isDownloading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-[#C5F500]" />
                        <span>Generating...</span>
                      </>
                    ) : isSuccess ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#C5F500]" />
                        <span>Saved</span>
                      </>
                    ) : (
                      <>
                        <Download className="w-3.5 h-3.5" />
                        <span>Download</span>
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-gray-50/80 border-t border-gray-100 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl text-gray-600 hover:text-black font-bold text-xs hover:bg-gray-200/60 transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
