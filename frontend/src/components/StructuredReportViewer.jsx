import React from 'react';
import {
  Building2,
  BarChart3,
  TrendingUp,
  Newspaper,
  ShieldAlert,
  Scale,
  Link2,
  AlertOctagon,
  Clock,
  Sparkles,
  ExternalLink
} from 'lucide-react';

const SECTION_ICONS = {
  1: Building2,
  2: BarChart3,
  3: TrendingUp,
  4: Newspaper,
  5: ShieldAlert,
  6: Scale,
  7: Link2,
  8: AlertOctagon,
};

export const StructuredReportViewer = ({ content }) => {
  if (!content) return null;

  // Split content by markdown section headings (### X.)
  const rawSections = content.split(/(?=### \d+\.)/);

  const renderBadge = (tag) => {
    const t = tag.toUpperCase();
    if (t.includes('FACTUAL') || t.includes('CALCULATED')) {
      return null;
    }
    if (t.includes('COMING SOON') || t.includes('SCHEDULED')) {
      return (
        <span key={tag} className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-300 border border-purple-500/30">
          COMING SOON
        </span>
      );
    }
    return null;
  };

  return (
    <div className="space-y-3.5">
      {rawSections.map((sec, idx) => {
        const trimmed = sec.trim();
        if (!trimmed) return null;

        const lines = trimmed.split('\n');
        const firstLine = lines[0] || '';
        const isHeader = firstLine.startsWith('### ');

        // Extract section number and clean title
        let secNumber = idx + 1;
        let cleanTitle = firstLine;
        let badges = [];

        if (isHeader) {
          const numMatch = firstLine.match(/###\s+(\d+)\./);
          if (numMatch) secNumber = parseInt(numMatch[1], 10);

          const tagMatches = firstLine.match(/\[(.*?)\]/g) || [];
          badges = tagMatches.map((t) => t.replace(/[\[\]]/g, ''));

          cleanTitle = firstLine
            .replace(/^###\s+\d+\.\s*/, '')
            .replace(/\[.*?\]/g, '')
            .trim();
        }

        if (!isHeader) {
          // Ignore preambles (such as legacy currency notices) before Section 1 to prevent duplicate popups
          return null;
        }

        const IconComponent = SECTION_ICONS[secNumber] || Sparkles;
        const bodyLines = lines.slice(1);

        return (
          <div
            key={idx}
            className="p-4 rounded-2xl bg-[#0a0e15] border border-[#1a2332] shadow-sm hover:border-[#223044] transition-all space-y-3"
          >
            {/* Section Header */}
            <div className="flex items-center justify-between flex-wrap gap-2 pb-2.5 border-b border-[#141b25]">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 shrink-0">
                  <IconComponent className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h5 className="text-xs sm:text-sm font-bold text-white flex items-center gap-1.5">
                    <span className="text-slate-400 font-mono text-xs">{secNumber}.</span>
                    <span>{cleanTitle}</span>
                  </h5>
                </div>
              </div>

              <div className="flex items-center gap-1.5 flex-wrap">
                {badges.map((b) => renderBadge(b))}
              </div>
            </div>

            {/* Section Content */}
            <div className="space-y-2 text-xs text-slate-300 leading-relaxed font-sans">
              {bodyLines.map((line, lIdx) => {
                const lineTrim = line.trim();
                if (!lineTrim) return null;

                // Suppress duplicate currency notice (it is already cleanly displayed in Executive Synthesis)
                if (lineTrim.startsWith('**⚠️') || lineTrim.includes('Currency Notice')) {
                  return null;
                }

                // Bullet point parsing
                if (lineTrim.startsWith('- **')) {
                  const match = lineTrim.match(/^-\s+\*\*(.*?)\*\*(.*)/);
                  if (match) {
                    const label = match[1]
                      .replace(/\[FACTUAL DATA\]/gi, '')
                      .replace(/\[CALCULATED METRIC(S)?\]/gi, '')
                      .replace(/\[.*?\]/g, '')
                      .trim();
                    let val = match[2]
                      .trim()
                      .replace(/^:/, '')
                      .replace(/\[FACTUAL DATA\]/gi, '')
                      .replace(/\[CALCULATED METRIC(S)?\]/gi, '')
                      .trim();

                    // Check if value is an upcoming agent notice
                    const isComingSoon =
                      val.includes('Coming Soon') ||
                      val.includes('in development') ||
                      val.includes('Scheduled for Module') ||
                      val.includes('Autonomous Agent');

                    // Check for URL
                    const urlMatch = val.match(/(https?:\/\/[^\s\)]+)/);

                    return (
                      <div key={lIdx} className="flex items-start gap-2 py-0.5">
                        <span className="text-emerald-400/80 mt-1 font-mono text-[10px]">▸</span>
                        <div className="flex-1">
                          <span className="font-semibold text-slate-200">{label}:</span>{' '}
                          {isComingSoon ? (
                            <div className="mt-1 p-2 rounded-lg bg-purple-950/25 border border-purple-500/30 text-purple-300 text-[11px] flex items-center gap-2">
                              <span>{val.replace(/\*/g, '')}</span>
                            </div>
                          ) : urlMatch ? (
                            <span className="text-slate-300">
                              {val.split(urlMatch[0])[0]}
                              <a
                                href={urlMatch[0]}
                                target="_blank"
                                rel="noreferrer"
                                className="text-cyan-400 underline hover:text-cyan-300 inline-flex items-center gap-0.5 ml-1"
                              >
                                {urlMatch[0]}
                                <ExternalLink className="w-2.5 h-2.5 inline" />
                              </a>
                              {val.split(urlMatch[0])[1]}
                            </span>
                          ) : (
                            <span className="text-slate-300">{val}</span>
                          )}
                        </div>
                      </div>
                    );
                  }
                }

                return (
                  <p key={lIdx} className="text-slate-400">
                    {lineTrim}
                  </p>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StructuredReportViewer;
