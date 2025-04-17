"""
InversorIA Pro - Utilidades de IA
---------------------------------
Este archivo contiene funciones para procesar análisis de IA y formatear datos para prompts.
"""

import logging
import streamlit as st
import pandas as pd
import numpy as np
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Importar componentes personalizados
try:
    from market_utils import get_market_context
    from technical_analysis import (
        detect_support_resistance,
        detect_trend_lines,
        detect_candle_patterns,
    )
except Exception as e:
    logging.error(f"Error importando componentes: {str(e)}")

# Importar OpenAI si está disponible
try:
    import openai
except ImportError:
    logging.warning(
        "OpenAI no está instalado. Algunas funciones no estarán disponibles."
    )

logger = logging.getLogger(__name__)


def format_patterns_for_prompt(patterns, symbol, price=None):
    """Formatea los patrones técnicos para incluirlos en el prompt del asistente IA"""
    if not patterns:
        return "No se detectaron patrones técnicos significativos."

    formatted_text = f"PATRONES TÉCNICOS DETECTADOS PARA {symbol}:\n\n"

    if price:
        formatted_text += f"Precio actual: ${price:.2f}\n\n"

    # Soportes y resistencias
    if "supports" in patterns and patterns["supports"]:
        formatted_text += "SOPORTES DETECTADOS:\n"
        for level in patterns["supports"]:
            dist = ((level / price) - 1) * 100 if price else 0
            formatted_text += f"- ${level:.2f} ({dist:.2f}% desde precio actual)\n"
        formatted_text += "\n"

    if "resistances" in patterns and patterns["resistances"]:
        formatted_text += "RESISTENCIAS DETECTADAS:\n"
        for level in patterns["resistances"]:
            dist = ((level / price) - 1) * 100 if price else 0
            formatted_text += f"- ${level:.2f} ({dist:.2f}% desde precio actual)\n"
        formatted_text += "\n"

    # Líneas de tendencia
    if "trend_lines" in patterns:
        if "bullish" in patterns["trend_lines"] and patterns["trend_lines"]["bullish"]:
            formatted_text += "LÍNEAS DE TENDENCIA ALCISTAS:\n"
            for line in patterns["trend_lines"]["bullish"]:
                formatted_text += f"- Desde ${line[0]:.2f} hasta ${line[1]:.2f}\n"
            formatted_text += "\n"

        if "bearish" in patterns["trend_lines"] and patterns["trend_lines"]["bearish"]:
            formatted_text += "LÍNEAS DE TENDENCIA BAJISTAS:\n"
            for line in patterns["trend_lines"]["bearish"]:
                formatted_text += f"- Desde ${line[0]:.2f} hasta ${line[1]:.2f}\n"
            formatted_text += "\n"

    # Patrones de velas
    if "candle_patterns" in patterns and patterns["candle_patterns"]:
        formatted_text += "PATRONES DE VELAS JAPONESAS:\n"
        for pattern in patterns["candle_patterns"]:
            pattern_name = pattern.get("pattern", "Desconocido")
            pattern_type = pattern.get("type", "neutral")
            confidence = pattern.get("confidence", "media")

            # Determinar emoji según tipo de patrón
            emoji = (
                "🟢"
                if pattern_type == "bullish"
                else "🔴" if pattern_type == "bearish" else "⚪"
            )

            formatted_text += f"{emoji} {pattern_name} (Confianza: {confidence})\n"
        formatted_text += "\n"

    return formatted_text


def process_message_with_citations(message):
    """Extrae y devuelve el texto del mensaje del asistente con manejo mejorado de errores"""
    try:
        if hasattr(message, "content") and len(message.content) > 0:
            message_content = message.content[0]
            if hasattr(message_content, "text"):
                nested_text = message_content.text
                if hasattr(nested_text, "value"):
                    return nested_text.value
                elif isinstance(nested_text, str):
                    return nested_text
            elif isinstance(message_content, dict) and "text" in message_content:
                return message_content["text"].get("value", message_content["text"])
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")

    return "No se pudo procesar el mensaje del asistente"


def process_expert_analysis(client, assistant_id, symbol, context):
    """Procesa análisis experto con OpenAI asegurando una sección de análisis fundamental"""
    if not client or not assistant_id:
        return None

    # Formatear prompt para el asistente
    price = context.get("last_price", 0)
    change = context.get("change_percent", 0)
    vix_level = context.get("vix_level", "N/A")
    signals = context.get("signals", {})

    # Obtener señal general
    overall_signal = "NEUTRAL"
    if "overall" in signals:
        signal = signals["overall"]["signal"]
        if signal in ["compra", "compra_fuerte"]:
            overall_signal = "ALCISTA"
        elif signal in ["venta", "venta_fuerte"]:
            overall_signal = "BAJISTA"

    # Obtener señal de opciones
    option_signal = "NEUTRAL"
    if "options" in signals:
        signal = signals["options"].get("signal", "neutral")
        if signal in ["compra", "compra_fuerte"]:
            option_signal = "ALCISTA"
        elif signal in ["venta", "venta_fuerte"]:
            option_signal = "BAJISTA"

    # Extraer información fundamental si está disponible
    fundamentals = context.get("fundamentals", {})
    fundamentals_text = "No hay información fundamental disponible."
    if fundamentals:
        fundamentals_text = "DATOS FUNDAMENTALES:\n"
        for key, value in fundamentals.items():
            if key in ["pe_ratio", "eps", "market_cap", "dividend_yield"]:
                fundamentals_text += f"- {key}: {value}\n"

    # Extraer información de sentimiento si está disponible
    sentiment = context.get("news_sentiment", {})
    sentiment_text = "No hay información de sentimiento disponible."
    if sentiment:
        sentiment_score = sentiment.get("score", 0.5)
        sentiment_label = (
            "Positivo"
            if sentiment_score > 0.6
            else "Negativo" if sentiment_score < 0.4 else "Neutral"
        )
        sentiment_text = (
            f"SENTIMIENTO DE MERCADO: {sentiment_label} ({sentiment_score*100:.1f}%)\n"
        )
        if "sources" in sentiment:
            sentiment_text += "Fuentes de sentimiento:\n"
            for source in sentiment["sources"][:3]:  # Limitar a 3 fuentes
                sentiment_text += f"- {source.get('name', 'Desconocida')}: {source.get('sentiment', 'neutral')}\n"

    # Extraer información de noticias si está disponible
    news = context.get("news", [])
    news_text = "No hay noticias recientes disponibles."
    if news:
        news_text = "NOTICIAS RECIENTES:\n"
        for i, item in enumerate(news[:5]):  # Limitar a 5 noticias principales
            sentiment_indicator = ""
            if item.get("sentiment", 0.5) > 0.6:
                sentiment_indicator = "📈 [POSITIVA]"
            elif item.get("sentiment", 0.5) < 0.4:
                sentiment_indicator = "📉 [NEGATIVA]"

            news_text += f"{i+1}. {sentiment_indicator} {item.get('title', '')}\n"
            if item.get("summary"):
                news_text += f"   Resumen: {item.get('summary')[:150]}...\n"
            news_text += f"   Fuente: {item.get('source', 'Desconocida')}\n\n"

    # Extraer información de análisis web si está disponible
    web_insights = context.get("web_results", [])
    web_insights_text = "No hay análisis web disponible."
    if web_insights:
        web_insights_text = "ANÁLISIS DE MERCADO DE FUENTES WEB:\n"
        for i, insight in enumerate(web_insights[:3]):  # Limitar a 3 insights
            web_insights_text += f"{i+1}. {insight.get('title', 'Sin título')}\n"
            if insight.get("content"):
                web_insights_text += f"   {insight.get('content')[:200]}...\n"
            web_insights_text += (
                f"   Fuente: {insight.get('source', 'Desconocida')}\n\n"
            )

    # Detectar patrones técnicos
    patterns = {}
    chart_data = context.get("data", pd.DataFrame())

    if not chart_data.empty:
        try:
            supports, resistances = detect_support_resistance(chart_data)
            patterns["supports"] = supports
            patterns["resistances"] = resistances

            bullish_lines, bearish_lines = detect_trend_lines(chart_data)
            patterns["trend_lines"] = {
                "bullish": bullish_lines,
                "bearish": bearish_lines,
            }

            # Patrones de velas (últimas 20)
            candle_patterns = detect_candle_patterns(chart_data.tail(20))
            patterns["candle_patterns"] = candle_patterns

            # Formatear patrones para el prompt
            patterns_text = format_patterns_for_prompt(patterns, symbol, price)
        except Exception as e:
            logger.error(f"Error detectando patrones: {str(e)}")
            patterns_text = (
                "No se pudieron detectar patrones técnicos debido a un error."
            )
    else:
        patterns_text = "No hay datos de gráfico disponibles para detectar patrones."

    # Crear estructura para el análisis
    analysis_structure = """
## EVALUACIÓN GENERAL
(Evaluación general del activo, tendencia principal y contexto de mercado)

## ANÁLISIS TÉCNICO
(Análisis detallado de indicadores técnicos, patrones de precio y señales)

## NIVELES CLAVE
(Identificación de soportes, resistencias y niveles de precio importantes)

## ANÁLISIS FUNDAMENTAL
(Evaluación de factores fundamentales, noticias y sentimiento de mercado)

## ESTRATEGIAS RECOMENDADAS
(Estrategias de trading específicas con entradas, salidas y gestión de riesgo)

## ANÁLISIS DE RIESGO
(Evaluación de riesgos potenciales y factores a vigilar)

## PROYECCIÓN DE MOVIMIENTO
(Proyección de posibles escenarios de precio a corto y medio plazo)

## RECOMENDACIÓN FINAL: CALL/PUT/NEUTRAL
(Texto de recomendación final...)
"""

    # Crear contenido del prompt enriquecido con toda la información disponible
    prompt = f"""
    Como Especialista en Trading y Análisis Técnico Avanzado, realiza un análisis profesional integral del siguiente activo:

    SÍMBOLO: {symbol}

    DATOS DE MERCADO:
    - Precio actual: ${price:.2f} ({'+' if change > 0 else ''}{change:.2f}%)
    - VIX: {vix_level}
    - Señal técnica: {overall_signal}
    - Señal de opciones: {option_signal}

    INFORMACIÓN FUNDAMENTAL:
    {fundamentals_text}

    SENTIMIENTO DE MERCADO:
    {sentiment_text}

    NOTICIAS RELEVANTES:
    {news_text}

    ANÁLISIS DE ANALISTAS:
    {web_insights_text}

    PATRONES TÉCNICOS:
    {patterns_text}

    Estructura tu análisis siguiendo exactamente este formato:
    {analysis_structure}

    IMPORTANTE:
    - Sé específico con los niveles de precio y porcentajes
    - Incluye estrategias prácticas con puntos de entrada, salida y stop loss
    - Evalúa el riesgo/recompensa de forma cuantitativa
    - Concluye con una recomendación clara: CALL (alcista), PUT (bajista) o NEUTRAL
    - Mantén un tono profesional y objetivo
    """

    # Verificar si existe un thread en la sesión
    if "thread_id" not in st.session_state:
        # Crear un nuevo thread
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        logger.info(f"Nuevo thread creado: {thread.id}")

    try:
        # Enviar mensaje al thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=prompt
        )

        # Crear una ejecución para el thread
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=assistant_id
        )

        # Mostrar progreso
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Esperar a que se complete la ejecución con timeout
        start_time = time.time()
        timeout = 45  # 45 segundos máximo
        while run.status in ["queued", "in_progress"]:
            # Calcular progreso basado en tiempo transcurrido
            elapsed = time.time() - start_time
            progress = min(elapsed / timeout, 0.95)  # Máximo 95% hasta completar
            progress_bar.progress(progress)

            # Actualizar mensaje de estado
            status_text.text(f"Analizando {symbol}... ({run.status})")

            # Verificar timeout
            if elapsed > timeout:
                status_text.text(f"Tiempo de espera excedido, finalizando análisis...")
                break

            # Esperar un momento antes de verificar de nuevo
            time.sleep(1)

            # Actualizar estado de la ejecución
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id, run_id=run.id
            )

        # Completar barra de progreso
        progress_bar.progress(1.0)
        status_text.empty()

        if run.status != "completed":
            return f"Error: La consulta al experto falló con estado {run.status}"

        # Recuperar mensajes
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Obtener respuesta
        for message in messages:
            if message.run_id == run.id and message.role == "assistant":
                # Extraer texto del mensaje
                return process_message_with_citations(message)

        return "No se recibió respuesta del experto."

    except Exception as e:
        logger.error(f"Error al consultar al experto: {str(e)}")
        return f"Error al consultar al experto: {str(e)}"


def process_chat_input_with_openai(
    prompt, symbol=None, api_key=None, assistant_id=None, context=None
):
    """
    Procesa la entrada del chat utilizando OpenAI para respuestas más naturales y variadas.
    """
    try:
        # Si no se proporciona símbolo, intentar detectarlo en el mensaje
        if not symbol:
            # Aquí iría la lógica para detectar el símbolo en el mensaje
            if not symbol:
                symbol = st.session_state.get("current_symbol", "SPY")

        # Verificar si OpenAI está configurado correctamente
        if not api_key:
            # Modo fallback: generar respuesta basada en análisis local
            return fallback_analyze_symbol(symbol, prompt)

        # Si no se proporciona contexto, obtenerlo
        if not context:
            context = get_market_context(symbol)

        if not context or "error" in context:
            return f"❌ Error: No se pudo obtener el contexto de mercado para {symbol}."

        # Si tenemos un assistant_id, usar la API de asistentes
        if assistant_id:
            return process_with_assistant(prompt, symbol, context, assistant_id)
        else:
            # Usar la API de Chat Completion directamente
            return process_with_chat_completion(prompt, symbol, context, api_key)

    except Exception as e:
        logger.error(f"Error procesando consulta: {str(e)}")
        return f"Error procesando consulta: {str(e)}"


def process_with_assistant(prompt, symbol, context, assistant_id):
    """Procesa el mensaje utilizando la API de Asistentes de OpenAI con manejo mejorado"""
    try:
        # Crear thread si no existe
        if "thread_id" not in st.session_state:
            thread = openai.beta.threads.create()
            st.session_state.thread_id = thread.id
            logger.info(f"Nuevo thread creado: {thread.id}")

        # Formatear contexto para el mensaje
        price = context.get("last_price", 0)
        change = context.get("change_percent", 0)
        vix_level = context.get("vix_level", "N/A")

        signals = context.get("signals", {})

        # Obtener señal general
        overall_signal = "NEUTRAL"
        if "overall" in signals:
            signal = signals["overall"]["signal"]
            if signal in ["compra", "compra_fuerte"]:
                overall_signal = "ALCISTA"
            elif signal in ["venta", "venta_fuerte"]:
                overall_signal = "BAJISTA"

        # Obtener señal de opciones
        option_signal = "NEUTRAL"
        if "options" in signals:
            signal = signals["options"].get("signal", "neutral")
            if signal in ["compra", "compra_fuerte"]:
                option_signal = "ALCISTA"
            elif signal in ["venta", "venta_fuerte"]:
                option_signal = "BAJISTA"

        # Incluir información de sentimiento si está disponible
        sentiment_info = ""
        if "news_sentiment" in context and context["news_sentiment"]:
            sentiment = context["news_sentiment"]
            sentiment_info = f"\nSentimiento: {sentiment.get('sentiment', 'neutral')} ({sentiment.get('score', 0.5)*100:.1f}%)\n"

        # Incluir información de noticias si está disponible
        news_info = ""
        if "news" in context and context["news"]:
            news_info = "\nNoticias recientes:\n"
            for item in context["news"][:3]:  # Mostrar hasta 3 noticias
                news_info += (
                    f"- {item.get('date', 'N/A')}: {item.get('title', 'N/A')}\n"
                )

        # Crear mensaje enriquecido con contexto
        context_prompt = f"""
        Consulta sobre {symbol} a ${price:.2f} ({'+' if change > 0 else ''}{change:.2f}%):

        Señales técnicas actuales:
        - Tendencia general: {overall_signal}
        - Señal de opciones: {option_signal}
        - VIX: {vix_level}
        {sentiment_info}
        {news_info}

        Pregunta del usuario: {prompt}
        """

        # Crear mensaje en el thread
        thread_messages = openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=context_prompt
        )

        # Ejecutar con herramientas
        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=assistant_id
        )

        # Esperar a que se complete la ejecución con timeout
        start_time = time.time()
        timeout = 30  # 30 segundos máximo
        while True:
            # Verificar timeout
            if time.time() - start_time > timeout:
                logger.warning(f"Timeout esperando respuesta del asistente")
                return "La consulta tomó demasiado tiempo. Por favor, intenta de nuevo con una pregunta más específica."

            # Esperar un momento antes de verificar de nuevo
            time.sleep(1)

            # Actualizar estado de la ejecución
            run = openai.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id, run_id=run.id
            )

            # Verificar si la ejecución ha terminado
            if run.status in ["completed", "failed", "cancelled", "expired"]:
                break

        # Verificar si la ejecución fue exitosa
        if run.status != "completed":
            logger.error(f"La ejecución falló con estado: {run.status}")
            return f"Error: La consulta falló con estado {run.status}"

        # Obtener mensajes actualizados
        try:
            messages = openai.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )

            # Encontrar respuesta del asistente
            for message in messages:
                if message.run_id == run.id and message.role == "assistant":
                    # Extraer texto de la respuesta
                    return process_message_with_citations(message)

            return "No se pudo obtener una respuesta del asistente."
        except Exception as msg_error:
            logger.error(f"Error obteniendo mensajes: {str(msg_error)}")
            return f"Error obteniendo respuesta: {str(msg_error)}"

    except Exception as e:
        logger.error(f"Error en process_with_assistant: {str(e)}")
        # En caso de error, caer en el modo fallback
        return fallback_analyze_symbol(symbol, prompt)


def process_with_chat_completion(prompt, symbol, context, api_key):
    """Procesa el mensaje utilizando la API de Chat Completion de OpenAI"""
    try:
        # Formatear contexto para el mensaje
        price = context.get("last_price", 0)
        change = context.get("change_percent", 0)
        vix_level = context.get("vix_level", "N/A")

        signals = context.get("signals", {})
        support_resistance = context.get("support_resistance", {})

        # Extraer información de noticias y sentimiento si está disponible
        news = context.get("news", [])
        sentiment = context.get("news_sentiment", {})

        news_text = ""
        if news:
            news_text = "\nNoticias recientes:\n"
            for item in news[:3]:  # Limitar a 3 noticias
                news_text += f"- {item.get('date', '')}: {item.get('title', '')}\n"

        sentiment_text = ""
        if sentiment:
            sentiment_text = f"\nSentimiento: {sentiment.get('sentiment', 'neutral')} ({sentiment.get('score', 0.5)*100:.1f}%)"

        # Crear prompt del sistema
        system_prompt = """
        Eres un Especialista en Trading y Análisis Técnico, experto en mercados financieros.

        Proporciona análisis precisos, concisos y útiles sobre activos financieros.
        Utiliza el contexto de mercado proporcionado para dar respuestas informadas.

        Cuando sea apropiado, incluye:
        - Análisis técnico relevante
        - Niveles de soporte y resistencia
        - Interpretación de indicadores
        - Patrones de precio
        - Estrategias potenciales

        Mantén un tono profesional y objetivo. Evita predicciones exageradas.
        """

        # Crear mensaje de contexto
        context_message = f"""
        Contexto actual para {symbol}:

        Precio: ${price:.2f} ({change:+.2f}%)
        VIX: {vix_level}

        Señales técnicas:
        - Tendencia general: {signals.get('overall', {}).get('signal', 'neutral')}
        - Momentum: {signals.get('momentum', {}).get('signal', 'neutral')}
        - Tendencia: {signals.get('trend', {}).get('signal', 'neutral')}

        Principales niveles:
        - Resistencias: {', '.join([f"${r:.2f}" for r in support_resistance.get('resistances', [])[:2]])}
        - Soportes: {', '.join([f"${s:.2f}" for s in support_resistance.get('supports', [])[:2]])}

        {sentiment_text}
        {news_text}
        """

        # Crear mensajes para la API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_message},
            {"role": "user", "content": prompt},
        ]

        # Realizar llamada a la API con manejo de errores
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",  # Usar el modelo más avanzado
                messages=messages,
                temperature=0.7,  # Balancear creatividad y precisión
                max_tokens=1000,  # Respuesta detallada pero no excesiva
            )

            # Extraer la respuesta
            return response.choices[0].message.content

        except Exception as api_err:
            logger.error(f"Error en API de OpenAI: {str(api_err)}")
            return f"Error en el servicio de OpenAI: {str(api_err)}"

    except Exception as e:
        logger.error(f"Error en process_with_chat_completion: {str(e)}")
        # En caso de error, caer en el modo fallback
        return fallback_analyze_symbol(symbol, prompt)


def process_content_with_ai(
    client, assistant_id, content_type, content, symbol, additional_context=None
):
    """
    Procesa cualquier tipo de contenido con IA para mejorar su calidad y coherencia

    Args:
        client: Cliente de OpenAI
        assistant_id: ID del asistente de OpenAI
        content_type: Tipo de contenido a procesar ('analysis', 'technical_analysis', 'news', etc.)
        content: Contenido original a mejorar
        symbol: Símbolo del activo
        additional_context: Contexto adicional para mejorar el procesamiento

    Returns:
        str: Contenido procesado y mejorado
    """
    if not client or not assistant_id:
        return content

    try:
        # Crear un prompt específico según el tipo de contenido
        if content_type == "analysis":
            prompt = f"""
            Como analista financiero experto, mejora el siguiente análisis para el símbolo {symbol}.
            Haz que sea más coherente, informativo y profesional, manteniendo los puntos clave pero mejorando
            la redacción y estructura. El análisis debe estar en español y ser fácil de entender.

            Análisis original:
            {content}

            Contexto adicional:
            {additional_context or ''}
            """
        elif content_type == "technical_analysis":
            prompt = f"""
            Como especialista en análisis técnico, mejora el siguiente análisis técnico para {symbol}.
            Haz que sea más preciso, detallado y profesional, incluyendo referencias a indicadores clave,
            patrones y niveles importantes. El análisis debe estar en español y ser técnicamente sólido.

            Análisis técnico original:
            {content}

            Contexto adicional:
            {additional_context or ''}
            """
        elif content_type == "news":
            prompt = f"""
            Como periodista financiero, mejora la siguiente noticia relacionada con {symbol}.
            Haz que sea más informativa, precisa y profesional. La noticia debe estar en español,
            ser objetiva y proporcionar información relevante para inversores.

            Noticia original:
            {content}

            Contexto adicional:
            {additional_context or ''}

            Asegúrate de incluir una fuente confiable y una URL si está disponible.
            """
        elif content_type == "expert_analysis":
            prompt = f"""
            Como experto en mercados financieros, proporciona un análisis completo y detallado para {symbol}.
            El análisis debe incluir evaluación técnica, fundamental, de sentimiento y de riesgo.
            Debe estar en español, ser profesional y proporcionar una recomendación clara.

            Información disponible:
            {content}

            Contexto adicional:
            {additional_context or ''}

            Estructura tu respuesta con las siguientes secciones:
            1. Evaluación General
            2. Análisis Técnico
            3. Niveles Clave
            4. Análisis Fundamental
            5. Estrategias Recomendadas
            6. Gestión de Riesgo
            7. Proyección de Movimiento
            8. Recomendación Final (CALL/PUT/NEUTRAL)
            """
        else:
            # Caso genérico para otros tipos de contenido
            prompt = f"""
            Como experto financiero, mejora el siguiente contenido relacionado con {symbol}.
            Haz que sea más coherente, informativo y profesional. El contenido debe estar en español
            y ser fácil de entender para inversores.

            Contenido original:
            {content}

            Contexto adicional:
            {additional_context or ''}
            """

        # Verificar si existe un thread en la sesión
        thread_id = None
        if hasattr(st, "session_state") and "content_thread_id" in st.session_state:
            thread_id = st.session_state.content_thread_id

        if not thread_id:
            # Crear un nuevo thread
            thread = client.beta.threads.create()
            thread_id = thread.id
            if hasattr(st, "session_state"):
                st.session_state.content_thread_id = thread_id
            logger.info(f"Nuevo thread creado para procesar contenido: {thread_id}")

        # Enviar mensaje al thread
        client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=prompt
        )

        # Crear una ejecución para el thread
        run = client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=assistant_id
        )

        # Esperar a que se complete la ejecución con timeout
        start_time = time.time()
        timeout = 30  # 30 segundos máximo
        while run.status in ["queued", "in_progress"]:
            # Verificar timeout
            if time.time() - start_time > timeout:
                logger.warning(
                    f"Timeout esperando respuesta del asistente para procesar contenido"
                )
                return content  # Devolver contenido original si hay timeout

            # Esperar un momento antes de verificar de nuevo
            time.sleep(1)

            # Actualizar estado de la ejecución
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status != "completed":
            logger.warning(
                f"La ejecución para procesar contenido falló con estado {run.status}"
            )
            return content  # Devolver contenido original si hay error

        # Recuperar mensajes
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Obtener respuesta
        for message in messages:
            if message.run_id == run.id and message.role == "assistant":
                # Extraer texto del mensaje
                processed_content = process_message_with_citations(message)
                if (
                    processed_content and len(processed_content) > len(content) * 0.5
                ):  # Verificar que la respuesta sea sustancial
                    return processed_content

        # Si no se pudo procesar, devolver el contenido original
        return content

    except Exception as e:
        logger.error(f"Error procesando contenido con IA: {str(e)}")
        return content  # Devolver contenido original si hay error


def fallback_analyze_symbol(symbol, prompt):
    """Función de respaldo para analizar símbolos cuando OpenAI no está disponible"""
    try:
        # Obtener contexto de mercado
        context = get_market_context(symbol)

        # Extraer información básica
        if context and "error" not in context:
            price = context.get("last_price", 0)
            change = context.get("change_percent", 0)
            signals = context.get("signals", {})

            # Obtener información de la empresa
            company_info = context.get("company_info", {})
            name = company_info.get("name", symbol)
            sector = company_info.get("sector", "No especificado")

            # Determinar tendencia general
            trend = "neutral"
            if "overall" in signals:
                signal = signals["overall"]["signal"]
                if signal in ["compra", "compra_fuerte"]:
                    trend = "alcista"
                elif signal in ["venta", "venta_fuerte"]:
                    trend = "bajista"

            # Generar respuesta básica basada en la consulta
            if "tendencia" in prompt.lower() or "dirección" in prompt.lower():
                return f"""
                La tendencia actual de {name} ({symbol}) es {trend.upper()}.

                Precio actual: ${price:.2f} ({change:+.2f}%)
                Sector: {sector}

                Análisis técnico básico:
                - RSI: {signals.get('momentum', {}).get('rsi', 'N/A')}
                - MACD: {signals.get('momentum', {}).get('macd', 'N/A')}
                - Media móvil 50: {signals.get('trend', {}).get('sma50', 'N/A')}
                """
            elif "soporte" in prompt.lower() or "resistencia" in prompt.lower():
                support_resistance = context.get("support_resistance", {})
                supports = support_resistance.get("supports", [])
                resistances = support_resistance.get("resistances", [])

                return f"""
                Niveles clave para {name} ({symbol}):

                Soportes:
                {', '.join([f"${s:.2f}" for s in supports[:3]])}

                Resistencias:
                {', '.join([f"${r:.2f}" for r in resistances[:3]])}

                Precio actual: ${price:.2f}
                """
            else:
                # Respuesta general
                return f"""
                Análisis básico de {name} ({symbol}):

                Precio actual: ${price:.2f} ({change:+.2f}%)
                Sector: {sector}
                Tendencia: {trend.upper()}

                Indicadores técnicos:
                - RSI: {signals.get('momentum', {}).get('rsi', 'N/A')}
                - MACD: {signals.get('momentum', {}).get('macd', 'N/A')}
                - Media móvil 50: {signals.get('trend', {}).get('sma50', 'N/A')}

                Para un análisis más detallado, considera configurar la API de OpenAI en la aplicación.
                """
        else:
            # Si no hay contexto, dar una respuesta genérica
            error_msg = context.get(
                "error", "No se pudo obtener información de mercado."
            )

            response = f"""
            ## Información sobre {symbol}

            Lo siento, no se pudieron obtener datos actuales de mercado para {symbol}. {error_msg}

            Algunas posibles razones:

            - El símbolo puede no estar disponible en nuestras fuentes de datos
            - Puede haber una interrupción temporal en los servicios de datos
            - El mercado puede estar cerrado actualmente

            Recomendaciones:

            - Intenta con otro símbolo
            - Verifica que el símbolo esté escrito correctamente
            - Intenta nuevamente más tarde
            """
            return response

    except Exception as e:
        logger.error(f"Error analizando símbolo {symbol}: {str(e)}")
        return f"❌ Error analizando {symbol}: {str(e)}"
