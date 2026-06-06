CREATE TABLE IF NOT EXISTS stocks(

symbol TEXT PRIMARY KEY,

company_name TEXT,

sector TEXT
);
CREATE TABLE IF NOT EXISTS fundamentals(

symbol TEXT,

roe REAL,

roce REAL,

debt_equity REAL,

sales_growth REAL,

profit_growth REAL,

market_cap REAL,

updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS technicals(

symbol TEXT,

rsi REAL,

sma50 REAL,

sma200 REAL,

volume REAL,

breakout INTEGER,

updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS news(

symbol TEXT,

headline TEXT,

sentiment TEXT,

score INTEGER,

published_at DATETIME
);

CREATE TABLE IF NOT EXISTS scores(

symbol TEXT,

fundamental_score INTEGER,

technical_score INTEGER,

news_score INTEGER,

final_score INTEGER,

updated_at DATETIME
);