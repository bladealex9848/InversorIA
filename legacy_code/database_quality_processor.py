#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador de calidad de datos para la base de datos.
Este script analiza los registros con campos vacíos y los procesa con el experto en IA.
"""

import logging
import sys
import time
from typing import Dict, List, Any, Optional

# Importar módulos propios
from database_quality_utils import (
    load_db_config,
    connect_to_db,
    get_empty_news_summaries,
    get_empty_sentiment_analysis,
    update_news_summary,
    update_news_title,
    update_news_url,
    update_sentiment_analysis,
)
from text_processing import translate_title_to_spanish
from ai_content_generator import (
    generate_summary_with_ai,
    generate_sentiment_analysis_with_ai,
)
from data_enrichment import get_news_from_yahoo

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def process_empty_news_summaries(connection, limit: int = 10) -> int:
    """
    Procesa noticias con resumen vacío

    Args:
        connection: Conexión a la base de datos
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
            if update_news_title(connection, news_id, translated_title):
                logger.info(f"Título actualizado para noticia ID {news_id}")

                # Usar el título traducido para generar el resumen
                title = translated_title
            else:
                logger.error(f"Error actualizando título para noticia ID {news_id}")

        # Intentar obtener noticias de Yahoo Finance si no hay URL
        if not url:
            yahoo_news = get_news_from_yahoo(symbol, 1)
            if yahoo_news:
                # Usar la primera noticia como referencia
                url = yahoo_news[0].get("url", "")
                logger.info(f"URL obtenida de Yahoo Finance: {url}")

                # Actualizar URL en la base de datos
                if update_news_url(connection, news_id, url):
                    logger.info(f"URL actualizada para noticia ID {news_id}")
                else:
                    logger.error(f"Error actualizando URL para noticia ID {news_id}")

        # Generar resumen con IA
        summary = generate_summary_with_ai(title, symbol, url)

        # Actualizar resumen en la base de datos solo si se generó un resumen válido
        if summary is not None:
            if update_news_summary(connection, news_id, summary):
                logger.info(f"Resumen actualizado para noticia ID {news_id}")
                processed_count += 1
            else:
                logger.error(f"Error actualizando resumen para noticia ID {news_id}")
        else:
            logger.warning(
                f"No se pudo generar un resumen válido para la noticia ID {news_id}"
            )

        # Esperar un poco para no sobrecargar la API
        time.sleep(1)

    return processed_count


def process_empty_sentiment_analysis(connection, limit: int = 10) -> int:
    """
    Procesa registros de sentimiento con análisis vacío

    Args:
        connection: Conexión a la base de datos
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

        # Actualizar análisis en la base de datos solo si se generó un análisis válido
        if analysis is not None:
            if update_sentiment_analysis(connection, sentiment_id, analysis):
                logger.info(f"Análisis actualizado para sentimiento ID {sentiment_id}")
                processed_count += 1
            else:
                logger.error(
                    f"Error actualizando análisis para sentimiento ID {sentiment_id}"
                )
        else:
            logger.warning(
                f"No se pudo generar un análisis válido para el sentimiento ID {sentiment_id}"
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


def update_sentiment_analysis(
    connection: mysql.connector.MySQLConnection,
    sentiment_id: int,
    analysis: Optional[str],
) -> bool:
    """
    Actualiza el análisis de un registro de sentimiento

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        sentiment_id (int): ID del registro de sentimiento
        analysis (Optional[str]): Nuevo análisis o None si no se pudo generar un análisis válido

    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    # Si el análisis es None, no actualizar y devolver False
    if analysis is None:
        logger.warning(
            f"No se actualizó el análisis para el sentimiento {sentiment_id} porque el análisis es None"
        )
        return False

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


# Funciones para análisis de texto


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


# Funciones para conexión a la base de datos


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
