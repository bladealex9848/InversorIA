#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar las conexiones a la base de datos y al servidor de correo
para el sistema de notificaciones de InversorIA.

Este script verifica:
1. La conexión a la base de datos MariaDB
2. La existencia de las tablas necesarias
3. La conexión al servidor de correo SMTP
"""

import os
import sys
import logging
import smtplib
import mysql.connector
from datetime import datetime
import streamlit as st
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_connections")

# Asegurar que el directorio raíz está en el path
root_dir = Path(__file__).parent.parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

def load_secrets():
    """Carga las credenciales desde secrets.toml o variables de entorno"""
    try:
        # Intentar cargar desde Streamlit secrets
        db_config = {
            "host": st.secrets.get("db_host", os.environ.get("DB_HOST", "localhost")),
            "user": st.secrets.get("db_user", os.environ.get("DB_USER", "")),
            "password": st.secrets.get("db_password", os.environ.get("DB_PASSWORD", "")),
            "database": st.secrets.get("db_name", os.environ.get("DB_NAME", "inversoria")),
            "port": st.secrets.get("db_port", os.environ.get("DB_PORT", 3306)),
        }
        
        email_config = {
            "smtp_server": st.secrets.get("smtp_server", os.environ.get("SMTP_SERVER", "smtp.gmail.com")),
            "smtp_port": st.secrets.get("smtp_port", os.environ.get("SMTP_PORT", 587)),
            "email_user": st.secrets.get("email_user", os.environ.get("EMAIL_USER", "")),
            "email_password": st.secrets.get("email_password", os.environ.get("EMAIL_PASSWORD", "")),
            "email_from": st.secrets.get("email_from", os.environ.get("EMAIL_FROM", "")),
        }
        
        logger.info("Credenciales cargadas desde Streamlit secrets")
        return db_config, email_config
    except Exception as e:
        logger.warning(f"Error cargando secrets de Streamlit: {str(e)}")
        
        # Cargar desde variables de entorno
        db_config = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "user": os.environ.get("DB_USER", ""),
            "password": os.environ.get("DB_PASSWORD", ""),
            "database": os.environ.get("DB_NAME", "inversoria"),
            "port": int(os.environ.get("DB_PORT", 3306)),
        }
        
        email_config = {
            "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.environ.get("SMTP_PORT", 587)),
            "email_user": os.environ.get("EMAIL_USER", ""),
            "email_password": os.environ.get("EMAIL_PASSWORD", ""),
            "email_from": os.environ.get("EMAIL_FROM", ""),
        }
        
        logger.info("Credenciales cargadas desde variables de entorno")
        return db_config, email_config

def test_db_connection(db_config):
    """Prueba la conexión a la base de datos"""
    logger.info("Probando conexión a la base de datos...")
    
    if not db_config.get("user") or not db_config.get("password"):
        logger.error("Faltan credenciales de base de datos")
        return False
    
    try:
        # Intentar conectar a la base de datos
        connection = mysql.connector.connect(**db_config)
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f"Conectado a MariaDB/MySQL versión: {db_info}")
            
            # Verificar la existencia de las tablas
            cursor = connection.cursor()
            
            # Obtener lista de tablas
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            # Verificar tablas requeridas
            required_tables = [
                "trading_signals", 
                "email_logs", 
                "market_sentiment", 
                "market_news",
                "notification_settings"
            ]
            
            missing_tables = [table for table in required_tables if table not in table_names]
            
            if missing_tables:
                logger.warning(f"Faltan las siguientes tablas: {', '.join(missing_tables)}")
                logger.info("Puede crear las tablas ejecutando el script create_tables.sql")
            else:
                logger.info("Todas las tablas requeridas existen en la base de datos")
            
            # Probar inserción y eliminación
            try:
                logger.info("Probando operaciones CRUD...")
                
                # Crear tabla temporal de prueba
                cursor.execute("""
                CREATE TEMPORARY TABLE test_connection (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_value VARCHAR(100),
                    created_at DATETIME
                )
                """)
                
                # Insertar dato de prueba
                cursor.execute(
                    "INSERT INTO test_connection (test_value, created_at) VALUES (%s, %s)",
                    ("Test connection successful", datetime.now())
                )
                connection.commit()
                
                # Verificar inserción
                cursor.execute("SELECT * FROM test_connection")
                result = cursor.fetchone()
                if result:
                    logger.info("Operaciones CRUD exitosas")
                
                logger.info("Prueba de base de datos completada con éxito")
            except Exception as crud_error:
                logger.error(f"Error en operaciones CRUD: {str(crud_error)}")
            
            cursor.close()
            connection.close()
            return True
        
    except mysql.connector.Error as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        return False

def test_email_connection(email_config):
    """Prueba la conexión al servidor de correo"""
    logger.info("Probando conexión al servidor de correo...")
    
    if not email_config.get("email_user") or not email_config.get("email_password"):
        logger.error("Faltan credenciales de correo electrónico")
        return False
    
    try:
        # Verificar si el puerto es 465 (SSL) o 587 (TLS)
        port = email_config.get("smtp_port")
        use_ssl = port == 465
        
        try:
            if use_ssl:
                # Conexión SSL directa
                logger.info("Usando conexión SSL")
                server = smtplib.SMTP_SSL(
                    email_config.get("smtp_server"),
                    port,
                    timeout=10,  # Timeout de 10 segundos
                )
            else:
                # Conexión normal con STARTTLS
                logger.info("Usando conexión con STARTTLS")
                server = smtplib.SMTP(
                    email_config.get("smtp_server"),
                    port,
                    timeout=10,  # Timeout de 10 segundos
                )
                server.starttls()
            
            # Intentar login
            logger.info(f"Iniciando sesión con usuario: {email_config.get('email_user')}")
            server.login(
                email_config.get("email_user"),
                email_config.get("email_password"),
            )
            
            # Si llegamos aquí, la conexión fue exitosa
            logger.info("Conexión al servidor de correo exitosa")
            server.quit()
            return True
            
        except Exception as conn_error:
            logger.error(f"Error conectando al servidor SMTP: {str(conn_error)}")
            return False
        
    except Exception as e:
        logger.error(f"Error en la prueba de correo: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("Iniciando pruebas de conexión...")
    
    # Cargar credenciales
    db_config, email_config = load_secrets()
    
    # Probar conexión a la base de datos
    db_success = test_db_connection(db_config)
    
    # Probar conexión al servidor de correo
    email_success = test_email_connection(email_config)
    
    # Resumen de resultados
    logger.info("\n" + "="*50)
    logger.info("RESUMEN DE PRUEBAS DE CONEXIÓN")
    logger.info("="*50)
    logger.info(f"Base de datos: {'✅ EXITOSA' if db_success else '❌ FALLIDA'}")
    logger.info(f"Servidor de correo: {'✅ EXITOSA' if email_success else '❌ FALLIDA'}")
    logger.info("="*50)
    
    if not db_success or not email_success:
        logger.warning("Algunas pruebas fallaron. Revise los mensajes de error anteriores.")
    else:
        logger.info("Todas las pruebas completadas con éxito.")

if __name__ == "__main__":
    main()
