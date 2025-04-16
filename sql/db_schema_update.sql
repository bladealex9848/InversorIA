-- Script para actualizar la estructura de la tabla trading_signals
-- Este script añade nuevos campos para almacenar información más detallada de las señales

-- Primero, hacemos una copia de seguridad de la tabla actual
CREATE TABLE IF NOT EXISTS trading_signals_backup LIKE trading_signals;
INSERT INTO trading_signals_backup SELECT * FROM trading_signals;

-- Ahora añadimos los nuevos campos a la tabla trading_signals
ALTER TABLE trading_signals
    ADD COLUMN entry_price DECIMAL(10,2) COMMENT 'Precio de entrada recomendado' AFTER price,
    ADD COLUMN stop_loss DECIMAL(10,2) COMMENT 'Nivel de stop loss recomendado' AFTER entry_price,
    ADD COLUMN target_price DECIMAL(10,2) COMMENT 'Precio objetivo recomendado' AFTER stop_loss,
    ADD COLUMN risk_reward DECIMAL(5,2) COMMENT 'Ratio riesgo/recompensa' AFTER target_price,
    ADD COLUMN setup_type VARCHAR(100) COMMENT 'Tipo de setup (patrón técnico identificado)' AFTER strategy,
    ADD COLUMN technical_analysis TEXT COMMENT 'Análisis técnico detallado' AFTER analysis,
    ADD COLUMN support_level DECIMAL(10,2) COMMENT 'Nivel de soporte identificado' AFTER technical_analysis,
    ADD COLUMN resistance_level DECIMAL(10,2) COMMENT 'Nivel de resistencia identificado' AFTER support_level,
    ADD COLUMN rsi DECIMAL(5,2) COMMENT 'Valor del indicador RSI' AFTER resistance_level,
    ADD COLUMN trend VARCHAR(50) COMMENT 'Tendencia del activo (ALCISTA, BAJISTA, LATERAL)' AFTER rsi,
    ADD COLUMN trend_strength VARCHAR(50) COMMENT 'Fuerza de la tendencia (ALTA, MEDIA, BAJA)' AFTER trend,
    ADD COLUMN volatility DECIMAL(5,2) COMMENT 'Volatilidad implícita (para opciones)' AFTER trend_strength,
    ADD COLUMN options_signal VARCHAR(50) COMMENT 'Señal derivada del análisis de opciones' AFTER volatility,
    ADD COLUMN options_analysis TEXT COMMENT 'Análisis detallado de opciones' AFTER options_signal,
    ADD COLUMN trading_specialist_signal VARCHAR(50) COMMENT 'Señal del Trading Specialist (COMPRA, VENTA, NEUTRAL)' AFTER options_analysis,
    ADD COLUMN trading_specialist_confidence VARCHAR(50) COMMENT 'Nivel de confianza del Trading Specialist (ALTA, MEDIA, BAJA)' AFTER trading_specialist_signal,
    ADD COLUMN sentiment VARCHAR(50) COMMENT 'Sentimiento de mercado (positivo, negativo, neutral)' AFTER trading_specialist_confidence,
    ADD COLUMN sentiment_score DECIMAL(5,2) COMMENT 'Puntuación numérica del sentimiento (0-1)' AFTER sentiment,
    ADD COLUMN latest_news TEXT COMMENT 'Última noticia relevante sobre el activo' AFTER sentiment_score,
    ADD COLUMN news_source VARCHAR(255) COMMENT 'Fuente de la última noticia' AFTER latest_news,
    ADD COLUMN additional_news TEXT COMMENT 'Noticias adicionales relevantes' AFTER news_source,
    ADD COLUMN expert_analysis TEXT COMMENT 'Análisis del experto' AFTER additional_news,
    ADD COLUMN recommendation VARCHAR(50) COMMENT 'Recomendación final (COMPRAR, VENDER, MANTENER)' AFTER expert_analysis,
    ADD COLUMN mtf_analysis TEXT COMMENT 'Análisis multi-timeframe' AFTER recommendation,
    ADD COLUMN daily_trend VARCHAR(50) COMMENT 'Tendencia en timeframe diario' AFTER mtf_analysis,
    ADD COLUMN weekly_trend VARCHAR(50) COMMENT 'Tendencia en timeframe semanal' AFTER daily_trend,
    ADD COLUMN monthly_trend VARCHAR(50) COMMENT 'Tendencia en timeframe mensual' AFTER weekly_trend,
    ADD COLUMN bullish_indicators TEXT COMMENT 'Indicadores alcistas identificados' AFTER monthly_trend,
    ADD COLUMN bearish_indicators TEXT COMMENT 'Indicadores bajistas identificados' AFTER bullish_indicators,
    ADD COLUMN is_high_confidence BOOLEAN DEFAULT FALSE COMMENT 'Indica si es una señal de alta confianza' AFTER bearish_indicators;

-- Añadir índices para mejorar el rendimiento de las consultas
ALTER TABLE trading_signals
    ADD INDEX idx_entry_price (entry_price),
    ADD INDEX idx_setup_type (setup_type),
    ADD INDEX idx_trend (trend),
    ADD INDEX idx_trading_specialist_signal (trading_specialist_signal),
    ADD INDEX idx_sentiment (sentiment),
    ADD INDEX idx_is_high_confidence (is_high_confidence);

-- Actualizar los comentarios de la tabla
ALTER TABLE trading_signals COMMENT = 'Señales de trading generadas por el sistema con información detallada de análisis';

-- Crear una vista para facilitar la consulta de señales de alta confianza
CREATE OR REPLACE VIEW high_confidence_signals AS
SELECT *
FROM trading_signals
WHERE is_high_confidence = TRUE
   OR confidence_level = 'Alta'
   OR (trading_specialist_signal IN ('COMPRA', 'VENTA') AND trading_specialist_confidence = 'ALTA')
ORDER BY created_at DESC;

-- Crear una vista para señales activas (generadas en las últimas 24 horas)
CREATE OR REPLACE VIEW active_signals AS
SELECT *
FROM trading_signals
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY created_at DESC;
