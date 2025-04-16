-- Esquema de base de datos para el sistema de notificaciones de InversorIA Pro
-- Este archivo contiene las definiciones de las tablas necesarias para almacenar
-- señales de trading y registros de envíos de boletines.

-- Tabla para almacenar señales de trading
CREATE TABLE IF NOT EXISTS trading_signals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT 'Símbolo del activo',
    price DECIMAL(10, 2) COMMENT 'Precio al momento de la señal',
    direction ENUM('CALL', 'PUT', 'NEUTRAL') NOT NULL COMMENT 'Dirección de la señal (compra, venta, neutral)',
    confidence_level ENUM('Alta', 'Media', 'Baja') NOT NULL COMMENT 'Nivel de confianza de la señal',
    timeframe VARCHAR(20) COMMENT 'Marco temporal de la señal (corto, medio, largo plazo)',
    strategy VARCHAR(100) COMMENT 'Estrategia utilizada para generar la señal',
    category VARCHAR(50) COMMENT 'Categoría del activo (tecnología, finanzas, etc.)',
    analysis TEXT COMMENT 'Análisis detallado que justifica la señal',
    created_at DATETIME NOT NULL COMMENT 'Fecha y hora de creación de la señal',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha y hora de última actualización',
    INDEX idx_symbol (symbol),
    INDEX idx_direction (direction),
    INDEX idx_confidence (confidence_level),
    INDEX idx_category (category),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Señales de trading generadas por el sistema';

-- Tabla para almacenar registros de envíos de boletines
CREATE TABLE IF NOT EXISTS email_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipients TEXT NOT NULL COMMENT 'Lista de destinatarios',
    subject VARCHAR(255) NOT NULL COMMENT 'Asunto del correo',
    content_summary VARCHAR(255) COMMENT 'Resumen del contenido enviado',
    signals_included TEXT COMMENT 'IDs de las señales incluidas en el boletín',
    sent_at DATETIME NOT NULL COMMENT 'Fecha y hora de envío',
    status ENUM('success', 'failed') DEFAULT 'success' COMMENT 'Estado del envío',
    error_message TEXT COMMENT 'Mensaje de error en caso de fallo',
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Registro de envíos de boletines';

-- Tabla para almacenar sentimiento de mercado
CREATE TABLE IF NOT EXISTS market_sentiment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL COMMENT 'Fecha del sentimiento',
    overall ENUM('Alcista', 'Bajista', 'Neutral') NOT NULL COMMENT 'Sentimiento general del mercado',
    vix DECIMAL(5, 2) COMMENT 'Valor del índice VIX',
    sp500_trend VARCHAR(100) COMMENT 'Tendencia del S&P 500',
    technical_indicators VARCHAR(100) COMMENT 'Resumen de indicadores técnicos',
    volume VARCHAR(100) COMMENT 'Descripción del volumen',
    notes TEXT COMMENT 'Notas adicionales sobre el sentimiento',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha y hora de registro',
    UNIQUE INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Registro diario del sentimiento de mercado';

-- Tabla para almacenar noticias relevantes
CREATE TABLE IF NOT EXISTS market_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL COMMENT 'Título de la noticia',
    summary TEXT COMMENT 'Resumen de la noticia',
    source VARCHAR(100) COMMENT 'Fuente de la noticia',
    url VARCHAR(255) COMMENT 'URL de la noticia original',
    news_date DATETIME COMMENT 'Fecha y hora de la noticia',
    impact ENUM('Alto', 'Medio', 'Bajo') COMMENT 'Impacto potencial en el mercado',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha y hora de registro',
    INDEX idx_news_date (news_date),
    INDEX idx_impact (impact)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Noticias relevantes del mercado';
