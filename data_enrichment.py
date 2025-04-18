#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para enriquecer datos de mercado.
Incluye funciones para obtener noticias, URLs y otros datos complementarios.
"""

import logging
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Intentar importar el scraper de Yahoo Finance
YAHOO_SCRAPER_AVAILABLE = False
try:
    from yahoo_finance_scraper import YahooFinanceScraper
    YAHOO_SCRAPER_AVAILABLE = True
    logger.info("YahooFinanceScraper disponible para uso en data_enrichment.py")
except ImportError:
    logger.warning("YahooFinanceScraper no está disponible en data_enrichment.py. Se usarán métodos alternativos.")

# Intentar importar yfinance
YFINANCE_AVAILABLE = False
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    logger.info("yfinance disponible para uso en data_enrichment.py")
except ImportError:
    logger.warning("yfinance no está disponible en data_enrichment.py. Se usarán métodos alternativos.")


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
        logger.warning("YahooFinanceScraper no está disponible. No se pueden obtener noticias de Yahoo Finance.")
        return []
    
    try:
        # Inicializar scraper
        scraper = YahooFinanceScraper()
        
        # Obtener noticias
        news = scraper.get_news(symbol, max_news)
        
        return news
    except Exception as e:
        logger.error(f"Error obteniendo noticias de Yahoo Finance para {symbol}: {str(e)}")
        return []


def get_news_from_yfinance(symbol: str, max_news: int = 5) -> List[Dict[str, Any]]:
    """
    Obtiene noticias utilizando la biblioteca yfinance
    
    Args:
        symbol (str): Símbolo del activo
        max_news (int): Número máximo de noticias a obtener
        
    Returns:
        List[Dict[str, Any]]: Lista de noticias
    """
    if not YFINANCE_AVAILABLE:
        logger.warning("yfinance no está disponible. No se pueden obtener noticias.")
        return []
    
    try:
        # Obtener ticker
        ticker = yf.Ticker(symbol)
        
        # Obtener noticias
        news_data = ticker.news
        
        # Limitar número de noticias
        news_data = news_data[:max_news] if news_data else []
        
        # Formatear noticias
        formatted_news = []
        for news in news_data:
            formatted_news.append({
                "title": news.get("title", ""),
                "summary": news.get("summary", ""),
                "url": news.get("link", ""),
                "source": news.get("publisher", "Yahoo Finance"),
                "date": news.get("providerPublishTime", "")
            })
        
        return formatted_news
    except Exception as e:
        logger.error(f"Error obteniendo noticias con yfinance para {symbol}: {str(e)}")
        return []


def get_company_info(symbol: str) -> Dict[str, Any]:
    """
    Obtiene información de la empresa
    
    Args:
        symbol (str): Símbolo del activo
        
    Returns:
        Dict[str, Any]: Información de la empresa
    """
    if not YFINANCE_AVAILABLE:
        logger.warning("yfinance no está disponible. No se puede obtener información de la empresa.")
        return {}
    
    try:
        # Obtener ticker
        ticker = yf.Ticker(symbol)
        
        # Obtener información
        info = ticker.info
        
        # Extraer datos relevantes
        company_info = {
            "name": info.get("shortName", symbol),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "website": info.get("website", ""),
            "description": info.get("longBusinessSummary", ""),
            "country": info.get("country", ""),
            "employees": info.get("fullTimeEmployees", 0),
            "market_cap": info.get("marketCap", 0)
        }
        
        return company_info
    except Exception as e:
        logger.error(f"Error obteniendo información de la empresa para {symbol}: {str(e)}")
        return {}


def generate_fallback_url(symbol: str, source: str = "") -> str:
    """
    Genera una URL de respaldo basada en la fuente y el símbolo
    
    Args:
        symbol (str): Símbolo del activo
        source (str): Fuente de la noticia
        
    Returns:
        str: URL de respaldo
    """
    source_lower = source.lower() if source else ""
    
    if "yahoo" in source_lower:
        return f"https://finance.yahoo.com/quote/{symbol}"
    elif "bloomberg" in source_lower:
        return f"https://www.bloomberg.com/quote/{symbol}"
    elif "cnbc" in source_lower:
        return f"https://www.cnbc.com/quotes/{symbol}"
    elif "reuters" in source_lower:
        return f"https://www.reuters.com/companies/{symbol}"
    elif "marketwatch" in source_lower:
        return f"https://www.marketwatch.com/investing/stock/{symbol}"
    elif "investing.com" in source_lower:
        return f"https://www.investing.com/search/?q={symbol}"
    else:
        return f"https://www.google.com/finance/quote/{symbol}"


def get_technical_indicators(symbol: str) -> Dict[str, Any]:
    """
    Obtiene indicadores técnicos para un símbolo
    
    Args:
        symbol (str): Símbolo del activo
        
    Returns:
        Dict[str, Any]: Indicadores técnicos
    """
    if not YFINANCE_AVAILABLE:
        logger.warning("yfinance no está disponible. No se pueden obtener indicadores técnicos.")
        return {}
    
    try:
        # Obtener ticker
        ticker = yf.Ticker(symbol)
        
        # Obtener historial de precios
        hist = ticker.history(period="6mo")
        
        if hist.empty:
            logger.warning(f"No hay datos históricos disponibles para {symbol}")
            return {}
        
        # Calcular medias móviles
        hist['MA50'] = hist['Close'].rolling(window=50).mean()
        hist['MA200'] = hist['Close'].rolling(window=200).mean()
        
        # Obtener último precio
        last_price = hist['Close'].iloc[-1]
        
        # Calcular RSI (Relative Strength Index)
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # Obtener volumen promedio
        avg_volume = hist['Volume'].mean()
        
        # Determinar tendencia
        ma50_last = hist['MA50'].iloc[-1]
        ma200_last = hist['MA200'].iloc[-1]
        
        if ma50_last > ma200_last:
            trend = "Alcista"
        elif ma50_last < ma200_last:
            trend = "Bajista"
        else:
            trend = "Neutral"
        
        # Crear diccionario de indicadores
        indicators = {
            "current_price": round(last_price, 2),
            "ma_50": round(ma50_last, 2) if not pd.isna(ma50_last) else None,
            "ma_200": round(ma200_last, 2) if not pd.isna(ma200_last) else None,
            "rsi": round(rsi, 2) if not pd.isna(rsi) else None,
            "volume": int(avg_volume) if not pd.isna(avg_volume) else None,
            "trend": trend
        }
        
        return indicators
    except Exception as e:
        logger.error(f"Error obteniendo indicadores técnicos para {symbol}: {str(e)}")
        return {}


if __name__ == "__main__":
    # Pruebas básicas
    test_symbol = "AAPL"
    
    print(f"Pruebas para el símbolo: {test_symbol}")
    
    if YAHOO_SCRAPER_AVAILABLE:
        print("\nPrueba de obtención de noticias con Yahoo Finance Scraper:")
        news = get_news_from_yahoo(test_symbol, 2)
        for i, item in enumerate(news, 1):
            print(f"{i}. {item.get('title', 'Sin título')}")
            print(f"   URL: {item.get('url', 'Sin URL')}")
    
    if YFINANCE_AVAILABLE:
        print("\nPrueba de obtención de noticias con yfinance:")
        news = get_news_from_yfinance(test_symbol, 2)
        for i, item in enumerate(news, 1):
            print(f"{i}. {item.get('title', 'Sin título')}")
            print(f"   URL: {item.get('url', 'Sin URL')}")
        
        print("\nPrueba de obtención de información de la empresa:")
        info = get_company_info(test_symbol)
        print(f"Nombre: {info.get('name', 'N/A')}")
        print(f"Sector: {info.get('sector', 'N/A')}")
        print(f"Industria: {info.get('industry', 'N/A')}")
        print(f"Descripción: {info.get('description', 'N/A')[:100]}...")
        
        print("\nPrueba de obtención de indicadores técnicos:")
        indicators = get_technical_indicators(test_symbol)
        print(f"Precio actual: {indicators.get('current_price', 'N/A')}")
        print(f"MA50: {indicators.get('ma_50', 'N/A')}")
        print(f"MA200: {indicators.get('ma_200', 'N/A')}")
        print(f"RSI: {indicators.get('rsi', 'N/A')}")
        print(f"Tendencia: {indicators.get('trend', 'N/A')}")
    
    print("\nPrueba de generación de URL de respaldo:")
    sources = ["Yahoo Finance", "Bloomberg", "CNBC", "Reuters", "MarketWatch", "Investing.com", "Unknown"]
    for source in sources:
        url = generate_fallback_url(test_symbol, source)
        print(f"Fuente: {source} -> URL: {url}")
