-- Crear tabla para señales de trading
CREATE TABLE IF NOT EXISTS trading_signals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    direction ENUM('CALL', 'PUT', 'NEUTRAL') NOT NULL,
    confidence_level ENUM('Alta', 'Media', 'Baja') NOT NULL,
    timeframe VARCHAR(50) NOT NULL,
    strategy VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    analysis TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_direction (direction),
    INDEX idx_confidence (confidence_level),
    INDEX idx_category (category),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear tabla para logs de correos enviados
CREATE TABLE IF NOT EXISTS email_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipients TEXT NOT NULL,
    subject VARCHAR(255) NOT NULL,
    content_summary VARCHAR(255),
    signals_included VARCHAR(255) COMMENT 'IDs de las señales incluidas en el boletín, separados por comas',
    sent_at DATETIME NOT NULL,
    status ENUM('success', 'error') DEFAULT 'success',
    error_message TEXT,
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear tabla para sentimiento de mercado
CREATE TABLE IF NOT EXISTS market_sentiment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    overall ENUM('Alcista', 'Bajista', 'Neutral') NOT NULL,
    vix VARCHAR(50),
    sp500_trend VARCHAR(100),
    technical_indicators VARCHAR(100),
    volume VARCHAR(100),
    notes TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear tabla para noticias de mercado
CREATE TABLE IF NOT EXISTS market_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    source VARCHAR(100),
    url VARCHAR(255),
    news_date DATETIME NOT NULL,
    impact ENUM('Alto', 'Medio', 'Bajo') DEFAULT 'Medio',
    created_at DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_news_date (news_date),
    INDEX idx_impact (impact)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
