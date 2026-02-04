-- PostgreSQL Database Initialization SQL Script
-- Includes: User, Portfolio, News, Stock Tables
-- Note: User and database are created by Docker Compose environment variables

-- Grant Schema Privileges (database already created by Docker)
GRANT ALL ON SCHEMA public TO ruo_user;

-- ==================== News Table ====================

-- Create News Table
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    source VARCHAR(20) NOT NULL,
    external_id VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    content TEXT,
    raw_json TEXT,
    relation_stock TEXT,
    ai_analysis TEXT,
    publish_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create News Indexes
CREATE INDEX IF NOT EXISTS idx_news_publish_time ON news(publish_time);
CREATE INDEX IF NOT EXISTS idx_news_source ON news(source);
CREATE UNIQUE INDEX IF NOT EXISTS uq_news_source_external_id ON news(source, external_id);

-- ==================== Portfolio Table ====================

-- Create Portfolio Table
CREATE TABLE IF NOT EXISTS portfolio (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(100),
    cost_price NUMERIC(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    current_price NUMERIC(10, 2),
    cost_value NUMERIC(15, 2),
    market_value NUMERIC(15, 2),
    profit_loss NUMERIC(15, 2),
    profit_loss_ratio NUMERIC(10, 4),
    change_pct NUMERIC(10, 4),
    strategy_tag VARCHAR(20),
    notes TEXT,
    has_new_news BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Portfolio Indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_user_id ON portfolio(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON portfolio(symbol);
CREATE INDEX IF NOT EXISTS idx_portfolio_created_at ON portfolio(created_at);

-- ==================== Trade Table ====================

-- Create Trade Table
CREATE TABLE IF NOT EXISTS trade (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolio(id) ON DELETE CASCADE,
    trade_type VARCHAR(10) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    trade_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Trade Indexes
CREATE INDEX IF NOT EXISTS idx_trade_portfolio_id ON trade(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_trade_date ON trade(trade_date);

-- ==================== User Table ====================

-- Create User Table
CREATE TABLE IF NOT EXISTS user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create User Indexes
CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);

-- ==================== Stock Table ====================

-- Create Stock Table
CREATE TABLE IF NOT EXISTS stock (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100),
    industry VARCHAR(50),
    market VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Stock Indexes
CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stock(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_industry ON stock(industry);

-- Create Stock Price Table
CREATE TABLE IF NOT EXISTS stock_price (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stock(id) ON DELETE CASCADE,
    price NUMERIC(10, 2) NOT NULL,
    change NUMERIC(10, 2),
    change_pct NUMERIC(10, 4),
    volume BIGINT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Stock Price Indexes
CREATE INDEX IF NOT EXISTS idx_stock_price_stock_id ON stock_price(stock_id);
CREATE INDEX IF NOT EXISTS idx_stock_price_timestamp ON stock_price(timestamp);

-- Sample Data (Optional - Commented Out)
INSERT INTO users (username, email, password_hash) VALUES
('admin', 'admin@ruo.com', '$2b$12$w8F...');

INSERT INTO portfolio (user_id, symbol, name, cost_price, quantity, current_price, strategy_tag) VALUES
(1, '002460', '赣锋锂业', 60.00, 100, 67.90, '趋势');

-- Output Success Message
SELECT 'Database setup completed successfully!' AS status;
