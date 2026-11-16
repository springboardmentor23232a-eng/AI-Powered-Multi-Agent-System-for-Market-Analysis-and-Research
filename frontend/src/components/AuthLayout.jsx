import React from 'react';

/**
 * FinCrew AuthLayout
 * Uses /fincrew-office-apple.png directly as the exact authentication page background.
 * Requirements:
 * - Uses the original image directly at public URL /fincrew-office-apple.png without alteration or quality degradation.
 * - Displays across the full left section of the login and registration pages.
 * - Preserves original aspect ratio and visual quality.
 * - No other background image behind it.
 * - Not placed inside a smaller rectangular card.
 * - Form built separately on the right side, ensuring character and desk are never covered.
 * - Fully responsive.
 */
export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen w-full relative flex flex-col lg:flex-row bg-[#204933] overflow-x-hidden selection:bg-[#9bd946] selection:text-[#111827]">
      {/* 
        Exact FinCrew Authentication Page Background:
        Original /fincrew-office-apple.png used directly at root public URL.
      */}
      <div className="fixed inset-0 z-0 pointer-events-none select-none overflow-hidden">
        <img
          src="/fincrew-office-apple.png"
          alt="FinCrew Office"
          className="w-full h-full object-cover object-left"
        />
      </div>

      {/* Mobile Top Illustration View (< lg) */}
      <div className="lg:hidden w-full h-56 sm:h-72 relative z-10 shrink-0 overflow-hidden">
        <img
          src="/fincrew-office-apple.png"
          alt="FinCrew Office"
          className="w-full h-full object-cover object-left"
        />
      </div>

      {/* Main Split Screen Container */}
      <div className="w-full min-h-screen flex flex-col lg:flex-row items-stretch justify-between relative z-10">
        
        {/* Left Section (approx 52% on desktop) - dedicated clear viewport for character & desk */}
        <div 
          className="hidden lg:flex lg:w-[50%] xl:w-[54%] 2xl:w-[56%] min-h-screen relative select-none"
          aria-hidden="true"
        />

        {/* Right Section (approx 48% on desktop) - separate white rounded authentication panel */}
        <div className="w-full lg:w-[50%] xl:w-[46%] 2xl:w-[44%] min-h-screen flex items-center justify-center lg:justify-end p-4 sm:p-6 lg:p-8 pr-4 sm:pr-8 lg:pr-10 xl:pr-16 relative z-10">
          <div className="w-full max-w-[470px] bg-white rounded-[32px] p-7 sm:p-9 md:p-10 shadow-[0_25px_60px_-15px_rgba(15,23,42,0.18)] border border-white/70 transition-all duration-300">
            {children}
          </div>
        </div>

      </div>
    </div>
  );
}
