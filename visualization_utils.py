"""
InversorIA Pro - Utilidades de Visualización
-------------------------------------------
Este archivo contiene funciones para visualizar datos y análisis en la interfaz de usuario.
"""

import logging
import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

# Importar componentes personalizados
try:
    from company_data import get_company_info, COMPANY_INFO
except Exception as e:
    logging.error(f"Error importando company_data: {str(e)}")
    
    # Definir función de respaldo si no se puede importar
    def get_company_info(symbol):
        """Función de respaldo para obtener información de la empresa"""
        return {
            "name": symbol,
            "sector": "No especificado",
            "description": f"Activo financiero negociado bajo el símbolo {symbol}",
        }

logger = logging.getLogger(__name__)

def display_asset_info(symbol, price=None, change=None):
    """Muestra información básica del activo compatible con modo claro y oscuro"""
    # Obtener información completa de la empresa/activo
    company_info = get_company_info(symbol)

    # Obtener nombre completo del activo
    full_name = company_info.get("name", symbol)
    sector = company_info.get("sector", "No especificado")
    description = company_info.get("description", "")

    # Estimar precio y cambio si no están disponibles
    price_display = f"${price:.2f}" if price is not None else "N/A"
    change_display = f"{change:+.2f}%" if change is not None else ""

    # Color condicional para cambio
    change_color = (
        "green"
        if change is not None and change >= 0
        else "red" if change is not None and change < 0 else "inherit"
    )

    # Usar st.container() con estilos nativos de Streamlit que se adaptan al modo oscuro/claro
    with st.container():
        # Encabezado del activo
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"## {full_name} ({symbol})")

        with col2:
            st.markdown(
                f"<h2 style='text-align: right; color: {change_color};'>{price_display} <span style='font-size: 0.8em;'>{change_display}</span></h2>",
                unsafe_allow_html=True,
            )

        # Descripción y detalles
        st.markdown(description)

        # Mostrar detalles adicionales
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Sector:** {sector}")

        with col2:
            st.markdown(
                f"**Última Actualización:** {datetime.now().strftime('%H:%M:%S')}"
            )

        # Línea separadora
        st.markdown("---")

def display_expert_opinion(expert_opinion):
    """Muestra la opinión del experto IA con formato mejorado y opción de exportar a MD"""
    if not expert_opinion:
        return

    st.markdown("## 🧠 Análisis del Experto")

    # Procesamiento mejorado del texto: buscar secciones clave
    sections = {
        "evaluación": "",
        "niveles": "",
        "técnico": "",
        "fundamental": "",
        "estrategias": "",
        "riesgo": "",
        "proyección": "",
        "recomendación": "",
    }

    current_section = None
    final_recommendation = None
    recommendation_type = "NEUTRAL"

    try:
        # Limpiar el texto completo de marcadores de código, HTML y formateo markdown
        expert_opinion = re.sub(r"```.*?```", "", expert_opinion, flags=re.DOTALL)
        expert_opinion = expert_opinion.replace("```", "")
        expert_opinion = re.sub(r"<.*?>", "", expert_opinion)

        # Buscar recomendación final
        recommendation_match = re.search(
            r"(RECOMENDACIÓN|RECOMENDACION).*?:(.*?)(?=\n\n|\n#|\Z)",
            expert_opinion,
            re.IGNORECASE | re.DOTALL,
        )
        if recommendation_match:
            final_recommendation = recommendation_match.group(2).strip()
            if "compra" in final_recommendation.lower() or "alcista" in final_recommendation.lower():
                recommendation_type = "ALCISTA"
            elif "venta" in final_recommendation.lower() or "bajista" in final_recommendation.lower():
                recommendation_type = "BAJISTA"

        # Dividir por líneas y procesar
        lines = expert_opinion.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detectar encabezados de sección
            section_match = re.match(r"^#+\s*(.*?)$", line)
            if section_match:
                section_title = section_match.group(1).lower()
                for key in sections.keys():
                    if key in section_title:
                        current_section = key
                        break
                continue

            # Detectar secciones por dos puntos
            section_match = re.match(r"^(.*?):\s*$", line)
            if section_match:
                section_title = section_match.group(1).lower()
                for key in sections.keys():
                    if key in section_title:
                        current_section = key
                        break
                continue

            # Añadir línea a la sección actual
            if current_section:
                sections[current_section] += line + "\n"
    except Exception as e:
        logger.error(f"Error procesando opinión experta: {str(e)}")

    # Si no se identificaron secciones, mostrar el texto completo
    if all(not v for v in sections.values()):
        # Limpiar el texto completo de marcadores de código
        cleaned_opinion = re.sub(r"[\*\`]", "", expert_opinion)

        st.markdown(
            f"""
            <div class="expert-container">
                <div class="expert-header">
                    <div class="expert-avatar">E</div>
                    <div class="expert-title">Analista de Mercados</div>
                </div>
                <div class="expert-content">
                    {cleaned_opinion}
                </div>
                <div class="expert-footer">
                    Análisis generado por IA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Mostrar análisis estructurado
        recommendation_color = (
            "green"
            if recommendation_type == "ALCISTA"
            else "red" if recommendation_type == "BAJISTA" else "#888"
        )

        st.markdown(
            f"""
            <div class="expert-container">
                <div class="expert-header">
                    <div class="expert-avatar">E</div>
                    <div class="expert-title">Analista de Mercados</div>
                </div>
                <div class="expert-content">
            """,
            unsafe_allow_html=True,
        )

        if final_recommendation:
            st.markdown(
                f"""
                <div class="recommendation-box" style="background-color: {recommendation_color}20; border-left: 4px solid {recommendation_color}; padding: 10px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: {recommendation_color};">Recomendación</h3>
                    <p>{final_recommendation}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if sections["evaluación"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["evaluación"])
            st.markdown("### 📊 Evaluación General")
            st.markdown(cleaned_text)

        if sections["técnico"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["técnico"])
            st.markdown("### 📈 Análisis Técnico")
            st.markdown(cleaned_text)

        if sections["niveles"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["niveles"])
            st.markdown("### 🎯 Niveles Clave")
            st.markdown(cleaned_text)

        if sections["fundamental"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["fundamental"])
            st.markdown("### 📊 Análisis Fundamental")
            st.markdown(cleaned_text)

        if sections["estrategias"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["estrategias"])
            st.markdown("### 🧩 Estrategias Recomendadas")
            st.markdown(cleaned_text)

        if sections["riesgo"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["riesgo"])
            st.markdown("### ⚠️ Análisis de Riesgo")
            st.markdown(cleaned_text)

        if sections["proyección"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["proyección"])
            st.markdown("### 🔮 Proyección de Movimiento")
            st.markdown(cleaned_text)

        st.markdown(
            f"""
                </div>
                <div class="expert-footer">
                    Análisis generado por IA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def display_sentiment_analysis(context):
    """Muestra análisis de sentimiento integrado desde MarketIntel"""
    sentiment = context.get("news_sentiment", {})
    web_analysis = context.get("web_analysis", {})

    if not sentiment and not web_analysis:
        st.info(
            """
        No se encontró análisis de sentimiento disponible.

        **Posibles soluciones:**
        - Verifica la configuración de API keys en .streamlit/secrets.toml
        - Asegúrate de que las claves "you_api_key", "tavily_api_key" o "alpha_vantage_api_key" estén configuradas
        - Para evitar errores, puedes importar la función get_api_keys_from_secrets de market_utils
        """
        )
        return

    st.markdown(
        '<div class="sub-header">📊 Análisis de Sentimiento</div>',
        unsafe_allow_html=True,
    )

    # Crear columnas para mostrar datos
    col1, col2 = st.columns(2)

    with col1:
        if sentiment:
            # Determinar color basado en el sentimiento
            sentiment_score = sentiment.get("score", 0.5)
            sentiment_color = (
                "green"
                if sentiment_score > 0.6
                else "red" if sentiment_score < 0.4 else "orange"
            )
            sentiment_label = (
                "Positivo"
                if sentiment_score > 0.6
                else "Negativo" if sentiment_score < 0.4 else "Neutral"
            )

            # Mostrar medidor de sentimiento
            st.markdown(
                f"""
            <div style="text-align: center;">
                <div style="font-size: 1.2em; margin-bottom: 5px;">Sentimiento de Mercado</div>
                <div style="font-size: 2em; color: {sentiment_color};">{sentiment_label}</div>
                <div style="font-size: 1.2em; color: {sentiment_color};">{sentiment_score*100:.1f}%</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col2:
        if web_analysis:
            # Mostrar análisis web
            st.markdown("#### Análisis Web")
            st.markdown(web_analysis.get("summary", "No hay análisis disponible"))

    # Mostrar fuentes si están disponibles
    if sentiment and "sources" in sentiment:
        with st.expander("Ver fuentes de sentimiento"):
            for source in sentiment["sources"]:
                st.markdown(
                    f"""
                - **{source.get('name', 'Fuente')}**: {source.get('sentiment', 'N/A')} ({source.get('score', 0)*100:.1f}%)
                """
                )

def display_news_feed(context):
    """Muestra feed de noticias integrado desde MarketIntel"""
    news = context.get("news", [])

    if not news:
        st.info(
            """
        No se encontraron noticias recientes.

        **Posibles soluciones:**
        - Verifica la configuración de Alpha Vantage API key
        - Asegúrate de que tienes acceso al endpoint de noticias de Alpha Vantage
        - Algunos símbolos pueden no tener cobertura de noticias
        """
        )
        return

    st.markdown(
        '<div class="sub-header">📰 Noticias Recientes</div>', unsafe_allow_html=True
    )

    # Mostrar noticias recientes
    for item in news:
        st.markdown(
            f"""
        <div class="news-card">
            <div class="news-date">{item.get('date', 'Fecha no disponible')}</div>
            <a href="{item.get('url', '#')}" target="_blank">{item.get('title', 'Sin título')}</a>
        </div>
        """,
            unsafe_allow_html=True,
        )

def display_web_insights(context):
    """Muestra insights de búsqueda web integrado desde MarketIntel"""
    web_results = context.get("web_results", [])

    if not web_results:
        st.info("No se encontraron resultados de búsqueda web.")
        return

    st.markdown(
        '<div class="sub-header">🌐 Insights de Mercado</div>', unsafe_allow_html=True
    )

    # Mostrar resultados de búsqueda web en un expander
    with st.expander("Ver fuentes de análisis"):
        for i, result in enumerate(web_results):
            st.markdown(
                f"""
            #### {result.get('title', 'Sin título')}
            {result.get('content', 'Sin contenido')}

            [Leer más en {result.get('source', 'Fuente')}]({result.get('url', '#')})
            """
            )

            if i < len(web_results) - 1:
                st.markdown("---")

def display_technical_summary(symbol, technical_data):
    """Muestra resumen técnico en un formato mejorado"""
    st.markdown("### 📊 Resumen Técnico")

    # Crear columnas para mostrar datos clave
    col1, col2, col3, col4 = st.columns(4)

    # Extraer últimos valores
    if isinstance(technical_data, pd.DataFrame) and not technical_data.empty:
        last_row = technical_data.iloc[-1]
        last_price = last_row["Close"]

        # Calcular cambio porcentual
        if len(technical_data) > 1:
            prev_close = technical_data.iloc[-2]["Close"]
            change_pct = (last_price - prev_close) / prev_close * 100
        else:
            change_pct = 0

        # Mostrar precio y cambio
        with col1:
            st.metric(
                "Precio",
                f"${last_price:.2f}",
                f"{change_pct:+.2f}%",
                delta_color="normal",
            )

        # Mostrar volumen si está disponible
        if "Volume" in last_row:
            volume = last_row["Volume"]
            volume_formatted = (
                f"{volume/1000000:.1f}M"
                if volume >= 1000000
                else f"{volume/1000:.1f}K" if volume >= 1000 else f"{volume:.0f}"
            )

            # Calcular cambio de volumen
            if len(technical_data) > 1 and "Volume" in technical_data.iloc[-2]:
                prev_volume = technical_data.iloc[-2]["Volume"]
                if prev_volume > 0:
                    volume_change = (volume - prev_volume) / prev_volume * 100
                    with col2:
                        st.metric(
                            "Volumen",
                            volume_formatted,
                            f"{volume_change:+.2f}%",
                            delta_color="normal",
                        )
                else:
                    with col2:
                        st.metric("Volumen", volume_formatted)
            else:
                with col2:
                    st.metric("Volumen", volume_formatted)

        # Mostrar RSI si está disponible
        if "RSI" in last_row:
            rsi = last_row["RSI"]
            rsi_status = (
                "Sobrecompra" if rsi > 70 else "Sobreventa" if rsi < 30 else "Neutral"
            )
            with col3:
                st.metric("RSI", f"{rsi:.1f}", rsi_status)

        # Mostrar MACD si está disponible
        if "MACD" in last_row and "MACD_Signal" in last_row:
            macd = last_row["MACD"]
            macd_signal = last_row["MACD_Signal"]
            macd_diff = macd - macd_signal
            macd_status = "Alcista" if macd_diff > 0 else "Bajista"
            with col4:
                st.metric("MACD", f"{macd:.2f}", f"{macd_diff:+.2f} ({macd_status})")
    else:
        st.warning("No hay datos técnicos disponibles para mostrar.")

def display_signal_card(signal, index=0):
    """Muestra una tarjeta de señal de trading con formato mejorado"""
    # Extraer datos de la señal
    symbol = signal.get("symbol", "N/A")
    direction = signal.get("direction", "NEUTRAL")
    confidence = signal.get("confidence_level", "Media")
    price = signal.get("price", 0.0)
    strategy = signal.get("strategy", "Análisis Técnico")
    category = signal.get("category", "General")
    analysis = signal.get("analysis", "")
    created_at = signal.get("created_at", datetime.now())
    
    # Formatear fecha
    if isinstance(created_at, datetime):
        fecha = created_at.strftime("%d/%m/%Y %H:%M")
    else:
        fecha = str(created_at)
    
    # Determinar colores según dirección
    if direction == "CALL":
        bg_color = "rgba(76, 175, 80, 0.1)"
        border_color = "#4CAF50"
        icon = "📈"
        text_color = "#4CAF50"
    elif direction == "PUT":
        bg_color = "rgba(244, 67, 54, 0.1)"
        border_color = "#F44336"
        icon = "📉"
        text_color = "#F44336"
    else:
        bg_color = "rgba(158, 158, 158, 0.1)"
        border_color = "#9E9E9E"
        icon = "📊"
        text_color = "#9E9E9E"
    
    # Mostrar tarjeta
    st.markdown(
        f"""
        <div style="background-color: {bg_color}; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid {border_color}">
            <h3 style="margin-top: 0; display: flex; justify-content: space-between;">
                <span>{icon} {symbol} ({category})</span>
                <span style="color: {text_color};">{direction}</span>
            </h3>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span><strong>Precio:</strong> ${price:.2f}</span>
                <span><strong>Confianza:</strong> {confidence}</span>
                <span><strong>Estrategia:</strong> {strategy}</span>
            </div>
            <div style="margin-bottom: 10px;">
                <strong style="color: #555;">Análisis:</strong> {analysis}
            </div>
            <div style="text-align: right; font-size: 0.8em; color: #777;">
                <strong style="color: #555;">Fecha:</strong> {fecha}
            </div>
            <details style="margin-top: 15px; cursor: pointer;">
                <summary style="color: {text_color}; font-weight: 500;">Ver análisis detallado</summary>
                <div style="background-color: rgba(255,255,255,0.5); padding: 15px; border-radius: 8px; margin-top: 10px;">
                    <p style="margin: 0;">{analysis}</p>
                </div>
            </details>
        </div>
        """,
        unsafe_allow_html=True,
    )

def display_market_sentiment_card(sentiment):
    """Muestra una tarjeta con el sentimiento del mercado"""
    if not sentiment:
        st.warning("No hay datos de sentimiento disponibles")
        return
    
    # Determinar color según sentimiento
    overall = sentiment.get("overall", "Neutral")
    if overall == "Alcista":
        bg_color = "rgba(76, 175, 80, 0.1)"
        border_color = "#4CAF50"
        icon = "📈"
        text_color = "#4CAF50"
    elif overall == "Bajista":
        bg_color = "rgba(244, 67, 54, 0.1)"
        border_color = "#F44336"
        icon = "📉"
        text_color = "#F44336"
    else:
        bg_color = "rgba(158, 158, 158, 0.1)"
        border_color = "#9E9E9E"
        icon = "📊"
        text_color = "#9E9E9E"
    
    # Formatear fecha
    date = sentiment.get("date", datetime.now().date())
    if isinstance(date, datetime):
        fecha = date.strftime("%d/%m/%Y")
    else:
        fecha = str(date)
    
    # Mostrar tarjeta
    st.markdown(
        f"""
        <div style="background-color: {bg_color}; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid {border_color}">
            <h3 style="margin-top: 0; display: flex; justify-content: space-between;">
                <span>{icon} Sentimiento de Mercado</span>
                <span style="color: {text_color};">{overall}</span>
            </h3>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span><strong>VIX:</strong> {sentiment.get('vix', 'N/A')}</span>
                <span><strong>S&P 500:</strong> {sentiment.get('sp500_trend', 'N/A')}</span>
                <span><strong>Volumen:</strong> {sentiment.get('volume', 'N/A')}</span>
            </div>
            <div style="margin-bottom: 10px;">
                <strong style="color: #555;">Indicadores Técnicos:</strong> {sentiment.get('technical_indicators', 'N/A')}
            </div>
            <div style="text-align: right; font-size: 0.8em; color: #777;">
                <strong style="color: #555;">Fecha:</strong> {fecha}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def display_news_card(news_item):
    """Muestra una tarjeta de noticia con formato mejorado"""
    if not news_item:
        return
    
    # Extraer datos de la noticia
    title = news_item.get("title", "Sin título")
    summary = news_item.get("summary", "")
    source = news_item.get("source", "Fuente desconocida")
    url = news_item.get("url", "#")
    date = news_item.get("date", datetime.now())
    
    # Formatear fecha
    if isinstance(date, datetime):
        fecha = date.strftime("%d/%m/%Y %H:%M")
    else:
        fecha = str(date)
    
    # Mostrar tarjeta
    st.markdown(
        f"""
        <div style="background-color: rgba(33, 150, 243, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #2196F3">
            <h3 style="margin-top: 0;">{title}</h3>
            <div style="margin-bottom: 10px;">
                {summary}
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.8em; color: #777;">
                <span><strong>Fuente:</strong> {source}</span>
                <span><strong>Fecha:</strong> {fecha}</span>
            </div>
            <div style="margin-top: 10px;">
                <a href="{url}" target="_blank" style="color: #2196F3; text-decoration: none;">Leer más</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_dataframe(df):
    """
    Convierte un DataFrame a un formato seguro para Streamlit
    
    Args:
        df (pd.DataFrame): DataFrame a convertir
        
    Returns:
        pd.DataFrame: DataFrame convertido
    """
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    
    # Hacer una copia para evitar modificar el original
    safe_df = df.copy()
    
    # Convertir columnas problemáticas a string
    for col in safe_df.columns:
        # Verificar si la columna contiene tipos mixtos
        if safe_df[col].dtype == 'object':
            safe_df[col] = safe_df[col].astype(str)
        
        # Convertir fechas a string
        elif pd.api.types.is_datetime64_any_dtype(safe_df[col]):
            safe_df[col] = safe_df[col].astype(str)
    
    return safe_df
