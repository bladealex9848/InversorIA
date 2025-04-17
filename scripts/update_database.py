#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar la estructura de la base de datos
para el sistema de notificaciones de InversorIA.

Este script:
1. Conecta a la base de datos usando las credenciales de secrets.toml
2. Ejecuta el script SQL para actualizar la estructura de la tabla trading_signals
3. Verifica que la estructura se haya actualizado correctamente
"""

import os
import sys
import logging
import mysql.connector
from datetime import datetime
import streamlit as st
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
                "database": "inversoria",
            }
    except Exception as e:
        logger.error(f"Error obteniendo configuración de BD: {str(e)}")
        return {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "inversoria",
        }

def update_database():
    """Actualiza la estructura de la base de datos"""
    try:
        # Obtener configuración de la base de datos
        config = get_db_config()
        
        # Conectar a la base de datos
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f"Conectado a MariaDB/MySQL versión: {db_info}")
            
            # Leer el script SQL
            script_path = Path(__file__).parent.parent / "sql" / "update_trading_signals.sql"
            
            if not script_path.exists():
                logger.error(f"No se encontró el archivo SQL en {script_path}")
                return False
            
            with open(script_path, "r") as f:
                sql_script = f.read()
            
            # Ejecutar el script SQL
            cursor = connection.cursor()
            
            # Dividir el script en comandos individuales
            commands = sql_script.split(';')
            
            for command in commands:
                command = command.strip()
                if command:
                    try:
                        cursor.execute(command)
                        connection.commit()
                    except Exception as e:
                        logger.warning(f"Error ejecutando comando SQL: {str(e)}")
                        logger.warning(f"Comando: {command}")
            
            # Verificar la estructura actualizada
            cursor.execute("DESCRIBE trading_signals")
            columns = cursor.fetchall()
            column_names = [column[0] for column in columns]
            
            # Verificar que se hayan añadido los nuevos campos
            required_fields = [
                "entry_price", "stop_loss", "target_price", "risk_reward", "setup_type",
                "technical_analysis", "support_level", "resistance_level", "rsi", "trend",
                "trend_strength", "volatility", "options_signal", "options_analysis",
                "trading_specialist_signal", "trading_specialist_confidence", "sentiment",
                "sentiment_score", "latest_news", "news_source", "additional_news",
                "expert_analysis", "recommendation", "mtf_analysis", "daily_trend",
                "weekly_trend", "monthly_trend", "bullish_indicators", "bearish_indicators",
                "is_high_confidence"
            ]
            
            missing_fields = [field for field in required_fields if field not in column_names]
            
            if missing_fields:
                logger.warning(f"Faltan los siguientes campos: {', '.join(missing_fields)}")
                return False
            else:
                logger.info("Todos los campos requeridos existen en la tabla trading_signals")
                return True
            
    except Exception as e:
        logger.error(f"Error actualizando la base de datos: {str(e)}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            logger.info("Conexión cerrada")

def update_database_manager():
    """Actualiza el método save_signal en database_utils.py"""
    try:
        # Ruta al archivo database_utils.py
        file_path = Path(__file__).parent.parent / "database_utils.py"
        
        if not file_path.exists():
            logger.error(f"No se encontró el archivo database_utils.py en {file_path}")
            return False
        
        # Leer el archivo
        with open(file_path, "r") as f:
            content = f.read()
        
        # Buscar el método save_signal
        if "def save_signal(self, signal_data):" in content:
            # Reemplazar el método save_signal
            start_marker = "    def save_signal(self, signal_data):"
            end_marker = "        return None"
            
            new_method = """    def save_signal(self, signal_data):
        \"\"\"Guarda una señal de trading en la base de datos\"\"\"
        try:
            if self.connect():
                cursor = self.connection.cursor()

                # Preparar consulta con todos los campos
                query = \"\"\"INSERT INTO trading_signals
                          (symbol, price, direction, confidence_level, timeframe,
                           strategy, category, analysis, created_at,
                           entry_price, stop_loss, target_price, risk_reward, setup_type,
                           technical_analysis, support_level, resistance_level, rsi, trend, trend_strength,
                           volatility, options_signal, options_analysis, trading_specialist_signal,
                           trading_specialist_confidence, sentiment, sentiment_score, latest_news,
                           news_source, additional_news, expert_analysis, recommendation, mtf_analysis,
                           daily_trend, weekly_trend, monthly_trend, bullish_indicators, bearish_indicators,
                           is_high_confidence)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\"\"\"

                # Preparar datos
                params = (
                    signal_data.get("symbol", ""),
                    signal_data.get("price", 0.0),
                    signal_data.get("direction", "NEUTRAL"),
                    signal_data.get("confidence_level", "Baja"),
                    signal_data.get("timeframe", "Corto Plazo"),
                    signal_data.get("strategy", "Análisis Técnico"),
                    signal_data.get("category", "General"),
                    signal_data.get("analysis", ""),
                    signal_data.get("created_at", datetime.now()),
                    signal_data.get("entry_price", 0.0),
                    signal_data.get("stop_loss", 0.0),
                    signal_data.get("target_price", 0.0),
                    signal_data.get("risk_reward", 0.0),
                    signal_data.get("setup_type", ""),
                    signal_data.get("technical_analysis", ""),
                    signal_data.get("support_level", 0.0),
                    signal_data.get("resistance_level", 0.0),
                    signal_data.get("rsi", 0.0),
                    signal_data.get("trend", ""),
                    signal_data.get("trend_strength", ""),
                    signal_data.get("volatility", 0.0),
                    signal_data.get("options_signal", ""),
                    signal_data.get("options_analysis", ""),
                    signal_data.get("trading_specialist_signal", ""),
                    signal_data.get("trading_specialist_confidence", ""),
                    signal_data.get("sentiment", ""),
                    signal_data.get("sentiment_score", 0.0),
                    signal_data.get("latest_news", ""),
                    signal_data.get("news_source", ""),
                    signal_data.get("additional_news", ""),
                    signal_data.get("expert_analysis", ""),
                    signal_data.get("recommendation", ""),
                    signal_data.get("mtf_analysis", ""),
                    signal_data.get("daily_trend", ""),
                    signal_data.get("weekly_trend", ""),
                    signal_data.get("monthly_trend", ""),
                    signal_data.get("bullish_indicators", ""),
                    signal_data.get("bearish_indicators", ""),
                    signal_data.get("is_high_confidence", False),
                )

                # Ejecutar consulta
                cursor.execute(query, params)
                self.connection.commit()

                # Obtener ID insertado
                signal_id = cursor.lastrowid
                cursor.close()
                self.disconnect()

                logger.info(f"Señal guardada con ID: {signal_id}")
                return signal_id
            else:
                logger.warning(
                    "No se pudo conectar a la base de datos para guardar la señal"
                )
                return None
        except Exception as e:
            logger.error(f"Error guardando señal: {str(e)}")
            return None"""
            
            # Encontrar el inicio y fin del método actual
            start_index = content.find(start_marker)
            if start_index == -1:
                logger.error("No se encontró el método save_signal en database_utils.py")
                return False
            
            # Buscar el final del método
            end_index = content.find(end_marker, start_index)
            if end_index == -1:
                logger.error("No se pudo determinar el final del método save_signal")
                return False
            
            # Ajustar el índice final para incluir la línea completa
            end_index = content.find("\n", end_index) + 1
            
            # Reemplazar el método
            new_content = content[:start_index] + new_method + content[end_index:]
            
            # Guardar el archivo
            with open(file_path, "w") as f:
                f.write(new_content)
            
            logger.info("Método save_signal actualizado en database_utils.py")
            return True
        else:
            logger.error("No se encontró el método save_signal en database_utils.py")
            return False
    except Exception as e:
        logger.error(f"Error actualizando database_utils.py: {str(e)}")
        return False

if __name__ == "__main__":
    print("Actualizando la estructura de la base de datos...")
    if update_database():
        print("✅ Base de datos actualizada correctamente")
    else:
        print("❌ Error actualizando la base de datos")
    
    print("\nActualizando el método save_signal en database_utils.py...")
    if update_database_manager():
        print("✅ Método save_signal actualizado correctamente")
    else:
        print("❌ Error actualizando el método save_signal")
