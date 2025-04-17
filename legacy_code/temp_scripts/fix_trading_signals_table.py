"""
Script para actualizar la estructura de la tabla trading_signals
y añadir un valor por defecto al campo signal_date
"""

import mysql.connector
import streamlit as st
from datetime import datetime
import logging

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
        # Intentar obtener configuración desde secrets.toml con los nombres de variables correctos
        if hasattr(st, "secrets") and "db_host" in st.secrets:
            logger.info("Usando configuración de base de datos desde secrets.toml")
            return {
                "host": st.secrets.get("db_host", "localhost"),
                "port": st.secrets.get("db_port", 3306),
                "user": st.secrets.get("db_user", "root"),
                "password": st.secrets.get("db_password", ""),
                "database": st.secrets.get("db_name", "inversoria"),
            }
        # Intentar con nombres alternativos
        elif hasattr(st, "secrets") and "mysql_host" in st.secrets:
            logger.info(
                "Usando configuración alternativa de base de datos desde secrets.toml"
            )
            return {
                "host": st.secrets.get("mysql_host", "localhost"),
                "port": st.secrets.get("mysql_port", 3306),
                "user": st.secrets.get("mysql_user", "root"),
                "password": st.secrets.get("mysql_password", ""),
                "database": st.secrets.get("mysql_database", "inversoria"),
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

def check_column_exists(connection, table, column):
    """Verifica si una columna existe en una tabla"""
    query = f"SHOW COLUMNS FROM {table} LIKE %s"
    params = [column]
    results = execute_query(connection, query, params)
    return results and len(results) > 0

def add_signal_date_column(connection):
    """Añade la columna signal_date a la tabla trading_signals si no existe"""
    if not check_column_exists(connection, "trading_signals", "signal_date"):
        logger.info("Añadiendo columna signal_date a la tabla trading_signals")
        query = """
        ALTER TABLE trading_signals
        ADD COLUMN signal_date DATE DEFAULT CURRENT_DATE
        """
        result = execute_query(connection, query, fetch=False)
        if result is not None:
            logger.info("✅ Columna signal_date añadida correctamente")
        else:
            logger.error("❌ Error añadiendo columna signal_date")
    else:
        logger.info("La columna signal_date ya existe en la tabla trading_signals")
        # Verificar si la columna tiene un valor por defecto
        query = """
        SELECT COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'trading_signals'
        AND COLUMN_NAME = 'signal_date'
        """
        result = execute_query(connection, query)
        if result and result[0]["COLUMN_DEFAULT"] is None:
            logger.info("Modificando columna signal_date para añadir valor por defecto")
            query = """
            ALTER TABLE trading_signals
            MODIFY COLUMN signal_date DATE DEFAULT CURRENT_DATE
            """
            result = execute_query(connection, query, fetch=False)
            if result is not None:
                logger.info("✅ Columna signal_date modificada correctamente")
            else:
                logger.error("❌ Error modificando columna signal_date")
        else:
            logger.info("La columna signal_date ya tiene un valor por defecto")

def update_existing_records(connection):
    """Actualiza los registros existentes para establecer signal_date = created_at"""
    logger.info("Actualizando registros existentes")
    query = """
    UPDATE trading_signals
    SET signal_date = DATE(created_at)
    WHERE signal_date IS NULL
    """
    result = execute_query(connection, query, fetch=False)
    if result is not None:
        logger.info(f"✅ {result} registros actualizados correctamente")
    else:
        logger.error("❌ Error actualizando registros existentes")

def main():
    """Función principal"""
    logger.info("Iniciando actualización de la tabla trading_signals")
    
    # Obtener configuración de la base de datos
    config = get_db_config()
    
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**config)
        logger.info(f"Conexión establecida con la base de datos {config['database']}")
        
        # Añadir columna signal_date
        add_signal_date_column(connection)
        
        # Actualizar registros existentes
        update_existing_records(connection)
        
        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    
    logger.info("Actualización completada")

if __name__ == "__main__":
    main()
