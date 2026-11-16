/**
 * AlertBanner.jsx
 * Reusable top-of-form alert for API-level error or info messages.
 */

import React from 'react';
import { AlertCircle, CheckCircle2, Info } from 'lucide-react';

/**
 * @param {{ message: string, variant?: 'error' | 'info' | 'success' }} props
 */
export default function AlertBanner({ message, variant = 'error' }) {
  if (!message) return null;

  const isError = variant === 'error';
  const isSuccess = variant === 'success';

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={[
        'flex items-start gap-3 rounded-xl border px-4 py-3 text-xs sm:text-sm font-medium backdrop-blur-md transition-all',
        isError
          ? 'border-rose-500/30 bg-rose-950/25 text-rose-300 shadow-sm shadow-rose-950/30'
          : isSuccess
          ? 'border-emerald-500/30 bg-emerald-950/25 text-emerald-300 shadow-sm shadow-emerald-950/30'
          : 'border-white/[0.1] bg-white/[0.04] text-zinc-300',
      ].join(' ')}
    >
      {isError ? (
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-400" aria-hidden="true" />
      ) : isSuccess ? (
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" aria-hidden="true" />
      ) : (
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" aria-hidden="true" />
      )}
      <span className="leading-relaxed">{message}</span>
    </div>
  );
}
