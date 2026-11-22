-- PostgreSQL schema (generated from app/models.py)

CREATE TABLE users (
	user_id SERIAL NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (user_id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE data_collections (
	collection_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	ticker VARCHAR(20) NOT NULL, 
	company_name VARCHAR(200) NOT NULL, 
	market VARCHAR(10) NOT NULL, 
	analysis_period VARCHAR(3) NOT NULL, 
	source VARCHAR(80) NOT NULL, 
	retrieved_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	rows_raw INTEGER NOT NULL, 
	rows_clean INTEGER NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	report JSON NOT NULL, 
	profile JSON, 
	financials JSON, 
	PRIMARY KEY (collection_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE INDEX ix_data_collections_user_id ON data_collections (user_id);

CREATE TABLE research_tasks (
	task_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	company_name VARCHAR(200) NOT NULL, 
	ticker VARCHAR(20) NOT NULL, 
	market VARCHAR(10) NOT NULL, 
	analysis_period VARCHAR(3) NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	report TEXT, 
	error_message TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (task_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE INDEX ix_research_tasks_user_id ON research_tasks (user_id);

CREATE TABLE saved_stocks (
	saved_stock_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	ticker VARCHAR(20) NOT NULL, 
	company_name VARCHAR(200) NOT NULL, 
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
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);


CREATE TABLE price_bars (
	bar_id SERIAL NOT NULL, 
	collection_id INTEGER NOT NULL, 
	date DATE NOT NULL, 
	open FLOAT NOT NULL, 
	high FLOAT NOT NULL, 
	low FLOAT NOT NULL, 
	close FLOAT NOT NULL, 
	volume BIGINT NOT NULL, 
	PRIMARY KEY (bar_id), 
	CONSTRAINT uq_price_bar_collection_date UNIQUE (collection_id, date), 
	FOREIGN KEY(collection_id) REFERENCES data_collections (collection_id) ON DELETE CASCADE
);

CREATE INDEX ix_price_bars_collection_id ON price_bars (collection_id);

