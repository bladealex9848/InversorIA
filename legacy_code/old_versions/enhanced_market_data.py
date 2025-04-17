#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Market Data - Módulo mejorado para obtener datos de mercado de múltiples fuentes
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import json
import re
import time
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from duckduckgo_search import DDGS

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedMarketData:
    """Clase para obtener datos de mercado de múltiples fuentes con fallbacks"""
    
    def __init__(self):
        """Inicializa el recolector de datos de mercado"""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 3600  # 1 hora en segundos
        
        # Intentar importar yfinance
        self.yfinance_available = False
        try:
            import yfinance as yf
            self.yfinance_available = True
            logger.info("yfinance disponible para uso")
        except ImportError:
            logger.warning("yfinance no está disponible. Se usarán métodos alternativos.")
        
        # Intentar importar duckduckgo_search
        self.ddg_available = False
        try:
            from duckduckgo_search import DDGS
            self.ddg_available = True
            self.ddgs = DDGS()
            logger.info("DuckDuckGo Search disponible para uso")
        except ImportError:
            logger.warning("DuckDuckGo Search no está disponible. Se usarán métodos alternativos.")
    
    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Obtiene datos de la caché si están disponibles y no han expirado"""
        if key in self.cache and key in self.cache_expiry:
            if datetime.now().timestamp() < self.cache_expiry[key]:
                return self.cache[key]
        return None
    
    def _cache_data(self, key: str, data: Any) -> None:
        """Almacena datos en la caché con tiempo de expiración"""
        self.cache[key] = data
        self.cache_expiry[key] = datetime.now().timestamp() + self.cache_duration
    
    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene datos completos de un símbolo utilizando múltiples fuentes
        
        Args:
            symbol (str): Símbolo del activo (ej. AAPL, MSFT)
            
        Returns:
            Dict[str, Any]: Datos completos del activo
        """
        cache_key = f"stock_data_{symbol}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Datos a recopilar
        data = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "price": {},
            "company_info": {},
            "stats": {},
            "news": [],
            "analysis": {},
            "options": {}
        }
        
        # Método 1: Usar yfinance (más confiable)
        if self.yfinance_available:
            try:
                logger.info(f"Obteniendo datos de {symbol} con yfinance")
                yf_data = self._get_data_from_yfinance(symbol)
                if yf_data:
                    # Actualizar datos con la información de yfinance
                    data.update(yf_data)
                    logger.info(f"Datos de yfinance obtenidos correctamente para {symbol}")
            except Exception as e:
                logger.error(f"Error obteniendo datos con yfinance: {str(e)}")
        
        # Método 2: Web scraping de Yahoo Finance
        if not data["price"].get("current"):
            try:
                logger.info(f"Obteniendo datos de {symbol} con web scraping")
                scrape_data = self._get_data_from_scraping(symbol)
                if scrape_data:
                    # Actualizar datos con la información del scraping
                    self._merge_dict(data, scrape_data)
                    logger.info(f"Datos de scraping obtenidos correctamente para {symbol}")
            except Exception as e:
                logger.error(f"Error obteniendo datos con scraping: {str(e)}")
        
        # Método 3: Obtener noticias de DuckDuckGo si están disponibles
        if not data["news"] and self.ddg_available:
            try:
                logger.info(f"Obteniendo noticias de {symbol} con DuckDuckGo")
                ddg_news = self._get_news_from_duckduckgo(symbol)
                if ddg_news:
                    data["news"] = ddg_news
                    logger.info(f"Noticias de DuckDuckGo obtenidas correctamente para {symbol}")
            except Exception as e:
                logger.error(f"Error obteniendo noticias con DuckDuckGo: {str(e)}")
        
        # Método 4: Obtener noticias de Google Finance como último recurso
        if not data["news"]:
            try:
                logger.info(f"Obteniendo noticias de {symbol} con Google Finance")
                google_news = self._get_news_from_google_finance(symbol)
                if google_news:
                    data["news"] = google_news
                    logger.info(f"Noticias de Google Finance obtenidas correctamente para {symbol}")
            except Exception as e:
                logger.error(f"Error obteniendo noticias con Google Finance: {str(e)}")
        
        # Almacenar en caché
        self._cache_data(cache_key, data)
        
        return data
    
    def _get_data_from_yfinance(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene datos de un símbolo utilizando yfinance
        
        Args:
            symbol (str): Símbolo del activo
            
        Returns:
            Dict[str, Any]: Datos del activo
        """
        try:
            # Obtener datos básicos
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Crear estructura de datos
            data = {
                "symbol": symbol,
                "price": {
                    "current": info.get("currentPrice", info.get("regularMarketPrice")),
                    "change": info.get("regularMarketChange"),
                    "change_percent": info.get("regularMarketChangePercent"),
                    "open": info.get("regularMarketOpen"),
                    "high": info.get("regularMarketDayHigh"),
                    "low": info.get("regularMarketDayLow"),
                    "volume": info.get("regularMarketVolume"),
                    "previous_close": info.get("regularMarketPreviousClose")
                },
                "company_info": {
                    "name": info.get("shortName", info.get("longName")),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "description": info.get("longBusinessSummary"),
                    "website": info.get("website"),
                    "market_cap": info.get("marketCap"),
                    "employees": info.get("fullTimeEmployees")
                },
                "stats": {
                    "pe_ratio": info.get("trailingPE"),
                    "eps": info.get("trailingEps"),
                    "dividend_yield": info.get("dividendYield"),
                    "beta": info.get("beta"),
                    "52_week_high": info.get("fiftyTwoWeekHigh"),
                    "52_week_low": info.get("fiftyTwoWeekLow"),
                    "50_day_avg": info.get("fiftyDayAverage"),
                    "200_day_avg": info.get("twoHundredDayAverage")
                },
                "analysis": {
                    "target_mean_price": info.get("targetMeanPrice"),
                    "target_high_price": info.get("targetHighPrice"),
                    "target_low_price": info.get("targetLowPrice"),
                    "recommendation": info.get("recommendationKey")
                }
            }
            
            # Obtener noticias
            try:
                news_data = ticker.news
                news = []
                for item in news_data[:10]:  # Limitar a 10 noticias
                    news.append({
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "url": item.get("link", ""),
                        "source": item.get("publisher", "Yahoo Finance"),
                        "date": datetime.fromtimestamp(item.get("providerPublishTime", 0)).strftime("%Y-%m-%d")
                    })
                data["news"] = news
            except Exception as e:
                logger.warning(f"Error obteniendo noticias con yfinance: {str(e)}")
            
            # Obtener datos de opciones
            try:
                options = ticker.options
                if options:
                    # Obtener datos de la primera fecha de vencimiento
                    expiration = options[0]
                    calls = ticker.option_chain(expiration).calls.to_dict('records')
                    puts = ticker.option_chain(expiration).puts.to_dict('records')
                    
                    # Convertir a formato serializable
                    calls_data = []
                    for call in calls[:10]:  # Limitar a 10 opciones
                        calls_data.append({k: float(v) if isinstance(v, (int, float)) else v for k, v in call.items()})
                    
                    puts_data = []
                    for put in puts[:10]:  # Limitar a 10 opciones
                        puts_data.append({k: float(v) if isinstance(v, (int, float)) else v for k, v in put.items()})
                    
                    data["options"] = {
                        "expiration_dates": options,
                        "current_expiration": expiration,
                        "calls": calls_data,
                        "puts": puts_data
                    }
            except Exception as e:
                logger.warning(f"Error obteniendo opciones con yfinance: {str(e)}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error en _get_data_from_yfinance para {symbol}: {str(e)}")
            return {}
    
    def _get_data_from_scraping(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene datos de un símbolo mediante web scraping
        
        Args:
            symbol (str): Símbolo del activo
            
        Returns:
            Dict[str, Any]: Datos del activo
        """
        try:
            # Datos a recopilar
            data = {
                "symbol": symbol,
                "price": {},
                "company_info": {},
                "stats": {},
                "news": [],
                "analysis": {}
            }
            
            # Obtener página principal
            url = f"https://finance.yahoo.com/quote/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Error obteniendo datos para {symbol}: HTTP {response.status_code}")
                return data
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extraer precio actual
            try:
                price_elem = soup.select_one('[data-test="qsp-price"]')
                if price_elem:
                    data["price"]["current"] = float(price_elem.text.replace(",", ""))
                
                # Cambio y porcentaje de cambio
                change_elems = soup.select('[data-test="qsp-price-change"]')
                if len(change_elems) >= 2:
                    data["price"]["change"] = float(change_elems[0].text.replace(",", ""))
                    # Extraer solo el número del porcentaje (quitar paréntesis y %)
                    percent_text = change_elems[1].text.strip("()%")
                    data["price"]["change_percent"] = float(percent_text)
            except Exception as e:
                logger.debug(f"Error obteniendo precio para {symbol}: {str(e)}")
            
            # Nombre de la empresa
            try:
                name_elem = soup.select_one('h1')
                if name_elem:
                    data["company_info"]["name"] = name_elem.text.strip()
            except Exception as e:
                logger.debug(f"Error obteniendo nombre para {symbol}: {str(e)}")
            
            # Obtener noticias
            try:
                news_url = f"https://finance.yahoo.com/quote/{symbol}/news"
                news_response = requests.get(news_url, headers=self.headers, timeout=10)
                
                if news_response.status_code == 200:
                    news_soup = BeautifulSoup(news_response.text, "html.parser")
                    news_items = news_soup.select('div[data-test="story"]')
                    
                    if not news_items:
                        # Intentar con otro selector si el primero falla
                        news_items = news_soup.select('li[class*="js-stream-content"]')
                    
                    if news_items:
                        for item in news_items[:5]:  # Limitar a 5 noticias
                            # Extraer título
                            title_element = item.select_one('h3, a[class*="headline"]')
                            title = title_element.text.strip() if title_element else "Sin título"
                            
                            # Extraer enlace
                            link_element = item.select_one('a[href]')
                            url = link_element['href'] if link_element and 'href' in link_element.attrs else "#"
                            
                            # Convertir enlaces relativos a absolutos
                            if url.startswith('/'):
                                url = f"https://finance.yahoo.com{url}"
                            
                            # Extraer descripción/resumen
                            summary_element = item.select_one('p, div[class*="summary"]')
                            summary = summary_element.text.strip() if summary_element else ""
                            
                            # Extraer fuente y fecha
                            source_element = item.select_one('div[class*="author"], span[class*="provider-name"]')
                            source = source_element.text.strip() if source_element else "Yahoo Finance"
                            
                            date_element = item.select_one('div[class*="date"], span[class*="date"]')
                            date_str = date_element.text.strip() if date_element else ""
                            
                            # Convertir fecha relativa a absoluta si es posible
                            try:
                                if "ago" in date_str.lower():
                                    # Fecha aproximada basada en texto relativo
                                    date = datetime.now().strftime("%Y-%m-%d")
                                else:
                                    # Intentar parsear la fecha
                                    date = datetime.strptime(date_str, "%b %d, %Y").strftime("%Y-%m-%d")
                            except:
                                date = datetime.now().strftime("%Y-%m-%d")
                            
                            data["news"].append({
                                "title": title,
                                "summary": summary,
                                "url": url,
                                "source": source,
                                "date": date
                            })
            except Exception as e:
                logger.debug(f"Error obteniendo noticias para {symbol}: {str(e)}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error en _get_data_from_scraping para {symbol}: {str(e)}")
            return {}
    
    def _get_news_from_duckduckgo(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Obtiene noticias de un símbolo utilizando DuckDuckGo
        
        Args:
            symbol (str): Símbolo del activo
            
        Returns:
            List[Dict[str, Any]]: Lista de noticias
        """
        if not self.ddg_available:
            return []
        
        try:
            # Buscar noticias recientes sobre el símbolo
            company_name = self._get_company_name(symbol)
            query = f"{company_name} {symbol} stock news"
            
            # Realizar búsqueda de noticias
            results = self.ddgs.news(query, max_results=5)
            
            news = []
            for item in results:
                news.append({
                    "title": item.get("title", ""),
                    "summary": item.get("body", ""),
                    "url": item.get("url", ""),
                    "source": item.get("source", ""),
                    "date": item.get("date", datetime.now().strftime("%Y-%m-%d"))
                })
            
            return news
            
        except Exception as e:
            logger.error(f"Error en _get_news_from_duckduckgo para {symbol}: {str(e)}")
            return []
    
    def _get_news_from_google_finance(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Obtiene noticias de un símbolo utilizando Google Finance
        
        Args:
            symbol (str): Símbolo del activo
            
        Returns:
            List[Dict[str, Any]]: Lista de noticias
        """
        try:
            url = f"https://www.google.com/finance/quote/{symbol}:NASDAQ"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                # Intentar con NYSE
                url = f"https://www.google.com/finance/quote/{symbol}:NYSE"
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code != 200:
                    logger.warning(f"Error obteniendo datos de Google Finance para {symbol}: HTTP {response.status_code}")
                    return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Buscar sección de noticias
            news_section = soup.select('div[role="feed"]')
            if not news_section:
                return []
            
            news_items = news_section[0].select('div[role="article"]')
            
            news = []
            for item in news_items[:5]:  # Limitar a 5 noticias
                # Extraer título
                title_element = item.select_one('div[role="heading"]')
                title = title_element.text.strip() if title_element else "Sin título"
                
                # Extraer enlace
                link_element = item.select_one('a[href]')
                url = link_element['href'] if link_element and 'href' in link_element.attrs else "#"
                
                # Convertir enlaces relativos a absolutos
                if url.startswith('/'):
                    url = f"https://www.google.com{url}"
                
                # Extraer fuente y fecha
                source_element = item.select_one('div:nth-child(2) > div:nth-child(1)')
                source = source_element.text.strip() if source_element else "Google Finance"
                
                date_element = item.select_one('div:nth-child(2) > div:nth-child(2)')
                date_str = date_element.text.strip() if date_element else ""
                
                # Convertir fecha relativa a absoluta
                date = datetime.now().strftime("%Y-%m-%d")
                
                # Extraer resumen si está disponible
                summary_element = item.select_one('div[role="heading"] + div')
                summary = summary_element.text.strip() if summary_element else ""
                
                news.append({
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "source": source,
                    "date": date
                })
            
            return news
            
        except Exception as e:
            logger.error(f"Error en _get_news_from_google_finance para {symbol}: {str(e)}")
            return []
    
    def _get_company_name(self, symbol: str) -> str:
        """
        Obtiene el nombre de la empresa a partir del símbolo
        
        Args:
            symbol (str): Símbolo del activo
            
        Returns:
            str: Nombre de la empresa
        """
        # Intentar obtener de yfinance
        if self.yfinance_available:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return info.get("shortName", info.get("longName", symbol))
            except:
                pass
        
        # Intentar obtener de scraping
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                name_elem = soup.select_one('h1')
                if name_elem:
                    return name_elem.text.strip()
        except:
            pass
        
        # Devolver el símbolo como fallback
        return symbol
    
    def _merge_dict(self, target: Dict, source: Dict) -> None:
        """
        Combina dos diccionarios de forma recursiva, actualizando solo los valores vacíos
        
        Args:
            target (Dict): Diccionario destino
            source (Dict): Diccionario fuente
        """
        for key, value in source.items():
            if key in target:
                if isinstance(value, dict) and isinstance(target[key], dict):
                    # Recursivamente combinar diccionarios anidados
                    self._merge_dict(target[key], value)
                elif not target[key]:
                    # Actualizar solo si el valor destino está vacío
                    target[key] = value
            else:
                # Añadir clave si no existe
                target[key] = value
    
    def process_with_expert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa los datos con el agente experto para mejorar la calidad
        
        Args:
            data (Dict[str, Any]): Datos a procesar
            
        Returns:
            Dict[str, Any]: Datos procesados
        """
        # Aquí se implementaría la lógica para procesar con el agente experto
        # Por ahora, simplemente devolvemos los datos sin cambios
        return data

# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia
    market_data = EnhancedMarketData()
    
    # Obtener datos para un símbolo
    symbol = "AAPL"
    data = market_data.get_stock_data(symbol)
    
    # Mostrar resultados
    print(f"Datos para {symbol}:")
    
    # Precio actual
    if data["price"].get("current"):
        print(f"Precio actual: ${data['price']['current']}")
        if data["price"].get("change") and data["price"].get("change_percent"):
            print(f"Cambio: {data['price']['change']} ({data['price']['change_percent']}%)")
    else:
        print("Precio actual: No disponible")
    
    # Información de la empresa
    if data["company_info"].get("name"):
        print(f"\nEmpresa: {data['company_info']['name']}")
        if data["company_info"].get("sector"):
            print(f"Sector: {data['company_info']['sector']}")
        if data["company_info"].get("industry"):
            print(f"Industria: {data['company_info']['industry']}")
    
    # Noticias
    print("\nNoticias recientes:")
    if data["news"]:
        for i, news in enumerate(data["news"][:3], 1):
            print(f"{i}. {news['title']}")
            print(f"   Fuente: {news['source']} - Fecha: {news['date']}")
            if news.get("url"):
                print(f"   URL: {news['url']}")
    else:
        print("No hay noticias disponibles")
    
    # Análisis
    print("\nAnálisis:")
    if data["analysis"].get("recommendation"):
        print(f"Recomendación: {data['analysis']['recommendation']}")
    if data["analysis"].get("target_mean_price"):
        print(f"Precio objetivo promedio: ${data['analysis']['target_mean_price']}")
        if data["analysis"].get("target_low_price") and data["analysis"].get("target_high_price"):
            print(f"Rango de precio objetivo: ${data['analysis']['target_low_price']} - ${data['analysis']['target_high_price']}")
    else:
        print("No hay análisis disponible")
    
    # Estadísticas
    print("\nEstadísticas clave:")
    if data["stats"]:
        if data["stats"].get("pe_ratio"):
            print(f"P/E Ratio: {data['stats']['pe_ratio']}")
        if data["stats"].get("eps"):
            print(f"EPS: {data['stats']['eps']}")
        if data["stats"].get("dividend_yield"):
            print(f"Rendimiento de dividendos: {data['stats']['dividend_yield']}")
        if data["stats"].get("market_cap"):
            print(f"Capitalización de mercado: {data['stats']['market_cap']}")
    else:
        print("No hay estadísticas disponibles")
