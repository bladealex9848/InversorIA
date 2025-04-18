"""
InversorIA Pro - Utilidades de Base de Datos
--------------------------------------------
Este archivo contiene clases y funciones para gestionar la conexión y operaciones con la base de datos.
"""

import logging
import mysql.connector
from datetime import datetime
import streamlit as st
from typing import Dict, List, Any, Optional, Union

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
                        logger.info(
                            "No se pudo identificar un símbolo, usando SPY como valor por defecto"
                        )
                except Exception as e:
                    logger.warning(
                        f"Error al usar IA para identificar símbolo: {str(e)}"
                    )
                    # Usar SPY como valor por defecto
                    news_data["symbol"] = "SPY"
                    logger.info(
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
                "symbol", "SPY"
            ),  # Usar SPY como valor por defecto si no hay símbolo
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

                    # Procesar solo las noticias
                    post_save_quality_check.process_quality_after_save(
                        table_name="news", limit=1
                    )
                    logger.info(
                        f"Procesamiento de calidad completado para la noticia {news_id}"
                    )
                except Exception as e:
                    logger.warning(f"Error en el procesamiento de calidad: {str(e)}")
                    logger.warning(f"Traza completa:", exc_info=True)

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

        # Asegurar que la fecha esté presente
        if not sentiment_data.get("date"):
            sentiment_data["date"] = datetime.now().date()

        # Asegurar que los campos adicionales estén presentes
        if not sentiment_data.get("symbol"):
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

            params = (
                cleaned_data.get("overall", "Neutral"),
                cleaned_data.get("vix", "N/A"),
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
                    logger.warning(f"Traza completa:", exc_info=True)

            return sentiment_id
        else:
            # Insertar nuevo registro con todos los campos
            insert_query = """INSERT INTO market_sentiment
                          (date, overall, vix, sp500_trend, technical_indicators, volume, notes,
                           symbol, sentiment, score, source, analysis, sentiment_date, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())"""

            params = (
                cleaned_data.get("date", datetime.now().date()),
                cleaned_data.get("overall", "Neutral"),
                cleaned_data.get("vix", "N/A"),
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
                    logger.warning(f"Traza completa:", exc_info=True)

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
                logger.warning(f"Traza completa:", exc_info=True)

        return signal_id

    except Exception as e:
        logger.error(f"Error guardando señal de trading: {str(e)}")
        return None


def extract_symbol_from_title(title: str) -> Optional[str]:
    """
    Extrae el símbolo de una acción o ETF del título de una noticia.
    Utiliza company_data.py para validar los símbolos encontrados.

    Args:
        title (str): Título de la noticia

    Returns:
        Optional[str]: Símbolo extraído o None si no se encuentra
    """
    if not title:
        return None

    # Importar re si no está disponible en este contexto
    import re

    # Importar datos de company_data.py
    from company_data import COMPANY_INFO

    # Buscar patrones comunes de símbolos en el título
    # Patrón 1: Símbolos entre paréntesis como (AAPL), (TSLA), etc.
    parenthesis_pattern = r"\(([A-Z]{1,5})\)"
    matches = re.findall(parenthesis_pattern, title)
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
        ]
        for match in matches:
            if match not in common_abbr and len(match) >= 2 and len(match) <= 5:
                # Verificar si el símbolo existe en COMPANY_INFO
                if match in COMPANY_INFO:
                    return match

    # Patrón 2: Símbolos con prefijo NYSE: o NASDAQ: como NYSE:AAPL, NASDAQ:TSLA, etc.
    exchange_pattern = r"(NYSE|NASDAQ):\s*([A-Z]{1,5})"
    matches = re.findall(exchange_pattern, title)
    if matches:
        symbol = matches[0][1]  # Devolver el símbolo, no el exchange
        # Verificar si el símbolo existe en COMPANY_INFO
        if symbol in COMPANY_INFO:
            return symbol

    # Patrón 3: Buscar símbolos directamente en el texto (palabras en mayúsculas de 2-5 letras)
    ticker_pattern = r"\b([A-Z]{2,5})\b"
    matches = re.findall(ticker_pattern, title)
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
        ]
        for match in matches:
            if match not in common_words and match in COMPANY_INFO:
                return match

    # Patrón 4: Buscar nombres de empresas en el título
    # Crear un diccionario inverso de nombres de empresas a símbolos
    company_name_to_symbol = {}
    for symbol, info in COMPANY_INFO.items():
        company_name = info.get("name", "")
        if company_name:
            # Guardar el nombre completo
            company_name_to_symbol[company_name] = symbol
            # Guardar también la primera palabra del nombre (para casos como "Apple Inc." -> "Apple")
            first_word = company_name.split()[0]
            if len(first_word) > 2:  # Evitar palabras muy cortas
                company_name_to_symbol[first_word] = symbol

    # Buscar coincidencias de nombres de empresas en el título
    for company_name, symbol in company_name_to_symbol.items():
        if company_name in title:
            return symbol

    # Si no se encuentra ningún símbolo, devolver None
    return None
