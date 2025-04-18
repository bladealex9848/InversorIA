#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador de calidad de datos para la base de datos.
Este script analiza los registros con campos vacíos y los procesa con el experto en IA.
Versión standalone que no depende de Streamlit.
"""

import logging
import sys
import time
from typing import Dict, List, Any, Optional
import mysql.connector

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
from data_enrichment import get_news_from_yahoo

# Importar la versión standalone de AIExpert que utiliza el modelo y asistente configurados en secrets.toml
from ai_expert_fix import (
    StandaloneAIExpert,
    generate_summary_with_ai,
    generate_sentiment_analysis_with_ai,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


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

        # Generar resumen con IA usando la versión standalone
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

        # Generar análisis con IA usando la versión standalone
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
