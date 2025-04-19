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
        print("No hay noticias con resumen vacío para procesar")
        return 0

    print(f"Se encontraron {len(empty_news)} noticias con resumen vacío")
    print("Detalles de las primeras 5 noticias:")
    for i, news in enumerate(empty_news[:5]):
        print(
            f"  - ID: {news.get('id')}, Título: {news.get('title')[:50]}..., Símbolo: {news.get('symbol')}"
        )

    # Procesar cada noticia
    processed_count = 0
    for i, news in enumerate(empty_news):
        news_id = news.get("id")
        title = news.get("title", "")
        symbol = news.get("symbol", "SPY")
        url = news.get("url", "")

        print(
            f"\nProcesando noticia {i+1}/{len(empty_news)} - ID {news_id}: {title[:50]}..."
        )

        # Traducir título si está en inglés
        original_title = title
        print(f"Traduciendo título: {original_title[:50]}...")
        translated_title = translate_title_to_spanish(title)
        if translated_title != original_title:
            print(f"Título traducido: {translated_title[:50]}...")

            # Actualizar título en la base de datos
            if update_news_title(connection, news_id, translated_title):
                print(f"Título actualizado para noticia ID {news_id}")

                # Usar el título traducido para generar el resumen
                title = translated_title
            else:
                print(f"Error actualizando título para noticia ID {news_id}")

        # Intentar obtener noticias de Yahoo Finance si no hay URL
        if not url:
            print(
                f"No hay URL para la noticia ID {news_id}. Intentando obtener de Yahoo Finance..."
            )
            yahoo_news = get_news_from_yahoo(symbol, 1)
            if yahoo_news:
                # Usar la primera noticia como referencia
                url = yahoo_news[0].get("url", "")
                print(f"URL obtenida de Yahoo Finance: {url}")

                # Actualizar URL en la base de datos
                if update_news_url(connection, news_id, url):
                    print(f"URL actualizada para noticia ID {news_id}")
                else:
                    print(f"Error actualizando URL para noticia ID {news_id}")
            else:
                print(
                    f"No se encontraron noticias en Yahoo Finance para el símbolo {symbol}"
                )

        # Generar resumen con IA
        print(f"Generando resumen con IA para noticia ID {news_id}...")
        try:
            summary = generate_summary_with_ai(title, symbol, url)
            if summary:
                print(f"Resumen generado: {summary[:100]}...")
            else:
                print("No se pudo generar un resumen válido (resultado None)")
        except Exception as e:
            print(f"Error generando resumen con IA: {str(e)}")
            summary = None

        # Actualizar resumen en la base de datos solo si se generó un resumen válido
        if summary is not None:
            print(
                f"Actualizando resumen en la base de datos para noticia ID {news_id}..."
            )
            if update_news_summary(connection, news_id, summary):
                print(f"Resumen actualizado correctamente para noticia ID {news_id}")
                processed_count += 1
            else:
                print(f"Error actualizando resumen para noticia ID {news_id}")
        else:
            print(f"No se pudo generar un resumen válido para la noticia ID {news_id}")

        # Esperar un poco para no sobrecargar la API
        print("Esperando 1 segundo antes de procesar la siguiente noticia...")
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
        # Configurar nivel de logging para ver más información
        logging.getLogger().setLevel(logging.DEBUG)
        print("\n" + "=" * 80)
        print("INICIANDO PROCESAMIENTO DE CALIDAD DE DATOS")
        print("=" * 80)

        # Cargar configuración
        print("Cargando configuración de base de datos...")
        db_config = load_db_config()
        print(
            f"Configuración cargada: {db_config['host']}:{db_config['port']} - {db_config['database']}"
        )

        # Conectar a la base de datos
        print("Conectando a la base de datos...")
        connection = connect_to_db(db_config)
        if not connection:
            logger.error("No se pudo conectar a la base de datos")
            return
        print("Conexión establecida correctamente")

        # Verificar noticias con resumen vacío
        print("\nVerificando noticias con resumen vacío...")
        empty_news = get_empty_news_summaries(connection, 1000)
        print(f"Se encontraron {len(empty_news)} noticias con resumen vacío")

        # Procesar noticias con resumen vacío (sin límite)
        if empty_news:
            print("Procesando noticias con resumen vacío...")
            news_processed = process_empty_news_summaries(connection, 1000)
            print(f"Se procesaron {news_processed} noticias con resumen vacío")
        else:
            news_processed = 0
            print("No hay noticias con resumen vacío para procesar")

        # Verificar registros de sentimiento con análisis vacío
        print("\nVerificando registros de sentimiento con análisis vacío...")
        empty_sentiment = get_empty_sentiment_analysis(connection, 1000)
        print(
            f"Se encontraron {len(empty_sentiment)} registros de sentimiento con análisis vacío"
        )

        # Procesar registros de sentimiento con análisis vacío (sin límite)
        if empty_sentiment:
            print("Procesando registros de sentimiento con análisis vacío...")
            sentiment_processed = process_empty_sentiment_analysis(connection, 1000)
            print(
                f"Se procesaron {sentiment_processed} registros de sentimiento con análisis vacío"
            )
        else:
            sentiment_processed = 0
            print("No hay registros de sentimiento con análisis vacío para procesar")

        # Cerrar conexión
        connection.close()
        print("Conexión cerrada")

        # Mostrar resumen
        print("\n" + "=" * 80)
        print("RESUMEN DE PROCESAMIENTO")
        print("=" * 80)
        print(f"Noticias procesadas: {news_processed}")
        print(f"Registros de sentimiento procesados: {sentiment_processed}")
        print("=" * 80)
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
