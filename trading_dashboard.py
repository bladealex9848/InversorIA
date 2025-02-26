import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import traceback
import time
import os

from market_utils import (
    fetch_market_data,
    TechnicalAnalyzer,
    get_market_context,
    get_vix_level,
    clear_cache,
    OptionsParameterManager,
    logger
)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Constantes
TIMEFRAMES = {
    "Intradía": ["1m", "5m", "15m", "30m", "1h"],
    "Swing": ["1d", "1wk"],
    "Posicional": ["1mo", "3mo"]
}

# Paleta de colores profesional
COLORS = {
    "primary": "#1f77b4",       # Azul principal
    "secondary": "#ff7f0e",     # Naranja
    "success": "#2ca02c",       # Verde
    "danger": "#d62728",        # Rojo
    "warning": "#bcbd22",       # Amarillo
    "info": "#17becf",          # Azul claro
    "neutral": "#7f7f7f",       # Gris
    "accent1": "#9467bd",       # Morado
    "accent2": "#e377c2",       # Rosa
    "accent3": "#8c564b",       # Marrón
    "grid": "rgba(128,128,128,0.2)",  # Gris para grillas
    "background": "rgba(0,0,0,0)",    # Transparente
    "text": "#FFFFFF"           # Texto blanco
}

#=================================================
# COMPONENTES DE VISUALIZACIÓN
#=================================================

def create_advanced_chart(data, timeframe="diario", patterns=None, levels=None):
    """
    Crea gráfico técnico avanzado con análisis institucional.
    
    Args:
        data (pd.DataFrame): DataFrame con datos e indicadores
        timeframe (str): Texto descriptivo del timeframe mostrado
        patterns (list): Lista de patrones de velas detectados
        levels (dict): Diccionario con niveles de soporte y resistencia
    
    Returns:
        plotly.graph_objects.Figure: Figura Plotly completa
    """
    try:
        if data is None or len(data) < 2:
            logger.warning(f"Datos insuficientes para crear gráfico: {len(data) if data is not None else 0} registros")
            return None

        # Crear estructura de subplots
        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.4, 0.2, 0.2, 0.2],
            subplot_titles=(
                f"Análisis Técnico Avanzado ({timeframe})",
                "MACD & Señal",
                "RSI & Estocástico",
                "Volumen & OBV"
            )
        )

        #===== PANEL 1: OHLC, MEDIAS MÓVILES Y BANDAS DE BOLLINGER =====
        
        # Velas (OHLC)
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="OHLC",
                increasing_line_color=COLORS["success"],
                decreasing_line_color=COLORS["danger"]
            ),
            row=1, col=1
        )

        # Bandas de Bollinger
        for band, name, color in [
            ('BB_High', 'BB Superior', 'rgba(173, 204, 255, 0.3)'),
            ('BB_Mid', 'BB Media', 'rgba(173, 204, 255, 0.6)'),
            ('BB_Low', 'BB Inferior', 'rgba(173, 204, 255, 0.3)')
        ]:
            if band in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[band],
                        name=name,
                        line=dict(color=color, width=1),
                        fill='tonexty' if band == 'BB_Low' else None
                    ),
                    row=1, col=1
                )

        # Medias Móviles
        for ma, name, color, width in [
            ('SMA_20', 'SMA 20', COLORS["primary"], 1.5),
            ('SMA_50', 'SMA 50', COLORS["secondary"], 1.5),
            ('SMA_200', 'SMA 200', COLORS["danger"], 1.5)
        ]:
            ma_col = ma.replace('_', '')  # Compatibilidad con diferentes formatos de nombre
            if ma in data.columns:
                ma_col = ma
            elif ma_col in data.columns:
                ma_col = ma_col
            else:
                continue
                
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[ma_col],
                    name=name,
                    line=dict(color=color, width=width)
                ),
                row=1, col=1
            )
        
        # Añadir patrones de velas si están disponibles
        if patterns:
            for pattern in patterns:
                if pattern["position"] >= 0 and pattern["position"] < len(data):
                    # Obtener índice de tiempo correcto
                    if isinstance(pattern["position"], int):
                        pos_idx = pattern["position"]
                    else:
                        pos_idx = data.index.get_loc(pattern["position"])
                    
                    pattern_x = data.index[pos_idx]
                    pattern_y = data['High'].iloc[pos_idx] * 1.01  # Ligeramente por encima
                    
                    # Color según tipo de patrón
                    color = COLORS["success"] if "bullish" in pattern["type"] else \
                            COLORS["danger"] if "bearish" in pattern["type"] else \
                            COLORS["neutral"]
                    
                    # Añadir marcador y anotación
                    fig.add_trace(
                        go.Scatter(
                            x=[pattern_x],
                            y=[pattern_y],
                            mode="markers+text",
                            marker=dict(size=10, color=color, symbol="triangle-down" if "bearish" in pattern["type"] else "triangle-up"),
                            text=pattern["pattern"],
                            textposition="top center",
                            name=pattern["pattern"]
                        ),
                        row=1, col=1
                    )
        
        # Añadir niveles de soporte/resistencia si están disponibles
        if levels and isinstance(levels, dict):
            # Soportes
            if "supports" in levels and levels["supports"]:
                for level in levels["supports"]:
                    fig.add_shape(
                        type="line",
                        x0=data.index[0],
                        x1=data.index[-1],
                        y0=level,
                        y1=level,
                        line=dict(color=COLORS["success"], width=1, dash="dash"),
                        row=1, col=1
                    )
            
            # Resistencias
            if "resistances" in levels and levels["resistances"]:
                for level in levels["resistances"]:
                    fig.add_shape(
                        type="line",
                        x0=data.index[0],
                        x1=data.index[-1],
                        y0=level,
                        y1=level,
                        line=dict(color=COLORS["danger"], width=1, dash="dash"),
                        row=1, col=1
                    )

        #===== PANEL 2: MACD =====
        
        if all(x in data.columns for x in ['MACD', 'MACD_Signal', 'MACD_Hist']):
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['MACD'],
                    name='MACD',
                    line=dict(color=COLORS["primary"], width=1.5)
                ),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['MACD_Signal'],
                    name='Signal',
                    line=dict(color=COLORS["secondary"], width=1.5)
                ),
                row=2, col=1
            )

            # Histograma MACD con colores dinámicos
            colors = np.where(data['MACD_Hist'] >= 0, COLORS["success"], COLORS["danger"])
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['MACD_Hist'],
                    name='MACD Hist',
                    marker_color=colors,
                    opacity=0.5
                ),
                row=2, col=1
            )
            
            # Línea cero
            fig.add_shape(
                type="line",
                x0=data.index[0],
                x1=data.index[-1],
                y0=0,
                y1=0,
                line=dict(color="white", width=0.5, dash="dot"),
                row=2, col=1
            )

        #===== PANEL 3: RSI Y ESTOCÁSTICO =====
        
        if 'RSI' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['RSI'],
                    name='RSI',
                    line=dict(color=COLORS["accent1"], width=1.5)
                ),
                row=3, col=1
            )

            # Zonas RSI
            for level, color in [
                (70, 'rgba(239, 83, 80, 0.2)'),  # Zona sobrecompra
                (30, 'rgba(38, 166, 154, 0.2)')  # Zona sobreventa
            ]:
                fig.add_hline(
                    y=level,
                    line=dict(color='rgba(255,255,255,0.3)', width=1, dash='dash'),
                    row=3, col=1
                )
                
            # Área sombreada entre 30-70
            fig.add_shape(
                type="rect",
                x0=data.index[0],
                x1=data.index[-1],
                y0=30,
                y1=70,
                fillcolor="rgba(255,255,255,0.1)",
                line=dict(width=0),
                row=3, col=1
            )

        # Estocástico
        stoch_k_col = 'Stoch_K' if 'Stoch_K' in data.columns else 'StochK' if 'StochK' in data.columns else None
        stoch_d_col = 'Stoch_D' if 'Stoch_D' in data.columns else 'StochD' if 'StochD' in data.columns else None
        
        if stoch_k_col and stoch_d_col:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[stoch_k_col],
                    name='%K',
                    line=dict(color=COLORS["info"], width=1)
                ),
                row=3, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[stoch_d_col],
                    name='%D',
                    line=dict(color=COLORS["accent2"], width=1)
                ),
                row=3, col=1
            )
            
            # Líneas de sobrecompra/sobreventa para estocástico
            for level in [20, 80]:
                fig.add_shape(
                    type="line",
                    x0=data.index[0],
                    x1=data.index[-1],
                    y0=level,
                    y1=level,
                    line=dict(color='rgba(255,255,255,0.2)', width=1, dash="dot"),
                    row=3, col=1
                )

        #===== PANEL 4: VOLUMEN Y OBV =====
        
        if 'Volume' in data.columns:
            # Colores basados en dirección de precios
            volume_colors = np.where(
                data['Close'] >= data['Open'],
                'rgba(38, 166, 154, 0.5)',  # Verde para velas alcistas
                'rgba(239, 83, 80, 0.5)'    # Rojo para velas bajistas
            )
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volumen',
                    marker_color=volume_colors
                ),
                row=4, col=1
            )
            
            # Media móvil de volumen si está disponible
            if 'Volume_SMA' in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['Volume_SMA'],
                        name='Vol MA',
                        line=dict(color="white", width=1.5, dash="dash")
                    ),
                    row=4, col=1
                )

            # OBV normalizado si está disponible
            if 'OBV' in data.columns and data['OBV'].abs().max() > 0:
                # Normalizar OBV para visualización
                normalized_obv = (data['OBV'] - data['OBV'].min()) / (data['OBV'].max() - data['OBV'].min()) * data['Volume'].max() * 0.8
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=normalized_obv,
                        name='OBV Norm',
                        line=dict(color=COLORS["info"], width=1.5)
                    ),
                    row=4, col=1
                )
            elif 'OBV' in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['OBV'] * data['Volume'].max() / abs(data['OBV']).max() if abs(data['OBV']).max() > 0 else data['OBV'],
                        name='OBV',
                        line=dict(color=COLORS["info"], width=1.5)
                    ),
                    row=4, col=1
                )

        #===== CONFIGURACIÓN GENERAL DEL GRÁFICO =====
        
        # Layout profesional
        fig.update_layout(
            height=900,
            template='plotly_dark',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            xaxis_rangeslider_visible=False,
            margin=dict(l=50, r=50, t=60, b=50),
            paper_bgcolor=COLORS["background"],
            plot_bgcolor=COLORS["background"],
            font=dict(color=COLORS["text"])
        )

        # Grids y ejes
        for i in range(1, 5):
            fig.update_xaxes(
                gridcolor=COLORS["grid"],
                zerolinecolor='rgba(255,255,255,0.2)',
                showgrid=True,
                row=i,
                col=1
            )
            fig.update_yaxes(
                gridcolor=COLORS["grid"],
                zerolinecolor='rgba(255,255,255,0.2)',
                showgrid=True,
                row=i,
                col=1
            )

        return fig

    except Exception as e:
        logger.error(f"Error en visualización avanzada: {str(e)}\n{traceback.format_exc()}")
        return None

def create_multi_timeframe_chart(symbol, timeframes=["1d", "1wk", "1mo"]):
    """
    Crea un gráfico comparativo de múltiples timeframes.
    
    Args:
        symbol (str): Símbolo a analizar
        timeframes (list): Lista de timeframes a mostrar
    
    Returns:
        plotly.graph_objects.Figure: Figura Plotly
    """
    try:
        # Crear figura con subplots
        fig = make_subplots(
            rows=len(timeframes),
            cols=1,
            shared_xaxes=False,
            vertical_spacing=0.05,
            subplot_titles=[f"Timeframe: {tf}" for tf in timeframes]
        )
        
        # Para cada timeframe, obtener datos y añadir gráfico de velas
        for i, tf in enumerate(timeframes):
            try:
                # Cargar datos para este timeframe
                data = fetch_market_data(symbol, "1y", tf)
                
                if data is not None and len(data) > 1:
                    # Añadir velas
                    fig.add_trace(
                        go.Candlestick(
                            x=data.index,
                            open=data['Open'],
                            high=data['High'],
                            low=data['Low'],
                            close=data['Close'],
                            name=f"OHLC {tf}",
                            increasing_line_color=COLORS["success"],
                            decreasing_line_color=COLORS["danger"],
                            showlegend=False
                        ),
                        row=i+1, col=1
                    )
                    
                    # Añadir SMA 50 si hay suficientes datos
                    if len(data) >= 50:
                        sma50 = data['Close'].rolling(window=50).mean()
                        fig.add_trace(
                            go.Scatter(
                                x=data.index,
                                y=sma50,
                                name=f"SMA 50 ({tf})",
                                line=dict(color=COLORS["secondary"], width=1.5),
                                showlegend=False
                            ),
                            row=i+1, col=1
                        )
                    
                    # Añadir EMA 20 si hay suficientes datos
                    if len(data) >= 20:
                        ema20 = data['Close'].ewm(span=20, adjust=False).mean()
                        fig.add_trace(
                            go.Scatter(
                                x=data.index,
                                y=ema20,
                                name=f"EMA 20 ({tf})",
                                line=dict(color=COLORS["primary"], width=1.5),
                                showlegend=False
                            ),
                            row=i+1, col=1
                        )
                    
                    # Configurar eje Y específico
                    fig.update_yaxes(
                        title_text=f"{tf}",
                        gridcolor=COLORS["grid"],
                        zerolinecolor='rgba(255,255,255,0.2)',
                        row=i+1, col=1
                    )
                else:
                    fig.add_annotation(
                        x=0.5, y=0.5,
                        text=f"No hay datos suficientes para {tf}",
                        showarrow=False,
                        row=i+1, col=1
                    )
            except Exception as e:
                logger.error(f"Error en timeframe {tf}: {str(e)}")
                fig.add_annotation(
                    x=0.5, y=0.5,
                    text=f"Error procesando {tf}",
                    showarrow=False,
                    row=i+1, col=1
                )
        
        # Configuración general
        fig.update_layout(
            height=200 * len(timeframes),
            template='plotly_dark',
            showlegend=False,
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor=COLORS["background"],
            plot_bgcolor=COLORS["background"],
            font=dict(color=COLORS["text"])
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error en gráfico multi-timeframe: {str(e)}")
        return None

def create_options_matrix(symbol, price, signals, options_params):
    """
    Crea matriz visual de opciones disponibles.
    
    Args:
        symbol (str): Símbolo del activo
        price (float): Precio actual
        signals (dict): Señales técnicas
        options_params (dict): Parámetros de opciones
    
    Returns:
        plotly.graph_objects.Figure: Figura Plotly
    """
    try:
        # Calcular strikes aproximados basados en el precio actual
        strikes = []
        
        # Extraer distance_spot_strike del params
        if options_params and "distance_spot_strike" in options_params:
            distance_str = options_params["distance_spot_strike"]
            
            # Intentar extraer valor numérico
            import re
            distance_values = re.findall(r'(\d+(?:\.\d+)?)', distance_str)
            if distance_values:
                # Usar el primer valor numérico encontrado
                base_distance = float(distance_values[0])
            else:
                base_distance = 5.0  # Valor por defecto
        else:
            base_distance = 5.0  # Valor por defecto
        
        # Calcular distancia en puntos (ajustada según precio)
        distance_pct = base_distance / 100
        
        # Generar strikes
        for pct in [-3, -2, -1, -0.5, 0, 0.5, 1, 2, 3]:
            strike = round(price * (1 + pct * distance_pct), 2)
            strikes.append(strike)
        
        strikes.sort()
        
        # Crear datos para tabla de opciones
        call_data = []
        put_data = []
        
        # Estimar valores de opciones simplificados (simulados)
        for strike in strikes:
            # Premium estimado basado en distancia relativa al precio
            distance_to_price = abs(strike - price) / price
            base_premium = float(re.findall(r'\$(\d+\.\d+)', options_params.get("costo_strike", "$0.50"))[0]) if options_params else 0.50
            
            # Calcular delta teórico aproximado
            delta_call = max(0, min(1, 0.5 + (price - strike) / (price * 0.2)))
            delta_put = max(0, min(1, 0.5 + (strike - price) / (price * 0.2)))
            
            # Añadir datos de CALL
            call_data.append({
                "Strike": strike,
                "Premium": round(base_premium * (1 - distance_to_price * 0.5), 2),
                "Delta": round(delta_call, 2),
                "Volumen Est.": "Medio" if abs(strike - price) / price < 0.05 else "Bajo"
            })
            
            # Añadir datos de PUT
            put_data.append({
                "Strike": strike,
                "Premium": round(base_premium * (1 - distance_to_price * 0.5), 2),
                "Delta": round(delta_put, 2), 
                "Volumen Est.": "Medio" if abs(strike - price) / price < 0.05 else "Bajo"
            })
        
        # Crear figura con dos tablas (CALLs y PUTs)
        header_color = 'rgba(100, 100, 100, 0.7)'
        cell_color_calls = 'rgba(50, 200, 100, 0.2)'
        cell_color_puts = 'rgba(200, 50, 50, 0.2)'
        
        fig = go.Figure()
        
        # Posición de las tablas
        calls_pos_y = 0
        puts_pos_y = len(strikes) + 2  # +2 para espacio entre tablas
        
        # Añadir tabla de CALLs
        fig.add_trace(
            go.Table(
                header=dict(
                    values=["<b>CALL Strike</b>", "<b>Premium</b>", "<b>Delta</b>", "<b>Volumen</b>"],
                    line_color='darkslategray',
                    fill_color=header_color,
                    align='center',
                    font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=[
                        [d["Strike"] for d in call_data],
                        ["$" + str(d["Premium"]) for d in call_data],
                        [d["Delta"] for d in call_data],
                        [d["Volumen Est."] for d in call_data]
                    ],
                    line_color='darkslategray',
                    fill_color=[cell_color_calls],
                    align='center',
                    font=dict(color='white', size=11)
                ),
                domain=dict(y=[0.55, 1.0])
            )
        )
        
        # Añadir tabla de PUTs
        fig.add_trace(
            go.Table(
                header=dict(
                    values=["<b>PUT Strike</b>", "<b>Premium</b>", "<b>Delta</b>", "<b>Volumen</b>"],
                    line_color='darkslategray',
                    fill_color=header_color,
                    align='center',
                    font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=[
                        [d["Strike"] for d in put_data],
                        ["$" + str(d["Premium"]) for d in put_data],
                        [d["Delta"] for d in put_data],
                        [d["Volumen Est."] for d in put_data]
                    ],
                    line_color='darkslategray',
                    fill_color=[cell_color_puts],
                    align='center',
                    font=dict(color='white', size=11)
                ),
                domain=dict(y=[0.0, 0.45])
            )
        )
        
        # Configuración general
        fig.update_layout(
            title=f"Matriz de Opciones Estimada para {symbol} (Precio Actual: ${price})",
            template='plotly_dark',
            height=500,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor=COLORS["background"],
            plot_bgcolor=COLORS["background"],
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creando matriz de opciones: {str(e)}")
        return None

def render_technical_metrics(df_technical):
    """
    Renderiza métricas técnicas avanzadas e institucionales.
    
    Args:
        df_technical (pd.DataFrame): DataFrame con indicadores técnicos calculados
    """
    try:
        if df_technical is None or len(df_technical) < 2:
            st.warning("⚠️ Datos insuficientes para calcular métricas técnicas")
            return

        # 1. Métricas principales
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            price_change = ((df_technical['Close'].iloc[-1]/df_technical['Close'].iloc[-2])-1)*100
            st.metric(
                "Precio",
                f"${df_technical['Close'].iloc[-1]:.2f}",
                f"{price_change:.2f}%",
                delta_color="normal" if price_change >= 0 else "inverse"
            )

        with col2:
            # Verificar si RSI existe
            if 'RSI' in df_technical.columns:
                rsi_value = df_technical['RSI'].iloc[-1]
                rsi_status = (
                    "Sobrecomprado" if rsi_value > 70
                    else "Sobrevendido" if rsi_value < 30
                    else "Neutral"
                )
                st.metric(
                    "RSI",
                    f"{rsi_value:.1f}",
                    rsi_status,
                    delta_color="off" if rsi_status == "Neutral" else "inverse" if rsi_status == "Sobrecomprado" else "normal"
                )
            else:
                st.metric("RSI", "N/A", "No disponible")

        with col3:
            # Verificar si Volume existe
            if 'Volume' in df_technical.columns and df_technical['Volume'].mean() > 0:
                vol_ratio = df_technical['Volume'].iloc[-1] / df_technical['Volume'].mean()
                st.metric(
                    "Vol Ratio",
                    f"{vol_ratio:.2f}x",
                    f"{(vol_ratio-1)*100:.1f}% vs Media",
                    delta_color="normal" if vol_ratio > 1 else "inverse"
                )
            else:
                st.metric("Vol Ratio", "N/A", "No disponible")

        with col4:
            # Verificar si BB_Width existe
            if 'BB_Width' in df_technical.columns and df_technical['BB_Width'].mean() > 0:
                bb_width = df_technical['BB_Width'].iloc[-1]
                bb_avg = df_technical['BB_Width'].mean()
                st.metric(
                    "BB Width",
                    f"{bb_width:.3f}",
                    f"{(bb_width/bb_avg-1)*100:.1f}% vs Media",
                    delta_color="normal" if bb_width > bb_avg else "inverse"
                )
            else:
                st.metric("BB Width", "N/A", "No disponible")

        # 2. Análisis institucional expandido
        with st.expander("🔍 Análisis Institucional", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### Tendencia & Momentum")
                
                # Comprobamos la existencia de indicadores antes de usar
                sma_trend = "Alcista" if ('SMA_20' in df_technical.columns and 
                                         'SMA_50' in df_technical.columns and 
                                         df_technical['SMA_20'].iloc[-1] > df_technical['SMA_50'].iloc[-1]) else "Bajista"
                
                macd_signal = "Alcista" if ('MACD' in df_technical.columns and 
                                           'MACD_Signal' in df_technical.columns and 
                                           df_technical['MACD'].iloc[-1] > df_technical['MACD_Signal'].iloc[-1]) else "Bajista"
                
                rsi_value = f"{df_technical['RSI'].iloc[-1]:.1f}" if 'RSI' in df_technical.columns else "N/A"
                
                stoch_k_col = 'Stoch_K' if 'Stoch_K' in df_technical.columns else 'StochK' if 'StochK' in df_technical.columns else None
                stoch_d_col = 'Stoch_D' if 'Stoch_D' in df_technical.columns else 'StochD' if 'StochD' in df_technical.columns else None
                
                stoch_k = f"{df_technical[stoch_k_col].iloc[-1]:.1f}" if stoch_k_col else "N/A"
                
                st.markdown(f"""
                - **Tendencia MA:** {sma_trend} {'🔼' if sma_trend == 'Alcista' else '🔽'}
                - **MACD Signal:** {macd_signal} {'🔼' if macd_signal == 'Alcista' else '🔽'}
                - **RSI:** {rsi_value}
                - **Estocástico %K:** {stoch_k}
                """)
                
                # Direccionalidad general del mercado
                st.markdown("#### Direccionalidad")
                direction = "ALCISTA" if sma_trend == "Alcista" and macd_signal == "Alcista" else \
                            "BAJISTA" if sma_trend == "Bajista" and macd_signal == "Bajista" else \
                            "MIXTA"
                st.markdown(f"""
                <div style="background-color:{'rgba(38, 166, 154, 0.2)' if direction == 'ALCISTA' else 'rgba(239, 83, 80, 0.2)' if direction == 'BAJISTA' else 'rgba(255, 255, 255, 0.1)'}; 
                    padding: 10px; 
                    border-radius: 5px;
                    text-align: center;">
                    <span style="font-size: 16px; font-weight: bold;">
                        {direction} {'↗️' if direction == 'ALCISTA' else '↘️' if direction == 'BAJISTA' else '↔️'}
                    </span>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("### Volatilidad & Risk")
                
                # Calculamos métricas solo si existen los datos necesarios
                if 'Close' in df_technical.columns and len(df_technical) > 1:
                    hist_vol = df_technical['Close'].pct_change().std() * np.sqrt(252) * 100
                else:
                    hist_vol = 0
                
                bb_width = df_technical['BB_Width'].iloc[-1] if 'BB_Width' in df_technical.columns else 0
                
                atr_ratio = (df_technical['ATR'].iloc[-1]/df_technical['ATR'].mean() 
                           if 'ATR' in df_technical.columns and df_technical['ATR'].mean() > 0 
                           else 0)
                
                bb_percentile = ((df_technical['BB_Width'] <= bb_width).mean()*100 
                               if 'BB_Width' in df_technical.columns 
                               else 0)
                
                st.markdown(f"""
                - **Vol Histórica:** {hist_vol:.1f}%
                - **BB Width:** {bb_width:.3f}
                - **ATR Ratio:** {atr_ratio:.2f}
                - **Vol Percentil:** {bb_percentile:.0f}%
                """)
                
                # Estado de volatilidad
                st.markdown("#### Estado de Volatilidad")
                vol_state = "ALTA" if bb_width > df_technical['BB_Width'].mean() * 1.3 else \
                            "BAJA" if bb_width < df_technical['BB_Width'].mean() * 0.7 else \
                            "NORMAL"
                
                vol_color = "rgba(239, 83, 80, 0.2)" if vol_state == "ALTA" else \
                            "rgba(38, 166, 154, 0.2)" if vol_state == "BAJA" else \
                            "rgba(255, 255, 255, 0.1)"
                
                st.markdown(f"""
                <div style="background-color:{vol_color}; 
                    padding: 10px; 
                    border-radius: 5px;
                    text-align: center;">
                    <span style="font-size: 16px; font-weight: bold;">
                        {vol_state} {'📈' if vol_state == 'ALTA' else '📉' if vol_state == 'BAJA' else '📊'}
                    </span>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown("### Volumen & Flujo")
                
                # Verificamos existencia de datos de volumen
                if 'Volume' in df_technical.columns and df_technical['Volume'].mean() > 0:
                    vol_ratio = df_technical['Volume'].iloc[-1] / df_technical['Volume'].mean()
                else:
                    vol_ratio = 0
                
                vwap_pos = ('Por encima' if 'VWAP' in df_technical.columns and 
                           df_technical['Close'].iloc[-1] > df_technical['VWAP'].iloc[-1] 
                           else 'Por debajo')
                
                obv_trend = ('Alcista' if 'OBV' in df_technical.columns and 
                           len(df_technical) > 1 and 
                           df_technical['OBV'].iloc[-1] > df_technical['OBV'].iloc[-2] 
                           else 'Bajista')
                
                if all(x in df_technical.columns for x in ['High', 'Low', 'Close']):
                    vol_spread = (df_technical['High'].iloc[-1] - df_technical['Low'].iloc[-1])/df_technical['Close'].iloc[-1]*100
                else:
                    vol_spread = 0
                
                st.markdown(f"""
                - **Vol/Avg:** {vol_ratio:.2f}x
                - **VWAP Pos:** {vwap_pos}
                - **OBV Trend:** {obv_trend}
                - **Vol Spread:** {vol_spread:.2f}%
                """)
                
                # Presión del volumen
                st.markdown("#### Presión del Volumen")
                
                vol_pressure = "ALTA" if vol_ratio > 1.5 else \
                               "MEDIA" if vol_ratio > 0.8 else \
                               "BAJA"
                
                vol_direction = "COMPRADORA" if obv_trend == "Alcista" and df_technical['Close'].iloc[-1] > df_technical['Open'].iloc[-1] else \
                                "VENDEDORA" if obv_trend == "Bajista" and df_technical['Close'].iloc[-1] < df_technical['Open'].iloc[-1] else \
                                "NEUTRAL"
                
                pressure_color = "rgba(38, 166, 154, 0.2)" if vol_direction == "COMPRADORA" else \
                                 "rgba(239, 83, 80, 0.2)" if vol_direction == "VENDEDORA" else \
                                 "rgba(255, 255, 255, 0.1)"
                
                st.markdown(f"""
                <div style="background-color:{pressure_color}; 
                    padding: 10px; 
                    border-radius: 5px;
                    text-align: center;">
                    <span style="font-size: 16px; font-weight: bold;">
                        {vol_pressure} {vol_direction}
                    </span>
                </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Error en métricas técnicas: {str(e)}\n{traceback.format_exc()}")
        st.warning("❌ No se pudieron calcular todas las métricas debido a datos insuficientes o errores")

def render_options_recommendation(symbol, price, signals, options_params, vix_level):
    """
    Renderiza la sección de recomendación de opciones.
    
    Args:
        symbol (str): Símbolo del activo
        price (float): Precio actual
        signals (dict): Señales técnicas
        options_params (dict): Parámetros de opciones
        vix_level (float): Nivel actual del VIX
    """
    try:
        st.subheader("🎯 Recomendación de Opciones")
        
        # Verificar si tenemos señales y opciones de opciones
        if signals and "options" in signals:
            options_signal = signals["options"]
            
            # Mostrar recomendación principal con color
            direction = options_signal["direction"]
            confidence = options_signal["confidence"]
            timeframe = options_signal["timeframe"]
            strategy = options_signal["strategy"]
            
            # Determinar colores basados en dirección
            direction_color = "rgba(38, 166, 154, 0.2)" if direction == "CALL" else \
                             "rgba(239, 83, 80, 0.2)" if direction == "PUT" else \
                             "rgba(255, 255, 255, 0.1)"
            
            confidence_label = "⭐⭐⭐" if confidence == "ALTA" else \
                              "⭐⭐" if confidence == "MEDIA" else \
                              "⭐"
            
            # Columna para la recomendación principal
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background-color:{direction_color}; 
                    padding: 15px; 
                    border-radius: 5px;
                    margin-bottom: 12px;">
                    <h3 style="margin: 0; text-align: center;">
                        {direction} {' 📈' if direction == 'CALL' else ' 📉' if direction == 'PUT' else ''}
                    </h3>
                    <p style="text-align: center; margin: 5px 0;">
                        <span style="font-weight: bold;">Confianza:</span> {confidence} {confidence_label}<br>
                        <span style="font-weight: bold;">Timeframe:</span> {timeframe}<br>
                        <span style="font-weight: bold;">Estrategia:</span> {strategy}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Mostrar ajustes por volatilidad
                st.markdown("### Ajustes VIX")
                st.metric("Nivel VIX", f"{vix_level:.2f}", 
                         delta=f"{'Alto' if vix_level > 25 else 'Bajo' if vix_level < 15 else 'Normal'}", 
                         delta_color="inverse" if vix_level > 25 else "normal" if vix_level < 15 else "off")
                
                options_manager = OptionsParameterManager()
                vol_adjustments = options_manager.get_volatility_adjustments(vix_level)
                
                if vol_adjustments:
                    st.caption(f"**{vol_adjustments['category'].upper()}**: {vol_adjustments['description']}")
            
            # Niveles para opciones (usando línea separadora)
            st.markdown("---")
            
            # Parámetros de strike y monitoreo
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📊 Parámetros")
                
                # Información de opciones desde options_params
                if options_params:
                    st.markdown(f"""
                    - **Costo/Strike:** {options_params.get('costo_strike', 'N/A')}
                    - **Volumen Mín.:** {options_params.get('volumen_min', 'N/A')}
                    - **Distancia Spot-Strike:** {options_params.get('distance_spot_strike', 'N/A')}
                    """)
                else:
                    st.info("No hay parámetros específicos disponibles para este símbolo.")
            
            with col2:
                st.markdown("### 🔍 Niveles")
                
                # Calcular strike
                if options_params and "distance_spot_strike" in options_params:
                    import re
                    distance_values = re.findall(r'(\d+(?:\.\d+)?)', options_params["distance_spot_strike"])
                    if distance_values:
                        distance = float(distance_values[0])
                    else:
                        distance = 5.0
                else:
                    distance = 5.0
                
                # Convertir puntos a porcentaje
                distance_pct = distance / 100
                
                if direction == "CALL":
                    # Strike para CALL
                    strike = round(price * (1 + distance_pct), 2)
                    stop_price = round(price * 0.96, 2)  # 4% por debajo para stop
                    
                    st.markdown(f"""
                    - **Entrada:** ${price:.2f} (actual)
                    - **Strike recomendado:** ${strike:.2f} 
                    - **Stop Loss precio subyacente:** ${stop_price:.2f}
                    """)
                    
                elif direction == "PUT":
                    # Strike para PUT
                    strike = round(price * (1 - distance_pct), 2)
                    stop_price = round(price * 1.04, 2)  # 4% por encima para stop
                    
                    st.markdown(f"""
                    - **Entrada:** ${price:.2f} (actual)
                    - **Strike recomendado:** ${strike:.2f}
                    - **Stop Loss precio subyacente:** ${stop_price:.2f}
                    """)
                
                else:
                    st.info("Sin dirección clara para recomendar strike.")
            
            with col3:
                st.markdown("### ⏱️ Duración")
                
                # Recomendaciones de duración basadas en timeframe
                if timeframe == "CORTO":
                    st.markdown("""
                    - **Expiración recomendada:** 1-2 semanas
                    - **Monitoreo:** Diario
                    - **Toma de ganancias:** 40-60%
                    """)
                    
                elif timeframe == "MEDIO":
                    st.markdown("""
                    - **Expiración recomendada:** 3-6 semanas
                    - **Monitoreo:** 2-3 veces por semana
                    - **Toma de ganancias:** 50-80%
                    """)
                    
                else:  # LARGO
                    st.markdown("""
                    - **Expiración recomendada:** 2-3 meses
                    - **Monitoreo:** Semanal
                    - **Toma de ganancias:** 70-100%
                    """)
            
            # Matriz visual de opciones
            st.markdown("### Matriz de Opciones Estimada")
            options_matrix = create_options_matrix(symbol, price, signals, options_params)
            if options_matrix:
                st.plotly_chart(options_matrix, use_container_width=True)
            else:
                st.warning("No se pudo generar la matriz de opciones.")
            
            # Gestión de riesgo
            with st.expander("📉 Gestión de Riesgo"):
                st.markdown("""
                ### Recomendaciones de Gestión de Riesgo
                
                1. **Tamaño de posición:**
                   - Máximo 2-5% del capital por operación de opciones
                   - Considerar reducir aún más en alta volatilidad
                
                2. **Stop Loss:**
                   - Fixed Stop: 50% del premium pagado
                   - Trailing Stop: Activar después de 30% de ganancia
                
                3. **Toma de Ganancias:**
                   - Take Profit parcial: 50% de la posición al 40% de ganancia
                   - Take Profit total: 80-100% de ganancia
                
                4. **Reglas de Ejecución:**
                   - No perseguir operaciones perdidas
                   - No promediar a la baja en opciones
                   - Evitar hold overnight sin hedge
                """)
        else:
            st.info("No hay suficientes datos para generar recomendaciones de opciones.")
            
    except Exception as e:
        logger.error(f"Error en recomendación de opciones: {str(e)}")
        st.warning("Error generando recomendaciones de opciones.")

def render_multi_timeframe_analysis(symbol, multi_tf_analysis):
    """
    Renderiza análisis multi-timeframe.
    
    Args:
        symbol (str): Símbolo del activo
        multi_tf_analysis (dict): Análisis técnico en múltiples timeframes
    """
    try:
        st.subheader("📊 Análisis Multi-Timeframe")
        
        if not multi_tf_analysis:
            st.warning("No hay análisis multi-timeframe disponible.")
            return
            
        # Verificar si hay error
        if "error" in multi_tf_analysis:
            st.error(f"Error en análisis multi-timeframe: {multi_tf_analysis['error']}")
            return
            
        # Verificar si hay análisis consolidado
        if "consolidated" in multi_tf_analysis:
            consolidated = multi_tf_analysis["consolidated"]
            
            # Mostrar señal consolidada con estilo
            signal = consolidated["signal"]
            confidence = consolidated["confidence"]
            alignment = consolidated["timeframe_alignment"]
            
            # Color basado en señal
            signal_color = "rgba(38, 166, 154, 0.2)" if signal in ["compra", "compra_fuerte"] else \
                         "rgba(239, 83, 80, 0.2)" if signal in ["venta", "venta_fuerte"] else \
                         "rgba(255, 255, 255, 0.1)"
            
            # Presentación de señal consolidada
            st.markdown(f"""
            <div style="background-color:{signal_color}; 
                padding: 10px; 
                border-radius: 5px;
                margin-bottom: 12px;
                text-align: center;">
                <h3 style="margin: 0;">
                    Señal Consolidada: {signal.upper()} 
                    {'📈' if signal in ["compra", "compra_fuerte"] else '📉' if signal in ["venta", "venta_fuerte"] else '↔️'}
                </h3>
                <p style="margin: 5px 0;">
                    <span style="font-weight: bold;">Confianza:</span> {confidence.upper()}<br>
                    <span style="font-weight: bold;">Alineación:</span> {alignment}<br>
                    <span style="font-weight: bold;">Recomendación Opciones:</span> {consolidated["options_recommendation"]}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar comparativa de timeframes en tabla
        timeframes = [tf for tf in multi_tf_analysis.keys() if tf != "consolidated" and tf != "error"]
        
        if timeframes:
            # Crear datos para tabla de comparación
            tf_data = []
            for tf in timeframes:
                signals = multi_tf_analysis[tf]
                if signals and "overall" in signals:
                    tf_data.append({
                        "Timeframe": tf,
                        "Señal": signals["overall"]["signal"],
                        "Confianza": signals["overall"]["confidence"],
                        "RSI": signals["momentum"]["rsi"],
                        "MACD": "Alcista" if signals["trend"]["macd"] == "alcista" else "Bajista",
                        "Volumen": "Alto" if signals["volume"]["ratio"] > 1.2 else "Medio" if signals["volume"]["ratio"] > 0.8 else "Bajo"
                    })
            
            if tf_data:
                # Convertir a DataFrame para mostrar como tabla estilizada
                df_tf = pd.DataFrame(tf_data)
                
                # Aplicar estilos
                def color_signal(val):
                    if 'compra' in val:
                        return 'background-color: rgba(38, 166, 154, 0.2)'
                    elif 'venta' in val:
                        return 'background-color: rgba(239, 83, 80, 0.2)'
                    else:
                        return ''
                
                # Aplicar estilo y mostrar tabla
                styled_df = df_tf.style.applymap(color_signal, subset=['Señal'])
                st.dataframe(styled_df, use_container_width=True)
                
                # Mostrar gráfico comparativo
                st.markdown("### Comparativa Visual de Timeframes")
                multi_chart = create_multi_timeframe_chart(symbol, timeframes)
                if multi_chart:
                    st.plotly_chart(multi_chart, use_container_width=True)
        else:
            st.info("No hay datos de timeframes individuales disponibles.")
            
        # Descargo de responsabilidad sobre el análisis multi-timeframe
        st.caption("""
        **Nota sobre análisis multi-timeframe**: Las señales en diferentes timeframes pueden 
        parecer contradictiorias. Generalmente, los timeframes más largos tienen prioridad para 
        inversiones a medio/largo plazo, mientras que los cortos son más útiles para trading activo.
        """)
            
    except Exception as e:
        logger.error(f"Error en análisis multi-timeframe: {str(e)}")
        st.warning("Error procesando análisis multi-timeframe.")

def render_candle_patterns_analysis(patterns):
    """
    Renderiza análisis de patrones de velas.
    
    Args:
        patterns (list): Lista de patrones de velas detectados
    """
    try:
        st.subheader("🕯️ Patrones de Velas")
        
        if not patterns:
            st.info("No se detectaron patrones de velas significativos en este período.")
            return
            
        # Agrupar patrones por tipo (alcista/bajista)
        bullish_patterns = [p for p in patterns if "bullish" in p.get("type", "")]
        bearish_patterns = [p for p in patterns if "bearish" in p.get("type", "")]
        neutral_patterns = [p for p in patterns if "bullish" not in p.get("type", "") and "bearish" not in p.get("type", "")]
        
        # Usar columnas para mostrar patrones por tipo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📈 Patrones Alcistas")
            if bullish_patterns:
                for pattern in bullish_patterns:
                    st.markdown(f"""
                    <div style="background-color: rgba(38, 166, 154, 0.2); padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                        <strong>{pattern["pattern"]}</strong><br>
                        Tipo: {pattern["type"]}<br>
                        Fuerza: {pattern["strength"]}<br>
                        Fecha: {pattern["date"].strftime("%Y-%m-%d") if hasattr(pattern["date"], "strftime") else pattern["date"]}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No se detectaron patrones alcistas.")
                
        with col2:
            st.markdown("### 📉 Patrones Bajistas")
            if bearish_patterns:
                for pattern in bearish_patterns:
                    st.markdown(f"""
                    <div style="background-color: rgba(239, 83, 80, 0.2); padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                        <strong>{pattern["pattern"]}</strong><br>
                        Tipo: {pattern["type"]}<br>
                        Fuerza: {pattern["strength"]}<br>
                        Fecha: {pattern["date"].strftime("%Y-%m-%d") if hasattr(pattern["date"], "strftime") else pattern["date"]}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No se detectaron patrones bajistas.")
                
        with col3:
            st.markdown("### ↔️ Patrones Neutrales")
            if neutral_patterns:
                for pattern in neutral_patterns:
                    st.markdown(f"""
                    <div style="background-color: rgba(255, 255, 255, 0.1); padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                        <strong>{pattern["pattern"]}</strong><br>
                        Tipo: {pattern["type"]}<br>
                        Fuerza: {pattern["strength"]}<br>
                        Fecha: {pattern["date"].strftime("%Y-%m-%d") if hasattr(pattern["date"], "strftime") else pattern["date"]}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No se detectaron patrones neutrales.")
                
        # Explicación de patrones
        with st.expander("ℹ️ Interpretación de Patrones"):
            st.markdown("""
            ### Guía de Interpretación de Patrones
            
            **Patrones Alcistas**
            - **Martillo**: Posible fin de tendencia bajista, indica presión compradora después de un período vendedor
            - **Envolvente alcista**: Señal fuerte de reversal alcista, la segunda vela envuelve a la primera
            - **Doji en soporte**: Indecisión en niveles de soporte, posible pausa antes de reanudación alcista
            
            **Patrones Bajistas**
            - **Hombre Colgado**: Posible fin de tendencia alcista, señal de agotamiento comprador
            - **Envolvente bajista**: Señal fuerte de reversal bajista
            - **Estrella Fugaz**: Señal bajista tras tendencia alcista, presión vendedora en máximos
            
            **Consejos de Trading**
            - Combinar patrones con niveles técnicos (soportes/resistencias)
            - Confirmar señales con indicadores (RSI, MACD)
            - Considerar volumen para validar fuerza del patrón
            """)
            
    except Exception as e:
        logger.error(f"Error en análisis de patrones: {str(e)}")
        st.warning("Error procesando patrones de velas.")

def render_support_resistance_levels(levels, price):
    """
    Renderiza niveles de soporte y resistencia.
    
    Args:
        levels (dict): Diccionario con niveles de soporte y resistencia
        price (float): Precio actual
    """
    try:
        st.subheader("📏 Niveles Clave")
        
        if not levels or not isinstance(levels, dict):
            st.info("No hay niveles de soporte y resistencia disponibles.")
            return
            
        # Extraer niveles
        supports = levels.get("supports", [])
        resistances = levels.get("resistances", [])
        fibonacci = levels.get("fibonacci", {})
        
        # Ordenar niveles
        supports = sorted(supports, reverse=True)
        resistances = sorted(resistances)
        
        # Calcular distancia porcentual al precio actual
        def distance_to_price(level):
            return ((level / price) - 1) * 100
            
        # Añadir indicador de nivel más cercano
        nearest_support = min(supports, key=lambda x: abs(x - price)) if supports else None
        nearest_resistance = min(resistances, key=lambda x: abs(x - price)) if resistances else None
        
        # Mostrar niveles
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Resistencias")
            if resistances:
                for level in resistances:
                    dist = distance_to_price(level)
                    is_nearest = level == nearest_resistance
                    
                    st.markdown(f"""
                    <div style="
                        background-color: {'rgba(239, 83, 80, 0.3)' if is_nearest else 'rgba(239, 83, 80, 0.1)'};
                        padding: 8px;
                        border-radius: 5px;
                        margin-bottom: 5px;
                        display: flex;
                        justify-content: space-between;
                    ">
                        <span><strong>${level:.2f}</strong> {' ⭐' if is_nearest else ''}</span>
                        <span>{dist:.2f}% {'⬆️' if dist > 0 else '⬇️'}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hay resistencias detectadas.")
        
        with col2:
            st.markdown("### Soportes")
            if supports:
                for level in supports:
                    dist = distance_to_price(level)
                    is_nearest = level == nearest_support
                    
                    st.markdown(f"""
                    <div style="
                        background-color: {'rgba(38, 166, 154, 0.3)' if is_nearest else 'rgba(38, 166, 154, 0.1)'};
                        padding: 8px;
                        border-radius: 5px;
                        margin-bottom: 5px;
                        display: flex;
                        justify-content: space-between;
                    ">
                        <span><strong>${level:.2f}</strong> {' ⭐' if is_nearest else ''}</span>
                        <span>{dist:.2f}% {'⬆️' if dist > 0 else '⬇️'}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hay soportes detectados.")
        
        # Mostrar niveles de Fibonacci si están disponibles
        if fibonacci:
            st.markdown("### Niveles de Fibonacci")
            
            # Crear datos para tabla
            fib_data = []
            for ratio, level in fibonacci.items():
                dist = distance_to_price(level)
                fib_data.append({
                    "Ratio": ratio,
                    "Nivel": f"${level:.2f}",
                    "Distancia": f"{dist:.2f}%"
                })
            
            # Convertir a DataFrame y mostrar
            df_fib = pd.DataFrame(fib_data)
            st.dataframe(df_fib, use_container_width=True)
            
        # Mostrar información sobre zonas de valor
        with st.expander("📍 Zonas de Valor"):
            st.markdown("""
            ### Zonas de Trading
            
            #### Soportes
            Los soportes son niveles de precio donde históricamente la presión compradora ha superado a la vendedora, 
            deteniendo la caída de precios. Son zonas ideales para:
            - Entrada en posiciones CALL (alcistas)
            - Colocación de stops ajustados para posiciones PUT
            - Zonas de escalado en posiciones alcistas
            
            #### Resistencias
            Las resistencias son niveles donde la presión vendedora ha superado a la compradora en el pasado, 
            frenando las subidas. Son zonas ideales para:
            - Entrada en posiciones PUT (bajistas)
            - Toma de beneficios en posiciones CALL
            - Colocación de stops ajustados para posiciones CALL
            
            #### Estrategias en Niveles
            - **Rebote**: Entrar en la dirección de la tendencia principal al tocar un nivel
            - **Ruptura**: Esperar confirmación de ruptura del nivel y entrar en esa dirección
            - **Falso Quiebre**: Entrar en contra de la ruptura cuando el precio vuelve al nivel
            """)
            
    except Exception as e:
        logger.error(f"Error en niveles de soporte/resistencia: {str(e)}")
        st.warning("Error procesando niveles de soporte y resistencia.")

def render_technical_tab(symbol, timeframe, context=None):
    """
    Renderiza pestaña de análisis técnico avanzado.
    
    Args:
        symbol (str): Símbolo a analizar
        timeframe (str): Timeframe seleccionado
        context (dict, optional): Contexto de mercado preexistente
    """
    try:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected_timeframe = st.selectbox(
                "Timeframe",
                [tf for group in TIMEFRAMES.values() for tf in group],
                index=[tf for group in TIMEFRAMES.values() for tf in group].index(timeframe) if timeframe in [tf for group in TIMEFRAMES.values() for tf in group] else 4
            )
            # Actualizar timeframe si cambia la selección
            if selected_timeframe != timeframe:
                timeframe = selected_timeframe
        with col2:
            chart_type = st.selectbox(
                "Tipo de Gráfico",
                ["Candlestick con Indicadores", "Precio Simple", "Soportes/Resistencias", "Patrones de Velas"]
            )
        with col3:
            indicator_sets = st.multiselect(
                "Indicadores",
                ["Tendencia", "Momentum", "Volatilidad", "Volumen"],
                default=["Tendencia", "Momentum"]
            )

        # 1. Conseguir contexto de mercado si no fue proporcionado
        if context is None:
            with st.spinner("Analizando mercado..."):
                context = get_market_context(symbol)
                
        # 2. Verificar si hay errores
        if context and "error" in context:
            st.error(f"Error obteniendo datos: {context['error']}")
            
            # Mostrar mensaje para intentar con otro timeframe
            st.info("""
            **¿Por qué no intentar con otro timeframe?**
            Los errores pueden ocurrir por falta de datos en timeframes específicos.
            Intente con un timeframe más común como 1d (diario) o 1wk (semanal).
            """)
            return
            
        # 3. Mostrar datos disponibles del contexto
        if context:
            # Obtener datos del timeframe seleccionado si cambia
            if timeframe != "1d":
                with st.spinner(f"Cargando timeframe {timeframe}..."):
                    data = fetch_market_data(symbol, "1y", timeframe)
                    
                    if data is None or len(data) < 5:
                        st.warning(f"No hay datos suficientes para {symbol} en timeframe {timeframe}")
                        # Intentar con datos diarios
                        data = fetch_market_data(symbol, "1y", "1d")
                        if data is None or len(data) < 5:
                            st.error("No se pudieron obtener datos. Intente con otro símbolo.")
                            return
                            
                    # Calcular indicadores para este timeframe
                    analyzer = TechnicalAnalyzer(data)
                    df_technical = analyzer.calculate_indicators()
                    
                    # Obtener patrones y niveles
                    patterns = analyzer.get_candle_patterns()
                    levels = analyzer.get_support_resistance()
                    
            else:
                # Usar datos del contexto
                data = fetch_market_data(symbol)
                analyzer = TechnicalAnalyzer(data)
                df_technical = analyzer.calculate_indicators()
                patterns = context.get("candle_patterns", [])
                levels = context.get("support_resistance", {})
            
            # 4. Mostrar gráfico según tipo seleccionado
            if chart_type == "Candlestick con Indicadores":
                fig = create_advanced_chart(df_technical, timeframe, patterns, levels)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No se pudo generar el gráfico técnico")
                    
            elif chart_type == "Precio Simple":
                # Gráfico simple de precios
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data["Close"],
                        name="Precio",
                        line=dict(color=COLORS["primary"], width=2)
                    )
                )
                fig.update_layout(
                    title=f"Precio de {symbol}",
                    template="plotly_dark",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Soportes/Resistencias":
                # Gráfico con enfoque en soportes y resistencias
                fig = go.Figure()
                
                # Añadir precio
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data["Close"],
                        name="Precio",
                        line=dict(color=COLORS["primary"], width=2)
                    )
                )
                
                # Añadir soportes y resistencias
                if levels:
                    for support in levels.get("supports", []):
                        fig.add_shape(
                            type="line",
                            x0=data.index[0],
                            x1=data.index[-1],
                            y0=support,
                            y1=support,
                            line=dict(color=COLORS["success"], width=1.5, dash="dash"),
                        )
                        
                    for resistance in levels.get("resistances", []):
                        fig.add_shape(
                            type="line",
                            x0=data.index[0],
                            x1=data.index[-1],
                            y0=resistance,
                            y1=resistance,
                            line=dict(color=COLORS["danger"], width=1.5, dash="dash"),
                        )
                
                fig.update_layout(
                    title=f"Soportes y Resistencias de {symbol}",
                    template="plotly_dark",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Patrones de Velas":
                # Gráfico con enfoque en patrones de velas
                fig = go.Figure()
                
                # Añadir velas
                fig.add_trace(
                    go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name="OHLC",
                        increasing_line_color=COLORS["success"],
                        decreasing_line_color=COLORS["danger"]
                    )
                )
                
                # Añadir anotaciones para patrones
                if patterns:
                    for pattern in patterns:
                        if pattern["position"] >= 0 and pattern["position"] < len(data):
                            # Obtener posición correcta
                            if isinstance(pattern["position"], int):
                                pos_idx = pattern["position"]
                            else:
                                pos_idx = data.index.get_loc(pattern["position"])
                                
                            pattern_x = data.index[pos_idx]
                            
                            # Posición vertical según tipo de patrón
                            if "bearish" in pattern["type"]:
                                pattern_y = data['High'].iloc[pos_idx] * 1.02  # Por encima para bajistas
                                symbol_shape = "triangle-down"
                                color = COLORS["danger"]
                            else:
                                pattern_y = data['Low'].iloc[pos_idx] * 0.98  # Por debajo para alcistas
                                symbol_shape = "triangle-up"
                                color = COLORS["success"]
                            
                            # Añadir marcador
                            fig.add_trace(
                                go.Scatter(
                                    x=[pattern_x],
                                    y=[pattern_y],
                                    mode="markers+text",
                                    marker=dict(
                                        size=12,
                                        color=color,
                                        symbol=symbol_shape
                                    ),
                                    text=pattern["pattern"],
                                    textposition="bottom center" if "bearish" in pattern["type"] else "top center",
                                    name=pattern["pattern"]
                                )
                            )
                
                fig.update_layout(
                    title=f"Patrones de Velas de {symbol}",
                    template="plotly_dark",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # 5. Mostrar métricas técnicas
            render_technical_metrics(df_technical)
            
            # 6. Mostrar patrones de velas
            if patterns:
                render_candle_patterns_analysis(patterns)
            
            # 7. Mostrar niveles de soporte y resistencia
            if levels:
                render_support_resistance_levels(levels, context.get("last_price", 0))
        else:
            st.warning("No hay datos disponibles para el análisis técnico.")
    
    except Exception as e:
        logger.error(f"Error en tab técnico: {str(e)}\n{traceback.format_exc()}")
        st.error(f"Error procesando análisis técnico: {str(e)}")

def render_options_tab(symbol, context=None):
    """
    Renderiza pestaña de análisis de opciones.
    
    Args:
        symbol (str): Símbolo a analizar
        context (dict, optional): Contexto de mercado preexistente
    """
    try:
        # 1. Conseguir contexto de mercado si no fue proporcionado
        if context is None:
            with st.spinner("Analizando mercado y opciones..."):
                context = get_market_context(symbol)
                
        # 2. Verificar si hay errores
        if context and "error" in context:
            st.error(f"Error obteniendo datos: {context['error']}")
            return
            
        # 3. Extraer datos relevantes
        price = context.get("last_price", 0)
        signals = context.get("signals", {})
        options_params = context.get("options_params", {})
        vix_level = context.get("vix_level", 15.0)
        
        # 4. Filtros de opciones
        col1, col2, col3 = st.columns(3)
        
        with col1:
            strategy_filter = st.selectbox(
                "Estrategia",
                ["Direccional", "Income", "Volatilidad", "Hedging"]
            )
        
        with col2:
            expiry_filter = st.selectbox(
                "Vencimiento",
                ["Corto (1-2 semanas)", "Medio (3-6 semanas)", "Largo (2-3 meses)"]
            )
            
        with col3:
            risk_filter = st.select_slider(
                "Perfil de Riesgo",
                options=["Conservador", "Moderado", "Agresivo"],
                value="Moderado"
            )
        
        # 5. Mostrar recomendación principal
        render_options_recommendation(symbol, price, signals, options_params, vix_level)
        
        # 6. Mostrar análisis multi-timeframe para opciones
        st.markdown("---")
        st.subheader("⏱️ Análisis Multi-Timeframe para Opciones")
        
        # Contexto de análisis multi-timeframe si está disponible
        multi_tf = context.get("multi_timeframe", None)
        if multi_tf:
            render_multi_timeframe_analysis(symbol, multi_tf)
        else:
            st.info("Análisis multi-timeframe no disponible.")
        
        # 7. Estrategias adicionales según filtros
        st.markdown("---")
        st.subheader("🧩 Estrategias Avanzadas de Opciones")
        
        # Adaptar estrategias según filtros
        if strategy_filter == "Direccional":
            if signals and "options" in signals and signals["options"]["direction"] == "CALL":
                st.markdown("""
                ### Estrategias CALL Direccionales
                
                1. **Call Simple**
                   - Máxima exposición a dirección y volatilidad
                   - Mejor para movimientos rápidos y direccionales
                
                2. **Call Diagonal**
                   - Comprar CALL de vencimiento largo, vender CALL de vencimiento corto
                   - Menor costo, menor exposición a theta
                
                3. **Bull Call Spread**
                   - Comprar CALL ATM, vender CALL OTM
                   - Reduce costo y riesgo, pero limita ganancias
                """)
            else:
                st.markdown("""
                ### Estrategias PUT Direccionales
                
                1. **Put Simple**
                   - Máxima exposición a dirección y volatilidad
                   - Mejor para movimientos rápidos a la baja
                
                2. **Put Diagonal**
                   - Comprar PUT de vencimiento largo, vender PUT de vencimiento corto
                   - Menor costo, menor exposición a theta
                
                3. **Bear Put Spread**
                   - Comprar PUT ATM, vender PUT OTM
                   - Reduce costo y riesgo, pero limita ganancias
                """)
                
        elif strategy_filter == "Income":
            st.markdown("""
            ### Estrategias de Income
            
            1. **Iron Condor**
               - Vender Call y Put OTM, comprar Call y Put más alejados
               - Beneficio cuando el precio permanece en un rango
            
            2. **Credit Spread**
               - Bull Put Spread: Vender Put ATM, comprar Put OTM
               - Bear Call Spread: Vender Call ATM, comprar Call OTM
            
            3. **Butterfly**
               - Comprar Call ITM, vender 2 Calls ATM, comprar Call OTM
               - Beneficio máximo cuando el precio cierra exactamente en el strike medio
            """)
            
        elif strategy_filter == "Volatilidad":
            st.markdown("""
            ### Estrategias de Volatilidad
            
            1. **Straddle**
               - Comprar Call y Put en el mismo strike (generalmente ATM)
               - Beneficio con movimientos grandes en cualquier dirección
            
            2. **Strangle**
               - Comprar Call OTM y Put OTM
               - Menor costo que straddle, requiere movimiento mayor
            
            3. **Calendar Spread**
               - Vender opción de vencimiento cercano, comprar de vencimiento lejano
               - Beneficio con baja volatilidad a corto plazo, alta a largo plazo
            """)
            
        else:  # Hedging
            st.markdown("""
            ### Estrategias de Hedging
            
            1. **Protective Put**
               - Mantener acciones, comprar put OTM
               - Limita pérdidas en caso de caída, mantiene potencial alcista
            
            2. **Collar**
               - Mantener acciones, comprar put OTM, vender call OTM
               - Protección con costo reducido, pero limita ganancias
            
            3. **Hedge Ratio Dinámico**
               - Ajustar cantidad de opciones basado en delta y tamaño de posición
               - Protección parcial con menor costo
            """)
            
        # 8. Configurador de estrategia
        with st.expander("⚙️ Configurador de Estrategia"):
            st.markdown(f"### Configurar Estrategia para {symbol}")
            
            # Columnas para configuración
            config_col1, config_col2 = st.columns(2)
            
            with config_col1:
                # Parámetros de estrategia
                strategy_type = st.selectbox(
                    "Tipo de Estrategia",
                    ["Simple", "Vertical Spread", "Calendar", "Diagonal", "Iron Condor", "Butterfly"]
                )
                
                direction = st.radio(
                    "Dirección",
                    ["Alcista (CALL)", "Bajista (PUT)", "Neutral"]
                )
                
                capital = st.number_input(
                    "Capital a Invertir ($)",
                    min_value=100,
                    max_value=100000,
                    value=1000,
                    step=100
                )
                
            with config_col2:
                # Opciones específicas según estrategia
                if strategy_type in ["Simple", "Vertical Spread"]:
                    expiry_days = st.slider(
                        "Días a Expiración",
                        min_value=7,
                        max_value=90,
                        value=30,
                        step=1
                    )
                    
                    strike_pct = st.slider(
                        "Strike (% del precio actual)",
                        min_value=80,
                        max_value=120,
                        value=100 if direction == "Neutral" else (105 if "Alcista" in direction else 95),
                        step=1
                    )
                    
                    if strategy_type == "Vertical Spread":
                        width_pct = st.slider(
                            "Ancho del Spread (%)",
                            min_value=2,
                            max_value=20,
                            value=5,
                            step=1
                        )
                
                elif strategy_type in ["Calendar", "Diagonal"]:
                    short_expiry = st.slider(
                        "Expiración Corta (días)",
                        min_value=7,
                        max_value=45,
                        value=14,
                        step=1
                    )
                    
                    long_expiry = st.slider(
                        "Expiración Larga (días)",
                        min_value=short_expiry + 7,
                        max_value=120,
                        value=short_expiry + 30,
                        step=1
                    )
                    
                    if strategy_type == "Diagonal":
                        strike_diff = st.slider(
                            "Diferencia de Strikes (%)",
                            min_value=1,
                            max_value=15,
                            value=5,
                            step=1
                        )
                        
                elif strategy_type in ["Iron Condor", "Butterfly"]:
                    expiry_days = st.slider(
                        "Días a Expiración",
                        min_value=7,
                        max_value=90,
                        value=30,
                        step=1
                    )
                    
                    width_pct = st.slider(
                        "Ancho del Spread (%)",
                        min_value=2,
                        max_value=20,
                        value=5 if strategy_type == "Iron Condor" else 3,
                        step=1
                    )
                    
                    if strategy_type == "Iron Condor":
                        distance_pct = st.slider(
                            "Distancia del Centro (%)",
                            min_value=2,
                            max_value=20,
                            value=5,
                            step=1
                        )
            
            # Calcular parámetros aproximados de la estrategia
            st.markdown("### Configuración Generada")
            
            # Precio teórico de contrato
            contract_price = 0
            max_profit = 0
            max_loss = 0
            breakeven = 0
            
            # Cálculos aproximados según estrategia
            if strategy_type == "Simple":
                strike = price * (strike_pct / 100)
                # Estimación simple de precio de opción
                contract_price = price * 0.05 * (1 - abs(strike_pct - 100) / 100) * (expiry_days / 30)
                max_loss = contract_price * 100  # 1 contrato = 100 acciones
                max_profit = "Ilimitado" if "Alcista" in direction else "Ilimitado a la baja"
                breakeven = strike + contract_price if "Alcista" in direction else strike - contract_price
                
            elif strategy_type == "Vertical Spread":
                strike1 = price * (strike_pct / 100)
                strike2 = strike1 * (1 + width_pct/100) if "Alcista" in direction else strike1 * (1 - width_pct/100)
                
                # Estimación de precio de spread
                contract_price = price * 0.02 * (width_pct / 5) * (expiry_days / 30)
                max_loss = contract_price * 100
                max_profit = (abs(strike2 - strike1) - contract_price) * 100
                breakeven = strike1 + contract_price if "Alcista" in direction else strike1 - contract_price
            
            # Mostrar detalles
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Costo Estimado", f"${contract_price * 100:.2f}")
            
            with col2:
                st.metric("Contratos", f"{int(capital / (contract_price * 100))}")
            
            with col3:
                if isinstance(max_profit, str):
                    st.metric("Beneficio Máx", max_profit)
                else:
                    st.metric("Beneficio Máx", f"${max_profit:.2f}")
            
            with col4:
                st.metric("Breakeven", f"${breakeven:.2f}")
            
            # Disclaimer
            st.caption("""
            **Nota**: Estas son estimaciones simplificadas. Los precios reales de opciones 
            dependen de factores como volatilidad implícita, tiempo a expiración exacto, y 
            condiciones de mercado. Consulte su plataforma de trading para valores precisos.
            """)
            
    except Exception as e:
        logger.error(f"Error en tab opciones: {str(e)}\n{traceback.format_exc()}")
        st.error(f"Error procesando análisis de opciones: {str(e)}")

def render_multi_timeframe_tab(symbol, context=None):
    """
    Renderiza pestaña de análisis multi-timeframe.
    
    Args:
        symbol (str): Símbolo a analizar
        context (dict, optional): Contexto de mercado preexistente
    """
    try:
        # 1. Conseguir contexto de mercado si no fue proporcionado
        if context is None:
            with st.spinner("Analizando múltiples timeframes..."):
                context = get_market_context(symbol)
                
        # 2. Verificar si hay errores
        if context and "error" in context:
            st.error(f"Error obteniendo datos: {context['error']}")
            return
            
        # 3. Verificar si hay análisis multi-timeframe
        multi_tf = context.get("multi_timeframe", None)
        
        if multi_tf:
            # Ajustes para el análisis
            timeframes_to_show = st.multiselect(
                "Timeframes a Analizar",
                ["1d", "1wk", "1mo", "1h", "4h"],
                default=["1d", "1wk", "1mo"]
            )
            
            # Filtrar análisis según selección
            filtered_tf = {k: v for k, v in multi_tf.items() if k in timeframes_to_show or k == "consolidated"}
            
            # Mostrar análisis completo
            render_multi_timeframe_analysis(symbol, filtered_tf)
            
            # Mostrar gráfico comparativo
            st.markdown("## Comparativa Visual de Timeframes")
            
            # Obtener datos para cada timeframe y crear gráficos comparativos
            with st.spinner("Generando visualización comparativa..."):
                multi_chart = create_multi_timeframe_chart(symbol, timeframes_to_show)
                if multi_chart:
                    st.plotly_chart(multi_chart, use_container_width=True)
                else:
                    st.warning("No se pudo generar el gráfico comparativo.")
                    
            # Mostrar análisis de divergencias
            st.markdown("## Análisis de Divergencias")
            
            # Crear tabla de comparación específica
            if len(filtered_tf) > 1:
                metrics_to_compare = ["Tendencia", "RSI", "Volatilidad", "Volumen"]
                timeframes_data = {}
                
                # Extraer datos para cada timeframe
                for tf, signals in filtered_tf.items():
                    if tf != "consolidated" and isinstance(signals, dict):
                        timeframes_data[tf] = {
                            "Tendencia": signals["trend"]["sma_20_50"] if "trend" in signals else "N/A",
                            "RSI": signals["momentum"]["rsi"] if "momentum" in signals else 50,
                            "Volatilidad": signals["volatility"]["volatility_state"] if "volatility" in signals else "N/A",
                            "Volumen": signals["volume"]["trend"] if "volume" in signals else "N/A"
                        }
                
                # Detectar divergencias
if len(timeframes_data) > 1:
    st.markdown("### Divergencias Detectadas")
    
    # Comprobar divergencias entre TFs
    divergences = []
    
    # Divergencia de tendencia
    trend_values = [data["Tendencia"] for tf, data in timeframes_data.items()]
    if "alcista" in trend_values and "bajista" in trend_values:
        divergences.append({
            "type": "Tendencia",
            "description": "Divergencia en tendencia principal entre timeframes",
            "severity": "Alta",
            "recommendation": "Priorizar el timeframe mayor para decisiones a medio/largo plazo"
        })
        
    # Divergencia de RSI
    rsi_values = [data["RSI"] for tf, data in timeframes_data.items()]
    if any(rsi > 70 for rsi in rsi_values) and any(rsi < 30 for rsi in rsi_values):
        divergences.append({
            "type": "RSI",
            "description": "Sobrecompra en algunos timeframes, sobreventa en otros",
            "severity": "Alta",
            "recommendation": "Posible zona de reversión, considerar estrategias de volatilidad"
        })
        
    # Divergencia de volatilidad
    vol_values = [data["Volatilidad"] for tf, data in timeframes_data.items()]
    if "alta" in vol_values and "baja" in vol_values:
        divergences.append({
            "type": "Volatilidad",
            "description": "Volatilidad inconsistente entre timeframes",
            "severity": "Media",
            "recommendation": "Ajustar tamaño de posición y considerar opciones para timeframes específicos"
        })
        
    # Divergencia de volumen
    vol_trend_values = [data["Volumen"] for tf, data in timeframes_data.items()]
    if "alcista" in vol_trend_values and "bajista" in vol_trend_values:
        divergences.append({
            "type": "Volumen",
            "description": "Divergencia en volumen entre timeframes",
            "severity": "Media",
            "recommendation": "Verificar acumulación/distribución y posible manipulación"
        })
        
    # Mostrar divergencias encontradas
    if divergences:
        for div in divergences:
            color = "rgba(239, 83, 80, 0.2)" if div["severity"] == "Alta" else "rgba(255, 255, 255, 0.1)"
            st.markdown(f"""
            <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <strong>Divergencia: {div["type"]}</strong> - Severidad: {div["severity"]}
                <p>{div["description"]}</p>
                <p><em>Recomendación:</em> {div["recommendation"]}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No se detectaron divergencias significativas entre timeframes.")
        
    # Explicación sobre divergencias
    with st.expander("ℹ️ Sobre las Divergencias Multi-Timeframe"):
        st.markdown("""
        ### Importancia de las Divergencias Entre Timeframes
        
        Las divergencias entre diferentes timeframes pueden proporcionar información valiosa sobre:
        
        1. **Cambios de tendencia inminentes**: Cuando timeframes cortos muestran señales opuestas a los largos
        2. **Oportunidades de trading específicas**: Aprovechando desplazamientos temporales entre timeframes
        3. **Posible volatilidad futura**: Mayor divergencia suele preceder aumento de volatilidad
        
        ### Cómo Interpretar las Divergencias
        
        - **Divergencia Bajista**: TFs menores ya bajistas, mayores aún alcistas → Posible cambio a bajista
        - **Divergencia Alcista**: TFs menores ya alcistas, mayores aún bajistas → Posible cambio a alcista
        - **Divergencia de Momentum**: RSI divergente entre timeframes → Señal de agotamiento en tendencia
        
        ### Trading con Divergencias
        
        - **Estrategia Conservadora**: Esperar alineación de timeframes para máxima probabilidad
        - **Estrategia Agresiva**: Entrar en dirección del timeframe menor anticipando cambio en mayor
        - **Opciones**: Utilizar calendario o diagonales para explotar diferencias temporales
        """)

    # Tabla comparativa detallada
    st.markdown("### Matriz Comparativa Multi-Timeframe")
    
    # Crear DataFrame para la comparativa
    comparison_data = []
    for tf, data in timeframes_data.items():
        comparison_data.append({
            "Timeframe": tf,
            "Tendencia": data["Tendencia"],
            "RSI": data["RSI"],
            "Volatilidad": data["Volatilidad"],
            "Volumen": data["Volumen"]
        })
    
    # Convertir a DataFrame y mostrar con estilos
    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        
        # Función para colorear celdas según valor
        def style_cells(val):
            if isinstance(val, str):
                if val == "alcista":
                    return 'background-color: rgba(38, 166, 154, 0.2)'
                elif val == "bajista":
                    return 'background-color: rgba(239, 83, 80, 0.2)'
                elif val == "alta":
                    return 'background-color: rgba(239, 83, 80, 0.2)'
                elif val == "baja":
                    return 'background-color: rgba(38, 166, 154, 0.2)'
            return ''
        
        # Aplicar estilos y mostrar tabla
        styled_comparison = df_comparison.style.applymap(style_cells)
        st.dataframe(styled_comparison, use_container_width=True)
else:
    st.info("Se necesitan al menos dos timeframes para detectar divergencias.")

def render_fundamental_tab(symbol, context=None):
    """
    Renderiza pestaña de análisis fundamental.
    
    Args:
        symbol (str): Símbolo a analizar
        context (dict, optional): Contexto de mercado preexistente
    """
    try:
        # Mostrar mensaje informativo
        st.info("Los datos fundamentales se obtienen de fuentes externas y pueden tener un retraso de hasta 24 horas.")
        
        # Intentar obtener datos mediante yfinance (como ejemplo)
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
        except Exception as e:
            st.error(f"Error obteniendo datos fundamentales: {str(e)}")
            info = {}
        
        # Información básica de la empresa
        if info:
            # Header con info básica
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Información General")
                
                # Logo si está disponible
                if "logo_url" in info:
                    st.image(info["logo_url"], width=100)
                
                # Nombre y sector
                st.markdown(f"""
                ### {info.get('longName', symbol)}
                **Sector:** {info.get('sector', 'N/A')}  
                **Industria:** {info.get('industry', 'N/A')}  
                **País:** {info.get('country', 'N/A')}  
                **Página Web:** [{info.get('website', 'N/A')}]({info.get('website', '#')})
                """)
            
            with col2:
                st.subheader("Métricas Clave")
                
                # Crear 3 columnas para métricas
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    market_cap = info.get('marketCap', 0)
                    market_cap_str = f"${market_cap/1000000000:.2f}B" if market_cap >= 1e9 else \
                                    f"${market_cap/1000000:.2f}M" if market_cap >= 1e6 else \
                                    f"${market_cap:.2f}"
                    st.metric("Market Cap", market_cap_str)
                    
                    if 'trailingPE' in info:
                        st.metric("P/E Ratio", f"{info['trailingPE']:.2f}")
                    else:
                        st.metric("P/E Ratio", "N/A")
                
                with metric_col2:
                    if 'dividendYield' in info and info['dividendYield'] is not None:
                        div_yield = info['dividendYield'] * 100
                        st.metric("Dividend Yield", f"{div_yield:.2f}%")
                    else:
                        st.metric("Dividend Yield", "N/A")
                    
                    if 'beta' in info:
                        st.metric("Beta", f"{info['beta']:.2f}")
                    else:
                        st.metric("Beta", "N/A")
                
                with metric_col3:
                    if 'fiftyTwoWeekHigh' in info and 'fiftyTwoWeekLow' in info:
                        current = info.get('currentPrice', info.get('regularMarketPrice', 0))
                        high52 = info['fiftyTwoWeekHigh']
                        low52 = info['fiftyTwoWeekLow']
                        
                        # Calcular % desde máximo/mínimo
                        pct_from_high = ((current / high52) - 1) * 100
                        pct_from_low = ((current / low52) - 1) * 100
                        
                        st.metric("52w High", f"${high52:.2f}", f"{pct_from_high:.1f}%", delta_color="inverse")
                        st.metric("52w Low", f"${low52:.2f}", f"{pct_from_low:.1f}%", delta_color="normal")
                    else:
                        st.metric("52w Range", "N/A")
            
            # Separador
            st.markdown("---")
            
            # Tabs para diferentes aspectos fundamentales
            fund_tab1, fund_tab2, fund_tab3, fund_tab4 = st.tabs([
                "📊 Valoración", "💰 Financieros", "📈 Crecimiento", "🏢 Institucional"
            ])
            
            with fund_tab1:
                st.subheader("Métricas de Valoración")
                
                # Crear tabla de valoración
                valuation_metrics = [
                    {"Métrica": "P/E (TTM)", "Valor": info.get('trailingPE', "N/A")},
                    {"Métrica": "Forward P/E", "Valor": info.get('forwardPE', "N/A")},
                    {"Métrica": "PEG Ratio", "Valor": info.get('pegRatio', "N/A")},
                    {"Métrica": "P/S (TTM)", "Valor": info.get('priceToSalesTrailing12Months', "N/A")},
                    {"Métrica": "P/B", "Valor": info.get('priceToBook', "N/A")},
                    {"Métrica": "Enterprise Value/EBITDA", "Valor": info.get('enterpriseToEbitda', "N/A")},
                    {"Métrica": "Enterprise Value/Revenue", "Valor": info.get('enterpriseToRevenue', "N/A")}
                ]
                
                # Formatear datos numéricos
                for metric in valuation_metrics:
                    if isinstance(metric["Valor"], (int, float)):
                        metric["Valor"] = f"{metric['Valor']:.2f}"
                
                # Mostrar como tabla
                st.table(pd.DataFrame(valuation_metrics))
                
                # Análisis relativo al sector
                st.markdown("### Valoración Relativa al Sector")
                st.info("Esta sección requiere datos de sector que no están disponibles en esta demostración.")
            
            with fund_tab2:
                st.subheader("Datos Financieros")
                
                # Métricas financieras clave
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Rentabilidad")
                    profitability = [
                        {"Métrica": "Margen Bruto", "Valor": info.get('grossMargins', "N/A")},
                        {"Métrica": "Margen Operativo", "Valor": info.get('operatingMargins', "N/A")},
                        {"Métrica": "Margen Neto", "Valor": info.get('profitMargins', "N/A")},
                        {"Métrica": "ROE", "Valor": info.get('returnOnEquity', "N/A")},
                        {"Métrica": "ROA", "Valor": info.get('returnOnAssets', "N/A")}
                    ]
                    
                    # Formatear porcentajes
                    for metric in profitability:
                        if isinstance(metric["Valor"], (int, float)):
                            metric["Valor"] = f"{metric['Valor']*100:.2f}%"
                    
                    st.table(pd.DataFrame(profitability))
                
                with col2:
                    st.markdown("### Balance y Deuda")
                    balance = [
                        {"Métrica": "Efectivo Total", "Valor": info.get('totalCash', "N/A")},
                        {"Métrica": "Deuda Total", "Valor": info.get('totalDebt', "N/A")},
                        {"Métrica": "Ratio Deuda/Capital", "Valor": info.get('debtToEquity', "N/A")},
                        {"Métrica": "Current Ratio", "Valor": info.get('currentRatio', "N/A")},
                        {"Métrica": "Quick Ratio", "Valor": info.get('quickRatio', "N/A")}
                    ]
                    
                    # Formatear valores monetarios
                    for metric in balance:
                        if isinstance(metric["Valor"], (int, float)) and metric["Métrica"] in ["Efectivo Total", "Deuda Total"]:
                            value = metric["Valor"]
                            if value >= 1e9:
                                metric["Valor"] = f"${value/1e9:.2f}B"
                            elif value >= 1e6:
                                metric["Valor"] = f"${value/1e6:.2f}M"
                            else:
                                metric["Valor"] = f"${value:.2f}"
                        elif isinstance(metric["Valor"], (int, float)):
                            metric["Valor"] = f"{metric['Valor']:.2f}"
                    
                    st.table(pd.DataFrame(balance))
                
                # Ingresos y beneficios (últimos años)
                st.markdown("### Ingresos y Beneficios")
                st.info("Esta sección requiere datos históricos de ingresos que no están disponibles en esta demostración.")
            
            with fund_tab3:
                st.subheader("Métricas de Crecimiento")
                
                growth_metrics = [
                    {"Métrica": "Crecimiento de Ingresos (YoY)", "Valor": info.get('revenueGrowth', "N/A")},
                    {"Métrica": "Crecimiento de Beneficios (YoY)", "Valor": info.get('earningsGrowth', "N/A")},
                    {"Métrica": "Crecimiento de EPS (TTM)", "Valor": info.get('earningsQuarterlyGrowth', "N/A")},
                    {"Métrica": "Estimación de Crecimiento (5y)", "Valor": info.get('earningsGrowth', "N/A")}
                ]
                
                # Formatear porcentajes
                for metric in growth_metrics:
                    if isinstance(metric["Valor"], (int, float)):
                        metric["Valor"] = f"{metric['Valor']*100:.2f}%"
                
                st.table(pd.DataFrame(growth_metrics))
                
                # Expectativas de crecimiento
                st.markdown("### Expectativas Futuras")
                st.info("Esta sección requiere estimaciones de analistas que no están disponibles en esta demostración.")
            
            with fund_tab4:
                st.subheader("Propiedad Institucional")
                
                # Información institucional
                inst_data = [
                    {"Métrica": "% Institucional", "Valor": info.get('institutionsPercentHeld', "N/A")},
                    {"Métrica": "% Insider", "Valor": info.get('heldPercentInsiders', "N/A")},
                    {"Métrica": "Short Ratio", "Valor": info.get('shortRatio', "N/A")},
                    {"Métrica": "Short % of Float", "Valor": info.get('shortPercentOfFloat', "N/A")}
                ]
                
                # Formatear porcentajes
                for metric in inst_data:
                    if isinstance(metric["Valor"], (int, float)) and "%" in metric["Métrica"]:
                        metric["Valor"] = f"{metric['Valor']*100:.2f}%"
                    elif isinstance(metric["Valor"], (int, float)):
                        metric["Valor"] = f"{metric['Valor']:.2f}"
                
                st.table(pd.DataFrame(inst_data))
                
                # Principales accionistas
                st.markdown("### Principales Accionistas")
                st.info("Esta sección requiere datos de accionistas que no están disponibles en esta demostración.")
        else:
            st.warning(f"No se pudieron obtener datos fundamentales para {symbol}.")
            
    except Exception as e:
        logger.error(f"Error en tab fundamental: {str(e)}\n{traceback.format_exc()}")
        st.error(f"Error procesando análisis fundamental: {str(e)}")

def render_report_tab(symbol, context=None):
    """
    Renderiza pestaña de informe ejecutivo.
    
    Args:
        symbol (str): Símbolo a analizar
        context (dict, optional): Contexto de mercado preexistente
    """
    try:
        # 1. Conseguir contexto de mercado si no fue proporcionado
        if context is None:
            with st.spinner("Generando informe ejecutivo..."):
                context = get_market_context(symbol)
                
        # 2. Verificar si hay errores
        if context and "error" in context:
            st.error(f"Error obteniendo datos: {context['error']}")
            return
            
        # 3. Mostrar resumen ejecutivo
        st.subheader("📋 Informe Ejecutivo Institucional")
        
        # Datos clave
        price = context.get("last_price", 0)
        change = context.get("change", 0)
        change_pct = context.get("change_percent", 0)
        signals = context.get("signals", {})
        multi_tf = context.get("multi_timeframe", {})
        
        # Panel de resumen
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Encabezado con nombre y precio
            st.markdown(f"""
            # {symbol}
            ### ${price:.2f} {' 📈' if change > 0 else ' 📉' if change < 0 else ''}
            **Variación:** {change:.2f} ({change_pct:.2f}%) | **Actualizado:** {context.get('updated_at', 'N/A')}
            """)
        
        with col2:
            # Señal general
            if signals and "overall" in signals:
                signal = signals["overall"]["signal"]
                confidence = signals["overall"]["confidence"]
                
                # Color basado en señal
                signal_color = "rgba(38, 166, 154, 0.2)" if signal in ["compra", "compra_fuerte"] else \
                             "rgba(239, 83, 80, 0.2)" if signal in ["venta", "venta_fuerte"] else \
                             "rgba(255, 255, 255, 0.1)"
                
                st.markdown(f"""
                <div style="background-color:{signal_color}; 
                    padding: 15px; 
                    border-radius: 5px;
                    text-align: center;">
                    <h3 style="margin: 0;">
                        {signal.upper()} 
                        {'📈' if signal in ["compra", "compra_fuerte"] else '📉' if signal in ["venta", "venta_fuerte"] else '↔️'}
                    </h3>
                    <p style="margin: 5px 0;">
                        <span style="font-weight: bold;">Confianza:</span> {confidence.upper()}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Separador
        st.markdown("---")
        
        # Resumen técnico
        st.markdown("## 📊 Análisis Técnico")
        
        if signals:
            # Crear tabla resumen
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### Tendencia & Momentum")
                
                trend_sma = signals["trend"]["sma_20_50"]
                trend_macd = signals["trend"]["macd"]
                trend_sma200 = signals["trend"]["sma_200"]
                
                rsi = signals["momentum"]["rsi"]
                rsi_condition = signals["momentum"]["rsi_condition"]
                
                st.markdown(f"""
                - **Tendencia SMA:** {trend_sma} {' 📈' if trend_sma == 'alcista' else ' 📉'}
                - **MACD Signal:** {trend_macd} {' 📈' if trend_macd == 'alcista' else ' 📉'}
                - **Posición vs SMA200:** {trend_sma200}
                - **RSI (14):** {rsi:.1f} - {rsi_condition}
                """)
                
            with col2:
                st.markdown("### Volatilidad & Volumen")
                
                volatility = signals["volatility"]["volatility_state"]
                bb_width = signals["volatility"]["bb_width"]
                vol_trend = signals["volume"]["trend"]
                vol_ratio = signals["volume"]["ratio"]
                
                st.markdown(f"""
                - **Estado Volatilidad:** {volatility}
                - **BB Width:** {bb_width:.3f}
                - **Tendencia Volumen:** {vol_trend}
                - **Ratio Volumen:** {vol_ratio:.2f}x
                """)
                
            with col3:
                st.markdown("### Patrones & Alertas")
                
                # Mostrar patrones detectados
                patterns = context.get("candle_patterns", [])
                pattern_list = []
                
                for pattern in patterns[:3]:  # Limitar a 3 patrones
                    pattern_type = "📈" if "bullish" in pattern.get("type", "") else "📉" if "bearish" in pattern.get("type", "") else "🔄"
                    pattern_list.append(f"{pattern_type} {pattern.get('pattern', 'N/A')}")
                
                if not pattern_list:
                    pattern_list = ["No se detectaron patrones"]
                
                st.markdown("\n".join([f"- {p}" for p in pattern_list]))
        
        # Multi-timeframe
        st.markdown("## ⏱️ Análisis Multi-Timeframe")
        
        if multi_tf and "consolidated" in multi_tf:
            # Mostrar señal consolidada
            consolidated = multi_tf["consolidated"]
            signal = consolidated["signal"]
            confidence = consolidated["confidence"]
            alignment = consolidated["timeframe_alignment"]
            
            # Timeframes individuales
            timeframes_data = {}
            for tf, signals_tf in multi_tf.items():
                if tf != "consolidated" and signals_tf and "overall" in signals_tf:
                    timeframes_data[tf] = signals_tf["overall"]["signal"]
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Señal consolidada
                st.markdown(f"""
                ### Señal Multi-TF
                - **Dirección:** {signal.upper()} {' 📈' if 'compra' in signal else ' 📉' if 'venta' in signal else ' ↔️'}
                - **Confianza:** {confidence}
                - **Alineación:** {alignment}
                """)
                
            with col2:
                # Timeframes individuales
                st.markdown("### Por Timeframe")
                
                tf_markdown = ""
                for tf, signal_tf in timeframes_data.items():
                    icon = " 📈" if "compra" in signal_tf else " 📉" if "venta" in signal_tf else " ↔️"
                    tf_markdown += f"- **{tf}:** {signal_tf.upper()}{icon}\n"
                
                st.markdown(tf_markdown)
        
        # Recomendaciones de opciones
        st.markdown("## 🎯 Recomendación de Opciones")
        
        if signals and "options" in signals:
            options_signal = signals["options"]
            
            direction = options_signal["direction"]
            confidence = options_signal["confidence"]
            timeframe = options_signal["timeframe"]
            strategy = options_signal["strategy"]
            
            # Obtener ajustes por volatilidad
            vix_level = context.get("vix_level", 15.0)
            options_manager = OptionsParameterManager()
            vol_adjustments = options_manager.get_volatility_adjustments(vix_level)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Recomendación principal
                strike_est = price * (1.05 if direction == "CALL" else 0.95)
                expiry_rec = "2-4 semanas" if timeframe == "MEDIO" else "1-2 semanas" if timeframe == "CORTO" else "4-8 semanas"
                
                st.markdown(f"""
                ### Estrategia Recomendada
                - **Tipo:** {direction} {' 📈' if direction == 'CALL' else ' 📉'}
                - **Setup:** {strategy}
                - **Strike Estimado:** ${strike_est:.2f}
                - **Expiración Recomendada:** {expiry_rec}
                - **Confianza:** {confidence}
                """)
                
            with col2:
                # Ajustes por volatilidad
                st.markdown(f"""
                ### Ajustes de Volatilidad
                - **Nivel VIX:** {vix_level:.2f}
                - **Estado:** {vol_adjustments.get('category', 'normal').upper()}
                - **Recomendación:** {vol_adjustments.get('adjustments', ['N/A'])[0]}
                """)
        
        # Niveles de entrada/salida
        st.markdown("## 📏 Niveles Operativos")
        
        # Obtener niveles de soporte/resistencia
        levels = context.get("support_resistance", {})
        
        if levels:
            supports = levels.get("supports", [])
            resistances = levels.get("resistances", [])
            
            # Encontrar niveles más cercanos
            nearest_support = min(supports, key=lambda x: abs(x - price)) if supports else None
            nearest_resistance = min(resistances, key=lambda x: abs(x - price)) if resistances else None
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### Entradas")
                
                # Recomendación basada en tendencia general
                if signals and "overall" in signals:
                    signal = signals["overall"]["signal"]
                    
                    if "compra" in signal:
                        entry_price = nearest_support if nearest_support and nearest_support < price else price * 0.98
                        st.markdown(f"""
                        - **Nivel Agresivo:** ${price:.2f} (Actual)
                        - **Nivel Conservador:** ${entry_price:.2f}
                        - **Mejor Momento:** Pullback a soporte
                        """)
                    elif "venta" in signal:
                        entry_price = nearest_resistance if nearest_resistance and nearest_resistance > price else price * 1.02
                        st.markdown(f"""
                        - **Nivel Agresivo:** ${price:.2f} (Actual)
                        - **Nivel Conservador:** ${entry_price:.2f}
                        - **Mejor Momento:** Rechazo en resistencia
                        """)
                    else:
                        st.markdown("- **Sin señal clara de entrada**")
                else:
                    st.markdown("- **Datos insuficientes**")
                    
            with col2:
                st.markdown("### Stop Loss")
                
                # Recomendación de stop loss
                if signals and "overall" in signals:
                    signal = signals["overall"]["signal"]
                    
                    if "compra" in signal:
                        stop_level = min(supports) * 0.99 if supports else price * 0.95
                        st.markdown(f"""
                        - **Stop Técnico:** ${stop_level:.2f}
                        - **Stop % Precio:** ${price * 0.96:.2f} (-4%)
                        - **ATR Stop:** ${price * (1 - signals["volatility"].get("atr_pct", 2)/100):.2f}
                        """)
                    elif "venta" in signal:
                        stop_level = max(resistances) * 1.01 if resistances else price * 1.05
                        st.markdown(f"""
                        - **Stop Técnico:** ${stop_level:.2f}
                        - **Stop % Precio:** ${price * 1.04:.2f} (+4%)
                        - **ATR Stop:** ${price * (1 + signals["volatility"].get("atr_pct", 2)/100):.2f}
                        """)
                    else:
                        st.markdown("- **Sin nivel de stop recomendado**")
                else:
                    st.markdown("- **Datos insuficientes**")
                    
            with col3:
                st.markdown("### Objetivos")
                
                # Recomendación de objetivos
                if signals and "overall" in signals:
                    signal = signals["overall"]["signal"]
                    
                    if "compra" in signal:
                        target1 = nearest_resistance if nearest_resistance and nearest_resistance > price else price * 1.05
                        target2 = max(resistances) if resistances else price * 1.1
                        st.markdown(f"""
                        - **Target 1:** ${target1:.2f}
                        - **Target 2:** ${target2:.2f}
                        - **R/R Ratio:** {((target1 - price) / (price - (price * 0.96))):.2f}
                        """)
                    elif "venta" in signal:
                        target1 = nearest_support if nearest_support and nearest_support < price else price * 0.95
                        target2 = min(supports) if supports else price * 0.9
                        st.markdown(f"""
                        - **Target 1:** ${target1:.2f}
                        - **Target 2:** ${target2:.2f}
                        - **R/R Ratio:** {((price - target1) / ((price * 1.04) - price)):.2f}
                        """)
                    else:
                        st.markdown("- **Sin objetivos recomendados**")
                else:
                    st.markdown("- **Datos insuficientes**")
                    
        # Conclusión y gestión de riesgo
        st.markdown("## 🛡️ Gestión de Riesgo")
        
        if signals and "overall" in signals:
            signal = signals["overall"]["signal"]
            
            # Recomendaciones de gestión de riesgo
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Sizing & Money Management")
                
                # Adaptar según volatilidad y confianza
                if "alta" in signals["volatility"]["volatility_state"]:
                    position_size = "2-3% del capital"
                    sizing_note = "Reducir debido a alta volatilidad"
                else:
                    position_size = "3-5% del capital"
                    sizing_note = "Estándar para volatilidad normal"
                
                confidence = signals["overall"]["confidence"]
                if confidence == "alta":
                    confidence_adj = "Posición completa justificada"
                else:
                    confidence_adj = "Considerar entrada escalonada"
                
                st.markdown(f"""
                - **Tamaño Recomendado:** {position_size}
                - **Nota Volatilidad:** {sizing_note}
                - **Escalado:** {confidence_adj}
                - **Máx. Exposición Sector:** 20% del capital
                """)
                
            with col2:
                st.markdown("### Escenarios & Alertas")
                
                # Escenarios según la señal
                if "compra" in signal:
                    st.markdown("""
                    - **Alcista:** Ruptura de resistencia con volumen
                    - **Base:** Continuación de tendencia actual
                    - **Bajista:** Pérdida de soporte clave
                    - **Alerta Clave:** Divergencia RSI en máximos
                    """)
                elif "venta" in signal:
                    st.markdown("""
                    - **Bajista:** Ruptura de soporte con volumen
                    - **Base:** Continuación de tendencia actual
                    - **Alcista:** Rebote en soporte clave
                    - **Alerta Clave:** Divergencia RSI en mínimos
                    """)
                else:
                    st.markdown("""
                    - **Alcista:** Ruptura de rango con volumen
                    - **Base:** Consolidación en rango actual
                    - **Bajista:** Pérdida de soporte del rango
                    - **Alerta Clave:** Aumento de volatilidad
                    """)
        
        # Disclaimer
        st.markdown("---")
        st.caption("""
        **Disclaimer:** Este informe ejecutivo es generado automáticamente con fines informativos y no constituye
        asesoramiento financiero. Los niveles, recomendaciones y análisis presentados son estimaciones basadas
        en análisis técnico y deben ser validados con investigación adicional. Trading conlleva riesgo de pérdida.
        """)
                    
    except Exception as e:
        logger.error(f"Error en tab informe: {str(e)}\n{traceback.format_exc()}")
        st.error(f"Error generando informe ejecutivo: {str(e)}")

def render_risk_tab(symbol, context=None):
    """
    Renderiza pestaña de gestión de riesgo.
    
    Args:
        symbol (str): Símbolo a analizar
        context (dict, optional): Contexto de mercado preexistente
    """
    try:
        # 1. Conseguir contexto de mercado si no fue proporcionado
        if context is None:
            with st.spinner("Analizando perfil de riesgo..."):
                context = get_market_context(symbol)
                
        # 2. Verificar si hay errores
        if context and "error" in context:
            st.error(f"Error obteniendo datos: {context['error']}")
            return
            
        # 3. Mostrar resumen de riesgo
        st.subheader("⚠️ Análisis de Riesgo Profesional")
        
        # Datos clave
        price = context.get("last_price", 0)
        signals = context.get("signals", {})
        vix_level = context.get("vix_level", 15.0)
        
        # Panel de configuración
        col1, col2, col3 = st.columns(3)
        
        with col1:
            account_size = st.number_input(
                "Tamaño de Cuenta ($)",
                min_value=1000,
                max_value=10000000,
                value=100000,
                step=5000,
                help="Capital total disponible para trading"
            )
        
        with col2:
            risk_per_trade = st.slider(
                "Riesgo por Operación (%)",
                min_value=0.5,
                max_value=5.0,
                value=2.0,
                step=0.5,
                help="Porcentaje máximo del capital a arriesgar en una operación"
            )
        
        with col3:
            max_loss = st.slider(
                "Drawdown Máximo (%)",
                min_value=5.0,
                max_value=30.0,
                value=15.0,
                step=5.0,
                help="Pérdida máxima aceptable antes de reducir tamaño o pausar trading"
            )
        
        # 4. Análisis de riesgo basado en volatilidad
        st.markdown("## 📊 Métricas de Riesgo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            volatility = "ALTA" if vix_level > 25 else "BAJA" if vix_level < 15 else "NORMAL"
            vol_color = "inverse" if volatility == "ALTA" else "normal" if volatility == "BAJA" else "off"
            
            st.metric("Volatilidad de Mercado", volatility, f"VIX: {vix_level:.2f}", delta_color=vol_color)
            
        with col2:
            if signals and "volatility" in signals:
                atr_pct = signals["volatility"].get("atr_pct", 0)
                if atr_pct == 0 and "volatility" in signals:
                    atr = signals["volatility"].get("atr", 0)
                    if atr > 0 and price > 0:
                        atr_pct = (atr / price) * 100
                        
                st.metric("ATR (%)", f"{atr_pct:.2f}%", help="Average True Range como % del precio")
            else:
                st.metric("ATR (%)", "N/A")
            
        with col3:
            # Calcular riesgo por volatilidad
            if signals and "volatility" in signals:
                vol_risk = (atr_pct / 100) * account_size * (risk_per_trade / 100) / (atr_pct / 100)
                st.metric("Riesgo por Volatilidad", f"${vol_risk:.2f}", help="Riesgo ajustado por volatilidad")
            else:
                st.metric("Riesgo por Volatilidad", "N/A")
            
        with col4:
            # Calcular riesgo monetario
            risk_amount = account_size * (risk_per_trade / 100)
            st.metric("Riesgo Monetario", f"${risk_amount:.2f}", help="Cantidad monetaria a riesgo por operación")
        
        # 5. Calculadora de posición
        st.markdown("## 📐 Calculadora de Posición")
        
        # Configuración de entrada/salida
        col1, col2 = st.columns(2)
        
        with col1:
            # Definir entrada/stop basado en señales
            default_stop = 0
            
            if signals and "overall" in signals:
                signal = signals["overall"]["signal"]
                if "compra" in signal:
                    default_stop = price * 0.96  # 4% debajo para compras
                elif "venta" in signal:
                    default_stop = price * 1.04  # 4% arriba para ventas
                else:
                    default_stop = price * 0.95  # Default conservador
            else:
                default_stop = price * 0.95
                
            entry_price = st.number_input(
                "Precio de Entrada",
                min_value=0.01,
                max_value=float(price * 10),
                value=float(price),
                step=0.01
            )
            
            stop_price = st.number_input(
                "Precio de Stop Loss",
                min_value=0.01,
                max_value=float(price * 10),
                value=float(default_stop),
                step=0.01
            )
            
        with col2:
            # Objetivos basados en R:R
            if entry_price > stop_price:  # Long position
                target1_default = entry_price + (entry_price - stop_price) * 1.5  # R:R 1.5
                target2_default = entry_price + (entry_price - stop_price) * 2.5  # R:R 2.5
            else:  # Short position
                target1_default = entry_price - (stop_price - entry_price) * 1.5
                target2_default = entry_price - (stop_price - entry_price) * 2.5
                
            target_price1 = st.number_input(
                "Precio Objetivo 1",
                min_value=0.01,
                max_value=float(price * 10),
                value=float(target1_default),
                step=0.01
            )
            
            target_price2 = st.number_input(
                "Precio Objetivo 2",
                min_value=0.01,
                max_value=float(price * 10),
                value=float(target2_default),
                step=0.01
            )
            
        # Calcular tamaño de posición y métricas de riesgo
        col1, col2, col3 = st.columns(3)
        
        # Calcular riesgo por acción
        risk_per_share = abs(entry_price - stop_price)
        
        # Calcular tamaño de posición
        if risk_per_share > 0:
            position_size = risk_amount / risk_per_share
            position_value = position_size * entry_price
            
            # Calcular R:R
            if entry_price > stop_price:  # Long
                rr_ratio1 = (target_price1 - entry_price) / (entry_price - stop_price)
                rr_ratio2 = (target_price2 - entry_price) / (entry_price - stop_price)
            else:  # Short
                rr_ratio1 = (entry_price - target_price1) / (stop_price - entry_price)
                rr_ratio2 = (entry_price - target_price2) / (stop_price - entry_price)
        else:
            position_size = 0
            position_value = 0
            rr_ratio1 = 0
            rr_ratio2 = 0
            
        with col1:
            st.metric("Tamaño de Posición", f"{int(position_size)} acciones")
            st.metric("Valor de Posición", f"${position_value:.2f}")
            
        with col2:
            st.metric("Riesgo por Acción", f"${risk_per_share:.2f}")
            st.metric("% de la Cuenta", f"{(position_value/account_size)*100:.2f}%")
            
        with col3:
            st.metric("R/R Ratio (Obj. 1)", f"{rr_ratio1:.2f}")
            st.metric("R/R Ratio (Obj. 2)", f"{rr_ratio2:.2f}")
            
        # 6. Simulador de escenarios
        st.markdown("## 🎮 Simulador de Escenarios")
        
        # Probabilidades de escenarios
        col1, col2, col3 = st.columns(3)
        
        with col1:
            win_rate = st.slider(
                "Win Rate (%)",
                min_value=30,
                max_value=70,
                value=50,
                step=5,
                help="Porcentaje estimado de operaciones ganadoras"
            )
            
        with col2:
            partial_win = st.slider(
                "% Salidas Parciales",
                min_value=0,
                max_value=100,
                value=30,
                step=10,
                help="Porcentaje de operaciones con salida parcial en Objetivo 1"
            )
            
        with col3:
            consecutive_losses = st.slider(
                "Máx. Pérdidas Consecutivas",
                min_value=2,
                max_value=10,
                value=5,
                step=1,
                help="Número estimado de pérdidas consecutivas (worst case)"
            )
            
        # Resultados de escenarios
        st.markdown("### Resultados de Simulación")
        
        # Calcular expectativa matemática
        win_amount1 = (target_price1 - entry_price) * position_size if entry_price < target_price1 else (entry_price - target_price1) * position_size
        win_amount2 = (target_price2 - entry_price) * position_size if entry_price < target_price2 else (entry_price - target_price2) * position_size
        loss_amount = risk_amount
        
        # Ajustar por salidas parciales
        avg_win = (win_amount1 * (partial_win/100)) + (win_amount2 * (1 - partial_win/100))
        
        # Expectativa por trade
        expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * loss_amount)
        
        # Equity después de drawdown estimado
        max_drawdown = loss_amount * consecutive_losses
        equity_after_dd = account_size - max_drawdown
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Expectativa por Trade", f"${expectancy:.2f}", 
                     f"{'+' if expectancy > 0 else ''}{(expectancy/risk_amount)*100:.1f}% del riesgo")
            
        with col2:
            st.metric("Drawdown Máximo Estimado", f"${max_drawdown:.2f}", 
                     f"{(max_drawdown/account_size)*100:.1f}% del capital")
            
        with col3:
            st.metric("Equity Después de Drawdown", f"${equity_after_dd:.2f}", 
                     f"{((equity_after_dd/account_size)-1)*100:.1f}%")
            
        # 7. Recomendaciones de gestión de riesgo
        with st.expander("📋 Recomendaciones de Gestión de Riesgo", expanded=True):
            # Adaptar recomendaciones según análisis
            
            # Tamaño de posición recomendado basado en volatilidad
            if vix_level > 25:
                position_rec = "Reducir tamaño de posición en 30-50% del estándar"
                strategy_rec = "Considerar estrategias con stop más amplio y tamaño reducido"
            elif vix_level < 15:
                position_rec = "Tamaño estándar aceptable (1-2% de riesgo por operación)"
                strategy_rec = "Ideal para estrategias direccionales con opciones"
            else:
                position_rec = "Tamaño estándar (1-2% de riesgo por operación)"
                strategy_rec = "Balance entre directional y non-directional"
                
            # Recomendaciones basadas en R:R
            if rr_ratio1 < 1:
                rr_rec = "Relación riesgo/recompensa deficiente. Reconsiderar la operación o ajustar niveles."
            elif rr_ratio1 < 1.5:
                rr_rec = "R:R aceptable pero no óptimo. Requiere win rate superior al 60%."
            else:
                rr_rec = "Buena relación riesgo/recompensa. Adecuado para estrategia a largo plazo."
                
            # Mostrar recomendaciones
            st.markdown(f"""
            ### Recomendaciones Personalizadas
            
            #### Tamaño y Exposición
            - {position_rec}
            - Máximo drawdown permitido: {max_loss:.1f}% (${account_size * max_loss/100:.2f})
            - No superar 20-25% de exposición total en activos correlacionados
            
            #### Estrategia y Expectativa
            - {strategy_rec}
            - {rr_rec}
            - Con {win_rate}% win rate, expectativa: ${expectancy:.2f} por operación
            
            #### Plan de Contingencia
            - Reducir tamaño 50% tras {consecutive_losses-2} pérdidas consecutivas
            - Pausa de trading tras {consecutive_losses} pérdidas consecutivas
            - Obligatorio revisión de estrategia al alcanzar {max_loss/2:.1f}% de drawdown
            """)
            
    except Exception as e:
        logger.error(f"Error en tab gestión de riesgo: {str(e)}\n{traceback.format_exc()}")
        st.error(f"Error procesando análisis de riesgo: {str(e)}")

def render_dashboard(symbol, timeframe):
    """Renderiza el dashboard principal de trading institucional"""
    try:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Análisis Técnico",
            "🎯 Opciones",
            "📊 Multi-Timeframe",
            "🔍 Fundamental",
            "📋 Reporte",
            "⚠️ Risk Management"
        ])

        # Obtener contexto completo una vez para todas las pestañas
        with st.spinner(f"Analizando {symbol}..."):
            context = get_market_context(symbol)
        
        # Si hay error en el contexto, mostrar mensaje
        if context and "error" in context:
            st.error(f"Error obteniendo datos de mercado para {symbol}: {context['error']}")
            return

        with tab1:
            render_technical_tab(symbol, timeframe, context)

        with tab2:
            render_options_tab(symbol, context)

        with tab3:
            render_multi_timeframe_tab(symbol, context)

        with tab4:
            render_fundamental_tab(symbol, context)

        with tab5:
            render_report_tab(symbol, context)

        with tab6:
            render_risk_tab(symbol, context)

    except Exception as e:
        logger.error(f"Error renderizando dashboard: {str(e)}\n{traceback.format_exc()}")
        st.error("Error al cargar el dashboard institucional")
        st.info("Detalles técnicos: verifique los logs para más información")