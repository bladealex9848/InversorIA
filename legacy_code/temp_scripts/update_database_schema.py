"""
Script para actualizar el esquema de la base de datos
"""

import logging
from database_utils import DatabaseManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def update_trading_signals_schema(db_manager):
    """Actualiza el esquema de la tabla trading_signals"""
    try:
        # Modificar la columna recommendation para permitir textos más largos
        query = """
        ALTER TABLE trading_signals 
        MODIFY COLUMN recommendation TEXT
        """
        
        result = db_manager.execute_query(query, fetch=False)
        if result is not None:
            logger.info("Columna 'recommendation' actualizada correctamente a tipo TEXT")
            return True
        else:
            logger.error("Error actualizando columna 'recommendation'")
            return False
    except Exception as e:
        logger.error(f"Error actualizando esquema de trading_signals: {str(e)}")
        return False

def update_market_news_schema(db_manager):
    """Actualiza el esquema de la tabla market_news"""
    try:
        # Verificar si la columna url ya es VARCHAR(255)
        query = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'market_news'
        AND COLUMN_NAME = 'url'
        """
        
        result = db_manager.execute_query(query)
        if result and len(result) > 0:
            current_length = result[0].get('CHARACTER_MAXIMUM_LENGTH', 0)
            if current_length < 255:
                # Modificar la columna url para permitir URLs más largas
                update_query = """
                ALTER TABLE market_news 
                MODIFY COLUMN url VARCHAR(255)
                """
                
                update_result = db_manager.execute_query(update_query, fetch=False)
                if update_result is not None:
                    logger.info("Columna 'url' actualizada correctamente a VARCHAR(255)")
                else:
                    logger.error("Error actualizando columna 'url'")
            else:
                logger.info("La columna 'url' ya tiene el tamaño adecuado")
        
        return True
    except Exception as e:
        logger.error(f"Error actualizando esquema de market_news: {str(e)}")
        return False

def update_email_logs_schema(db_manager):
    """Actualiza el esquema de la tabla email_logs"""
    try:
        # Modificar la columna content_summary para permitir textos más largos
        query = """
        ALTER TABLE email_logs 
        MODIFY COLUMN content_summary TEXT
        """
        
        result = db_manager.execute_query(query, fetch=False)
        if result is not None:
            logger.info("Columna 'content_summary' actualizada correctamente a tipo TEXT")
            return True
        else:
            logger.error("Error actualizando columna 'content_summary'")
            return False
    except Exception as e:
        logger.error(f"Error actualizando esquema de email_logs: {str(e)}")
        return False

def main():
    """Función principal"""
    print("\n===== ACTUALIZACIÓN DEL ESQUEMA DE LA BASE DE DATOS =====\n")
    
    # Crear instancia del gestor de base de datos
    db_manager = DatabaseManager()
    
    # Actualizar esquema de trading_signals
    print("\n----- Actualizando tabla: trading_signals -----")
    if update_trading_signals_schema(db_manager):
        print("✅ Esquema de trading_signals actualizado correctamente")
    else:
        print("❌ Error actualizando esquema de trading_signals")
    
    # Actualizar esquema de market_news
    print("\n----- Actualizando tabla: market_news -----")
    if update_market_news_schema(db_manager):
        print("✅ Esquema de market_news actualizado correctamente")
    else:
        print("❌ Error actualizando esquema de market_news")
    
    # Actualizar esquema de email_logs
    print("\n----- Actualizando tabla: email_logs -----")
    if update_email_logs_schema(db_manager):
        print("✅ Esquema de email_logs actualizado correctamente")
    else:
        print("❌ Error actualizando esquema de email_logs")
    
    print("\n===== ACTUALIZACIÓN COMPLETADA =====")

if __name__ == "__main__":
    main()
