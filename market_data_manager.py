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

logger = logging.getLogger(__name__)


class MarketDataManager:
    """Clase para gestionar datos de mercado (noticias y sentimiento)"""

    def __init__(self, db_manager=None):
        """Inicializa el gestor de datos de mercado"""
        self.db_manager = db_manager if db_manager else DatabaseManager()

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
            if not signal_data.get("latest_news") and not signal_data.get(
                "additional_news"
            ):
                logger.warning(
                    f"No hay noticias para guardar en la señal de {signal_data.get('symbol', '')}"
                )
                return news_ids

            # Obtener información de la empresa para mejorar el contexto
            company_name = signal_data.get(
                "company_name", signal_data.get("symbol", "")
            )

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

                # Crear URL si está disponible en la fuente
                url = ""
                if "http" in signal_data.get("news_source", ""):
                    url = signal_data.get("news_source", "")

                main_news = {
                    "title": signal_data.get("latest_news", ""),
                    "summary": summary,
                    "source": signal_data.get("news_source", "InversorIA Analytics"),
                    "url": url,
                    "news_date": datetime.now(),
                    "impact": self._determine_news_impact(signal_data),
                }

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

                        add_news = {
                            "title": news_title.strip(),
                            "summary": summary,
                            "source": signal_data.get(
                                "news_source", "InversorIA Analytics"
                            ),
                            "url": "",  # URL no disponible para noticias adicionales
                            "news_date": datetime.now(),
                            "impact": impact,
                        }

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

            # Guardar datos de sentimiento
            sentiment_id = self.db_manager.save_market_sentiment(sentiment_data)

            if sentiment_id:
                logger.info(f"Datos de sentimiento guardados con ID: {sentiment_id}")

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

        return " | ".join(technical_info) if technical_info else "N/A"

    def _extract_vix(self, signal_data):
        """Extrae información del VIX del análisis"""
        # Intentar extraer el valor del VIX del análisis
        if signal_data.get("analysis"):
            vix_match = re.search(r"VIX.*?(\d+\.?\d*)", signal_data.get("analysis", ""))
            if vix_match:
                return vix_match.group(1)

        return "N/A"

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

        return "N/A"

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
