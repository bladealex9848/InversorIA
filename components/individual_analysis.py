"""
Componente de análisis individual para InversorIA Pro
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from market_utils import fetch_market_data, TechnicalAnalyzer, get_market_context
from visualization_utils import (
    display_asset_info,
    display_expert_opinion,
    display_sentiment_analysis,
    display_news_feed,
    display_web_insights,
    display_technical_summary,
)
from trading_dashboard import (
    render_technical_tab,
    render_options_tab,
    render_multiframe_tab,
    render_fundamental_tab,
    render_report_tab,
    render_risk_tab,
)

logger = logging.getLogger(__name__)


def render_individual_analysis():
    """
    Renderiza la pestaña de análisis individual
    """
    st.markdown("## 📊 Análisis Individual")

    # Obtener el símbolo actual
    symbol = st.session_state.current_symbol

    # Mostrar información básica del activo
    display_asset_info(symbol)

    # Crear pestañas para diferentes tipos de análisis
    tabs = st.tabs(
        [
            "📈 Análisis Técnico",
            "🔄 Opciones",
            "⏱️ Multi-Timeframe",
            "📊 Fundamental",
            "📝 Reporte",
            "⚠️ Riesgo",
        ]
    )

    # Obtener datos de mercado para el símbolo actual
    try:
        # Obtener datos históricos
        days = st.session_state.get("history_days", 180)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Obtener datos de mercado
        df = fetch_market_data(symbol, start_date, end_date)

        if df is not None and not df.empty:
            # Inicializar analizador técnico
            analyzer = TechnicalAnalyzer(df)

            # Obtener contexto de mercado
            context = get_market_context(symbol)

            # Renderizar cada pestaña
            with tabs[0]:  # Análisis Técnico
                render_technical_tab(symbol, df)

            with tabs[1]:  # Opciones
                render_options_tab(symbol, df)

            with tabs[2]:  # Multi-Timeframe
                render_multiframe_tab(symbol)

            with tabs[3]:  # Fundamental
                render_fundamental_tab(symbol)

            with tabs[4]:  # Reporte
                render_report_tab(symbol, df)

            with tabs[5]:  # Riesgo
                render_risk_tab(symbol, df)
        else:
            st.error(f"No se pudieron obtener datos para {symbol}")
    except Exception as e:
        st.error(f"Error al analizar {symbol}: {str(e)}")
        logger.error(f"Error en análisis individual: {str(e)}")

    # Mostrar análisis del experto
    st.markdown("### 🧠 Análisis del Experto")
    display_expert_opinion(symbol)

    # Mostrar análisis de sentimiento y noticias
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📰 Noticias Recientes")
        display_news_feed(symbol)

    with col2:
        st.markdown("### 🌐 Sentimiento de Mercado")
        display_sentiment_analysis(symbol)

    # Mostrar resumen técnico
    st.markdown("### 📊 Resumen Técnico")
    display_technical_summary(symbol)

    # Mostrar insights web
    st.markdown("### 🔍 Insights Web")
    display_web_insights(symbol)
