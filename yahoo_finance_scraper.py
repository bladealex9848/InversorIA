#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yahoo Finance Scraper - Módulo para obtener datos y noticias de Yahoo Finance
Versión mejorada con múltiples fuentes y fallbacks
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

# Intentar importar yfinance
YFINANCE_AVAILABLE = False
try:
    import yfinance as yf

    YFINANCE_AVAILABLE = True
    logger.info("yfinance disponible para uso")
except ImportError:
    logger.warning("yfinance no está disponible. Se usarán métodos alternativos.")

# Intentar importar duckduckgo_search
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
    """Clase para obtener datos y noticias de Yahoo Finance con múltiples fuentes"""

    def __init__(self):
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

            # Precio actual
            try:
                price_elem = soup.select_one('[data-test="qsp-price"]')
                if price_elem:
                    data["price"]["current"] = float(price_elem.text.replace(",", ""))

                # Cambio y porcentaje de cambio
                change_elems = soup.select('[data-test="qsp-price-change"]')
                if len(change_elems) >= 2:
                    data["price"]["change"] = float(
                        change_elems[0].text.replace(",", "")
                    )
                    # Extraer solo el número del porcentaje (quitar paréntesis y %)
                    percent_text = change_elems[1].text.strip("()%")
                    data["price"]["change_percent"] = float(percent_text)
            except Exception as e:
                logger.debug(f"Error obteniendo precio para {symbol}: {str(e)}")

            # Nombre de la empresa
            try:
                name_elem = soup.select_one("h1")
                if name_elem:
                    data["company_info"]["name"] = name_elem.text.strip()
            except Exception as e:
                logger.debug(f"Error obteniendo nombre para {symbol}: {str(e)}")

            # Estadísticas clave (volumen, rango, etc.)
            try:
                stat_rows = soup.select('table[data-test="qsp-statistics"] tr')
                for row in stat_rows:
                    cells = row.select("td")
                    if len(cells) >= 2:
                        key = cells[0].text.strip().lower().replace(" ", "_")
                        value = cells[1].text.strip()
                        data["stats"][key] = value
            except Exception as e:
                logger.debug(f"Error obteniendo estadísticas para {symbol}: {str(e)}")

            # Almacenar en caché
            self._cache_data(cache_key, data)

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

        # Intentar primero con yfinance si está disponible
        if YFINANCE_AVAILABLE:
            try:
                logger.info(f"Obteniendo noticias de {symbol} con yfinance")
                ticker = yf.Ticker(symbol)
                news_data = ticker.news

                if news_data and isinstance(news_data, list) and len(news_data) > 0:
                    news = []
                    for item in news_data[:max_news]:  # Limitar a max_news noticias
                        # Verificar que el item sea un diccionario válido
                        if not isinstance(item, dict):
                            continue

                        # Verificar que tenga al menos título
                        if not item.get("title"):
                            continue

                        # Crear objeto de noticia con valores por defecto para campos faltantes
                        news_item = {
                            "title": item.get("title", "Sin título"),
                            "summary": item.get("summary", ""),
                            "url": item.get("link", ""),
                            "source": item.get("publisher", "Yahoo Finance"),
                            "date": datetime.now().strftime("%Y-%m-%d"),
                        }

                        # Intentar obtener la fecha de publicación si está disponible
                        if item.get("providerPublishTime") and isinstance(
                            item.get("providerPublishTime"), (int, float)
                        ):
                            try:
                                news_item["date"] = datetime.fromtimestamp(
                                    item.get("providerPublishTime")
                                ).strftime("%Y-%m-%d")
                            except:
                                pass  # Mantener la fecha por defecto

                        news.append(news_item)

                    # Registrar la fuente de las noticias
                    for item in news:
                        item["_source_method"] = "yfinance"

                    # Almacenar en caché
                    self._cache_data(cache_key, news)
                    logger.info(
                        f"Noticias de yfinance obtenidas correctamente para {symbol}"
                    )
                    return news
            except Exception as e:
                logger.warning(
                    f"Error obteniendo noticias con yfinance: {str(e)}. Intentando con scraping..."
                )

        # Intentar con scraping de Yahoo Finance
        try:
            logger.info(f"Obteniendo noticias de {symbol} con web scraping")
            url = f"{self.base_url}/quote/{symbol}/news"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.warning(
                    f"Error obteniendo noticias para {symbol}: HTTP {response.status_code}"
                )
                # No retornar aquí, intentar con DuckDuckGo si está disponible
            else:
                soup = BeautifulSoup(response.text, "html.parser")

                # Buscar elementos de noticias
                news_items = soup.select('div[data-test="story"]')

                if not news_items:
                    # Intentar con otro selector si el primero falla
                    news_items = soup.select('li[class*="js-stream-content"]')

                if news_items:
                    news = []
                    for item in news_items[:max_news]:
                        # Extraer título
                        title_element = item.select_one('h3, a[class*="headline"]')
                        title = (
                            title_element.text.strip()
                            if title_element
                            else "Sin título"
                        )

                        # Extraer enlace
                        link_element = item.select_one("a[href]")
                        url = (
                            link_element["href"]
                            if link_element and "href" in link_element.attrs
                            else "#"
                        )

                        # Convertir enlaces relativos a absolutos
                        if url.startswith("/"):
                            url = f"{self.base_url}{url}"

                        # Extraer descripción/resumen
                        summary_element = item.select_one('p, div[class*="summary"]')
                        summary = (
                            summary_element.text.strip() if summary_element else ""
                        )

                        # Extraer fuente y fecha
                        source_element = item.select_one(
                            'div[class*="author"], span[class*="provider-name"]'
                        )
                        source = (
                            source_element.text.strip()
                            if source_element
                            else "Yahoo Finance"
                        )

                        date_element = item.select_one(
                            'div[class*="date"], span[class*="date"]'
                        )
                        date_str = date_element.text.strip() if date_element else ""

                        # Convertir fecha relativa a absoluta si es posible
                        try:
                            if "ago" in date_str.lower():
                                # Fecha aproximada basada en texto relativo
                                date = datetime.now().strftime("%Y-%m-%d")
                            else:
                                # Intentar parsear la fecha
                                date = datetime.strptime(
                                    date_str, "%b %d, %Y"
                                ).strftime("%Y-%m-%d")
                        except:
                            date = datetime.now().strftime("%Y-%m-%d")

                        news.append(
                            {
                                "title": title,
                                "summary": summary,
                                "url": url,
                                "source": source,
                                "date": date,
                            }
                        )

                    # Registrar la fuente de las noticias
                    for item in news:
                        item["_source_method"] = "yahoo_scraping"

                    # Almacenar en caché
                    self._cache_data(cache_key, news)
                    logger.info(
                        f"Noticias de scraping obtenidas correctamente para {symbol}"
                    )
                    return news
        except Exception as e:
            logger.error(f"Error en scraping de noticias para {symbol}: {str(e)}")

        # Intentar con DuckDuckGo si está disponible
        if DDG_AVAILABLE and self.ddgs:
            try:
                logger.info(f"Obteniendo noticias de {symbol} con DuckDuckGo")
                # Obtener nombre de la empresa para mejorar la búsqueda
                company_name = self._get_company_name(symbol)
                query = f"{company_name} {symbol} stock news"

                # Realizar búsqueda de noticias
                results = self.ddgs.news(query, max_results=max_news)

                if results:
                    news = []
                    for item in results:
                        news.append(
                            {
                                "title": item.get("title", ""),
                                "summary": item.get("body", ""),
                                "url": item.get("url", ""),
                                "source": item.get("source", ""),
                                "date": item.get(
                                    "date", datetime.now().strftime("%Y-%m-%d")
                                ),
                            }
                        )

                    # Registrar la fuente de las noticias
                    for item in news:
                        item["_source_method"] = "duckduckgo"

                    # Almacenar en caché
                    self._cache_data(cache_key, news)
                    logger.info(
                        f"Noticias de DuckDuckGo obtenidas correctamente para {symbol}"
                    )
                    return news
            except Exception as e:
                logger.error(f"Error en búsqueda de noticias con DuckDuckGo: {str(e)}")

        # Intentar con Google Finance como alternativa
        try:
            logger.info(f"Obteniendo noticias de {symbol} con Google Finance")
            google_news = self._get_news_from_google_finance(symbol, max_news)
            if google_news:
                # Registrar la fuente de las noticias
                for item in google_news:
                    item["_source_method"] = "google_finance"

                # Almacenar en caché
                self._cache_data(cache_key, google_news)
                logger.info(
                    f"Noticias de Google Finance obtenidas correctamente para {symbol}"
                )
                return google_news
        except Exception as e:
            logger.error(f"Error en búsqueda de noticias con Google Finance: {str(e)}")

        # Intentar con MarketWatch como última alternativa
        try:
            logger.info(f"Obteniendo noticias de {symbol} con MarketWatch")
            mw_news = self._get_news_from_marketwatch(symbol, max_news)
            if mw_news:
                # Registrar la fuente de las noticias
                for item in mw_news:
                    item["_source_method"] = "marketwatch"

                # Almacenar en caché
                self._cache_data(cache_key, mw_news)
                logger.info(
                    f"Noticias de MarketWatch obtenidas correctamente para {symbol}"
                )
                return mw_news
        except Exception as e:
            logger.error(f"Error en búsqueda de noticias con MarketWatch: {str(e)}")

        # Si todo falla, devolver lista vacía
        logger.warning(
            f"No se pudieron obtener noticias para {symbol} de ninguna fuente"
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

        try:
            url = f"{self.base_url}/quote/{symbol}/analysis"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.warning(
                    f"Error obteniendo análisis para {symbol}: HTTP {response.status_code}"
                )
                return {"error": f"HTTP {response.status_code}", "symbol": symbol}

            soup = BeautifulSoup(response.text, "html.parser")

            data = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "recommendations": {},
                "price_targets": {},
                "ratings": [],
            }

            # Recomendaciones de analistas
            try:
                rec_section = soup.select_one('section[data-test="analyst-ratings"]')
                if rec_section:
                    # Obtener recomendación promedio
                    avg_rec = rec_section.select_one(
                        'div[class*="recommendation-text"]'
                    )
                    if avg_rec:
                        data["recommendations"]["average"] = avg_rec.text.strip()

                    # Obtener distribución de recomendaciones
                    rec_rows = rec_section.select("tr")
                    for row in rec_rows:
                        cells = row.select("td")
                        if len(cells) >= 2:
                            key = cells[0].text.strip().lower().replace(" ", "_")
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
                target_section = soup.select_one('section[data-test="price-targets"]')
                if target_section:
                    # Obtener objetivo promedio
                    avg_target = target_section.select_one('div[class*="price-text"]')
                    if avg_target:
                        try:
                            data["price_targets"]["average"] = float(
                                avg_target.text.strip().replace(",", "")
                            )
                        except:
                            data["price_targets"]["average"] = avg_target.text.strip()

                    # Obtener rango de objetivos
                    range_elements = target_section.select('div[class*="range-text"]')
                    if len(range_elements) >= 2:
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
                ratings_table = soup.select_one('table[class*="ratings-history"]')
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

            # Almacenar en caché
            self._cache_data(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Error en get_analysis para {symbol}: {str(e)}")
            return {"error": str(e), "symbol": symbol}

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
                expiry_select = soup.select_one('select[class*="expiration-date"]')
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
                calls_table = soup.select_one('table[class*="calls"]')
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
                puts_table = soup.select_one('table[class*="puts"]')
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
        time.sleep(random.uniform(0.5, 1.5))

        quote_data = self.get_quote_data(symbol)

        # Si hay error en los datos básicos, no continuar
        if "error" in quote_data:
            return quote_data

        # Añadir pequeño retraso entre solicitudes
        time.sleep(random.uniform(0.5, 1.5))

        news_data = self.get_news(symbol)

        # Añadir pequeño retraso entre solicitudes
        time.sleep(random.uniform(0.5, 1.5))

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
        Procesa noticias con el experto en IA para mejorar su calidad

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
        elif "google" in source_lower:
            return f"https://www.google.com/finance/quote/{symbol}"
        elif "marketwatch" in source_lower:
            return f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"
        elif "bloomberg" in source_lower:
            return f"https://www.bloomberg.com/quote/{symbol}"
        elif "cnbc" in source_lower:
            return f"https://www.cnbc.com/quotes/{symbol}"
        elif "reuters" in source_lower:
            return f"https://www.reuters.com/companies/{symbol}"
        elif "investing.com" in source_lower:
            return f"https://www.investing.com/search/?q={symbol}"
        elif "seeking alpha" in source_lower:
            return f"https://seekingalpha.com/symbol/{symbol}"
        elif "barrons" in source_lower:
            return f"https://www.barrons.com/quote/stock/{symbol}"
        elif "financial times" in source_lower or "ft.com" in source_lower:
            return f"https://markets.ft.com/data/equities/tearsheet/summary?s={symbol}"
        elif "wsj" in source_lower or "wall street journal" in source_lower:
            return f"https://www.wsj.com/market-data/quotes/{symbol}"
        else:
            return f"https://www.google.com/finance/quote/{symbol}"

    def _parse_float(self, value: str) -> Optional[float]:
        """Convierte un string a float, manejando errores"""
        try:
            # Eliminar comas y otros caracteres no numéricos
            clean_value = value.replace(",", "").replace("N/A", "").strip()
            if not clean_value:
                return None
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
            # Si ya está en formato ISO
            if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
                return date_str

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
            "marketwatch",
            "seeking alpha",
            "yahoo finance",
            "barrons",
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

    def _get_news_from_google_finance(
        self, symbol: str, max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene noticias de un símbolo utilizando Google Finance

        Args:
            symbol (str): Símbolo del activo
            max_news (int): Número máximo de noticias a obtener

        Returns:
            List[Dict[str, Any]]: Lista de noticias
        """
        try:
            # Intentar primero con NASDAQ
            url = f"https://www.google.com/finance/quote/{symbol}:NASDAQ"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                # Intentar con NYSE
                url = f"https://www.google.com/finance/quote/{symbol}:NYSE"
                response = requests.get(url, headers=self.headers, timeout=10)

                if response.status_code != 200:
                    # Intentar sin especificar el mercado
                    url = f"https://www.google.com/finance/quote/{symbol}"
                    response = requests.get(url, headers=self.headers, timeout=10)

                    if response.status_code != 200:
                        logger.warning(
                            f"Error obteniendo datos de Google Finance para {symbol}: HTTP {response.status_code}"
                        )
                        return []

            soup = BeautifulSoup(response.text, "html.parser")

            # Buscar sección de noticias
            news_section = soup.select('div[role="feed"]')
            if not news_section:
                return []

            news_items = news_section[0].select('div[role="article"]')

            news = []
            for item in news_items[:max_news]:  # Limitar a max_news noticias
                # Extraer título
                title_element = item.select_one('div[role="heading"]')
                title = title_element.text.strip() if title_element else "Sin título"

                # Extraer enlace
                link_element = item.select_one("a[href]")
                url = (
                    link_element["href"]
                    if link_element and "href" in link_element.attrs
                    else "#"
                )

                # Convertir enlaces relativos a absolutos
                if url.startswith("/"):
                    url = f"https://www.google.com{url}"

                # Extraer fuente y fecha
                source_element = item.select_one("div:nth-child(2) > div:nth-child(1)")
                source = (
                    source_element.text.strip() if source_element else "Google Finance"
                )

                # Intentar extraer fecha
                date_element = item.select_one("div:nth-child(2) > div:nth-child(2)")
                date = datetime.now().strftime("%Y-%m-%d")  # Fecha por defecto

                # Si hay fecha en el elemento, intentar procesarla
                if date_element:
                    # Aquí se podría implementar un parser de fechas relativas
                    # Por ahora usamos la fecha actual
                    pass

                # Extraer resumen si está disponible
                summary_element = item.select_one('div[role="heading"] + div')
                summary = summary_element.text.strip() if summary_element else ""

                news.append(
                    {
                        "title": title,
                        "summary": summary,
                        "url": url,
                        "source": source,
                        "date": date,
                    }
                )

            return news

        except Exception as e:
            logger.error(
                f"Error en _get_news_from_google_finance para {symbol}: {str(e)}"
            )
            return []

    def _get_news_from_marketwatch(
        self, symbol: str, max_news: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene noticias de un símbolo utilizando MarketWatch

        Args:
            symbol (str): Símbolo del activo
            max_news (int): Número máximo de noticias a obtener

        Returns:
            List[Dict[str, Any]]: Lista de noticias
        """
        try:
            url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.warning(
                    f"Error obteniendo datos de MarketWatch para {symbol}: HTTP {response.status_code}"
                )
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # Buscar sección de noticias
            news_section = soup.select(".collection__elements")
            if not news_section:
                # Intentar con otro selector
                news_section = soup.select(".article__content")
                if not news_section:
                    return []

            # Buscar elementos de noticias
            news_items = []
            for section in news_section:
                items = section.select(".element--article, .article__headline")
                if items:
                    news_items.extend(items)

            if not news_items:
                return []

            news = []
            for item in news_items[:max_news]:  # Limitar a max_news noticias
                # Extraer título y enlace
                title_element = item.select_one("a.link, h3.article__headline a")
                if not title_element:
                    continue

                title = title_element.text.strip()
                url = title_element["href"] if "href" in title_element.attrs else "#"

                # Convertir enlaces relativos a absolutos
                if url.startswith("/"):
                    url = f"https://www.marketwatch.com{url}"

                # Extraer resumen si está disponible
                summary_element = item.select_one(".article__summary")
                summary = summary_element.text.strip() if summary_element else ""

                # Extraer fuente y fecha
                source = "MarketWatch"
                date = datetime.now().strftime("%Y-%m-%d")

                # Intentar extraer fecha si está disponible
                date_element = item.select_one(".article__timestamp")
                if date_element:
                    date_str = date_element.text.strip()
                    try:
                        # Intentar parsear la fecha
                        if "ago" not in date_str.lower():
                            parsed_date = datetime.strptime(date_str, "%b. %d, %Y")
                            date = parsed_date.strftime("%Y-%m-%d")
                    except:
                        pass

                news.append(
                    {
                        "title": title,
                        "summary": summary,
                        "url": url,
                        "source": source,
                        "date": date,
                    }
                )

            return news

        except Exception as e:
            logger.error(f"Error en _get_news_from_marketwatch para {symbol}: {str(e)}")
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
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return info.get("shortName", info.get("longName", symbol))
            except Exception as e:
                logger.debug(
                    f"Error obteniendo nombre de empresa con yfinance: {str(e)}"
                )

        # Intentar obtener de scraping
        try:
            url = f"{self.base_url}/quote/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=5)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                name_elem = soup.select_one("h1")
                if name_elem:
                    return name_elem.text.strip()
        except Exception as e:
            logger.debug(f"Error obteniendo nombre de empresa con scraping: {str(e)}")

        # Devolver el símbolo como fallback
        return symbol


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging para ver mensajes en consola
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    scraper = YahooFinanceScraper()

    # Obtener datos para Microsoft
    symbol = "MSFT"
    print(f"\nObteniendo datos para {symbol}...\n")

    # Obtener datos básicos
    quote_data = scraper.get_quote_data(symbol)

    # Imprimir información básica
    print(f"Datos para {symbol}:")
    if quote_data["price"].get("current"):
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

    # Probar todas las fuentes de noticias
    print("\n=== PRUEBA DE TODAS LAS FUENTES DE NOTICIAS ===")

    # 1. Probar yfinance
    if YFINANCE_AVAILABLE:
        print("\n1. Obteniendo noticias con yfinance:")
        try:
            ticker = yf.Ticker(symbol)
            news_data = ticker.news

            if news_data:
                news = []
                for item in news_data[:3]:  # Limitar a 3 noticias
                    news_item = {
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "url": item.get("link", ""),
                        "source": item.get("publisher", "Yahoo Finance"),
                        "date": datetime.fromtimestamp(
                            item.get("providerPublishTime", 0)
                        ).strftime("%Y-%m-%d"),
                    }
                    news.append(news_item)
                    print(f"- {news_item['title']}")
                    print(
                        f"  Fuente: {news_item['source']} - Fecha: {news_item['date']}"
                    )
                    print(f"  URL: {news_item['url']}")
            else:
                print("No se encontraron noticias con yfinance")
        except Exception as e:
            print(f"Error obteniendo noticias con yfinance: {str(e)}")
    else:
        print("yfinance no está disponible")

    # 2. Probar scraping de Yahoo Finance
    print("\n2. Obteniendo noticias con scraping de Yahoo Finance:")
    try:
        url = f"{scraper.base_url}/quote/{symbol}/news"
        response = requests.get(url, headers=scraper.headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            news_items = soup.select('div[data-test="story"]')

            if not news_items:
                news_items = soup.select('li[class*="js-stream-content"]')

            if news_items:
                for i, item in enumerate(news_items[:3]):
                    title_element = item.select_one('h3, a[class*="headline"]')
                    title = (
                        title_element.text.strip() if title_element else "Sin título"
                    )

                    link_element = item.select_one("a[href]")
                    url = (
                        link_element["href"]
                        if link_element and "href" in link_element.attrs
                        else "#"
                    )
                    if url.startswith("/"):
                        url = f"{scraper.base_url}{url}"

                    summary_element = item.select_one('p, div[class*="summary"]')
                    summary = summary_element.text.strip() if summary_element else ""

                    print(f"- {title}")
                    print(f"  URL: {url}")
                    if summary:
                        print(
                            f"  Resumen: {summary[:100]}..."
                            if len(summary) > 100
                            else f"  Resumen: {summary}"
                        )
            else:
                print("No se encontraron noticias con scraping de Yahoo Finance")
        else:
            print(
                f"Error HTTP {response.status_code} al obtener noticias de Yahoo Finance"
            )
    except Exception as e:
        print(f"Error obteniendo noticias con scraping de Yahoo Finance: {str(e)}")

    # 3. Probar DuckDuckGo
    if DDG_AVAILABLE and scraper.ddgs:
        print("\n3. Obteniendo noticias con DuckDuckGo:")
        try:
            query = f"{company_name} {symbol} stock news"
            results = scraper.ddgs.news(query, max_results=3)

            if results:
                for item in results:
                    print(f"- {item.get('title', '')}")
                    print(
                        f"  Fuente: {item.get('source', '')} - Fecha: {item.get('date', '')}"
                    )
                    print(f"  URL: {item.get('url', '')}")
            else:
                print("No se encontraron noticias con DuckDuckGo")
        except Exception as e:
            print(f"Error obteniendo noticias con DuckDuckGo: {str(e)}")
    else:
        print("DuckDuckGo no está disponible")

    # 4. Probar Google Finance
    print("\n4. Obteniendo noticias con Google Finance:")
    try:
        google_news = scraper._get_news_from_google_finance(symbol, 3)
        if google_news:
            for news in google_news:
                print(f"- {news['title']}")
                print(f"  Fuente: {news['source']} - Fecha: {news['date']}")
                print(f"  URL: {news['url']}")
        else:
            print("No se encontraron noticias con Google Finance")
    except Exception as e:
        print(f"Error obteniendo noticias con Google Finance: {str(e)}")

    # 5. Probar MarketWatch
    print("\n5. Obteniendo noticias con MarketWatch:")
    try:
        mw_news = scraper._get_news_from_marketwatch(symbol, 3)
        if mw_news:
            for news in mw_news:
                print(f"- {news['title']}")
                print(f"  Fuente: {news['source']} - Fecha: {news['date']}")
                print(f"  URL: {news['url']}")
        else:
            print("No se encontraron noticias con MarketWatch")
    except Exception as e:
        print(f"Error obteniendo noticias con MarketWatch: {str(e)}")

    # 6. Probar el método principal get_news
    print("\n6. Probando el método principal get_news:")
    news_data = scraper.get_news(symbol, max_news=3)
    if news_data:
        print(f"Se obtuvieron {len(news_data)} noticias con el método principal")
        for i, news in enumerate(news_data, 1):
            print(f"{i}. {news.get('title', 'Sin título')}")
            print(
                f"   Fuente: {news.get('source', 'N/A')} - Fecha: {news.get('date', 'N/A')}"
            )
            print(f"   URL: {news.get('url', 'N/A')}")
            print(f"   Método: {getattr(news, '_source_method', 'Desconocido')}")
    else:
        print("No se obtuvieron noticias con el método principal")

    # 7. Probar el procesamiento de noticias
    print("\n7. Probando el procesamiento de noticias:")
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
            print(f"   URL: {news.get('url', 'N/A')}")
    else:
        print("No hay noticias para procesar")

    print("\n=== FIN DE LA PRUEBA DE FUENTES DE NOTICIAS ===")

    # Obtener y mostrar análisis
    print("\nRecomendaciones de analistas:")
    analysis_data = scraper.get_analysis(symbol)
    if "recommendations" in analysis_data and analysis_data["recommendations"]:
        print(f"Promedio: {analysis_data['recommendations'].get('average', 'N/A')}")
        # Mostrar distribución de recomendaciones si está disponible
        for key, value in analysis_data["recommendations"].items():
            if key != "average":
                print(f"  {key}: {value}")
    else:
        print("No hay recomendaciones disponibles")

    print("\nObjetivos de precio:")
    if "price_targets" in analysis_data and analysis_data["price_targets"]:
        print(f"Promedio: ${analysis_data['price_targets'].get('average', 'N/A')}")
        print(
            f"Rango: ${analysis_data['price_targets'].get('low', 'N/A')} - ${analysis_data['price_targets'].get('high', 'N/A')}"
        )
    else:
        print("No hay objetivos de precio disponibles")
