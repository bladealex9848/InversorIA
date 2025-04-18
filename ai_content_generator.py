#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para generar contenido utilizando IA.
Incluye funciones para generar resúmenes de noticias y análisis de sentimiento.
"""

import logging
import re
from typing import Dict, Any, Optional, List

# Importar módulo de procesamiento de texto
from text_processing import clean_text, contains_prompt_text

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Intentar importar el experto en IA
AI_EXPERT_AVAILABLE = False
try:
    from ai_utils import AIExpert

    AI_EXPERT_AVAILABLE = True
    logger.info("AIExpert disponible para uso en ai_content_generator.py")
except ImportError:
    logger.warning(
        "AIExpert no está disponible en ai_content_generator.py. No se podrá generar contenido con IA."
    )


def generate_summary_with_ai(title: str, symbol: str, url: str = None) -> Optional[str]:
    """
    Genera un resumen de noticia utilizando IA

    Args:
        title (str): Título de la noticia
        symbol (str): Símbolo del activo
        url (str, optional): URL de la noticia

    Returns:
        Optional[str]: Resumen generado o None si no se pudo generar un resumen válido
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning(
            "AIExpert no está disponible. No se puede generar resumen con IA."
        )
        return None

    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()

        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, "client") or not ai_expert.client:
            logger.warning("Cliente OpenAI no disponible. No se puede generar resumen.")
            return None

        # Crear prompt para generar resumen (sin espacios al inicio de cada línea)
        url_info = f"URL: {url}" if url else ""
        prompt = f"""Genera un resumen informativo y detallado en español (150-200 caracteres)
para una noticia financiera sobre {symbol} con este título: '{title}'.
{url_info}

El resumen debe:
1. Ser específico y relevante para inversores
2. Incluir posibles implicaciones para el precio de la acción
3. Estar escrito en un tono profesional y objetivo
4. NO incluir frases genéricas de introducción o cierre
5. Ir directo al punto principal de la noticia"""

        # Generar resumen
        summary = ai_expert.process_text(prompt, max_tokens=250)

        # Verificar si el resumen contiene parte del prompt (caso de fallback)
        prompt_fragments = [
            "Genera un resumen informativo",
            "Como experto financiero",
            "El resumen debe",
        ]

        if not summary or contains_prompt_text(summary, prompt_fragments):
            logger.warning(
                "El resumen generado contiene parte del prompt o está vacío."
            )
            return None

        # Limpiar resumen
        summary = clean_text(summary)

        # Verificar que el resumen tenga una longitud mínima
        if len(summary) < 30:
            logger.warning(f"Resumen demasiado corto: {summary}")
            return None

        return summary
    except Exception as e:
        logger.error(f"Error generando resumen con IA: {str(e)}")
        return None


def generate_sentiment_analysis_with_ai(
    sentiment_data: Dict[str, Any],
) -> Optional[str]:
    """
    Genera un análisis de sentimiento utilizando IA

    Args:
        sentiment_data (Dict[str, Any]): Datos de sentimiento

    Returns:
        Optional[str]: Análisis generado o None si no se pudo generar un análisis válido
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning(
            "AIExpert no está disponible. No se puede generar análisis con IA."
        )
        return None

    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()

        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, "client") or not ai_expert.client:
            logger.warning(
                "Cliente OpenAI no disponible. No se puede generar análisis."
            )
            return None

        # Recopilar datos disponibles para generar un análisis completo
        overall = sentiment_data.get("overall", "Neutral")
        vix = sentiment_data.get("vix", "N/A")
        sp500_trend = sentiment_data.get("sp500_trend", "N/A")
        tech_indicators = sentiment_data.get("technical_indicators", "N/A")

        # Crear prompt para generar análisis (sin espacios al inicio de cada línea)
        prompt = f"""Genera un análisis detallado del sentimiento de mercado
basado en los siguientes datos:

- Sentimiento general: {overall}
- VIX (índice de volatilidad): {vix}
- Tendencia S&P500: {sp500_trend}
- Indicadores técnicos: {tech_indicators}

El análisis debe:
1. Explicar las implicaciones de estos datos para inversores
2. Incluir una evaluación de riesgos y oportunidades
3. Proporcionar contexto sobre la situación actual del mercado
4. Estar escrito en español profesional y objetivo
5. Tener entre 150-300 palabras
6. NO incluir frases genéricas de introducción o cierre"""

        # Generar análisis
        analysis = ai_expert.process_text(prompt, max_tokens=500)

        # Verificar si el análisis contiene parte del prompt (caso de fallback)
        prompt_fragments = [
            "Genera un análisis detallado",
            "El análisis debe",
            "basado en los siguientes datos",
        ]

        if not analysis or contains_prompt_text(analysis, prompt_fragments):
            logger.warning(
                "El análisis generado contiene parte del prompt o está vacío."
            )
            return None

        # Limpiar análisis
        analysis = clean_text(analysis)

        # Verificar que el análisis tenga una longitud mínima
        if len(analysis) < 50:
            logger.warning(f"Análisis demasiado corto: {analysis}")
            return None

        return analysis
    except Exception as e:
        logger.error(f"Error generando análisis con IA: {str(e)}")
        return None


def generate_technical_analysis_with_ai(
    symbol: str, price_data: Dict[str, Any]
) -> Optional[str]:
    """
    Genera un análisis técnico utilizando IA

    Args:
        symbol (str): Símbolo del activo
        price_data (Dict[str, Any]): Datos de precios y técnicos

    Returns:
        Optional[str]: Análisis generado o None si no se pudo generar un análisis válido
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning(
            "AIExpert no está disponible. No se puede generar análisis técnico con IA."
        )
        return None

    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()

        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, "client") or not ai_expert.client:
            logger.warning(
                "Cliente OpenAI no disponible. No se puede generar análisis técnico."
            )
            return None

        # Recopilar datos disponibles para generar un análisis completo
        current_price = price_data.get("current_price", "N/A")
        change_percent = price_data.get("change_percent", "N/A")
        volume = price_data.get("volume", "N/A")
        ma_50 = price_data.get("ma_50", "N/A")
        ma_200 = price_data.get("ma_200", "N/A")
        rsi = price_data.get("rsi", "N/A")

        # Crear prompt para generar análisis técnico
        prompt = f"""Genera un análisis técnico detallado para {symbol} basado en los siguientes datos:

- Precio actual: {current_price}
- Cambio porcentual: {change_percent}
- Volumen: {volume}
- Media móvil 50 días: {ma_50}
- Media móvil 200 días: {ma_200}
- RSI: {rsi}

El análisis debe:
1. Interpretar los indicadores técnicos y su significado
2. Identificar posibles niveles de soporte y resistencia
3. Evaluar la tendencia actual (alcista, bajista o lateral)
4. Proporcionar una perspectiva a corto y medio plazo
5. Estar escrito en español profesional y objetivo
6. Tener entre 150-250 palabras
7. NO incluir frases genéricas de introducción o cierre"""

        # Generar análisis
        analysis = ai_expert.process_text(prompt, max_tokens=400)

        # Verificar si el análisis contiene parte del prompt (caso de fallback)
        prompt_fragments = [
            "Genera un análisis técnico",
            "El análisis debe",
            "basado en los siguientes datos",
        ]

        if not analysis or contains_prompt_text(analysis, prompt_fragments):
            logger.warning(
                "El análisis técnico generado contiene parte del prompt o está vacío."
            )
            return None

        # Limpiar análisis
        analysis = clean_text(analysis)

        # Verificar que el análisis tenga una longitud mínima
        if len(analysis) < 50:
            logger.warning(f"Análisis técnico demasiado corto: {analysis}")
            return None

        return analysis
    except Exception as e:
        logger.error(f"Error generando análisis técnico con IA: {str(e)}")
        return None


def generate_trading_signal_analysis_with_ai(
    signal_data: Dict[str, Any],
) -> Optional[str]:
    """
    Genera un análisis experto para una señal de trading utilizando IA

    Args:
        signal_data (Dict[str, Any]): Datos de la señal de trading

    Returns:
        Optional[str]: Análisis generado o None si no se pudo generar un análisis válido
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning(
            "AIExpert no está disponible. No se puede generar análisis experto con IA."
        )
        return None

    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()

        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, "client") or not ai_expert.client:
            logger.warning(
                "Cliente OpenAI no disponible. No se puede generar análisis experto."
            )
            return None

        # Recopilar datos disponibles para generar un análisis completo
        symbol = signal_data.get("symbol", "N/A")
        price = signal_data.get("price", "N/A")
        direction = signal_data.get("direction", "N/A")
        confidence = signal_data.get("confidence_level", "N/A")
        timeframe = signal_data.get("timeframe", "N/A")
        strategy = signal_data.get("strategy", "N/A")
        category = signal_data.get("category", "N/A")
        analysis = signal_data.get("analysis", "N/A")
        technical_analysis = signal_data.get("technical_analysis", "N/A")
        support = signal_data.get("support_level", "N/A")
        resistance = signal_data.get("resistance_level", "N/A")
        rsi = signal_data.get("rsi", "N/A")
        trend = signal_data.get("trend", "N/A")
        trend_strength = signal_data.get("trend_strength", "N/A")
        volatility = signal_data.get("volatility", "N/A")
        options_signal = signal_data.get("options_signal", "N/A")
        options_analysis = signal_data.get("options_analysis", "N/A")
        sentiment = signal_data.get("sentiment", "N/A")
        sentiment_score = signal_data.get("sentiment_score", "N/A")
        latest_news = signal_data.get("latest_news", "N/A")

        # Crear prompt para generar análisis experto
        prompt = f"""Genera un análisis experto detallado para la señal de trading de {symbol} basado en los siguientes datos:

- Símbolo: {symbol}
- Precio: {price}
- Dirección: {direction}
- Nivel de confianza: {confidence}
- Marco temporal: {timeframe}
- Estrategia: {strategy}
- Categoría: {category}
- Soporte: {support}
- Resistencia: {resistance}
- RSI: {rsi}
- Tendencia: {trend}
- Fuerza de tendencia: {trend_strength}
- Volatilidad: {volatility}
- Señal de opciones: {options_signal}
- Sentimiento: {sentiment}
- Puntuación de sentimiento: {sentiment_score}
- Últimas noticias: {latest_news}

Análisis técnico disponible: {technical_analysis}

El análisis experto debe:
1. Comenzar con una evaluación general del activo y su posición actual en el mercado
2. Analizar los indicadores técnicos y fundamentales más relevantes
3. Evaluar el contexto macroeconómico y sectorial
4. Proporcionar una justificación clara para la dirección de la señal ({direction})
5. Identificar los principales catalizadores que podrían afectar al precio
6. Incluir consideraciones sobre la gestión de riesgos
7. Estar escrito en español profesional y objetivo
8. Tener entre 200-300 palabras
9. Estructurar el análisis con encabezados claros (EVALUACIÓN GENERAL, ANÁLISIS TÉCNICO, CATALIZADORES, RECOMENDACIÓN)
10. NO incluir frases genéricas de introducción o cierre"""

        # Generar análisis
        analysis = ai_expert.process_text(prompt, max_tokens=600)

        # Verificar si el análisis contiene parte del prompt (caso de fallback)
        prompt_fragments = [
            "Genera un análisis experto",
            "El análisis experto debe",
            "basado en los siguientes datos",
        ]

        if not analysis or contains_prompt_text(analysis, prompt_fragments):
            logger.warning(
                "El análisis experto generado contiene parte del prompt o está vacío."
            )
            return None

        # Limpiar análisis
        analysis = clean_text(analysis)

        # Verificar que el análisis tenga una longitud mínima
        if len(analysis) < 100:
            logger.warning(f"Análisis experto demasiado corto: {analysis}")
            return None

        return analysis
    except Exception as e:
        logger.error(f"Error generando análisis experto con IA: {str(e)}")
        return None


if __name__ == "__main__":
    # Pruebas básicas
    if AI_EXPERT_AVAILABLE:
        print("Prueba de generación de resumen:")
        summary = generate_summary_with_ai(
            "Apple reports record revenue in Q3 despite supply chain challenges", "AAPL"
        )
        print(f"Resumen generado: {summary}")

        print("\nPrueba de generación de análisis de sentimiento:")
        sentiment_data = {
            "overall": "Positivo",
            "vix": "18.5 (Bajo)",
            "sp500_trend": "Alcista",
            "technical_indicators": "RSI: 65, MACD: Positivo",
        }
        analysis = generate_sentiment_analysis_with_ai(sentiment_data)
        print(f"Análisis generado: {analysis[:100]}...")

        print("\nPrueba de generación de análisis técnico:")
        price_data = {
            "current_price": "185.92",
            "change_percent": "+1.5%",
            "volume": "75.3M",
            "ma_50": "180.45",
            "ma_200": "170.20",
            "rsi": "62",
        }
        tech_analysis = generate_technical_analysis_with_ai("AAPL", price_data)
        print(f"Análisis técnico generado: {tech_analysis[:100]}...")

        print("\nPrueba de generación de análisis experto para señal de trading:")
        signal_data = {
            "symbol": "AAPL",
            "price": "185.92",
            "direction": "CALL",
            "confidence_level": "Alta",
            "timeframe": "Medio Plazo",
            "strategy": "Tendencia",
            "category": "Tecnología",
            "support_level": "180.45",
            "resistance_level": "190.20",
            "rsi": "62",
            "trend": "ALCISTA",
            "trend_strength": "Fuerte",
            "volatility": "Baja",
            "options_signal": "CALL",
            "sentiment": "Positivo",
            "sentiment_score": "0.75",
            "latest_news": "Apple reports record revenue in Q3 despite supply chain challenges",
        }
        expert_analysis = generate_trading_signal_analysis_with_ai(signal_data)
        print(f"Análisis experto generado: {expert_analysis[:100]}...")
    else:
        print("AIExpert no está disponible. No se pueden realizar pruebas.")
