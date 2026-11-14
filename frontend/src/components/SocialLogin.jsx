import React from 'react';
import { authService } from '../services/api';

export const SocialLogin = () => {
  const handleGoogleLogin = () => {
    window.location.href = authService.getGoogleAuthUrl();
  };

  const handleAppleLogin = () => {
    window.location.href = authService.getAppleAuthUrl();
  };

  return (
    <div className="w-full mt-5">
      {/* Divider */}
      <div className="relative flex items-center justify-center my-4">
        <div className="w-full border-t border-[#1e293b]"></div>
        <span className="absolute bg-[#0b0f15] px-3 text-[11px] font-semibold text-slate-400 tracking-wider uppercase">
          OR CONTINUE WITH
        </span>
      </div>

      {/* Side-by-side social buttons */}
      <div className="grid grid-cols-2 gap-3 mt-4">
        {/* Google Button */}
        <button
          type="button"
          onClick={handleGoogleLogin}
          className="flex items-center justify-center gap-2.5 py-2.5 px-3 rounded-lg bg-[#0e141e] hover:bg-[#131b28] border border-[#1e293b] hover:border-slate-600 transition-all text-xs sm:text-sm font-medium text-slate-200 shadow-sm"
        >
          {/* Multicolor Google G SVG */}
          <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
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
              d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.98 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
            />
            <path
              fill="#EA4335"
              d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
            />
          </svg>
          <span>Continue with Google</span>
        </button>

        {/* Apple Button */}
        <button
          type="button"
          onClick={handleAppleLogin}
          className="flex items-center justify-center gap-2.5 py-2.5 px-3 rounded-lg bg-[#0e141e] hover:bg-[#131b28] border border-[#1e293b] hover:border-slate-600 transition-all text-xs sm:text-sm font-medium text-slate-200 shadow-sm"
        >
          {/* Apple White Logo SVG */}
          <svg className="w-4 h-4 fill-current text-white shrink-0" viewBox="0 0 170 170">
            <path d="M150.37 130.25c-2.45 5.66-5.35 10.87-8.71 15.66-4.58 6.53-8.33 11.05-11.22 13.56-4.48 4.12-9.28 6.23-14.42 6.35-3.69 0-8.14-1.05-13.32-3.18-5.19-2.12-9.97-3.17-14.34-3.17-4.58 0-9.49 1.05-14.75 3.17-5.26 2.13-9.5 3.24-12.74 3.35-4.35.13-9.16-1.9-14.42-6.08-3.69-3.08-7.7-7.98-12.02-14.7-6.08-9.52-10.88-20.08-14.42-31.67-3.54-11.59-5.31-22.39-5.31-32.4 0-14.42 3.63-26.06 10.88-34.93 7.26-8.87 16.48-13.38 27.67-13.53 4.8 0 10.15 1.25 16.05 3.75 5.91 2.5 9.77 3.75 11.6 3.75 1.52 0 5.61-1.33 12.27-4 6.66-2.67 12.35-3.83 17.06-3.48 12.87.65 23.09 5.39 30.64 14.21-11.36 6.86-16.92 16.46-16.69 28.79.23 9.8 4.07 18.06 11.52 24.78 7.45 6.72 16.27 10.51 26.47 11.36-2.39 7.42-5.46 14.72-9.21 21.91zM119.22 31.84c0-7.39 2.65-14.24 7.96-20.55 5.3-6.31 11.89-10.4 19.75-12.29.22 1.3.33 2.45.33 3.44 0 7.39-2.73 14.29-8.19 20.7-5.46 6.41-12.18 10.36-20.15 11.85-.43-1.08-.7-2.13-.7-3.15z"/>
          </svg>
          <span>Continue with Apple</span>
        </button>
      </div>
    </div>
  );
};

export default SocialLogin;

