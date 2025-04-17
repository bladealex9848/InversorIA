#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la estructura de las tablas de la base de datos
"""

import mysql.connector
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Credenciales de la base de datos
DB_CONFIG = {
    "host": "190.8.178.74",
    "port": 3306,
    "user": "liceopan_root",
    "password": "@Soporte2020@",
    "database": "liceopan_enki_sincelejo",
}

def check_table_structure(table_name):
    """Verifica la estructura de una tabla"""
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Consultar estructura de la tabla
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        logger.info(f"Estructura de la tabla {table_name}:")
        for column in columns:
            logger.info(f"  {column['Field']} - {column['Type']} - {column['Null']} - {column['Default']}")
        
        # Cerrar conexión
        cursor.close()
        connection.close()
        
        return columns
    except Exception as e:
        logger.error(f"Error verificando estructura de {table_name}: {str(e)}")
        return None

def check_latest_records(table_name, limit=3):
    """Verifica los últimos registros de una tabla"""
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Consultar últimos registros
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}")
        records = cursor.fetchall()
        
        logger.info(f"Últimos {len(records)} registros de la tabla {table_name}:")
        for i, record in enumerate(records, 1):
            logger.info(f"  Registro {i}:")
            for key, value in record.items():
                if isinstance(value, (datetime, bytes)):
                    value = str(value)
                # Limitar la longitud de los valores largos
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                logger.info(f"    {key}: {value}")
        
        # Cerrar conexión
        cursor.close()
        connection.close()
        
        return records
    except Exception as e:
        logger.error(f"Error verificando registros de {table_name}: {str(e)}")
        return None

def main():
    """Función principal"""
    logger.info("Verificando estructura y registros de las tablas")
    
    # Verificar estructura de las tablas
    tables = ["market_sentiment", "market_news", "trading_signals"]
    for table in tables:
        logger.info(f"\n{'='*50}\nVerificando estructura de {table}\n{'='*50}")
        check_table_structure(table)
        
        logger.info(f"\n{'='*50}\nVerificando registros de {table}\n{'='*50}")
        check_latest_records(table)
    
    logger.info("Verificación completada")

if __name__ == "__main__":
    main()
