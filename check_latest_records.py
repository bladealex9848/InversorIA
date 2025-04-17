"""
Script para consultar los últimos registros de las tablas de la base de datos
"""

import logging
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_latest_trading_signals(db_manager, limit=10):
    """Obtiene los últimos registros de la tabla trading_signals"""
    query = """
    SELECT id, symbol, price, direction, trend, recommendation, sentiment,
           sentiment_score, created_at, signal_date
    FROM trading_signals
    ORDER BY created_at DESC
    LIMIT %s
    """

    results = db_manager.execute_query(query, params=(limit,))
    if results:
        print(f"\n===== ÚLTIMOS {len(results)} REGISTROS DE TRADING_SIGNALS =====")
        for i, record in enumerate(results, 1):
            print(f"\n----- Registro {i} -----")
            print(f"ID: {record['id']}")
            print(f"Símbolo: {record['symbol']}")
            print(f"Precio: {record['price']}")
            print(f"Dirección: {record['direction']}")
            print(f"Tendencia: {record['trend']}")
            print(f"Recomendación: {record['recommendation']}")
            print(
                f"Sentimiento: {record['sentiment']} (Score: {record['sentiment_score']})"
            )
            print(f"Fecha de creación: {record['created_at']}")
            print(f"Fecha de señal: {record['signal_date']}")
    else:
        print("\nNo se encontraron registros en la tabla trading_signals")

    return results


def get_latest_market_news(db_manager, limit=10):
    """Obtiene los últimos registros de la tabla market_news"""
    query = """
    SELECT id, title, summary, source, url, news_date, impact, created_at
    FROM market_news
    ORDER BY created_at DESC
    LIMIT %s
    """

    results = db_manager.execute_query(query, params=(limit,))
    if results:
        print(f"\n===== ÚLTIMOS {len(results)} REGISTROS DE MARKET_NEWS =====")
        for i, record in enumerate(results, 1):
            print(f"\n----- Registro {i} -----")
            print(f"ID: {record['id']}")
            print(f"Título: {record['title']}")
            print(
                f"Resumen: {record['summary'][:100]}..."
                if len(record["summary"]) > 100
                else f"Resumen: {record['summary']}"
            )
            print(f"Fuente: {record['source']}")
            print(f"URL: {record['url']}")
            print(f"Fecha de noticia: {record['news_date']}")
            print(f"Impacto: {record['impact']}")
            print(f"Fecha de creación: {record['created_at']}")
    else:
        print("\nNo se encontraron registros en la tabla market_news")

    return results


def get_latest_market_sentiment(db_manager, limit=10):
    """Obtiene los últimos registros de la tabla market_sentiment"""
    query = """
    SELECT id, symbol, sentiment, score, source, analysis, sentiment_date,
           overall, vix, sp500_trend, technical_indicators, volume, notes, created_at
    FROM market_sentiment
    ORDER BY created_at DESC
    LIMIT %s
    """

    results = db_manager.execute_query(query, params=(limit,))
    if results:
        print(f"\n===== ÚLTIMOS {len(results)} REGISTROS DE MARKET_SENTIMENT =====")
        for i, record in enumerate(results, 1):
            print(f"\n----- Registro {i} -----")
            print(f"ID: {record['id']}")
            print(f"Símbolo: {record['symbol']}")
            print(f"Sentimiento: {record['sentiment']} (Score: {record['score']})")
            print(f"Fuente: {record['source']}")
            print(
                f"Análisis: {record['analysis'][:100]}..."
                if record["analysis"] and len(record["analysis"]) > 100
                else f"Análisis: {record['analysis']}"
            )
            print(f"Fecha de sentimiento: {record['sentiment_date']}")
            print(f"Overall: {record['overall']}")
            print(f"VIX: {record['vix']}")
            print(f"Tendencia SP500: {record['sp500_trend']}")
            print(
                f"Indicadores técnicos: {record['technical_indicators'][:100]}..."
                if record["technical_indicators"]
                and len(record["technical_indicators"]) > 100
                else f"Indicadores técnicos: {record['technical_indicators']}"
            )
            print(f"Volumen: {record['volume']}")
            print(
                f"Notas: {record['notes'][:100]}..."
                if record["notes"] and len(record["notes"]) > 100
                else f"Notas: {record['notes']}"
            )
            print(f"Fecha de creación: {record['created_at']}")
    else:
        print("\nNo se encontraron registros en la tabla market_sentiment")

    return results


def get_latest_email_logs(db_manager, limit=10):
    """Obtiene los últimos registros de la tabla email_logs"""
    query = """
    SELECT id, recipient_email, subject, content_summary, signals_included,
           status, error_message, sent_at, created_at
    FROM email_logs
    ORDER BY created_at DESC
    LIMIT %s
    """

    results = db_manager.execute_query(query, params=(limit,))
    if results:
        print(f"\n===== ÚLTIMOS {len(results)} REGISTROS DE EMAIL_LOGS =====")
        for i, record in enumerate(results, 1):
            print(f"\n----- Registro {i} -----")
            print(f"ID: {record['id']}")
            print(f"Email destinatario: {record['recipient_email']}")
            print(f"Asunto: {record['subject']}")
            print(f"Resumen de contenido: {record['content_summary']}")
            print(f"Señales incluidas: {record['signals_included']}")
            print(f"Estado: {record['status']}")
            print(f"Mensaje de error: {record['error_message']}")
            print(f"Fecha de envío: {record['sent_at']}")
            print(f"Fecha de creación: {record['created_at']}")
    else:
        print("\nNo se encontraron registros en la tabla email_logs")

    return results


def check_duplicate_sentiment(db_manager):
    """Verifica si hay registros duplicados de sentimiento para el mismo símbolo en el mismo día"""
    query = """
    SELECT symbol, DATE(sentiment_date) as date, COUNT(*) as count
    FROM market_sentiment
    GROUP BY symbol, DATE(sentiment_date)
    HAVING COUNT(*) > 1
    ORDER BY date DESC, count DESC
    """

    results = db_manager.execute_query(query)
    if results:
        print(f"\n===== REGISTROS DUPLICADOS DE SENTIMIENTO =====")
        for i, record in enumerate(results, 1):
            print(
                f"{i}. Símbolo: {record['symbol']}, Fecha: {record['date']}, Cantidad: {record['count']}"
            )
    else:
        print("\nNo se encontraron registros duplicados de sentimiento")

    return results


def check_sentiment_update_error(db_manager):
    """Verifica si hay errores en la actualización de sentimiento"""
    query = """
    SHOW COLUMNS FROM market_sentiment
    """

    results = db_manager.execute_query(query)
    columns = [col["Field"] for col in results]

    print(f"\n===== ESTRUCTURA DE LA TABLA MARKET_SENTIMENT =====")
    for col in results:
        print(
            f"Campo: {col['Field']}, Tipo: {col['Type']}, Nulo: {col['Null']}, Clave: {col['Key']}, Default: {col['Default']}"
        )

    if "updated_at" not in columns:
        print("\n⚠️ La columna 'updated_at' no existe en la tabla market_sentiment")
        print("Esto explica el error: 'Unknown column 'updated_at' in 'field list'")

    return columns


def analyze_data_quality(trading_signals, market_news, market_sentiment):
    """Analiza la calidad de los datos almacenados"""
    print("\n===== ANÁLISIS DE CALIDAD DE DATOS =====")

    # Análisis de trading_signals
    if trading_signals:
        empty_recommendations = sum(
            1
            for record in trading_signals
            if not record["recommendation"] or record["recommendation"] == ""
        )
        short_recommendations = sum(
            1
            for record in trading_signals
            if record["recommendation"] and len(record["recommendation"]) < 20
        )

        print("\n----- TRADING_SIGNALS -----")
        print(f"Total de registros analizados: {len(trading_signals)}")
        print(
            f"Recomendaciones vacías: {empty_recommendations} ({empty_recommendations/len(trading_signals)*100:.1f}%)"
        )
        print(
            f"Recomendaciones cortas (<20 caracteres): {short_recommendations} ({short_recommendations/len(trading_signals)*100:.1f}%)"
        )

    # Análisis de market_news
    if market_news:
        empty_urls = sum(
            1 for record in market_news if not record["url"] or record["url"] == ""
        )
        empty_summaries = sum(
            1
            for record in market_news
            if not record["summary"] or record["summary"] == ""
        )
        short_summaries = sum(
            1
            for record in market_news
            if record["summary"] and len(record["summary"]) < 50
        )

        print("\n----- MARKET_NEWS -----")
        print(f"Total de registros analizados: {len(market_news)}")
        print(f"URLs vacías: {empty_urls} ({empty_urls/len(market_news)*100:.1f}%)")
        print(
            f"Resúmenes vacíos: {empty_summaries} ({empty_summaries/len(market_news)*100:.1f}%)"
        )
        print(
            f"Resúmenes cortos (<50 caracteres): {short_summaries} ({short_summaries/len(market_news)*100:.1f}%)"
        )

    # Análisis de market_sentiment
    if market_sentiment:
        empty_analysis = sum(
            1
            for record in market_sentiment
            if not record["analysis"] or record["analysis"] == ""
        )
        short_analysis = sum(
            1
            for record in market_sentiment
            if record["analysis"] and len(record["analysis"]) < 50
        )

        print("\n----- MARKET_SENTIMENT -----")
        print(f"Total de registros analizados: {len(market_sentiment)}")
        print(
            f"Análisis vacíos: {empty_analysis} ({empty_analysis/len(market_sentiment)*100:.1f}%)"
        )
        print(
            f"Análisis cortos (<50 caracteres): {short_analysis} ({short_analysis/len(market_sentiment)*100:.1f}%)"
        )


def main():
    """Función principal"""
    print("\n===== CONSULTA DE ÚLTIMOS REGISTROS DE LA BASE DE DATOS =====\n")

    # Crear instancia del gestor de base de datos
    db_manager = DatabaseManager()

    # Obtener los últimos registros de las tablas
    trading_signals = get_latest_trading_signals(db_manager, limit=5)
    market_news = get_latest_market_news(db_manager, limit=5)
    market_sentiment = get_latest_market_sentiment(db_manager, limit=5)
    email_logs = get_latest_email_logs(db_manager, limit=5)

    # Verificar si hay registros duplicados de sentimiento
    duplicate_sentiment = check_duplicate_sentiment(db_manager)

    # Verificar si hay errores en la actualización de sentimiento
    columns = check_sentiment_update_error(db_manager)

    # Analizar la calidad de los datos almacenados
    analyze_data_quality(trading_signals, market_news, market_sentiment)

    print("\n===== CONSULTA COMPLETADA =====")


if __name__ == "__main__":
    main()
