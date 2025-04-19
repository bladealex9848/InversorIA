#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para verificar y mejorar la calidad de los datos en la base de datos.
Incluye funciones para obtener registros con campos vacíos y actualizarlos.
"""

import os
import logging
import toml
import mysql.connector
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_db_config() -> Dict[str, Any]:
    """
    Carga la configuración de la base de datos desde secrets.toml

    Returns:
        Dict[str, Any]: Configuración de la base de datos
    """
    try:
        # Ruta al archivo secrets.toml
        secrets_path = os.path.join(".streamlit", "secrets.toml")

        # Verificar si el archivo existe
        if not os.path.exists(secrets_path):
            logger.error(f"El archivo {secrets_path} no existe")
            # Buscar en otras ubicaciones comunes
            alt_paths = [
                "secrets.toml",
                os.path.join("..", ".streamlit", "secrets.toml"),
                os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml"),
            ]

            for path in alt_paths:
                if os.path.exists(path):
                    secrets_path = path
                    logger.info(f"Usando archivo de secretos alternativo: {path}")
                    break
            else:
                raise FileNotFoundError(f"No se encontró el archivo secrets.toml")

        # Leer el archivo secrets.toml
        secrets = toml.load(secrets_path)

        # Intentar obtener configuración con diferentes nombres de variables
        if "mysql" in secrets:
            logger.info(
                "Usando configuración de base de datos desde secrets.toml (formato mysql)"
            )
            return {
                "host": secrets["mysql"].get("host", "localhost"),
                "port": int(secrets["mysql"].get("port", 3306)),
                "user": secrets["mysql"].get("user", "root"),
                "password": secrets["mysql"].get("password", ""),
                "database": secrets["mysql"].get("database", "inversoria"),
            }
        elif "db_host" in secrets:
            logger.info(
                "Usando configuración de base de datos desde secrets.toml (formato db_)"
            )
            return {
                "host": secrets.get("db_host", "localhost"),
                "port": int(secrets.get("db_port", 3306)),
                "user": secrets.get("db_user", "root"),
                "password": secrets.get("db_password", ""),
                "database": secrets.get("db_name", "inversoria"),
            }
        else:
            # No se encontró configuración válida
            logger.error("No se encontró configuración válida en secrets.toml")
            logger.error(
                "Por favor, asegúrate de que el archivo secrets.toml contiene las credenciales de la base de datos"
            )
            logger.error(
                "El archivo debe estar en la carpeta .streamlit o en la raíz del proyecto"
            )
            raise ValueError(
                "Configuración de base de datos no encontrada en secrets.toml"
            )
    except Exception as e:
        logger.error(f"Error cargando configuración: {str(e)}")
        logger.error("No se pudo cargar la configuración de la base de datos")
        logger.error(
            "Por favor, verifica que el archivo secrets.toml existe y contiene las credenciales correctas"
        )
        raise ValueError("Error al cargar la configuración de la base de datos")


def connect_to_db(config: Dict[str, Any]) -> Optional[mysql.connector.MySQLConnection]:
    """
    Conecta a la base de datos usando la configuración proporcionada

    Args:
        config (Dict[str, Any]): Configuración de la base de datos

    Returns:
        Optional[mysql.connector.MySQLConnection]: Conexión a la base de datos o None si hay error
    """
    try:
        connection = mysql.connector.connect(**config)
        logger.info(f"Conexión establecida con la base de datos {config['database']}")
        return connection
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        return None


def get_empty_news_summaries(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Obtiene noticias con resumen vacío

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a obtener

    Returns:
        List[Dict[str, Any]]: Lista de noticias con resumen vacío
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Ejecutar consulta
        query = """
        SELECT id, title, symbol, source, url, news_date, impact
        FROM market_news
        WHERE (summary IS NULL OR summary = '')
        ORDER BY id DESC
        LIMIT %s
        """
        cursor.execute(query, (limit,))

        # Obtener resultados
        results = cursor.fetchall()

        # Cerrar cursor
        cursor.close()

        return results
    except Exception as e:
        logger.error(f"Error obteniendo noticias con resumen vacío: {str(e)}")
        return []


def get_empty_sentiment_analysis(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Obtiene registros de sentimiento con campos críticos vacíos

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a obtener

    Returns:
        List[Dict[str, Any]]: Lista de registros de sentimiento con campos críticos vacíos
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Ejecutar consulta para obtener registros con cualquier campo crítico vacío
        query = """
        SELECT id, date, overall, vix, sp500_trend, technical_indicators, volume, notes,
               symbol, sentiment, score, source, sentiment_date, analysis
        FROM market_sentiment
        WHERE (analysis IS NULL OR analysis = '') OR
              (symbol IS NULL OR symbol = '') OR
              (sentiment IS NULL OR sentiment = '') OR
              (score IS NULL) OR
              (source IS NULL OR source = '') OR
              (sentiment_date IS NULL)
        ORDER BY id DESC
        LIMIT %s
        """
        cursor.execute(query, (limit,))

        # Obtener resultados
        results = cursor.fetchall()

        # Cerrar cursor
        cursor.close()

        return results
    except Exception as e:
        logger.error(
            f"Error obteniendo registros de sentimiento con campos críticos vacíos: {str(e)}"
        )
        return []


def update_news_summary(
    connection: mysql.connector.MySQLConnection, news_id: int, summary: Optional[str]
) -> bool:
    """
    Actualiza el resumen de una noticia

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        news_id (int): ID de la noticia
        summary (Optional[str]): Nuevo resumen o None si no se pudo generar un resumen válido

    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    # Si el resumen es None, no actualizar y devolver False
    if summary is None:
        logger.warning(
            f"No se actualizó el resumen para la noticia {news_id} porque el resumen es None"
        )
        return False

    try:
        cursor = connection.cursor()

        # Ejecutar consulta
        query = """
        UPDATE market_news
        SET summary = %s, updated_at = NOW()
        WHERE id = %s
        """
        cursor.execute(query, (summary, news_id))

        # Confirmar cambios
        connection.commit()

        # Cerrar cursor
        cursor.close()

        return True
    except Exception as e:
        logger.error(f"Error actualizando resumen de noticia {news_id}: {str(e)}")
        return False


def update_news_title(
    connection: mysql.connector.MySQLConnection, news_id: int, title: str
) -> bool:
    """
    Actualiza el título de una noticia

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        news_id (int): ID de la noticia
        title (str): Nuevo título

    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        cursor = connection.cursor()

        # Ejecutar consulta
        query = """
        UPDATE market_news
        SET title = %s, updated_at = NOW()
        WHERE id = %s
        """
        cursor.execute(query, (title, news_id))

        # Confirmar cambios
        connection.commit()

        # Cerrar cursor
        cursor.close()

        return True
    except Exception as e:
        logger.error(f"Error actualizando título de noticia {news_id}: {str(e)}")
        return False


def update_news_url(
    connection: mysql.connector.MySQLConnection, news_id: int, url: str
) -> bool:
    """
    Actualiza la URL de una noticia

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        news_id (int): ID de la noticia
        url (str): Nueva URL

    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        cursor = connection.cursor()

        # Ejecutar consulta
        query = """
        UPDATE market_news
        SET url = %s, updated_at = NOW()
        WHERE id = %s
        """
        cursor.execute(query, (url, news_id))

        # Confirmar cambios
        connection.commit()

        # Cerrar cursor
        cursor.close()

        return True
    except Exception as e:
        logger.error(f"Error actualizando URL de noticia {news_id}: {str(e)}")
        return False


def update_sentiment_analysis(
    connection: mysql.connector.MySQLConnection,
    sentiment_id: int,
    analysis: Optional[str],
    symbol: Optional[str] = None,
    sentiment_value: Optional[str] = None,
    score: Optional[float] = None,
    source: Optional[str] = None,
    sentiment_date: Optional[str] = None,
) -> bool:
    """
    Actualiza los campos de un registro de sentimiento

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        sentiment_id (int): ID del registro de sentimiento
        analysis (Optional[str]): Nuevo análisis o None si no se pudo generar un análisis válido
        symbol (Optional[str]): Símbolo del activo
        sentiment_value (Optional[str]): Valor del sentimiento
        score (Optional[float]): Puntuación del sentimiento
        source (Optional[str]): Fuente del sentimiento
        sentiment_date (Optional[str]): Fecha del sentimiento

    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    # Si todos los campos son None, no actualizar y devolver False
    if all(
        field is None
        for field in [analysis, symbol, sentiment_value, score, source, sentiment_date]
    ):
        logger.warning(
            f"No se actualizó el registro de sentimiento {sentiment_id} porque todos los campos son None"
        )
        return False

    try:
        cursor = connection.cursor()

        # Construir la consulta dinámicamente según los campos proporcionados
        query_parts = ["UPDATE market_sentiment SET"]
        params = []

        # Añadir cada campo a la consulta si no es None
        if analysis is not None:
            query_parts.append("analysis = %s,")
            params.append(analysis)

        if symbol is not None:
            query_parts.append("symbol = %s,")
            params.append(symbol)

        if sentiment_value is not None:
            query_parts.append("sentiment = %s,")
            params.append(sentiment_value)

        if score is not None:
            query_parts.append("score = %s,")
            params.append(score)

        if source is not None:
            query_parts.append("source = %s,")
            params.append(source)

        if sentiment_date is not None:
            query_parts.append("sentiment_date = %s,")
            params.append(sentiment_date)

        # Añadir updated_at y WHERE
        query_parts.append("updated_at = NOW() WHERE id = %s")
        params.append(sentiment_id)

        # Unir las partes de la consulta
        query = " ".join(query_parts)

        # Ejecutar consulta
        cursor.execute(query, params)

        # Confirmar cambios
        connection.commit()

        # Cerrar cursor
        cursor.close()

        return True
    except Exception as e:
        logger.error(
            f"Error actualizando registro de sentimiento {sentiment_id}: {str(e)}"
        )
        return False


def get_database_tables(connection: mysql.connector.MySQLConnection) -> List[str]:
    """
    Obtiene la lista de tablas en la base de datos

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos

    Returns:
        List[str]: Lista de nombres de tablas
    """
    try:
        cursor = connection.cursor()

        # Ejecutar consulta
        query = "SHOW TABLES"
        cursor.execute(query)

        # Obtener resultados
        results = cursor.fetchall()

        # Cerrar cursor
        cursor.close()

        # Extraer nombres de tablas
        tables = [table[0] for table in results]

        return tables
    except Exception as e:
        logger.error(f"Error obteniendo tablas de la base de datos: {str(e)}")
        return []


def get_table_columns(
    connection: mysql.connector.MySQLConnection, table_name: str
) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de columnas de una tabla

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        table_name (str): Nombre de la tabla

    Returns:
        List[Dict[str, Any]]: Lista de información de columnas
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Ejecutar consulta
        query = f"DESCRIBE {table_name}"
        cursor.execute(query)

        # Obtener resultados
        results = cursor.fetchall()

        # Cerrar cursor
        cursor.close()

        return results
    except Exception as e:
        logger.error(f"Error obteniendo columnas de la tabla {table_name}: {str(e)}")
        return []


def get_empty_fields_count(
    connection: mysql.connector.MySQLConnection, table_name: str
) -> Dict[str, int]:
    """
    Obtiene el conteo de campos vacíos por columna en una tabla

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        table_name (str): Nombre de la tabla

    Returns:
        Dict[str, int]: Diccionario con el conteo de campos vacíos por columna
    """
    try:
        # Obtener columnas de la tabla
        columns = get_table_columns(connection, table_name)

        if not columns:
            return {}

        # Inicializar diccionario de resultados
        empty_counts = {}

        # Obtener conteo de campos vacíos para cada columna
        cursor = connection.cursor()

        for column in columns:
            column_name = column["Field"]

            # Ejecutar consulta para contar campos vacíos
            query = f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE {column_name} IS NULL OR {column_name} = ''
            """

            try:
                cursor.execute(query)
                count = cursor.fetchone()[0]

                # Añadir al diccionario si hay campos vacíos
                if count > 0:
                    empty_counts[column_name] = count
            except Exception as e:
                logger.warning(
                    f"Error contando campos vacíos para {table_name}.{column_name}: {str(e)}"
                )

        # Cerrar cursor
        cursor.close()

        return empty_counts
    except Exception as e:
        logger.error(
            f"Error obteniendo conteo de campos vacíos para la tabla {table_name}: {str(e)}"
        )
        return {}


def get_empty_news_symbols(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Obtiene noticias con símbolos marcados para revisión (symbol = 'REVIEW')

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a obtener

    Returns:
        List[Dict[str, Any]]: Lista de noticias con símbolos para revisión
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Ejecutar consulta
        query = """
        SELECT id, title, summary, source, url, news_date, symbol
        FROM market_news
        WHERE symbol = 'REVIEW'
        ORDER BY news_date DESC
        LIMIT %s
        """
        cursor.execute(query, (limit,))

        # Obtener resultados
        results = cursor.fetchall()

        # Cerrar cursor
        cursor.close()

        return results
    except Exception as e:
        logger.error(f"Error obteniendo noticias con símbolos para revisión: {str(e)}")
        return []


def get_empty_trading_signals_analysis(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Obtiene señales de trading con análisis experto vacío

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a obtener

    Returns:
        List[Dict[str, Any]]: Lista de señales de trading con análisis experto vacío
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Ejecutar consulta
        query = """
        SELECT id, symbol, price, direction, confidence_level, timeframe, strategy,
               category, analysis, technical_analysis, support_level, resistance_level,
               rsi, trend, trend_strength, volatility, options_signal, options_analysis,
               trading_specialist_signal, trading_specialist_confidence, sentiment,
               sentiment_score, signal_date, latest_news, news_source, additional_news
        FROM trading_signals
        WHERE (expert_analysis IS NULL OR expert_analysis = '')
        ORDER BY id DESC
        LIMIT %s
        """
        cursor.execute(query, (limit,))

        # Obtener resultados
        results = cursor.fetchall()

        # Cerrar cursor
        cursor.close()

        return results
    except Exception as e:
        logger.error(
            f"Error obteniendo señales de trading con análisis experto vacío: {str(e)}"
        )
        return []


def get_error_trading_signals_analysis(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Obtiene señales de trading con errores en el análisis experto

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a obtener

    Returns:
        List[Dict[str, Any]]: Lista de señales de trading con errores en el análisis experto
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Ejecutar consulta para buscar análisis que contengan mensajes de error comunes
        query = """
        SELECT id, symbol, price, direction, confidence_level, timeframe, strategy,
               category, analysis, technical_analysis, support_level, resistance_level,
               rsi, trend, trend_strength, volatility, options_signal, options_analysis,
               trading_specialist_signal, trading_specialist_confidence, sentiment,
               sentiment_score, signal_date, latest_news, news_source, additional_news,
               expert_analysis
        FROM trading_signals
        WHERE expert_analysis LIKE '%%Error%%' OR
              expert_analysis LIKE '%%error%%' OR
              expert_analysis LIKE '%%st.session_state%%' OR
              expert_analysis LIKE '%%AttributeError%%' OR
              expert_analysis LIKE '%%Exception%%'
        ORDER BY id DESC
        LIMIT %s
        """
        cursor.execute(query, (limit,))

        # Obtener resultados
        results = cursor.fetchall()

        # Cerrar cursor
        cursor.close()

        return results
    except Exception as e:
        logger.error(
            f"Error obteniendo señales de trading con errores en el análisis experto: {str(e)}"
        )
        return []


def update_trading_signal_analysis(
    connection: mysql.connector.MySQLConnection,
    signal_id: int,
    analysis: Optional[str],
) -> bool:
    """
    Actualiza el análisis experto de una señal de trading

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        signal_id (int): ID de la señal de trading
        analysis (Optional[str]): Nuevo análisis o None si no se pudo generar un análisis válido

    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    # Si el análisis es None, no actualizar y devolver False
    if analysis is None:
        logger.warning(
            f"No se actualizó el análisis experto para la señal {signal_id} porque el análisis es None"
        )
        return False

    try:
        cursor = connection.cursor()

        # Ejecutar consulta
        query = """
        UPDATE trading_signals
        SET expert_analysis = %s, updated_at = NOW()
        WHERE id = %s
        """
        cursor.execute(query, (analysis, signal_id))

        # Confirmar cambios
        connection.commit()

        # Cerrar cursor
        cursor.close()

        return True
    except Exception as e:
        logger.error(
            f"Error actualizando análisis experto de señal {signal_id}: {str(e)}"
        )
        return False


if __name__ == "__main__":
    # Pruebas básicas
    try:
        # Cargar configuración
        config = load_db_config()

        # Conectar a la base de datos
        connection = connect_to_db(config)

        if connection:
            print("Conexión establecida correctamente")

            # Obtener tablas
            tables = get_database_tables(connection)
            print(f"Tablas en la base de datos: {tables}")

            # Obtener información de campos vacíos
            for table in tables:
                empty_counts = get_empty_fields_count(connection, table)
                if empty_counts:
                    print(f"\nCampos vacíos en la tabla {table}:")
                    for column, count in empty_counts.items():
                        print(f"  - {column}: {count} registros")
                else:
                    print(f"\nNo hay campos vacíos en la tabla {table}")

            # Obtener noticias con resumen vacío
            empty_news = get_empty_news_summaries(connection, 5)
            print(f"\nNoticias con resumen vacío: {len(empty_news)}")

            # Obtener registros de sentimiento con análisis vacío
            empty_sentiment = get_empty_sentiment_analysis(connection, 5)
            print(
                f"Registros de sentimiento con análisis vacío: {len(empty_sentiment)}"
            )

            # Cerrar conexión
            connection.close()
            print("\nConexión cerrada")
        else:
            print("No se pudo establecer conexión con la base de datos")
    except Exception as e:
        print(f"Error en las pruebas: {str(e)}")
