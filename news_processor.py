#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Processor - Módulo para procesar noticias financieras con IA
"""

import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NewsProcessor:
    """Clase para procesar noticias financieras con IA"""

    def __init__(self, ai_expert=None):
        """
        Inicializa el procesador de noticias

        Args:
            ai_expert: Experto en IA para procesar noticias
        """
        self.ai_expert = ai_expert

        # Intentar importar el scraper de Yahoo Finance
        try:
            from yahoo_finance_scraper import YahooFinanceScraper

            self.scraper = YahooFinanceScraper()
            self.scraper_available = True
            logger.info("Yahoo Finance Scraper disponible para uso")
        except ImportError:
            self.scraper = None
            self.scraper_available = False
            logger.warning("Yahoo Finance Scraper no está disponible")

    def get_news_for_symbol(
        self, symbol: str, company_name: str = None, max_news: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Obtiene noticias para un símbolo

        Args:
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa
            max_news (int): Número máximo de noticias a obtener

        Returns:
            List[Dict[str, Any]]: Lista de noticias procesadas
        """
        if not self.scraper_available:
            logger.error(
                "No se puede obtener noticias: Yahoo Finance Scraper no está disponible"
            )
            return []

        # Obtener noticias del scraper
        start_time = time.time()
        logger.info(f"Obteniendo noticias para {symbol}...")

        try:
            # Intentar obtener noticias con el método principal
            news_data = self.scraper.get_news(symbol, max_news=max_news)

            # Si no hay noticias, intentar directamente con DuckDuckGo
            if not news_data and hasattr(self.scraper, "ddgs") and self.scraper.ddgs:
                logger.info(
                    f"Intentando obtener noticias directamente con DuckDuckGo para {symbol}"
                )
                try:
                    # Obtener nombre de la empresa si no se proporcionó
                    if not company_name:
                        company_name = self.scraper._get_company_name(symbol)

                    # Construir consulta
                    query = f"{company_name} {symbol} stock news"

                    # Realizar búsqueda
                    results = self.scraper.ddgs.news(query, max_results=max_news)

                    if results:
                        news_data = []
                        for item in results:
                            news_item = {
                                "title": item.get("title", ""),
                                "summary": item.get("body", ""),
                                "url": item.get("url", ""),
                                "source": item.get("source", ""),
                                "date": item.get(
                                    "date", datetime.now().strftime("%Y-%m-%d")
                                ),
                                "_source_method": "duckduckgo_direct",
                            }
                            news_data.append(news_item)

                        logger.info(
                            f"Se obtuvieron {len(news_data)} noticias con DuckDuckGo para {symbol}"
                        )
                except Exception as e:
                    logger.error(f"Error obteniendo noticias con DuckDuckGo: {str(e)}")

            # Si aún no hay noticias, intentar con MarketWatch directamente
            if not news_data:
                logger.info(
                    f"Intentando obtener noticias directamente con MarketWatch para {symbol}"
                )
                try:
                    mw_news = self.scraper._get_news_from_marketwatch(symbol, max_news)
                    if mw_news:
                        # Registrar la fuente
                        for item in mw_news:
                            item["_source_method"] = "marketwatch_direct"
                        news_data = mw_news
                        logger.info(
                            f"Se obtuvieron {len(news_data)} noticias con MarketWatch para {symbol}"
                        )
                except Exception as e:
                    logger.error(f"Error obteniendo noticias con MarketWatch: {str(e)}")

            # Si aún no hay noticias, intentar con Google Finance directamente
            if not news_data:
                logger.info(
                    f"Intentando obtener noticias directamente con Google Finance para {symbol}"
                )
                try:
                    google_news = self.scraper._get_news_from_google_finance(
                        symbol, max_news
                    )
                    if google_news:
                        # Registrar la fuente
                        for item in google_news:
                            item["_source_method"] = "google_finance_direct"
                        news_data = google_news
                        logger.info(
                            f"Se obtuvieron {len(news_data)} noticias con Google Finance para {symbol}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error obteniendo noticias con Google Finance: {str(e)}"
                    )

            # Si no hay noticias después de intentar con todas las fuentes
            if not news_data:
                logger.warning(
                    f"No se encontraron noticias para {symbol} en ninguna fuente"
                )
                return []

            # Procesar noticias
            processed_news = self.scraper.process_news_with_expert(
                news_data, symbol, company_name
            )

            # Procesar con IA si está disponible
            if self.ai_expert and processed_news:
                processed_news = self.process_with_ai(
                    processed_news, symbol, company_name
                )

            elapsed_time = time.time() - start_time
            logger.info(
                f"Se obtuvieron y procesaron {len(processed_news)} noticias para {symbol} en {elapsed_time:.2f} segundos"
            )

            return processed_news

        except Exception as e:
            logger.error(f"Error obteniendo noticias para {symbol}: {str(e)}")
            return []

    def process_with_ai(
        self, news_data: List[Dict[str, Any]], symbol: str, company_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        Procesa noticias con el experto en IA

        Args:
            news_data (List[Dict[str, Any]]): Lista de noticias a procesar
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa

        Returns:
            List[Dict[str, Any]]: Noticias procesadas con IA
        """
        if not self.ai_expert or not news_data:
            return news_data

        try:
            logger.info(f"Procesando {len(news_data)} noticias con IA para {symbol}...")

            for i, news in enumerate(news_data):
                # Procesar título
                if news.get("title"):
                    try:
                        original_title = news["title"]
                        processed_title = self.ai_expert.process_text(
                            f"Mejora este título de noticia financiera para {company_name or symbol}: '{original_title}'",
                            max_tokens=100,
                        )
                        if processed_title:
                            news["title"] = processed_title
                            news["original_title"] = original_title
                    except Exception as e:
                        logger.error(f"Error procesando título con IA: {str(e)}")

                # Procesar resumen
                if news.get("summary"):
                    try:
                        original_summary = news["summary"]
                        processed_summary = self.ai_expert.process_text(
                            f"Mejora este resumen de noticia financiera para {company_name or symbol}, "
                            f"haciéndolo más informativo y específico: '{original_summary}'",
                            max_tokens=250,
                        )
                        if processed_summary:
                            news["summary"] = processed_summary
                            news["original_summary"] = original_summary
                    except Exception as e:
                        logger.error(f"Error procesando resumen con IA: {str(e)}")

                # Añadir análisis de impacto
                try:
                    impact_analysis = self.ai_expert.process_text(
                        f"Analiza el posible impacto de esta noticia en el precio de las acciones de {company_name or symbol} "
                        f"basado en el título: '{news.get('title', '')}' y el resumen: '{news.get('summary', '')}'",
                        max_tokens=150,
                    )
                    if impact_analysis:
                        news["impact_analysis"] = impact_analysis
                except Exception as e:
                    logger.error(
                        f"Error generando análisis de impacto con IA: {str(e)}"
                    )

                # Añadir análisis técnico y fundamental
                try:
                    technical_analysis = self.ai_expert.process_text(
                        f"Proporciona un breve análisis técnico para {company_name or symbol} basado en esta noticia: "
                        f"'{news.get('title', '')}'. Incluye posibles niveles de soporte/resistencia y tendencia.",
                        max_tokens=150,
                    )
                    if technical_analysis:
                        news["technical_analysis"] = technical_analysis
                except Exception as e:
                    logger.error(f"Error generando análisis técnico con IA: {str(e)}")

                try:
                    fundamental_analysis = self.ai_expert.process_text(
                        f"Proporciona un breve análisis fundamental para {company_name or symbol} basado en esta noticia: "
                        f"'{news.get('title', '')}'. Incluye posible impacto en ingresos, beneficios o valoración.",
                        max_tokens=150,
                    )
                    if fundamental_analysis:
                        news["fundamental_analysis"] = fundamental_analysis
                except Exception as e:
                    logger.error(
                        f"Error generando análisis fundamental con IA: {str(e)}"
                    )

                # Añadir recomendación de trading
                try:
                    trading_recommendation = self.ai_expert.process_text(
                        f"Basado en esta noticia para {company_name or symbol}: '{news.get('title', '')}', "
                        f"proporciona una recomendación de trading (COMPRA FUERTE, COMPRA, NEUTRAL, VENTA, VENTA FUERTE) "
                        f"y si recomiendas opciones CALL o PUT. Formato: 'DIRECCIÓN: [recomendación], OPCIONES: [CALL/PUT/NEUTRAL]'",
                        max_tokens=100,
                    )
                    if trading_recommendation:
                        news["trading_recommendation"] = trading_recommendation
                except Exception as e:
                    logger.error(
                        f"Error generando recomendación de trading con IA: {str(e)}"
                    )

                # Añadir traducción al español si no está en español
                if self._is_english_text(news.get("title", "")):
                    try:
                        spanish_title = self.ai_expert.process_text(
                            f"Traduce este título de noticia financiera al español: '{news.get('title', '')}'",
                            max_tokens=100,
                        )
                        if spanish_title:
                            news["spanish_title"] = spanish_title
                    except Exception as e:
                        logger.error(f"Error traduciendo título con IA: {str(e)}")

                if self._is_english_text(news.get("summary", "")):
                    try:
                        spanish_summary = self.ai_expert.process_text(
                            f"Traduce este resumen de noticia financiera al español: '{news.get('summary', '')}'",
                            max_tokens=250,
                        )
                        if spanish_summary:
                            news["spanish_summary"] = spanish_summary
                    except Exception as e:
                        logger.error(f"Error traduciendo resumen con IA: {str(e)}")

                # Traducir análisis de impacto si está en inglés
                if news.get("impact_analysis") and self._is_english_text(
                    news.get("impact_analysis", "")
                ):
                    try:
                        spanish_impact = self.ai_expert.process_text(
                            f"Traduce este análisis de impacto al español: '{news.get('impact_analysis', '')}'",
                            max_tokens=200,
                        )
                        if spanish_impact:
                            news["spanish_impact_analysis"] = spanish_impact
                    except Exception as e:
                        logger.error(
                            f"Error traduciendo análisis de impacto con IA: {str(e)}"
                        )

                # Marcar como procesado por IA
                news["ai_processed"] = True

                logger.info(f"Noticia {i+1}/{len(news_data)} procesada con IA")

            # Ordenar noticias por relevancia y sentimiento si están disponibles
            if all("relevance_score" in news for news in news_data) and all(
                "sentiment_score" in news for news in news_data
            ):
                news_data.sort(
                    key=lambda x: (
                        x.get("relevance_score", 0),
                        abs(x.get("sentiment_score", 0)),
                    ),
                    reverse=True,
                )

            return news_data

        except Exception as e:
            logger.error(f"Error en process_with_ai: {str(e)}")
            return news_data

    def _is_english_text(self, text: str) -> bool:
        """
        Determina si un texto está en inglés

        Args:
            text (str): Texto a evaluar

        Returns:
            bool: True si el texto está en inglés, False en caso contrario
        """
        if not text:
            return False

        # Palabras comunes en inglés
        english_words = [
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "will",
            "have",
            "has",
        ]

        # Contar palabras en inglés
        text_lower = text.lower()
        english_count = sum(
            1 for word in english_words if f" {word} " in f" {text_lower} "
        )

        # Si hay al menos 2 palabras en inglés, considerar que está en inglés
        return english_count >= 2


# Ejemplo de uso
if __name__ == "__main__":
    # Crear un experto en IA simulado para pruebas
    class MockAIExpert:
        def process_text(self, prompt, max_tokens=100):
            print(f"Procesando: {prompt[:50]}...")
            return f"Texto procesado para: {prompt[:30]}..."

    # Crear procesador de noticias
    processor = NewsProcessor(ai_expert=MockAIExpert())

    # Obtener noticias para un símbolo
    symbol = "GOOGL"
    company_name = "Alphabet Inc."

    news = processor.get_news_for_symbol(symbol, company_name, max_news=3)

    # Mostrar resultados
    print(f"\nNoticias procesadas para {symbol}:")
    for i, item in enumerate(news, 1):
        print(f"{i}. {item.get('title', 'Sin título')}")
        if item.get("spanish_title"):
            print(f"   Título (ES): {item['spanish_title']}")
        print(
            f"   Fuente: {item.get('source', 'N/A')} - Fecha: {item.get('date', 'N/A')}"
        )
        print(f"   URL: {item.get('url', 'N/A')}")
        if item.get("summary"):
            print(
                f"   Resumen: {item['summary'][:100]}..."
                if len(item.get("summary", "")) > 100
                else f"   Resumen: {item.get('summary', '')}"
            )
        if item.get("impact_analysis"):
            print(f"   Análisis de impacto: {item['impact_analysis']}")
        if item.get("technical_analysis"):
            print(f"   Análisis técnico: {item['technical_analysis']}")
        if item.get("fundamental_analysis"):
            print(f"   Análisis fundamental: {item['fundamental_analysis']}")
        if item.get("trading_recommendation"):
            print(f"   Recomendación de trading: {item['trading_recommendation']}")
        if item.get("relevance_score"):
            print(f"   Puntuación de relevancia: {item['relevance_score']:.2f}")
        if item.get("sentiment_score"):
            print(f"   Puntuación de sentimiento: {item['sentiment_score']:.2f}")
        print(f"   Método de obtención: {item.get('_source_method', 'Desconocido')}")
        print()
