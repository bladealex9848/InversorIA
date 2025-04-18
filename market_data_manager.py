#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para gestionar datos de mercado (noticias y sentimiento)
"""

import logging
from datetime import datetime
import re
import json
from database_utils import DatabaseManager

# Importar el validador de datos
try:
    from utils.data_validator import DataValidator

    DATA_VALIDATOR_AVAILABLE = True
except ImportError:
    DATA_VALIDATOR_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(
        "No se pudo importar DataValidator. Los datos no serán validados antes de guardarlos."
    )

# Importar el scraper de Yahoo Finance
try:
    from yahoo_finance_scraper import YahooFinanceScraper

    yahoo_scraper = YahooFinanceScraper()
    YAHOO_SCRAPER_AVAILABLE = True
except ImportError:
    YAHOO_SCRAPER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(
        "No se pudo importar YahooFinanceScraper. Las noticias serán generadas."
    )

# Importar el procesador de datos de mercado
try:
    from market_data_processor import MarketDataProcessor

    market_processor = MarketDataProcessor()
    MARKET_PROCESSOR_AVAILABLE = True
except ImportError:
    MARKET_PROCESSOR_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(
        "No se pudo importar MarketDataProcessor. Los datos no serán procesados con IA."
    )

# Gestor de resúmenes no es necesario aquí, usaremos st.success para mostrar mensajes
SUMMARY_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class MarketDataManager:
    """Clase para gestionar datos de mercado (noticias y sentimiento)"""

    def __init__(self, db_manager=None, ai_expert=None):
        """Inicializa el gestor de datos de mercado"""
        self.db_manager = db_manager if db_manager else DatabaseManager()

        # Inicializar el validador de datos si está disponible
        self.data_validator = None
        if DATA_VALIDATOR_AVAILABLE:
            try:
                from ai_utils import AIExpert

                # Si no se proporciona un experto en IA, intentar crear uno
                if not ai_expert and "openai_client" in globals():
                    ai_expert = AIExpert()
                self.data_validator = DataValidator(ai_expert)
                logger.info("Validador de datos inicializado correctamente")
            except Exception as e:
                logger.warning(
                    f"No se pudo inicializar el validador de datos: {str(e)}"
                )

    def save_news_from_signal(self, signal_data):
        """
        Guarda noticias relevantes de una señal en la tabla market_news

        Args:
            signal_data (dict): Datos de la señal

        Returns:
            list: IDs de las noticias guardadas
        """
        try:
            news_ids = []

            # Verificar si hay noticias en la señal
            if (
                not signal_data.get("latest_news")
                and not signal_data.get("additional_news")
                and not signal_data.get("news")
            ):
                logger.warning(
                    f"No hay noticias para guardar en la señal de {signal_data.get('symbol', '')}"
                )
                return news_ids

            # Obtener información de la empresa para mejorar el contexto
            company_name = signal_data.get(
                "company_name", signal_data.get("symbol", "")
            )

            # Intentar obtener noticias reales de Yahoo Finance
            symbol = signal_data.get("symbol", "")
            yahoo_news = []

            if YAHOO_SCRAPER_AVAILABLE:
                try:
                    # Obtener noticias de Yahoo Finance
                    yahoo_news = yahoo_scraper.get_news(symbol, max_news=5)
                    if yahoo_news:
                        logger.info(
                            f"Se obtuvieron {len(yahoo_news)} noticias de Yahoo Finance para {symbol}"
                        )

                        # Procesar noticias con IA si está disponible
                        if MARKET_PROCESSOR_AVAILABLE:
                            try:
                                # Procesar noticias para mejorar calidad
                                yahoo_news = market_processor.process_news(
                                    yahoo_news, symbol, company_name
                                )
                                logger.info(f"Noticias procesadas con IA para {symbol}")
                            except Exception as e:
                                logger.error(
                                    f"Error procesando noticias con IA: {str(e)}"
                                )

                        # Guardar noticias de Yahoo Finance
                        for i, news_item in enumerate(yahoo_news):
                            # Determinar impacto basado en la dirección de la señal
                            impact = self._determine_news_impact(signal_data)

                            # Crear objeto de noticia
                            news = {
                                "title": news_item.get(
                                    "title", f"Noticia sobre {company_name}"
                                ),
                                "summary": news_item.get("summary", ""),
                                "source": news_item.get("source", "Yahoo Finance"),
                                "url": news_item.get(
                                    "url", f"https://finance.yahoo.com/quote/{symbol}"
                                ),
                                "news_date": datetime.now(),
                                "impact": impact,
                            }

                            # Validar y mejorar la noticia antes de guardarla
                            if self.data_validator:
                                news = self.data_validator.validate_market_news(news)
                                logger.info(f"Noticia {i+1} validada y mejorada con IA")

                            # Guardar noticia
                            news_id = self.db_manager.save_market_news(news)
                            if news_id:
                                news_ids.append(news_id)
                                logger.info(
                                    f"Noticia real de Yahoo Finance {i+1} guardada con ID: {news_id}"
                                )
                except Exception as e:
                    logger.error(
                        f"Error obteniendo noticias de Yahoo Finance: {str(e)}"
                    )

            # Si no hay noticias de Yahoo Finance, usar las noticias proporcionadas en signal_data
            if (
                not yahoo_news
                and signal_data.get("news")
                and isinstance(signal_data.get("news"), list)
            ):
                for news_item in signal_data.get("news", []):
                    if isinstance(news_item, dict) and news_item.get("title"):
                        # Crear noticia con datos reales
                        real_news = {
                            "title": news_item.get("title", ""),
                            "summary": news_item.get(
                                "summary", news_item.get("description", "")
                            ),
                            "source": news_item.get("source", "Fuente Financiera"),
                            "url": news_item.get("url", ""),
                            "news_date": news_item.get("date", datetime.now()),
                            "impact": self._determine_news_impact(signal_data),
                        }

                        # Asegurar que la URL sea válida
                        if not real_news["url"] or not real_news["url"].startswith(
                            "http"
                        ):
                            # Buscar URL alternativa
                            if "yahoo" in real_news["source"].lower():
                                real_news["url"] = (
                                    f"https://finance.yahoo.com/quote/{signal_data.get('symbol', '')}"
                                )
                            elif "bloomberg" in real_news["source"].lower():
                                real_news["url"] = (
                                    f"https://www.bloomberg.com/quote/{signal_data.get('symbol', '')}"
                                )
                            elif "cnbc" in real_news["source"].lower():
                                real_news["url"] = (
                                    f"https://www.cnbc.com/quotes/{signal_data.get('symbol', '')}"
                                )
                            elif "reuters" in real_news["source"].lower():
                                real_news["url"] = (
                                    f"https://www.reuters.com/companies/{signal_data.get('symbol', '')}"
                                )
                            else:
                                real_news["url"] = (
                                    f"https://www.google.com/finance/quote/{signal_data.get('symbol', '')}"
                                )

                        # Guardar noticia real
                        news_id = self.db_manager.save_market_news(real_news)
                        if news_id:
                            news_ids.append(news_id)
                            logger.info(f"Noticia real guardada con ID: {news_id}")

            # Si ya guardamos noticias reales y son suficientes, podemos omitir la noticia principal
            if len(news_ids) >= 3:
                logger.info(
                    f"Ya se guardaron {len(news_ids)} noticias reales, omitiendo noticia principal"
                )

                # Mostrar mensaje de éxito en lugar de usar summary_manager
                logger.info(
                    f"Se guardaron {len(news_ids)} noticias para {symbol} ({company_name})"
                )

                return news_ids

            # Guardar la noticia principal con todos los campos requeridos
            if signal_data.get("latest_news"):
                # Generar un resumen más detallado basado en el análisis experto si está disponible
                summary = signal_data.get("analysis", "")
                if (
                    signal_data.get("expert_analysis")
                    and len(signal_data.get("expert_analysis", "")) > 100
                ):
                    # Extraer un resumen del análisis experto (primeros 300 caracteres)
                    expert_summary = (
                        signal_data.get("expert_analysis", "")[:300] + "..."
                    )
                    summary = f"Análisis experto para {company_name}: {expert_summary}"

                # Crear URL si está disponible en la fuente o en las noticias
                url = ""
                source = signal_data.get("news_source", "InversorIA Analytics")

                if "http" in signal_data.get("news_source", ""):
                    url = signal_data.get("news_source", "")
                elif signal_data.get("news") and isinstance(
                    signal_data.get("news"), list
                ):
                    # Buscar URL en las noticias
                    for news_item in signal_data.get("news", []):
                        if (
                            isinstance(news_item, dict)
                            and news_item.get("url")
                            and "http" in news_item.get("url", "")
                        ):
                            url = news_item.get("url")
                            # Actualizar también la fuente si está disponible
                            if news_item.get("source"):
                                source = news_item.get("source")
                            break

                # Si no hay URL, generar una basada en la fuente o usar una fuente financiera conocida
                if not url:
                    if "yahoo" in source.lower() or source == "InversorIA Analytics":
                        url = f"https://finance.yahoo.com/quote/{signal_data.get('symbol', '')}"
                        if source == "InversorIA Analytics":
                            source = "Yahoo Finance"
                    elif "bloomberg" in source.lower():
                        url = f"https://www.bloomberg.com/quote/{signal_data.get('symbol', '')}"
                    elif "cnbc" in source.lower():
                        url = f"https://www.cnbc.com/quotes/{signal_data.get('symbol', '')}"
                    elif "reuters" in source.lower():
                        url = f"https://www.reuters.com/companies/{signal_data.get('symbol', '')}"
                    else:
                        url = f"https://www.google.com/finance/quote/{signal_data.get('symbol', '')}"
                        if source == "InversorIA Analytics":
                            source = "Google Finance"

                # Mejorar el título usando el procesador de IA
                title = signal_data.get("latest_news", "")
                if title.startswith("Análisis técnico muestra") or len(title) < 20:
                    direction = (
                        "alcista"
                        if signal_data.get("direction") == "CALL"
                        else "bajista"
                    )
                    default_title = f"{company_name} ({signal_data.get('symbol', '')}) muestra tendencia {direction} con soporte en ${signal_data.get('support_level', 0):.2f}"

                    # Contexto adicional para el procesador de IA
                    context = {
                        "price": signal_data.get("price", 0),
                        "direction": signal_data.get("direction", ""),
                        "trend": signal_data.get("trend", ""),
                        "rsi": signal_data.get("rsi", ""),
                        "support_level": signal_data.get("support_level", 0),
                        "resistance_level": signal_data.get("resistance_level", 0),
                        "company_name": company_name,
                    }

                    # Procesar con IA si está disponible
                    if hasattr(self, "ai_processor") and self.ai_processor:
                        processed_title = self.ai_processor.process_content_with_ai(
                            signal_data.get("symbol", ""),
                            default_title,
                            "latest_news",
                            context,
                        )
                        title = processed_title if processed_title else default_title
                    else:
                        title = default_title

                # Mejorar el resumen usando el procesador de IA
                if hasattr(self, "ai_processor") and self.ai_processor:
                    processed_summary = self.ai_processor.process_content_with_ai(
                        signal_data.get("symbol", ""),
                        summary,
                        "additional_news",
                        context,
                    )
                    if processed_summary:
                        summary = processed_summary

                main_news = {
                    "title": title,
                    "summary": summary,
                    "source": source,  # Usar la fuente actualizada
                    "url": url,
                    "news_date": datetime.now(),
                    "impact": self._determine_news_impact(signal_data),
                }

                # Validar y mejorar la noticia principal antes de guardarla
                if self.data_validator:
                    main_news = self.data_validator.validate_market_news(main_news)
                    logger.info("Noticia principal validada y mejorada con IA")

                # Guardar la noticia principal (permitir múltiples noticias del mismo día)
                news_id = self.db_manager.save_market_news(main_news)
                if news_id:
                    news_ids.append(news_id)
                    logger.info(f"Noticia principal guardada con ID: {news_id}")

            # Guardar noticias adicionales con mejor formato
            if signal_data.get("additional_news"):
                # Dividir las noticias adicionales (pueden estar separadas por saltos de línea)
                additional_news_text = signal_data.get("additional_news", "")

                # Manejar diferentes formatos de separación
                if "\\n" in additional_news_text:
                    additional_news_list = additional_news_text.split("\\n")
                elif ". " in additional_news_text:
                    additional_news_list = additional_news_text.split(". ")
                    additional_news_list = [
                        item + "." for item in additional_news_list if item
                    ]
                else:
                    additional_news_list = [additional_news_text]

                for i, news_title in enumerate(additional_news_list):
                    if news_title.strip():
                        # Determinar impacto basado en palabras clave
                        impact = "Medio"
                        news_text = news_title.lower()
                        if any(
                            word in news_text
                            for word in [
                                "importante",
                                "crucial",
                                "significativo",
                                "fuerte",
                                "gran",
                            ]
                        ):
                            impact = "Alto"
                        elif any(
                            word in news_text
                            for word in ["menor", "leve", "pequeño", "ligero"]
                        ):
                            impact = "Bajo"

                        # Crear resumen más informativo
                        summary = f"Noticia relacionada con {company_name}: {news_title.strip()[:100]}"

                        # Mejorar el resumen usando el procesador de IA si está disponible
                        if hasattr(self, "ai_processor") and self.ai_processor:
                            # Contexto adicional para el procesador de IA
                            context = {
                                "price": signal_data.get("price", 0),
                                "direction": signal_data.get("direction", ""),
                                "trend": signal_data.get("trend", ""),
                                "company_name": company_name,
                            }

                            processed_summary = (
                                self.ai_processor.process_content_with_ai(
                                    signal_data.get("symbol", ""),
                                    news_title.strip(),
                                    "additional_news",
                                    context,
                                )
                            )
                            if processed_summary:
                                summary = processed_summary

                        # Buscar URL y fuente en las noticias si están disponibles
                        url = ""
                        source = signal_data.get("news_source", "InversorIA Analytics")

                        if signal_data.get("news") and isinstance(
                            signal_data.get("news"), list
                        ):
                            # Buscar coincidencia por título
                            for news_item in signal_data.get("news", []):
                                if isinstance(news_item, dict) and news_item.get(
                                    "title"
                                ):
                                    # Verificar si hay coincidencia parcial en el título
                                    if (
                                        news_title.strip().lower()
                                        in news_item.get("title", "").lower()
                                        or news_item.get("title", "").lower()
                                        in news_title.strip().lower()
                                    ):
                                        if news_item.get(
                                            "url"
                                        ) and "http" in news_item.get("url", ""):
                                            url = news_item.get("url")
                                        if news_item.get("source"):
                                            source = news_item.get("source")
                                        break

                        add_news = {
                            "title": news_title.strip(),
                            "summary": summary,
                            "source": source,
                            "url": url,
                            "news_date": datetime.now(),
                            "impact": impact,
                        }

                        # Validar y mejorar la noticia adicional antes de guardarla
                        if self.data_validator:
                            add_news = self.data_validator.validate_market_news(
                                add_news
                            )
                            logger.info(
                                f"Noticia adicional {i+1} validada y mejorada con IA"
                            )

                        # Guardar la noticia adicional (permitir múltiples noticias)
                        news_id = self.db_manager.save_market_news(add_news)
                        if news_id:
                            news_ids.append(news_id)
                            logger.info(
                                f"Noticia adicional {i+1} guardada con ID: {news_id}"
                            )

            return news_ids

        except Exception as e:
            logger.error(f"Error guardando noticias: {str(e)}")
            return []

    def save_sentiment_from_signal(self, signal_data):
        """
        Guarda datos de sentimiento de mercado basados en una señal

        Args:
            signal_data (dict): Datos de la señal

        Returns:
            int: ID del sentimiento guardado o None si hay error
        """
        try:
            # Verificar si hay datos de sentimiento en la señal
            if not signal_data.get("sentiment"):
                logger.warning(
                    f"No hay datos de sentimiento para guardar en la señal de {signal_data.get('symbol', '')}"
                )
                return None

            # Obtener información de la empresa para mejorar el contexto
            company_name = signal_data.get(
                "company_name", signal_data.get("symbol", "")
            )

            # Mapear el sentimiento de la señal al formato de la tabla
            sentiment_mapping = {
                "positivo": "Alcista",
                "negativo": "Bajista",
                "neutral": "Neutral",
                "muy positivo": "Alcista",
                "muy negativo": "Bajista",
                "ligeramente positivo": "Alcista",
                "ligeramente negativo": "Bajista",
            }

            overall_sentiment = sentiment_mapping.get(
                signal_data.get("sentiment", "").lower(), "Neutral"
            )

            # Extraer información técnica del análisis
            technical_indicators = self._extract_technical_info(signal_data)

            # Extraer información del VIX con mejor manejo
            vix_value = self._extract_vix(signal_data)
            if vix_value == "N/A" and signal_data.get("expert_analysis"):
                # Intentar extraer el VIX del análisis experto
                vix_match = re.search(
                    r"VIX.*?(\d+\.?\d*)", signal_data.get("expert_analysis", "")
                )
                if vix_match:
                    vix_value = vix_match.group(1)

            # Extraer tendencia del S&P 500 con mejor manejo
            sp500_trend = self._extract_sp500_trend(signal_data)
            if sp500_trend == "N/A" and signal_data.get("expert_analysis"):
                # Intentar extraer la tendencia del S&P 500 del análisis experto
                if "S&P 500" in signal_data.get("expert_analysis", ""):
                    expert_text = signal_data.get("expert_analysis", "").lower()
                    if "alcista" in expert_text:
                        sp500_trend = "Alcista"
                    elif "bajista" in expert_text:
                        sp500_trend = "Bajista"
                    elif "lateral" in expert_text:
                        sp500_trend = "Lateral"

            # Extraer información de volumen con mejor manejo
            volume_info = self._extract_volume_info(signal_data)
            if volume_info == "N/A" and signal_data.get("expert_analysis"):
                # Intentar extraer información de volumen del análisis experto
                volume_match = re.search(
                    r"volumen.*?(alto|bajo|normal|fuerte|débil)",
                    signal_data.get("expert_analysis", "").lower(),
                )
                if volume_match:
                    volume_info = volume_match.group(1).capitalize()

            # Crear notas más detalladas
            notes = f"Análisis de {company_name} ({signal_data.get('symbol', '')}). "
            notes += f"Sentimiento: {signal_data.get('sentiment', 'Neutral')} "
            notes += f"(Score: {signal_data.get('sentiment_score', 0.5)}). "

            # Añadir información de la recomendación si está disponible
            if signal_data.get("recommendation"):
                notes += f"Recomendación: {signal_data.get('recommendation')}. "

            # Añadir información de la dirección de la señal
            if signal_data.get("direction"):
                direction_text = (
                    "Alcista"
                    if signal_data.get("direction") == "CALL"
                    else (
                        "Bajista"
                        if signal_data.get("direction") == "PUT"
                        else "Neutral"
                    )
                )
                notes += f"Dirección: {direction_text}. "

            # Crear datos de sentimiento
            sentiment_data = {
                "date": datetime.now().date(),
                "overall": overall_sentiment,
                "vix": vix_value,
                "sp500_trend": sp500_trend,
                "technical_indicators": technical_indicators,
                "volume": volume_info,
                "notes": notes,
            }

            # Validar y mejorar los datos de sentimiento antes de guardarlos
            if self.data_validator:
                sentiment_data = self.data_validator.validate_market_sentiment(
                    sentiment_data
                )
                logger.info("Datos de sentimiento validados y mejorados con IA")

            # No guardamos el sentimiento de mercado aquí, ya que se carga al inicio de la aplicación principal
            logger.info(
                "Omitiendo guardado de sentimiento de mercado, ya que se carga al inicio de la aplicación principal"
            )
            sentiment_id = None

            return sentiment_id

        except Exception as e:
            logger.error(f"Error guardando datos de sentimiento: {str(e)}")
            return None

    def _determine_news_impact(self, signal_data):
        """Determina el impacto de una noticia basado en los datos de la señal"""
        # Si es una señal de alta confianza, el impacto es alto
        if (
            signal_data.get("is_high_confidence")
            or signal_data.get("confidence_level") == "Alta"
        ):
            return "Alto"

        # Si el sentimiento es muy positivo o muy negativo, el impacto es alto
        sentiment = signal_data.get("sentiment", "").lower()
        if "muy positivo" in sentiment or "muy negativo" in sentiment:
            return "Alto"

        # Si el sentimiento es ligeramente positivo o negativo, el impacto es medio
        if "ligeramente" in sentiment:
            return "Medio"

        # Por defecto, impacto medio
        return "Medio"

    def _extract_technical_info(self, signal_data):
        """Extrae información técnica del análisis"""
        technical_info = []

        # Añadir indicadores alcistas y bajistas
        if signal_data.get("bullish_indicators"):
            technical_info.append(
                f"Indicadores alcistas: {signal_data.get('bullish_indicators')}"
            )

        if signal_data.get("bearish_indicators"):
            technical_info.append(
                f"Indicadores bajistas: {signal_data.get('bearish_indicators')}"
            )

        # Añadir RSI si está disponible
        if signal_data.get("rsi"):
            technical_info.append(f"RSI: {signal_data.get('rsi')}")

        # Añadir tendencia
        if signal_data.get("trend"):
            technical_info.append(f"Tendencia: {signal_data.get('trend')}")

        # Añadir parámetros de opciones si están disponibles
        if signal_data.get("options_params") or signal_data.get("costo_strike"):
            options_info = []
            if signal_data.get("costo_strike"):
                options_info.append(f"Costo strike: {signal_data.get('costo_strike')}")
            if signal_data.get("volumen_min"):
                options_info.append(f"Volumen mínimo: {signal_data.get('volumen_min')}")
            if signal_data.get("distance_spot_strike"):
                options_info.append(
                    f"Distancia spot-strike: {signal_data.get('distance_spot_strike')}"
                )

            if options_info:
                technical_info.append(" | ".join(options_info))

        # Limitar la longitud total para evitar errores de base de datos
        result = " | ".join(technical_info) if technical_info else "N/A"
        if len(result) > 1000:  # Limitar a 1000 caracteres para evitar errores
            result = result[:997] + "..."

        return result

    def _extract_vix(self, signal_data):
        """Extrae información del VIX del análisis"""
        # Primero, verificar si el VIX está directamente disponible en los datos de la señal
        if (
            signal_data.get("vix_level")
            and str(signal_data.get("vix_level")).replace(".", "").isdigit()
        ):
            return str(signal_data.get("vix_level"))

        # Intentar extraer el valor del VIX del análisis
        if signal_data.get("analysis"):
            vix_match = re.search(r"VIX.*?(\d+\.?\d*)", signal_data.get("analysis", ""))
            if vix_match:
                return vix_match.group(1)

        # Intentar extraer el valor del VIX del análisis experto
        if signal_data.get("expert_analysis"):
            vix_match = re.search(
                r"VIX.*?(\d+\.?\d*)", signal_data.get("expert_analysis", "")
            )
            if vix_match:
                return vix_match.group(1)

        # Si no se encuentra, usar un valor predeterminado basado en la volatilidad del mercado
        if signal_data.get("volatility"):
            volatility = float(signal_data.get("volatility", 0))
            if volatility > 30:
                return "30.0"  # Alta volatilidad
            elif volatility > 20:
                return "20.0"  # Volatilidad media
            else:
                return "15.0"  # Baja volatilidad

        # Valor predeterminado
        return "20.0"  # Valor típico del VIX

    def _extract_sp500_trend(self, signal_data):
        """Extrae información de la tendencia del S&P 500"""
        # Intentar extraer información sobre el S&P 500
        if signal_data.get("analysis"):
            if "S&P 500" in signal_data.get("analysis", ""):
                if "alcista" in signal_data.get("analysis", "").lower():
                    return "Alcista"
                elif "bajista" in signal_data.get("analysis", "").lower():
                    return "Bajista"
                elif "lateral" in signal_data.get("analysis", "").lower():
                    return "Lateral"

        # Si no se encuentra en el análisis, intentar extraer del expert_analysis
        if signal_data.get("expert_analysis"):
            if "S&P 500" in signal_data.get("expert_analysis", ""):
                expert_text = signal_data.get("expert_analysis", "").lower()
                if "alcista" in expert_text and "s&p" in expert_text:
                    return "Alcista"
                elif "bajista" in expert_text and "s&p" in expert_text:
                    return "Bajista"
                elif "lateral" in expert_text and "s&p" in expert_text:
                    return "Lateral"

        # Si no se encuentra en ninguna parte, usar la tendencia general del mercado
        if signal_data.get("market_trend"):
            return signal_data.get("market_trend")

        # Si todo lo demás falla, usar un valor predeterminado basado en la dirección de la señal
        if signal_data.get("direction") == "CALL":
            return "Alcista"
        elif signal_data.get("direction") == "PUT":
            return "Bajista"

        return "Neutral"  # Valor predeterminado en lugar de N/A

    def _extract_volume_info(self, signal_data):
        """Extrae información sobre el volumen"""
        # Intentar extraer información sobre el volumen
        if signal_data.get("analysis"):
            volume_match = re.search(
                r"volumen.*?(alto|bajo|normal|fuerte|débil)",
                signal_data.get("analysis", "").lower(),
            )
            if volume_match:
                return volume_match.group(1).capitalize()

        return "N/A"
