#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar y procesar la calidad de los datos después de la grabación de señales, noticias y sentimiento.
Este script debe ser llamado después de cada proceso de grabación para asegurar que no queden campos vacíos.
"""

import sys
import logging
import argparse
import time
from datetime import datetime
from typing import Dict
import mysql.connector
import toml
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# Importar módulo de credenciales de OpenAI
try:
    from openai_credentials import (
        OPENAI_API_KEY,
        OPENAI_API_MODEL,
        initialize_openai_client,
    )

    logger.info("Módulo de credenciales de OpenAI importado correctamente")
    OPENAI_CREDENTIALS_AVAILABLE = True
except ImportError:
    logger.warning("No se pudo importar el módulo de credenciales de OpenAI")
    OPENAI_CREDENTIALS_AVAILABLE = False


# Cargar configuración de OpenAI
def load_openai_config():
    """
    Carga la configuración de OpenAI

    Returns:
        dict: Configuración de OpenAI
    """
    if OPENAI_CREDENTIALS_AVAILABLE:
        return {"api_key": OPENAI_API_KEY, "model": OPENAI_API_MODEL}
    else:
        # Fallback al método anterior
        try:
            secrets_path = os.path.join(".streamlit", "secrets.toml")
            if os.path.exists(secrets_path):
                secrets = toml.load(secrets_path)

                # Buscar la API key en diferentes ubicaciones
                api_key = None
                if "OPENAI_API_KEY" in secrets:
                    api_key = secrets["OPENAI_API_KEY"]
                elif "openai" in secrets and "api_key" in secrets["openai"]:
                    api_key = secrets["openai"]["api_key"]
                elif "api_keys" in secrets and "OPENAI_API_KEY" in secrets["api_keys"]:
                    api_key = secrets["api_keys"]["OPENAI_API_KEY"]

                # Buscar el modelo en diferentes ubicaciones
                model = "gpt-4.1-nano"
                if "OPENAI_API_MODEL" in secrets:
                    model = secrets["OPENAI_API_MODEL"]
                elif "openai" in secrets and "model" in secrets["openai"]:
                    model = secrets["openai"]["model"]
                elif (
                    "api_keys" in secrets and "OPENAI_API_MODEL" in secrets["api_keys"]
                ):
                    model = secrets["api_keys"]["OPENAI_API_MODEL"]

                return {"api_key": api_key, "model": model}
            else:
                logger.warning(f"No se encontró el archivo {secrets_path}")
                return {}
        except Exception as e:
            logger.error(f"Error cargando configuración de OpenAI: {str(e)}")
            return {}


# Importar módulos propios
from database_quality_utils import (
    load_db_config,
    connect_to_db,
    get_empty_news_summaries,
    get_empty_sentiment_analysis,
    update_news_summary,
    update_news_title,
    update_news_url,
    update_sentiment_analysis,
    get_empty_trading_signals_analysis,
    get_error_trading_signals_analysis,
    update_trading_signal_analysis,
    get_empty_news_symbols,
)
from text_processing import translate_title_to_spanish
from data_enrichment import get_news_from_yahoo


# Función para generar análisis de respaldo para señales de trading
def generate_fallback_analysis(signal_data: dict) -> str:
    """Genera un análisis básico de respaldo para una señal de trading"""
    symbol = signal_data.get("symbol", "desconocido")
    direction = signal_data.get("direction", "NEUTRAL")
    price = signal_data.get("price", 0.0)
    confidence = signal_data.get("confidence_level", "Media")

    # Crear un análisis básico con la información disponible
    basic_analysis = f"Análisis experto para {symbol}: "

    if direction == "CALL":
        basic_analysis += (
            f"Se observa una señal ALCISTA con nivel de confianza {confidence}. "
        )
        basic_analysis += (
            f"El precio actual de {price} muestra potencial de crecimiento. "
        )
        if confidence == "Alta":
            basic_analysis += "Se recomienda considerar una posición de compra con stop loss ajustado. "
        else:
            basic_analysis += (
                "Se sugiere esperar confirmación adicional antes de tomar posiciones. "
            )
    elif direction == "PUT":
        basic_analysis += (
            f"Se observa una señal BAJISTA con nivel de confianza {confidence}. "
        )
        basic_analysis += f"El precio actual de {price} muestra signos de debilidad. "
        if confidence == "Alta":
            basic_analysis += "Se recomienda considerar una posición de venta con stop loss ajustado. "
        else:
            basic_analysis += (
                "Se sugiere esperar confirmación adicional antes de tomar posiciones. "
            )
    else:
        basic_analysis += "La señal actual es NEUTRAL. Se recomienda esperar a una mejor configuración de mercado. "

    basic_analysis += "Este análisis fue generado automáticamente como respaldo."

    logger.info(f"Generado análisis básico de respaldo para {symbol}")
    return basic_analysis


# Intentar importar funciones de generación de contenido con IA
try:
    from ai_content_generator import (
        generate_summary_with_ai,
        generate_sentiment_analysis_with_ai,
        generate_trading_signal_analysis_with_ai,
    )

    AI_CONTENT_GENERATOR_AVAILABLE = True
except ImportError:
    logger.warning(
        "No se pudo importar ai_content_generator. Se usarán funciones de respaldo."
    )
    AI_CONTENT_GENERATOR_AVAILABLE = False

    # Funciones de respaldo para generar contenido con IA
    def generate_summary_with_ai(title: str, symbol: str, url: str = None) -> str:
        """Función de respaldo para generar resumen de noticia"""
        try:
            # Cargar configuración de OpenAI
            config = load_openai_config()
            api_key = config.get("api_key")
            model = config.get("model", "gpt-4.1-nano")

            if not api_key:
                logger.warning("No se encontró la API key de OpenAI")
                return f"Resumen generado automáticamente para la noticia: {title}"

            # Inicializar cliente de OpenAI
            try:
                if OPENAI_CREDENTIALS_AVAILABLE:
                    client = initialize_openai_client()
                else:
                    import openai

                    openai.api_key = api_key
                    client = openai.OpenAI(api_key=api_key)

                if client:
                    logger.info("Cliente OpenAI inicializado correctamente")
                else:
                    logger.warning("No se pudo inicializar el cliente OpenAI")
                    return f"Resumen generado automáticamente para la noticia: {title}"
            except Exception as e:
                logger.warning(f"Error inicializando cliente OpenAI: {str(e)}")
                return f"Resumen generado automáticamente para la noticia: {title}"

            # Crear prompt para generar el resumen
            prompt = f"Genera un resumen detallado en español para la siguiente noticia financiera sobre {symbol}. "
            prompt += f"Título: {title}. "
            if url:
                prompt += f"URL: {url}. "
            prompt += "El resumen debe ser informativo, objetivo y enfocado en los aspectos financieros relevantes para inversores."

            # Generar resumen con OpenAI
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un analista financiero experto especializado en resumir noticias del mercado.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=500,
                )

                summary = response.choices[0].message.content.strip()
                logger.info(
                    f"Resumen generado correctamente para {symbol}: {summary[:50]}..."
                )
                return summary
            except Exception as e:
                logger.warning(f"Error generando resumen con OpenAI: {str(e)}")
                return f"Resumen generado automáticamente para la noticia: {title}"
        except Exception as e:
            logger.error(f"Error en generate_summary_with_ai: {str(e)}")
            return f"Resumen generado automáticamente para la noticia: {title}"

    def generate_sentiment_analysis_with_ai(sentiment_data: dict) -> str:
        """Función de respaldo para generar análisis de sentimiento"""
        try:
            # Cargar configuración de OpenAI
            config = load_openai_config()
            api_key = config.get("api_key")
            model = config.get("model", "gpt-4.1-nano")

            if not api_key:
                logger.warning("No se encontró la API key de OpenAI")
                return "Análisis de sentimiento de mercado generado automáticamente."

            # Inicializar cliente de OpenAI
            try:
                if OPENAI_CREDENTIALS_AVAILABLE:
                    client = initialize_openai_client()
                else:
                    import openai

                    openai.api_key = api_key
                    client = openai.OpenAI(api_key=api_key)

                if client:
                    logger.info("Cliente OpenAI inicializado correctamente")
                else:
                    logger.warning("No se pudo inicializar el cliente OpenAI")
                    return (
                        "Análisis de sentimiento de mercado generado automáticamente."
                    )
            except Exception as e:
                logger.warning(f"Error inicializando cliente OpenAI: {str(e)}")
                return "Análisis de sentimiento de mercado generado automáticamente."

            # Crear prompt para generar el análisis
            prompt = "Genera un análisis detallado del sentimiento de mercado basado en los siguientes datos:\n"
            prompt += (
                f"Sentimiento general: {sentiment_data.get('overall', 'Neutral')}\n"
            )
            prompt += f"VIX: {sentiment_data.get('vix', 'N/A')}\n"
            prompt += f"Tendencia S&P 500: {sentiment_data.get('sp500_trend', 'N/A')}\n"
            prompt += f"Indicadores técnicos: {sentiment_data.get('technical_indicators', 'N/A')}\n"
            prompt += f"Volumen: {sentiment_data.get('volume', 'N/A')}\n"
            prompt += f"Notas: {sentiment_data.get('notes', '')}\n"
            prompt += "El análisis debe ser detallado, objetivo y enfocado en los aspectos relevantes para inversores."

            # Generar análisis con OpenAI
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un analista financiero experto especializado en interpretar el sentimiento del mercado.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=500,
                )

                analysis = response.choices[0].message.content.strip()
                logger.info(
                    f"Análisis de sentimiento generado correctamente: {analysis[:50]}..."
                )
                return analysis
            except Exception as e:
                logger.warning(f"Error generando análisis con OpenAI: {str(e)}")
                return "Análisis de sentimiento de mercado generado automáticamente."
        except Exception as e:
            logger.error(f"Error en generate_sentiment_analysis_with_ai: {str(e)}")
            return "Análisis de sentimiento de mercado generado automáticamente."

    def generate_trading_signal_analysis_with_ai(signal_data: dict) -> str:
        """Función de respaldo para generar análisis experto para una señal de trading"""
        # Verificar si hay un error previo relacionado con progress_bars
        error_message = signal_data.get("expert_analysis", "")
        if error_message and "st.session_state has no attribute" in error_message:
            logger.warning(f"Detectado error previo de session_state: {error_message}")
            # Generar un análisis básico basado en los datos disponibles
            symbol = signal_data.get("symbol", "desconocido")
            direction = signal_data.get("direction", "NEUTRAL")
            price = signal_data.get("price", 0.0)
            confidence = signal_data.get("confidence_level", "Media")

            # Crear un análisis básico con la información disponible
            basic_analysis = f"Análisis experto para {symbol}: "

            if direction == "CALL":
                basic_analysis += f"Se observa una señal ALCISTA con nivel de confianza {confidence}. "
                basic_analysis += (
                    f"El precio actual de {price} muestra potencial de crecimiento. "
                )
                if confidence == "Alta":
                    basic_analysis += "Se recomienda considerar una posición de compra con stop loss ajustado. "
                else:
                    basic_analysis += "Se sugiere esperar confirmación adicional antes de tomar posiciones. "
            elif direction == "PUT":
                basic_analysis += f"Se observa una señal BAJISTA con nivel de confianza {confidence}. "
                basic_analysis += (
                    f"El precio actual de {price} muestra signos de debilidad. "
                )
                if confidence == "Alta":
                    basic_analysis += "Se recomienda considerar una posición de venta con stop loss ajustado. "
                else:
                    basic_analysis += "Se sugiere esperar confirmación adicional antes de tomar posiciones. "
            else:
                basic_analysis += "La señal actual es NEUTRAL. Se recomienda esperar a una mejor configuración de mercado. "

            basic_analysis += "Este análisis fue generado automáticamente como respaldo debido a un error en el sistema de IA."

            logger.info(f"Generado análisis básico de respaldo para {symbol}")
            return basic_analysis

        try:
            # Cargar configuración de OpenAI
            config = load_openai_config()
            api_key = config.get("api_key")
            model = config.get("model", "gpt-4.1-nano")

            if not api_key:
                logger.warning("No se encontró la API key de OpenAI")
                return generate_fallback_analysis(signal_data)

            # Inicializar cliente de OpenAI
            try:
                if OPENAI_CREDENTIALS_AVAILABLE:
                    client = initialize_openai_client()
                else:
                    import openai

                    openai.api_key = api_key
                    client = openai.OpenAI(api_key=api_key)

                if client:
                    logger.info("Cliente OpenAI inicializado correctamente")
                else:
                    logger.warning("No se pudo inicializar el cliente OpenAI")
                    return generate_fallback_analysis(signal_data)
            except Exception as e:
                logger.warning(f"Error inicializando cliente OpenAI: {str(e)}")
                return generate_fallback_analysis(signal_data)

            # Crear prompt para generar el análisis
            symbol = signal_data.get("symbol", "")
            direction = signal_data.get("direction", "")
            price = signal_data.get("price", 0.0)
            confidence = signal_data.get("confidence_level", "")
            strategy = signal_data.get("strategy", "")

            prompt = f"Genera un análisis experto detallado para la siguiente señal de trading:\n"
            prompt += f"Símbolo: {symbol}\n"
            prompt += f"Dirección: {direction}\n"
            prompt += f"Precio: {price}\n"
            prompt += f"Nivel de confianza: {confidence}\n"
            prompt += f"Estrategia: {strategy}\n"

            # Agregar información adicional si está disponible
            if signal_data.get("entry_price"):
                prompt += f"Precio de entrada: {signal_data.get('entry_price')}\n"
            if signal_data.get("stop_loss"):
                prompt += f"Stop loss: {signal_data.get('stop_loss')}\n"
            if signal_data.get("take_profit") or signal_data.get("target_price"):
                target = signal_data.get("take_profit") or signal_data.get(
                    "target_price"
                )
                prompt += f"Take profit/Target: {target}\n"
            if signal_data.get("risk_reward"):
                prompt += f"Riesgo/Recompensa: {signal_data.get('risk_reward')}\n"
            if signal_data.get("expiration_date"):
                prompt += f"Fecha de expiración: {signal_data.get('expiration_date')}\n"
            if signal_data.get("market_sentiment") or signal_data.get("sentiment"):
                sentiment = signal_data.get("market_sentiment") or signal_data.get(
                    "sentiment", "neutral"
                )
                prompt += f"Sentimiento de mercado: {sentiment}\n"
            if signal_data.get("technical_indicators") or signal_data.get(
                "technical_analysis"
            ):
                tech_indicators = signal_data.get(
                    "technical_indicators"
                ) or signal_data.get("technical_analysis", "")
                prompt += f"Indicadores técnicos: {tech_indicators}\n"
            if signal_data.get("fundamental_analysis"):
                prompt += (
                    f"Análisis fundamental: {signal_data.get('fundamental_analysis')}\n"
                )
            if signal_data.get("latest_news"):
                prompt += f"Últimas noticias: {signal_data.get('latest_news')}\n"

            prompt += "El análisis debe ser detallado, objetivo y enfocado en los aspectos relevantes para inversores. Incluye recomendaciones específicas y justificación técnica."

            # Generar análisis con OpenAI
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un trader profesional experto en análisis técnico y fundamental de mercados financieros.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=800,
                )

                analysis = response.choices[0].message.content.strip()
                logger.info(
                    f"Análisis experto generado correctamente para {symbol}: {analysis[:50]}..."
                )
                return analysis
            except Exception as e:
                logger.warning(f"Error generando análisis experto con OpenAI: {str(e)}")
                return generate_fallback_analysis(signal_data)
        except Exception as e:
            logger.error(f"Error en generate_trading_signal_analysis_with_ai: {str(e)}")
            return generate_fallback_analysis(signal_data)


def check_database_quality(
    connection: mysql.connector.MySQLConnection,
) -> Dict[str, int]:
    """
    Verifica la calidad de los datos en la base de datos

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos

    Returns:
        Dict[str, int]: Diccionario con el número de registros con campos vacíos por tabla
    """
    result = {}

    # Verificar noticias con resumen vacío
    empty_news = get_empty_news_summaries(connection, limit=1000)
    result["empty_news_summaries"] = len(empty_news) if empty_news else 0

    # Verificar noticias marcadas para revisión
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as count FROM market_news WHERE symbol = 'REVIEW'")
    review_news = cursor.fetchone()
    result["news_for_review"] = review_news["count"] if review_news else 0
    cursor.close()

    # Verificar sentimiento con análisis vacío
    empty_sentiment = get_empty_sentiment_analysis(connection, limit=1000)
    result["empty_sentiment_analysis"] = len(empty_sentiment) if empty_sentiment else 0

    # Verificar señales de trading con análisis experto vacío
    empty_signals = get_empty_trading_signals_analysis(connection, limit=1000)
    result["empty_trading_signals_analysis"] = (
        len(empty_signals) if empty_signals else 0
    )

    # Verificar señales de trading con errores en el análisis experto
    error_signals = get_error_trading_signals_analysis(connection, limit=1000)
    result["error_trading_signals_analysis"] = (
        len(error_signals) if error_signals else 0
    )

    return result


def process_empty_news_summaries(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> int:
    """
    Procesa noticias con resumen vacío

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a procesar

    Returns:
        int: Número de registros procesados
    """
    # Obtener noticias con resumen vacío
    empty_news = get_empty_news_summaries(connection, limit)

    if not empty_news:
        logger.info("No hay noticias con resumen vacío para procesar")
        return 0

    logger.info(f"Se encontraron {len(empty_news)} noticias con resumen vacío")

    # Procesar cada noticia
    processed_count = 0
    for news in empty_news:
        news_id = news.get("id")
        title = news.get("title", "")
        symbol = news.get("symbol", "SPY")
        url = news.get("url", "")

        logger.info(f"Procesando noticia ID {news_id}: {title[:50]}...")

        # Traducir título si está en inglés
        original_title = title
        translated_title = translate_title_to_spanish(title)
        if translated_title != original_title:
            logger.info(f"Título traducido: {translated_title}")

            # Actualizar título en la base de datos
            if update_news_title(connection, news_id, translated_title):
                logger.info(f"Título actualizado para noticia ID {news_id}")

                # Usar el título traducido para generar el resumen
                title = translated_title
            else:
                logger.error(f"Error actualizando título para noticia ID {news_id}")

        # Intentar obtener noticias de Yahoo Finance si no hay URL
        if not url:
            yahoo_news = get_news_from_yahoo(symbol, 1)
            if yahoo_news:
                # Usar la primera noticia como referencia
                url = yahoo_news[0].get("url", "")
                logger.info(f"URL obtenida de Yahoo Finance: {url}")

                # Actualizar URL en la base de datos
                if update_news_url(connection, news_id, url):
                    logger.info(f"URL actualizada para noticia ID {news_id}")
                else:
                    logger.error(f"Error actualizando URL para noticia ID {news_id}")

        # Generar resumen con IA
        summary = generate_summary_with_ai(title, symbol, url)

        # Actualizar resumen en la base de datos solo si se generó un resumen válido
        if summary is not None:
            if update_news_summary(connection, news_id, summary):
                logger.info(f"Resumen actualizado para noticia ID {news_id}")
                processed_count += 1
            else:
                logger.error(f"Error actualizando resumen para noticia ID {news_id}")
        else:
            logger.warning(
                f"No se pudo generar un resumen válido para la noticia ID {news_id}"
            )

        # Esperar un poco para no sobrecargar la API
        time.sleep(1)

    return processed_count


def process_empty_sentiment_analysis(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> int:
    """
    Procesa registros de sentimiento con campos críticos vacíos

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a procesar

    Returns:
        int: Número de registros procesados
    """
    # Obtener registros de sentimiento con campos críticos vacíos
    empty_sentiment = get_empty_sentiment_analysis(connection, limit)

    if not empty_sentiment:
        logger.info(
            "No hay registros de sentimiento con campos críticos vacíos para procesar"
        )
        return 0

    logger.info(
        f"Se encontraron {len(empty_sentiment)} registros de sentimiento con campos críticos vacíos"
    )

    # Procesar cada registro
    processed_count = 0
    for sentiment in empty_sentiment:
        sentiment_id = sentiment.get("id")

        logger.info(f"Procesando sentimiento ID {sentiment_id}...")

        # Verificar qué campos están vacíos
        fields_to_update = {}

        # Verificar si el análisis está vacío
        if not sentiment.get("analysis"):
            # Generar análisis con IA
            analysis = generate_sentiment_analysis_with_ai(sentiment)
            if analysis is not None:
                fields_to_update["analysis"] = analysis

        # Verificar si el símbolo está vacío
        if not sentiment.get("symbol"):
            # Usar SPY como valor predeterminado o determinar el símbolo basado en otros campos
            fields_to_update["symbol"] = "SPY"

        # Verificar si el sentimiento está vacío
        if not sentiment.get("sentiment"):
            # Determinar el sentimiento basado en overall o usar un valor predeterminado
            overall = sentiment.get("overall")
            if overall == "Alcista":
                fields_to_update["sentiment"] = "Positivo"
            elif overall == "Bajista":
                fields_to_update["sentiment"] = "Negativo"
            else:
                fields_to_update["sentiment"] = "Neutral"

        # Verificar si el score está vacío
        if sentiment.get("score") is None:
            # Asignar un score basado en overall o usar un valor predeterminado
            overall = sentiment.get("overall")
            if overall == "Alcista":
                fields_to_update["score"] = 0.75
            elif overall == "Bajista":
                fields_to_update["score"] = 0.25
            else:
                fields_to_update["score"] = 0.5

        # Verificar si la fuente está vacía
        if not sentiment.get("source"):
            fields_to_update["source"] = "InversorIA AI"

        # Verificar si la fecha del sentimiento está vacía
        if not sentiment.get("sentiment_date"):
            # Usar la fecha actual
            fields_to_update["sentiment_date"] = sentiment.get(
                "date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        # Actualizar los campos en la base de datos
        if fields_to_update:
            if update_sentiment_analysis(
                connection,
                sentiment_id,
                analysis=fields_to_update.get("analysis"),
                symbol=fields_to_update.get("symbol"),
                sentiment_value=fields_to_update.get("sentiment"),
                score=fields_to_update.get("score"),
                source=fields_to_update.get("source"),
                sentiment_date=fields_to_update.get("sentiment_date"),
            ):
                logger.info(
                    f"Campos actualizados para sentimiento ID {sentiment_id}: {', '.join(fields_to_update.keys())}"
                )
                processed_count += 1
            else:
                logger.error(
                    f"Error actualizando campos para sentimiento ID {sentiment_id}"
                )
        else:
            logger.info(
                f"No hay campos para actualizar en el sentimiento ID {sentiment_id}"
            )

        # Esperar un poco para no sobrecargar la API
        time.sleep(1)

    return processed_count


def process_empty_trading_signals_analysis(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> int:
    """
    Procesa señales de trading con análisis experto vacío o con errores

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a procesar

    Returns:
        int: Número de registros procesados
    """
    # Obtener señales de trading con análisis experto vacío
    empty_signals = get_empty_trading_signals_analysis(connection, limit)

    # Obtener señales con errores en el análisis experto
    error_signals = get_error_trading_signals_analysis(connection, limit)

    # Combinar ambas listas, eliminando duplicados por ID
    all_signals = {signal.get("id"): signal for signal in empty_signals}
    for signal in error_signals:
        if signal.get("id") not in all_signals:
            all_signals[signal.get("id")] = signal

    signals_to_process = list(all_signals.values())

    if not signals_to_process:
        logger.info(
            "No hay señales de trading con análisis experto vacío o con errores para procesar"
        )
        return 0

    logger.info(
        f"Se encontraron {len(signals_to_process)} señales de trading con análisis experto vacío o con errores"
    )

    # Procesar cada señal
    processed_count = 0
    for signal in signals_to_process:
        signal_id = signal.get("id")

        logger.info(f"Procesando señal ID {signal_id}...")

        # Verificar si hay un error en el análisis experto
        expert_analysis = signal.get("expert_analysis", "")
        if expert_analysis and "st.session_state has no attribute" in expert_analysis:
            logger.warning(
                f"Se detectó un error en el análisis experto de la señal ID {signal_id}: {expert_analysis[:100]}..."
            )

        # Generar análisis con IA
        analysis = generate_trading_signal_analysis_with_ai(signal)

        # Actualizar análisis en la base de datos solo si se generó un análisis válido
        if analysis is not None:
            if update_trading_signal_analysis(connection, signal_id, analysis):
                logger.info(f"Análisis experto actualizado para señal ID {signal_id}")
                processed_count += 1
            else:
                logger.error(
                    f"Error actualizando análisis experto para señal ID {signal_id}"
                )
        else:
            logger.warning(
                f"No se pudo generar un análisis válido para la señal ID {signal_id}"
            )

        # Esperar un poco para no sobrecargar la API
        time.sleep(1)

    return processed_count


def process_quality_after_save(
    table_name: str = "all", limit: int = 10
) -> Dict[str, int]:
    """
    Procesa la calidad de los datos después de guardar registros

    Args:
        table_name (str): Nombre de la tabla a procesar (news, sentiment, signals o all)
        limit (int): Número máximo de registros a procesar por tabla

    Returns:
        Dict[str, int]: Diccionario con el número de registros procesados por tabla
    """
    result = {"news_processed": 0, "sentiment_processed": 0, "signals_processed": 0}

    # Intentar importar streamlit para mostrar mensajes de progreso
    try:
        import streamlit as st

        has_streamlit = True
        # Crear un contenedor para mostrar el progreso
        quality_container = st.empty()
        quality_container.info("⏳ Iniciando control de calidad de datos...")
    except ImportError:
        has_streamlit = False
        quality_container = None

    try:
        # Cargar configuración
        db_config = load_db_config()

        # Mostrar mensaje de progreso
        if has_streamlit:
            quality_container.info("⏳ Conectando a la base de datos...")

        # Conectar a la base de datos
        connection = connect_to_db(db_config)
        if not connection:
            logger.error("No se pudo conectar a la base de datos")
            if has_streamlit:
                quality_container.error(
                    "❌ Error: No se pudo conectar a la base de datos"
                )
                # Limpiar el contenedor después de 3 segundos
                import time

                time.sleep(3)
                quality_container.empty()
            return result

        # Verificar la calidad de los datos
        if has_streamlit:
            quality_container.info("⏳ Analizando calidad de los datos...")

        quality_stats = check_database_quality(connection)

        # Mostrar estadísticas de calidad
        logger.info("=" * 80)
        logger.info("ESTADÍSTICAS DE CALIDAD DE DATOS")
        logger.info("=" * 80)
        logger.info(
            f"Noticias con resumen vacío: {quality_stats['empty_news_summaries']}"
        )
        if "news_for_review" in quality_stats:
            logger.info(
                f"Noticias marcadas para revisión: {quality_stats['news_for_review']}"
            )
            if quality_stats["news_for_review"] > 0:
                logger.warning(
                    "Ejecute 'python review_news_symbols.py' para revisar y asignar símbolos correctos."
                )
        logger.info(
            f"Registros de sentimiento con análisis vacío: {quality_stats['empty_sentiment_analysis']}"
        )
        logger.info(
            f"Señales de trading con análisis experto vacío: {quality_stats['empty_trading_signals_analysis']}"
        )
        if "error_trading_signals_analysis" in quality_stats:
            logger.info(
                f"Señales de trading con errores en el análisis: {quality_stats['error_trading_signals_analysis']}"
            )
        logger.info("=" * 80)

        # Procesar los datos según la tabla seleccionada
        if table_name in ["news", "all"] and quality_stats["empty_news_summaries"] > 0:
            # Procesar noticias con resumen vacío
            if has_streamlit:
                quality_container.info("⏳ Procesando noticias con resumen vacío...")

            result["news_processed"] = process_empty_news_summaries(connection, limit)
            logger.info(
                f"Se procesaron {result['news_processed']} noticias con resumen vacío"
            )

            if has_streamlit and result["news_processed"] > 0:
                quality_container.success(
                    f"✅ Se completaron {result['news_processed']} resúmenes de noticias"
                )

        # Procesar noticias con símbolos marcados para revisión
        if (
            table_name in ["news", "all"]
            and quality_stats.get("news_for_review", 0) > 0
        ):
            try:
                # Intentar procesar automáticamente con IA avanzada
                if has_streamlit:
                    quality_container.info(
                        f"⏳ Procesando {quality_stats.get('news_for_review', 0)} noticias marcadas para revisión..."
                    )

                from review_news_symbols import batch_review
                import sys
                import os

                logger.info(
                    f"Procesando {quality_stats.get('news_for_review', 0)} noticias marcadas para revisión..."
                )

                # Ejecutar en modo silencioso (sin interacción con el usuario)
                original_stdout = sys.stdout
                sys.stdout = open(os.devnull, "w")
                batch_review(use_advanced_ai=True)
                sys.stdout = original_stdout

                # Verificar cuántas noticias quedan por revisar
                remaining = get_empty_news_symbols(connection, limit=1000)
                remaining_count = len(remaining) if remaining else 0

                if remaining_count > 0:
                    logger.warning(
                        f"Quedan {remaining_count} noticias que requieren revisión manual."
                    )
                    logger.warning(
                        "Ejecute 'python review_news_symbols.py' para revisar y asignar símbolos manualmente."
                    )

                    if has_streamlit:
                        quality_container.warning(
                            f"⚠️ Quedan {remaining_count} noticias que requieren revisión manual"
                        )
                else:
                    logger.info(
                        "Todas las noticias fueron procesadas correctamente con IA avanzada."
                    )

                    if has_streamlit:
                        quality_container.success(
                            "✅ Todas las noticias fueron procesadas correctamente"
                        )

                result["news_symbols_processed"] = (
                    quality_stats.get("news_for_review", 0) - remaining_count
                )
                result["news_symbols_remaining"] = remaining_count
            except Exception as e:
                logger.error(f"Error en la corrección automática de símbolos: {str(e)}")
                logger.warning(
                    "Ejecute 'python review_news_symbols.py' para revisar y asignar símbolos correctos."
                )

                if has_streamlit:
                    quality_container.error(
                        f"❌ Error en la corrección automática de símbolos: {str(e)}"
                    )

        if (
            table_name in ["sentiment", "all"]
            and quality_stats["empty_sentiment_analysis"] > 0
        ):
            # Procesar registros de sentimiento con análisis vacío
            if has_streamlit:
                quality_container.info(
                    "⏳ Procesando registros de sentimiento de mercado..."
                )

            result["sentiment_processed"] = process_empty_sentiment_analysis(
                connection, limit
            )
            logger.info(
                f"Se procesaron {result['sentiment_processed']} registros de sentimiento con análisis vacío"
            )

            if has_streamlit and result["sentiment_processed"] > 0:
                quality_container.success(
                    f"✅ Se completaron {result['sentiment_processed']} análisis de sentimiento de mercado"
                )

        # Procesar señales de trading con análisis experto vacío o con errores
        if table_name in ["signals", "all"]:
            signals_to_process = False
            process_message = ""

            # Verificar si hay señales con análisis vacío
            if quality_stats["empty_trading_signals_analysis"] > 0:
                signals_to_process = True
                process_message = "análisis vacío"

            # Verificar si hay señales con errores en el análisis
            if (
                "error_trading_signals_analysis" in quality_stats
                and quality_stats["error_trading_signals_analysis"] > 0
            ):
                signals_to_process = True
                if process_message:
                    process_message += " o con errores"
                else:
                    process_message = "errores en el análisis"

            if signals_to_process:
                # Procesar señales de trading con análisis experto vacío o con errores
                if has_streamlit:
                    quality_container.info(
                        f"⏳ Procesando señales de trading con {process_message}..."
                    )

                result["signals_processed"] = process_empty_trading_signals_analysis(
                    connection, limit
                )
                logger.info(
                    f"Se procesaron {result['signals_processed']} señales de trading con {process_message}"
                )

                if has_streamlit and result["signals_processed"] > 0:
                    quality_container.success(
                        f"✅ Se completaron {result['signals_processed']} análisis expertos para señales de trading"
                    )

        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")

        # Mostrar resumen
        logger.info("=" * 80)
        logger.info("RESUMEN DE PROCESAMIENTO")
        logger.info("=" * 80)
        logger.info(f"Noticias con resumen procesadas: {result['news_processed']}")
        if "news_symbols_processed" in result:
            logger.info(
                f"Noticias con símbolos procesadas: {result['news_symbols_processed']}"
            )
        logger.info(
            f"Registros de sentimiento procesados: {result['sentiment_processed']}"
        )
        logger.info(f"Señales de trading procesadas: {result['signals_processed']}")
        logger.info("=" * 80)

        # Mostrar mensaje final
        total_processed = (
            result["news_processed"]
            + result.get("news_symbols_processed", 0)
            + result["sentiment_processed"]
            + result["signals_processed"]
        )
        if has_streamlit:
            if total_processed > 0:
                quality_container.success(
                    f"✅ Control de calidad completado: {total_processed} registros procesados"
                )
            else:
                quality_container.info(
                    "ℹ️ No se requirió procesamiento adicional de datos"
                )

            # Limpiar el contenedor después de 3 segundos
            import time

            time.sleep(3)
            quality_container.empty()

        return result
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")
        # Mostrar error
        if has_streamlit:
            quality_container.error(f"❌ Error en el control de calidad: {str(e)}")
            # Limpiar el contenedor después de 3 segundos
            import time

            time.sleep(3)
            quality_container.empty()
        return result


def main():
    """Función principal"""
    try:
        # Configurar argumentos de línea de comandos
        parser = argparse.ArgumentParser(description="Procesar calidad de datos")
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Número máximo de registros a procesar por tabla",
        )
        parser.add_argument(
            "--check-only",
            action="store_true",
            help="Solo verificar la calidad de los datos sin procesarlos",
        )
        parser.add_argument(
            "--table",
            type=str,
            choices=["news", "sentiment", "signals", "all"],
            default="all",
            help="Tabla a procesar (news, sentiment, signals o all)",
        )
        args = parser.parse_args()

        # Cargar configuración
        db_config = load_db_config()

        # Conectar a la base de datos
        connection = connect_to_db(db_config)
        if not connection:
            logger.error("No se pudo conectar a la base de datos")
            return

        # Verificar la calidad de los datos
        quality_stats = check_database_quality(connection)

        # Mostrar estadísticas de calidad
        print("\n" + "=" * 80)
        print("ESTADÍSTICAS DE CALIDAD DE DATOS")
        print("=" * 80)
        print(f"Noticias con resumen vacío: {quality_stats['empty_news_summaries']}")
        if "news_for_review" in quality_stats:
            print(
                f"Noticias marcadas para revisión: {quality_stats['news_for_review']}"
            )
            if quality_stats["news_for_review"] > 0:
                print(
                    "\033[93m⚠️  Ejecute 'python review_news_symbols.py' para revisar y asignar símbolos correctos.\033[0m"
                )
        print(
            f"Registros de sentimiento con análisis vacío: {quality_stats['empty_sentiment_analysis']}"
        )
        print(
            f"Señales de trading con análisis experto vacío: {quality_stats['empty_trading_signals_analysis']}"
        )
        print("=" * 80)

        # Si solo se quiere verificar la calidad, terminar aquí
        if args.check_only:
            logger.info("Modo de solo verificación. No se procesarán los datos.")
            connection.close()
            return

        # Procesar los datos según la tabla seleccionada
        news_processed = 0
        sentiment_processed = 0
        signals_processed = 0

        if args.table in ["news", "all"]:
            # Procesar noticias con resumen vacío
            news_processed = process_empty_news_summaries(connection, args.limit)
            logger.info(f"Se procesaron {news_processed} noticias con resumen vacío")

            # Procesar noticias con símbolos marcados para revisión
            if quality_stats.get("news_for_review", 0) > 0:
                try:
                    # Intentar procesar automáticamente con IA avanzada
                    from review_news_symbols import batch_review
                    import sys
                    import os

                    print(
                        f"\nProcesando {quality_stats.get('news_for_review', 0)} noticias marcadas para revisión..."
                    )

                    # Ejecutar en modo silencioso (sin interacción con el usuario)
                    original_stdout = sys.stdout
                    sys.stdout = open(os.devnull, "w")
                    batch_review(use_advanced_ai=True)
                    sys.stdout = original_stdout

                    # Verificar cuántas noticias quedan por revisar
                    remaining = get_empty_news_symbols(connection, limit=1000)
                    remaining_count = len(remaining) if remaining else 0

                    if remaining_count > 0:
                        print(
                            f"\033[93m⚠️  Quedan {remaining_count} noticias que requieren revisión manual.\033[0m"
                        )
                        print(
                            "\033[93m⚠️  Ejecute 'python review_news_symbols.py' para revisar y asignar símbolos manualmente.\033[0m"
                        )
                    else:
                        print(
                            "\033[92m✅ Todas las noticias fueron procesadas correctamente con IA avanzada.\033[0m"
                        )

                    news_symbols_processed = (
                        quality_stats.get("news_for_review", 0) - remaining_count
                    )
                    print(f"Símbolos de noticias procesados: {news_symbols_processed}")
                except Exception as e:
                    logger.error(
                        f"Error en la corrección automática de símbolos: {str(e)}"
                    )
                    print(
                        "\033[91m❌ Error en la corrección automática de símbolos.\033[0m"
                    )
                    print(
                        "\033[93m⚠️  Ejecute 'python review_news_symbols.py' para revisar y asignar símbolos correctos.\033[0m"
                    )

        if args.table in ["sentiment", "all"]:
            # Procesar registros de sentimiento con análisis vacío
            sentiment_processed = process_empty_sentiment_analysis(
                connection, args.limit
            )
            logger.info(
                f"Se procesaron {sentiment_processed} registros de sentimiento con análisis vacío"
            )

        if args.table in ["signals", "all"]:
            # Procesar señales de trading con análisis experto vacío o con errores
            process_message = ""

            # Verificar si hay señales con análisis vacío
            if quality_stats["empty_trading_signals_analysis"] > 0:
                process_message = "análisis vacío"

            # Verificar si hay señales con errores en el análisis
            if (
                "error_trading_signals_analysis" in quality_stats
                and quality_stats["error_trading_signals_analysis"] > 0
            ):
                if process_message:
                    process_message += " o con errores"
                else:
                    process_message = "errores en el análisis"

            signals_processed = process_empty_trading_signals_analysis(
                connection, args.limit
            )
            logger.info(
                f"Se procesaron {signals_processed} señales de trading con {process_message}"
            )

        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")

        # Mostrar resumen
        print("\n" + "=" * 80)
        print("RESUMEN DE PROCESAMIENTO")
        print("=" * 80)
        print(f"Noticias con resumen procesadas: {news_processed}")
        if "news_symbols_processed" in locals():
            print(f"Noticias con símbolos procesadas: {news_symbols_processed}")
        print(f"Registros de sentimiento procesados: {sentiment_processed}")
        print(f"Señales de trading procesadas: {signals_processed}")
        print("=" * 80)
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")


if __name__ == "__main__":
    main()
