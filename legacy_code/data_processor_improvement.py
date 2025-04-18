#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para mejorar el procesamiento de datos antes de guardarlos en la base de datos.
Este script analiza los registros con campos vacíos y los procesa con el experto en IA.
"""

import logging
import sys
import os
import toml
import mysql.connector
from datetime import datetime
import time
import re
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Intentar importar el experto en IA
AI_EXPERT_AVAILABLE = False
try:
    from ai_utils import AIExpert

    AI_EXPERT_AVAILABLE = True
    logger.info("AIExpert disponible para uso")
except ImportError:
    logger.warning("AIExpert no está disponible. Se usarán métodos alternativos.")

# Intentar importar el scraper de Yahoo Finance
YAHOO_SCRAPER_AVAILABLE = False
try:
    from yahoo_finance_scraper import YahooFinanceScraper

    YAHOO_SCRAPER_AVAILABLE = True
    logger.info("YahooFinanceScraper disponible para uso")
except ImportError:
    logger.warning(
        "YahooFinanceScraper no está disponible. Se usarán métodos alternativos."
    )

# Intentar importar el validador de datos
DATA_VALIDATOR_AVAILABLE = False
try:
    from utils.data_validator import DataValidator

    DATA_VALIDATOR_AVAILABLE = True
    logger.info("DataValidator disponible para uso")
except ImportError:
    logger.warning("DataValidator no está disponible. Se usarán métodos alternativos.")


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
    Obtiene registros de sentimiento con análisis vacío

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a obtener

    Returns:
        List[Dict[str, Any]]: Lista de registros de sentimiento con análisis vacío
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Ejecutar consulta
        query = """
        SELECT id, date, overall, vix, sp500_trend, technical_indicators, volume, notes
        FROM market_sentiment
        WHERE (analysis IS NULL OR analysis = '')
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
            f"Error obteniendo registros de sentimiento con análisis vacío: {str(e)}"
        )
        return []


def update_news_summary(
    connection: mysql.connector.MySQLConnection, news_id: int, summary: str
) -> bool:
    """
    Actualiza el resumen de una noticia

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        news_id (int): ID de la noticia
        summary (str): Nuevo resumen

    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
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


def update_sentiment_analysis(
    connection: mysql.connector.MySQLConnection, sentiment_id: int, analysis: str
) -> bool:
    """
    Actualiza el análisis de un registro de sentimiento

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        sentiment_id (int): ID del registro de sentimiento
        analysis (str): Nuevo análisis

    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        cursor = connection.cursor()

        # Ejecutar consulta
        query = """
        UPDATE market_sentiment
        SET analysis = %s, updated_at = NOW()
        WHERE id = %s
        """
        cursor.execute(query, (analysis, sentiment_id))

        # Confirmar cambios
        connection.commit()

        # Cerrar cursor
        cursor.close()

        return True
    except Exception as e:
        logger.error(
            f"Error actualizando análisis de sentimiento {sentiment_id}: {str(e)}"
        )
        return False


def get_news_from_yahoo(symbol: str, max_news: int = 5) -> List[Dict[str, Any]]:
    """
    Obtiene noticias de Yahoo Finance

    Args:
        symbol (str): Símbolo del activo
        max_news (int): Número máximo de noticias a obtener

    Returns:
        List[Dict[str, Any]]: Lista de noticias
    """
    if not YAHOO_SCRAPER_AVAILABLE:
        logger.warning(
            "YahooFinanceScraper no está disponible. No se pueden obtener noticias de Yahoo Finance."
        )
        return []

    try:
        # Inicializar scraper
        scraper = YahooFinanceScraper()

        # Obtener noticias
        news = scraper.get_news(symbol, max_news)

        return news
    except Exception as e:
        logger.error(
            f"Error obteniendo noticias de Yahoo Finance para {symbol}: {str(e)}"
        )
        return []


def generate_summary_with_ai(title: str, symbol: str, url: str = None) -> Optional[str]:
    """
    Genera un resumen de noticia utilizando IA

    Args:
        title (str): Título de la noticia
        symbol (str): Símbolo del activo
        url (str, optional): URL de la noticia

    Returns:
        str: Resumen generado
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning(
            "AIExpert no está disponible. No se puede generar resumen con IA."
        )
        return None

    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()

        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, "client") or not ai_expert.client:
            logger.warning("Cliente OpenAI no disponible. No se puede generar resumen.")
            return None

        # Crear prompt para generar resumen (sin espacios al inicio de cada línea)
        prompt = f"""Genera un resumen informativo y detallado en español (150-200 caracteres)
para una noticia financiera sobre {symbol} con este título: '{title}'.

El resumen debe:
1. Ser específico y relevante para inversores
2. Incluir posibles implicaciones para el precio de la acción
3. Estar escrito en un tono profesional y objetivo
4. NO incluir frases genéricas de introducción o cierre
5. Ir directo al punto principal de la noticia"""

        # Generar resumen
        summary = ai_expert.process_text(prompt, max_tokens=250)

        # Verificar si el resumen contiene parte del prompt (caso de fallback)
        if (
            not summary
            or "Genera un resumen informativo" in summary
            or "Como experto financiero" in summary
        ):
            logger.warning(
                "El resumen generado contiene parte del prompt o está vacío."
            )
            return None

            # Limpiar resumen
            # Eliminar comillas al inicio y final
            summary = re.sub(r'^["\']|["\']$', "", summary)

            # Reemplazar múltiples saltos de línea por uno solo
            summary = re.sub(r"\n+", " ", summary)

            # Reemplazar múltiples espacios por uno solo
            summary = re.sub(r"\s+", " ", summary)

            # Eliminar espacios al inicio y final
            summary = summary.strip()

            return summary

        return f"Noticia relacionada con {symbol}: {title}"
    except Exception as e:
        logger.error(f"Error generando resumen con IA: {str(e)}")
        return f"Noticia relacionada con {symbol}: {title}"


def generate_sentiment_analysis_with_ai(sentiment_data: Dict[str, Any]) -> str:
    """
    Genera un análisis de sentimiento utilizando IA

    Args:
        sentiment_data (Dict[str, Any]): Datos de sentimiento

    Returns:
        str: Análisis generado
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning(
            "AIExpert no está disponible. No se puede generar análisis con IA."
        )
        return f"Sentimiento de mercado: {sentiment_data.get('overall', 'Neutral')}"

    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()

        # Recopilar datos disponibles para generar un análisis completo
        overall = sentiment_data.get("overall", "Neutral")
        vix = sentiment_data.get("vix", "N/A")
        sp500_trend = sentiment_data.get("sp500_trend", "N/A")
        tech_indicators = sentiment_data.get("technical_indicators", "N/A")

        # Crear prompt para generar análisis
        prompt = f"""
        Como analista financiero experto, genera un análisis detallado del sentimiento de mercado
        basado en los siguientes datos:

        - Sentimiento general: {overall}
        - VIX (índice de volatilidad): {vix}
        - Tendencia S&P500: {sp500_trend}
        - Indicadores técnicos: {tech_indicators}

        El análisis debe:
        1. Explicar las implicaciones de estos datos para inversores
        2. Incluir una evaluación de riesgos y oportunidades
        3. Proporcionar contexto sobre la situación actual del mercado
        4. Estar escrito en español profesional y objetivo
        5. Tener entre 150-300 palabras
        6. NO incluir frases genéricas de introducción o cierre
        """

        # Generar análisis
        analysis = ai_expert.process_text(prompt, max_tokens=500)

        # Limpiar análisis
        if analysis:
            # Eliminar comillas al inicio y final
            analysis = re.sub(r'^["\']|["\']$', "", analysis)

            # Reemplazar múltiples saltos de línea por uno solo
            analysis = re.sub(r"\n+", " ", analysis)

            # Reemplazar múltiples espacios por uno solo
            analysis = re.sub(r"\s+", " ", analysis)

            # Eliminar espacios al inicio y final
            analysis = analysis.strip()

            return analysis

        return f"El mercado muestra un sentimiento {overall.lower()} con VIX en {vix} y tendencia {sp500_trend.lower()} en el S&P500."
    except Exception as e:
        logger.error(f"Error generando análisis con IA: {str(e)}")
        return f"Sentimiento de mercado: {sentiment_data.get('overall', 'Neutral')}"


def translate_title_to_spanish(title: str) -> str:
    """
    Traduce un título al español utilizando IA

    Args:
        title (str): Título a traducir

    Returns:
        str: Título traducido
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning("AIExpert no está disponible. No se puede traducir título.")
        return title

    # Verificar si el título ya está en español
    if not is_english_text(title):
        return title

    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()

        # Crear prompt para traducir título
        prompt = f"""
        Traduce este título de noticia financiera al español de forma profesional y concisa:
        '{title}'

        La traducción debe:
        1. Mantener el significado original
        2. Usar terminología financiera correcta en español
        3. Ser clara y directa
        4. NO exceder la longitud original significativamente
        """

        # Traducir título
        translated_title = ai_expert.process_text(prompt, max_tokens=150)

        # Limpiar título traducido
        if translated_title:
            # Eliminar comillas al inicio y final
            translated_title = re.sub(r'^["\']|["\']$', "", translated_title)

            # Reemplazar múltiples saltos de línea por uno solo
            translated_title = re.sub(r"\n+", " ", translated_title)

            # Reemplazar múltiples espacios por uno solo
            translated_title = re.sub(r"\s+", " ", translated_title)

            # Eliminar espacios al inicio y final
            translated_title = translated_title.strip()

            return translated_title

        return title
    except Exception as e:
        logger.error(f"Error traduciendo título con IA: {str(e)}")
        return title


def translate_title_to_spanish_without_ai(title: str) -> str:
    """
    Traduce un título al español sin usar IA (traducción básica)

    Args:
        title (str): Título a traducir

    Returns:
        str: Título traducido de forma básica
    """
    # Diccionario básico de traducción para palabras comunes en títulos financieros
    translation_dict = {
        "stock": "acción",
        "stocks": "acciones",
        "market": "mercado",
        "markets": "mercados",
        "price": "precio",
        "prices": "precios",
        "rise": "sube",
        "rises": "sube",
        "fall": "cae",
        "falls": "cae",
        "drop": "cae",
        "drops": "cae",
        "gain": "gana",
        "gains": "gana",
        "lose": "pierde",
        "loses": "pierde",
        "bull": "alcista",
        "bear": "bajista",
        "bullish": "alcista",
        "bearish": "bajista",
        "up": "arriba",
        "down": "abajo",
        "high": "alto",
        "low": "bajo",
        "report": "informe",
        "reports": "informes",
        "earnings": "ganancias",
        "revenue": "ingresos",
        "profit": "beneficio",
        "profits": "beneficios",
        "loss": "pérdida",
        "losses": "pérdidas",
        "investor": "inversor",
        "investors": "inversores",
        "trading": "operaciones",
        "trader": "operador",
        "traders": "operadores",
        "buy": "compra",
        "sell": "venta",
        "buys": "compra",
        "sells": "vende",
        "bought": "compró",
        "sold": "vendió",
        "crypto": "cripto",
        "cryptocurrency": "criptomoneda",
        "cryptocurrencies": "criptomonedas",
        "bitcoin": "Bitcoin",
        "ethereum": "Ethereum",
        "ripple": "Ripple",
        "the": "",
        "a": "",
        "an": "",
        "and": "y",
        "or": "o",
        "in": "en",
        "on": "en",
        "at": "en",
        "to": "a",
        "for": "para",
        "with": "con",
        "without": "sin",
        "by": "por",
        "from": "de",
        "of": "de",
        "as": "como",
        "is": "es",
        "are": "son",
        "was": "fue",
        "were": "fueron",
        "will": "será",
        "would": "sería",
        "could": "podría",
        "should": "debería",
        "can": "puede",
        "cannot": "no puede",
        "not": "no",
        "no": "no",
        "yes": "sí",
    }

    # Dividir el título en palabras
    words = title.split()

    # Traducir cada palabra
    translated_words = []
    for word in words:
        # Eliminar puntuación al final de la palabra para buscarla en el diccionario
        clean_word = word.lower().rstrip(".,;:!?")
        punctuation = word[len(clean_word) :] if len(clean_word) < len(word) else ""

        # Buscar en el diccionario
        if clean_word in translation_dict:
            translated_word = translation_dict[clean_word]
            # Si la palabra original empieza con mayúscula, mantener la mayúscula
            if word[0].isupper() and translated_word:
                translated_word = translated_word[0].upper() + translated_word[1:]
            translated_words.append(translated_word + punctuation)
        else:
            translated_words.append(word)

    # Unir las palabras traducidas
    translated_title = " ".join(word for word in translated_words if word)

    return translated_title


def is_english_text(text: str) -> bool:
    """
    Detecta si un texto está en inglés

    Args:
        text (str): Texto a analizar

    Returns:
        bool: True si el texto parece estar en inglés, False en caso contrario
    """
    if not text or len(text) < 10:
        return False

    # Palabras comunes en inglés que no suelen usarse en español
    english_words = [
        r"\bthe\b",
        r"\band\b",
        r"\bof\b",
        r"\bto\b",
        r"\ba\b",
        r"\bin\b",
        r"\bthat\b",
        r"\bhave\b",
        r"\bI\b",
        r"\bit\b",
        r"\bfor\b",
        r"\bnot\b",
        r"\bon\b",
        r"\bwith\b",
        r"\bhe\b",
        r"\bas\b",
        r"\byou\b",
        r"\bdo\b",
        r"\bat\b",
        r"\bthis\b",
        r"\bbut\b",
        r"\bhis\b",
        r"\bby\b",
        r"\bfrom\b",
        r"\bthey\b",
        r"\bwe\b",
        r"\bsay\b",
        r"\bher\b",
        r"\bshe\b",
        r"\bor\b",
        r"\ban\b",
        r"\bwill\b",
        r"\bmy\b",
        r"\bone\b",
        r"\ball\b",
        r"\bwould\b",
        r"\bthere\b",
        r"\btheir\b",
        r"\bwhat\b",
        r"\bso\b",
        r"\bup\b",
        r"\bout\b",
        r"\bif\b",
        r"\babout\b",
        r"\bwho\b",
        r"\bget\b",
        r"\bwhich\b",
        r"\bgo\b",
        r"\bme\b",
        r"\bwhen\b",
        r"\bmake\b",
        r"\bcan\b",
        r"\blike\b",
        r"\btime\b",
        r"\bno\b",
        r"\bjust\b",
        r"\bhim\b",
        r"\bknow\b",
        r"\btake\b",
        r"\bpeople\b",
    ]

    # Contar palabras en inglés
    english_count = 0
    for word in english_words:
        if re.search(word, text.lower()):
            english_count += 1

    # Si hay más de 3 palabras en inglés, consideramos que el texto está en inglés
    return english_count > 3


def process_empty_news_summaries(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> int:
    """
    Procesa noticias con resumen vacío

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a procesar

    Returns:
        int: Número de registros procesados
    """
    # Obtener noticias con resumen vacío
    empty_news = get_empty_news_summaries(connection, limit)

    if not empty_news:
        logger.info("No hay noticias con resumen vacío para procesar")
        return 0

    logger.info(f"Se encontraron {len(empty_news)} noticias con resumen vacío")

    # Procesar cada noticia
    processed_count = 0
    for news in empty_news:
        news_id = news.get("id")
        title = news.get("title", "")
        symbol = news.get("symbol", "SPY")
        url = news.get("url", "")

        logger.info(f"Procesando noticia ID {news_id}: {title[:50]}...")

        # Traducir título si está en inglés
        original_title = title
        translated_title = translate_title_to_spanish(title)
        if translated_title != original_title:
            logger.info(f"Título traducido: {translated_title}")

            # Actualizar título en la base de datos
            try:
                cursor = connection.cursor()
                query = "UPDATE market_news SET title = %s, updated_at = NOW() WHERE id = %s"
                cursor.execute(query, (translated_title, news_id))
                connection.commit()
                cursor.close()
                logger.info(f"Título actualizado para noticia ID {news_id}")

                # Usar el título traducido para generar el resumen
                title = translated_title
            except Exception as e:
                logger.error(
                    f"Error actualizando título para noticia ID {news_id}: {str(e)}"
                )

        # Intentar obtener noticias de Yahoo Finance si no hay URL
        if not url and YAHOO_SCRAPER_AVAILABLE:
            yahoo_news = get_news_from_yahoo(symbol, 1)
            if yahoo_news:
                # Usar la primera noticia como referencia
                url = yahoo_news[0].get("url", "")
                logger.info(f"URL obtenida de Yahoo Finance: {url}")

                # Actualizar URL en la base de datos
                try:
                    cursor = connection.cursor()
                    query = "UPDATE market_news SET url = %s, updated_at = NOW() WHERE id = %s"
                    cursor.execute(query, (url, news_id))
                    connection.commit()
                    cursor.close()
                    logger.info(f"URL actualizada para noticia ID {news_id}")
                except Exception as e:
                    logger.error(
                        f"Error actualizando URL para noticia ID {news_id}: {str(e)}"
                    )

        # Generar resumen con IA
        summary = generate_summary_with_ai(title, symbol, url)

        # Actualizar resumen en la base de datos
        if update_news_summary(connection, news_id, summary):
            logger.info(f"Resumen actualizado para noticia ID {news_id}")
            processed_count += 1
        else:
            logger.error(f"Error actualizando resumen para noticia ID {news_id}")

        # Esperar un poco para no sobrecargar la API
        time.sleep(1)

    return processed_count


def process_empty_sentiment_analysis(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> int:
    """
    Procesa registros de sentimiento con análisis vacío

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a procesar

    Returns:
        int: Número de registros procesados
    """
    # Obtener registros de sentimiento con análisis vacío
    empty_sentiment = get_empty_sentiment_analysis(connection, limit)

    if not empty_sentiment:
        logger.info("No hay registros de sentimiento con análisis vacío para procesar")
        return 0

    logger.info(
        f"Se encontraron {len(empty_sentiment)} registros de sentimiento con análisis vacío"
    )

    # Procesar cada registro
    processed_count = 0
    for sentiment in empty_sentiment:
        sentiment_id = sentiment.get("id")

        logger.info(f"Procesando sentimiento ID {sentiment_id}...")

        # Generar análisis con IA
        analysis = generate_sentiment_analysis_with_ai(sentiment)

        # Actualizar análisis en la base de datos
        if update_sentiment_analysis(connection, sentiment_id, analysis):
            logger.info(f"Análisis actualizado para sentimiento ID {sentiment_id}")
            processed_count += 1
        else:
            logger.error(
                f"Error actualizando análisis para sentimiento ID {sentiment_id}"
            )

        # Esperar un poco para no sobrecargar la API
        time.sleep(1)

    return processed_count


def main():
    """Función principal"""
    try:
        # Cargar configuración
        db_config = load_db_config()

        # Conectar a la base de datos
        connection = connect_to_db(db_config)
        if not connection:
            logger.error("No se pudo conectar a la base de datos")
            return

        # Procesar noticias con resumen vacío
        news_processed = process_empty_news_summaries(connection, 10)
        logger.info(f"Se procesaron {news_processed} noticias con resumen vacío")

        # Procesar registros de sentimiento con análisis vacío
        sentiment_processed = process_empty_sentiment_analysis(connection, 5)
        logger.info(
            f"Se procesaron {sentiment_processed} registros de sentimiento con análisis vacío"
        )

        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")

        # Mostrar resumen
        print("\n" + "=" * 80)
        print("RESUMEN DE PROCESAMIENTO")
        print("=" * 80)
        print(f"Noticias procesadas: {news_processed}")
        print(f"Registros de sentimiento procesados: {sentiment_processed}")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")


if __name__ == "__main__":
    main()
