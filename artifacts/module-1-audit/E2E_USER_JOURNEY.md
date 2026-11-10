# Module 1 — End-to-End User Journey Verification Guide

Follow this guided verification script to manually inspect and validate every Module 1 requirement in the live application.

**Live URL:** [**http://localhost:5173**](http://localhost:5173)

---

## Journey 1: New User Registration & Form Validation

1. Open your browser and navigate to [http://localhost:5173/login](http://localhost:5173/login).
2. Click **"New here? Create an account"**.
3. **Verify:** The form smoothly reveals four required fields:
   - Full Name
   - Email
   - Password (minimum 8 characters)
   - Confirm Password
4. **Test Mismatched Password Validation:**
   - Enter Full Name: `Jane Doe`
   - Enter Email: `jane.doe@veritas.test`
   - Enter Password: `SecurePassword123!`
   - Enter Confirm Password: `WrongPassword123!`
   - Click **"Create account"**.
   - **Verify:** A red error alert appears: *"Passwords do not match"*. No network request is submitted.
5. **Test Successful Registration:**
   - Change Confirm Password to `SecurePassword123!`.
   - Click **"Create account"**.
   - **Verify:** The account is created in PostgreSQL with an Argon2id password hash, a JWT token is issued, and you are automatically redirected into the authenticated dashboard at `/`.

---

## Journey 2: Login, Error Handling & Session Security

1. Click **"Sign out"** in the top right navigation bar.
2. **Verify:** You are redirected to `/login` and `localStorage.getItem("veritas_token")` is cleared.
3. **Test Invalid Login:**
   - Enter Email: `nonexistent@veritas.test`
   - Enter Password: `InvalidPassword123!`
   - Click **"Sign in"**.
   - **Verify:** A red error alert appears: *"Invalid email or password"*.
4. **Test Valid Login:**
   - Enter Email: `analyst.test@veritas.demo`
   - Enter Password: `Password123!`
   - Click **"Sign in"**.
   - **Verify:** Authentication succeeds and you are redirected to the main dashboard.

---

## Journey 3: Stock Search & Watchlist Management

1. In the **"Research a stock"** card, click on the search input.
2. Type `Infosys` or `INFY`.
3. **Verify:** The search list displays matching results:
   - `INFY` `Infosys Limited`
   - Action buttons: `Watch` and `Research`
4. Click the **"Watch"** button.
5. **Verify:**
   - The button label updates to **"Unwatch"**.
   - INFY immediately appears in the right sidebar **"Watchlist"** panel showing `INFY` `Infosys Limited` with **"Remove"** and **"Research"** action buttons.
   - The record is persisted in PostgreSQL table `saved_stocks`.

---

## Journey 4: User Preferences (Market & Analysis Period)

1. Locate the **"Preferences"** card in the right sidebar.
2. **Inspect Market Selection:**
   - Open the Market dropdown.
   - **Verify:** Both supported internship markets are present:
     - `NSE (National Stock Exchange)`
     - `BSE (Bombay Stock Exchange)`
   - Select **BSE**.
   - **Verify:** A green **"Saved"** badge appears in the card header confirming PostgreSQL persistence.
3. **Inspect Analysis Period Selection:**
   - Open the Default analysis period dropdown.
   - **Verify:** All 5 supported periods are clearly labeled:
     - `1 Month (1mo)`
     - `3 Months (3mo)`
     - `6 Months (6mo)`
     - `1 Year (1y)`
     - `5 Years (5y)`
   - Select **1 Year (1y)**.
   - **Verify:** The **"Saved"** indicator appears again.

---

## Journey 5: Research History & Completed Report Viewing

1. Inspect the **"Research history"** table in the main panel.
2. **Verify the metadata columns:**
   - **Stock:** Shows `INFY` link and company name `Infosys Limited`.
   - **Market:** Shows `NSE`.
   - **Period:** Shows `1y`.
   - **Status:** Shows a green **Completed** status pill badge.
   - **Date:** Shows the formatted execution date.
3. Click the blue **"INFY"** link in the history table.
4. **Verify the Completed Research Report:**
   - The page navigates to `/research/:task_id`.
   - The **Summary** tab loads the full Markdown research report with market dynamics, financial metrics, and audit verdict.
   - Click the **"Claims"** tab in the navigation bar.
   - **Verify:** The typed claims table lists all 27 verified claims categorized by type (`FACT`, `CALC`, `AI`) with evidence quotes from stored source documents.

---

## Journey 6: Watchlist Removal & Protected Route Enforcement

1. Click the **"Veritas Equity Research"** brand title in the header to return to the dashboard.
2. In the sidebar **"Watchlist"** panel, click the red **"Remove"** button next to INFY.
3. **Verify:** INFY is removed from the watchlist and the panel transitions to the empty state: *"Nothing saved yet."*
4. Click **"Sign out"** in the top navigation bar.
5. **Verify:** You are redirected to `/login`.
6. Now attempt to directly type and navigate to `http://localhost:5173/` in your browser address bar.
7. **Verify:** The `<Protected>` route guard intercepts the unauthenticated access and immediately redirects you back to `/login`.

