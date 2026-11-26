-- PostgreSQL schema for Module 1 / Milestone 1 (generated from app/models.py; the app also creates these on startup)

CREATE TABLE users (
	user_id SERIAL NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(255), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (user_id), 
	UNIQUE (email)
);


CREATE TABLE oauth_identities (
	identity_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	provider VARCHAR(10) NOT NULL, 
	provider_user_id VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (identity_id), 
	CONSTRAINT ck_oauth_provider CHECK (provider IN ('google', 'apple')), 
	CONSTRAINT uq_oauth_provider_identity UNIQUE (provider, provider_user_id), 
	CONSTRAINT uq_oauth_user_provider UNIQUE (user_id, provider), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE INDEX ix_oauth_identities_user_id ON oauth_identities (user_id);

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


CREATE TABLE agent_results (
	result_id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	agent_name VARCHAR(50) NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	output JSONB NOT NULL, 
	error_message TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (result_id), 
	CONSTRAINT ck_agent_result_status CHECK (status IN ('Completed', 'Failed', 'Unavailable')), 
	FOREIGN KEY(task_id) REFERENCES research_tasks (task_id) ON DELETE CASCADE
);

CREATE INDEX ix_agent_results_task_id ON agent_results (task_id);

CREATE TABLE source_documents (
	source_id SERIAL NOT NULL, 
	task_id INTEGER, 
	user_id INTEGER, 
	ticker VARCHAR(20) NOT NULL, 
	market VARCHAR(10) NOT NULL, 
	doc_type VARCHAR(12) NOT NULL, 
	source_name VARCHAR(150) NOT NULL, 
	source_url VARCHAR(500), 
	is_synthetic BOOLEAN NOT NULL, 
	retrieved_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	record_count INTEGER, 
	quality JSONB, 
	PRIMARY KEY (source_id), 
	CONSTRAINT ck_source_doc_type CHECK (doc_type IN ('ohlcv', 'profile', 'financials', 'news')), 
	FOREIGN KEY(task_id) REFERENCES research_tasks (task_id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE INDEX ix_source_documents_task_id ON source_documents (task_id);
CREATE INDEX ix_source_documents_user_retrieved ON source_documents (user_id, retrieved_at);
