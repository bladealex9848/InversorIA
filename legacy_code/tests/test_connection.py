import streamlit as st
import mysql.connector
import smtplib
import logging
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_connection")

def test_db_connection():
    """Prueba la conexión a la base de datos"""
    try:
        # Obtener credenciales desde secrets.toml
        db_config = {
            "host": st.secrets.get("db_host", ""),
            "user": st.secrets.get("db_user", ""),
            "password": st.secrets.get("db_password", ""),
            "database": st.secrets.get("db_name", ""),
        }
        
        # Verificar que hay credenciales
        if not db_config["host"] or not db_config["user"] or not db_config["password"] or not db_config["database"]:
            logger.error("Faltan credenciales de base de datos en secrets.toml")
            return False
        
        # Intentar conectar
        logger.info(f"Conectando a la base de datos: {db_config['host']}/{db_config['database']}")
        connection = mysql.connector.connect(**db_config)
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f"Conexión exitosa a MySQL versión: {db_info}")
            
            # Probar una consulta simple
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            logger.info(f"MySQL versión: {version[0]}")
            
            # Verificar si existen las tablas necesarias
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            table_names = [t[0] for t in tables]
            
            required_tables = ["trading_signals", "email_logs", "market_sentiment", "market_news"]
            missing_tables = [t for t in required_tables if t not in table_names]
            
            if missing_tables:
                logger.warning(f"Faltan las siguientes tablas: {', '.join(missing_tables)}")
                logger.info("Puede crear las tablas ejecutando el script SQL en sql/create_tables.sql")
            else:
                logger.info("Todas las tablas requeridas existen")
            
            cursor.close()
            connection.close()
            logger.info("Conexión cerrada")
            return True
        else:
            logger.error("No se pudo conectar a la base de datos")
            return False
    except mysql.connector.Error as e:
        logger.error(f"Error de MySQL: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return False

def test_email_connection():
    """Prueba la conexión al servidor de correo"""
    try:
        # Obtener credenciales desde secrets.toml
        email_config = {
            "smtp_server": st.secrets.get("smtp_server", "smtp.gmail.com"),
            "smtp_port": st.secrets.get("smtp_port", 587),
            "email_user": st.secrets.get("email_user", ""),
            "email_password": st.secrets.get("email_password", ""),
            "email_from": st.secrets.get("email_from", ""),
        }
        
        # Verificar que hay credenciales
        if not email_config["email_user"] or not email_config["email_password"]:
            logger.error("Faltan credenciales de correo en secrets.toml")
            return False
        
        # Intentar conectar al servidor SMTP
        logger.info(f"Conectando al servidor SMTP: {email_config['smtp_server']}:{email_config['smtp_port']}")
        
        # Verificar si el puerto es 465 (SSL) o 587 (TLS)
        port = email_config["smtp_port"]
        use_ssl = port == 465
        
        try:
            if use_ssl:
                # Conexión SSL directa
                logger.info("Usando conexión SSL")
                server = smtplib.SMTP_SSL(
                    email_config["smtp_server"],
                    port,
                    timeout=10,  # Timeout de 10 segundos
                )
            else:
                # Conexión normal con STARTTLS
                logger.info("Usando conexión con STARTTLS")
                server = smtplib.SMTP(
                    email_config["smtp_server"],
                    port,
                    timeout=10,  # Timeout de 10 segundos
                )
                server.starttls()
            
            # Intentar login
            logger.info(f"Iniciando sesión con usuario: {email_config['email_user']}")
            server.login(
                email_config["email_user"],
                email_config["email_password"],
            )
            
            logger.info("Conexión y autenticación exitosas")
            server.quit()
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {str(e)}")
            logger.error("Verifica tu usuario y contraseña. Si usas Gmail, asegúrate de usar una 'Clave de aplicación'.")
            return False
        except Exception as e:
            logger.error(f"Error conectando al servidor SMTP: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Prueba de conexión a la base de datos ===")
    db_success = test_db_connection()
    print(f"\nResultado: {'✅ ÉXITO' if db_success else '❌ ERROR'}")
    
    print("\n=== Prueba de conexión al servidor de correo ===")
    email_success = test_email_connection()
    print(f"\nResultado: {'✅ ÉXITO' if email_success else '❌ ERROR'}")
    
    if db_success and email_success:
        print("\n✅ Todas las pruebas exitosas. El sistema está listo para funcionar.")
    else:
        print("\n❌ Hay errores en la configuración. Revisa los mensajes anteriores.")
