"""
InversorIA Pro - Utilidades de Base de Datos
--------------------------------------------
Este archivo contiene clases y funciones para gestionar la conexión y operaciones con la base de datos.
"""

import logging
import mysql.connector
from datetime import datetime
import streamlit as st
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestiona la conexión y operaciones con la base de datos"""

    def __init__(self):
        """Inicializa el gestor de base de datos"""
        self.connection = None
        self.config = self._get_db_config()

    def _get_db_config(self):
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

    def connect(self):
        """Establece conexión con la base de datos"""
        try:
            # Primero intentar conectar sin especificar la base de datos
            config_without_db = self.config.copy()
            if "database" in config_without_db:
                del config_without_db["database"]

            # Conectar al servidor MySQL
            temp_connection = mysql.connector.connect(**config_without_db)
            temp_cursor = temp_connection.cursor()

            # Verificar si la base de datos existe
            temp_cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in temp_cursor]

            # Si la base de datos no existe, crearla
            if self.config["database"] not in databases:
                logger.info(f"Creando base de datos {self.config['database']}")
                temp_cursor.execute(f"CREATE DATABASE {self.config['database']}")
                temp_connection.commit()

                # Crear tablas necesarias
                temp_cursor.execute(f"USE {self.config['database']}")

                # Tabla de señales de trading con estructura mejorada
                temp_cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    direction ENUM('CALL', 'PUT', 'NEUTRAL') NOT NULL,
                    confidence_level ENUM('Alta', 'Media', 'Baja') NOT NULL,
                    timeframe VARCHAR(50) NOT NULL,
                    strategy VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    analysis TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_symbol (symbol),
                    INDEX idx_direction (direction),
                    INDEX idx_confidence (confidence_level),
                    INDEX idx_category (category),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                )

                # Tabla de registro de correos enviados
                temp_cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS email_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    recipients TEXT NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    content_summary TEXT,
                    signals_included TEXT,
                    status ENUM('sent', 'failed') NOT NULL,
                    error_message TEXT,
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_status (status),
                    INDEX idx_sent_at (sent_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                )

                # Tabla de sentimiento de mercado con estructura mejorada
                temp_cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS market_sentiment (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    overall ENUM('Alcista', 'Bajista', 'Neutral') NOT NULL,
                    vix VARCHAR(50),
                    sp500_trend VARCHAR(100),
                    technical_indicators TEXT,
                    volume VARCHAR(100),
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE INDEX idx_date (date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                )

                # Tabla de noticias de mercado
                temp_cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS market_news (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    summary TEXT,
                    source VARCHAR(100),
                    url VARCHAR(255),
                    news_date DATETIME,
                    impact ENUM('Alto', 'Medio', 'Bajo') DEFAULT 'Medio',
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_news_date (news_date),
                    INDEX idx_impact (impact)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                )

            # Cerrar conexión temporal
            temp_cursor.close()
            temp_connection.close()

            # Conectar a la base de datos
            self.connection = mysql.connector.connect(**self.config)
            logger.info(
                f"Conexión establecida con la base de datos {self.config['database']}"
            )
            return True
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {str(e)}")
            return False

    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def execute_query(self, query, params=None, fetch=True):
        """Ejecuta una consulta SQL y devuelve los resultados"""
        results = []
        try:
            if self.connect():
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(query, params or [])

                if fetch:
                    # Obtener resultados como diccionarios
                    results = cursor.fetchall()

                    # Si los resultados no son diccionarios, convertirlos
                    if results and not isinstance(results[0], dict):
                        # Obtener nombres de columnas
                        column_names = [desc[0] for desc in cursor.description]

                        # Convertir cada fila a diccionario
                        dict_results = []
                        for row in results:
                            row_dict = {}
                            for i, value in enumerate(row):
                                if i < len(column_names):
                                    row_dict[column_names[i]] = value
                            dict_results.append(row_dict)
                        results = dict_results
                else:
                    # Para operaciones de escritura, hacer commit
                    self.connection.commit()
                    results = cursor.lastrowid

                cursor.close()
                self.disconnect()
                return results
            else:
                logger.warning("No se pudo conectar a la base de datos")
                return [] if fetch else None
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {str(e)}")
            return [] if fetch else None

    def get_signals(self, days_back=7, categories=None, confidence_levels=None):
        """Obtiene señales de trading filtradas"""
        query = """SELECT * FROM trading_signals
                  WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"""
        params = [days_back]

        # Añadir filtros adicionales
        if categories and "Todas" not in categories:
            placeholders = ", ".join(["%s"] * len(categories))
            query += f" AND category IN ({placeholders})"
            params.extend(categories)

        if confidence_levels and len(confidence_levels) > 0:
            placeholders = ", ".join(["%s"] * len(confidence_levels))
            query += f" AND confidence_level IN ({placeholders})"
            params.extend(confidence_levels)

        query += " ORDER BY created_at DESC"

        return self.execute_query(query, params)

    def get_detailed_analysis(self, symbol):
        """Obtiene análisis detallado para un símbolo específico"""
        query = """SELECT * FROM trading_signals
                  WHERE symbol = %s
                  ORDER BY created_at DESC
                  LIMIT 1"""
        params = [symbol]

        return self.execute_query(query, params)

    def save_signal(self, signal_data):
        """Guarda una señal de trading en la base de datos con todos los campos disponibles"""
        try:
            if self.connect():
                cursor = self.connection.cursor()

                # Preparar consulta con todos los campos de la tabla
                query = """INSERT INTO trading_signals
                          (symbol, price, entry_price, stop_loss, target_price, risk_reward,
                           direction, confidence_level, timeframe, strategy, setup_type,
                           category, analysis, technical_analysis, support_level, resistance_level,
                           rsi, trend, trend_strength, volatility, options_signal, options_analysis,
                           trading_specialist_signal, trading_specialist_confidence, sentiment,
                           sentiment_score, latest_news, news_source, additional_news, expert_analysis,
                           recommendation, mtf_analysis, daily_trend, weekly_trend, monthly_trend,
                           bullish_indicators, bearish_indicators, is_high_confidence, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                  %s, %s, %s, %s, %s, %s, %s)"""

                # Preparar datos con todos los campos
                params = (
                    signal_data.get("symbol", ""),
                    signal_data.get("price", 0.0),
                    signal_data.get("entry_price", 0.0),
                    signal_data.get("stop_loss", 0.0),
                    signal_data.get("target_price", 0.0),
                    signal_data.get("risk_reward", 0.0),
                    signal_data.get("direction", "NEUTRAL"),
                    signal_data.get("confidence_level", "Baja"),
                    signal_data.get("timeframe", "Corto Plazo"),
                    signal_data.get("strategy", "Análisis Técnico"),
                    signal_data.get("setup_type", ""),
                    signal_data.get("category", "General"),
                    signal_data.get("analysis", ""),
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
                    signal_data.get("created_at", datetime.now()),
                )

                # Ejecutar consulta
                cursor.execute(query, params)
                self.connection.commit()

                # Obtener ID insertado
                signal_id = cursor.lastrowid
                cursor.close()
                self.disconnect()

                logger.info(
                    f"Señal guardada con ID: {signal_id} para símbolo: {signal_data.get('symbol', '')}"
                )
                return signal_id
            else:
                logger.warning(
                    "No se pudo conectar a la base de datos para guardar la señal"
                )
                return None
        except Exception as e:
            logger.error(f"Error guardando señal: {str(e)}")
            return None

    def log_email_sent(self, email_data):
        """Registra el envío de un correo electrónico"""
        query = """INSERT INTO email_logs
                  (recipients, subject, content_summary, signals_included, status, error_message, sent_at)
                  VALUES (%s, %s, %s, %s, %s, %s, NOW())"""

        params = (
            email_data.get("recipients", ""),
            email_data.get("subject", ""),
            email_data.get("content_summary", ""),
            email_data.get("signals_included", ""),
            email_data.get("status", "sent"),
            email_data.get("error_message", ""),
        )

        return self.execute_query(query, params, fetch=False)

    def save_market_sentiment(self, sentiment_data):
        """Guarda datos de sentimiento de mercado"""
        try:
            if self.connect():
                cursor = self.connection.cursor()

                # Preparar consulta
                query = """INSERT INTO market_sentiment
                          (date, overall, vix, sp500_trend, technical_indicators, volume, notes, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""

                # Preparar datos
                params = (
                    sentiment_data.get("date", datetime.now().date()),
                    sentiment_data.get("overall", "Neutral"),
                    sentiment_data.get("vix", "N/A"),
                    sentiment_data.get("sp500_trend", "N/A"),
                    sentiment_data.get("technical_indicators", "N/A"),
                    sentiment_data.get("volume", "N/A"),
                    sentiment_data.get("notes", ""),
                )

                # Ejecutar consulta
                cursor.execute(query, params)
                self.connection.commit()

                # Obtener ID insertado
                sentiment_id = cursor.lastrowid
                cursor.close()
                self.disconnect()

                return sentiment_id
            else:
                logger.warning(
                    "No se pudo conectar a la base de datos para guardar el sentimiento"
                )
                return None
        except Exception as e:
            logger.error(f"Error guardando sentimiento: {str(e)}")
            return None

    def get_market_sentiment(self, days_back=7):
        """Obtiene datos de sentimiento de mercado"""
        query = """SELECT * FROM market_sentiment
                  WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                  ORDER BY date DESC"""
        params = [days_back]

        return self.execute_query(query, params)

    def save_market_news(self, news_data):
        """Guarda noticias de mercado"""
        try:
            if self.connect():
                cursor = self.connection.cursor()

                # Preparar consulta
                query = """INSERT INTO market_news
                          (title, summary, source, url, news_date, impact, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, NOW())"""

                # Preparar datos
                params = (
                    news_data.get("title", ""),
                    news_data.get("summary", ""),
                    news_data.get("source", ""),
                    news_data.get("url", ""),
                    news_data.get("news_date", datetime.now()),
                    news_data.get("impact", "Medio"),
                )

                # Ejecutar consulta
                cursor.execute(query, params)
                self.connection.commit()

                # Obtener ID insertado
                news_id = cursor.lastrowid
                cursor.close()
                self.disconnect()

                return news_id
            else:
                logger.warning(
                    "No se pudo conectar a la base de datos para guardar la noticia"
                )
                return None
        except Exception as e:
            logger.error(f"Error guardando noticia: {str(e)}")
            return None

    def get_market_news(self, days_back=7):
        """Obtiene noticias de mercado"""
        query = """SELECT * FROM market_news
                  WHERE news_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
                  ORDER BY news_date DESC"""
        params = [days_back]

        return self.execute_query(query, params)
