import React from 'react';
import { ArrowLeft, Plus, Sparkles } from 'lucide-react';

export default function PageHeader({
  title,
  subtitle,
  onBack,
  actionLabel = 'New Research',
  onAction,
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 select-none">
      {/* Title & Back Arrow */}
      <div className="flex items-center gap-3 sm:gap-4">
        {onBack && (
          <button
            onClick={onBack}
            className="w-10 h-10 rounded-full bg-white border border-[#DCE7F6] shadow-xs flex items-center justify-center text-[#111318] hover:bg-gray-50 active:scale-95 transition cursor-pointer shrink-0"
            title="Go back"
            aria-label="Go back"
          >
            <ArrowLeft className="w-4.5 h-4.5 text-[#111318]" />
          </button>
        )}

        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-[#111318] tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs sm:text-sm text-[#64748B] font-medium mt-0.5">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      {/* Right Controls: Primary Lime CTA Button */}
      <div className="flex items-center gap-3 shrink-0">
        {onAction && (
          <button
            onClick={onAction}
            className="h-10 px-5 rounded-full bg-[#C5F500] hover:bg-[#b3e000] active:scale-98 text-[#111318] font-black text-xs sm:text-sm flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4 stroke-[3]" />
            <span>{actionLabel}</span>
          </button>
        )}
      </div>
    </div>
  );
}
