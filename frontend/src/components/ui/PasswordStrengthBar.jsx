/**
 * PasswordStrengthBar.jsx
 * Visual password-strength indicator (Weak / Fair / Strong / Very Strong).
 * Purely presentational – driven by the password string.
 */

import React, { useMemo } from 'react';

/** Returns a 0–4 score based on heuristics */
function calcScore(password) {
  if (!password) return 0;
  let score = 0;
  if (password.length >= 8)  score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  // Cap at 4
  return Math.min(score, 4);
}

const LEVELS = [
  { label: 'Too short',   color: 'bg-white/[0.1]' },
  { label: 'Weak',        color: 'bg-rose-600'      },
  { label: 'Fair',        color: 'bg-amber-500'    },
  { label: 'Strong',      color: 'bg-emerald-500'  },
  { label: 'Very strong', color: 'bg-emerald-400'  },
];

/**
 * @param {{ password: string }} props
 */
export default function PasswordStrengthBar({ password }) {
  const score = useMemo(() => calcScore(password), [password]);
  const level = LEVELS[score];

  if (!password) return null;

  return (
    <div className="mt-1.5 space-y-1.5" aria-live="polite" aria-label="Password strength">
      {/* Bar segments */}
      <div className="flex gap-1.5">
        {[1, 2, 3, 4].map((seg) => (
          <div
            key={seg}
            className={[
              'h-1 flex-1 rounded-full transition-all duration-300',
              score >= seg ? level.color : 'bg-white/[0.08]',
            ].join(' ')}
          />
        ))}
      </div>

      {/* Label */}
      <p
        className={[
          'text-xs font-medium transition-colors duration-300',
          score <= 1 ? 'text-rose-400'     : '',
          score === 2 ? 'text-amber-400'   : '',
          score === 3 ? 'text-emerald-400' : '',
          score === 4 ? 'text-emerald-300' : '',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {level.label}
      </p>
    </div>
  );
}
