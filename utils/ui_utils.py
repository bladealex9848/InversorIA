"""
Utilidades de UI para InversorIA Pro
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def display_header(title, subtitle=None):
    """
    Muestra un encabezado con estilo consistente
    """
    st.markdown(f"<h1 class='main-header'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<h2 class='sub-header'>{subtitle}</h2>", unsafe_allow_html=True)

def display_info_message(message):
    """
    Muestra un mensaje informativo con estilo
    """
    st.markdown(
        f"""
        <div class="info-message">
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )

def display_error_message(message):
    """
    Muestra un mensaje de error con estilo
    """
    st.markdown(
        f"""
        <div class="error-message">
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )

def display_asset_card(symbol, price, change, sector=None, additional_info=None):
    """
    Muestra una tarjeta de activo con información básica
    """
    change_color = "green" if change >= 0 else "red"
    change_sign = "+" if change >= 0 else ""
    
    st.markdown(
        f"""
        <div class="asset-card">
            <div class="asset-header">
                <h2 class="asset-name">{symbol}</h2>
                <div class="asset-price">${price:.2f} <span style="color:{change_color}; font-size:1rem;">({change_sign}{change:.2f}%)</span></div>
            </div>
            {f'<div class="asset-sector">{sector}</div>' if sector else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if additional_info:
        cols = st.columns(len(additional_info))
        for i, (label, value) in enumerate(additional_info.items()):
            with cols[i]:
                st.metric(label, value)

def create_candlestick_chart(df, title="Gráfico de Precios", height=500):
    """
    Crea un gráfico de velas con Plotly
    """
    fig = go.Figure()
    
    # Añadir gráfico de velas
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Precio",
        )
    )
    
    # Configurar diseño
    fig.update_layout(
        title=title,
        xaxis_title="Fecha",
        yaxis_title="Precio",
        height=height,
        xaxis_rangeslider_visible=False,
        template="plotly_white",
    )
    
    return fig

def format_timestamp(timestamp):
    """
    Formatea una marca de tiempo para mostrarla
    """
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except ValueError:
            return timestamp
    
    if isinstance(timestamp, datetime):
        return timestamp.strftime("%d/%m/%Y %H:%M")
    
    return str(timestamp)

def display_data_table(df, column_config=None, use_container_width=True, height=None):
    """
    Muestra una tabla de datos con formato mejorado
    """
    if column_config:
        return st.dataframe(
            df,
            column_config=column_config,
            use_container_width=use_container_width,
            height=height,
            hide_index=True,
        )
    else:
        return st.dataframe(
            df,
            use_container_width=use_container_width,
            height=height,
            hide_index=True,
        )
