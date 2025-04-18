#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar y procesar la calidad de los datos después de la grabación de señales, noticias y sentimiento.
Este script debe ser llamado después de cada proceso de grabación para asegurar que no queden campos vacíos.
"""

import sys
import logging
import argparse
import time
from datetime import datetime
from typing import Dict
import mysql.connector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

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
    get_empty_trading_signals_analysis,
    update_trading_signal_analysis,
)
from text_processing import translate_title_to_spanish
from data_enrichment import get_news_from_yahoo
from ai_content_generator import (
    generate_summary_with_ai,
    generate_sentiment_analysis_with_ai,
    generate_trading_signal_analysis_with_ai,
)


def check_database_quality(
    connection: mysql.connector.MySQLConnection,
) -> Dict[str, int]:
    """
    Verifica la calidad de los datos en la base de datos

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos

    Returns:
        Dict[str, int]: Diccionario con el número de registros con campos vacíos por tabla
    """
    result = {}

    # Verificar noticias con resumen vacío
    empty_news = get_empty_news_summaries(connection, limit=1000)
    result["empty_news_summaries"] = len(empty_news) if empty_news else 0

    # Verificar sentimiento con análisis vacío
    empty_sentiment = get_empty_sentiment_analysis(connection, limit=1000)
    result["empty_sentiment_analysis"] = len(empty_sentiment) if empty_sentiment else 0

    # Verificar señales de trading con análisis experto vacío
    empty_signals = get_empty_trading_signals_analysis(connection, limit=1000)
    result["empty_trading_signals_analysis"] = (
        len(empty_signals) if empty_signals else 0
    )

    return result


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


def process_empty_sentiment_analysis(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> int:
    """
    Procesa registros de sentimiento con campos críticos vacíos

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a procesar

    Returns:
        int: Número de registros procesados
    """
    # Obtener registros de sentimiento con campos críticos vacíos
    empty_sentiment = get_empty_sentiment_analysis(connection, limit)

    if not empty_sentiment:
        logger.info(
            "No hay registros de sentimiento con campos críticos vacíos para procesar"
        )
        return 0

    logger.info(
        f"Se encontraron {len(empty_sentiment)} registros de sentimiento con campos críticos vacíos"
    )

    # Procesar cada registro
    processed_count = 0
    for sentiment in empty_sentiment:
        sentiment_id = sentiment.get("id")

        logger.info(f"Procesando sentimiento ID {sentiment_id}...")

        # Verificar qué campos están vacíos
        fields_to_update = {}

        # Verificar si el análisis está vacío
        if not sentiment.get("analysis"):
            # Generar análisis con IA
            analysis = generate_sentiment_analysis_with_ai(sentiment)
            if analysis is not None:
                fields_to_update["analysis"] = analysis

        # Verificar si el símbolo está vacío
        if not sentiment.get("symbol"):
            # Usar SPY como valor predeterminado o determinar el símbolo basado en otros campos
            fields_to_update["symbol"] = "SPY"

        # Verificar si el sentimiento está vacío
        if not sentiment.get("sentiment"):
            # Determinar el sentimiento basado en overall o usar un valor predeterminado
            overall = sentiment.get("overall")
            if overall == "Alcista":
                fields_to_update["sentiment"] = "Positivo"
            elif overall == "Bajista":
                fields_to_update["sentiment"] = "Negativo"
            else:
                fields_to_update["sentiment"] = "Neutral"

        # Verificar si el score está vacío
        if sentiment.get("score") is None:
            # Asignar un score basado en overall o usar un valor predeterminado
            overall = sentiment.get("overall")
            if overall == "Alcista":
                fields_to_update["score"] = 0.75
            elif overall == "Bajista":
                fields_to_update["score"] = 0.25
            else:
                fields_to_update["score"] = 0.5

        # Verificar si la fuente está vacía
        if not sentiment.get("source"):
            fields_to_update["source"] = "InversorIA AI"

        # Verificar si la fecha del sentimiento está vacía
        if not sentiment.get("sentiment_date"):
            # Usar la fecha actual
            fields_to_update["sentiment_date"] = sentiment.get(
                "date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        # Actualizar los campos en la base de datos
        if fields_to_update:
            if update_sentiment_analysis(
                connection,
                sentiment_id,
                analysis=fields_to_update.get("analysis"),
                symbol=fields_to_update.get("symbol"),
                sentiment_value=fields_to_update.get("sentiment"),
                score=fields_to_update.get("score"),
                source=fields_to_update.get("source"),
                sentiment_date=fields_to_update.get("sentiment_date"),
            ):
                logger.info(
                    f"Campos actualizados para sentimiento ID {sentiment_id}: {', '.join(fields_to_update.keys())}"
                )
                processed_count += 1
            else:
                logger.error(
                    f"Error actualizando campos para sentimiento ID {sentiment_id}"
                )
        else:
            logger.info(
                f"No hay campos para actualizar en el sentimiento ID {sentiment_id}"
            )

        # Esperar un poco para no sobrecargar la API
        time.sleep(1)

    return processed_count


def process_empty_trading_signals_analysis(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> int:
    """
    Procesa señales de trading con análisis experto vacío

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a procesar

    Returns:
        int: Número de registros procesados
    """
    # Obtener señales de trading con análisis experto vacío
    empty_signals = get_empty_trading_signals_analysis(connection, limit)

    if not empty_signals:
        logger.info(
            "No hay señales de trading con análisis experto vacío para procesar"
        )
        return 0

    logger.info(
        f"Se encontraron {len(empty_signals)} señales de trading con análisis experto vacío"
    )

    # Procesar cada señal
    processed_count = 0
    for signal in empty_signals:
        signal_id = signal.get("id")

        logger.info(f"Procesando señal ID {signal_id}...")

        # Generar análisis con IA
        analysis = generate_trading_signal_analysis_with_ai(signal)

        # Actualizar análisis en la base de datos solo si se generó un análisis válido
        if analysis is not None:
            if update_trading_signal_analysis(connection, signal_id, analysis):
                logger.info(f"Análisis experto actualizado para señal ID {signal_id}")
                processed_count += 1
            else:
                logger.error(
                    f"Error actualizando análisis experto para señal ID {signal_id}"
                )
        else:
            logger.warning(
                f"No se pudo generar un análisis válido para la señal ID {signal_id}"
            )

        # Esperar un poco para no sobrecargar la API
        time.sleep(1)

    return processed_count


def process_quality_after_save(
    table_name: str = "all", limit: int = 10
) -> Dict[str, int]:
    """
    Procesa la calidad de los datos después de guardar registros

    Args:
        table_name (str): Nombre de la tabla a procesar (news, sentiment, signals o all)
        limit (int): Número máximo de registros a procesar por tabla

    Returns:
        Dict[str, int]: Diccionario con el número de registros procesados por tabla
    """
    result = {"news_processed": 0, "sentiment_processed": 0, "signals_processed": 0}

    try:
        # Cargar configuración
        db_config = load_db_config()

        # Conectar a la base de datos
        connection = connect_to_db(db_config)
        if not connection:
            logger.error("No se pudo conectar a la base de datos")
            return result

        # Verificar la calidad de los datos
        quality_stats = check_database_quality(connection)

        # Mostrar estadísticas de calidad
        logger.info("=" * 80)
        logger.info("ESTADÍSTICAS DE CALIDAD DE DATOS")
        logger.info("=" * 80)
        logger.info(
            f"Noticias con resumen vacío: {quality_stats['empty_news_summaries']}"
        )
        logger.info(
            f"Registros de sentimiento con análisis vacío: {quality_stats['empty_sentiment_analysis']}"
        )
        logger.info(
            f"Señales de trading con análisis experto vacío: {quality_stats['empty_trading_signals_analysis']}"
        )
        logger.info("=" * 80)

        # Procesar los datos según la tabla seleccionada
        if table_name in ["news", "all"] and quality_stats["empty_news_summaries"] > 0:
            # Procesar noticias con resumen vacío
            result["news_processed"] = process_empty_news_summaries(connection, limit)
            logger.info(
                f"Se procesaron {result['news_processed']} noticias con resumen vacío"
            )

        if (
            table_name in ["sentiment", "all"]
            and quality_stats["empty_sentiment_analysis"] > 0
        ):
            # Procesar registros de sentimiento con análisis vacío
            result["sentiment_processed"] = process_empty_sentiment_analysis(
                connection, limit
            )
            logger.info(
                f"Se procesaron {result['sentiment_processed']} registros de sentimiento con análisis vacío"
            )

        if (
            table_name in ["signals", "all"]
            and quality_stats["empty_trading_signals_analysis"] > 0
        ):
            # Procesar señales de trading con análisis experto vacío
            result["signals_processed"] = process_empty_trading_signals_analysis(
                connection, limit
            )
            logger.info(
                f"Se procesaron {result['signals_processed']} señales de trading con análisis experto vacío"
            )

        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")

        # Mostrar resumen
        logger.info("=" * 80)
        logger.info("RESUMEN DE PROCESAMIENTO")
        logger.info("=" * 80)
        logger.info(f"Noticias procesadas: {result['news_processed']}")
        logger.info(
            f"Registros de sentimiento procesados: {result['sentiment_processed']}"
        )
        logger.info(f"Señales de trading procesadas: {result['signals_processed']}")
        logger.info("=" * 80)

        return result
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")
        return result


def main():
    """Función principal"""
    try:
        # Configurar argumentos de línea de comandos
        parser = argparse.ArgumentParser(description="Procesar calidad de datos")
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Número máximo de registros a procesar por tabla",
        )
        parser.add_argument(
            "--check-only",
            action="store_true",
            help="Solo verificar la calidad de los datos sin procesarlos",
        )
        parser.add_argument(
            "--table",
            type=str,
            choices=["news", "sentiment", "signals", "all"],
            default="all",
            help="Tabla a procesar (news, sentiment, signals o all)",
        )
        args = parser.parse_args()

        # Cargar configuración
        db_config = load_db_config()

        # Conectar a la base de datos
        connection = connect_to_db(db_config)
        if not connection:
            logger.error("No se pudo conectar a la base de datos")
            return

        # Verificar la calidad de los datos
        quality_stats = check_database_quality(connection)

        # Mostrar estadísticas de calidad
        print("\n" + "=" * 80)
        print("ESTADÍSTICAS DE CALIDAD DE DATOS")
        print("=" * 80)
        print(f"Noticias con resumen vacío: {quality_stats['empty_news_summaries']}")
        print(
            f"Registros de sentimiento con análisis vacío: {quality_stats['empty_sentiment_analysis']}"
        )
        print(
            f"Señales de trading con análisis experto vacío: {quality_stats['empty_trading_signals_analysis']}"
        )
        print("=" * 80)

        # Si solo se quiere verificar la calidad, terminar aquí
        if args.check_only:
            logger.info("Modo de solo verificación. No se procesarán los datos.")
            connection.close()
            return

        # Procesar los datos según la tabla seleccionada
        news_processed = 0
        sentiment_processed = 0
        signals_processed = 0

        if args.table in ["news", "all"]:
            # Procesar noticias con resumen vacío
            news_processed = process_empty_news_summaries(connection, args.limit)
            logger.info(f"Se procesaron {news_processed} noticias con resumen vacío")

        if args.table in ["sentiment", "all"]:
            # Procesar registros de sentimiento con análisis vacío
            sentiment_processed = process_empty_sentiment_analysis(
                connection, args.limit
            )
            logger.info(
                f"Se procesaron {sentiment_processed} registros de sentimiento con análisis vacío"
            )

        if args.table in ["signals", "all"]:
            # Procesar señales de trading con análisis experto vacío
            signals_processed = process_empty_trading_signals_analysis(
                connection, args.limit
            )
            logger.info(
                f"Se procesaron {signals_processed} señales de trading con análisis experto vacío"
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
        print(f"Señales de trading procesadas: {signals_processed}")
        print("=" * 80)
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")


if __name__ == "__main__":
    main()
