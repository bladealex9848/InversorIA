#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar campos específicos en las tablas de la base de datos
"""

import mysql.connector
import streamlit as st
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def get_db_config():
    """Obtiene la configuración de la base de datos desde secrets.toml"""
    return {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "liceopan_enki_sincelejo",
    }

def check_market_news(connection):
    """Verifica los campos en la tabla market_news"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Verificar si hay noticias en inglés o genéricas
        query = """
        SELECT id, title, summary, source, url, news_date, impact, symbol
        FROM market_news
        ORDER BY id DESC
        LIMIT 5
        """
        cursor.execute(query)
        records = cursor.fetchall()
        
        logger.info(f"Últimas 5 noticias en market_news:")
        for record in records:
            logger.info(f"  ID: {record['id']}")
            logger.info(f"  Título: {record['title']}")
            logger.info(f"  Resumen: {record['summary']}")
            logger.info(f"  Fuente: {record['source']}")
            logger.info(f"  URL: {record['url']}")
            logger.info(f"  Fecha: {record['news_date']}")
            logger.info(f"  Impacto: {record['impact']}")
            logger.info(f"  Símbolo: {record['symbol']}")
            logger.info("  " + "-"*50)
        
        cursor.close()
        return True
    
    except Exception as e:
        logger.error(f"Error verificando market_news: {str(e)}")
        return False

def check_trading_signals(connection):
    """Verifica los campos latest_news y news_source en la tabla trading_signals"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Verificar latest_news y news_source
        query = """
        SELECT id, symbol, signal_type, latest_news, news_source
        FROM trading_signals
        ORDER BY id DESC
        LIMIT 5
        """
        cursor.execute(query)
        records = cursor.fetchall()
        
        logger.info(f"Últimas 5 señales en trading_signals:")
        for record in records:
            logger.info(f"  ID: {record['id']}")
            logger.info(f"  Símbolo: {record['symbol']}")
            logger.info(f"  Tipo de señal: {record['signal_type']}")
            logger.info(f"  Últimas noticias: {record['latest_news']}")
            logger.info(f"  Fuente de noticias: {record['news_source']}")
            logger.info("  " + "-"*50)
        
        cursor.close()
        return True
    
    except Exception as e:
        logger.error(f"Error verificando trading_signals: {str(e)}")
        return False

def check_market_sentiment(connection):
    """Verifica los campos en la tabla market_sentiment"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Verificar campos de sentimiento
        query = """
        SELECT id, symbol, sentiment, score, source, analysis, sentiment_date
        FROM market_sentiment
        ORDER BY id DESC
        LIMIT 5
        """
        cursor.execute(query)
        records = cursor.fetchall()
        
        logger.info(f"Últimos 5 registros en market_sentiment:")
        for record in records:
            logger.info(f"  ID: {record['id']}")
            logger.info(f"  Símbolo: {record['symbol']}")
            logger.info(f"  Sentimiento: {record['sentiment']}")
            logger.info(f"  Puntuación: {record['score']}")
            logger.info(f"  Fuente: {record['source']}")
            logger.info(f"  Análisis: {record['analysis']}")
            logger.info(f"  Fecha: {record['sentiment_date']}")
            logger.info("  " + "-"*50)
        
        cursor.close()
        return True
    
    except Exception as e:
        logger.error(f"Error verificando market_sentiment: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("Iniciando verificación de campos específicos")
    
    # Obtener configuración de la base de datos
    config = get_db_config()
    
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**config)
        logger.info(f"Conexión establecida con la base de datos {config['database']}")
        
        # Verificar campos específicos
        logger.info(f"\n{'='*50}\nVerificando market_news\n{'='*50}")
        check_market_news(connection)
        
        logger.info(f"\n{'='*50}\nVerificando trading_signals\n{'='*50}")
        check_trading_signals(connection)
        
        logger.info(f"\n{'='*50}\nVerificando market_sentiment\n{'='*50}")
        check_market_sentiment(connection)
        
        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    
    logger.info("Verificación completada")

if __name__ == "__main__":
    main()
