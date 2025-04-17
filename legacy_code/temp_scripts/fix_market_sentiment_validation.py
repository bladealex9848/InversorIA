"""
Script para corregir la validación del sentimiento de mercado (una vez al día)
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
                "database": "liceopan_enki_sincelejo",
            }
    except Exception as e:
        logger.error(f"Error obteniendo configuración de BD: {str(e)}")
        return {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "liceopan_enki_sincelejo",
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

def check_market_sentiment_today(connection):
    """Verifica si ya existe un registro de sentimiento de mercado para hoy"""
    today = datetime.now().strftime("%Y-%m-%d")
    query = "SELECT * FROM market_sentiment WHERE DATE(created_at) = %s"
    params = [today]
    results = execute_query(connection, query, params)
    
    if results and len(results) > 0:
        logger.info(f"Ya existe un registro de sentimiento de mercado para hoy ({today}): {len(results)} registros")
        return True, results
    else:
        logger.info(f"No existe un registro de sentimiento de mercado para hoy ({today})")
        return False, None

def modify_database_utils(connection):
    """Modifica el archivo database_utils.py para validar si ya existe un registro de sentimiento de mercado para hoy"""
    # Verificar si la función save_market_sentiment existe en database_utils.py
    try:
        with open("database_utils.py", "r") as file:
            content = file.read()
            
            # Buscar la función save_market_sentiment
            if "def save_market_sentiment" in content:
                logger.info("Función save_market_sentiment encontrada en database_utils.py")
                
                # Verificar si ya tiene la validación
                if "# Verificar si ya existe un registro para hoy" in content:
                    logger.info("La validación ya existe en la función save_market_sentiment")
                    return False
                
                # Buscar el inicio de la función
                start_index = content.find("def save_market_sentiment")
                if start_index == -1:
                    logger.error("No se pudo encontrar el inicio de la función save_market_sentiment")
                    return False
                
                # Buscar el inicio del cuerpo de la función
                body_start = content.find(":", start_index)
                if body_start == -1:
                    logger.error("No se pudo encontrar el inicio del cuerpo de la función save_market_sentiment")
                    return False
                
                # Buscar la primera línea después de la definición de la función
                next_line_index = content.find("\n", body_start) + 1
                if next_line_index == 0:
                    logger.error("No se pudo encontrar la primera línea después de la definición de la función")
                    return False
                
                # Insertar la validación
                validation_code = """
        # Verificar si ya existe un registro para hoy
        today = datetime.now().strftime("%Y-%m-%d")
        check_query = "SELECT id FROM market_sentiment WHERE DATE(created_at) = %s"
        existing_record = self.execute_query(check_query, params=[today], fetch=True)
        
        if existing_record and len(existing_record) > 0:
            logger.info(f"Ya existe un registro de sentimiento de mercado para hoy ({today}). No se guardará otro.")
            return existing_record[0]["id"]
                
"""
                
                # Insertar la validación después de la primera línea
                new_content = content[:next_line_index] + validation_code + content[next_line_index:]
                
                # Guardar el archivo modificado
                with open("database_utils.py", "w") as file:
                    file.write(new_content)
                
                logger.info("Archivo database_utils.py modificado correctamente")
                return True
            else:
                logger.error("Función save_market_sentiment no encontrada en database_utils.py")
                return False
    except Exception as e:
        logger.error(f"Error modificando database_utils.py: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("Iniciando corrección de validación de sentimiento de mercado")
    
    # Obtener configuración de la base de datos
    config = get_db_config()
    
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**config)
        logger.info(f"Conexión establecida con la base de datos {config['database']}")
        
        # Verificar si ya existe un registro de sentimiento de mercado para hoy
        exists, records = check_market_sentiment_today(connection)
        
        # Modificar database_utils.py para validar si ya existe un registro
        modified = modify_database_utils(connection)
        
        if modified:
            logger.info("Se ha añadido la validación para guardar el sentimiento de mercado solo una vez al día")
        
        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    
    logger.info("Corrección completada")

if __name__ == "__main__":
    main()
