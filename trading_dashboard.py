import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from market_utils import (
    fetch_market_data,
    TechnicalAnalyzer,
    get_market_context,
    logger
)

# Timeframes institucionales
TIMEFRAMES = {
    "Intradía": ["1m", "5m", "15m", "30m", "1h"],
    "Swing": ["1d", "1wk"],
    "Posicional": ["1mo", "3mo"]
}

def create_advanced_chart(data, timeframe="diario"):
    """Crea gráfico técnico avanzado con análisis institucional"""
    try:
        if data is None:
            return None

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

        # Panel Principal: OHLC y Bandas de Bollinger
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="OHLC",
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )

        # Bollinger Bands con área sombreada
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

        # Medias Móviles Avanzadas
        for ma, color, width in [
            ('SMA_20', '#2196f3', 1.5),  # Azul
            ('SMA_50', '#ff9800', 1.5),  # Naranja
            ('SMA_200', '#f44336', 1.5)  # Rojo
        ]:
            if ma in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[ma],
                        name=f"{ma}",
                        line=dict(color=color, width=width)
                    ),
                    row=1, col=1
                )

        # Panel MACD con histograma dinámico
        if all(x in data.columns for x in ['MACD', 'MACD_Signal', 'MACD_Hist']):
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['MACD'],
                    name='MACD',
                    line=dict(color='#2196f3', width=1.5)
                ),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['MACD_Signal'],
                    name='Signal',
                    line=dict(color='#ff9800', width=1.5)
                ),
                row=2, col=1
            )

            colors = np.where(data['MACD_Hist'] >= 0, '#26a69a', '#ef5350')
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

        # Panel RSI y Estocástico
        if 'RSI' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['RSI'],
                    name='RSI',
                    line=dict(color='#9c27b0', width=1.5)
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

        # Estocástico si está disponible
        if all(x in data.columns for x in ['Stoch_K', 'Stoch_D']):
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['Stoch_K'],
                    name='%K',
                    line=dict(color='#2196f3', width=1)
                ),
                row=3, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['Stoch_D'],
                    name='%D',
                    line=dict(color='#ff9800', width=1)
                ),
                row=3, col=1
            )

        # Panel de Volumen con análisis OBV
        if 'Volume' in data.columns:
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

            if 'OBV' in data.columns:
                # Normalizar OBV para visualización
                normalized_obv = data['OBV']/data['OBV'].max()*data['Volume'].max()
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=normalized_obv,
                        name='OBV Norm',
                        line=dict(color='#2196f3', width=1.5)
                    ),
                    row=4, col=1
                )

        # Layout profesional
        fig.update_layout(
            height=900,
            template='plotly_dark',
            showlegend=True,
            xaxis_rangeslider_visible=False,
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        # Grids y ejes
        for i in range(1, 5):
            fig.update_xaxes(
                gridcolor='rgba(128,128,128,0.2)',
                zerolinecolor='rgba(128,128,128,0.5)',
                row=i,
                col=1
            )
            fig.update_yaxes(
                gridcolor='rgba(128,128,128,0.2)',
                zerolinecolor='rgba(128,128,128,0.5)',
                row=i,
                col=1
            )

        return fig

    except Exception as e:
        logger.error(f"Error en visualización avanzada: {str(e)}")
        return None

def render_technical_metrics(df_technical):
    """Renderiza métricas técnicas avanzadas e institucionales"""
    try:
        # Métricas principales
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
            rsi_value = df_technical['RSI'].iloc[-1]
            rsi_status = (
                "Sobrecomprado" if rsi_value > 70
                else "Sobrevendido" if rsi_value < 30
                else "Neutral"
            )
            st.metric(
                "RSI",
                f"{rsi_value:.1f}",
                rsi_status
            )

        with col3:
            vol_ratio = df_technical['Volume'].iloc[-1] / df_technical['Volume'].mean()
            st.metric(
                "Vol Ratio",
                f"{vol_ratio:.2f}x",
                f"{(vol_ratio-1)*100:.1f}% vs Media"
            )

        with col4:
            bb_width = df_technical['BB_Width'].iloc[-1]
            bb_avg = df_technical['BB_Width'].mean()
            st.metric(
                "BB Width",
                f"{bb_width:.3f}",
                f"{(bb_width/bb_avg-1)*100:.1f}% vs Media"
            )

        # Análisis institucional
        with st.expander("🔍 Análisis Institucional", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### Tendencia & Momentum")
                st.markdown(f"""
                - **Tendencia MA:** {'Alcista' if df_technical['SMA_20'].iloc[-1] > df_technical['SMA_50'].iloc[-1] else 'Bajista'}
                - **MACD Signal:** {'Alcista' if df_technical['MACD'].iloc[-1] > df_technical['MACD_Signal'].iloc[-1] else 'Bajista'}
                - **RSI:** {df_technical['RSI'].iloc[-1]:.1f}
                - **Estocástico %K:** {df_technical.get('Stoch_K', pd.Series([0])).iloc[-1]:.1f}
                """)

            with col2:
                st.markdown("### Volatilidad & Risk")
                hist_vol = df_technical['Close'].pct_change().std() * np.sqrt(252) * 100
                st.markdown(f"""
                - **Vol Histórica:** {hist_vol:.1f}%
                - **BB Width:** {bb_width:.3f}
                - **ATR Ratio:** {df_technical['ATR'].iloc[-1]/df_technical['ATR'].mean():.2f}
                - **Vol Percentil:** {(df_technical['BB_Width'] <= bb_width).mean()*100:.0f}%
                """)

            with col3:
                st.markdown("### Volumen & Flujo")
                st.markdown(f"""
                - **Vol/Avg:** {vol_ratio:.2f}x
                - **VWAP Pos:** {'Por encima' if df_technical['Close'].iloc[-1] > df_technical['VWAP'].iloc[-1] else 'Por debajo'}
                - **OBV Trend:** {'Alcista' if df_technical['OBV'].iloc[-1] > df_technical['OBV'].iloc[-2] else 'Bajista'}
                - **Vol Spread:** {(df_technical['High'].iloc[-1] - df_technical['Low'].iloc[-1])/df_technical['Close'].iloc[-1]*100:.2f}%
                """)

    except Exception as e:
        logger.error(f"Error en métricas técnicas: {str(e)}")
        st.error("Error calculando métricas")

def render_technical_tab(symbol, timeframe, data):
    """Renderiza pestaña de análisis técnico avanzado"""
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        timeframe = st.selectbox(
            "Timeframe",
            [tf for group in TIMEFRAMES.values() for tf in group],
            index=4
        )
    with col2:
        chart_type = st.selectbox(
            "Tipo de Gráfico",
            ["Candlestick", "Renko", "Heiken Ashi", "Line"]
        )
    with col3:
        indicator_sets = st.multiselect(
            "Indicadores",
            ["Tendencia", "Momentum", "Volatilidad", "Volumen"],
            default=["Tendencia"]
        )

    if data is not None:
        analyzer = TechnicalAnalyzer(data)
        df_technical = analyzer.calculate_indicators()
        if df_technical is not None:
            fig = create_advanced_chart(df_technical, timeframe)
            st.plotly_chart(fig, use_container_width=True)
            render_technical_metrics(df_technical)

def render_options_tab():
    """Análisis avanzado de opciones y volatilidad institucional"""
    col1, col2 = st.columns([1, 2])
    with col1:
        expiry_range = st.selectbox(
            "Vencimientos",
            ["Cercanos (1m)", "Medianos (1-3m)", "Lejanos (3m+)"]
        )
        strategy_type = st.selectbox(
            "Estrategia",
            ["Direccional", "Volatilidad", "Income", "Hedging"]
        )

    with col2:
        st.markdown(f"""
        ### Análisis de Volatilidad
        - **IV Rank:** 65% (Percentil histórico)
        - **IV vs HV:** +2.5 pts (IV Premium)
        - **Term Structure:** Contango (Normal)
        - **Put/Call Skew:** 1.2 (Moderado)
        """)

    # Matriz de opciones
    st.subheader("Matriz de Opciones & Greeks")
    expiry_dates = ["2024-03-15", "2024-04-19", "2024-06-21"]
    strikes = ["ATM-2", "ATM-1", "ATM", "ATM+1", "ATM+2"]

    tab1, tab2, tab3 = st.tabs(["Análisis de Volatilidad", "Greeks", "Risk Analysis"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            ### Surface Analysis
            - **ATM Vol:** 25.5%
            - **25Δ Call:** +2.1%
            - **25Δ Put:** +2.8%
            - **Vol Cone:** 65%
            """)

        with col2:
            st.markdown("""
            ### Term Structure
            - **Front Month:** 24.5%
            - **Mid-Term:** 26.2%
            - **Back Month:** 27.8%
            - **Contango Factor:** 1.12
            """)

        st.markdown("### Volatility Surface Heatmap")
        # Aquí iría el heatmap de volatilidad

    with tab2:
        st.markdown("### Greek Exposure")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            #### Delta Analysis
            - **Net Delta:** +0.35
            - **Dollar Delta:** $125,000
            - **Gamma Scalping:** Favorable
            - **Delta Decay:** -0.02/día
            """)

        with col2:
            st.markdown("""
            #### Gamma Profile
            - **Net Gamma:** +0.08
            - **Gamma Max:** 115.50
            - **Flip Point:** 112.25
            - **Risk Reversal:** +25Δ
            """)

        with col3:
            st.markdown("""
            #### Theta/Vega
            - **Net Theta:** -250
            - **Theta/Vega Ratio:** 0.85
            - **Vega Notional:** $50,000
            - **Vega Risk:** Moderado
            """)

    with tab3:
        st.markdown("### Risk Metrics")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            #### Position Risk
            - **VaR (95%):** -$15,000
            - **Expected Shortfall:** -$22,500
            - **Max Drawdown:** -$35,000
            - **Stress Test:** -8.5%
            """)

        with col2:
            st.markdown("""
            #### Risk Ratios
            - **Sharpe Ratio:** 1.85
            - **Sortino Ratio:** 2.25
            - **Win Rate:** 65%
            - **Profit Factor:** 1.75
            """)

    # Estrategias sugeridas
    with st.expander("🎯 Estrategias Institucionales"):
        st.markdown("""
        ### Volatility Strategies

        #### Iron Condor Setup
        - **Strikes:** 25Δ Calls/Puts
        - **Width:** 10 puntos
        - **Risk/Reward:** 1:1.5
        - **Prob. of Profit:** 75%
        - **Greeks:**
          - Delta: 0.02
          - Gamma: -0.001
          - Theta: +25
          - Vega: -100

        #### Calendar Spread
        - **Strike:** ATM
        - **Ratio:** 1:1
        - **Front Month:** April 2024
        - **Back Month:** June 2024
        - **Greeks:**
          - Delta: Neutral
          - Gamma: +0.02
          - Theta: +15
          - Vega: +150

        #### Risk Management
        - Stop Loss: 2x Theta
        - Position Sizing: 2% del capital
        - Delta Hedge: Dynamic 25%
        - Vega Limit: $100 per point
        """)

def render_multiframe_tab(symbol):
    """Análisis multi-timeframe institucional"""
    timeframes = ["1d", "1wk", "1mo"]
    analysis_multi = {}

    for tf in timeframes:
        data = fetch_market_data(symbol, "1y", tf)
        if data is not None:
            analyzer = TechnicalAnalyzer(data)
            df = analyzer.calculate_indicators()
            if df is not None:
                analysis_multi[tf] = analyzer.get_current_signals()

    if analysis_multi:
        # Vista consolidada
        st.markdown("### Análisis Multi-Timeframe")

        # Crear tabla de análisis
        analysis_table = pd.DataFrame()

        for tf in timeframes:
            if tf in analysis_multi:
                signals = analysis_multi[tf]
                analysis_table.loc[tf, "Tendencia"] = signals["trend"]["sma_20_50"]
                analysis_table.loc[tf, "RSI"] = f"{signals['momentum']['rsi']:.1f}"
                analysis_table.loc[tf, "Volatilidad"] = signals["volatility"]["volatility_state"]
                analysis_table.loc[tf, "Volumen"] = signals["volume"]["trend"]
                analysis_table.loc[tf, "Señal"] = signals["overall"]["signal"]

        # Mostrar tabla estilizada
        st.dataframe(
            analysis_table.style.apply(lambda x: ['background-color: rgba(38,166,154,0.2)'
                                               if v == "alcista" or v == "compra_fuerte"
                                               else 'background-color: rgba(239,83,80,0.2)'
                                               if v == "bajista" or v == "venta_fuerte"
                                               else '' for v in x], axis=1),
            height=200
        )

        # Análisis de correlaciones
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Convergencia/Divergencia")
            # Aquí iría un gráfico de convergencia/divergencia

        with col2:
            st.markdown("### Correlación Temporal")
            # Aquí iría un gráfico de correlación temporal

def render_fundamental_tab():
    """Análisis fundamental y cuantitativo"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Métricas de Valoración")
        metrics = {
            "P/E Ratio": "25.4",
            "P/B Ratio": "3.2",
            "EV/EBITDA": "15.6",
            "ROE": "18.5%",
            "Margen Op.": "22.4%"
        }

        for metric, value in metrics.items():
            st.metric(metric, value)

    with col2:
        st.markdown("### Análisis Sectorial")
        st.markdown("""
        - **Posición Competitiva:** Líder (Top 3)
        - **Market Share:** 23.5% (+2.5% YoY)
        - **Crecimiento:** +15.2% vs +8.5% Sector
        - **Margen vs Industria:** +250bps
        """)

    # Factor Analysis
    with st.expander("📊 Análisis de Factores"):
        st.markdown("""
        ### Factor Exposures
        - **Value:** +0.85
        - **Momentum:** +1.25
        - **Quality:** +0.95
        - **Size:** -0.15
        - **Low Vol:** +0.45
        """)

def render_report_tab():
    """Reporte ejecutivo institucional"""
    st.markdown("### Análisis Ejecutivo")

    st.markdown("""
    #### 📈 Análisis Técnico
    - **Tendencia:** Alcista moderada (85% confianza)
    - **Momentum:** Positivo (RSI: 58)
    - **Volatilidad:** Baja (ATR p25)
    - **Volumen:** +15% vs Media 20D

    #### 🎯 Niveles Clave
    - **R2:** $162.25 (Fibonacci 161.8%)
    - **R1:** $158.50 (Máximo previo)
    - **Pivot:** $155.75 (VWAP semanal)
    - **S1:** $152.30 (SMA 50)
    - **S2:** $150.75 (Soporte estructural)
    """)

    with st.expander("🎯 Plan de Trading"):
        st.markdown("""
        ### Estrategia Institucional
        1. **Entrada:**
           - Base: Pullback a SMA 20
           - Alternativa: Breakout $158.50
           - Confirmación: RSI > 40 + Volumen > 1.5x

        2. **Gestión:**
           - Stop inicial: -2.5% ($151.85)
           - Breakeven: +2% ($158.85)
           - Trailing: 2x ATR

        3. **Objetivos:**
           - TP1: +4% (R:R 1.6)
           - TP2: +6.25% (R:R 2.5)

        4. **Sizing:**
           - Posición: 5% capital
           - Beta-adjusted: 0.85
           - Delta-equiv: 0.65
        """)

def render_risk_tab():
    """Análisis de riesgo institucional"""
    st.markdown("### Risk Management Dashboard")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### 📊 Risk Metrics
        - **Beta:** 1.15
        - **Sigma:** 22.5% anual
        - **Max DD:** -15.4%
        - **Sharpe:** 1.8
        """)

    with col2:
        st.markdown("""
        #### ⚠️ Position Risk
        - **Size:** 5% AUM
        - **Stop:** 2.5%
        - **Beta-Adj:** 0.75
        - **VaR 95%:** -1.8%
        """)

    # Escenarios y stress testing
    st.markdown("### Análisis de Escenarios")
    scenarios = {
        "Alcista": "+12.5% (prob: 35%)",
        "Base": "+6.25% (prob: 45%)",
        "Bajista": "-4.5% (prob: 20%)"
    }

    for scenario, projection in scenarios.items():
        st.metric(scenario, projection)

    with st.expander("📊 Risk Analysis"):
        st.markdown("""
        #### Factor Exposures
        - **Market:** +0.85β
        - **Size:** -0.15
        - **Value:** +0.45
        - **Momentum:** +0.75
        - **Volatility:** -0.25

        #### Risk Decomposition
        - **Systematic:** 65%
        - **Idiosyncratic:** 25%
        - **Factor:** 10%

        #### Stress Tests
        - **2008 Crisis:** -28.5%
        - **Covid Crash:** -15.2%
        - **Taper Tantrum:** -8.5%
        - **Rate Hike:** -5.2%
        """)

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

        # Cargar datos una sola vez
        data = fetch_market_data(symbol, "1y", timeframe)

        with tab1:
            render_technical_tab(symbol, timeframe, data)

        with tab2:
            render_options_tab()

        with tab3:
            render_multiframe_tab(symbol)

        with tab4:
            render_fundamental_tab()

        with tab5:
            render_report_tab()

        with tab6:
            render_risk_tab()

    except Exception as e:
        logger.error(f"Error renderizando dashboard: {str(e)}")
        st.error("Error al cargar el dashboard institucional")
