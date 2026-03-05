-- Ruo - AI 智能投顾副驾 数据库初始化脚本
-- 基于 SQLAlchemy 模型定义的表结构同步

-- 授予 schema 权限 (数据库通常由环境变量创建)
GRANT ALL ON SCHEMA public TO ruo_user;

-- ==================== 1. 用户模块 (User) ====================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ==================== 2. 股票及概念模块 (Stock & Concept) ====================
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    market VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol);

CREATE TABLE IF NOT EXISTS concepts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name);

CREATE TABLE IF NOT EXISTS concept_stocks (
    id SERIAL PRIMARY KEY,
    concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    stock_symbol VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    positioning VARCHAR(20) DEFAULT '补涨',
    notes VARCHAR(200),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(concept_id, stock_symbol)
);
CREATE INDEX IF NOT EXISTS idx_concept_stocks_symbol ON concept_stocks(stock_symbol);

-- ==================== 3. 策略模块 (Strategy) ====================
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL,
    config JSONB DEFAULT '{}',
    entry_rules JSONB DEFAULT '[]',
    exit_rules JSONB DEFAULT '[]',
    position_rules JSONB DEFAULT '{}',
    risk_rules JSONB DEFAULT '{}',
    is_active INTEGER DEFAULT 1,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_return DOUBLE PRECISION DEFAULT 0.0,
    max_drawdown DOUBLE PRECISION DEFAULT 0.0,
    sharpe_ratio DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==================== 4. 持仓及交易 (Portfolio & Trade) ====================
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) DEFAULT 1,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(50) NOT NULL,
    market VARCHAR(50),
    cost_price DOUBLE PRECISION NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    strategy_tag VARCHAR(20),
    strategy_id INTEGER REFERENCES strategies(id),
    current_price DOUBLE PRECISION DEFAULT 0.0,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_portfolios_symbol ON portfolios(symbol);
CREATE INDEX IF NOT EXISTS idx_portfolios_user ON portfolios(user_id);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    symbol VARCHAR(10) NOT NULL,
    trade_type VARCHAR(10) NOT NULL,
    shares DOUBLE PRECISION NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    commission DOUBLE PRECISION DEFAULT 0.0,
    trade_date TIMESTAMP WITH TIME ZONE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);

-- ==================== 5. 行情引擎 (Market Data) ====================

-- 三表物理拆分 ( market_daily_price, market_weekly_price, market_monthly_price )
CREATE TABLE IF NOT EXISTS market_daily_price (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    pre_close DOUBLE PRECISION,
    volume DOUBLE PRECISION NOT NULL,
    amount DOUBLE PRECISION,
    change DOUBLE PRECISION,
    change_pct DOUBLE PRECISION,
    turnover DOUBLE PRECISION,
    ma5 DOUBLE PRECISION,
    ma10 DOUBLE PRECISION,
    ma20 DOUBLE PRECISION,
    ma60 DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_daily_query ON market_daily_price(symbol, trade_date);

CREATE TABLE IF NOT EXISTS market_weekly_price (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    pre_close DOUBLE PRECISION,
    volume DOUBLE PRECISION NOT NULL,
    amount DOUBLE PRECISION,
    change DOUBLE PRECISION,
    change_pct DOUBLE PRECISION,
    turnover DOUBLE PRECISION,
    ma5 DOUBLE PRECISION,
    ma10 DOUBLE PRECISION,
    ma20 DOUBLE PRECISION,
    ma60 DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, trade_date)
);

CREATE TABLE IF NOT EXISTS market_monthly_price (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    pre_close DOUBLE PRECISION,
    volume DOUBLE PRECISION NOT NULL,
    amount DOUBLE PRECISION,
    change DOUBLE PRECISION,
    change_pct DOUBLE PRECISION,
    turnover DOUBLE PRECISION,
    ma5 DOUBLE PRECISION,
    ma10 DOUBLE PRECISION,
    ma20 DOUBLE PRECISION,
    ma60 DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, trade_date)
);

-- ==================== 6. 预警模块 (Alert) ====================
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) DEFAULT 1,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    alert_type VARCHAR(20) NOT NULL,
    threshold_value DOUBLE PRECISION NOT NULL,
    compare_operator VARCHAR(10) DEFAULT '>=',
    is_active INTEGER DEFAULT 1,
    cooldown_minutes INTEGER DEFAULT 60,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alert_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) DEFAULT 1,
    alert_rule_id INTEGER NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    trigger_price DOUBLE PRECISION NOT NULL,
    trigger_value DOUBLE PRECISION NOT NULL,
    message TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==================== 7. 新闻资讯 (News) ====================
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source, external_id)
);
CREATE INDEX IF NOT EXISTS idx_news_time ON news(publish_time);

-- ==================== 8. 回测及信号 (Backtest & Signal) ====================
CREATE TABLE IF NOT EXISTS backtests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) DEFAULT 1,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    start_date VARCHAR(10) NOT NULL,
    end_date VARCHAR(10) NOT NULL,
    initial_capital DOUBLE PRECISION NOT NULL DEFAULT 1000000.0,
    final_capital DOUBLE PRECISION DEFAULT 0.0,
    total_return DOUBLE PRECISION DEFAULT 0.0,
    annualized_return DOUBLE PRECISION DEFAULT 0.0,
    max_drawdown DOUBLE PRECISION DEFAULT 0.0,
    sharpe_ratio DOUBLE PRECISION DEFAULT 0.0,
    sortino_ratio DOUBLE PRECISION DEFAULT 0.0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DOUBLE PRECISION DEFAULT 0.0,
    avg_profit DOUBLE PRECISION DEFAULT 0.0,
    avg_loss DOUBLE PRECISION DEFAULT 0.0,
    profit_factor DOUBLE PRECISION DEFAULT 0.0,
    trades JSONB DEFAULT '[]',
    daily_returns JSONB DEFAULT '[]',
    equity_curve JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS strategy_signals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) DEFAULT 1,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(50),
    signal_type VARCHAR(10) NOT NULL,
    strength INTEGER DEFAULT 5,
    suggested_position DOUBLE PRECISION DEFAULT 0.0,
    trigger_price DOUBLE PRECISION,
    stop_loss_price DOUBLE PRECISION,
    take_profit_price DOUBLE PRECISION,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expired_at TIMESTAMP WITH TIME ZONE
);

-- ==================== 9. 初始基础数据 ====================
-- 此处可添加板块数据等
INSERT INTO users (id, username, email, hashed_password, is_superuser) 
VALUES (1, 'admin', 'admin@ruo.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGGa31S2', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO concepts (name, description) VALUES 
('人工智能', '涵盖大模型、算力、应用等环节'),
('半导体', '集成电路设计、制造、封测'),
('低空经济', '无人机、eVTOL及相关配套')
ON CONFLICT (name) DO NOTHING;

-- 输出完成信息
SELECT 'Ruo database initialization completed successfully!' AS status;
