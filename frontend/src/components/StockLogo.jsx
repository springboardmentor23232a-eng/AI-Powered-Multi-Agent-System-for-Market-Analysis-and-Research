import React from 'react';

/**
 * Reusable StockLogo component providing authentic SVG brand logos
 * for AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA with a clean fallback.
 */
export default function StockLogo({ ticker = '', size = 'md', className = '' }) {
  const cleanTicker = (ticker || '').trim().toUpperCase();

  const sizeClasses = {
    xs: 'w-5 h-5 text-[10px]',
    sm: 'w-7 h-7 text-xs',
    md: 'w-9 h-9 text-xs',
    lg: 'w-11 h-11 text-sm',
    xl: 'w-14 h-14 text-base',
  }[size] || 'w-9 h-9 text-xs';

  const iconSizes = {
    xs: 'w-3.5 h-3.5',
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
    xl: 'w-8 h-8',
  }[size] || 'w-5 h-5';

  // Apple Inc.
  if (cleanTicker === 'AAPL') {
    return (
      <div
        className={`${sizeClasses} rounded-2xl bg-white border border-gray-200/80 shadow-xs flex items-center justify-center shrink-0 ${className}`}
        title="Apple Inc. (AAPL)"
      >
        <svg viewBox="0 0 24 24" className={`${iconSizes} fill-black`}>
          <path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701" />
        </svg>
      </div>
    );
  }

  // Microsoft Corporation
  if (cleanTicker === 'MSFT') {
    return (
      <div
        className={`${sizeClasses} rounded-2xl bg-white border border-gray-200/80 shadow-xs flex items-center justify-center shrink-0 ${className}`}
        title="Microsoft Corporation (MSFT)"
      >
        <svg viewBox="0 0 24 24" className={iconSizes}>
          <rect x="2" y="2" width="9.5" height="9.5" fill="#F25022" />
          <rect x="12.5" y="2" width="9.5" height="9.5" fill="#7FBA00" />
          <rect x="2" y="12.5" width="9.5" height="9.5" fill="#00A4EF" />
          <rect x="12.5" y="12.5" width="9.5" height="9.5" fill="#FFB900" />
        </svg>
      </div>
    );
  }

  // NVIDIA Corporation
  if (cleanTicker === 'NVDA') {
    return (
      <div
        className={`${sizeClasses} rounded-2xl bg-white border border-gray-200/80 shadow-xs flex items-center justify-center shrink-0 ${className}`}
        title="NVIDIA Corporation (NVDA)"
      >
        <svg viewBox="0 0 24 24" className={`${iconSizes} fill-[#76B900]`}>
          <path d="M8.948 8.798v-1.43a6.7 6.7 0 0 1 .424-.018c3.922-.124 6.493 3.374 6.493 3.374s-2.774 3.851-5.75 3.851c-.398 0-.787-.062-1.158-.185v-4.346c1.528.185 1.837.857 2.747 2.385l2.04-1.714s-1.492-1.952-4-1.952a6.016 6.016 0 0 0-.796.035m0-4.735v2.138l.424-.027c5.45-.185 9.01 4.47 9.01 4.47s-4.08 4.964-8.33 4.964c-.37 0-.733-.035-1.095-.097v1.325c.3.035.61.062.91.062 3.957 0 6.82-2.023 9.593-4.408.459.371 2.34 1.263 2.73 1.652-2.633 2.208-8.772 3.984-12.253 3.984-.335 0-.653-.018-.971-.053v1.864H24V4.063zm0 10.326v1.131c-3.657-.654-4.673-4.46-4.673-4.46s1.758-1.944 4.673-2.262v1.237H8.94c-1.528-.186-2.73 1.245-2.73 1.245s.68 2.412 2.739 3.11M2.456 10.9s2.164-3.197 6.5-3.533V6.201C4.153 6.59 0 10.653 0 10.653s2.35 6.802 8.948 7.42v-1.237c-4.84-.6-6.492-5.936-6.492-5.936z" />
        </svg>
      </div>
    );
  }

  // Alphabet / Google
  if (cleanTicker === 'GOOGL' || cleanTicker === 'GOOG') {
    return (
      <div
        className={`${sizeClasses} rounded-2xl bg-white border border-gray-200/80 shadow-xs flex items-center justify-center shrink-0 ${className}`}
        title="Alphabet Inc. (GOOGL)"
      >
        <svg viewBox="0 0 24 24" className={iconSizes}>
          <path
            fill="#4285F4"
            d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"
          />
          <path
            fill="#34A853"
            d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
          />
          <path
            fill="#FBBC05"
            d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.97 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
          />
          <path
            fill="#EA4335"
            d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
          />
        </svg>
      </div>
    );
  }

  // Amazon.com, Inc.
  if (cleanTicker === 'AMZN') {
    return (
      <div
        className={`${sizeClasses} rounded-2xl bg-white border border-gray-200/80 shadow-xs flex items-center justify-center shrink-0 ${className}`}
        title="Amazon.com, Inc. (AMZN)"
      >
        <svg viewBox="0 0 448 512" className={iconSizes}>
          {/* Bold 'a' letter in dark charcoal */}
          <path
            fill="#111318"
            d="M257.2 162.7c-48.7 1.8-169.5 15.5-169.5 117.5 0 109.5 138.3 114 183.5 43.2 6.5 10.2 35.4 37.5 45.3 46.8l56.8-56S341 288.9 341 261.4V114.3C341 89 316.5 32 228.7 32 140.7 32 94 87 94 136.3l73.5 6.8c16.3-49.5 54.2-49.5 54.2-49.5 40.7-.1 35.5 29.8 35.5 69.1zm0 86.8c0 80-84.2 68-84.2 17.2 0-47.2 50.5-56.7 84.2-57.8v40.6z"
          />
          {/* Signature Amazon Smile curved arrow in vibrant orange */}
          <path
            fill="#FF9900"
            d="M393.2 413c-7.7 10-70 67-174.5 67S34.2 408.5 9.7 379c-6.8-7.7 1-11.3 5.5-8.3C88.5 415.2 203 488.5 387.7 401c7.5-3.7 13.3 2 5.5 12zm39.8 2.2c-6.5 15.8-16 26.8-21.2 31-5.5 4.5-9.5 2.7-6.5-3.8s19.3-46.5 12.7-55c-6.5-8.3-37-4.3-48-3.2-10.8 1-13 2-14-.3-2.3-5.7 21.7-15.5 37.5-17.5 15.7-1.8 41-.8 46 5.7 3.7 5.1 0 27.1-6.5 43.1z"
          />
        </svg>
      </div>
    );
  }

  // Tesla, Inc.
  if (cleanTicker === 'TSLA') {
    return (
      <div
        className={`${sizeClasses} rounded-2xl bg-white border border-gray-200/80 shadow-xs flex items-center justify-center shrink-0 ${className}`}
        title="Tesla, Inc. (TSLA)"
      >
        <svg viewBox="0 0 24 24" className={`${iconSizes} fill-[#E82127]`}>
          <path d="M12 5.362l2.475-3.026s4.245.09 8.471 2.054c-1.082 1.636-3.231 2.438-3.231 2.438-.146-1.439-1.154-1.79-4.354-1.79L12 24 8.619 5.034c-3.18 0-4.188.354-4.335 1.792 0 0-2.146-.795-3.229-2.43C5.28 2.431 9.525 2.34 9.525 2.34L12 5.362l-.004.002H12v-.002zm0-3.899c3.415-.03 7.326.528 11.328 2.28.535-.968.672-1.395.672-1.395C19.625.612 15.528.015 12 0 8.472.015 4.375.61 0 2.349c0 0 .195.525.672 1.396C4.674 1.989 8.585 1.435 12 1.46v.003z" />
        </svg>
      </div>
    );
  }

  // Clean Fallback for any other ticker
  const displayLetters = cleanTicker.slice(0, 3) || 'EQ';
  return (
    <div
      className={`${sizeClasses} rounded-2xl bg-gradient-to-br from-[#17191F] to-[#282B33] text-[#C5F500] font-black tracking-tight border border-[#282B33] shadow-xs flex items-center justify-center shrink-0 select-none ${className}`}
      title={cleanTicker}
    >
      <span>{displayLetters}</span>
    </div>
  );
}
