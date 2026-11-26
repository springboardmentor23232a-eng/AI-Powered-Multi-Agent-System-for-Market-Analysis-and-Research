-- PostgreSQL schema for Module 1 (generated from app/models.py; the app also creates these on startup)

CREATE TABLE users (
	user_id SERIAL NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (user_id), 
	UNIQUE (email)
);


CREATE TABLE research_tasks (
	task_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	ticker VARCHAR(20) NOT NULL, 
	company_name VARCHAR(150) NOT NULL, 
	market VARCHAR(10) NOT NULL, 
	analysis_period VARCHAR(3) NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	error_message TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (task_id), 
	CONSTRAINT ck_task_status CHECK (status IN ('Pending', 'Processing', 'Completed', 'Failed')), 
	CONSTRAINT ck_task_market CHECK (market IN ('NSE', 'BSE', 'NASDAQ', 'NYSE')), 
	CONSTRAINT ck_task_period CHECK (analysis_period IN ('1M', '3M', '6M', '1Y', '5Y')), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE INDEX ix_research_tasks_status ON research_tasks (status);
CREATE INDEX ix_research_tasks_user_created ON research_tasks (user_id, created_at);

CREATE TABLE saved_stocks (
	saved_stock_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	ticker VARCHAR(20) NOT NULL, 
	company_name VARCHAR(150) NOT NULL, 
	market VARCHAR(10) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (saved_stock_id), 
	CONSTRAINT uq_saved_stock_user_ticker UNIQUE (user_id, ticker), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE INDEX ix_saved_stocks_user_id ON saved_stocks (user_id);

CREATE TABLE user_preferences (
	user_id INTEGER NOT NULL, 
	market VARCHAR(10) NOT NULL, 
	analysis_period VARCHAR(3) NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (user_id), 
	CONSTRAINT ck_pref_market CHECK (market IN ('NSE', 'BSE', 'NASDAQ', 'NYSE')), 
	CONSTRAINT ck_pref_period CHECK (analysis_period IN ('1M', '3M', '6M', '1Y', '5Y')), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);


CREATE TABLE research_reports (
	report_id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	summary TEXT NOT NULL, 
	content JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (report_id), 
	UNIQUE (task_id), 
	FOREIGN KEY(task_id) REFERENCES research_tasks (task_id) ON DELETE CASCADE
);

