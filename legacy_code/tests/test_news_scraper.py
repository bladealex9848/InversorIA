#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el scraper de noticias financieras
"""

import logging
import argparse
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_yahoo_finance_scraper(symbol: str, max_news: int = 5) -> None:
    """
    Prueba el scraper de Yahoo Finance
    
    Args:
        symbol (str): Símbolo del activo
        max_news (int): Número máximo de noticias a obtener
    """
    try:
        from yahoo_finance_scraper import YahooFinanceScraper
        
        logger.info(f"Probando YahooFinanceScraper para {symbol}...")
        
        # Crear instancia del scraper
        scraper = YahooFinanceScraper()
        
        # Obtener datos básicos
        logger.info("Obteniendo datos básicos...")
        quote_data = scraper.get_quote_data(symbol)
        
        # Mostrar información básica
        if "price" in quote_data and quote_data["price"].get("current"):
            logger.info(f"Precio actual: ${quote_data['price'].get('current')}")
            if quote_data["price"].get("change") and quote_data["price"].get("change_percent"):
                logger.info(f"Cambio: {quote_data['price'].get('change')} ({quote_data['price'].get('change_percent')}%)")
        else:
            logger.warning("No se pudieron obtener datos básicos")
        
        # Obtener nombre de la empresa
        company_name = scraper._get_company_name(symbol)
        logger.info(f"Nombre de la empresa: {company_name}")
        
        # Probar todas las fuentes de noticias
        logger.info("\n=== PRUEBA DE TODAS LAS FUENTES DE NOTICIAS ===")
        
        # 1. Probar yfinance
        logger.info("\n1. Obteniendo noticias con yfinance:")
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            news_data = ticker.news
            
            if news_data:
                logger.info(f"Se obtuvieron {len(news_data)} noticias con yfinance")
                for i, item in enumerate(news_data[:3], 1):
                    logger.info(f"{i}. {item.get('title', '')}")
                    logger.info(f"   Fuente: {item.get('publisher', 'N/A')}")
                    logger.info(f"   URL: {item.get('link', 'N/A')}")
            else:
                logger.warning("No se encontraron noticias con yfinance")
        except Exception as e:
            logger.error(f"Error obteniendo noticias con yfinance: {str(e)}")
        
        # 2. Probar scraping de Yahoo Finance
        logger.info("\n2. Obteniendo noticias con scraping de Yahoo Finance:")
        try:
            news_data = scraper.get_news(symbol, max_news=max_news)
            
            if news_data:
                logger.info(f"Se obtuvieron {len(news_data)} noticias con scraping de Yahoo Finance")
                for i, news in enumerate(news_data, 1):
                    logger.info(f"{i}. {news.get('title', 'Sin título')}")
                    logger.info(f"   Fuente: {news.get('source', 'N/A')} - Fecha: {news.get('date', 'N/A')}")
                    logger.info(f"   URL: {news.get('url', 'N/A')}")
                    logger.info(f"   Método: {news.get('_source_method', 'Desconocido')}")
            else:
                logger.warning("No se encontraron noticias con scraping de Yahoo Finance")
        except Exception as e:
            logger.error(f"Error obteniendo noticias con scraping de Yahoo Finance: {str(e)}")
        
        # 3. Probar DuckDuckGo
        logger.info("\n3. Obteniendo noticias con DuckDuckGo:")
        try:
            if hasattr(scraper, 'ddgs') and scraper.ddgs:
                query = f"{company_name} {symbol} stock news"
                results = scraper.ddgs.news(query, max_results=max_news)
                
                if results:
                    logger.info(f"Se obtuvieron {len(results)} noticias con DuckDuckGo")
                    for i, item in enumerate(results, 1):
                        logger.info(f"{i}. {item.get('title', '')}")
                        logger.info(f"   Fuente: {item.get('source', 'N/A')} - Fecha: {item.get('date', 'N/A')}")
                        logger.info(f"   URL: {item.get('url', 'N/A')}")
                else:
                    logger.warning("No se encontraron noticias con DuckDuckGo")
            else:
                logger.warning("DuckDuckGo no está disponible")
        except Exception as e:
            logger.error(f"Error obteniendo noticias con DuckDuckGo: {str(e)}")
        
        # 4. Probar Google Finance
        logger.info("\n4. Obteniendo noticias con Google Finance:")
        try:
            google_news = scraper._get_news_from_google_finance(symbol, max_news)
            
            if google_news:
                logger.info(f"Se obtuvieron {len(google_news)} noticias con Google Finance")
                for i, news in enumerate(google_news, 1):
                    logger.info(f"{i}. {news.get('title', 'Sin título')}")
                    logger.info(f"   Fuente: {news.get('source', 'N/A')} - Fecha: {news.get('date', 'N/A')}")
                    logger.info(f"   URL: {news.get('url', 'N/A')}")
            else:
                logger.warning("No se encontraron noticias con Google Finance")
        except Exception as e:
            logger.error(f"Error obteniendo noticias con Google Finance: {str(e)}")
        
        # 5. Probar MarketWatch
        logger.info("\n5. Obteniendo noticias con MarketWatch:")
        try:
            mw_news = scraper._get_news_from_marketwatch(symbol, max_news)
            
            if mw_news:
                logger.info(f"Se obtuvieron {len(mw_news)} noticias con MarketWatch")
                for i, news in enumerate(mw_news, 1):
                    logger.info(f"{i}. {news.get('title', 'Sin título')}")
                    logger.info(f"   Fuente: {news.get('source', 'N/A')} - Fecha: {news.get('date', 'N/A')}")
                    logger.info(f"   URL: {news.get('url', 'N/A')}")
            else:
                logger.warning("No se encontraron noticias con MarketWatch")
        except Exception as e:
            logger.error(f"Error obteniendo noticias con MarketWatch: {str(e)}")
        
        # 6. Probar procesamiento de noticias
        logger.info("\n6. Probando procesamiento de noticias:")
        try:
            # Obtener noticias
            news_data = scraper.get_news(symbol, max_news=max_news)
            
            if news_data:
                # Procesar noticias
                processed_news = scraper.process_news_with_expert(news_data, symbol, company_name)
                
                logger.info(f"Se procesaron {len(processed_news)} noticias")
                for i, news in enumerate(processed_news, 1):
                    logger.info(f"{i}. {news.get('title', 'Sin título')}")
                    logger.info(f"   Fuente: {news.get('source', 'N/A')} - Fecha: {news.get('date', 'N/A')}")
                    logger.info(f"   URL: {news.get('url', 'N/A')}")
                    logger.info(f"   Método: {news.get('_source_method', 'Desconocido')}")
            else:
                logger.warning("No hay noticias para procesar")
        except Exception as e:
            logger.error(f"Error procesando noticias: {str(e)}")
        
        logger.info("\n=== FIN DE LA PRUEBA DE FUENTES DE NOTICIAS ===")
        
    except ImportError:
        logger.error("No se pudo importar YahooFinanceScraper")
    except Exception as e:
        logger.error(f"Error en test_yahoo_finance_scraper: {str(e)}")

def test_news_processor(symbol: str, company_name: str = None, max_news: int = 5) -> None:
    """
    Prueba el procesador de noticias
    
    Args:
        symbol (str): Símbolo del activo
        company_name (str, optional): Nombre de la empresa
        max_news (int): Número máximo de noticias a obtener
    """
    try:
        from news_processor import NewsProcessor
        
        logger.info(f"Probando NewsProcessor para {symbol}...")
        
        # Crear un experto en IA simulado para pruebas
        class MockAIExpert:
            def process_text(self, prompt, max_tokens=100):
                logger.info(f"Procesando: {prompt[:50]}...")
                return f"Texto procesado para: {prompt[:30]}..."
        
        # Crear procesador de noticias
        processor = NewsProcessor(ai_expert=MockAIExpert())
        
        # Obtener noticias
        start_time = time.time()
        news = processor.get_news_for_symbol(symbol, company_name, max_news)
        elapsed_time = time.time() - start_time
        
        # Mostrar resultados
        logger.info(f"Se obtuvieron {len(news)} noticias en {elapsed_time:.2f} segundos")
        
        for i, item in enumerate(news, 1):
            logger.info(f"{i}. {item.get('title', 'Sin título')}")
            if item.get("spanish_title"):
                logger.info(f"   Título (ES): {item['spanish_title']}")
            logger.info(f"   Fuente: {item.get('source', 'N/A')} - Fecha: {item.get('date', 'N/A')}")
            logger.info(f"   URL: {item.get('url', 'N/A')}")
            if item.get("summary"):
                summary = item.get("summary", "")
                logger.info(f"   Resumen: {summary[:100]}..." if len(summary) > 100 else f"   Resumen: {summary}")
            if item.get("impact_analysis"):
                logger.info(f"   Análisis de impacto: {item['impact_analysis']}")
            logger.info(f"   Método de obtención: {item.get('_source_method', 'Desconocido')}")
            logger.info("")
        
    except ImportError:
        logger.error("No se pudo importar NewsProcessor")
    except Exception as e:
        logger.error(f"Error en test_news_processor: {str(e)}")

def save_news_to_file(news: List[Dict[str, Any]], symbol: str) -> None:
    """
    Guarda las noticias en un archivo JSON
    
    Args:
        news (List[Dict[str, Any]]): Lista de noticias
        symbol (str): Símbolo del activo
    """
    if not news:
        logger.warning("No hay noticias para guardar")
        return
    
    try:
        # Crear nombre de archivo
        filename = f"news_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Guardar en archivo
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(news, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Noticias guardadas en {filename}")
    except Exception as e:
        logger.error(f"Error guardando noticias en archivo: {str(e)}")

if __name__ == "__main__":
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Prueba de scraper de noticias financieras")
    parser.add_argument("--symbol", type=str, default="AAPL", help="Símbolo del activo")
    parser.add_argument("--company", type=str, help="Nombre de la empresa")
    parser.add_argument("--max-news", type=int, default=5, help="Número máximo de noticias")
    parser.add_argument("--save", action="store_true", help="Guardar noticias en archivo")
    parser.add_argument("--test-scraper", action="store_true", help="Probar scraper de Yahoo Finance")
    parser.add_argument("--test-processor", action="store_true", help="Probar procesador de noticias")
    
    args = parser.parse_args()
    
    # Si no se especifica ninguna prueba, ejecutar ambas
    if not args.test_scraper and not args.test_processor:
        args.test_scraper = True
        args.test_processor = True
    
    # Probar scraper de Yahoo Finance
    if args.test_scraper:
        test_yahoo_finance_scraper(args.symbol, args.max_news)
    
    # Probar procesador de noticias
    if args.test_processor:
        test_news_processor(args.symbol, args.company, args.max_news)
    
    # Obtener y guardar noticias si se solicita
    if args.save:
        try:
            from news_processor import NewsProcessor
            
            # Crear un experto en IA simulado para pruebas
            class MockAIExpert:
                def process_text(self, prompt, max_tokens=100):
                    return f"Texto procesado para: {prompt[:30]}..."
            
            # Crear procesador de noticias
            processor = NewsProcessor(ai_expert=MockAIExpert())
            
            # Obtener noticias
            news = processor.get_news_for_symbol(args.symbol, args.company, args.max_news)
            
            # Guardar noticias
            save_news_to_file(news, args.symbol)
        except ImportError:
            logger.error("No se pudo importar NewsProcessor")
        except Exception as e:
            logger.error(f"Error obteniendo y guardando noticias: {str(e)}")
