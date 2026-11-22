import React from 'react';

export default function FinCrewLogo({ size = 'md', className = '', variant = 'bars' }) {
  const isLarge = size === 'lg';
  const textSize = isLarge ? 'text-2xl' : 'text-xl sm:text-[22px]';

  if (variant === 'badge') {
    const badgeSize = isLarge ? 'w-10 h-10 rounded-xl' : 'w-8 h-8 rounded-[9px]';
    const iconSize = isLarge ? 'w-5 h-5' : 'w-4 h-4';
    return (
      <div className={`flex items-center gap-2 select-none ${className}`}>
        <div className={`${badgeSize} bg-[#C5F500] flex items-center justify-center shadow-xs shrink-0`}>
          <svg
            viewBox="0 0 20 20"
            fill="none"
            stroke="#111318"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={iconSize}
          >
            <path d="M3.5 13.5l4-4 3 3 6-6" />
          </svg>
        </div>
        <span className={`${textSize} font-extrabold tracking-tight text-[#111318]`}>
          FinCrew
        </span>
      </div>
    );
  }

  // Primary top nav brand logo: 3 ascending lime-green rounded bars + FinCrew wordmark
  return (
    <div className={`flex items-center gap-2.5 select-none ${className}`}>
      <div className="flex items-end gap-1 shrink-0 h-6.5 py-0.5">
        <span className="w-1.5 h-3 bg-[#C5F500] rounded-xs shadow-xs" />
        <span className="w-1.5 h-4.5 bg-[#C5F500] rounded-xs shadow-xs" />
        <span className="w-1.5 h-6 bg-[#C5F500] rounded-xs shadow-xs" />
      </div>
      <span className={`${textSize} font-black tracking-tight text-[#111318]`}>
        FinCrew
      </span>
    </div>
  );
}
