#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar los campos vacíos o nulos en las tablas de la base de datos
"""

import mysql.connector
import streamlit as st
import logging
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

def check_table_fields(connection, table_name):
    """Verifica los campos vacíos o nulos en una tabla"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Obtener estructura de la tabla
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        logger.info(f"Estructura de la tabla {table_name}:")
        for column in columns:
            logger.info(f"  {column['Field']} - {column['Type']} - {column['Null']} - {column['Default']}")
        
        # Verificar campos vacíos o nulos
        logger.info(f"\nCampos vacíos o nulos en la tabla {table_name}:")
        for column in columns:
            column_name = column['Field']
            column_type = column['Type'].lower()
            
            # Verificar valores NULL
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name} WHERE {column_name} IS NULL")
            null_count = cursor.fetchone()['count']
            
            # Verificar valores vacíos para campos de texto
            empty_count = 0
            if 'char' in column_type or 'text' in column_type:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name} WHERE {column_name} = ''")
                empty_count = cursor.fetchone()['count']
            
            if null_count > 0 or empty_count > 0:
                logger.warning(f"  {column_name}: {null_count} valores NULL, {empty_count} valores vacíos")
        
        # Obtener los últimos 3 registros
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 3")
        records = cursor.fetchall()
        
        logger.info(f"\nÚltimos 3 registros de la tabla {table_name}:")
        for i, record in enumerate(records, 1):
            logger.info(f"  Registro {i}:")
            for key, value in record.items():
                if isinstance(value, (datetime, bytes)):
                    value = str(value)
                logger.info(f"    {key}: {value}")
        
        cursor.close()
        return True
    
    except Exception as e:
        logger.error(f"Error verificando campos en la tabla {table_name}: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("Iniciando verificación de campos en las tablas")
    
    # Obtener configuración de la base de datos
    config = get_db_config()
    
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**config)
        logger.info(f"Conexión establecida con la base de datos {config['database']}")
        
        # Verificar campos en las tablas
        tables = ["market_news", "trading_signals", "market_sentiment"]
        for table in tables:
            logger.info(f"\n{'='*50}\nVerificando tabla {table}\n{'='*50}")
            check_table_fields(connection, table)
        
        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    
    logger.info("Verificación completada")

if __name__ == "__main__":
    main()
