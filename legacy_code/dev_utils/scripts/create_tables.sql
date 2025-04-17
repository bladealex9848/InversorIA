-- Script para crear las tablas necesarias para el sistema de notificaciones de InversorIA

-- Tabla para almacenar señales de trading
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_direction (direction),
    INDEX idx_confidence (confidence_level),
    INDEX idx_category (category),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para almacenar registros de correos enviados
CREATE TABLE IF NOT EXISTS email_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipients TEXT NOT NULL,
    subject VARCHAR(255) NOT NULL,
    content_summary VARCHAR(255),
    signals_included TEXT COMMENT 'IDs de las señales incluidas en el boletín, separados por comas',
    sent_at DATETIME NOT NULL,
    status ENUM('success', 'error') DEFAULT 'success',
    error_message TEXT,
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para almacenar el sentimiento del mercado
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para almacenar noticias del mercado
CREATE TABLE IF NOT EXISTS market_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    source VARCHAR(100),
    url VARCHAR(255),
    news_date DATETIME NOT NULL,
    impact ENUM('Alto', 'Medio', 'Bajo') DEFAULT 'Medio',
    created_at DATETIME NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_news_date (news_date),
    INDEX idx_impact (impact)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para almacenar configuración del sistema de notificaciones
CREATE TABLE IF NOT EXISTS notification_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(50) NOT NULL,
    setting_value TEXT,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_setting_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar configuraciones iniciales
INSERT INTO notification_settings (setting_key, setting_value, description)
VALUES 
    ('default_recipients', '', 'Lista de destinatarios predeterminados separados por comas'),
    ('email_frequency', 'daily', 'Frecuencia de envío de boletines (daily, weekly, custom)'),
    ('include_sentiment', 'true', 'Incluir sentimiento de mercado en los boletines'),
    ('include_news', 'true', 'Incluir noticias en los boletines'),
    ('min_confidence_level', 'Media', 'Nivel mínimo de confianza para incluir señales en boletines automáticos')
ON DUPLICATE KEY UPDATE description = VALUES(description);
