-- Reference DDL (SQLAlchemy creates these automatically on first start)
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  market VARCHAR(10) NOT NULL DEFAULT 'NSE',
  analysis_period VARCHAR(5) NOT NULL DEFAULT '1Y',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE saved_stocks (
  saved_stock_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  ticker VARCHAR(20) NOT NULL,
  company_name VARCHAR(160) NOT NULL,
  market VARCHAR(10) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_user_ticker UNIQUE (user_id, ticker)
);
CREATE TABLE research_tasks (
  task_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  ticker VARCHAR(20) NOT NULL,
  company_name VARCHAR(160) NOT NULL,
  market VARCHAR(10) NOT NULL,
  analysis_period VARCHAR(5) NOT NULL,
  status VARCHAR(15) NOT NULL DEFAULT 'Pending',
  report JSON, error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);
CREATE INDEX ix_task_user_created ON research_tasks (user_id, created_at);
