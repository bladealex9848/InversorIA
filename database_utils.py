"""
InversorIA Pro - Utilidades de Base de Datos
--------------------------------------------
Este archivo contiene clases y funciones para gestionar la conexión y operaciones con la base de datos.
"""

import logging
import mysql.connector
import decimal
import json
import csv
import os
from datetime import datetime
import streamlit as st
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestiona la conexión y operaciones con la base de datos"""

    def __init__(self):
        """Inicializa el gestor de base de datos"""
        self.connection: Optional[mysql.connector.MySQLConnection] = None
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

    def connect(self) -> bool:
        """Establece conexión con la base de datos

        Returns:
            bool: True si la conexión se estableció correctamente, False en caso contrario
        """
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
            logger.debug("Conexión a la base de datos cerrada")

    def begin_transaction(self) -> bool:
        """Inicia una transacción en la base de datos

        Returns:
            bool: True si se inició la transacción correctamente, False en caso contrario
        """
        try:
            if self.connect():
                # Desactivar autocommit para iniciar transacción
                self.connection.autocommit = False
                logger.info("Transacción iniciada")
                return True
            else:
                logger.error("No se pudo iniciar la transacción: fallo en la conexión")
                return False
        except Exception as e:
            logger.error(f"Error iniciando transacción: {str(e)}")
            return False

    def commit_transaction(self) -> bool:
        """Confirma una transacción en la base de datos

        Returns:
            bool: True si se confirmó la transacción correctamente, False en caso contrario
        """
        try:
            if self.connection and self.connection.is_connected():
                self.connection.commit()
                logger.info("Transacción confirmada")
                self.disconnect()
                return True
            else:
                logger.error(
                    "No se pudo confirmar la transacción: no hay conexión activa"
                )
                return False
        except Exception as e:
            logger.error(f"Error confirmando transacción: {str(e)}")
            return False

    def rollback_transaction(self) -> bool:
        """Revierte una transacción en la base de datos

        Returns:
            bool: True si se revirtió la transacción correctamente, False en caso contrario
        """
        try:
            if self.connection and self.connection.is_connected():
                self.connection.rollback()
                logger.info("Transacción revertida")
                self.disconnect()
                return True
            else:
                logger.error(
                    "No se pudo revertir la transacción: no hay conexión activa"
                )
                return False
        except Exception as e:
            logger.error(f"Error revirtiendo transacción: {str(e)}")
            return False

    def clean_text_data(self, text: Any) -> str:
        """Limpia datos de texto para almacenarlos en la base de datos

        Args:
            text (Any): Texto a limpiar

        Returns:
            str: Texto limpio
        """
        if not text:
            return ""

        if not isinstance(text, str):
            text = str(text)

        # Eliminar caracteres especiales problemáticos para SQL
        text = text.replace("'", "'")
        text = text.replace('"', '"')
        text = text.replace("\\n", " ")
        text = text.replace("\\r", " ")
        text = text.replace("\\t", " ")

        # Eliminar espacios múltiples
        import re

        text = re.sub(r"\s+", " ", text)

        # Limitar longitud para evitar problemas con campos TEXT
        max_length = 65000  # Tamaño seguro para campos TEXT
        if len(text) > max_length:
            text = text[:max_length] + "..."

        return text.strip()

    def validate_url(self, url: Any) -> str:
        """Valida una URL

        Args:
            url (Any): URL a validar

        Returns:
            str: URL validada o cadena vacía si no es válida
        """
        if not url:
            return ""

        if not isinstance(url, str):
            url = str(url)

        # Validar formato básico de URL
        import re

        url_pattern = re.compile(
            r"^(?:http|https)://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
            r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if url_pattern.match(url):
            # Limitar longitud para evitar problemas con campos VARCHAR
            max_length = 255  # Tamaño típico para campos URL
            if len(url) > max_length:
                return url[:max_length]
            return url
        else:
            logger.warning(f"URL no válida: {url}")
            return ""

    def execute_query(
        self,
        query: str,
        params: Optional[List[Any]] = None,
        fetch: bool = True,
        in_transaction: bool = False,
    ) -> Union[List[Dict[str, Any]], int, None]:
        """Ejecuta una consulta SQL y devuelve los resultados

        Args:
            query (str): Consulta SQL a ejecutar
            params (Optional[List[Any]], optional): Parámetros para la consulta. Defaults to None.
            fetch (bool, optional): Si es True, devuelve resultados. Defaults to True.
            in_transaction (bool, optional): Si es True, no hace commit ni cierra la conexión. Defaults to False.

        Returns:
            Union[List[Dict[str, Any]], int, None]: Resultados de la consulta como lista de diccionarios,
                                                   ID de la última fila insertada, o None si hubo un error
        """
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
                    # Para operaciones de escritura, hacer commit solo si no estamos en una transacción
                    if not in_transaction:
                        self.connection.commit()
                    results = cursor.lastrowid

                cursor.close()

                # Cerrar conexión solo si no estamos en una transacción
                if not in_transaction:
                    self.disconnect()

                return results
            else:
                logger.warning("No se pudo conectar a la base de datos")
                return [] if fetch else None
        except Exception as e:
            # Registrar detalles específicos del error
            error_msg = f"Error ejecutando consulta: {str(e)}\nQuery: {query}\nParámetros: {params}"
            logger.error(error_msg)

            # Si estamos en una transacción, hacer rollback
            if in_transaction and self.connection:
                try:
                    self.connection.rollback()
                    logger.info("Rollback de transacción realizado")
                except Exception as rollback_error:
                    logger.error(f"Error haciendo rollback: {str(rollback_error)}")

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

    def save_signal(self, signal_data: Dict[str, Any]) -> Optional[int]:
        """Guarda una señal de trading en la base de datos con todos los campos disponibles

        Args:
            signal_data (Dict[str, Any]): Datos de la señal a guardar

        Returns:
            Optional[int]: ID de la señal guardada o None si hubo un error
        """
        try:
            # Validar datos mínimos requeridos
            if not signal_data.get("symbol"):
                logger.error("Error guardando señal: Falta el símbolo")
                return None

            # Limpiar datos de texto
            cleaned_data = {}
            for key, value in signal_data.items():
                if isinstance(value, str):
                    cleaned_data[key] = self.clean_text_data(value)
                elif key == "news_source" and value and isinstance(value, str):
                    # Validar URL si es un campo de URL
                    cleaned_data[key] = self.validate_url(value)
                else:
                    cleaned_data[key] = value

            # Iniciar transacción
            if not self.begin_transaction():
                logger.error("No se pudo iniciar la transacción para guardar la señal")
                return None

            try:
                # Verificar si la columna signal_date existe
                check_column_query = (
                    """SHOW COLUMNS FROM trading_signals LIKE 'signal_date'"""
                )
                column_exists = self.execute_query(
                    check_column_query, fetch=True, in_transaction=True
                )

                # Preparar consulta con todos los campos de la tabla
                if column_exists and len(column_exists) > 0:
                    query = """INSERT INTO trading_signals
                              (symbol, price, entry_price, stop_loss, target_price, risk_reward,
                               direction, confidence_level, timeframe, strategy, setup_type,
                               category, analysis, technical_analysis, support_level, resistance_level,
                               rsi, trend, trend_strength, volatility, options_signal, options_analysis,
                               trading_specialist_signal, trading_specialist_confidence, sentiment,
                               sentiment_score, latest_news, news_source, additional_news, expert_analysis,
                               recommendation, mtf_analysis, daily_trend, weekly_trend, monthly_trend,
                               bullish_indicators, bearish_indicators, is_high_confidence, signal_date, created_at)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                      %s, %s, %s, %s, %s, %s, %s, %s)"""
                else:
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
                if column_exists and len(column_exists) > 0:
                    params = (
                        cleaned_data.get("symbol", ""),
                        cleaned_data.get("price", 0.0),
                        cleaned_data.get("entry_price", 0.0),
                        cleaned_data.get("stop_loss", 0.0),
                        cleaned_data.get("target_price", 0.0),
                        cleaned_data.get("risk_reward", 0.0),
                        cleaned_data.get("direction", "NEUTRAL"),
                        cleaned_data.get("confidence_level", "Baja"),
                        cleaned_data.get("timeframe", "Corto Plazo"),
                        cleaned_data.get("strategy", "Análisis Técnico"),
                        cleaned_data.get("setup_type", ""),
                        cleaned_data.get("category", "General"),
                        cleaned_data.get("analysis", ""),
                        cleaned_data.get("technical_analysis", ""),
                        cleaned_data.get("support_level", 0.0),
                        cleaned_data.get("resistance_level", 0.0),
                        cleaned_data.get("rsi", 0.0),
                        cleaned_data.get("trend", ""),
                        cleaned_data.get("trend_strength", ""),
                        cleaned_data.get("volatility", 0.0),
                        cleaned_data.get("options_signal", ""),
                        cleaned_data.get("options_analysis", ""),
                        cleaned_data.get("trading_specialist_signal", ""),
                        cleaned_data.get("trading_specialist_confidence", ""),
                        cleaned_data.get("sentiment", ""),
                        cleaned_data.get("sentiment_score", 0.0),
                        cleaned_data.get("latest_news", ""),
                        cleaned_data.get("news_source", ""),
                        cleaned_data.get("additional_news", ""),
                        cleaned_data.get("expert_analysis", ""),
                        cleaned_data.get("recommendation", ""),
                        cleaned_data.get("mtf_analysis", ""),
                        cleaned_data.get("daily_trend", ""),
                        cleaned_data.get("weekly_trend", ""),
                        cleaned_data.get("monthly_trend", ""),
                        cleaned_data.get("bullish_indicators", ""),
                        cleaned_data.get("bearish_indicators", ""),
                        cleaned_data.get("is_high_confidence", False),
                        cleaned_data.get("signal_date", datetime.now().date()),
                        cleaned_data.get("created_at", datetime.now()),
                    )
                else:
                    params = (
                        cleaned_data.get("symbol", ""),
                        cleaned_data.get("price", 0.0),
                        cleaned_data.get("entry_price", 0.0),
                        cleaned_data.get("stop_loss", 0.0),
                        cleaned_data.get("target_price", 0.0),
                        cleaned_data.get("risk_reward", 0.0),
                        cleaned_data.get("direction", "NEUTRAL"),
                        cleaned_data.get("confidence_level", "Baja"),
                        cleaned_data.get("timeframe", "Corto Plazo"),
                        cleaned_data.get("strategy", "Análisis Técnico"),
                        cleaned_data.get("setup_type", ""),
                        cleaned_data.get("category", "General"),
                        cleaned_data.get("analysis", ""),
                        cleaned_data.get("technical_analysis", ""),
                        cleaned_data.get("support_level", 0.0),
                        cleaned_data.get("resistance_level", 0.0),
                        cleaned_data.get("rsi", 0.0),
                        cleaned_data.get("trend", ""),
                        cleaned_data.get("trend_strength", ""),
                        cleaned_data.get("volatility", 0.0),
                        cleaned_data.get("options_signal", ""),
                        cleaned_data.get("options_analysis", ""),
                        cleaned_data.get("trading_specialist_signal", ""),
                        cleaned_data.get("trading_specialist_confidence", ""),
                        cleaned_data.get("sentiment", ""),
                        cleaned_data.get("sentiment_score", 0.0),
                        cleaned_data.get("latest_news", ""),
                        cleaned_data.get("news_source", ""),
                        cleaned_data.get("additional_news", ""),
                        cleaned_data.get("expert_analysis", ""),
                        cleaned_data.get("recommendation", ""),
                        cleaned_data.get("mtf_analysis", ""),
                        cleaned_data.get("daily_trend", ""),
                        cleaned_data.get("weekly_trend", ""),
                        cleaned_data.get("monthly_trend", ""),
                        cleaned_data.get("bullish_indicators", ""),
                        cleaned_data.get("bearish_indicators", ""),
                        cleaned_data.get("is_high_confidence", False),
                        cleaned_data.get("created_at", datetime.now()),
                    )

                # Ejecutar consulta dentro de la transacción
                signal_id = self.execute_query(
                    query, params, fetch=False, in_transaction=True
                )

                # Confirmar transacción
                if self.commit_transaction():
                    logger.info(
                        f"Señal guardada con ID: {signal_id} para símbolo: {cleaned_data.get('symbol', '')}"
                    )
                    return signal_id
                else:
                    logger.error("Error confirmando transacción para guardar señal")
                    return None
            except Exception as inner_e:
                # Revertir transacción en caso de error
                self.rollback_transaction()
                logger.error(f"Error en transacción guardando señal: {str(inner_e)}")
                return None
        except Exception as e:
            logger.error(f"Error guardando señal: {str(e)}\nDatos: {signal_data}")
            return None

    def log_email_sent(self, email_data: Dict[str, Any]) -> Optional[int]:
        """Registra el envío de un correo electrónico en la base de datos

        Args:
            email_data (Dict[str, Any]): Datos del correo enviado

        Returns:
            Optional[int]: ID del registro o None si hubo un error
        """
        try:
            # Limpiar datos de texto
            cleaned_data = {}
            for key, value in email_data.items():
                if isinstance(value, str):
                    cleaned_data[key] = self.clean_text_data(value)
                else:
                    cleaned_data[key] = value

            # Iniciar transacción
            if not self.begin_transaction():
                logger.error(
                    "No se pudo iniciar la transacción para registrar el envío de correo"
                )
                return None

            try:
                # Preparar consulta
                query = """INSERT INTO email_logs
                          (recipients, subject, content_summary, signals_included, status, error_message, sent_at)
                          VALUES (%s, %s, %s, %s, %s, %s, NOW())"""

                # Preparar datos
                params = (
                    cleaned_data.get("recipients", ""),
                    cleaned_data.get("subject", ""),
                    cleaned_data.get("content_summary", ""),
                    cleaned_data.get("signals_included", ""),
                    cleaned_data.get("status", "sent"),
                    cleaned_data.get("error_message", ""),
                )

                # Ejecutar consulta dentro de la transacción
                log_id = self.execute_query(
                    query, params, fetch=False, in_transaction=True
                )

                # Confirmar transacción
                if self.commit_transaction():
                    logger.info(f"Envío de correo registrado con ID: {log_id}")
                    return log_id
                else:
                    logger.error(
                        "Error confirmando transacción para registrar envío de correo"
                    )
                    return None
            except Exception as inner_e:
                # Revertir transacción en caso de error
                self.rollback_transaction()
                logger.error(
                    f"Error en transacción registrando envío de correo: {str(inner_e)}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Error registrando envío de correo: {str(e)}\nDatos: {email_data}"
            )
            return None

    def save_market_sentiment(self, sentiment_data: Dict[str, Any]) -> Optional[int]:

        # Verificar si ya existe un registro para hoy
        today = datetime.now().strftime("%Y-%m-%d")
        check_query = "SELECT id FROM market_sentiment WHERE DATE(created_at) = %s"
        existing_record = self.execute_query(check_query, params=[today], fetch=True)

        if existing_record and len(existing_record) > 0:
            logger.info(
                f"Ya existe un registro de sentimiento de mercado para hoy ({today}). No se guardará otro."
            )
            return existing_record[0]["id"]

        """Guarda datos de sentimiento de mercado en la base de datos

        Args:
            sentiment_data (Dict[str, Any]): Datos de sentimiento a guardar

        Returns:
            Optional[int]: ID del sentimiento guardado o None si hubo un error
        """
        try:
            # Limpiar datos de texto
            cleaned_data = {}
            for key, value in sentiment_data.items():
                if isinstance(value, str):
                    cleaned_data[key] = self.clean_text_data(value)
                else:
                    cleaned_data[key] = value

            # Iniciar transacción
            if not self.begin_transaction():
                logger.error(
                    "No se pudo iniciar la transacción para guardar el sentimiento de mercado"
                )
                return None

            try:
                # Verificar si ya existe un registro para la fecha especificada
                check_query = """SELECT id FROM market_sentiment
                                WHERE date = %s"""
                check_params = [cleaned_data.get("date", datetime.now().date())]
                existing_sentiment = self.execute_query(
                    check_query, check_params, fetch=True, in_transaction=True
                )

                if existing_sentiment and len(existing_sentiment) > 0:
                    # Actualizar registro existente
                    update_query = """UPDATE market_sentiment
                                    SET overall = %s,
                                        vix = %s,
                                        sp500_trend = %s,
                                        technical_indicators = %s,
                                        volume = %s,
                                        notes = %s,
                                        updated_at = NOW()
                                    WHERE id = %s"""

                    params = (
                        cleaned_data.get("overall", "Neutral"),
                        cleaned_data.get("vix", "N/A"),
                        cleaned_data.get("sp500_trend", "N/A"),
                        cleaned_data.get("technical_indicators", "N/A"),
                        cleaned_data.get("volume", "N/A"),
                        cleaned_data.get("notes", ""),
                        existing_sentiment[0].get("id"),
                    )

                    self.execute_query(
                        update_query, params, fetch=False, in_transaction=True
                    )
                    sentiment_id = existing_sentiment[0].get("id")
                    logger.info(
                        f"Sentimiento de mercado actualizado con ID: {sentiment_id} para fecha: {cleaned_data.get('date')}"
                    )
                else:
                    # Insertar nuevo registro
                    insert_query = """INSERT INTO market_sentiment
                                    (date, overall, vix, sp500_trend, technical_indicators, volume, notes, created_at)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""

                    params = (
                        cleaned_data.get("date", datetime.now().date()),
                        cleaned_data.get("overall", "Neutral"),
                        cleaned_data.get("vix", "N/A"),
                        cleaned_data.get("sp500_trend", "N/A"),
                        cleaned_data.get("technical_indicators", "N/A"),
                        cleaned_data.get("volume", "N/A"),
                        cleaned_data.get("notes", ""),
                    )

                    sentiment_id = self.execute_query(
                        insert_query, params, fetch=False, in_transaction=True
                    )
                    logger.info(
                        f"Nuevo sentimiento de mercado guardado con ID: {sentiment_id} para fecha: {cleaned_data.get('date')}"
                    )

                # Confirmar transacción
                if self.commit_transaction():
                    return sentiment_id
                else:
                    logger.error(
                        "Error confirmando transacción para guardar sentimiento de mercado"
                    )
                    return None
            except Exception as inner_e:
                # Revertir transacción en caso de error
                self.rollback_transaction()
                logger.error(
                    f"Error en transacción guardando sentimiento de mercado: {str(inner_e)}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Error guardando sentimiento de mercado: {str(e)}\nDatos: {sentiment_data}"
            )
            return None

    def get_market_sentiment(self, days_back=7):
        """Obtiene datos de sentimiento de mercado"""
        query = """SELECT * FROM market_sentiment
                  WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                  ORDER BY date DESC"""
        params = [days_back]

        return self.execute_query(query, params)

    def save_market_news(self, news_data: Dict[str, Any]) -> Optional[int]:
        """Guarda noticias de mercado en la base de datos

        Args:
            news_data (Dict[str, Any]): Datos de la noticia a guardar

        Returns:
            Optional[int]: ID de la noticia guardada o None si hubo un error
        """
        try:
            # Validar datos mínimos requeridos
            if not news_data.get("title"):
                logger.error("Error guardando noticia: Falta el título")
                return None

            # Limpiar datos de texto
            cleaned_data = {}
            for key, value in news_data.items():
                if key == "url" and value:
                    # Validar URL
                    cleaned_data[key] = self.validate_url(value)
                elif isinstance(value, str):
                    cleaned_data[key] = self.clean_text_data(value)
                else:
                    cleaned_data[key] = value

            # Iniciar transacción
            if not self.begin_transaction():
                logger.error(
                    "No se pudo iniciar la transacción para guardar la noticia"
                )
                return None

            try:
                # Verificar si la noticia ya existe (por título y fecha)
                check_query = """SELECT id FROM market_news
                                WHERE title = %s AND DATE(news_date) = DATE(%s)"""
                check_params = (
                    cleaned_data.get("title", ""),
                    cleaned_data.get("news_date", datetime.now()),
                )

                existing_news = self.execute_query(
                    check_query, check_params, fetch=True, in_transaction=True
                )

                if existing_news and len(existing_news) > 0:
                    logger.info(
                        f"La noticia ya existe en la base de datos: {cleaned_data.get('title', '')}"
                    )
                    self.commit_transaction()
                    return existing_news[0].get("id")  # Retornar ID existente

                # Preparar consulta para insertar nueva noticia
                query = """INSERT INTO market_news
                          (title, summary, source, url, news_date, impact, symbol, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""

                # Preparar datos
                params = (
                    cleaned_data.get("title", ""),
                    cleaned_data.get("summary", ""),
                    cleaned_data.get("source", ""),
                    cleaned_data.get("url", ""),
                    cleaned_data.get("news_date", datetime.now()),
                    cleaned_data.get("impact", "Medio"),
                    cleaned_data.get(
                        "symbol", "SPY"
                    ),  # Usar SPY como valor por defecto si no hay símbolo
                )

                # Ejecutar consulta dentro de la transacción
                news_id = self.execute_query(
                    query, params, fetch=False, in_transaction=True
                )

                # Confirmar transacción
                if self.commit_transaction():
                    logger.info(
                        f"Noticia guardada con ID: {news_id} - {cleaned_data.get('title', '')}"
                    )
                    return news_id
                else:
                    logger.error("Error confirmando transacción para guardar noticia")
                    return None
            except Exception as inner_e:
                # Revertir transacción en caso de error
                self.rollback_transaction()
                logger.error(f"Error en transacción guardando noticia: {str(inner_e)}")
                return None
        except Exception as e:
            logger.error(f"Error guardando noticia: {str(e)}\nDatos: {news_data}")
            return None

    def get_market_news(self, days_back=7):
        """Obtiene noticias de mercado"""
        query = """SELECT * FROM market_news
                  WHERE news_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
                  ORDER BY news_date DESC"""
        params = [days_back]

        return self.execute_query(query, params)

    def save_multiple_records(
        self, records_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Guarda múltiples registros en diferentes tablas en una sola transacción

        Args:
            records_data (Dict[str, Any]): Diccionario con los datos a guardar en cada tabla
                Ejemplo: {
                    'signals': [signal_data1, signal_data2, ...],
                    'news': [news_data1, news_data2, ...],
                    'sentiment': sentiment_data
                }

        Returns:
            Optional[Dict[str, Any]]: Diccionario con los IDs de los registros guardados o None si hubo un error
        """
        try:
            # Iniciar transacción
            if not self.begin_transaction():
                logger.error(
                    "No se pudo iniciar la transacción para guardar múltiples registros"
                )
                return None

            try:
                result_ids = {}

                # Guardar señales
                if "signals" in records_data and records_data["signals"]:
                    signal_ids = []
                    for signal_data in records_data["signals"]:
                        # Limpiar datos de texto
                        cleaned_data = {}
                        for key, value in signal_data.items():
                            if isinstance(value, str):
                                cleaned_data[key] = self.clean_text_data(value)
                            elif (
                                key == "news_source"
                                and value
                                and isinstance(value, str)
                            ):
                                cleaned_data[key] = self.validate_url(value)
                            else:
                                cleaned_data[key] = value

                        # Verificar si la columna signal_date existe
                        check_column_query = (
                            """SHOW COLUMNS FROM trading_signals LIKE 'signal_date'"""
                        )
                        column_exists = self.execute_query(
                            check_column_query, fetch=True, in_transaction=True
                        )

                        # Preparar consulta para insertar señal
                        if column_exists and len(column_exists) > 0:
                            query = """INSERT INTO trading_signals
                                      (symbol, price, entry_price, stop_loss, target_price, risk_reward,
                                       direction, confidence_level, timeframe, strategy, setup_type,
                                       category, analysis, technical_analysis, support_level, resistance_level,
                                       rsi, trend, trend_strength, volatility, options_signal, options_analysis,
                                       trading_specialist_signal, trading_specialist_confidence, sentiment,
                                       sentiment_score, latest_news, news_source, additional_news, expert_analysis,
                                       recommendation, mtf_analysis, daily_trend, weekly_trend, monthly_trend,
                                       bullish_indicators, bearish_indicators, is_high_confidence, signal_date, created_at)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                              %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                              %s, %s, %s, %s, %s, %s, %s, %s)"""
                        else:
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

                        # Preparar datos
                        if column_exists and len(column_exists) > 0:
                            params = (
                                cleaned_data.get("symbol", ""),
                                cleaned_data.get("price", 0.0),
                                cleaned_data.get("entry_price", 0.0),
                                cleaned_data.get("stop_loss", 0.0),
                                cleaned_data.get("target_price", 0.0),
                                cleaned_data.get("risk_reward", 0.0),
                                cleaned_data.get("direction", "NEUTRAL"),
                                cleaned_data.get("confidence_level", "Baja"),
                                cleaned_data.get("timeframe", "Corto Plazo"),
                                cleaned_data.get("strategy", "Análisis Técnico"),
                                cleaned_data.get("setup_type", ""),
                                cleaned_data.get("category", "General"),
                                cleaned_data.get("analysis", ""),
                                cleaned_data.get("technical_analysis", ""),
                                cleaned_data.get("support_level", 0.0),
                                cleaned_data.get("resistance_level", 0.0),
                                cleaned_data.get("rsi", 0.0),
                                cleaned_data.get("trend", ""),
                                cleaned_data.get("trend_strength", ""),
                                cleaned_data.get("volatility", 0.0),
                                cleaned_data.get("options_signal", ""),
                                cleaned_data.get("options_analysis", ""),
                                cleaned_data.get("trading_specialist_signal", ""),
                                cleaned_data.get("trading_specialist_confidence", ""),
                                cleaned_data.get("sentiment", ""),
                                cleaned_data.get("sentiment_score", 0.0),
                                cleaned_data.get("latest_news", ""),
                                cleaned_data.get("news_source", ""),
                                cleaned_data.get("additional_news", ""),
                                cleaned_data.get("expert_analysis", ""),
                                cleaned_data.get("recommendation", ""),
                                cleaned_data.get("mtf_analysis", ""),
                                cleaned_data.get("daily_trend", ""),
                                cleaned_data.get("weekly_trend", ""),
                                cleaned_data.get("monthly_trend", ""),
                                cleaned_data.get("bullish_indicators", ""),
                                cleaned_data.get("bearish_indicators", ""),
                                cleaned_data.get("is_high_confidence", False),
                                cleaned_data.get("signal_date", datetime.now().date()),
                                cleaned_data.get("created_at", datetime.now()),
                            )
                        else:
                            params = (
                                cleaned_data.get("symbol", ""),
                                cleaned_data.get("price", 0.0),
                                cleaned_data.get("entry_price", 0.0),
                                cleaned_data.get("stop_loss", 0.0),
                                cleaned_data.get("target_price", 0.0),
                                cleaned_data.get("risk_reward", 0.0),
                                cleaned_data.get("direction", "NEUTRAL"),
                                cleaned_data.get("confidence_level", "Baja"),
                                cleaned_data.get("timeframe", "Corto Plazo"),
                                cleaned_data.get("strategy", "Análisis Técnico"),
                                cleaned_data.get("setup_type", ""),
                                cleaned_data.get("category", "General"),
                                cleaned_data.get("analysis", ""),
                                cleaned_data.get("technical_analysis", ""),
                                cleaned_data.get("support_level", 0.0),
                                cleaned_data.get("resistance_level", 0.0),
                                cleaned_data.get("rsi", 0.0),
                                cleaned_data.get("trend", ""),
                                cleaned_data.get("trend_strength", ""),
                                cleaned_data.get("volatility", 0.0),
                                cleaned_data.get("options_signal", ""),
                                cleaned_data.get("options_analysis", ""),
                                cleaned_data.get("trading_specialist_signal", ""),
                                cleaned_data.get("trading_specialist_confidence", ""),
                                cleaned_data.get("sentiment", ""),
                                cleaned_data.get("sentiment_score", 0.0),
                                cleaned_data.get("latest_news", ""),
                                cleaned_data.get("news_source", ""),
                                cleaned_data.get("additional_news", ""),
                                cleaned_data.get("expert_analysis", ""),
                                cleaned_data.get("recommendation", ""),
                                cleaned_data.get("mtf_analysis", ""),
                                cleaned_data.get("daily_trend", ""),
                                cleaned_data.get("weekly_trend", ""),
                                cleaned_data.get("monthly_trend", ""),
                                cleaned_data.get("bullish_indicators", ""),
                                cleaned_data.get("bearish_indicators", ""),
                                cleaned_data.get("is_high_confidence", False),
                                cleaned_data.get("created_at", datetime.now()),
                            )

                        # Ejecutar consulta dentro de la transacción
                        signal_id = self.execute_query(
                            query, params, fetch=False, in_transaction=True
                        )
                        signal_ids.append(signal_id)

                    result_ids["signals"] = signal_ids

                # Guardar noticias
                if "news" in records_data and records_data["news"]:
                    news_ids = []
                    for news_data in records_data["news"]:
                        # Limpiar datos de texto
                        cleaned_data = {}
                        for key, value in news_data.items():
                            if key == "url" and value:
                                cleaned_data[key] = self.validate_url(value)
                            elif isinstance(value, str):
                                cleaned_data[key] = self.clean_text_data(value)
                            else:
                                cleaned_data[key] = value

                        # Verificar si la noticia ya existe
                        check_query = """SELECT id FROM market_news
                                        WHERE title = %s AND DATE(news_date) = DATE(%s)"""
                        check_params = (
                            cleaned_data.get("title", ""),
                            cleaned_data.get("news_date", datetime.now()),
                        )

                        existing_news = self.execute_query(
                            check_query, check_params, fetch=True, in_transaction=True
                        )

                        if existing_news and len(existing_news) > 0:
                            news_id = existing_news[0].get("id")
                            logger.info(
                                f"La noticia ya existe en la base de datos: {cleaned_data.get('title', '')}"
                            )
                        else:
                            # Preparar consulta para insertar noticia
                            query = """INSERT INTO market_news
                                      (title, summary, source, url, news_date, impact, symbol, created_at)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""

                            # Preparar datos
                            params = (
                                cleaned_data.get("title", ""),
                                cleaned_data.get("summary", ""),
                                cleaned_data.get("source", ""),
                                cleaned_data.get("url", ""),
                                cleaned_data.get("news_date", datetime.now()),
                                cleaned_data.get("impact", "Medio"),
                                cleaned_data.get(
                                    "symbol", "SPY"
                                ),  # Usar SPY como valor por defecto si no hay símbolo
                            )

                            # Ejecutar consulta dentro de la transacción
                            news_id = self.execute_query(
                                query, params, fetch=False, in_transaction=True
                            )
                            logger.info(
                                f"Noticia guardada con ID: {news_id} - {cleaned_data.get('title', '')}"
                            )

                        news_ids.append(news_id)

                    result_ids["news"] = news_ids

                # Guardar sentimiento
                if "sentiment" in records_data and records_data["sentiment"]:
                    sentiment_data = records_data["sentiment"]

                    # Limpiar datos de texto
                    cleaned_data = {}
                    for key, value in sentiment_data.items():
                        if isinstance(value, str):
                            cleaned_data[key] = self.clean_text_data(value)
                        else:
                            cleaned_data[key] = value

                    # Verificar si ya existe un registro para la fecha especificada
                    check_query = """SELECT id FROM market_sentiment
                                    WHERE date = %s"""
                    check_params = [cleaned_data.get("date", datetime.now().date())]
                    existing_sentiment = self.execute_query(
                        check_query, check_params, fetch=True, in_transaction=True
                    )

                    if existing_sentiment and len(existing_sentiment) > 0:
                        # Actualizar registro existente
                        # Verificar si la columna updated_at existe
                        check_column_query = (
                            """SHOW COLUMNS FROM market_sentiment LIKE 'updated_at'"""
                        )
                        column_exists = self.execute_query(
                            check_column_query, fetch=True, in_transaction=True
                        )

                        if column_exists and len(column_exists) > 0:
                            update_query = """UPDATE market_sentiment
                                            SET overall = %s,
                                                vix = %s,
                                                sp500_trend = %s,
                                                technical_indicators = %s,
                                                volume = %s,
                                                notes = %s,
                                                updated_at = NOW()
                                            WHERE id = %s"""
                        else:
                            update_query = """UPDATE market_sentiment
                                            SET overall = %s,
                                                vix = %s,
                                                sp500_trend = %s,
                                                technical_indicators = %s,
                                                volume = %s,
                                                notes = %s
                                            WHERE id = %s"""

                        params = (
                            cleaned_data.get("overall", "Neutral"),
                            cleaned_data.get("vix", "N/A"),
                            cleaned_data.get("sp500_trend", "N/A"),
                            cleaned_data.get("technical_indicators", "N/A"),
                            cleaned_data.get("volume", "N/A"),
                            cleaned_data.get("notes", ""),
                            existing_sentiment[0].get("id"),
                        )

                        self.execute_query(
                            update_query, params, fetch=False, in_transaction=True
                        )
                        sentiment_id = existing_sentiment[0].get("id")
                        logger.info(
                            f"Sentimiento de mercado actualizado con ID: {sentiment_id}"
                        )
                    else:
                        # Insertar nuevo registro
                        insert_query = """INSERT INTO market_sentiment
                                        (date, overall, vix, sp500_trend, technical_indicators, volume, notes, created_at)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""

                        params = (
                            cleaned_data.get("date", datetime.now().date()),
                            cleaned_data.get("overall", "Neutral"),
                            cleaned_data.get("vix", "N/A"),
                            cleaned_data.get("sp500_trend", "N/A"),
                            cleaned_data.get("technical_indicators", "N/A"),
                            cleaned_data.get("volume", "N/A"),
                            cleaned_data.get("notes", ""),
                        )

                        sentiment_id = self.execute_query(
                            insert_query, params, fetch=False, in_transaction=True
                        )
                        logger.info(
                            f"Nuevo sentimiento de mercado guardado con ID: {sentiment_id}"
                        )

                    result_ids["sentiment"] = sentiment_id

                # Confirmar transacción
                if self.commit_transaction():
                    logger.info(
                        f"Transacción completada: {len(result_ids)} tipos de registros guardados"
                    )
                    return result_ids
                else:
                    logger.error(
                        "Error confirmando transacción para guardar múltiples registros"
                    )
                    return None
            except Exception as inner_e:
                # Revertir transacción en caso de error
                self.rollback_transaction()
                logger.error(
                    f"Error en transacción guardando múltiples registros: {str(inner_e)}"
                )
                return None
        except Exception as e:
            logger.error(f"Error guardando múltiples registros: {str(e)}")
            return None


def save_market_news(
    news_data: Dict[str, Any], process_quality: bool = True
) -> Optional[int]:
    """Guarda una noticia de mercado en la base de datos

    Args:
        news_data (Dict[str, Any]): Datos de la noticia a guardar
        process_quality (bool): Indica si se debe procesar la calidad de los datos después de guardar

    Returns:
        Optional[int]: ID de la noticia guardada o None si hubo un error
    """
    try:
        db_manager = DatabaseManager()

        # Validar datos mínimos requeridos
        if not news_data.get("title"):
            logger.error("Error guardando noticia: Falta el título")
            return None

        # Asegurar que la fecha de la noticia esté presente
        if not news_data.get("news_date"):
            news_data["news_date"] = datetime.now()

        # Asegurar que el símbolo esté presente y sea correcto
        # Si ya viene un símbolo, verificar que sea válido usando company_data.py
        from company_data import COMPANY_INFO

        original_symbol = news_data.get("symbol")
        title = news_data.get("title", "")

        # Caso 1: Si ya viene un símbolo, verificar que sea válido
        if original_symbol:
            # Verificar si el símbolo existe en nuestra base de datos
            if original_symbol in COMPANY_INFO:
                # El símbolo es válido, mantenerlo
                logger.info(
                    f"Símbolo válido proporcionado: {original_symbol} - {COMPANY_INFO[original_symbol]['name']}"
                )
            else:
                # El símbolo no es reconocido, intentar extraerlo del título
                extracted_symbol = extract_symbol_from_title(title)
                if extracted_symbol and extracted_symbol in COMPANY_INFO:
                    news_data["symbol"] = extracted_symbol
                    logger.info(
                        f"Símbolo reemplazado: {original_symbol} -> {extracted_symbol} ({COMPANY_INFO[extracted_symbol]['name']})"
                    )
                else:
                    # Intentar usar IA para identificar el símbolo
                    try:
                        from ai_utils import get_expert_analysis

                        prompt = f"Identifica el símbolo bursátil (ticker) principal mencionado en este título de noticia financiera. Responde solo con el símbolo, sin explicaciones: '{title}'"
                        ai_symbol = get_expert_analysis(prompt).strip().upper()

                        # Verificar si el símbolo identificado por IA es válido
                        if ai_symbol and ai_symbol in COMPANY_INFO:
                            news_data["symbol"] = ai_symbol
                            logger.info(
                                f"Símbolo identificado por IA: {ai_symbol} ({COMPANY_INFO[ai_symbol]['name']})"
                            )
                        else:
                            # Mantener el símbolo original si no se puede identificar uno mejor
                            logger.info(
                                f"Manteniendo símbolo original no reconocido: {original_symbol}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error al usar IA para identificar símbolo: {str(e)}"
                        )
                        # Mantener el símbolo original
                        logger.info(f"Manteniendo símbolo original: {original_symbol}")

        # Caso 2: Si no viene un símbolo, intentar extraerlo del título
        else:
            # Verificar si hay un símbolo en el contexto de la función que llamó a esta
            # Por ejemplo, si estamos procesando noticias de un símbolo específico
            context_symbol = None
            import inspect
            import traceback

            # Obtener el stack completo para buscar el símbolo en cualquier nivel
            stack = traceback.extract_stack()
            frame = inspect.currentframe().f_back

            # Primero buscar en las variables locales de los frames
            while frame:
                if "symbol" in frame.f_locals and frame.f_locals["symbol"]:
                    context_symbol = frame.f_locals["symbol"]
                    logger.info(f"Símbolo encontrado en el contexto: {context_symbol}")
                    break
                frame = frame.f_back

            # Si no se encontró en los frames, buscar en el stack completo
            if not context_symbol:
                for frame_info in stack:
                    # Buscar patrones como 'symbol="XYZ"' o "symbol='XYZ'" en el código fuente
                    frame_line = frame_info[3]  # La línea de código
                    if frame_line and "symbol" in frame_line:
                        import re

                        symbol_match = re.search(
                            r'symbol\s*=\s*["\']([A-Z0-9]+)["\']', frame_line
                        )
                        if symbol_match:
                            context_symbol = symbol_match.group(1)
                            logger.info(
                                f"Símbolo encontrado en el stack: {context_symbol}"
                            )
                            break

            if context_symbol and context_symbol in COMPANY_INFO:
                news_data["symbol"] = context_symbol
                logger.info(
                    f"Usando símbolo del contexto: {context_symbol} ({COMPANY_INFO[context_symbol]['name']})"
                )
            else:
                # Intentar extraer el símbolo del título
                extracted_symbol = extract_symbol_from_title(title)
                if extracted_symbol and extracted_symbol in COMPANY_INFO:
                    news_data["symbol"] = extracted_symbol
                    logger.info(
                        f"Símbolo extraído del título: {extracted_symbol} ({COMPANY_INFO[extracted_symbol]['name']})"
                    )
                else:
                    # Intentar usar IA para identificar el símbolo
                    try:
                        from ai_utils import get_expert_analysis

                        prompt = f"Identifica el símbolo bursátil (ticker) principal mencionado en este título de noticia financiera. Responde solo con el símbolo, sin explicaciones: '{title}'"
                        ai_symbol = get_expert_analysis(prompt).strip().upper()

                        # Verificar si el símbolo identificado por IA es válido
                        if ai_symbol and ai_symbol in COMPANY_INFO:
                            news_data["symbol"] = ai_symbol
                            logger.info(
                                f"Símbolo identificado por IA: {ai_symbol} ({COMPANY_INFO[ai_symbol]['name']})"
                            )
                        else:
                            # Usar SPY como valor por defecto si no se puede identificar un símbolo
                            news_data["symbol"] = "SPY"
                            logger.warning(
                                "No se pudo identificar un símbolo, usando SPY como valor por defecto"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error al usar IA para identificar símbolo: {str(e)}"
                        )
                        # Usar SPY como valor por defecto
                        news_data["symbol"] = "SPY"
                        logger.warning(
                            "Error al identificar símbolo, usando SPY como valor por defecto"
                        )

        # Traducir y condensar el título y resumen al español usando el experto de IA
        try:
            from ai_utils import get_expert_analysis

            # Traducir título
            if news_data.get("title") and not news_data.get("title").startswith(
                "Error"
            ):
                original_title = news_data.get("title")
                prompt = f"Traduce este título de noticia financiera al español de forma concisa y profesional (máximo 100 caracteres): '{original_title}'"
                translated_title = get_expert_analysis(prompt)
                if translated_title and len(translated_title) > 10:
                    # Limitar la longitud del título a 250 caracteres (límite de la columna en la base de datos)
                    if len(translated_title) > 250:
                        translated_title = translated_title[:247] + "..."
                    news_data["title"] = translated_title.strip()
                    logger.info(f"Título traducido: {news_data['title']}")

            # Generar o traducir el resumen
            # Si hay un resumen existente, traducirlo
            if news_data.get("summary") and len(news_data.get("summary", "")) > 20:
                original_summary = news_data.get("summary")
                prompt = f"Traduce y condensa este resumen de noticia financiera al español de forma profesional y concisa (máximo 200 caracteres): '{original_summary}'"
                translated_summary = get_expert_analysis(prompt)
                if translated_summary and len(translated_summary) > 20:
                    news_data["summary"] = translated_summary.strip()
                    logger.info(
                        f"Resumen traducido y condensado: {news_data['summary']}"
                    )
            # Si no hay resumen o es muy corto, generarlo a partir del título y símbolo
            elif not news_data.get("summary") or len(news_data.get("summary", "")) < 20:
                title = news_data.get("title", "")
                symbol = news_data.get("symbol", "SPY")
                url = news_data.get("url", "")

                # Generar un prompt para el resumen
                if url:
                    prompt = f"Genera un resumen conciso (máximo 200 caracteres) en español para esta noticia financiera sobre {symbol}. Título: '{title}'. URL: {url}"
                else:
                    prompt = f"Genera un resumen conciso (máximo 200 caracteres) en español para esta noticia financiera sobre {symbol}. Título: '{title}'"

                generated_summary = get_expert_analysis(prompt)
                if generated_summary and len(generated_summary) > 20:
                    news_data["summary"] = generated_summary.strip()
                    logger.info(f"Resumen generado: {news_data['summary']}")
                else:
                    # Generar un resumen básico si falla la generación con IA
                    news_data["summary"] = f"Noticia relacionada con {symbol}: {title}"
                    logger.info(f"Resumen básico generado: {news_data['summary']}")
        except Exception as e:
            logger.warning(f"No se pudo procesar la noticia con IA: {str(e)}")
            # Generar un resumen básico si falla la generación con IA
            if not news_data.get("summary") or len(news_data.get("summary", "")) < 20:
                title = news_data.get("title", "")
                symbol = news_data.get("symbol", "SPY")
                news_data["summary"] = f"Noticia relacionada con {symbol}: {title}"
                logger.info(
                    f"Resumen básico generado (fallback): {news_data['summary']}"
                )

        # Limpiar datos de texto
        cleaned_data = {}
        for key, value in news_data.items():
            if isinstance(value, str):
                cleaned_data[key] = db_manager.clean_text_data(value)
            elif key == "url" and value and isinstance(value, str):
                # Validar URL
                cleaned_data[key] = db_manager.validate_url(value)
            else:
                cleaned_data[key] = value

        # Preparar consulta
        query = """INSERT INTO market_news
                  (title, summary, source, url, news_date, impact, symbol, created_at)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""

        params = (
            cleaned_data.get("title", ""),
            cleaned_data.get("summary", ""),
            cleaned_data.get("source", "InversorIA Analytics"),
            cleaned_data.get("url", ""),
            cleaned_data.get("news_date", datetime.now()),
            cleaned_data.get("impact", "Medio"),
            cleaned_data.get(
                "symbol"
            ),  # El símbolo ya debería estar establecido en el procesamiento anterior
        )

        # Ejecutar consulta
        news_id = db_manager.execute_query(query, params, fetch=False)
        if news_id:
            logger.info(f"Noticia guardada con ID: {news_id}")

            # Procesar la calidad de los datos después de guardar
            if process_quality:
                try:
                    # Importar aquí para evitar problemas de importación circular
                    import post_save_quality_check
                    import sys
                    import os

                    # Asegurar que post_save_quality_check está en el path
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    if current_dir not in sys.path:
                        sys.path.append(current_dir)

                    # Procesar solo las noticias
                    result = post_save_quality_check.process_quality_after_save(
                        table_name="news", limit=1
                    )

                    if result and result.get("news_processed", 0) > 0:
                        logger.info(
                            f"Procesamiento de calidad completado para la noticia {news_id}. Se procesaron {result.get('news_processed', 0)} noticias."
                        )
                    else:
                        logger.warning(
                            "No se procesaron noticias en post_save_quality_check"
                        )

                    # Ejecutar update_news_symbols.py para actualizar símbolos
                    try:
                        import update_news_symbols

                        updated, skipped = update_news_symbols.update_news_symbols()
                        logger.info(
                            f"Actualización de símbolos completada: {updated} registros actualizados, {skipped} sin cambios"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error en la actualización de símbolos: {str(e)}"
                        )
                        logger.warning("Traza completa:", exc_info=True)

                    # Mostrar mensaje de confirmación
                    logger.info(
                        "Los datos han sido almacenados correctamente en la base de datos y estarán disponibles para consultas futuras."
                    )
                except Exception as e:
                    logger.warning(f"Error en el procesamiento de calidad: {str(e)}")
                    logger.warning("Traza completa:", exc_info=True)

            return news_id
        else:
            logger.error("Error guardando noticia: No se obtuvo ID")
            return None

    except Exception as e:
        logger.error(f"Error guardando noticia: {str(e)}")
        return None


def save_market_sentiment(
    sentiment_data: Dict[str, Any], process_quality: bool = True
) -> Optional[int]:
    """Guarda datos de sentimiento de mercado en la base de datos

    Args:
        sentiment_data (Dict[str, Any]): Datos de sentimiento a guardar
        process_quality (bool): Indica si se debe procesar la calidad de los datos después de guardar

    Returns:
        Optional[int]: ID del sentimiento guardado o None si hubo un error
    """
    try:
        db_manager = DatabaseManager()

        # Verificar si ya existe un registro para hoy
        today = datetime.now().strftime("%Y-%m-%d")
        check_today_query = (
            "SELECT id FROM market_sentiment WHERE DATE(created_at) = %s"
        )
        existing_today = db_manager.execute_query(
            check_today_query, params=[today], fetch=True
        )

        if existing_today and len(existing_today) > 0:
            logger.info(
                f"Ya existe un registro de sentimiento de mercado para hoy ({today}). No se guardará otro."
            )
            return existing_today[0]["id"]

        # Validar datos mínimos requeridos
        if not sentiment_data.get("overall"):
            logger.error("Error guardando sentimiento: Falta el sentimiento general")
            return None

        # Corregir el campo vix si es 'N/A' o no es numérico
        if sentiment_data.get("vix") == "N/A" or sentiment_data.get("vix") is None:
            # Intentar obtener el valor actual del VIX
            try:
                from market_utils import get_vix_level

                vix_value = get_vix_level()
                if isinstance(vix_value, (int, float, decimal.Decimal)):
                    sentiment_data["vix"] = float(vix_value)
                else:
                    sentiment_data["vix"] = 0.0  # Usar 0.0 como valor por defecto
            except Exception as e:
                logger.warning(f"Error obteniendo VIX: {str(e)}")
                sentiment_data["vix"] = 0.0  # Usar 0.0 como valor por defecto
        elif not isinstance(sentiment_data.get("vix"), (int, float, decimal.Decimal)):
            # Intentar convertir a float si es una cadena
            try:
                sentiment_data["vix"] = float(sentiment_data.get("vix"))
            except (ValueError, TypeError):
                sentiment_data["vix"] = 0.0  # Usar 0.0 como valor por defecto

        # Asegurar que la fecha esté presente
        if not sentiment_data.get("date"):
            sentiment_data["date"] = datetime.now().date()

        # Asegurar que los campos adicionales estén presentes
        if not sentiment_data.get("symbol"):
            # Intentar extraer el símbolo del contexto o del contenido
            try:
                # Buscar en el contexto actual
                import inspect

                current_frame = inspect.currentframe()
                context_symbol = None

                # Buscar en los frames anteriores si hay un símbolo en el contexto
                while current_frame:
                    if (
                        "symbol" in current_frame.f_locals
                        and current_frame.f_locals["symbol"]
                    ):
                        context_symbol = current_frame.f_locals["symbol"]
                        break
                    current_frame = current_frame.f_back

                if context_symbol:
                    sentiment_data["symbol"] = context_symbol
                    logger.info(
                        f"Usando símbolo del contexto para sentimiento: {context_symbol}"
                    )
                else:
                    # Si no hay contexto, usar SPY como valor por defecto para el mercado general
                    sentiment_data["symbol"] = "SPY"
                    logger.info(
                        "Usando SPY como valor por defecto para sentimiento de mercado general"
                    )
            except Exception as e:
                logger.warning(f"Error al extraer símbolo del contexto: {str(e)}")
                sentiment_data["symbol"] = (
                    "SPY"  # Valor por defecto para el mercado general
                )

        if not sentiment_data.get("sentiment"):
            sentiment_data["sentiment"] = sentiment_data.get("overall", "Neutral")

        if not sentiment_data.get("score"):
            # Convertir el sentimiento a un score numérico
            sentiment_map = {"Alcista": 0.75, "Neutral": 0.5, "Bajista": 0.25}
            sentiment_data["score"] = sentiment_map.get(
                sentiment_data.get("overall", "Neutral"), 0.5
            )

        if not sentiment_data.get("source"):
            sentiment_data["source"] = "InversorIA Analytics"

        if not sentiment_data.get("analysis"):
            # Generar un análisis basado en los datos disponibles
            analysis = f"Análisis de sentimiento de mercado: {sentiment_data.get('overall', 'Neutral')}.\n"
            if sentiment_data.get("vix"):
                analysis += f"VIX: {sentiment_data.get('vix')}. "
            if sentiment_data.get("sp500_trend"):
                analysis += f"Tendencia S&P 500: {sentiment_data.get('sp500_trend')}. "
            if sentiment_data.get("technical_indicators"):
                analysis += f"\nIndicadores técnicos: {sentiment_data.get('technical_indicators')}"
            if sentiment_data.get("notes"):
                analysis += f"\nNotas adicionales: {sentiment_data.get('notes')}"
            sentiment_data["analysis"] = analysis

        if not sentiment_data.get("sentiment_date"):
            sentiment_data["sentiment_date"] = datetime.now()

        # Limpiar datos de texto
        cleaned_data = {}
        for key, value in sentiment_data.items():
            if isinstance(value, str):
                cleaned_data[key] = db_manager.clean_text_data(value)
            else:
                cleaned_data[key] = value

        # Verificar si ya existe un registro para la fecha y símbolo especificados
        check_query = """SELECT id FROM market_sentiment
                      WHERE date = %s AND symbol = %s"""
        check_params = [
            cleaned_data.get("date", datetime.now().date()),
            cleaned_data.get("symbol", "SPY"),
        ]
        existing_sentiment = db_manager.execute_query(check_query, check_params)

        if existing_sentiment and len(existing_sentiment) > 0:
            # Actualizar registro existente
            # Verificar si la columna updated_at existe
            check_column_query = (
                """SHOW COLUMNS FROM market_sentiment LIKE 'updated_at'"""
            )
            column_exists = db_manager.execute_query(check_column_query)

            if column_exists and len(column_exists) > 0:
                update_query = """UPDATE market_sentiment
                              SET overall = %s,
                                  vix = %s,
                                  sp500_trend = %s,
                                  technical_indicators = %s,
                                  volume = %s,
                                  notes = %s,
                                  symbol = %s,
                                  sentiment = %s,
                                  score = %s,
                                  source = %s,
                                  analysis = %s,
                                  sentiment_date = %s,
                                  updated_at = NOW()
                              WHERE id = %s"""
            else:
                update_query = """UPDATE market_sentiment
                              SET overall = %s,
                                  vix = %s,
                                  sp500_trend = %s,
                                  technical_indicators = %s,
                                  volume = %s,
                                  notes = %s,
                                  symbol = %s,
                                  sentiment = %s,
                                  score = %s,
                                  source = %s,
                                  analysis = %s,
                                  sentiment_date = %s
                              WHERE id = %s"""

            # Asegurar que vix sea un valor numérico
            vix_value = cleaned_data.get("vix", 0.0)
            if not isinstance(vix_value, (int, float, decimal.Decimal)):
                try:
                    vix_value = float(vix_value)
                except (ValueError, TypeError):
                    vix_value = 0.0

            params = (
                cleaned_data.get("overall", "Neutral"),
                vix_value,  # Valor numérico asegurado
                cleaned_data.get("sp500_trend", "N/A"),
                cleaned_data.get("technical_indicators", "N/A"),
                cleaned_data.get("volume", "N/A"),
                cleaned_data.get("notes", ""),
                cleaned_data.get("symbol", "SPY"),
                cleaned_data.get("sentiment", cleaned_data.get("overall", "Neutral")),
                cleaned_data.get("score", 0.5),
                cleaned_data.get("source", "InversorIA Analytics"),
                cleaned_data.get("analysis", ""),
                cleaned_data.get("sentiment_date", datetime.now()),
                existing_sentiment[0].get("id"),
            )

            db_manager.execute_query(update_query, params, fetch=False)
            sentiment_id = existing_sentiment[0].get("id")
            logger.info(f"Sentimiento de mercado actualizado con ID: {sentiment_id}")

            # Procesar la calidad de los datos después de guardar
            if process_quality:
                try:
                    # Importar aquí para evitar problemas de importación circular
                    import post_save_quality_check

                    # Procesar solo el sentimiento
                    post_save_quality_check.process_quality_after_save(
                        table_name="sentiment", limit=1
                    )
                    logger.info(
                        f"Procesamiento de calidad completado para el sentimiento {sentiment_id}"
                    )
                except Exception as e:
                    logger.warning(f"Error en el procesamiento de calidad: {str(e)}")
                    logger.warning("Traza completa:", exc_info=True)

            return sentiment_id
        else:
            # Insertar nuevo registro con todos los campos
            insert_query = """INSERT INTO market_sentiment
                          (date, overall, vix, sp500_trend, technical_indicators, volume, notes,
                           symbol, sentiment, score, source, analysis, sentiment_date, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())"""

            # Asegurar que vix sea un valor numérico
            vix_value = cleaned_data.get("vix", 0.0)
            if not isinstance(vix_value, (int, float, decimal.Decimal)):
                try:
                    vix_value = float(vix_value)
                except (ValueError, TypeError):
                    vix_value = 0.0

            params = (
                cleaned_data.get("date", datetime.now().date()),
                cleaned_data.get("overall", "Neutral"),
                vix_value,  # Valor numérico asegurado
                cleaned_data.get("sp500_trend", "N/A"),
                cleaned_data.get("technical_indicators", "N/A"),
                cleaned_data.get("volume", "N/A"),
                cleaned_data.get("notes", ""),
                cleaned_data.get("symbol", "SPY"),
                cleaned_data.get("sentiment", cleaned_data.get("overall", "Neutral")),
                cleaned_data.get("score", 0.5),
                cleaned_data.get("source", "InversorIA Analytics"),
                cleaned_data.get("analysis", ""),
                cleaned_data.get("sentiment_date", datetime.now()),
            )

            sentiment_id = db_manager.execute_query(insert_query, params, fetch=False)
            logger.info(f"Nuevo sentimiento de mercado guardado con ID: {sentiment_id}")

            # Procesar la calidad de los datos después de guardar
            if process_quality:
                try:
                    # Importar aquí para evitar problemas de importación circular
                    import post_save_quality_check

                    # Procesar solo el sentimiento
                    post_save_quality_check.process_quality_after_save(
                        table_name="sentiment", limit=1
                    )
                    logger.info(
                        f"Procesamiento de calidad completado para el sentimiento {sentiment_id}"
                    )
                except Exception as e:
                    logger.warning(f"Error en el procesamiento de calidad: {str(e)}")
                    logger.warning("Traza completa:", exc_info=True)

            return sentiment_id

    except Exception as e:
        logger.error(f"Error guardando sentimiento de mercado: {str(e)}")
        return None


def save_trading_signal(
    signal_data: Dict[str, Any], process_quality: bool = True
) -> Optional[int]:
    """Guarda una señal de trading en la base de datos

    Args:
        signal_data (Dict[str, Any]): Datos de la señal a guardar
        process_quality (bool): Indica si se debe procesar la calidad de los datos después de guardar

    Returns:
        Optional[int]: ID de la señal guardada o None si hubo un error
    """
    try:
        db_manager = DatabaseManager()

        # Validar datos mínimos requeridos
        if not signal_data.get("symbol"):
            logger.error("Error guardando señal: Falta el símbolo")
            return None

        # Mejorar los campos latest_news y news_source con el experto de IA
        try:
            from ai_utils import get_expert_analysis

            # Mejorar latest_news
            if (
                not signal_data.get("latest_news")
                or len(signal_data.get("latest_news", "")) < 30
            ):
                symbol = signal_data.get("symbol")
                direction = signal_data.get("direction", "NEUTRAL")
                price = signal_data.get("price", 0.0)

                # Generar noticia relevante basada en los datos de la señal
                prompt = f"Genera una noticia financiera concisa y específica en español para {symbol} a ${price:.2f} con dirección {direction}. Incluye datos relevantes y específicos, no genéricos. Máximo 150 caracteres."

                generated_news = get_expert_analysis(prompt)
                if generated_news and len(generated_news) > 20:
                    signal_data["latest_news"] = generated_news.strip()
                    logger.info(
                        f"Noticia generada para {symbol}: {signal_data['latest_news']}"
                    )

            # Mejorar news_source
            if (
                not signal_data.get("news_source")
                or signal_data.get("news_source") == ""
            ):
                # Buscar una fuente confiable basada en el símbolo
                symbol = signal_data.get("symbol")
                if (
                    symbol.startswith("BTC")
                    or symbol.startswith("ETH")
                    or "COIN" in symbol
                ):
                    signal_data["news_source"] = "https://www.coindesk.com/"
                elif symbol in ["SPY", "QQQ", "DIA", "IWM"]:
                    signal_data["news_source"] = "https://www.marketwatch.com/"
                else:
                    signal_data["news_source"] = (
                        f"https://finance.yahoo.com/quote/{symbol}/news/"
                    )

                logger.info(
                    f"Fuente de noticias asignada para {symbol}: {signal_data['news_source']}"
                )
        except Exception as e:
            logger.warning(f"No se pudieron mejorar los datos de noticias: {str(e)}")

        # Usar el método save_signal del DatabaseManager
        signal_id = db_manager.save_signal(signal_data)

        # Procesar la calidad de los datos después de guardar
        if signal_id and process_quality:
            try:
                # Importar aquí para evitar problemas de importación circular
                import post_save_quality_check

                # Procesar solo las señales de trading
                post_save_quality_check.process_quality_after_save(
                    table_name="signals", limit=1
                )
                logger.info(
                    f"Procesamiento de calidad completado para la señal {signal_id}"
                )
            except Exception as e:
                logger.warning(f"Error en el procesamiento de calidad: {str(e)}")
                logger.warning("Traza completa:", exc_info=True)

        return signal_id

    except Exception as e:
        logger.error(f"Error guardando señal de trading: {str(e)}")
        return None


def extract_symbol_from_content(
    text: str, content: str = None, current_context_symbol: str = None
) -> Optional[str]:
    """
    Extrae el símbolo de una acción o ETF del título y/o contenido de una noticia.
    Utiliza company_data.py para validar los símbolos encontrados.

    Args:
        text (str): Título de la noticia
        content (str, optional): Contenido o resumen de la noticia
        current_context_symbol (str, optional): Símbolo del contexto actual (si se está analizando un símbolo específico)

    Returns:
        Optional[str]: Símbolo extraído o None si no se encuentra
    """
    if not text and not content and not current_context_symbol:
        return None

    # Importar módulos necesarios
    import re
    import logging
    import inspect

    logger = logging.getLogger(__name__)

    # Importar datos de company_data.py
    from company_data import COMPANY_INFO

    # Lista de símbolos candidatos con su puntuación de relevancia
    candidates = {}

    # Si tenemos un símbolo de contexto, añadirlo como candidato con alta puntuación
    if current_context_symbol and current_context_symbol in COMPANY_INFO:
        candidates[current_context_symbol] = 5.0
        logger.info(f"Usando símbolo del contexto actual: {current_context_symbol}")

    # Si no se proporcionó un símbolo de contexto, intentar encontrarlo en el stack
    if not current_context_symbol:
        # Obtener el frame actual para buscar el símbolo en el contexto
        frame = inspect.currentframe().f_back

        # Primero buscar en las variables locales de los frames
        while frame:
            if "symbol" in frame.f_locals and frame.f_locals["symbol"]:
                context_symbol = frame.f_locals["symbol"]
                if context_symbol in COMPANY_INFO:
                    candidates[context_symbol] = 4.0
                    logger.info(f"Símbolo encontrado en el contexto: {context_symbol}")
                break
            frame = frame.f_back

    # Combinar título y contenido para análisis si ambos están disponibles
    all_text = text or ""
    if content:
        all_text = f"{all_text} {content}"

    # Buscar patrones comunes de símbolos en el texto
    logger.info(f"Buscando símbolos en texto: '{text[:100]}...'")

    # Patrón 1: Símbolos entre paréntesis como (AAPL), (TSLA), etc.
    parenthesis_pattern = r"\(([A-Z]{1,5})\)"
    matches = re.findall(parenthesis_pattern, all_text)
    logger.info(f"Coincidencias de paréntesis: {matches}")

    if matches:
        # Verificar que el símbolo no sea una abreviatura común
        common_abbr = [
            "CEO",
            "CFO",
            "CTO",
            "COO",
            "USA",
            "UK",
            "EU",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "AI",
            "IPO",
            "ETF",
        ]
        for match in matches:
            if match not in common_abbr and len(match) >= 2 and len(match) <= 5:
                # Verificar si el símbolo existe en COMPANY_INFO
                if match in COMPANY_INFO:
                    # Mayor puntuación si está en el título
                    score = 3.0 if match in text else 2.0
                    candidates[match] = candidates.get(match, 0) + score
                    logger.info(f"Símbolo encontrado en paréntesis: {match}")

    # Patrón 2: Símbolos con prefijo NYSE: o NASDAQ: como NYSE:AAPL, NASDAQ:TSLA, etc.
    exchange_pattern = r"(NYSE|NASDAQ):\s*([A-Z]{1,5})"
    matches = re.findall(exchange_pattern, all_text)
    logger.info(f"Coincidencias de exchange_pattern: {matches}")
    if matches:
        for match in matches:
            symbol = match[1]  # Devolver el símbolo, no el exchange
            # Verificar si el símbolo existe en COMPANY_INFO
            if symbol in COMPANY_INFO:
                # Mayor puntuación si está en el título
                score = 3.0 if f"{match[0]}:{symbol}" in text else 2.0
                candidates[symbol] = candidates.get(symbol, 0) + score
                logger.info(f"Símbolo encontrado con prefijo de exchange: {symbol}")

    # Patrón 3: Buscar nombres de compañías conocidas en el texto y devolver su símbolo
    for symbol, info in COMPANY_INFO.items():
        company_name = info.get("name", "")
        if company_name and len(company_name) > 3:  # Evitar nombres muy cortos
            # Buscar el nombre de la compañía en el texto
            if company_name.lower() in all_text.lower():
                # Mayor puntuación si está en el título
                score = 2.5 if company_name.lower() in text.lower() else 1.5
                candidates[symbol] = candidates.get(symbol, 0) + score
                logger.info(
                    f"Nombre de compañía encontrado: {company_name}, símbolo: {symbol}"
                )

    # Patrón 4: Buscar símbolos directamente en el texto (palabras en mayúsculas de 2-5 letras)
    ticker_pattern = r"\b([A-Z]{2,5})\b"
    matches = re.findall(ticker_pattern, all_text)
    logger.info(f"Coincidencias de ticker_pattern: {matches}")
    if matches:
        common_words = [
            "CEO",
            "CFO",
            "CTO",
            "COO",
            "USA",
            "UK",
            "EU",
            "AI",
            "IPO",
            "ETF",
            "SEC",
            "FED",
            "GDP",
            "CPI",
        ]
        for match in matches:
            if match not in common_words and match in COMPANY_INFO:
                # Mayor puntuación si está en el título
                score = 2.0 if match in text else 1.0
                candidates[symbol] = candidates.get(symbol, 0) + score
                logger.info(f"Símbolo encontrado directamente en el texto: {match}")

    # Patrón 5: Buscar índices comunes si se mencionan en el texto
    indices = {
        "S&P 500": "SPY",
        "S&P500": "SPY",
        "SP500": "SPY",
        "Dow Jones": "DIA",
        "DJIA": "DIA",
        "Nasdaq": "QQQ",
        "Nasdaq 100": "QQQ",
        "Russell 2000": "IWM",
        "VIX": "VIX",
        "Volatilidad": "VIX",
    }

    for index_name, index_symbol in indices.items():
        if index_name.lower() in all_text.lower():
            # Mayor puntuación si está en el título
            score = 1.5 if index_name.lower() in text.lower() else 0.8
            candidates[index_symbol] = candidates.get(index_symbol, 0) + score
            logger.info(f"Índice encontrado: {index_name}, símbolo: {index_symbol}")

    # Si hay candidatos, devolver el de mayor puntuación
    if candidates:
        best_symbol = max(candidates.items(), key=lambda x: x[1])[0]
        logger.info(
            f"Mejor símbolo encontrado: {best_symbol} con puntuación {candidates[best_symbol]}"
        )
        return best_symbol

    # Si no se encuentra ningún símbolo, devolver None
    return None


def extract_symbol_from_title(title: str) -> Optional[str]:
    """
    Extrae el símbolo de una acción o ETF del título de una noticia.
    Utiliza company_data.py para validar los símbolos encontrados.

    Esta función es un wrapper para mantener compatibilidad con el código existente.
    Internamente usa extract_symbol_from_content.

    Args:
        title (str): Título de la noticia

    Returns:
        Optional[str]: Símbolo extraído o None si no se encuentra
    """
    return extract_symbol_from_content(title)


class NewsletterSubscriberManager:
    """
    Gestiona los suscriptores del boletín de trading
    """

    def __init__(self):
        """
        Inicializa el gestor de suscriptores
        """
        self.db_manager = DatabaseManager()
        self._ensure_tables_exist()

    def _ensure_tables_exist(self) -> bool:
        """
        Asegura que las tablas necesarias existan en la base de datos

        Returns:
            bool: True si las tablas existen o se crearon correctamente, False en caso contrario
        """
        try:
            # Verificar si la tabla de suscriptores existe
            query = "SHOW TABLES LIKE 'newsletter_subscribers'"
            result = self.db_manager.execute_query(query)

            if not result:
                # Crear tabla de suscriptores
                create_subscribers_table = """
                CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    name VARCHAR(100),
                    last_name VARCHAR(100),
                    company VARCHAR(150),
                    active BOOLEAN DEFAULT TRUE,
                    subscription_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_sent_date DATETIME,
                    send_count INT DEFAULT 0,
                    preferences JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                self.db_manager.execute_query(create_subscribers_table, fetch=False)
                logger.info("Tabla newsletter_subscribers creada correctamente")

            # Verificar si la tabla de logs de envío existe
            query = "SHOW TABLES LIKE 'newsletter_send_logs'"
            result = self.db_manager.execute_query(query)

            if not result:
                # Crear tabla de logs de envío
                create_logs_table = """
                CREATE TABLE IF NOT EXISTS newsletter_send_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    subscriber_id INT NOT NULL,
                    email_log_id INT,
                    send_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'success',
                    error_message TEXT,
                    pdf_attached BOOLEAN DEFAULT FALSE,
                    signals_included TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subscriber_id) REFERENCES newsletter_subscribers(id) ON DELETE CASCADE,
                    FOREIGN KEY (email_log_id) REFERENCES email_logs(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                self.db_manager.execute_query(create_logs_table, fetch=False)
                logger.info("Tabla newsletter_send_logs creada correctamente")

            return True
        except Exception as e:
            logger.error(f"Error asegurando tablas de suscriptores: {str(e)}")
            return False

    def get_all_subscribers(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene todos los suscriptores del boletín

        Args:
            active_only (bool): Si es True, solo devuelve suscriptores activos

        Returns:
            List[Dict[str, Any]]: Lista de suscriptores
        """
        try:
            query = "SELECT * FROM newsletter_subscribers"
            params = []

            if active_only:
                query += " WHERE active = TRUE"

            query += " ORDER BY name, last_name, email"

            subscribers = self.db_manager.execute_query(query, params)

            # Convertir el campo preferences de JSON a diccionario
            for subscriber in subscribers:
                if subscriber.get("preferences") and isinstance(
                    subscriber["preferences"], str
                ):
                    try:
                        subscriber["preferences"] = json.loads(
                            subscriber["preferences"]
                        )
                    except json.JSONDecodeError:
                        subscriber["preferences"] = {}
                elif not subscriber.get("preferences"):
                    subscriber["preferences"] = {}

            return subscribers
        except Exception as e:
            logger.error(f"Error obteniendo suscriptores: {str(e)}")
            return []

    def get_subscriber_by_id(self, subscriber_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un suscriptor por su ID

        Args:
            subscriber_id (int): ID del suscriptor

        Returns:
            Optional[Dict[str, Any]]: Datos del suscriptor o None si no existe
        """
        try:
            query = "SELECT * FROM newsletter_subscribers WHERE id = %s"
            params = [subscriber_id]

            result = self.db_manager.execute_query(query, params)

            if result and len(result) > 0:
                subscriber = result[0]

                # Convertir el campo preferences de JSON a diccionario
                if subscriber.get("preferences") and isinstance(
                    subscriber["preferences"], str
                ):
                    try:
                        subscriber["preferences"] = json.loads(
                            subscriber["preferences"]
                        )
                    except json.JSONDecodeError:
                        subscriber["preferences"] = {}
                elif not subscriber.get("preferences"):
                    subscriber["preferences"] = {}

                return subscriber
            else:
                return None
        except Exception as e:
            logger.error(f"Error obteniendo suscriptor por ID: {str(e)}")
            return None

    def get_subscriber_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un suscriptor por su correo electrónico

        Args:
            email (str): Correo electrónico del suscriptor

        Returns:
            Optional[Dict[str, Any]]: Datos del suscriptor o None si no existe
        """
        try:
            query = "SELECT * FROM newsletter_subscribers WHERE email = %s"
            params = [email]

            result = self.db_manager.execute_query(query, params)

            if result and len(result) > 0:
                subscriber = result[0]

                # Convertir el campo preferences de JSON a diccionario
                if subscriber.get("preferences") and isinstance(
                    subscriber["preferences"], str
                ):
                    try:
                        subscriber["preferences"] = json.loads(
                            subscriber["preferences"]
                        )
                    except json.JSONDecodeError:
                        subscriber["preferences"] = {}
                elif not subscriber.get("preferences"):
                    subscriber["preferences"] = {}

                return subscriber
            else:
                return None
        except Exception as e:
            logger.error(f"Error obteniendo suscriptor por email: {str(e)}")
            return None

    def add_subscriber(
        self,
        email: str,
        name: str = "",
        last_name: str = "",
        company: str = "",
        preferences: Dict = None,
    ) -> Optional[int]:
        """
        Añade un nuevo suscriptor al boletín

        Args:
            email (str): Correo electrónico del suscriptor
            name (str, optional): Nombre del suscriptor
            last_name (str, optional): Apellido del suscriptor
            company (str, optional): Empresa del suscriptor
            preferences (Dict, optional): Preferencias del suscriptor

        Returns:
            Optional[int]: ID del suscriptor añadido o None si hubo un error
        """
        try:
            # Verificar si el suscriptor ya existe
            existing = self.get_subscriber_by_email(email)
            if existing:
                # Si existe pero está inactivo, activarlo
                if not existing.get("active", True):
                    self.update_subscriber(existing["id"], {"active": True})
                    logger.info(f"Suscriptor reactivado: {email}")
                return existing["id"]

            # Convertir preferencias a JSON
            preferences_json = json.dumps(preferences) if preferences else None

            query = """
            INSERT INTO newsletter_subscribers
            (email, name, last_name, company, preferences, subscription_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = [email, name, last_name, company, preferences_json, datetime.now()]

            subscriber_id = self.db_manager.execute_query(query, params, fetch=False)
            logger.info(f"Nuevo suscriptor añadido: {email}")

            return subscriber_id
        except Exception as e:
            logger.error(f"Error añadiendo suscriptor: {str(e)}")
            return None

    def update_subscriber(self, subscriber_id: int, data: Dict[str, Any]) -> bool:
        """
        Actualiza los datos de un suscriptor

        Args:
            subscriber_id (int): ID del suscriptor
            data (Dict[str, Any]): Datos a actualizar

        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Verificar si el suscriptor existe
            existing = self.get_subscriber_by_id(subscriber_id)
            if not existing:
                logger.warning(f"No se encontró el suscriptor con ID {subscriber_id}")
                return False

            # Preparar campos a actualizar
            update_fields = []
            params = []

            for key, value in data.items():
                if key in ["email", "name", "last_name", "company", "active"]:
                    update_fields.append(f"{key} = %s")
                    params.append(value)
                elif key == "preferences" and isinstance(value, dict):
                    update_fields.append("preferences = %s")
                    params.append(json.dumps(value))

            if not update_fields:
                logger.warning("No hay campos válidos para actualizar")
                return False

            # Construir consulta
            query = f"UPDATE newsletter_subscribers SET {', '.join(update_fields)} WHERE id = %s"
            params.append(subscriber_id)

            self.db_manager.execute_query(query, params, fetch=False)
            logger.info(f"Suscriptor actualizado: ID {subscriber_id}")

            return True
        except Exception as e:
            logger.error(f"Error actualizando suscriptor: {str(e)}")
            return False

    def delete_subscriber(self, subscriber_id: int) -> bool:
        """
        Elimina un suscriptor del boletín

        Args:
            subscriber_id (int): ID del suscriptor

        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        try:
            # Verificar si el suscriptor existe
            existing = self.get_subscriber_by_id(subscriber_id)
            if not existing:
                logger.warning(f"No se encontró el suscriptor con ID {subscriber_id}")
                return False

            query = "DELETE FROM newsletter_subscribers WHERE id = %s"
            params = [subscriber_id]

            self.db_manager.execute_query(query, params, fetch=False)
            logger.info(f"Suscriptor eliminado: ID {subscriber_id}")

            return True
        except Exception as e:
            logger.error(f"Error eliminando suscriptor: {str(e)}")
            return False

    def deactivate_subscriber(self, subscriber_id: int) -> bool:
        """
        Desactiva un suscriptor (alternativa a eliminarlo)

        Args:
            subscriber_id (int): ID del suscriptor

        Returns:
            bool: True si se desactivó correctamente, False en caso contrario
        """
        return self.update_subscriber(subscriber_id, {"active": False})

    def log_newsletter_send(
        self,
        subscriber_id: int,
        email_log_id: int,
        status: str = "success",
        error_message: str = "",
        pdf_attached: bool = False,
        signals_included: str = "",
    ) -> Optional[int]:
        """
        Registra el envío de un boletín a un suscriptor

        Args:
            subscriber_id (int): ID del suscriptor
            email_log_id (int): ID del registro de correo
            status (str, optional): Estado del envío
            error_message (str, optional): Mensaje de error si hubo alguno
            pdf_attached (bool, optional): Si se adjuntó un PDF
            signals_included (str, optional): IDs de las señales incluidas

        Returns:
            Optional[int]: ID del registro de envío o None si hubo un error
        """
        try:
            query = """
            INSERT INTO newsletter_send_logs
            (subscriber_id, email_log_id, status, error_message, pdf_attached, signals_included)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = [
                subscriber_id,
                email_log_id,
                status,
                error_message,
                pdf_attached,
                signals_included,
            ]

            log_id = self.db_manager.execute_query(query, params, fetch=False)

            # Actualizar contador y fecha de último envío del suscriptor
            update_query = """
            UPDATE newsletter_subscribers
            SET send_count = send_count + 1, last_sent_date = %s
            WHERE id = %s
            """
            update_params = [datetime.now(), subscriber_id]

            self.db_manager.execute_query(update_query, update_params, fetch=False)

            return log_id
        except Exception as e:
            logger.error(f"Error registrando envío de boletín: {str(e)}")
            return None

    def get_send_logs(
        self, subscriber_id: Optional[int] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los registros de envío de boletines

        Args:
            subscriber_id (Optional[int], optional): ID del suscriptor para filtrar
            limit (int, optional): Límite de registros a obtener

        Returns:
            List[Dict[str, Any]]: Lista de registros de envío
        """
        try:
            query = """
            SELECT l.*, s.email, s.name, s.last_name
            FROM newsletter_send_logs l
            JOIN newsletter_subscribers s ON l.subscriber_id = s.id
            """
            params = []

            if subscriber_id:
                query += " WHERE l.subscriber_id = %s"
                params.append(subscriber_id)

            query += " ORDER BY l.send_date DESC LIMIT %s"
            params.append(limit)

            return self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Error obteniendo registros de envío: {str(e)}")
            return []

    def get_subscriber_emails(self, active_only: bool = True) -> List[str]:
        """
        Obtiene la lista de correos electrónicos de los suscriptores

        Args:
            active_only (bool): Si es True, solo devuelve suscriptores activos

        Returns:
            List[str]: Lista de correos electrónicos
        """
        try:
            query = "SELECT email FROM newsletter_subscribers"
            params = []

            if active_only:
                query += " WHERE active = TRUE"

            result = self.db_manager.execute_query(query, params)

            return [r["email"] for r in result if r.get("email")]
        except Exception as e:
            logger.error(f"Error obteniendo correos de suscriptores: {str(e)}")
            return []

    def import_subscribers_from_csv(
        self, csv_file_path: str
    ) -> Tuple[int, int, List[str]]:
        """
        Importa suscriptores desde un archivo CSV

        Args:
            csv_file_path (str): Ruta al archivo CSV

        Returns:
            Tuple[int, int, List[str]]: (Número de suscriptores añadidos, número de errores, lista de errores)
        """
        try:
            import csv

            added = 0
            errors = 0
            error_messages = []

            with open(csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    email = row.get("email", "").strip()

                    if not email or "@" not in email:
                        errors += 1
                        error_messages.append(f"Correo inválido: {email}")
                        continue

                    name = row.get("name", "").strip()
                    last_name = row.get("last_name", "").strip()
                    company = row.get("company", "").strip()

                    # Intentar añadir el suscriptor
                    result = self.add_subscriber(email, name, last_name, company)

                    if result:
                        added += 1
                    else:
                        errors += 1
                        error_messages.append(f"Error añadiendo: {email}")

            return added, errors, error_messages
        except Exception as e:
            logger.error(f"Error importando suscriptores desde CSV: {str(e)}")
            return 0, 1, [str(e)]


class NewsletterSubscriberManager:
    """Gestiona los suscriptores del boletín"""

    def __init__(self):
        """Inicializa el gestor de suscriptores"""
        self.db_manager = DatabaseManager()

    def get_all_subscribers(self, active_only=True):
        """Obtiene todos los suscriptores

        Args:
            active_only (bool, optional): Si es True, solo devuelve suscriptores activos. Defaults to True.

        Returns:
            List[Dict[str, Any]]: Lista de suscriptores
        """
        query = "SELECT * FROM newsletter_subscribers"
        params = []

        if active_only:
            query += " WHERE active = 1"

        query += " ORDER BY subscription_date DESC"

        return self.db_manager.execute_query(query, params)

    def get_subscriber_by_email(self, email):
        """Obtiene un suscriptor por su correo electrónico

        Args:
            email (str): Correo electrónico del suscriptor

        Returns:
            Dict[str, Any]: Datos del suscriptor o None si no existe
        """
        query = "SELECT * FROM newsletter_subscribers WHERE email = %s LIMIT 1"
        params = [email]

        result = self.db_manager.execute_query(query, params)
        return result[0] if result and len(result) > 0 else None

    def add_subscriber(self, email, name="", last_name="", company=""):
        """Añade un nuevo suscriptor

        Args:
            email (str): Correo electrónico del suscriptor
            name (str, optional): Nombre del suscriptor. Defaults to "".
            last_name (str, optional): Apellido del suscriptor. Defaults to "".
            company (str, optional): Empresa del suscriptor. Defaults to "".

        Returns:
            bool: True si se añadió correctamente, False en caso contrario
        """
        # Verificar si ya existe
        existing = self.get_subscriber_by_email(email)
        if existing:
            logger.warning(f"El suscriptor {email} ya existe")
            return False

        # Añadir nuevo suscriptor
        query = """INSERT INTO newsletter_subscribers
                  (email, name, last_name, company, active, subscription_date)
                  VALUES (%s, %s, %s, %s, 1, NOW())"""
        params = [email, name, last_name, company]

        result = self.db_manager.execute_query(query, params, fetch=False)
        return result is not None

    def update_subscriber(self, subscriber_id, update_data):
        """Actualiza los datos de un suscriptor

        Args:
            subscriber_id (int): ID del suscriptor
            update_data (Dict[str, Any]): Datos a actualizar

        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        if not update_data:
            logger.warning("No hay datos para actualizar")
            return False

        # Construir consulta de actualización
        update_fields = []
        params = []

        for field, value in update_data.items():
            update_fields.append(f"{field} = %s")
            params.append(value)

        if not update_fields:
            logger.warning("No hay campos válidos para actualizar")
            return False

        query = f"UPDATE newsletter_subscribers SET {', '.join(update_fields)} WHERE id = %s"
        params.append(subscriber_id)

        result = self.db_manager.execute_query(query, params, fetch=False)
        return result is not None

    def delete_subscriber(self, subscriber_id):
        """Elimina un suscriptor

        Args:
            subscriber_id (int): ID del suscriptor

        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        query = "DELETE FROM newsletter_subscribers WHERE id = %s"
        params = [subscriber_id]

        result = self.db_manager.execute_query(query, params, fetch=False)
        return result is not None

    def log_newsletter_send(
        self,
        subscriber_id,
        email_log_id=None,
        status="success",
        error_message=None,
        pdf_attached=False,
        signals_included=None,
    ):
        """Registra el envío de un boletín a un suscriptor

        Args:
            subscriber_id (int): ID del suscriptor
            email_log_id (int, optional): ID del registro de correo. Defaults to None.
            status (str, optional): Estado del envío. Defaults to "success".
            error_message (str, optional): Mensaje de error. Defaults to None.
            pdf_attached (bool, optional): Si se adjuntó un PDF. Defaults to False.
            signals_included (str, optional): Señales incluidas en el boletín. Defaults to None.

        Returns:
            bool: True si se registró correctamente, False en caso contrario
        """
        query = """INSERT INTO newsletter_send_logs
                  (subscriber_id, email_log_id, send_date, status, error_message, pdf_attached, signals_included)
                  VALUES (%s, %s, NOW(), %s, %s, %s, %s)"""
        params = [
            subscriber_id,
            email_log_id,
            status,
            error_message,
            pdf_attached,
            signals_included,
        ]

        result = self.db_manager.execute_query(query, params, fetch=False)

        # Actualizar contador de envíos y fecha del último envío
        if result is not None and status == "success":
            update_query = """UPDATE newsletter_subscribers
                            SET send_count = send_count + 1, last_sent_date = NOW()
                            WHERE id = %s"""
            update_params = [subscriber_id]
            self.db_manager.execute_query(update_query, update_params, fetch=False)

        return result is not None

    def get_send_logs(self, subscriber_id, limit=10):
        """Obtiene los registros de envíos a un suscriptor

        Args:
            subscriber_id (int): ID del suscriptor
            limit (int, optional): Límite de registros a devolver. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: Lista de registros de envíos
        """
        query = """SELECT * FROM newsletter_send_logs
                  WHERE subscriber_id = %s
                  ORDER BY send_date DESC
                  LIMIT %s"""
        params = [subscriber_id, limit]

        return self.db_manager.execute_query(query, params)

    def import_subscribers_from_csv(self, csv_file_path):
        """Importa suscriptores desde un archivo CSV

        Args:
            csv_file_path (str): Ruta al archivo CSV

        Returns:
            Tuple[int, int, List[str]]: (Número de suscriptores añadidos, número de errores, lista de errores)
        """
        try:
            added = 0
            errors = 0
            error_messages = []

            with open(csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    email = row.get("email", "").strip()

                    if not email or "@" not in email:
                        errors += 1
                        error_messages.append(f"Correo inválido: {email}")
                        continue

                    name = row.get("name", "").strip()
                    last_name = row.get("last_name", "").strip()
                    company = row.get("company", "").strip()

                    # Intentar añadir el suscriptor
                    result = self.add_subscriber(email, name, last_name, company)

                    if result:
                        added += 1
                    else:
                        errors += 1
                        error_messages.append(f"Error añadiendo: {email}")

            return added, errors, error_messages
        except Exception as e:
            logger.error(f"Error importando suscriptores desde CSV: {str(e)}")
            return 0, 1, [str(e)]
