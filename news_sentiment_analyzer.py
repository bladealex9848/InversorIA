"""
Módulo para obtener noticias y sentimiento de mercado de fuentes fiables.
Utiliza múltiples fuentes y las consolida con ayuda de IA.
"""

import logging
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import re
import time
import random
from duckduckgo_search import DDGS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsSentimentAnalyzer:
    """Clase para obtener y analizar noticias y sentimiento de mercado de fuentes fiables"""

    def __init__(self, api_keys=None, openai_client=None):
        """
        Inicializa el analizador de noticias y sentimiento

        Args:
            api_keys (dict): Diccionario con claves de API para diferentes servicios
            openai_client: Cliente de OpenAI para análisis de sentimiento avanzado
        """
        self.api_keys = api_keys or {}
        self.openai_client = openai_client
        self.news_sources = [
            "Bloomberg",
            "CNBC",
            "Reuters",
            "Financial Times",
            "Wall Street Journal",
            "MarketWatch",
            "Investing.com",
            "Yahoo Finance",
            "Seeking Alpha",
            "Barron's",
            "The Economist",
            "Morningstar",
            "Benzinga",
            "Zacks",
            "TheStreet",
        ]
        self.cache = {}
        self.cache_expiry = 3600  # 1 hora en segundos

    def get_news_from_finnhub(self, symbol: str, days_back: int = 7) -> List[Dict]:
        """
        Obtiene noticias de Finnhub

        Args:
            symbol (str): Símbolo del activo
            days_back (int): Días hacia atrás para buscar noticias

        Returns:
            List[Dict]: Lista de noticias
        """
        if "finnhub" not in self.api_keys:
            logger.warning("No se encontró clave de API para Finnhub")
            return []

        try:
            # Calcular fecha desde
            from_date = (datetime.now() - timedelta(days=days_back)).strftime(
                "%Y-%m-%d"
            )
            to_date = datetime.now().strftime("%Y-%m-%d")

            # Construir URL
            url = f"https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": symbol,
                "from": from_date,
                "to": to_date,
                "token": self.api_keys["finnhub"],
            }

            # Realizar solicitud
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    news = []
                    for item in data[:10]:  # Limitar a 10 noticias
                        # Convertir timestamp a fecha
                        if "datetime" in item:
                            dt = datetime.fromtimestamp(item["datetime"])
                            item["datetime"] = dt.strftime("%Y-%m-%d %H:%M:%S")

                        news.append(
                            {
                                "title": item.get("headline", "Sin título"),
                                "summary": item.get("summary", ""),
                                "url": item.get("url", "#"),
                                "date": item.get("datetime", ""),
                                "source": item.get("source", "Finnhub"),
                                "sentiment": 0.5,  # Valor por defecto
                            }
                        )

                    return news

            logger.warning(
                f"Error obteniendo noticias de Finnhub: {response.status_code}"
            )
            return []

        except Exception as e:
            logger.error(f"Error en get_news_from_finnhub: {str(e)}")
            return []

    def get_news_from_alpha_vantage(
        self, symbol: str, days_back: int = 7
    ) -> List[Dict]:
        """
        Obtiene noticias de Alpha Vantage

        Args:
            symbol (str): Símbolo del activo
            days_back (int): Días hacia atrás para buscar noticias

        Returns:
            List[Dict]: Lista de noticias
        """
        if "alpha_vantage" not in self.api_keys:
            logger.warning("No se encontró clave de API para Alpha Vantage")
            return []

        try:
            # Construir URL
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": symbol,
                "apikey": self.api_keys["alpha_vantage"],
                "limit": 50,
            }

            # Realizar solicitud
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()

                if "feed" in data and isinstance(data["feed"], list):
                    # Filtrar por fecha
                    cutoff_date = datetime.now() - timedelta(days=days_back)

                    news = []
                    for item in data["feed"]:
                        # Verificar fecha
                        if "time_published" in item:
                            try:
                                pub_date = datetime.strptime(
                                    item["time_published"][:19], "%Y%m%dT%H%M%S"
                                )

                                if pub_date < cutoff_date:
                                    continue

                                date_str = pub_date.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                date_str = item.get("time_published", "")
                        else:
                            date_str = ""

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
                                "date": date_str,
                                "source": item.get("source", "Alpha Vantage"),
                                "sentiment": sentiment_score,
                            }
                        )

                    return news[:10]  # Limitar a 10 noticias

            logger.warning(
                f"Error obteniendo noticias de Alpha Vantage: {response.status_code}"
            )
            return []

        except Exception as e:
            logger.error(f"Error en get_news_from_alpha_vantage: {str(e)}")
            return []

    def get_news_from_web_search(
        self, symbol: str, company_name: str = None
    ) -> List[Dict]:
        """
        Obtiene noticias mediante búsqueda web

        Args:
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa

        Returns:
            List[Dict]: Lista de noticias
        """
        try:
            search_term = f"{symbol} stock news"
            if company_name:
                search_term = f"{company_name} ({symbol}) stock news"

            # Usar DuckDuckGo para búsqueda
            with DDGS() as ddgs:
                # Buscar noticias
                results = list(ddgs.news(search_term, region="wt-wt", max_results=10))

                if results:
                    news = []
                    for item in results:
                        # Calcular un sentimiento básico (neutral por defecto)
                        sentiment_value = 0.5

                        # Análisis simple de sentimiento basado en palabras clave
                        title_lower = item.get("title", "").lower()
                        if any(
                            word in title_lower
                            for word in [
                                "up",
                                "rise",
                                "gain",
                                "bull",
                                "positive",
                                "growth",
                            ]
                        ):
                            sentiment_value = 0.7  # Positivo
                        elif any(
                            word in title_lower
                            for word in [
                                "down",
                                "fall",
                                "drop",
                                "bear",
                                "negative",
                                "loss",
                            ]
                        ):
                            sentiment_value = 0.3  # Negativo

                        # Verificar si la fuente es confiable
                        source = item.get("source", "")
                        is_reliable = any(
                            reliable_source.lower() in source.lower()
                            for reliable_source in self.news_sources
                        )

                        if is_reliable:
                            news.append(
                                {
                                    "title": item.get("title", "Sin título"),
                                    "summary": item.get("body", ""),
                                    "url": item.get("url", "#"),
                                    "date": item.get("date", ""),
                                    "source": source,
                                    "sentiment": sentiment_value,
                                }
                            )

                    return news

            return []

        except Exception as e:
            logger.error(f"Error en get_news_from_web_search: {str(e)}")
            return []

    def analyze_sentiment_with_ai(self, news_data: List[Dict]) -> Dict:
        """
        Analiza el sentimiento de las noticias usando IA

        Args:
            news_data (List[Dict]): Lista de noticias

        Returns:
            Dict: Resultado del análisis de sentimiento
        """
        if not self.openai_client or not news_data:
            return self._analyze_sentiment_basic(news_data)

        try:
            # Preparar datos para análisis
            news_text = ""
            for i, item in enumerate(
                news_data[:5]
            ):  # Limitar a 5 noticias para el análisis
                news_text += f"Noticia {i+1}: {item['title']}\n"
                if item.get("summary"):
                    news_text += f"Resumen: {item['summary'][:200]}...\n"
                news_text += f"Fuente: {item.get('source', 'Desconocida')}\n\n"

            # Crear prompt para OpenAI
            prompt = f"""
            Analiza el sentimiento de mercado basado en las siguientes noticias financieras:
            
            {news_text}
            
            Proporciona un análisis detallado del sentimiento general (positivo, negativo o neutral),
            una puntuación numérica de sentimiento (0.0 a 1.0 donde 1.0 es completamente positivo),
            y una explicación de las razones principales que justifican tu análisis.
            
            Formato de respuesta:
            {{
                "sentiment": "positivo|negativo|neutral",
                "score": 0.XX,
                "explanation": "Explicación detallada",
                "key_factors": ["Factor 1", "Factor 2", "Factor 3"],
                "sources": [
                    {{"name": "Fuente 1", "sentiment": "positivo|negativo|neutral"}},
                    {{"name": "Fuente 2", "sentiment": "positivo|negativo|neutral"}}
                ]
            }}
            """

            # Realizar solicitud a OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un analista financiero experto especializado en análisis de sentimiento de mercado.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=800,
            )

            # Extraer respuesta
            response_text = response.choices[0].message.content

            # Intentar extraer JSON
            try:
                # Buscar patrón JSON en la respuesta
                json_match = re.search(r"({.*})", response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    result = json.loads(json_str)

                    # Asegurar que tiene los campos necesarios
                    if "sentiment" not in result or "score" not in result:
                        raise ValueError("Respuesta incompleta")

                    return result
            except:
                logger.warning("No se pudo extraer JSON de la respuesta de OpenAI")

            # Si falla la extracción de JSON, usar análisis básico
            return self._analyze_sentiment_basic(news_data)

        except Exception as e:
            logger.error(f"Error en analyze_sentiment_with_ai: {str(e)}")
            return self._analyze_sentiment_basic(news_data)

    def _analyze_sentiment_basic(self, news_data: List[Dict]) -> Dict:
        """
        Analiza el sentimiento de las noticias usando un método básico

        Args:
            news_data (List[Dict]): Lista de noticias

        Returns:
            Dict: Resultado del análisis de sentimiento
        """
        if not news_data:
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "explanation": "No hay suficientes datos para analizar el sentimiento.",
                "key_factors": [],
                "sources": [],
            }

        # Extraer y promediar puntuaciones de sentimiento de las noticias
        positive_mentions = 0
        negative_mentions = 0
        total_score = 0
        sources = []

        for item in news_data:
            sentiment_score = item.get("sentiment", 0.5)
            total_score += sentiment_score

            # Determinar sentimiento para esta fuente
            source_sentiment = "neutral"
            if sentiment_score > 0.6:
                source_sentiment = "positivo"
                positive_mentions += 1
            elif sentiment_score < 0.4:
                source_sentiment = "negativo"
                negative_mentions += 1

            # Añadir fuente
            sources.append(
                {
                    "name": item.get("source", "Desconocida"),
                    "sentiment": source_sentiment,
                }
            )

        # Calcular puntuación media
        avg_sentiment = total_score / len(news_data) if news_data else 0.5

        # Determinar etiqueta de sentimiento
        if avg_sentiment > 0.6:
            sentiment_label = "positivo"
            explanation = "La mayoría de las noticias muestran un tono positivo."
        elif avg_sentiment < 0.4:
            sentiment_label = "negativo"
            explanation = "La mayoría de las noticias muestran un tono negativo."
        else:
            sentiment_label = "neutral"
            explanation = "Las noticias muestran un tono mixto o neutral."

        # Crear factores clave
        key_factors = []
        if positive_mentions > 0:
            key_factors.append(f"{positive_mentions} menciones positivas")
        if negative_mentions > 0:
            key_factors.append(f"{negative_mentions} menciones negativas")
        if len(news_data) - positive_mentions - negative_mentions > 0:
            key_factors.append(
                f"{len(news_data) - positive_mentions - negative_mentions} menciones neutrales"
            )

        return {
            "sentiment": sentiment_label,
            "score": avg_sentiment,
            "explanation": explanation,
            "key_factors": key_factors,
            "sources": sources[:5],  # Limitar a 5 fuentes
        }

    def get_consolidated_news_and_sentiment(
        self, symbol: str, company_name: str = None
    ) -> Dict:
        """
        Obtiene noticias consolidadas y análisis de sentimiento de múltiples fuentes

        Args:
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa

        Returns:
            Dict: Noticias y sentimiento consolidados
        """
        cache_key = f"news_sentiment_{symbol}_{datetime.now().strftime('%Y-%m-%d')}"

        # Verificar caché
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if (
                datetime.now().timestamp() - cache_entry["timestamp"]
                < self.cache_expiry
            ):
                return cache_entry["data"]

        # Obtener noticias de diferentes fuentes
        finnhub_news = self.get_news_from_finnhub(symbol)
        alpha_vantage_news = self.get_news_from_alpha_vantage(symbol)
        web_news = self.get_news_from_web_search(symbol, company_name)

        # Consolidar noticias (eliminar duplicados por título)
        all_news = []
        seen_titles = set()

        for news_list in [finnhub_news, alpha_vantage_news, web_news]:
            for item in news_list:
                title = item.get("title", "").lower()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_news.append(item)

        # Ordenar por fecha (más recientes primero)
        try:
            all_news.sort(key=lambda x: x.get("date", ""), reverse=True)
        except:
            pass

        # Analizar sentimiento
        sentiment_analysis = self.analyze_sentiment_with_ai(all_news)

        # Crear resultado consolidado
        result = {
            "news": all_news[:10],  # Limitar a 10 noticias
            "sentiment": sentiment_analysis,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": list(
                set(item.get("source", "Desconocida") for item in all_news)
            ),
        }

        # Guardar en caché
        self.cache[cache_key] = {
            "data": result,
            "timestamp": datetime.now().timestamp(),
        }

        return result
