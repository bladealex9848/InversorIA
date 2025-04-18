-- Script para actualizar la estructura de la tabla market_sentiment
-- Asegura que todos los campos necesarios estén presentes

-- Verificar si la tabla existe
SET @table_exists = 0;
SELECT COUNT(*) INTO @table_exists FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_name = 'market_sentiment';

-- Si la tabla existe, añadir los campos que faltan
SET @add_symbol = CONCAT('ALTER TABLE market_sentiment ADD COLUMN IF NOT EXISTS symbol VARCHAR(20) DEFAULT NULL COMMENT "Símbolo del activo principal" AFTER notes');
SET @add_sentiment = CONCAT('ALTER TABLE market_sentiment ADD COLUMN IF NOT EXISTS sentiment VARCHAR(50) DEFAULT NULL COMMENT "Sentimiento específico del activo" AFTER symbol');
SET @add_score = CONCAT('ALTER TABLE market_sentiment ADD COLUMN IF NOT EXISTS score DECIMAL(5,2) DEFAULT NULL COMMENT "Puntuación numérica del sentimiento" AFTER sentiment');
SET @add_source = CONCAT('ALTER TABLE market_sentiment ADD COLUMN IF NOT EXISTS source VARCHAR(100) DEFAULT NULL COMMENT "Fuente del análisis de sentimiento" AFTER score');
SET @add_analysis = CONCAT('ALTER TABLE market_sentiment ADD COLUMN IF NOT EXISTS analysis TEXT DEFAULT NULL COMMENT "Análisis detallado del sentimiento" AFTER source');
SET @add_sentiment_date = CONCAT('ALTER TABLE market_sentiment ADD COLUMN IF NOT EXISTS sentiment_date DATETIME DEFAULT NULL COMMENT "Fecha y hora del análisis de sentimiento" AFTER analysis');

-- Ejecutar las consultas si la tabla existe
SET @sql = IF(@table_exists > 0, @add_symbol, 'SELECT "Tabla no existe"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@table_exists > 0, @add_sentiment, 'SELECT "Tabla no existe"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@table_exists > 0, @add_score, 'SELECT "Tabla no existe"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@table_exists > 0, @add_source, 'SELECT "Tabla no existe"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@table_exists > 0, @add_analysis, 'SELECT "Tabla no existe"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@table_exists > 0, @add_sentiment_date, 'SELECT "Tabla no existe"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Añadir índices para mejorar el rendimiento
SET @add_symbol_index = CONCAT('CREATE INDEX IF NOT EXISTS idx_symbol ON market_sentiment(symbol)');
SET @add_sentiment_index = CONCAT('CREATE INDEX IF NOT EXISTS idx_sentiment ON market_sentiment(sentiment)');
SET @add_sentiment_date_index = CONCAT('CREATE INDEX IF NOT EXISTS idx_sentiment_date ON market_sentiment(sentiment_date)');

SET @sql = IF(@table_exists > 0, @add_symbol_index, 'SELECT "Tabla no existe"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@table_exists > 0, @add_sentiment_index, 'SELECT "Tabla no existe"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@table_exists > 0, @add_sentiment_date_index, 'SELECT "Tabla no existe"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Mostrar la estructura actualizada
SELECT 'Estructura actualizada de la tabla market_sentiment:' AS Message;
DESCRIBE market_sentiment;
