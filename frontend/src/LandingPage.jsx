import { useState } from "react";
import "./landing.css";

const ROADMAP_MODULES = [
  {
    number: "MODULE 01",
    title: "Authentication & Research Workspace",
    status: "Completed / Live",
    statusType: "live",
    description:
      "User authentication with Argon2 and signed JWT cookies, Google OAuth, personal watchlists, default market preferences, research task queues, Yahoo Finance market data retrieval (OHLCV, profile, financial statements), and PostgreSQL persistence."
  },
  {
    number: "MODULE 02",
    title: "Quantitative & Technical Analysis",
    status: "In Progress",
    statusType: "progress",
    description:
      "Automated financial ratio computation (EV/EBITDA, P/E, P/FCF), DuPont ROE decomposition, exponential moving averages (20/50/200 EMA), RSI momentum oscillators, and volatility breakout indicators."
  },
  {
    number: "MODULE 03",
    title: "Sentiment & Catalyst Analysis",
    status: "Upcoming",
    statusType: "upcoming",
    description:
      "Regulatory disclosure parsing (SEC 10-K/10-Q, SEBI/BSE filings), earnings call transcript analysis, qualitative sentiment scoring, and macro catalyst tagging."
  },
  {
    number: "MODULE 04",
    title: "Multi-Agent Research Synthesis",
    status: "Upcoming",
    statusType: "upcoming",
    description:
      "LangGraph multi-agent coordination consolidating quantitative models, sentiment signals, and technical setups into structured, publication-ready investment dossiers and reports."
  }
];

const CORE_FEATURES = [
  {
    icon: "🌐",
    title: "Multi-Market Stock Research",
    description:
      "Search companies by ticker symbol or corporate name across Indian and US exchanges. Automatic symbol normalization routes NSE, BSE, NASDAQ, and NYSE queries seamlessly.",
    tags: ["NSE (.NS)", "BSE (.BO)", "NASDAQ", "NYSE"]
  },
  {
    icon: "📈",
    title: "Historical OHLCV Analysis",
    description:
      "Retrieve structured Open, High, Low, Close, and Volume series across customizable time horizons (1mo, 3mo, 6mo, 1y, 5y, max) and intervals (1d, 1wk, 1mo).",
    tags: ["Daily / Weekly Bars", "Multi-Timeframe", "Volume Series"]
  },
  {
    icon: "📊",
    title: "Interactive Financial Charts",
    description:
      "Inspect historical price action and trading volume in an interactive SVG chart within the workspace, with one-click CSV export for external spreadsheets or Python pipelines.",
    tags: ["SVG Visualization", "CSV Export", "Volume Histograms"]
  },
  {
    icon: "📑",
    title: "Company Financial Statements",
    description:
      "Examine standardized Income Statements, Balance Sheets, and Cash Flow Statements alongside fundamental valuation metrics extracted from published company filings.",
    tags: ["Income Statement", "Balance Sheet", "Cash Flow", "Key Ratios"]
  },
  {
    icon: "🗂️",
    title: "Watchlists & Personal Workspace",
    description:
      "Save tracked stocks to a personal watchlist, configure preferred default exchanges and analysis periods, and maintain a persistent history of research tasks.",
    tags: ["Custom Watchlists", "Preferences", "Task History"]
  },
  {
    icon: "🛡️",
    title: "Data-Source Attribution & Timestamps",
    description:
      "Every collected price bar, company profile, and financial statement records its authoritative data source and exact ISO-8601 UTC retrieval timestamp for transparency.",
    tags: ["Yahoo Finance via yfinance", "ISO-8601 UTC", "Verifiable History"]
  }
];

const SUPPORTED_MARKETS = [
  {
    flag: "🇮🇳",
    badge: "NSE INDIA",
    title: "National Stock Exchange",
    description:
      "India's primary electronic equity exchange, home to the benchmark NIFTY 50 index and liquid large-to-mid-cap equities.",
    format: ".NS suffix (e.g., TCS.NS, INFY.NS)",
    currency: "Indian Rupee (INR ₹)",
    hours: "09:15 - 15:30 IST"
  },
  {
    flag: "🇮🇳",
    badge: "BSE INDIA",
    title: "Bombay Stock Exchange",
    description:
      "Asia's oldest stock exchange, hosting the SENSEX 30 benchmark and over 5,000 listed Indian corporations.",
    format: ".BO suffix (e.g., 500325.BO)",
    currency: "Indian Rupee (INR ₹)",
    hours: "09:15 - 15:30 IST"
  },
  {
    flag: "🇺🇸",
    badge: "NASDAQ",
    title: "NASDAQ Stock Market",
    description:
      "The global benchmark market for technology, accelerated computing, cloud infrastructure, and growth companies.",
    format: "Native ticker (e.g., AAPL, NVDA, MSFT)",
    currency: "US Dollar (USD $)",
    hours: "09:30 - 16:00 EST"
  },
  {
    flag: "🇺🇸",
    badge: "NYSE",
    title: "New York Stock Exchange",
    description:
      "The world's largest equity exchange by market capitalization, listing global diversified conglomerates and blue chips.",
    format: "Native ticker (e.g., JNJ, BRK-B)",
    currency: "US Dollar (USD $)",
    hours: "09:30 - 16:00 EST"
  }
];

const SECURITY_POINTS = [
  {
    title: "Secure Authentication",
    description:
      "Passwords are encrypted with state-of-the-art Argon2id password hashing. Sessions are maintained via signed JSON Web Tokens (JWT) stored in HttpOnly, SameSite cookies with CSRF token verification."
  },
  {
    title: "User-Specific Research Records",
    description:
      "All watchlists, user preferences, and research requests enforce strict multi-tenant isolation in PostgreSQL. Server-side queries derive ownership directly from verified JWT tokens, never from client-supplied IDs."
  },
  {
    title: "Data-Source Attribution",
    description:
      "All market price series, corporate profiles, and financial statements explicitly record their data origin (Yahoo Finance via yfinance). The application does not generate or synthesize financial numbers."
  },
  {
    title: "Retrieval Timestamps",
    description:
      "Each market snapshot is tagged with an exact ISO-8601 UTC timestamp recording precisely when the data was retrieved, enabling users to evaluate the freshness and timing of their research records."
  },
  {
    title: "Transparent Handling of Missing Data",
    description:
      "When specific financial line items, valuation multiples, or historical price bars are not published by the upstream provider, the application marks them as unavailable rather than interpolating or fabricating values."
  }
];

const TECH_STACK = [
  {
    icon: "⚡",
    name: "FastAPI",
    category: "Backend Framework",
    description: "High-throughput asynchronous Python ASGI framework with Pydantic v2 validation schemas and automatic OpenAPI documentation."
  },
  {
    icon: "🐍",
    name: "Python 3.11+",
    category: "Runtime Environment",
    description: "Robust application runtime executing data retrieval, validation schemas, and password security algorithms."
  },
  {
    icon: "⚛️",
    name: "React 18 & Vite",
    category: "Frontend Architecture",
    description: "Component-based single-page application with responsive UI state management, sub-second HMR, and dynamic SVG visualization."
  },
  {
    icon: "🐘",
    name: "PostgreSQL & SQLAlchemy 2",
    category: "Database & ORM",
    description: "ACID-compliant relational persistence with foreign-key constraints and multi-tenant schema isolation, compatible with Neon serverless."
  },
  {
    icon: "📈",
    name: "yfinance",
    category: "Market Data Integration",
    description: "Direct Yahoo Finance provider integration for multi-market ticker search, historical OHLCV data, company profiles, and financial statements."
  },
  {
    icon: "🔐",
    name: "JWT & Argon2",
    category: "Security & Sessions",
    description: "Argon2 password hashing via pwdlib, signed JWT access tokens stored in HttpOnly cookies, and CSRF token verification."
  }
];

const FAQS = [
  {
    q: "Is an API key required?",
    a: "No paid API key or subscription is required to use this workspace. The platform uses the direct Yahoo Finance integration (yfinance) for company search, historical OHLCV data, company profiles, and financial statements across all supported exchanges."
  },
  {
    q: "Which exchanges are supported?",
    a: "Module 1 supports selected stock markets including Indian exchanges (NSE, BSE) and US exchanges (NASDAQ, NYSE), with automatic ticker normalization (such as appending .NS for NSE or .BO for BSE)."
  },
  {
    q: "How fresh is the market data?",
    a: "Market data reflects information published by Yahoo Finance according to standard exchange publishing schedules and historical availability. The system stamps every retrieved record with an exact ISO-8601 UTC timestamp so you always know when the data was retrieved."
  },
  {
    q: "How is user data stored?",
    a: "User accounts, hashed credentials, custom watchlists, default market preferences, and research task histories are persisted in a relational PostgreSQL database with foreign-key integrity and multi-tenant isolation. Neon serverless PostgreSQL is fully supported."
  },
  {
    q: "Can users save research?",
    a: "Yes. Authenticated users can save companies to their personal watchlist, record snapshots of collected market data (OHLCV, profiles, financial statements), and track research requests in their task history."
  },
  {
    q: "Which modules are currently available?",
    a: "Module 1 (Authentication, Personal Research Workspace, and Market Data Retrieval) is fully implemented and live. Subsequent modules for quantitative and technical agents (Module 2), sentiment analysis (Module 3), and multi-agent synthesis (Module 4) are part of the active development roadmap."
  }
];

export function LandingPage({ onNavigateAuth, onOpenWorkspace, user }) {
  const [openFaqIndex, setOpenFaqIndex] = useState(0);
  const [modalType, setModalType] = useState(null); // 'privacy' | 'terms' | 'about' | 'contact'

  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="landing-container">
      <div className="landing-ambient-bg" />

      {/* Top Navigation Bar */}
      <header className="landing-nav">
        <div
          className="landing-nav-brand"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        >
          <div className="brand-icon">S</div>
          <div className="landing-brand-text">
            <strong>Stock Research Analyst</strong>
            <span>Module 1 · Research Workspace</span>
          </div>
        </div>

        <nav className="landing-nav-links">
          <button className="landing-nav-link" onClick={() => scrollToSection("features")}>
            Features
          </button>
          <button className="landing-nav-link" onClick={() => scrollToSection("markets")}>
            Markets
          </button>
          <button className="landing-nav-link" onClick={() => scrollToSection("roadmap")}>
            Roadmap
          </button>
          <button className="landing-nav-link" onClick={() => scrollToSection("security")}>
            Security
          </button>
          <button className="landing-nav-link" onClick={() => scrollToSection("tech")}>
            Tech Stack
          </button>
          <button className="landing-nav-link" onClick={() => scrollToSection("faq")}>
            FAQ
          </button>
        </nav>

        <div className="landing-nav-actions">
          {user ? (
            <button className="btn-nav-primary" onClick={onOpenWorkspace}>
              Workspace ({user.full_name.split(" ")[0]}) <span>→</span>
            </button>
          ) : (
            <>
              <button className="btn-nav-outline" onClick={() => onNavigateAuth("login")}>
                Sign In
              </button>
              <button className="btn-nav-primary" onClick={() => onNavigateAuth("register")}>
                Get Started <span>→</span>
              </button>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-pill">
          <span className="hero-pill-pulse" />
          <span>MODULE 01 LIVE · AUTHENTICATION & RESEARCH WORKSPACE</span>
        </div>

        <h1 className="hero-title">
          Multi-Market Equity Research Workspace.<br />
          <span className="accent-mint">Structured for Deep Financial Analysis.</span>
        </h1>

        <p className="hero-subtitle">
          A dedicated research environment integrating Yahoo Finance market data across Indian (<strong>NSE</strong>, <strong>BSE</strong>) and US (<strong>NASDAQ</strong>, <strong>NYSE</strong>) exchanges. Manage watchlists, inspect historical OHLCV data, examine company financial statements, and track research tasks with transparent provenance.
        </p>

        <div className="hero-cta-group">
          {user ? (
            <button className="btn-hero-primary" onClick={onOpenWorkspace}>
              Enter Research Workspace <span>→</span>
            </button>
          ) : (
            <>
              <button className="btn-hero-primary" onClick={() => onNavigateAuth("register")}>
                Get Started Free <span>→</span>
              </button>
              <button className="btn-hero-secondary" onClick={() => onNavigateAuth("login")}>
                Sign In to Account
              </button>
            </>
          )}
        </div>

        <div className="hero-features-bar">
          <span><b className="check">✓</b> Yahoo Finance market-data integration</span>
          <span><b className="check">✓</b> NSE · BSE · NASDAQ · NYSE support</span>
          <span><b className="check">✓</b> Historical OHLCV & CSV export</span>
          <span><b className="check">✓</b> Company financial statements</span>
          <span><b className="check">✓</b> PostgreSQL multi-tenant isolation</span>
        </div>
      </section>

      {/* Core Features Grid */}
      <section className="landing-section" id="features">
        <div className="section-intro">
          <span className="section-kicker">CORE CAPABILITIES</span>
          <h2 className="section-title">Built for Systematic Stock Research</h2>
          <p className="section-desc">
            Module 1 provides a clean, authenticated research foundation connecting to authoritative market feeds with zero artificial data.
          </p>
        </div>

        <div className="features-grid">
          {CORE_FEATURES.map((feat, idx) => (
            <div className="feature-card" key={idx}>
              <div className="feature-icon-wrap">{feat.icon}</div>
              <h3>{feat.title}</h3>
              <p>{feat.description}</p>
              <div className="feature-card-tags">
                {feat.tags.map((tag, tIdx) => (
                  <span className="feature-tag" key={tIdx}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Supported Markets Section */}
      <section className="landing-section alt-bg" id="markets">
        <div className="section-intro">
          <span className="section-kicker">MARKET COVERAGE</span>
          <h2 className="section-title">Four Supported Stock Exchanges</h2>
          <p className="section-desc">
            Direct access to major Indian and United States equities with automatic ticker normalization and local currency denomination.
          </p>
        </div>

        <div className="markets-grid">
          {SUPPORTED_MARKETS.map((mkt, idx) => (
            <div className="market-card" key={idx}>
              <div className="market-card-top">
                <span className="market-flag-tag">{mkt.flag}</span>
                <span className="market-badge">{mkt.badge}</span>
              </div>
              <h4>{mkt.title}</h4>
              <p>{mkt.description}</p>
              <div className="market-specs">
                <div className="market-spec-item">
                  <span>Ticker Rule:</span>
                  <strong>{mkt.format}</strong>
                </div>
                <div className="market-spec-item">
                  <span>Currency:</span>
                  <strong>{mkt.currency}</strong>
                </div>
                <div className="market-spec-item">
                  <span>Trading Hours:</span>
                  <strong>{mkt.hours}</strong>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture & Development Roadmap */}
      <section className="landing-section" id="roadmap">
        <div className="section-intro">
          <span className="section-kicker">PROJECT ROADMAP</span>
          <h2 className="section-title">Architecture & Development Phases</h2>
          <p className="section-desc">
            This repository implements Module 1 of a multi-module research system. Subsequent modules add automated quant analysis, sentiment extraction, and multi-agent synthesis.
          </p>
        </div>

        <div className="roadmap-grid">
          {ROADMAP_MODULES.map((mod, idx) => (
            <div className={`roadmap-card roadmap-${mod.statusType}`} key={idx}>
              <div className="roadmap-card-top">
                <span className={`roadmap-status-badge badge-${mod.statusType}`}>
                  {mod.number} · {mod.status.toUpperCase()}
                </span>
              </div>
              <h4>{mod.title}</h4>
              <p>{mod.description}</p>
            </div>
          ))}
        </div>

        <div className="roadmap-scope-note">
          <div className="scope-note-icon">ℹ️</div>
          <div>
            <strong>Implementation Scope Notice</strong>
            <p>
              Module 1 implements the complete authentication and research workspace foundation. Research requests created in this module are saved with <code>Pending</code> status in PostgreSQL. They will remain pending until downstream research agents in later modules process the tasks. The application does not fabricate or simulate analysis results.
            </p>
          </div>
        </div>
      </section>

      {/* Security & Data Provenance */}
      <section className="landing-section alt-bg" id="security">
        <div className="section-intro">
          <span className="section-kicker">DATA INTEGRITY & SECURITY</span>
          <h2 className="section-title">Security & Data Provenance</h2>
          <p className="section-desc">
            Engineered with strict security practices, verifiable data provenance, and transparent data handling.
          </p>
        </div>

        <div className="security-grid">
          {SECURITY_POINTS.map((sec, idx) => (
            <div className="security-card" key={idx}>
              <div className="security-card-header">
                <div className="security-icon">🔒</div>
                <h4>{sec.title}</h4>
              </div>
              <p>{sec.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Technology Stack */}
      <section className="landing-section" id="tech">
        <div className="section-intro">
          <span className="section-kicker">IMPLEMENTED TECHNOLOGIES</span>
          <h2 className="section-title">Technology Stack</h2>
          <p className="section-desc">
            Every technology listed below is actively implemented and operating in this project codebase.
          </p>
        </div>

        <div className="tech-grid">
          {TECH_STACK.map((tech, idx) => (
            <div className="tech-card" key={idx}>
              <div className="tech-card-icon">{tech.icon}</div>
              <strong>{tech.name}</strong>
              <span className="tech-category">{tech.category}</span>
              <p>{tech.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ Section */}
      <section className="landing-section alt-bg" id="faq">
        <div className="section-intro">
          <span className="section-kicker">FREQUENTLY ASKED QUESTIONS</span>
          <h2 className="section-title">Common Questions & Answers</h2>
          <p className="section-desc">
            Clear, honest answers about provider feeds, security, module boundaries, and persistence.
          </p>
        </div>

        <div className="faq-list">
          {FAQS.map((faq, idx) => (
            <div
              key={idx}
              className={`faq-item ${openFaqIndex === idx ? "open" : ""}`}
            >
              <button
                className="faq-question-btn"
                onClick={() => setOpenFaqIndex(openFaqIndex === idx ? -1 : idx)}
              >
                <span>{faq.q}</span>
                <span className="faq-toggle-icon">{openFaqIndex === idx ? "−" : "+"}</span>
              </button>
              {openFaqIndex === idx && (
                <div className="faq-answer">
                  <p>{faq.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Final CTA Banner */}
      <section className="cta-banner-section">
        <div className="cta-banner-box">
          <h2>Ready to Explore Your Research Workspace?</h2>
          <p>
            Create an account or sign in to start managing your watchlists, collecting verified market data, and configuring your market research preferences.
          </p>
          <div className="cta-banner-actions">
            {user ? (
              <button className="btn-hero-primary" onClick={onOpenWorkspace}>
                Open Workspace <span>→</span>
              </button>
            ) : (
              <>
                <button className="btn-hero-primary" onClick={() => onNavigateAuth("register")}>
                  Get Started Free <span>→</span>
                </button>
                <button className="btn-hero-secondary" onClick={() => onNavigateAuth("login")}>
                  Sign In to Account
                </button>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="landing-footer-left">
            <div className="brand-icon" style={{ width: "30px", height: "30px", fontSize: "15px" }}>
              S
            </div>
            <div className="landing-footer-copy">
              <strong>Stock Research Analyst</strong>
              <p>Module 1: User Authentication and Research Workspace.</p>
            </div>
          </div>

          <div className="landing-footer-links">
            <button className="footer-link-btn" onClick={() => setModalType("about")}>
              About
            </button>
            <button className="footer-link-btn" onClick={() => setModalType("contact")}>
              Contact
            </button>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="footer-link-btn"
            >
              GitHub
            </a>
            <button className="footer-link-btn" onClick={() => setModalType("privacy")}>
              Privacy Policy
            </button>
            <button className="footer-link-btn" onClick={() => setModalType("terms")}>
              Terms and Conditions
            </button>
            <button
              className="back-to-top-btn"
              title="Back to top"
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            >
              ↑
            </button>
          </div>
        </div>

        <div className="landing-footer-sub">
          <p>
            © {new Date().getFullYear()} Stock Research Analyst. Developed for educational, research, and analysis workflows. Market data provided through Yahoo Finance (yfinance).
          </p>
        </div>
      </footer>

      {/* Floating Workspace Banner for Logged-In Users */}
      {user && (
        <div className="authenticated-floating-banner">
          <span>Signed in as <strong>{user.full_name}</strong></span>
          <button onClick={onOpenWorkspace}>Return to Workspace →</button>
        </div>
      )}

      {/* Modals for Footer Info */}
      {modalType && (
        <div className="landing-modal-backdrop" onClick={() => setModalType(null)}>
          <div className="landing-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="landing-modal-close" onClick={() => setModalType(null)}>
              ×
            </button>

            {modalType === "about" && (
              <div>
                <span className="section-kicker">PROJECT OVERVIEW</span>
                <h3>About Stock Research Analyst</h3>
                <p>
                  Stock Research Analyst is an extensible equity analysis workspace built to bridge reliable financial data extraction with modern full-stack engineering.
                </p>
                <p>
                  <strong>Module 1</strong> establishes user authentication, session security, personal watchlists, preference configuration, and Yahoo Finance market-data integration across Indian (NSE, BSE) and US (NASDAQ, NYSE) exchanges.
                </p>
                <p>
                  Subsequent modules expand the platform with autonomous LangGraph quantitative and sentiment research agents.
                </p>
              </div>
            )}

            {modalType === "contact" && (
              <div>
                <span className="section-kicker">COMMUNICATION</span>
                <h3>Contact & Project Support</h3>
                <p>
                  This project is maintained for research and educational purposes. For inquiries, feedback, or technical questions regarding Module 1:
                </p>
                <ul className="modal-list">
                  <li><strong>Repository Issues:</strong> Submit an issue or discussion on the project repository.</li>
                  <li><strong>API Documentation:</strong> Inspect interactive endpoints at <code>http://127.0.0.1:8000/docs</code> when the backend server is running.</li>
                  <li><strong>Security Inquiries:</strong> Report security concerns directly via project issue tracker.</li>
                </ul>
              </div>
            )}

            {modalType === "privacy" && (
              <div>
                <span className="section-kicker">DATA PROTECTION</span>
                <h3>Privacy Policy</h3>
                <p>
                  Your privacy and security are core priorities of the Stock Research Analyst workspace:
                </p>
                <ul className="modal-list">
                  <li><strong>Credential Security:</strong> Passwords are never stored in plaintext. All passwords are encrypted using Argon2id with random salts.</li>
                  <li><strong>Session Storage:</strong> User authentication tokens are stored in signed, HttpOnly cookies with SameSite protection to prevent client-side script interception.</li>
                  <li><strong>Data Isolation:</strong> Watchlists, preferences, and research tasks are stored in your configured PostgreSQL database with foreign-key isolation tied to your user ID.</li>
                  <li><strong>Zero Third-Party Trackers:</strong> No marketing trackers, behavioral analytics, or third-party advertising cookies are used.</li>
                </ul>
              </div>
            )}

            {modalType === "terms" && (
              <div>
                <span className="section-kicker">LEGAL DISCLAIMER</span>
                <h3>Terms and Conditions</h3>
                <p>
                  Please review the terms of use for the Stock Research Analyst application:
                </p>
                <ul className="modal-list">
                  <li><strong>Educational & Research Use Only:</strong> This application is designed solely for educational, technical, and informational research. It does not provide professional financial, investment, legal, or tax advice.</li>
                  <li><strong>No Investment Recommendation:</strong> The inclusion of any company, ticker, financial ratio, or historical price does not constitute an endorsement, recommendation, or solicitation to buy or sell securities.</li>
                  <li><strong>Market Data Sourcing:</strong> Market data is obtained through the Yahoo Finance integration (yfinance). We do not guarantee real-time delivery, uninterrupted availability, or complete accuracy of third-party market feeds. Always verify critical decisions with official exchange filings.</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default LandingPage;
