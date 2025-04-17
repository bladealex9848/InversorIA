#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yahoo Finance Scraper - Módulo para obtener datos y noticias financieras de múltiples fuentes
Versión optimizada con sistema robusto de fallbacks
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import re
import time
import random
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Intentar importar módulos opcionales
YFINANCE_AVAILABLE = False
try:
    import yfinance as yf

    YFINANCE_AVAILABLE = True
    logger.info("yfinance disponible para uso")
except ImportError:
    logger.warning("yfinance no está disponible. Se usarán métodos alternativos.")

DDG_AVAILABLE = False
try:
    from duckduckgo_search import DDGS

    DDG_AVAILABLE = True
    logger.info("DuckDuckGo Search disponible para uso")
except ImportError:
    logger.warning(
        "DuckDuckGo Search no está disponible. Se usarán métodos alternativos."
    )


class YahooFinanceScraper:
    """Clase para obtener datos y noticias financieras de múltiples fuentes"""

    def __init__(self, api_keys=None):
        """Inicializa el scraper con headers para simular un navegador"""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.base_url = "https://finance.yahoo.com"
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 3600  # 1 hora en segundos
        self.api_keys = api_keys or {}

        # Inicializar DuckDuckGo si está disponible
        self.ddgs = None
        if DDG_AVAILABLE:
            try:
                self.ddgs = DDGS()
                logger.info("DuckDuckGo Search inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando DuckDuckGo Search: {str(e)}")

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

    def get_quote_data(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene datos básicos de cotización para un símbolo

        Args:
            symbol (str): Símbolo del activo (ej. AAPL, MSFT)

        Returns:
            Dict[str, Any]: Datos de cotización
        """
        cache_key = f"quote_{symbol}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        # Intentar primero con yfinance (más confiable)
        if YFINANCE_AVAILABLE:
            try:
                logger.info(
                    f"Obteniendo datos de cotización para {symbol} con yfinance"
                )
                ticker = yf.Ticker(symbol)
                info = ticker.info

                if info:
                    data = {
                        "symbol": symbol,
                        "timestamp": datetime.now().isoformat(),
                        "price": {
                            "current": info.get(
                                "currentPrice", info.get("regularMarketPrice")
                            ),
                            "change": info.get("regularMarketChange"),
                            "change_percent": info.get("regularMarketChangePercent"),
                            "open": info.get("regularMarketOpen"),
                            "high": info.get("regularMarketDayHigh"),
                            "low": info.get("regularMarketDayLow"),
                            "previous_close": info.get("regularMarketPreviousClose"),
                        },
                        "company_info": {
                            "name": info.get("shortName", info.get("longName", symbol)),
                            "sector": info.get("sector"),
                            "industry": info.get("industry"),
                            "website": info.get("website"),
                            "description": info.get("longBusinessSummary"),
                        },
                        "stats": {
                            "market_cap": info.get("marketCap"),
                            "beta": info.get("beta"),
                            "pe_ratio": info.get("trailingPE"),
                            "eps": info.get("trailingEps"),
                            "dividend_rate": info.get("dividendRate"),
                            "dividend_yield": info.get("dividendYield"),
                            "52wk_high": info.get("fiftyTwoWeekHigh"),
                            "52wk_low": info.get("fiftyTwoWeekLow"),
                            "avg_volume": info.get("averageVolume"),
                            "volume": info.get("volume"),
                        },
                    }

                    # Almacenar en caché
                    self._cache_data(cache_key, data)
                    return data
            except Exception as e:
                logger.warning(
                    f"Error obteniendo datos con yfinance: {str(e)}. Intentando con API..."
                )

        # Intentar con la API de Yahoo Finance
        try:
            api_url = (
                f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
            )
            response = requests.get(api_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                json_data = response.json()
                quote_data = json_data.get("quoteResponse", {}).get("result", [])

                if quote_data and len(quote_data) > 0:
                    result = quote_data[0]

                    data = {
                        "symbol": symbol,
                        "timestamp": datetime.now().isoformat(),
                        "price": {
                            "current": result.get("regularMarketPrice"),
                            "change": result.get("regularMarketChange"),
                            "change_percent": result.get("regularMarketChangePercent"),
                            "open": result.get("regularMarketOpen"),
                            "high": result.get("regularMarketDayHigh"),
                            "low": result.get("regularMarketDayLow"),
                            "previous_close": result.get("regularMarketPreviousClose"),
                        },
                        "company_info": {
                            "name": result.get(
                                "shortName", result.get("longName", symbol)
                            ),
                            "exchange": result.get("fullExchangeName"),
                            "currency": result.get("currency"),
                        },
                        "stats": {
                            "market_cap": result.get("marketCap"),
                            "volume": result.get("regularMarketVolume"),
                            "avg_volume": result.get("averageDailyVolume3Month"),
                            "pe_ratio": result.get("trailingPE"),
                            "eps": result.get("epsTrailingTwelveMonths"),
                        },
                    }

                    # Almacenar en caché
                    self._cache_data(cache_key, data)
                    logger.info(
                        f"Datos de cotización obtenidos desde la API para {symbol}"
                    )
                    return data
        except Exception as e:
            logger.warning(
                f"Error obteniendo datos de la API de Yahoo Finance: {str(e)}. Intentando con scraping..."
            )

        # Si los métodos anteriores fallan, intentar con scraping directo
        try:
            url = f"{self.base_url}/quote/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.warning(
                    f"Error obteniendo datos para {symbol}: HTTP {response.status_code}"
                )
                return {"error": f"HTTP {response.status_code}", "symbol": symbol}

            soup = BeautifulSoup(response.text, "html.parser")

            # Datos básicos
            data = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "price": {},
                "company_info": {},
                "stats": {},
            }

            # Precio actual - Intentar varios selectores
            try:
                price_elem = None
                for selector in [
                    '[data-test="qsp-price"]',
                    'fin-streamer[data-field="regularMarketPrice"]',
                    'div[class*="price"] span',
                    'fin-streamer[data-symbol="'
                    + symbol
                    + '"][data-field="regularMarketPrice"]',
                ]:
                    price_elem = soup.select_one(selector)
                    if price_elem:
                        break

                if price_elem:
                    price_text = price_elem.text.replace(",", "")
                    try:
                        data["price"]["current"] = float(price_text)
                    except ValueError:
                        # Extraer usando regex si hay caracteres extra
                        price_match = re.search(r"(\d+\.\d+)", price_text)
                        if price_match:
                            data["price"]["current"] = float(price_match.group(1))

                # Cambio y porcentaje
                change_elem = None
                for selector in [
                    '[data-test="qsp-price-change"]',
                    'fin-streamer[data-field="regularMarketChange"]',
                    'div[class*="price-change"]',
                ]:
                    change_elems = soup.select(selector)
                    if change_elems:
                        break

                if change_elems and len(change_elems) >= 1:
                    try:
                        data["price"]["change"] = float(
                            change_elems[0].text.replace(",", "")
                        )
                    except (ValueError, IndexError):
                        pass

                # Buscar el porcentaje de cambio
                percent_elem = None
                for selector in [
                    'fin-streamer[data-field="regularMarketChangePercent"]',
                    'span[class*="percent"]',
                    'div[class*="percent"]',
                ]:
                    percent_elem = soup.select_one(selector)
                    if percent_elem:
                        break

                if percent_elem:
                    try:
                        # Extraer solo el número del porcentaje (quitar paréntesis y %)
                        percent_text = (
                            percent_elem.text.strip()
                            .replace("(", "")
                            .replace(")", "")
                            .replace("%", "")
                        )
                        data["price"]["change_percent"] = float(percent_text)
                    except ValueError:
                        pass
            except Exception as e:
                logger.debug(f"Error obteniendo precio para {symbol}: {str(e)}")

            # Nombre de la empresa
            try:
                name_elem = None
                for selector in [
                    "h1",
                    'div[class*="title"]',
                    'div[class*="header"] h1',
                ]:
                    name_elem = soup.select_one(selector)
                    if name_elem:
                        break

                if name_elem:
                    data["company_info"]["name"] = name_elem.text.strip()
            except Exception as e:
                logger.debug(f"Error obteniendo nombre para {symbol}: {str(e)}")

            # Estadísticas clave
            try:
                stat_tables = soup.select(
                    'table[data-test="qsp-statistics"], div[class*="key-statistics"] table'
                )

                for table in stat_tables:
                    rows = table.select("tr")
                    for row in rows:
                        cells = row.select("td, th")
                        if len(cells) >= 2:
                            key = (
                                cells[0]
                                .text.strip()
                                .lower()
                                .replace(" ", "_")
                                .replace(".", "")
                            )
                            value = cells[1].text.strip()
                            data["stats"][key] = value
            except Exception as e:
                logger.debug(f"Error obteniendo estadísticas para {symbol}: {str(e)}")

            # Almacenar en caché
            self._cache_data(cache_key, data)

            logger.info(
                f"Datos de cotización obtenidos mediante scraping para {symbol}"
            )
            return data

        except Exception as e:
            logger.error(f"Error en get_quote_data para {symbol}: {str(e)}")
            return {"error": str(e), "symbol": symbol}

    def get_news(self, symbol: str, max_news: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene noticias para un símbolo desde múltiples fuentes

        Args:
            symbol (str): Símbolo del activo
            max_news (int): Número máximo de noticias a obtener

        Returns:
            List[Dict[str, Any]]: Lista de noticias
        """
        cache_key = f"news_{symbol}_{max_news}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        # Lista de fuentes en orden de prioridad
        news_sources = [
            (
                self._get_news_from_yahoo_direct,
                "Yahoo Finance Direct",
                symbol,
                max_news,
            ),  # Nueva fuente prioritaria
            (self._get_news_from_yfinance, "yfinance", symbol, max_news),
            (self._get_news_from_yahoo_api, "Yahoo API", symbol, max_news),
            (self._get_news_from_finviz, "FinViz", symbol, max_news),
            (self._get_news_from_alpha_vantage, "Alpha Vantage", symbol, max_news),
            (self._get_news_from_duckduckgo, "DuckDuckGo", symbol, max_news),
            (self._get_news_from_investing, "Investing.com", symbol, max_news),
        ]

        # Intentar cada fuente en orden hasta obtener resultados
        for source_func, source_name, src_symbol, src_max_news in news_sources:
            try:
                logger.info(f"Obteniendo noticias de {symbol} con {source_name}")
                news_data = source_func(src_symbol, src_max_news)

                if news_data and isinstance(news_data, list) and len(news_data) > 0:
                    # Filtrar noticias vacías, inválidas o sin URL
                    news_data = [
                        n
                        for n in news_data
                        if n.get("title")
                        and n.get("title") != ""
                        and n.get("url")
                        and n.get("url") != ""
                    ]

                    # Si hay noticias sin URL, intentar generar URLs basadas en el título
                    for news_item in news_data:
                        if not news_item.get("url") or news_item.get("url") == "":
                            # Generar URL de búsqueda en Yahoo Finance
                            title_slug = news_item.get("title", "").replace(" ", "+")[
                                :100
                            ]
                            news_item["url"] = (
                                f"https://finance.yahoo.com/news/search?q={title_slug}"
                            )
                            logger.info(
                                f"URL generada para noticia: {news_item['url']}"
                            )

                    if news_data:  # Si hay noticias válidas
                        # Almacenar en caché
                        self._cache_data(cache_key, news_data)
                        logger.info(
                            f"Noticias de {source_name} obtenidas correctamente para {symbol}"
                        )
                        return news_data
            except Exception as e:
                logger.info(
                    f"⚠️ No se pudieron obtener noticias con {source_name}: {str(e)}. Intentando fuentes alternativas..."
                )

        # Si todo falla, devolver lista vacía
        logger.info(
            f"🚨 No se pudieron obtener noticias para {symbol} de ninguna fuente. Se usarán datos sintéticos o alternativos."
        )
        return []

    def _get_news_from_yfinance(
        self, symbol: str, max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene noticias usando yfinance"""
        if not YFINANCE_AVAILABLE:
            return []

        try:
            ticker = yf.Ticker(symbol)
            news_data = ticker.news

            if news_data and isinstance(news_data, list) and len(news_data) > 0:
                news = []
                for item in news_data[:max_news]:
                    if not isinstance(item, dict) or not item.get("title"):
                        continue

                    news_item = {
                        "title": item.get("title", "Sin título"),
                        "summary": item.get("summary", ""),
                        "url": item.get("link", ""),
                        "source": item.get("publisher", "Yahoo Finance"),
                        "date": datetime.now().strftime(
                            "%Y-%m-%d"
                        ),  # Valor por defecto
                        "_source_method": "yfinance",
                    }

                    # Obtener fecha de publicación si está disponible
                    if item.get("providerPublishTime") and isinstance(
                        item.get("providerPublishTime"), (int, float)
                    ):
                        try:
                            timestamp = item.get("providerPublishTime")
                            if timestamp > 0:
                                news_item["date"] = datetime.fromtimestamp(
                                    timestamp
                                ).strftime("%Y-%m-%d")
                        except:
                            pass

                    news.append(news_item)

                return news
        except Exception as e:
            logger.info(
                f"⚠️ No se pudieron obtener noticias con yfinance: {str(e)}. Intentando fuentes alternativas..."
            )

        return []

    def _get_news_from_yahoo_api(
        self, symbol: str, max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene noticias usando la API de Yahoo Finance"""
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount={max_news}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                json_data = response.json()
                news_items = json_data.get("news", [])

                if news_items:
                    news = []
                    for item in news_items[:max_news]:
                        # Verificar que tenga al menos título
                        if not item.get("title"):
                            continue

                        # Crear objeto de noticia
                        news_item = {
                            "title": item.get("title", "Sin título"),
                            "summary": item.get("summary", ""),
                            "url": item.get("link", ""),
                            "source": item.get("publisher", "Yahoo Finance"),
                            "date": datetime.now().strftime(
                                "%Y-%m-%d"
                            ),  # Valor por defecto
                            "_source_method": "yahoo_api",
                        }

                        # Obtener fecha de publicación
                        if item.get("providerPublishTime"):
                            try:
                                timestamp = item.get("providerPublishTime")
                                if timestamp > 0:
                                    news_item["date"] = datetime.fromtimestamp(
                                        timestamp
                                    ).strftime("%Y-%m-%d")
                            except:
                                pass

                        news.append(news_item)

                    return news
        except Exception as e:
            logger.info(
                f"⚠️ No se pudieron obtener noticias con la API de Yahoo: {str(e)}. Intentando fuentes alternativas..."
            )

        return []

    def _get_news_from_finviz(
        self, symbol: str, max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene noticias de FinViz"""
        try:
            url = f"https://finviz.com/quote.ashx?t={symbol}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # En FinViz, las noticias están en una tabla con id "news-table"
            news_table = soup.select_one("table#news-table")
            if not news_table:
                return []

            news_rows = news_table.select("tr")

            news = []
            current_date = None

            for i, row in enumerate(news_rows):
                if len(news) >= max_news:
                    break

                # Verificar si hay celdas
                cells = row.select("td")
                if len(cells) < 2:
                    continue

                # Extraer fecha/hora
                date_cell = cells[0].text.strip()

                # La fecha sólo aparece en la primera noticia del día
                # Las siguientes solo tienen hora
                if "-" in date_cell:
                    # Nueva fecha encontrada
                    date_parts = date_cell.split()
                    current_date = date_parts[0]
                    time_str = date_parts[1] if len(date_parts) > 1 else ""
                else:
                    # Solo hora, mantener la fecha anterior
                    time_str = date_cell

                # Normalizar fecha
                try:
                    date_obj = datetime.strptime(current_date, "%b-%d-%y")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except:
                    formatted_date = datetime.now().strftime("%Y-%m-%d")

                # Extraer título y enlace
                title_cell = cells[1]
                a_tag = title_cell.a

                if a_tag:
                    title = a_tag.text.strip()
                    url = a_tag["href"]

                    # Buscar fuente (texto junto al enlace)
                    source_span = title_cell.select_one("span.news-source")
                    source = source_span.text.strip() if source_span else "FinViz"

                    news.append(
                        {
                            "title": title,
                            "summary": "",  # FinViz no proporciona resúmenes
                            "url": url,
                            "source": source,
                            "date": formatted_date,
                            "_source_method": "finviz",
                        }
                    )

            return news
        except Exception as e:
            logger.info(
                f"⚠️ No se pudieron obtener noticias de FinViz: {str(e)}. Intentando fuentes alternativas..."
            )

        return []

    def _get_news_from_alpha_vantage(
        self, symbol: str, max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene noticias desde Alpha Vantage"""
        if "alpha_vantage" not in self.api_keys:
            return []

        try:
            api_key = self.api_keys["alpha_vantage"]
            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={api_key}&limit={max_news}"

            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return []

            data = response.json()
            news = []

            if "feed" in data and isinstance(data["feed"], list):
                for item in data["feed"][:max_news]:
                    # Procesar fecha
                    if "time_published" in item:
                        try:
                            pub_date = datetime.strptime(
                                item["time_published"][:19], "%Y%m%dT%H%M%S"
                            )
                            date_str = pub_date.strftime("%Y-%m-%d")
                        except:
                            date_str = datetime.now().strftime("%Y-%m-%d")
                    else:
                        date_str = datetime.now().strftime("%Y-%m-%d")

                    # Obtener sentimiento
                    sentiment_score = 0.5  # Neutral por defecto
                    if "overall_sentiment_score" in item:
                        try:
                            sentiment_score = float(item["overall_sentiment_score"])
                        except:
                            pass

                    news.append(
                        {
                            "title": item.get("title", "Sin título"),
                            "summary": item.get("summary", ""),
                            "url": item.get("url", "#"),
                            "source": item.get("source", "Alpha Vantage"),
                            "date": date_str,
                            "sentiment": sentiment_score,
                            "_source_method": "alpha_vantage",
                        }
                    )

                return news
        except Exception as e:
            logger.info(
                f"⚠️ No se pudieron obtener noticias de Alpha Vantage: {str(e)}. Intentando fuentes alternativas..."
            )

        return []

    def _get_news_from_duckduckgo(
        self, symbol: str, max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene noticias usando DuckDuckGo"""
        if not DDG_AVAILABLE or not self.ddgs:
            return []

        try:
            # Obtener nombre de la empresa para mejorar la búsqueda
            company_name = self._get_company_name(symbol)
            query = f"{company_name} {symbol} stock news"

            # Realizar búsqueda de noticias
            results = self.ddgs.news(query, max_results=max_news)

            if results:
                news = []
                for item in results:
                    # Calcular un sentimiento básico (neutral por defecto)
                    sentiment_value = 0.5

                    # Análisis simple basado en palabras clave
                    title_lower = item.get("title", "").lower()
                    if any(
                        word in title_lower
                        for word in ["up", "rise", "gain", "bull", "positive", "growth"]
                    ):
                        sentiment_value = 0.7  # Positivo
                    elif any(
                        word in title_lower
                        for word in ["down", "fall", "drop", "bear", "negative", "loss"]
                    ):
                        sentiment_value = 0.3  # Negativo

                    news.append(
                        {
                            "title": item.get("title", ""),
                            "summary": item.get("body", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", ""),
                            "date": self._normalize_date_format(item.get("date", "")),
                            "sentiment": sentiment_value,
                            "_source_method": "duckduckgo",
                        }
                    )

                return news
        except Exception as e:
            logger.info(
                f"⚠️ No se pudieron obtener noticias con DuckDuckGo: {str(e)}. Intentando fuentes alternativas..."
            )

        return []

    def _get_news_from_yahoo_direct(
        self, symbol: str, max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene noticias directamente de la página de noticias de Yahoo Finance"""
        try:
            # URL directa a la página de noticias de Yahoo Finance para el símbolo
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.info(
                    f"No se pudo acceder a la página de noticias de Yahoo Finance para {symbol}"
                )
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # Buscar elementos de noticias
            news_items = []

            # Intentar diferentes selectores para adaptarse a posibles cambios en la estructura de la página
            for selector in [
                'li[class*="js-stream-content"]',
                'div[class*="Ov(h)"]',
                "div.news-stream-item",
                "ul.My(0) li",
            ]:
                items = soup.select(selector)
                if items:
                    news_items = items
                    break

            if not news_items:
                # Intentar encontrar cualquier enlace que parezca una noticia
                all_links = soup.select('a[href*="/news/"]')
                if all_links:
                    # Crear noticias a partir de los enlaces encontrados
                    news = []
                    processed_urls = set()  # Para evitar duplicados

                    for link in all_links[
                        : max_news * 2
                    ]:  # Obtener más enlaces de los necesarios para filtrar
                        href = link.get("href", "")
                        if not href or href in processed_urls:
                            continue

                        # Asegurarse de que es una URL completa
                        if href.startswith("/"):
                            href = f"https://finance.yahoo.com{href}"

                        processed_urls.add(href)

                        title = link.text.strip()
                        if (
                            not title or len(title) < 10
                        ):  # Ignorar enlaces con texto muy corto
                            continue

                        news.append(
                            {
                                "title": title,
                                "summary": "",  # No hay resumen disponible
                                "url": href,
                                "source": "Yahoo Finance",
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "_source_method": "yahoo_direct_links",
                            }
                        )

                        if len(news) >= max_news:
                            break

                    return news

                return []

            # Procesar los elementos de noticias encontrados
            news = []
            for item in news_items[:max_news]:
                # Buscar el título y enlace
                link = None
                for link_selector in ['a[href*="/news/"]', "a"]:
                    links = item.select(link_selector)
                    if links:
                        for l in links:
                            # Verificar que el enlace parece ser de una noticia
                            href = l.get("href", "")
                            if "/news/" in href or "/m/" in href:
                                link = l
                                break
                        if link:
                            break

                if not link:
                    continue

                # Extraer título y URL
                title = link.text.strip()
                href = link.get("href", "")

                # Asegurarse de que es una URL completa
                if href.startswith("/"):
                    href = f"https://finance.yahoo.com{href}"

                # Buscar resumen
                summary = ""
                summary_elem = item.select_one('p, div[class*="Fz(14px)"]')
                if summary_elem:
                    summary = summary_elem.text.strip()

                # Buscar fuente y fecha
                source = "Yahoo Finance"
                date_str = datetime.now().strftime("%Y-%m-%d")

                source_elem = item.select_one('span[class*="C($tertiaryColor)"]')
                if source_elem:
                    source_text = source_elem.text.strip()
                    # Intentar extraer fuente y fecha del texto (ej: "Motley Fool·hace 2 días")
                    if "·" in source_text:
                        parts = source_text.split("·")
                        if len(parts) >= 1:
                            source = parts[0].strip()

                news.append(
                    {
                        "title": title,
                        "summary": summary,
                        "url": href,
                        "source": source,
                        "date": date_str,
                        "_source_method": "yahoo_direct",
                    }
                )

            return news

        except Exception as e:
            logger.info(
                f"⚠️ No se pudieron obtener noticias directamente de Yahoo Finance: {str(e)}. Intentando fuentes alternativas..."
            )
            return []

    def _get_news_from_investing(
        self, symbol: str, max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene noticias de Investing.com"""
        try:
            # Investing.com requiere una búsqueda para encontrar el perfil de la acción
            search_url = f"https://www.investing.com/search/?q={symbol}"
            response = requests.get(search_url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # Buscar el enlace a la página del instrumento
            stock_url = None

            # Buscar en resultados de búsqueda
            for selector in [
                "a.js-inner-all-results-quote-item",
                'a[class*="searchSuggest"]',
                'a[href*="/equities/"]',
                "table.searchSuggest a",
            ]:
                links = soup.select(selector)
                for link in links:
                    if symbol.lower() in link.text.lower():
                        stock_url = (
                            "https://www.investing.com" + link["href"]
                            if link["href"].startswith("/")
                            else link["href"]
                        )
                        break

                if stock_url:
                    break

            if not stock_url:
                # Intentar URL directa para los símbolos más comunes
                stock_url = f"https://www.investing.com/equities/{symbol.lower()}"

            # Obtener la página de noticias del instrumento
            news_url = (
                stock_url + "-news"
                if not stock_url.endswith("/")
                else stock_url + "news"
            )
            response = requests.get(news_url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # Extraer artículos de noticias
            news_items = []
            for selector in [
                "div.articleItem",
                "div.textDiv",
                "article.js-article-item",
                "div.common-articles article",
            ]:
                items = soup.select(selector)
                if items:
                    news_items = items
                    break

            news = []
            for item in news_items[:max_news]:
                # Extraer título
                title_element = None
                for selector in ["a.title", 'a[class*="title"]', "a.linkTitle", "h4 a"]:
                    title_element = item.select_one(selector)
                    if title_element:
                        break

                if not title_element:
                    continue

                title = title_element.text.strip()
                url = (
                    "https://www.investing.com" + title_element["href"]
                    if title_element["href"].startswith("/")
                    else title_element["href"]
                )

                # Extraer resumen
                summary_element = item.select_one('p, div[class*="articleSummary"]')
                summary = summary_element.text.strip() if summary_element else ""

                # Extraer fecha
                date_element = item.select_one("span.date, time")
                date_str = date_element.text.strip() if date_element else ""
                date = (
                    self._normalize_date_format(date_str)
                    if date_str
                    else datetime.now().strftime("%Y-%m-%d")
                )

                # Extraer fuente
                source = "Investing.com"

                news.append(
                    {
                        "title": title,
                        "summary": summary,
                        "url": url,
                        "source": source,
                        "date": date,
                        "_source_method": "investing",
                    }
                )

            return news
        except Exception as e:
            logger.info(
                f"⚠️ No se pudieron obtener noticias de Investing.com: {str(e)}. Intentando fuentes alternativas..."
            )

        return []

    def get_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene análisis y recomendaciones para un símbolo

        Args:
            symbol (str): Símbolo del activo

        Returns:
            Dict[str, Any]: Datos de análisis
        """
        cache_key = f"analysis_{symbol}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        # Estructura base para la respuesta
        data = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "recommendations": {},
            "price_targets": {},
            "ratings": [],
        }

        # Intentar primero con yfinance (más completo)
        if YFINANCE_AVAILABLE:
            try:
                logger.info(f"Obteniendo análisis para {symbol} con yfinance")
                ticker = yf.Ticker(symbol)

                # Obtener info básica (siempre disponible)
                info = ticker.info

                # Extraer objetivos de precio directamente de info
                if info:
                    target_fields = [
                        ("targetMeanPrice", "average"),
                        ("targetHighPrice", "high"),
                        ("targetLowPrice", "low"),
                        ("targetMedianPrice", "median"),
                    ]

                    for src_field, dest_field in target_fields:
                        if src_field in info and info[src_field] is not None:
                            data["price_targets"][dest_field] = info[src_field]

                # Intentar obtener recomendaciones
                try:
                    recommendations = ticker.recommendations
                    if recommendations is not None and not recommendations.empty:
                        # Buscar diferentes nombres de columnas posibles
                        for col in ["To Grade", "toGrade", "grade", "recommendation"]:
                            if col in recommendations.columns:
                                try:
                                    rec_counts = (
                                        recommendations[col].value_counts().to_dict()
                                    )

                                    # Determinar la recomendación promedio
                                    if rec_counts:
                                        most_common = max(
                                            rec_counts.items(), key=lambda x: x[1]
                                        )
                                        data["recommendations"]["average"] = (
                                            most_common[0]
                                        )

                                        # Agregar recuentos
                                        for grade, count in rec_counts.items():
                                            key = (
                                                grade.lower()
                                                .replace(" ", "_")
                                                .replace("-", "_")
                                            )
                                            data["recommendations"][key] = int(count)

                                        # Incluir historial reciente
                                        for idx, row in recommendations.tail(
                                            10
                                        ).iterrows():
                                            rating = {
                                                "date": (
                                                    idx.strftime("%Y-%m-%d")
                                                    if hasattr(idx, "strftime")
                                                    else str(idx)
                                                ),
                                                "firm": (
                                                    row.get("Firm", "")
                                                    if "Firm" in row
                                                    else ""
                                                ),
                                                "action": (
                                                    f"{row.get('From Grade', '')} to {row.get(col, '')}"
                                                    if "From Grade" in row
                                                    else row.get(col, "")
                                                ),
                                                "rating": row.get(col, ""),
                                            }
                                            data["ratings"].append(rating)
                                except Exception as e:
                                    logger.debug(
                                        f"Error procesando columna {col}: {str(e)}"
                                    )
                                break
                except Exception as e:
                    logger.debug(
                        f"Error obteniendo recomendaciones de yfinance: {str(e)}"
                    )

                # Si tenemos datos significativos, guardar en caché y devolver
                if (
                    (data["price_targets"] and len(data["price_targets"]) > 0)
                    or (data["recommendations"] and len(data["recommendations"]) > 1)
                    or len(data["ratings"]) > 0
                ):
                    self._cache_data(cache_key, data)
                    return data

            except Exception as e:
                logger.warning(
                    f"Error obteniendo análisis con yfinance: {str(e)}. Intentando con scraping..."
                )

        # Scraping de Yahoo Finance como alternativa
        try:
            url = f"{self.base_url}/quote/{symbol}/analysis"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.warning(
                    f"Error obteniendo análisis para {symbol}: HTTP {response.status_code}"
                )
                return data

            soup = BeautifulSoup(response.text, "html.parser")

            # Recomendaciones de analistas - actualizado para el nuevo diseño
            try:
                # Buscar sección de recomendaciones con diferentes selectores
                rec_section = None
                for selector in [
                    'section[data-test="analyst-ratings"]',
                    'div[class*="analyst-ratings"]',
                    'div[data-test="rec-rating-container"]',
                    'div[class*="recommend"]',
                ]:
                    rec_section = soup.select_one(selector)
                    if rec_section:
                        break

                if rec_section:
                    # Obtener recomendación promedio
                    avg_rec = None
                    for selector in [
                        'div[class*="recommendation-text"]',
                        'span[class*="rating-text"]',
                        'div[class*="ratings-container"] span',
                    ]:
                        avg_rec = rec_section.select_one(selector)
                        if avg_rec:
                            break

                    if avg_rec:
                        data["recommendations"]["average"] = avg_rec.text.strip()

                    # Obtener distribución de recomendaciones
                    rec_rows = rec_section.select("tr, div[class*='rec-rating-row']")
                    for row in rec_rows:
                        cells = row.select("td, span")
                        if len(cells) >= 2:
                            key = (
                                cells[0]
                                .text.strip()
                                .lower()
                                .replace(" ", "_")
                                .replace(".", "")
                            )
                            value_text = cells[1].text.strip()
                            try:
                                value = int(value_text)
                            except:
                                value = value_text
                            data["recommendations"][key] = value
            except Exception as e:
                logger.debug(
                    f"Error obteniendo recomendaciones para {symbol}: {str(e)}"
                )

            # Objetivos de precio
            try:
                # Buscar sección de objetivos de precio con diferentes selectores
                target_section = None
                for selector in [
                    'section[data-test="price-targets"]',
                    'div[class*="price-targets"]',
                    'div[data-test="price-target-container"]',
                    'div[class*="target"]',
                ]:
                    target_section = soup.select_one(selector)
                    if target_section:
                        break

                if target_section:
                    # Obtener objetivo promedio
                    avg_target = None
                    for selector in [
                        'div[class*="price-text"]',
                        'span[class*="target-price"]',
                        'div[class*="average"] span',
                    ]:
                        avg_target = target_section.select_one(selector)
                        if avg_target:
                            break

                    if avg_target:
                        try:
                            data["price_targets"]["average"] = float(
                                avg_target.text.strip().replace(",", "")
                            )
                        except:
                            data["price_targets"]["average"] = avg_target.text.strip()

                    # Obtener rango de objetivos
                    range_elements = None
                    for selector in [
                        'div[class*="range-text"]',
                        'span[class*="range"]',
                        'div[class*="low-high"] span',
                    ]:
                        range_elements = target_section.select(selector)
                        if range_elements and len(range_elements) >= 2:
                            break

                    if range_elements and len(range_elements) >= 2:
                        try:
                            data["price_targets"]["low"] = float(
                                range_elements[0].text.strip().replace(",", "")
                            )
                            data["price_targets"]["high"] = float(
                                range_elements[1].text.strip().replace(",", "")
                            )
                        except:
                            pass
            except Exception as e:
                logger.debug(
                    f"Error obteniendo objetivos de precio para {symbol}: {str(e)}"
                )

            # Historial de calificaciones
            try:
                # Buscar tabla de historial con diferentes selectores
                ratings_table = None
                for selector in [
                    'table[class*="ratings-history"]',
                    'table[data-test="research-ratings"]',
                    'div[class*="ratings-history"] table',
                ]:
                    ratings_table = soup.select_one(selector)
                    if ratings_table:
                        break

                if ratings_table:
                    rows = ratings_table.select("tr:not(:first-child)")
                    for row in rows:
                        cells = row.select("td")
                        if len(cells) >= 4:
                            rating = {
                                "date": cells[0].text.strip(),
                                "firm": cells[1].text.strip(),
                                "action": cells[2].text.strip(),
                                "rating": cells[3].text.strip(),
                            }

                            # Obtener precio objetivo si está disponible
                            if len(cells) >= 5:
                                try:
                                    rating["price_target"] = float(
                                        cells[4].text.strip().replace(",", "")
                                    )
                                except:
                                    rating["price_target"] = cells[4].text.strip()

                            data["ratings"].append(rating)
            except Exception as e:
                logger.debug(
                    f"Error obteniendo historial de calificaciones para {symbol}: {str(e)}"
                )
        except Exception as e:
            logger.error(f"Error en get_analysis para {symbol}: {str(e)}")

        # Almacenar en caché
        self._cache_data(cache_key, data)
        return data

    def get_options_data(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene datos de opciones para un símbolo

        Args:
            symbol (str): Símbolo del activo

        Returns:
            Dict[str, Any]: Datos de opciones
        """
        cache_key = f"options_{symbol}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        # Intentar primero con yfinance (más confiable)
        if YFINANCE_AVAILABLE:
            try:
                logger.info(f"Obteniendo opciones para {symbol} con yfinance")
                ticker = yf.Ticker(symbol)

                # Obtener fechas de vencimiento disponibles
                expirations = ticker.options

                if expirations:
                    data = {
                        "symbol": symbol,
                        "timestamp": datetime.now().isoformat(),
                        "expiration_dates": expirations,
                        "calls": [],
                        "puts": [],
                    }

                    # Obtener datos de opciones para la fecha más cercana
                    if len(expirations) > 0:
                        nearest_expiry = expirations[0]
                        options_chain = ticker.option_chain(nearest_expiry)

                        # Procesar opciones call
                        if (
                            hasattr(options_chain, "calls")
                            and not options_chain.calls.empty
                        ):
                            for _, row in options_chain.calls.iterrows():
                                option = {
                                    "contract_name": f"{symbol}{nearest_expiry}C{row.get('strike', 0)}",
                                    "strike": row.get("strike"),
                                    "last_price": row.get("lastPrice"),
                                    "bid": row.get("bid"),
                                    "ask": row.get("ask"),
                                    "change": row.get("change"),
                                    "percent_change": row.get("percentChange"),
                                    "volume": row.get("volume"),
                                    "open_interest": row.get("openInterest"),
                                    "implied_volatility": row.get("impliedVolatility"),
                                }
                                data["calls"].append(option)

                        # Procesar opciones put
                        if (
                            hasattr(options_chain, "puts")
                            and not options_chain.puts.empty
                        ):
                            for _, row in options_chain.puts.iterrows():
                                option = {
                                    "contract_name": f"{symbol}{nearest_expiry}P{row.get('strike', 0)}",
                                    "strike": row.get("strike"),
                                    "last_price": row.get("lastPrice"),
                                    "bid": row.get("bid"),
                                    "ask": row.get("ask"),
                                    "change": row.get("change"),
                                    "percent_change": row.get("percentChange"),
                                    "volume": row.get("volume"),
                                    "open_interest": row.get("openInterest"),
                                    "implied_volatility": row.get("impliedVolatility"),
                                }
                                data["puts"].append(option)

                        # Almacenar en caché
                        self._cache_data(cache_key, data)
                        logger.info(f"Opciones obtenidas con yfinance para {symbol}")
                        return data
            except Exception as e:
                logger.warning(
                    f"Error obteniendo opciones con yfinance: {str(e)}. Intentando con scraping..."
                )

        # Si yfinance falla, intentar con scraping
        try:
            url = f"{self.base_url}/quote/{symbol}/options"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.warning(
                    f"Error obteniendo opciones para {symbol}: HTTP {response.status_code}"
                )
                return {"error": f"HTTP {response.status_code}", "symbol": symbol}

            soup = BeautifulSoup(response.text, "html.parser")

            data = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "expiration_dates": [],
                "calls": [],
                "puts": [],
            }

            # Fechas de vencimiento disponibles
            try:
                # Buscar selector de fechas con diferentes selectores
                expiry_select = None
                for selector in [
                    'select[class*="expiration-date"]',
                    'select[data-test="date-picker"]',
                    'div[class*="options-menu"] select',
                ]:
                    expiry_select = soup.select_one(selector)
                    if expiry_select:
                        break

                if expiry_select:
                    options = expiry_select.select("option")
                    for option in options:
                        if "value" in option.attrs:
                            data["expiration_dates"].append(option["value"])
            except Exception as e:
                logger.debug(
                    f"Error obteniendo fechas de vencimiento para {symbol}: {str(e)}"
                )

            # Datos de opciones call
            try:
                # Buscar tabla de opciones call con diferentes selectores
                calls_table = None
                for selector in [
                    'table[class*="calls"]',
                    'section[data-test="options-calls"] table',
                    'div[class*="call-options"] table',
                ]:
                    calls_table = soup.select_one(selector)
                    if calls_table:
                        break

                if calls_table:
                    rows = calls_table.select("tr:not(:first-child)")
                    for row in rows:
                        cells = row.select("td")
                        if len(cells) >= 8:
                            option = {
                                "contract_name": cells[0].text.strip(),
                                "last_price": self._parse_float(cells[1].text.strip()),
                                "bid": self._parse_float(cells[2].text.strip()),
                                "ask": self._parse_float(cells[3].text.strip()),
                                "change": self._parse_float(cells[4].text.strip()),
                                "percent_change": self._parse_float(
                                    cells[5].text.strip().replace("%", "")
                                ),
                                "volume": self._parse_int(cells[6].text.strip()),
                                "open_interest": self._parse_int(cells[7].text.strip()),
                                "implied_volatility": (
                                    self._parse_float(
                                        cells[8].text.strip().replace("%", "")
                                    )
                                    if len(cells) > 8
                                    else None
                                ),
                            }

                            # Extraer strike price del nombre del contrato
                            strike_match = re.search(
                                r"C(\d+\.\d+)", option["contract_name"]
                            )
                            if strike_match:
                                option["strike"] = float(strike_match.group(1))

                            data["calls"].append(option)
            except Exception as e:
                logger.debug(f"Error obteniendo opciones call para {symbol}: {str(e)}")

            # Datos de opciones put
            try:
                # Buscar tabla de opciones put con diferentes selectores
                puts_table = None
                for selector in [
                    'table[class*="puts"]',
                    'section[data-test="options-puts"] table',
                    'div[class*="put-options"] table',
                ]:
                    puts_table = soup.select_one(selector)
                    if puts_table:
                        break

                if puts_table:
                    rows = puts_table.select("tr:not(:first-child)")
                    for row in rows:
                        cells = row.select("td")
                        if len(cells) >= 8:
                            option = {
                                "contract_name": cells[0].text.strip(),
                                "last_price": self._parse_float(cells[1].text.strip()),
                                "bid": self._parse_float(cells[2].text.strip()),
                                "ask": self._parse_float(cells[3].text.strip()),
                                "change": self._parse_float(cells[4].text.strip()),
                                "percent_change": self._parse_float(
                                    cells[5].text.strip().replace("%", "")
                                ),
                                "volume": self._parse_int(cells[6].text.strip()),
                                "open_interest": self._parse_int(cells[7].text.strip()),
                                "implied_volatility": (
                                    self._parse_float(
                                        cells[8].text.strip().replace("%", "")
                                    )
                                    if len(cells) > 8
                                    else None
                                ),
                            }

                            # Extraer strike price del nombre del contrato
                            strike_match = re.search(
                                r"P(\d+\.\d+)", option["contract_name"]
                            )
                            if strike_match:
                                option["strike"] = float(strike_match.group(1))

                            data["puts"].append(option)
            except Exception as e:
                logger.debug(f"Error obteniendo opciones put para {symbol}: {str(e)}")

            # Almacenar en caché
            self._cache_data(cache_key, data)
            return data

        except Exception as e:
            logger.error(f"Error en get_options_data para {symbol}: {str(e)}")
            return {"error": str(e), "symbol": symbol}

    def get_all_data(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene todos los datos disponibles para un símbolo

        Args:
            symbol (str): Símbolo del activo

        Returns:
            Dict[str, Any]: Todos los datos disponibles
        """
        # Añadir pequeño retraso para evitar bloqueos
        time.sleep(random.uniform(0.5, 1.0))

        quote_data = self.get_quote_data(symbol)

        # Si hay error en los datos básicos, no continuar
        if "error" in quote_data:
            return quote_data

        # Añadir pequeño retraso entre solicitudes
        time.sleep(random.uniform(0.5, 1.0))

        news_data = self.get_news(symbol)

        # Añadir pequeño retraso entre solicitudes
        time.sleep(random.uniform(0.5, 1.0))

        analysis_data = self.get_analysis(symbol)

        # Combinar todos los datos
        combined_data = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "quote": quote_data,
            "news": news_data,
            "analysis": analysis_data,
        }

        return combined_data

    def process_news_with_expert(
        self, news_data: List[Dict[str, Any]], symbol: str, company_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        Procesa noticias para mejorar su calidad

        Args:
            news_data (List[Dict[str, Any]]): Lista de noticias a procesar
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa

        Returns:
            List[Dict[str, Any]]: Noticias procesadas
        """
        if not news_data:
            return []

        # Si no tenemos nombre de empresa, intentar obtenerlo
        if not company_name:
            company_name = self._get_company_name(symbol)

        processed_news = []

        for news in news_data:
            # Verificar si la noticia tiene título
            if not news.get("title"):
                continue

            # Verificar si la noticia es relevante para el símbolo
            if not self._is_news_relevant(news, symbol, company_name):
                continue

            # Asegurar que la URL sea válida
            if not news.get("url") or not news["url"].startswith("http"):
                news["url"] = self._generate_fallback_url(
                    symbol, news.get("source", "")
                )

            # Asegurar que la fuente sea válida
            if not news.get("source"):
                news["source"] = "Fuente Financiera"

            # Asegurar que la fecha sea válida
            if not news.get("date"):
                news["date"] = datetime.now().strftime("%Y-%m-%d")
            else:
                # Normalizar formato de fecha si es posible
                news["date"] = self._normalize_date_format(news["date"])

            # Generar una puntuación de relevancia basada en el contenido
            news["relevance_score"] = self._calculate_relevance_score(
                news, symbol, company_name
            )

            # Generar una puntuación de sentimiento
            news["sentiment_score"] = self._analyze_sentiment(news)

            # Generar recomendación de trading basada en la noticia
            news["trading_recommendation"] = self._generate_trading_recommendation(
                news, symbol
            )

            # Añadir a las noticias procesadas
            processed_news.append(news)

        # Ordenar noticias por relevancia y sentimiento
        processed_news.sort(
            key=lambda x: (
                x.get("relevance_score", 0),
                abs(x.get("sentiment_score", 0)),
            ),
            reverse=True,
        )

        return processed_news

    def _is_news_relevant(
        self, news: Dict[str, Any], symbol: str, company_name: str = None
    ) -> bool:
        """
        Determina si una noticia es relevante para un símbolo

        Args:
            news (Dict[str, Any]): Noticia a evaluar
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa

        Returns:
            bool: True si la noticia es relevante, False en caso contrario
        """
        # Verificar si la noticia tiene título o resumen
        if not news.get("title") and not news.get("summary"):
            return False

        # Verificar si el símbolo aparece en el título o resumen
        title = news.get("title", "").lower()
        summary = news.get("summary", "").lower()
        source = news.get("source", "").lower()

        # Si el símbolo aparece exactamente, es relevante
        if (
            f" {symbol.lower()} " in f" {title} "
            or f" {symbol.lower()} " in f" {summary} "
        ):
            return True

        # Si el símbolo aparece al inicio o final, también es relevante
        if (
            title.startswith(symbol.lower())
            or title.endswith(symbol.lower())
            or summary.startswith(symbol.lower())
            or summary.endswith(symbol.lower())
        ):
            return True

        # Verificar si el nombre de la empresa aparece en el título o resumen
        if company_name:
            company_name_lower = company_name.lower()
            company_parts = company_name_lower.split()

            # Verificar nombre completo
            if company_name_lower in title or company_name_lower in summary:
                return True

            # Verificar partes significativas del nombre (ignorar palabras comunes)
            common_words = [
                "inc",
                "corporation",
                "corp",
                "company",
                "co",
                "ltd",
                "limited",
                "llc",
                "holdings",
                "group",
                "the",
                "and",
            ]
            significant_parts = [
                part
                for part in company_parts
                if len(part) > 2 and part not in common_words
            ]

            for part in significant_parts:
                if f" {part} " in f" {title} " or f" {part} " in f" {summary} ":
                    return True

        # Verificar palabras clave financieras de alta relevancia
        high_relevance_keywords = [
            "earnings",
            "revenue",
            "profit",
            "loss",
            "guidance",
            "forecast",
            "upgrade",
            "downgrade",
            "rating",
            "analyst",
            "merger",
            "acquisition",
            "dividend",
            "split",
            "CEO",
            "executive",
            "lawsuit",
            "investigation",
            "patent",
            "FDA",
            "approval",
            "product",
            "launch",
            "quarterly",
            "annual",
            "report",
            "financial",
            "results",
            "performance",
            "stock",
            "shares",
            "market",
            "investor",
            "trading",
            "price target",
            "valuation",
        ]

        # Si la fuente es específica para finanzas, dar más credibilidad
        financial_sources = [
            "yahoo finance",
            "bloomberg",
            "reuters",
            "cnbc",
            "marketwatch",
            "seeking alpha",
            "barrons",
            "financial times",
            "ft.com",
            "wsj",
            "wall street journal",
            "investor's business daily",
            "morningstar",
            "motley fool",
            "zacks",
            "investopedia",
            "finviz",
        ]

        is_financial_source = any(fs in source for fs in financial_sources)

        # Si es una fuente financiera, necesitamos menos palabras clave para considerarla relevante
        keyword_threshold = 1 if is_financial_source else 2
        keyword_count = 0

        for keyword in high_relevance_keywords:
            if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
                keyword_count += 1
                if keyword_count >= keyword_threshold:
                    return True

        # Si es una fuente financiera pero no tiene palabras clave suficientes,
        # verificar si la noticia es reciente (menos de 7 días)
        if is_financial_source and keyword_count > 0:
            try:
                news_date = news.get("date")
                if news_date:
                    news_date = self._normalize_date_format(news_date)
                    news_dt = datetime.strptime(news_date, "%Y-%m-%d")
                    days_old = (datetime.now() - news_dt).days
                    if days_old <= 7:
                        return True
            except Exception:
                pass

        # Por defecto, no considerar relevante a menos que cumpla los criterios
        return False

    def _generate_fallback_url(self, symbol: str, source: str = "") -> str:
        """
        Genera una URL de respaldo basada en la fuente y el símbolo

        Args:
            symbol (str): Símbolo del activo
            source (str): Fuente de la noticia

        Returns:
            str: URL de respaldo
        """
        source_lower = source.lower()

        if "yahoo" in source_lower:
            return f"https://finance.yahoo.com/quote/{symbol}"
        elif "finviz" in source_lower:
            return f"https://finviz.com/quote.ashx?t={symbol}"
        elif "investing" in source_lower:
            return f"https://www.investing.com/search/?q={symbol}"
        elif "bloomberg" in source_lower:
            return f"https://www.bloomberg.com/quote/{symbol}"
        elif "alpha vantage" in source_lower:
            return f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}"
        elif "cnbc" in source_lower:
            return f"https://www.cnbc.com/quotes/{symbol}"
        elif "reuters" in source_lower:
            return f"https://www.reuters.com/companies/{symbol}"
        elif "seeking alpha" in source_lower:
            return f"https://seekingalpha.com/symbol/{symbol}"
        elif "barrons" in source_lower:
            return f"https://www.barrons.com/quote/stock/{symbol}"
        elif "financial times" in source_lower or "ft.com" in source_lower:
            return f"https://markets.ft.com/data/equities/tearsheet/summary?s={symbol}"
        elif "wsj" in source_lower or "wall street journal" in source_lower:
            return f"https://www.wsj.com/market-data/quotes/{symbol}"
        else:
            return f"https://finance.yahoo.com/quote/{symbol}"

    def _parse_float(self, value: str) -> Optional[float]:
        """Convierte un string a float, manejando errores"""
        try:
            # Eliminar comas y otros caracteres no numéricos
            clean_value = value.replace(",", "").replace("N/A", "").strip()
            if not clean_value:
                return None

            # Intentar extraer el número usando regex si hay caracteres extra
            if not clean_value.replace(".", "").replace("-", "").isdigit():
                float_match = re.search(r"(-?\d+\.?\d*)", clean_value)
                if float_match:
                    clean_value = float_match.group(1)

            return float(clean_value)
        except:
            return None

    def _parse_int(self, value: str) -> Optional[int]:
        """Convierte un string a int, manejando errores"""
        try:
            # Eliminar comas y otros caracteres no numéricos
            clean_value = value.replace(",", "").replace("N/A", "").strip()
            if not clean_value:
                return None

            # Intentar extraer el número usando regex si hay caracteres extra
            if not clean_value.replace("-", "").isdigit():
                int_match = re.search(r"(-?\d+)", clean_value)
                if int_match:
                    clean_value = int_match.group(1)

            return int(clean_value)
        except:
            return None

    def _normalize_date_format(self, date_str: str) -> str:
        """
        Normaliza el formato de fecha a YYYY-MM-DD

        Args:
            date_str (str): Fecha en cualquier formato

        Returns:
            str: Fecha normalizada en formato YYYY-MM-DD
        """
        try:
            # Si ya está en formato ISO o similar
            if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
                return date_str

            # Para fechas ISO con timestamp (como las de DuckDuckGo)
            iso_match = re.search(r"(\d{4}-\d{2}-\d{2})T", date_str)
            if iso_match:
                return iso_match.group(1)

            # Intentar varios formatos comunes
            for fmt in [
                "%b %d, %Y",
                "%B %d, %Y",
                "%d %b %Y",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y/%m/%d",
                "%d-%m-%Y",
                "%m-%d-%Y",
                "%b-%d-%y",
            ]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # Manejar fechas relativas
            if "ago" in date_str.lower():
                # Extraer número y unidad de tiempo
                match = re.search(
                    r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago",
                    date_str.lower(),
                )
                if match:
                    num, unit = match.groups()
                    num = int(num)
                    now = datetime.now()

                    if unit == "second" or unit == "minute" or unit == "hour":
                        return now.strftime("%Y-%m-%d")
                    elif unit == "day":
                        dt = now - timedelta(days=num)
                    elif unit == "week":
                        dt = now - timedelta(weeks=num)
                    elif unit == "month":
                        # Aproximación: un mes = 30 días
                        dt = now - timedelta(days=num * 30)
                    elif unit == "year":
                        # Aproximación: un año = 365 días
                        dt = now - timedelta(days=num * 365)
                    else:
                        return now.strftime("%Y-%m-%d")

                    return dt.strftime("%Y-%m-%d")

            # Si no se puede parsear, devolver la fecha actual
            return datetime.now().strftime("%Y-%m-%d")

        except Exception as e:
            logger.debug(f"Error normalizando fecha '{date_str}': {str(e)}")
            return datetime.now().strftime("%Y-%m-%d")

    def _calculate_relevance_score(
        self, news: Dict[str, Any], symbol: str, company_name: str = None
    ) -> float:
        """
        Calcula una puntuación de relevancia para una noticia

        Args:
            news (Dict[str, Any]): Noticia a evaluar
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa

        Returns:
            float: Puntuación de relevancia (0-1)
        """
        score = 0.5  # Puntuación base

        title = news.get("title", "").lower()
        summary = news.get("summary", "").lower()
        source = news.get("source", "").lower()

        # Verificar si el símbolo aparece en el título (mayor relevancia)
        if symbol.lower() in title:
            score += 0.3
        elif symbol.lower() in summary:
            score += 0.1

        # Verificar si el nombre de la empresa aparece en el título
        if company_name and company_name.lower() in title:
            score += 0.2
        elif company_name and company_name.lower() in summary:
            score += 0.1

        # Verificar palabras clave de alta relevancia
        high_relevance_keywords = [
            "earnings",
            "revenue",
            "profit",
            "loss",
            "guidance",
            "forecast",
            "upgrade",
            "downgrade",
            "rating",
            "analyst",
            "merger",
            "acquisition",
            "dividend",
            "split",
            "CEO",
            "executive",
            "lawsuit",
            "investigation",
            "patent",
            "FDA",
            "approval",
            "product",
            "launch",
        ]

        for keyword in high_relevance_keywords:
            if keyword in title:
                score += 0.15
                break  # Solo sumar una vez por título

        for keyword in high_relevance_keywords:
            if keyword in summary:
                score += 0.05
                break  # Solo sumar una vez por resumen

        # Verificar fuentes de alta credibilidad
        credible_sources = [
            "bloomberg",
            "reuters",
            "wall street journal",
            "wsj",
            "financial times",
            "ft",
            "cnbc",
            "finviz",
            "seeking alpha",
            "yahoo finance",
            "barrons",
            "alpha vantage",
            "investing.com",
        ]

        for cs in credible_sources:
            if cs in source:
                score += 0.1
                break  # Solo sumar una vez

        # Limitar la puntuación entre 0 y 1
        return min(max(score, 0), 1)

    def _analyze_sentiment(self, news: Dict[str, Any]) -> float:
        """
        Analiza el sentimiento de una noticia

        Args:
            news (Dict[str, Any]): Noticia a analizar

        Returns:
            float: Puntuación de sentimiento (-1 a 1, donde -1 es muy negativo, 0 es neutral, 1 es muy positivo)
        """
        # Si ya tiene puntuación de sentimiento, usarla
        if "sentiment" in news and isinstance(news["sentiment"], (int, float)):
            sentiment = float(news["sentiment"])
            # Normalizar entre -1 y 1 si es necesario
            if 0 <= sentiment <= 1:
                return (sentiment * 2) - 1
            return max(min(sentiment, 1), -1)

        title = news.get("title", "").lower()
        summary = news.get("summary", "").lower()

        # Palabras positivas y negativas
        positive_words = [
            "up",
            "rise",
            "gain",
            "profit",
            "growth",
            "positive",
            "beat",
            "exceed",
            "outperform",
            "upgrade",
            "buy",
            "strong",
            "success",
            "improve",
            "higher",
            "bullish",
            "opportunity",
            "innovation",
            "launch",
            "approval",
            "partnership",
            "collaboration",
            "dividend",
            "increase",
        ]

        negative_words = [
            "down",
            "fall",
            "drop",
            "loss",
            "decline",
            "negative",
            "miss",
            "below",
            "underperform",
            "downgrade",
            "sell",
            "weak",
            "failure",
            "worsen",
            "lower",
            "bearish",
            "risk",
            "threat",
            "lawsuit",
            "investigation",
            "recall",
            "delay",
            "cut",
            "decrease",
            "layoff",
            "restructuring",
        ]

        # Contar palabras positivas y negativas
        positive_count = 0
        for word in positive_words:
            if f" {word} " in f" {title} " or f" {word} " in f" {summary} ":
                positive_count += 1

        negative_count = 0
        for word in negative_words:
            if f" {word} " in f" {title} " or f" {word} " in f" {summary} ":
                negative_count += 1

        # Calcular puntuación de sentimiento
        if positive_count == 0 and negative_count == 0:
            return 0  # Neutral

        total_count = positive_count + negative_count
        sentiment_score = (positive_count - negative_count) / total_count

        return sentiment_score

    def _generate_trading_recommendation(
        self, news: Dict[str, Any], symbol: str
    ) -> Dict[str, Any]:
        """
        Genera una recomendación de trading basada en la noticia

        Args:
            news (Dict[str, Any]): Noticia analizada
            symbol (str): Símbolo del activo

        Returns:
            Dict[str, Any]: Recomendación de trading
        """
        # Obtener puntuación de sentimiento
        sentiment_score = news.get("sentiment_score", 0)

        # Determinar dirección (compra/venta)
        if sentiment_score >= 0.7:
            direction = "COMPRA FUERTE"
            confidence = "alta"
            options_strategy = "CALL"
        elif sentiment_score >= 0.3:
            direction = "COMPRA"
            confidence = "media"
            options_strategy = "CALL"
        elif sentiment_score <= -0.7:
            direction = "VENTA FUERTE"
            confidence = "alta"
            options_strategy = "PUT"
        elif sentiment_score <= -0.3:
            direction = "VENTA"
            confidence = "media"
            options_strategy = "PUT"
        else:
            direction = "NEUTRAL"
            confidence = "baja"
            options_strategy = "NEUTRAL"

        # Generar recomendación
        recommendation = {
            "direction": direction,
            "confidence": confidence,
            "options_strategy": options_strategy,
            "based_on": "análisis de noticias",
            "sentiment_score": sentiment_score,
            "explanation": self._generate_recommendation_explanation(
                news, direction, sentiment_score
            ),
        }

        return recommendation

    def _generate_recommendation_explanation(
        self, news: Dict[str, Any], direction: str, sentiment_score: float
    ) -> str:
        """
        Genera una explicación para la recomendación de trading

        Args:
            news (Dict[str, Any]): Noticia analizada
            direction (str): Dirección de la recomendación
            sentiment_score (float): Puntuación de sentimiento

        Returns:
            str: Explicación de la recomendación
        """
        title = news.get("title", "")
        source = news.get("source", "")

        if direction == "COMPRA FUERTE":
            return f"Noticia muy positiva de {source}: '{title}'. El sentimiento es fuertemente alcista (puntuación: {sentiment_score:.2f})."
        elif direction == "COMPRA":
            return f"Noticia positiva de {source}: '{title}'. El sentimiento es moderadamente alcista (puntuación: {sentiment_score:.2f})."
        elif direction == "VENTA FUERTE":
            return f"Noticia muy negativa de {source}: '{title}'. El sentimiento es fuertemente bajista (puntuación: {sentiment_score:.2f})."
        elif direction == "VENTA":
            return f"Noticia negativa de {source}: '{title}'. El sentimiento es moderadamente bajista (puntuación: {sentiment_score:.2f})."
        else:
            return f"Noticia de {source}: '{title}'. El sentimiento es neutral (puntuación: {sentiment_score:.2f})."

    def _get_company_name(self, symbol: str) -> str:
        """
        Obtiene el nombre de la empresa a partir del símbolo

        Args:
            symbol (str): Símbolo del activo

        Returns:
            str: Nombre de la empresa
        """
        # Intentar obtener de yfinance (más confiable)
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if info:
                    return info.get("shortName", info.get("longName", symbol))
            except Exception as e:
                logger.debug(
                    f"Error obteniendo nombre de empresa con yfinance: {str(e)}"
                )

        # Intentar obtener de la API de Yahoo Finance
        try:
            api_url = (
                f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
            )
            response = requests.get(api_url, headers=self.headers, timeout=5)

            if response.status_code == 200:
                json_data = response.json()
                quote_data = json_data.get("quoteResponse", {}).get("result", [])

                if quote_data and len(quote_data) > 0:
                    result = quote_data[0]
                    name = result.get("shortName", result.get("longName", symbol))
                    if name and name != symbol:
                        return name
        except Exception as e:
            logger.debug(f"Error obteniendo nombre de empresa con la API: {str(e)}")

        # Intentar obtener de scraping
        try:
            url = f"{self.base_url}/quote/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=5)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Buscar el nombre con varios selectores posibles
                name_elem = None
                for selector in ["h1", 'div[class*="title"]', 'div[class*="D(ib)"] h1']:
                    name_elem = soup.select_one(selector)
                    if name_elem:
                        break

                if name_elem:
                    return name_elem.text.strip()
        except Exception as e:
            logger.debug(f"Error obteniendo nombre de empresa con scraping: {str(e)}")

        # Devolver el símbolo como fallback
        return symbol


# Script de prueba
if __name__ == "__main__":
    # Intentar cargar claves API desde secrets.toml
    try:
        import toml
        import os

        # Buscar el archivo secrets.toml en diferentes ubicaciones
        secrets_paths = [
            "./.streamlit/secrets.toml",
            "../.streamlit/secrets.toml",
            os.path.expanduser("~/.streamlit/secrets.toml"),
        ]

        secrets = None
        for path in secrets_paths:
            if os.path.exists(path):
                with open(path, "r") as f:
                    secrets = toml.load(f)
                print(f"Cargando secrets desde: {path}")
                break

        if secrets:
            # Configurar keys de API desde secrets.toml
            api_keys = {}

            # Intentar obtener de la sección api_keys
            if "api_keys" in secrets:
                if "ALPHA_VANTAGE_API_KEY" in secrets["api_keys"]:
                    api_keys["alpha_vantage"] = secrets["api_keys"][
                        "ALPHA_VANTAGE_API_KEY"
                    ]
                if "FINNHUB_API_KEY" in secrets["api_keys"]:
                    api_keys["finnhub"] = secrets["api_keys"]["FINNHUB_API_KEY"]

            # Intentar obtener de la raíz
            if "alpha_vantage_api_key" in secrets:
                api_keys["alpha_vantage"] = secrets["alpha_vantage_api_key"]
            if "finnhub_api_key" in secrets:
                api_keys["finnhub"] = secrets["finnhub_api_key"]

            print(f"API keys cargadas: {', '.join(api_keys.keys())}")
        else:
            print("No se encontró el archivo secrets.toml")
            # Usar valores por defecto
            api_keys = {
                "alpha_vantage": "E93GT2T7VWQJIVY1",  # Clave de ejemplo
                "finnhub": "cuv6cbhr01qpi6rtjdvgcuv6cbhr01qpi6rtje00",  # Clave de ejemplo
            }
    except Exception as e:
        print(f"Error cargando secrets: {str(e)}")
        # Usar valores por defecto
        api_keys = {
            "alpha_vantage": "E93GT2T7VWQJIVY1",  # Clave de ejemplo
            "finnhub": "cuv6cbhr01qpi6rtjdvgcuv6cbhr01qpi6rtje00",  # Clave de ejemplo
        }

    # Crear instancia del scraper
    scraper = YahooFinanceScraper(api_keys)

    # Símbolo a analizar
    symbol = "MSFT"
    print(f"\nObteniendo datos para {symbol}...\n")

    # Obtener datos básicos
    quote_data = scraper.get_quote_data(symbol)

    # Imprimir información básica
    print(f"Datos para {symbol}:")
    if "price" in quote_data and quote_data["price"].get("current"):
        print(f"Precio actual: ${quote_data['price'].get('current')}")
        if quote_data["price"].get("change") and quote_data["price"].get(
            "change_percent"
        ):
            print(
                f"Cambio: {quote_data['price'].get('change')} ({quote_data['price'].get('change_percent')}%)"
            )
    else:
        print("Precio actual: No disponible")

    # Obtener nombre de la empresa
    company_name = scraper._get_company_name(symbol)
    print(f"Nombre de la empresa: {company_name}")

    # Prueba de obtención de noticias
    print("\n=== PRUEBA DE FUENTES DE NOTICIAS ===")

    # Obtener noticias
    news_data = scraper.get_news(symbol, max_news=3)

    if news_data:
        print(f"\nSe obtuvieron {len(news_data)} noticias")
        for i, news in enumerate(news_data, 1):
            print(f"{i}. {news.get('title', 'Sin título')}")
            print(
                f"   Fuente: {news.get('source', 'N/A')} - Fecha: {news.get('date', 'N/A')}"
            )
            print(f"   URL: {news.get('url', 'N/A')}")
            print(f"   Método: {news.get('_source_method', 'Desconocido')}")
    else:
        print("\nNo se obtuvieron noticias")

    # Prueba de procesamiento de noticias
    print("\n=== PROCESAMIENTO DE NOTICIAS ===")

    if news_data:
        processed_news = scraper.process_news_with_expert(
            news_data, symbol, company_name
        )
        print(f"Se procesaron {len(processed_news)} noticias")
        for i, news in enumerate(processed_news, 1):
            print(f"{i}. {news.get('title', 'Sin título')}")
            print(
                f"   Fuente: {news.get('source', 'N/A')} - Fecha: {news.get('date', 'N/A')}"
            )
            print(
                f"   Relevancia: {news.get('relevance_score', 0):.2f} - Sentimiento: {news.get('sentiment_score', 0):.2f}"
            )
            if "trading_recommendation" in news:
                rec = news["trading_recommendation"]
                print(
                    f"   Recomendación: {rec.get('direction', 'N/A')} (Confianza: {rec.get('confidence', 'N/A')})"
                )
    else:
        print("No hay noticias para procesar")

    # Prueba de análisis
    print("\n=== ANÁLISIS Y RECOMENDACIONES ===")

    analysis_data = scraper.get_analysis(symbol)

    # Mostrar recomendaciones
    print("Recomendaciones de analistas:")
    if "recommendations" in analysis_data and analysis_data["recommendations"]:
        print(f"Promedio: {analysis_data['recommendations'].get('average', 'N/A')}")
        # Mostrar distribución si está disponible
        for key, value in analysis_data["recommendations"].items():
            if key != "average":
                print(f"  {key}: {value}")
    else:
        print("No hay recomendaciones disponibles")

    # Mostrar objetivos de precio
    print("\nObjetivos de precio:")
    if "price_targets" in analysis_data and analysis_data["price_targets"]:
        print(f"Promedio: ${analysis_data['price_targets'].get('average', 'N/A')}")
        if (
            "low" in analysis_data["price_targets"]
            and "high" in analysis_data["price_targets"]
        ):
            print(
                f"Rango: ${analysis_data['price_targets'].get('low', 'N/A')} - ${analysis_data['price_targets'].get('high', 'N/A')}"
            )
    else:
        print("No hay objetivos de precio disponibles")

    # Mostrar historial de calificaciones
    if "ratings" in analysis_data and analysis_data["ratings"]:
        print("\nÚltimas calificaciones de analistas:")
        for i, rating in enumerate(
            analysis_data["ratings"][:3], 1
        ):  # Mostrar las primeras 3
            print(f"{i}. Fecha: {rating.get('date', 'N/A')}")
            print(f"   Firma: {rating.get('firm', 'N/A')}")
            print(f"   Acción: {rating.get('action', 'N/A')}")
            print(f"   Calificación: {rating.get('rating', 'N/A')}")
            if "price_target" in rating:
                print(f"   Objetivo de precio: ${rating['price_target']}")
