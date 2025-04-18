#!/usr/bin/env python3
"""
Script para verificar la estructura de la tabla market_sentiment
"""

import sys
import os
import logging
import mysql.connector
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Añadir directorio raíz al path para importar módulos del proyecto principal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importar funciones necesarias
try:
    from database_utils import DatabaseManager
except ImportError:
    logger.error("No se pudo importar DatabaseManager. Verifica la estructura del proyecto.")
    sys.exit(1)

def check_table_structure():
    """Verifica la estructura de la tabla market_sentiment"""
    try:
        # Crear instancia del gestor de base de datos
        db_manager = DatabaseManager()
        
        # Verificar si se puede conectar a la base de datos
        if not db_manager.connect():
            logger.error("No se pudo conectar a la base de datos.")
            return False
        
        # Verificar si la tabla market_sentiment existe
        check_table_query = """
        SELECT COUNT(*) as table_exists 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() 
        AND table_name = 'market_sentiment'
        """
        
        result = db_manager.execute_query(check_table_query)
        
        if not result or result[0]['table_exists'] == 0:
            logger.error("La tabla market_sentiment no existe.")
            return False
        
        # Obtener la estructura de la tabla
        describe_query = "DESCRIBE market_sentiment"
        columns = db_manager.execute_query(describe_query)
        
        if not columns:
            logger.error("No se pudo obtener la estructura de la tabla market_sentiment.")
            return False
        
        # Verificar si los campos necesarios existen
        required_fields = [
            "symbol", "sentiment", "score", "source", "analysis", "sentiment_date"
        ]
        
        existing_fields = [col['Field'] for col in columns]
        logger.info(f"Campos existentes: {', '.join(existing_fields)}")
        
        missing_fields = [field for field in required_fields if field not in existing_fields]
        
        if missing_fields:
            logger.warning(f"Faltan los siguientes campos: {', '.join(missing_fields)}")
            
            # Añadir los campos faltantes
            for field in missing_fields:
                if field == "symbol":
                    alter_query = "ALTER TABLE market_sentiment ADD COLUMN symbol VARCHAR(20) DEFAULT NULL COMMENT 'Símbolo del activo principal' AFTER notes"
                elif field == "sentiment":
                    alter_query = "ALTER TABLE market_sentiment ADD COLUMN sentiment VARCHAR(50) DEFAULT NULL COMMENT 'Sentimiento específico del activo' AFTER symbol"
                elif field == "score":
                    alter_query = "ALTER TABLE market_sentiment ADD COLUMN score DECIMAL(5,2) DEFAULT NULL COMMENT 'Puntuación numérica del sentimiento' AFTER sentiment"
                elif field == "source":
                    alter_query = "ALTER TABLE market_sentiment ADD COLUMN source VARCHAR(100) DEFAULT NULL COMMENT 'Fuente del análisis de sentimiento' AFTER score"
                elif field == "analysis":
                    alter_query = "ALTER TABLE market_sentiment ADD COLUMN analysis TEXT DEFAULT NULL COMMENT 'Análisis detallado del sentimiento' AFTER source"
                elif field == "sentiment_date":
                    alter_query = "ALTER TABLE market_sentiment ADD COLUMN sentiment_date DATETIME DEFAULT NULL COMMENT 'Fecha y hora del análisis de sentimiento' AFTER analysis"
                
                logger.info(f"Añadiendo campo {field}...")
                db_manager.execute_query(alter_query, fetch=False)
            
            logger.info("Campos añadidos correctamente.")
        else:
            logger.info("La tabla market_sentiment ya tiene todos los campos necesarios.")
        
        # Verificar si hay registros en la tabla
        count_query = "SELECT COUNT(*) as record_count FROM market_sentiment"
        count_result = db_manager.execute_query(count_query)
        
        if count_result and count_result[0]['record_count'] > 0:
            logger.info(f"La tabla market_sentiment tiene {count_result[0]['record_count']} registros.")
            
            # Mostrar algunos registros de ejemplo
            sample_query = "SELECT * FROM market_sentiment LIMIT 3"
            sample_records = db_manager.execute_query(sample_query)
            
            if sample_records:
                logger.info("Registros de ejemplo:")
                for i, record in enumerate(sample_records):
                    logger.info(f"Registro {i+1}:")
                    for key, value in record.items():
                        logger.info(f"  {key}: {value}")
        else:
            logger.warning("La tabla market_sentiment no tiene registros.")
        
        # Desconectar de la base de datos
        db_manager.disconnect()
        
        return True
    
    except Exception as e:
        logger.error(f"Error verificando la estructura de la tabla: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("Verificando estructura de la tabla market_sentiment...")
    
    if check_table_structure():
        logger.info("Verificación completada con éxito.")
    else:
        logger.error("La verificación falló.")

if __name__ == "__main__":
    main()
