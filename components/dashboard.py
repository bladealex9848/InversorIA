"""
Componente de dashboard para InversorIA Pro
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
from market_utils import fetch_market_data, get_vix_level
from company_data import SYMBOLS
from utils.ui_utils import display_asset_card, create_candlestick_chart

logger = logging.getLogger(__name__)


def render_dashboard():
    """
    Renderiza el dashboard principal
    """
    st.markdown("## 📊 Dashboard")

    # Obtener fecha actual
    current_date = datetime.now()

    # Mostrar fecha y hora
    st.markdown(f"### 📅 {current_date.strftime('%d/%m/%Y %H:%M')}")

    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Obtener nivel de VIX
        vix = get_vix_level()
        st.metric("VIX", f"{vix:.2f}", delta=f"{vix - 20:.2f}")

    with col2:
        # Simular S&P 500
        st.metric("S&P 500", "4,783.45", delta="0.32%")

    with col3:
        # Simular Nasdaq
        st.metric("Nasdaq", "16,742.39", delta="0.58%")

    with col4:
        # Simular Dow Jones
        st.metric("Dow Jones", "38,239.98", delta="-0.12%")

    # Mostrar gráfico principal
    st.markdown("### 📈 Mercado Principal")

    # Obtener datos para SPY (S&P 500 ETF)
    try:
        spy_data = fetch_market_data("SPY", period="180d")

        if spy_data is not None and not spy_data.empty:
            # Crear gráfico de velas
            fig = create_candlestick_chart(spy_data, title="S&P 500 (SPY)", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No se pudieron obtener datos para SPY")
    except Exception as e:
        st.error(f"Error al obtener datos de SPY: {str(e)}")
        logger.error(f"Error en dashboard: {str(e)}")

    # Mostrar activos destacados
    st.markdown("### 🌟 Activos Destacados")

    # Seleccionar algunos activos destacados
    highlighted_assets = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META"]

    # Crear columnas para mostrar activos destacados
    cols = st.columns(3)

    for i, symbol in enumerate(highlighted_assets):
        with cols[i % 3]:
            try:
                # Obtener datos recientes
                asset_data = fetch_market_data(symbol, period="5d")

                if asset_data is not None and not asset_data.empty:
                    # Calcular cambio porcentual
                    last_price = asset_data["Close"].iloc[-1]
                    prev_price = asset_data["Close"].iloc[-2]
                    change_pct = (last_price - prev_price) / prev_price * 100

                    # Mostrar tarjeta de activo
                    display_asset_card(
                        symbol=symbol,
                        price=last_price,
                        change=change_pct,
                        sector=next(
                            (k for k, v in SYMBOLS.items() if symbol in v), None
                        ),
                        additional_info={
                            "Volumen": f"{asset_data['Volume'].iloc[-1]:,.0f}",
                            "Rango": f"${asset_data['Low'].iloc[-1]:.2f} - ${asset_data['High'].iloc[-1]:.2f}",
                        },
                    )
                else:
                    st.warning(f"No se pudieron obtener datos para {symbol}")
            except Exception as e:
                st.error(f"Error al mostrar {symbol}: {str(e)}")
                logger.error(f"Error en dashboard para {symbol}: {str(e)}")

    # Mostrar rendimiento por sector
    st.markdown("### 📊 Rendimiento por Sector")

    # Simular datos de rendimiento por sector
    sector_performance = {
        "Tecnología": 2.5,
        "Finanzas": -0.8,
        "Salud": 1.2,
        "Consumo": 0.5,
        "Energía": -1.5,
        "Industriales": 0.3,
        "Materiales": -0.2,
        "Servicios": 1.0,
        "Inmobiliario": -0.5,
        "Telecomunicaciones": 1.8,
    }

    # Crear DataFrame
    sector_df = pd.DataFrame(
        {
            "Sector": sector_performance.keys(),
            "Rendimiento (%)": sector_performance.values(),
        }
    )

    # Crear gráfico de barras
    fig = px.bar(
        sector_df,
        x="Sector",
        y="Rendimiento (%)",
        color="Rendimiento (%)",
        color_continuous_scale=["red", "yellow", "green"],
        range_color=[-2, 3],
        title="Rendimiento por Sector (Últimas 24h)",
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Mostrar calendario económico
    st.markdown("### 📅 Calendario Económico")

    # Simular datos de calendario económico
    economic_calendar = pd.DataFrame(
        {
            "Fecha": [
                current_date.strftime("%d/%m/%Y"),
                current_date.strftime("%d/%m/%Y"),
                (current_date + timedelta(days=1)).strftime("%d/%m/%Y"),
                (current_date + timedelta(days=1)).strftime("%d/%m/%Y"),
                (current_date + timedelta(days=2)).strftime("%d/%m/%Y"),
            ],
            "Hora": ["08:30", "14:00", "10:00", "16:30", "12:00"],
            "Evento": [
                "Informe de Empleo",
                "Decisión de Tipos de Interés",
                "IPC",
                "Inventarios de Petróleo",
                "Ventas Minoristas",
            ],
            "Impacto": ["Alto", "Alto", "Alto", "Medio", "Medio"],
            "País": ["EE.UU.", "EE.UU.", "Eurozona", "EE.UU.", "EE.UU."],
        }
    )

    # Mostrar tabla
    st.dataframe(
        economic_calendar,
        column_config={
            "Fecha": st.column_config.TextColumn("Fecha"),
            "Hora": st.column_config.TextColumn("Hora"),
            "Evento": st.column_config.TextColumn("Evento"),
            "Impacto": st.column_config.TextColumn("Impacto"),
            "País": st.column_config.TextColumn("País"),
        },
        use_container_width=True,
        hide_index=True,
    )
