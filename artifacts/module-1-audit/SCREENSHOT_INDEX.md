# Module 1 — Screenshot Index & Screen Inventory

This index details each screen in Module 1, its corresponding Student Implementation Guide requirement, its UI components, and backend integration.

---

## 1. Captured Screenshots

| File | Size | Requirement | Description |
|---|---|---|---|
| `artifacts/module-1-audit/screenshots/01_registration_page_empty.png` | 24,057 bytes | A. User Registration | Clean registration form with Full Name, Email, Password, and Confirm Password fields. Captured via real Electron/Chromium renderer. |

---

## 2. Complete Screen Inventory & Verification Matrix

Below is the structured breakdown of all 23 demonstration screens available for live inspection at **http://localhost:5173**:

### 1. User Registration Screen (`01_registration_page_empty`)
- **Route:** `/login` (mode = `register`)
- **Requirement:** A. User Registration (Form fields)
- **Key Elements:**
  - "Full Name" input (`type="text"`, required)
  - "Email" input (`type="email"`, required)
  - "Password" input (`type="password"`, `minLength=8`, required)
  - "Confirm Password" input (`type="password"`, `minLength=8`, required)
  - "Create account" submit button
  - Mode toggle: "Have an account? Sign in"

### 2. Registration Form Validation Error (`02_registration_validation_error`)
- **Requirement:** A. User Registration (Password confirmation validation)
- **Key Elements:**
  - Alert banner: `<p role="alert" className="text-sm text-red-700">Passwords do not match</p>`
  - Prevents network submission when confirmation does not match.

### 3. Registration Form Filled (`03_registration_form_filled`)
- **Requirement:** A. User Registration (Frontend form validation)
- **Key Elements:**
  - All four fields populated with valid, matching credentials.
  - Active submission state.

### 4. User Login Screen — Empty (`04_login_page_empty`)
- **Route:** `/login` (mode = `login`)
- **Requirement:** B. User Login (Input fields)
- **Key Elements:**
  - Clean form with Email and Password inputs.
  - "Sign in" submit button.
  - Mode toggle: "New here? Create an account".

### 5. Login Invalid Credentials Error (`05_login_invalid_credentials`)
- **Requirement:** B. User Login (Invalid credentials handling)
- **Key Elements:**
  - Submitting un-registered email or incorrect password.
  - Displays alert banner: `<p role="alert" className="text-sm text-red-700">Invalid email or password</p>`.
  - Generic message prevents account enumeration.

### 6. Login Valid Credentials (`06_login_valid_credentials`)
- **Requirement:** B. User Login (Password verification)
- **Key Elements:**
  - Valid registered email and password entered.

### 7. Main Authenticated Dashboard (`07_authenticated_dashboard_empty`)
- **Route:** `/` (Protected Route)
- **Requirement:** C. JWT Authentication & Workspace Dashboard
- **Key Elements:**
  - Header: Veritas brand link and "Sign out" button.
  - Stock search section: "Research a stock" input field and past-date replay expander.
  - Research history section: user-specific history table.
  - Sidebar: Watchlist panel and Preferences panel.

### 8. Stock Search Functionality (`08_stock_search_infy`)
- **Requirement:** E. Saved Stocks (Search by company name & ticker)
- **Key Elements:**
  - Debounced autocomplete search against the 20-ticker NSE universe.
  - Displays matching ticker (`INFY`) and company name (`Infosys Limited`).
  - Action buttons: "Watch" (add to watchlist) and "Research" (run workflow).

### 9. Watchlist with Saved Stocks (`09_watchlist_with_infy`)
- **Requirement:** E. Saved Stocks (Add to Watchlist & persistence)
- **Key Elements:**
  - Sidebar watchlist panel displays saved stocks with company name.
  - Action buttons: "Remove" (delete from watchlist) and "Research".
  - Persisted in PostgreSQL `saved_stocks` table.

### 10. User Preferences Panel (`10_preferences_initial`)
- **Requirement:** F. User Preferences (Existing preferences loaded)
- **Key Elements:**
  - Loads saved user preferences from PostgreSQL `users.preferences`.
  - Displays Market selection and Default analysis period.

### 11. Market Preference Dropdown (`11_market_preference_dropdown_open`)
- **Requirement:** F. User Preferences (Supported internship markets)
- **Key Elements:**
  - Select options:
    - `NSE (National Stock Exchange)`
    - `BSE (Bombay Stock Exchange)`

### 12. Preferences with BSE Selected (`12_preferences_bse_selected`)
- **Requirement:** F. User Preferences (Preference modification & persistence)
- **Key Elements:**
  - Changing market immediately triggers `PUT /workspace/preferences`.
  - Displays emerald "Saved" indicator pill upon success.

### 13. Analysis Period Dropdown (`13_analysis_period_dropdown_open`)
- **Requirement:** F. User Preferences (Analysis period selection)
- **Key Elements:**
  - Select options covering all 5 approved periods:
    - `1 Month (1mo)`
    - `3 Months (3mo)`
    - `6 Months (6mo)`
    - `1 Year (1y)`
    - `5 Years (5y)`

### 14. Preferences Saved with 1 Year (`14_preferences_saved_bse_1y`)
- **Requirement:** F. User Preferences (Persistence in PostgreSQL)
- **Key Elements:**
  - Both BSE and 1y stored in PostgreSQL.
  - Emerald "Saved" status pill confirms persistence.

### 15. Research Workflow Initiated (`15_research_task_initiated`)
- **Route:** `/research/:id`
- **Requirement:** D. Research History (Research status display)
- **Key Elements:**
  - Polling task state (`pending` / `processing`).
  - Status pill badge displays current execution phase.

### 16. Research History Table (`16_research_history_table`)
- **Requirement:** D. Research History (Record metadata & isolation)
- **Key Elements:**
  - Displays all user research tasks.
  - Columns: Stock link + Company name (`Infosys Limited`), Market (`NSE`), Period (`1y`), Status pill (`Completed`), and Date.

### 17. Completed Research Report — Summary (`17_completed_research_report_summary`)
- **Requirement:** D. Research History (Ability to open completed research reports)
- **Key Elements:**
  - Tab navigation: Summary, Charts, Fundamentals, News, Risk, Claims.
  - Rendered Markdown report with executive summary, market dynamics, and audit verdict.
  - Download report button.

### 18. Completed Research Report — Claims & Evidence (`18_completed_research_report_claims`)
- **Requirement:** D. Research History & Claim-level evidence audit
- **Key Elements:**
  - Claims table listing typed claims: `FACT`, `CALC`, `AI`.
  - Verified badges and quote excerpts from stored source documents.

### 19. Watchlist Removal Action (`19_watchlist_removed`)
- **Requirement:** E. Saved Stocks (Remove saved stocks & empty state)
- **Key Elements:**
  - Clicking "Remove" calls `DELETE /workspace/watchlist/:ticker`.
  - Watchlist updates to empty state: "Nothing saved yet."

### 20. Logout Functionality (`20_logout_successful`)
- **Requirement:** B. User Login (Logout & session invalidation)
- **Key Elements:**
  - Clicking "Sign out" removes `veritas_token` from `localStorage`.
  - Immediate client-side redirection to `/login`.

### 21. Protected Route Enforcement (`21_protected_route_redirect`)
- **Requirement:** C. JWT Security (Protected API endpoints & route guards)
- **Key Elements:**
  - Navigating to `/` without token is trapped by `<Protected>` guard in `App.tsx`.
  - Automatically redirects to `/login`.

### 22. Mobile Responsive Layout (`22_mobile_dashboard_view`)
- **Viewport:** 390×844 (iPhone 14)
- **Requirement:** Visual Quality (Mobile responsive layout)
- **Key Elements:**
  - Single-column stacked grid (`lg:grid-cols-3` collapses).
  - Horizontally scrollable research history table.
  - Full-width touch-friendly form inputs and buttons.

### 23. Tablet Responsive Layout (`23_tablet_dashboard_view`)
- **Viewport:** 768×1024 (iPad)
- **Requirement:** Visual Quality (Tablet layout & typography)
- **Key Elements:**
  - Intermediate layout preserving margins and readability.

