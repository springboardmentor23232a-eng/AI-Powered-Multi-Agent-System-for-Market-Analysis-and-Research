import { Link } from 'react-router-dom'

// Three candlesticks: the product's mark.
export default function Mark({ light = false }) {
  return (
    <Link to="/" className="inline-flex items-center gap-2.5 whitespace-nowrap" aria-label="ORIONNEX home">
      <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true">
        <g stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M5 4v18M13 2v20M21 7v15" />
        </g>
        <rect x="2.5" y="9" width="5" height="9" rx="1" fill={light ? '#FFE14D' : '#2430D6'} />
        <rect x="10.5" y="6" width="5" height="11" rx="1" fill="currentColor" />
        <rect x="18.5" y="11" width="5" height="8" rx="1" fill={light ? '#FFE14D' : '#2430D6'} />
      </svg>
      <span className="text-[17px] font-extrabold tracking-[0.12em]">ORIONNEX</span>
    </Link>
  )
}
