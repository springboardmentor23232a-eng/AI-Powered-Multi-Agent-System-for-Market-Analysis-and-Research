// Allowed values. These must match backend/app/models/enums.py.

export const MARKETS = [
  { value: 'NSE', label: 'NSE (India)' },
  { value: 'BSE', label: 'BSE (India)' },
  { value: 'NYSE', label: 'NYSE (USA)' },
  { value: 'NASDAQ', label: 'Nasdaq (USA)' },
]

export const ANALYSIS_PERIODS = [
  { value: '1M', label: '1 month' },
  { value: '3M', label: '3 months' },
  { value: '6M', label: '6 months' },
  { value: '1Y', label: '1 year' },
  { value: '2Y', label: '2 years' },
  { value: '5Y', label: '5 years' },
]

// Same rule as the backend: letters, digits, '.', '-', '&'; 1-20 characters.
export const TICKER_PATTERN = /^[A-Z0-9][A-Z0-9.&-]{0,19}$/
