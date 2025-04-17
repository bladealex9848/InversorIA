#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la estructura de la tabla market_sentiment
"""

import mysql.connector
import streamlit as st
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


def main():
    """Función principal"""
    try:
        # Conectar a la base de datos
        config = get_db_config()
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # Verificar estructura de la tabla market_sentiment
        cursor.execute("DESCRIBE market_sentiment")
        print("Estructura de la tabla market_sentiment:")
        for column in cursor.fetchall():
            print(f"  {column}")

        # Verificar registros en la tabla market_sentiment
        cursor.execute("SELECT * FROM market_sentiment")
        rows = cursor.fetchall()
        print(f"\nRegistros en la tabla market_sentiment: {len(rows)}")

        # Mostrar los primeros 5 registros
        if rows:
            print("\nPrimeros registros:")
            for i, row in enumerate(rows[:5]):
                print(f"  Registro {i+1}: {row}")

        # Cerrar conexión
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
