"""
Script para corregir problemas en las tablas de la base de datos
"""

import logging
import mysql.connector
import streamlit as st
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def get_db_config():
    """Obtiene la configuración de la base de datos desde secrets.toml"""
    try:
        # Intentar obtener configuración desde secrets.toml
        if hasattr(st, "secrets") and "db_host" in st.secrets:
            logger.info("Usando configuración de base de datos desde secrets.toml")
            return {
                "host": st.secrets.get("db_host", "localhost"),
                "port": st.secrets.get("db_port", 3306),
                "user": st.secrets.get("db_user", "root"),
                "password": st.secrets.get("db_password", ""),
                "database": st.secrets.get("db_name", "inversoria"),
            }
        else:
            logger.warning(
                "No se encontró configuración de base de datos en secrets.toml, usando valores por defecto"
            )
            return {
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "",
                "database": "inversoria_db",
            }
    except Exception as e:
        logger.error(f"Error obteniendo configuración de BD: {str(e)}")
        return {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "inversoria_db",
        }

def execute_query(connection, query, params=None, fetch=True):
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        cursor = connection.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            results = cursor.fetchall()
            cursor.close()
            return results
        else:
            connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
    except Exception as e:
        logger.error(f"Error ejecutando consulta: {str(e)}")
        logger.error(f"Query: {query}")
        if params:
            logger.error(f"Params: {params}")
        return None

def fix_market_sentiment_table(connection):
    """Corrige problemas en la tabla market_sentiment"""
    logger.info("Corrigiendo problemas en la tabla market_sentiment")
    
    # Verificar si hay registros con valores NULL
    query = """
    SELECT id FROM market_sentiment 
    WHERE symbol IS NULL OR sentiment IS NULL OR score IS NULL OR source IS NULL
    """
    results = execute_query(connection, query)
    
    if results:
        logger.info(f"Encontrados {len(results)} registros con valores NULL en market_sentiment")
        
        # Actualizar registros con valores NULL
        for record in results:
            update_query = """
            UPDATE market_sentiment
            SET 
                symbol = 'SPY',
                sentiment = 'neutral',
                score = 0.5,
                source = 'InversorIA Analytics',
                analysis = 'Análisis de sentimiento de mercado generado por InversorIA Analytics',
                sentiment_date = NOW()
            WHERE id = %s
            """
            affected_rows = execute_query(connection, update_query, params=[record["id"]], fetch=False)
            logger.info(f"Actualizado registro con ID {record['id']}: {affected_rows} filas afectadas")
    else:
        logger.info("No se encontraron registros con valores NULL en market_sentiment")
    
    return True

def fix_market_news_table(connection):
    """Corrige problemas en la tabla market_news"""
    logger.info("Corrigiendo problemas en la tabla market_news")
    
    # Verificar si hay registros con symbol NULL
    query = "SELECT id FROM market_news WHERE symbol IS NULL"
    results = execute_query(connection, query)
    
    if results:
        logger.info(f"Encontrados {len(results)} registros con symbol NULL en market_news")
        
        # Actualizar registros con symbol NULL
        update_query = """
        UPDATE market_news
        SET symbol = 'SPY'
        WHERE symbol IS NULL
        """
        affected_rows = execute_query(connection, update_query, fetch=False)
        logger.info(f"Actualizados {affected_rows} registros con symbol NULL en market_news")
    else:
        logger.info("No se encontraron registros con symbol NULL en market_news")
    
    # Verificar si hay registros con summary vacío
    query = "SELECT id FROM market_news WHERE summary = ''"
    results = execute_query(connection, query)
    
    if results:
        logger.info(f"Encontrados {len(results)} registros con summary vacío en market_news")
        
        # Actualizar registros con summary vacío
        for record in results:
            # Obtener título para generar un resumen
            title_query = "SELECT title FROM market_news WHERE id = %s"
            title_result = execute_query(connection, title_query, params=[record["id"]])
            
            if title_result and title_result[0]["title"]:
                title = title_result[0]["title"]
                summary = f"Resumen generado automáticamente para: {title}"
                
                update_query = """
                UPDATE market_news
                SET summary = %s
                WHERE id = %s
                """
                affected_rows = execute_query(connection, update_query, params=[summary, record["id"]], fetch=False)
                logger.info(f"Actualizado registro con ID {record['id']}: {affected_rows} filas afectadas")
    else:
        logger.info("No se encontraron registros con summary vacío en market_news")
    
    # Verificar si hay registros con url vacía
    query = "SELECT id FROM market_news WHERE url = ''"
    results = execute_query(connection, query)
    
    if results:
        logger.info(f"Encontrados {len(results)} registros con url vacía en market_news")
        
        # Actualizar registros con url vacía
        for record in results:
            # Obtener symbol para generar una URL
            symbol_query = "SELECT symbol FROM market_news WHERE id = %s"
            symbol_result = execute_query(connection, symbol_query, params=[record["id"]])
            
            if symbol_result and symbol_result[0]["symbol"]:
                symbol = symbol_result[0]["symbol"]
                url = f"https://finance.yahoo.com/quote/{symbol}"
                
                update_query = """
                UPDATE market_news
                SET url = %s
                WHERE id = %s
                """
                affected_rows = execute_query(connection, update_query, params=[url, record["id"]], fetch=False)
                logger.info(f"Actualizado registro con ID {record['id']}: {affected_rows} filas afectadas")
    else:
        logger.info("No se encontraron registros con url vacía en market_news")
    
    return True

def fix_email_logs_table(connection):
    """Corrige problemas en la tabla email_logs"""
    logger.info("Corrigiendo problemas en la tabla email_logs")
    
    # Verificar si hay registros con error_message NULL
    query = "SELECT id FROM email_logs WHERE error_message IS NULL"
    results = execute_query(connection, query)
    
    if results:
        logger.info(f"Encontrados {len(results)} registros con error_message NULL en email_logs")
        
        # Actualizar registros con error_message NULL
        update_query = """
        UPDATE email_logs
        SET error_message = ''
        WHERE error_message IS NULL
        """
        affected_rows = execute_query(connection, update_query, fetch=False)
        logger.info(f"Actualizados {affected_rows} registros con error_message NULL en email_logs")
    else:
        logger.info("No se encontraron registros con error_message NULL en email_logs")
    
    return True

def main():
    """Función principal"""
    logger.info("Iniciando corrección de problemas en las tablas de la base de datos")
    
    # Obtener configuración de la base de datos
    config = get_db_config()
    
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**config)
        logger.info(f"Conexión establecida con la base de datos {config['database']}")
        
        # Corregir problemas en las tablas
        fix_market_sentiment_table(connection)
        fix_market_news_table(connection)
        fix_email_logs_table(connection)
        
        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    
    logger.info("Corrección completada")

if __name__ == "__main__":
    main()
