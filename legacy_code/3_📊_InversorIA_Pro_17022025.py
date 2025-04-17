import os
import time
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import openai
import logging
import pandas as pd
import numpy as np
import json

# Verificación de autenticación
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.title("🔒 Acceso Restringido")
    st.warning("Por favor, inicie sesión desde la página principal del sistema.")
    st.stop()

# Importar utilidades personalizadas
from market_utils import (
    fetch_market_data,
    TechnicalAnalyzer,
    get_market_context,
    logger
)
from openai_utils import process_tool_calls, tools

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Configuración de la página
st.set_page_config(
    page_title="InversorIA Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.alexanderoviedofadul.dev/',
        'Report a bug': None,
        'About': "InversorIA Pro: Plataforma avanzada de trading con IA"
    }
)

# Símbolos por categoría
SYMBOLS = {
    "Índices": ["SPY", "QQQ", "DIA", "IWM", "EFA", "VWO", "IYR", "XLE", "XLF", "XLV"],
    "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "PYPL", "CRM"],
    "Finanzas": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK"],
    "Salud": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "AMGN", "BMY", "GILD", "TMO"],
    "Energía": ["XOM", "CVX", "SHEL", "TTE", "COP", "EOG", "PXD", "DVN", "MPC", "PSX"],
    "Consumo": ["MCD", "SBUX", "NKE", "TGT", "HD", "LOW", "TJX", "ROST", "CMG", "DHI"],
    "Materias Primas": ["GLD", "SLV", "USO", "UNG", "CORN", "SOYB", "WEAT"],
    "Cripto ETFs": ["BITO", "GBTC", "ETHE", "ARKW", "BLOK"],
    "Bonos": ["AGG", "BND", "IEF", "TLT", "LQD", "HYG", "JNK", "TIP", "MUB", "SHY"],
    "Inmobiliario": ["VNQ", "XLRE", "IYR", "REIT", "HST", "EQR", "AVB", "PLD", "SPG", "AMT"],
    "Volatilidad": ["VXX", "UVXY", "SVXY", "VIXY"]
}

# Timeframes disponibles
TIMEFRAMES = {
    "Intradía": ["1m", "5m", "15m", "30m", "1h"],
    "Swing": ["1d", "1wk"],
    "Posicional": ["1mo", "3mo"]
}

def create_advanced_chart(data, timeframe="diario"):
    """Crea gráfico técnico avanzado"""
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
                f"Análisis Técnico ({timeframe})",
                "MACD",
                "RSI",
                "Volumen"
            )
        )

        # Velas y Bandas de Bollinger
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="OHLC"
            ),
            row=1, col=1
        )

        # Bollinger Bands
        for band in ['BB_High', 'BB_Mid', 'BB_Low']:
            if band in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[band],
                        name=band,
                        line=dict(dash='dash')
                    ),
                    row=1, col=1
                )

        # Medias Móviles
        for ma in ['SMA_20', 'SMA_50', 'SMA_200']:
            if ma in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[ma],
                        name=ma
                    ),
                    row=1, col=1
                )

        # MACD
        if all(x in data.columns for x in ['MACD', 'MACD_Signal']):
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['MACD'],
                    name='MACD'
                ),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['MACD_Signal'],
                    name='Señal'
                ),
                row=2, col=1
            )

        # RSI
        if 'RSI' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['RSI'],
                    name='RSI'
                ),
                row=3, col=1
            )

            # Líneas de referencia RSI
            fig.add_hline(y=70, line_color="red", line_dash="dash", row=3, col=1)
            fig.add_hline(y=30, line_color="green", line_dash="dash", row=3, col=1)

        # Volumen
        if 'Volume' in data.columns:
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volumen'
                ),
                row=4, col=1
            )

        # Layout
        fig.update_layout(
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )

        return fig

    except Exception as e:
        logger.error(f"Error creando gráfico: {str(e)}")
        return None

def setup_openai():
    """Configura credenciales de OpenAI"""
    try:
        API_KEY = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        ASSISTANT_ID = os.environ.get("ASSISTANT_ID") or st.secrets.get("ASSISTANT_ID")

        if not API_KEY or not ASSISTANT_ID:
            st.error("⚠️ Se requieren credenciales de OpenAI")
            st.stop()

        openai.api_key = API_KEY
        return ASSISTANT_ID

    except Exception as e:
        logger.error(f"Error configurando OpenAI: {str(e)}")
        st.error("Error al configurar OpenAI")
        st.stop()

def initialize_session_state():
    """Inicializa el estado de la sesión"""
    if "thread_id" not in st.session_state:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "current_symbol" not in st.session_state:
        st.session_state.current_symbol = "SPY"

    if "current_timeframe" not in st.session_state:
        st.session_state.current_timeframe = "1d"

def render_sidebar():
    """Renderiza la barra lateral"""
    with st.sidebar:
        st.title("🧑‍💻 Trading Assistant Pro")

        st.markdown("""
        ### Especialidades:
        - 📊 Análisis técnico avanzado
        - 📈 Trading de opciones y volatilidad
        - 🤖 Estrategias sistemáticas
        - ⚠️ Gestión de riesgo profesional

        ### Certificaciones:
        - Chartered Market Technician (CMT)
        - Financial Risk Manager (FRM)
        - Chartered Financial Analyst (CFA)
        """)

        st.markdown("---")

        # Contacto profesional
        st.markdown("""
        ### Contacto
        Alexander Oviedo Fadul

        [💼 LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/)
        [🌐 Website](https://alexanderoviedofadul.dev/)
        """)

        st.markdown("---")
        st.markdown("v1.0.0 | © 2025 InversorIA Pro")

def process_chat_input(prompt, ASSISTANT_ID):
    """Procesa la entrada del chat"""
    try:
        if st.session_state.current_symbol:
            context_prompt = f"""
            Analizando {st.session_state.current_symbol}:
            Timeframe: {st.session_state.current_timeframe}

            Consulta: {prompt}

            Por favor proporciona:
            1. Situación técnica actual
            2. Niveles clave
            3. Señales relevantes
            4. Recomendaciones específicas
            5. Gestión de riesgo
            """
        else:
            context_prompt = prompt

        # Enviar mensaje
        openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=context_prompt
        )

        # Crear ejecución
        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
            tools=tools
        )

        # Procesar respuesta
        with st.spinner("Analizando mercado..."):
            while True:
                run = openai.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )

                if run.status == "completed":
                    break
                elif run.status == "requires_action":
                    tool_outputs = process_tool_calls(
                        run.required_action.submit_tool_outputs.tool_calls,
                        st.session_state.current_symbol
                    )

                    run = openai.beta.threads.runs.submit_tool_outputs(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

                time.sleep(0.5)

            # Obtener respuesta
            messages = openai.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )

            for message in messages:
                if message.run_id == run.id and message.role == "assistant":
                    return message.content[0].text.value

        return None

    except Exception as e:
        logger.error(f"Error procesando chat: {str(e)}")
        return None

def main():
    try:
        # Inicialización
        initialize_session_state()
        ASSISTANT_ID = setup_openai()
        render_sidebar()

        # Layout principal
        col1, col2 = st.columns([2, 1])

        # Columna de Análisis
        with col1:
            st.title("💹 Análisis de Mercado")

            # Selectores
            col_cat, col_sym = st.columns(2)
            with col_cat:
                category = st.selectbox("Categoría", list(SYMBOLS.keys()))
            with col_sym:
                symbol = st.selectbox("Símbolo", SYMBOLS[category])

            if symbol != st.session_state.current_symbol:
                st.session_state.current_symbol = symbol

            # Pestañas de análisis
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
                [
                    "📈 Análisis Técnico",
                    "🎯 Opciones",
                    "📊 Multi-Timeframe",
                    "🔍 Fundamental",
                    "📋 Reporte",
                    "⚠️ Risk Management",
                ]
            )

            # Tab Técnico
            with tab1:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    timeframe = st.selectbox(
                        "Timeframe",
                        [tf for group in TIMEFRAMES.values() for tf in group],
                        index=4,
                    )
                with col2:
                    chart_type = st.selectbox(
                        "Tipo de Gráfico", ["Candlestick", "Línea", "Renko", "Heiken Ashi"]
                    )
                with col3:
                    indicator_sets = st.multiselect(
                        "Indicadores",
                        ["Tendencia", "Momentum", "Volatilidad", "Volumen"],
                        default=["Tendencia"],
                    )

                # Gráfico principal
                data = fetch_market_data(symbol, "1y", timeframe)
                if data is not None:
                    if len(data) < 20:
                        st.error("Se requieren al menos 20 períodos para análisis. Seleccione un intervalo más largo.")
                    else:
                        analyzer = TechnicalAnalyzer(data)
                        df_technical = analyzer.calculate_indicators()
                        if df_technical is not None:
                            fig = create_advanced_chart(df_technical, timeframe)
                            st.plotly_chart(fig, use_container_width=True)

                            # Métricas clave
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(
                                    "Precio",
                                    f"${df_technical['Close'].iloc[-1]:.2f}",
                                    f"{((df_technical['Close'].iloc[-1] / df_technical['Close'].iloc[-2]) - 1) * 100:.2f}%",
                                )
                            with col2:
                                st.metric(
                                    "RSI",
                                    f"{df_technical['RSI'].iloc[-1]:.1f}",
                                    "Sobrecomprado"
                                    if df_technical["RSI"].iloc[-1] > 70
                                    else "Sobrevendido"
                                    if df_technical["RSI"].iloc[-1] < 30
                                    else "Neutral",
                                )
                            with col3:
                                st.metric(
                                    "Volatilidad",
                                    f"{df_technical['ATR'].iloc[-1]:.2f}",
                                    f"{((df_technical['ATR'].iloc[-1] / df_technical['ATR'].mean()) - 1) * 100:.1f}% vs Media",
                                )
                            with col4:
                                st.metric(
                                    "Volumen",
                                    f"{df_technical['Volume'].iloc[-1]:,.0f}",
                                    f"{((df_technical['Volume'].iloc[-1] / df_technical['Volume'].mean()) - 1) * 100:.1f}% vs Media",
                                )

            # Tab Opciones
            with tab2:
                col1, col2 = st.columns([1, 2])
                with col1:
                    expiry_range = st.selectbox(
                        "Rango de Vencimientos",
                        ["Cercanos (1m)", "Medianos (1-3m)", "Lejanos (3m+)"],
                    )
                    strategy_type = st.selectbox(
                        "Tipo de Estrategia",
                        ["Direccional", "Volatilidad", "Income", "Hedging"],
                    )

                with col2:
                    st.markdown(f"""
                    ### Análisis de Volatilidad
                    - **IV Rank:** 65% (Percentil histórico)
                    - **IV vs HV:** +2.5 puntos
                    - **Term Structure:** Contango
                    - **Put/Call Skew:** 1.2
                    """)

                # Matriz de opciones
                st.subheader("Matriz de Opciones")
                expiry_dates = ["2024-03-15", "2024-04-19", "2024-06-21"]
                strikes = ["ATM-2", "ATM-1", "ATM", "ATM+1", "ATM+2"]

                options_data = pd.DataFrame(
                    index=strikes,
                    columns=pd.MultiIndex.from_product([expiry_dates, ["Call", "Put"]]),
                )
                st.dataframe(options_data.astype(str))

                # Estrategias sugeridas
                with st.expander("🎯 Estrategias Sugeridas"):
                    st.markdown("""
                    #### Neutral Bullish
                    - **Iron Condor:** Short 30 delta strangles con alas protectoras
                    - **Risk/Reward:** 1:2
                    - **Probabilidad de éxito:** 70%

                    #### Direccional
                    - **Call Debit Spread:** ATM/ATM+2 strikes
                    - **Delta:** 0.45
                    - **Theta:** -0.15
                    """)

            # Tab Multi-Timeframe
            with tab3:
                timeframes = ["1d", "1wk", "1mo"]
                analysis_multi = {}

                # Obtener análisis para cada timeframe
                for tf in timeframes:
                    data = fetch_market_data(symbol, "1y", tf)
                    if data is not None:
                        if len(data) < 20:
                            st.error(f"Se requieren al menos 20 períodos para análisis en el timeframe {tf}. Seleccione un intervalo más largo.")
                        else:
                            analyzer = TechnicalAnalyzer(data)
                            df = analyzer.calculate_indicators()
                            if df is not None:
                                analysis_multi[tf] = analyzer.get_current_signals()

                if analysis_multi:
                    # Vista en tabla
                    st.markdown("### Análisis Multi-Timeframe")
                    analysis_table = pd.DataFrame()

                    for tf in timeframes:
                        if tf in analysis_multi:
                            signals = analysis_multi[tf]
                            analysis_table.loc[tf, "Tendencia"] = signals["trend"]["sma_20_50"]
                            analysis_table.loc[tf, "RSI"] = f"{signals['momentum']['rsi']:.1f}"
                            analysis_table.loc[tf, "Volatilidad"] = signals["volatility"]["volatility_state"]
                            analysis_table.loc[tf, "Señal"] = signals["overall"]["signal"]

                    st.dataframe(analysis_table.astype(str))

                    # Gráficos comparativos
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Convergencia/Divergencia")
                        # Gráfico comparativo de Convergencia/Divergencia
                        fig_convergence = make_subplots(
                            rows=1,
                            cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.05,
                            subplot_titles=("Convergencia/Divergencia")
                        )

                        for tf in timeframes:
                            if tf in analysis_multi:
                                signals = analysis_multi[tf]
                                fig_convergence.add_trace(
                                    go.Scatter(
                                        x=data.index,
                                        y=data['Close'],
                                        name=f"Close ({tf})",
                                        mode='lines'
                                    )
                                )

                        st.plotly_chart(fig_convergence, use_container_width=True)

                    with col2:
                        st.markdown("### Correlación Temporal")
                        # Gráfico comparativo de Correlación Temporal
                        fig_correlation = make_subplots(
                            rows=1,
                            cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.05,
                            subplot_titles=("Correlación Temporal")
                        )

                        for tf in timeframes:
                            if tf in analysis_multi:
                                signals = analysis_multi[tf]
                                fig_correlation.add_trace(
                                    go.Scatter(
                                        x=data.index,
                                        y=data['Close'],
                                        name=f"Close ({tf})",
                                        mode='lines'
                                    )
                                )

                        st.plotly_chart(fig_correlation, use_container_width=True)

            # Tab Fundamental
            with tab4:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Métricas de Valoración")
                    metrics = {
                        "P/E Ratio": "25.4",
                        "P/B Ratio": "3.2",
                        "EV/EBITDA": "15.6",
                        "ROE": "18.5%",
                        "Margen Operativo": "22.4%",
                    }

                    for metric, value in metrics.items():
                        st.metric(metric, value)

                with col2:
                    st.markdown("### Análisis Sectorial")
                    st.markdown("""
                    - **Posición Competitiva:** Líder
                    - **Cuota de Mercado:** 23.5%
                    - **Crecimiento YoY:** +15.2%
                    - **Margen vs Industria:** +2.5pp
                    """)

                # Análisis fundamental detallado
                with st.expander("📊 Análisis Detallado"):
                    st.markdown("""
                    ### Fortalezas
                    - Fuerte posición de mercado
                    - Alta generación de caja
                    - Márgenes superiores a la media

                    ### Oportunidades
                    - Expansión internacional
                    - Nuevos segmentos de mercado
                    - Sinergias potenciales

                    ### Riesgos
                    - Presión regulatoria
                    - Competencia emergente
                    - Ciclo económico
                    """)

            # Tab Reporte
            with tab5:
                st.markdown("### Resumen Ejecutivo")

                # Situación Técnica
                st.markdown("""
                #### 📈 Análisis Técnico
                - **Tendencia Dominante:** Alcista moderada
                - **Momentum:** Positivo (RSI: 58)
                - **Volatilidad:** Baja (ATR percentil 25)
                - **Volumen:** Por encima de la media (+15%)

                #### 🎯 Niveles Clave
                - **Resistencia:** $158.50 (máximo previo)
                - **Soporte:** $152.30 (MA50)
                - **Stop Loss Sugerido:** $150.75
                - **Objetivo:** $162.25

                #### ⚠️ Gestión de Riesgo
                - **Posición Máxima:** 5% del portafolio
                - **Ratio Riesgo/Recompensa:** 1:2.5
                - **Stop Loss %:** -2.5%
                - **Take Profit %:** +6.25%
                """)

                # Recomendaciones
                with st.expander("🎯 Recomendaciones"):
                    st.markdown("""
                    ### Estrategia Sugerida
                    1. **Entrada:** Compra en pullback a MA20
                    2. **Stop:** Por debajo de MA50
                    3. **Objetivo 1:** +4% (resistencia previa)
                    4. **Objetivo 2:** +6.25% (extensión Fibonacci)

                    ### Consideraciones
                    - Mantener posición mientras RSI > 40
                    - Ajustar stop a breakeven después de +2%
                    - Considerar toma parcial de beneficios
                    """)

            # Tab Risk Management
            with tab6:
                st.markdown("### Análisis de Riesgo")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    #### 📊 Métricas de Riesgo
                    - **Beta:** 1.15
                    - **Volatilidad Histórica:** 22.5%
                    - **Drawdown Máximo:** -15.4%
                    - **Sharpe Ratio:** 1.8
                    """)

                with col2:
                    st.markdown("""
                    #### ⚠️ Gestión de Posición
                    - **Tamaño Sugerido:** 5% del capital
                    - **Stop Loss:** 2.5%
                    - **Correlación SPY:** 0.75
                    - **VAR (95%):** -1.8%
                    """)

                # Escenarios
                st.markdown("### Análisis de Escenarios")
                scenarios = {
                    "Alcista": "+12.5% (probabilidad: 35%)",
                    "Base": "+6.25% (probabilidad: 45%)",
                    "Bajista": "-4.5% (probabilidad: 20%)",
                }

                for scenario, projection in scenarios.items():
                    st.metric(scenario, projection)

                # Correlaciones
                with st.expander("📊 Matriz de Correlaciones"):
                    st.markdown("""
                    - **SPY:** +0.75
                    - **QQQ:** +0.82
                    - **Sector:** +0.88
                    - **VIX:** -0.45
                    """)

        # Columna del Chat
        with col2:
            st.title("💬 Trading Assistant")

            # Mostrar contexto mejorado
            if st.session_state.current_symbol:
                st.info(f"""
                ### 📊 Análisis Actual: {st.session_state.current_symbol}

                **Capacidades de Análisis:**

                📈 **Análisis Técnico**
                - Patrones chartistas y price action
                - Indicadores avanzados y divergencias
                - Análisis multi-timeframe
                - Identificación de niveles clave

                🎯 **Opciones y Derivados**
                - Estrategias direccionales y de volatilidad
                - Análisis de superficie de volatilidad
                - Greeks y gestión de posiciones
                - Implementación de spreads

                📊 **Análisis Cuantitativo**
                - Métricas de riesgo/retorno
                - Correlaciones y beta
                - Análisis de volumen y flujos
                - Backtesting de estrategias

                ⚠️ **Gestión de Riesgo**
                - Sizing de posiciones
                - Stop loss dinámicos
                - Escenarios y stress testing
                - Optimización de portafolio
                """)

            # Chat container
            chat_container = st.container()

            with chat_container:
                # Mostrar mensajes
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                # Input
                if prompt := st.chat_input("¿Qué análisis necesitas?"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    # Procesar respuesta
                    response = process_chat_input(prompt, ASSISTANT_ID)
                    if response:
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )
                        with st.chat_message("assistant"):
                            st.markdown(response)
                    else:
                        st.error("Error procesando respuesta")

        # Controles del chat
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Limpiar Chat"):
                st.session_state.messages = []
                st.rerun()

        with col2:
            if st.button("📋 Exportar Análisis"):
                try:
                    # Preparar datos de exportación
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = (
                        f"analysis_{st.session_state.current_symbol}_{timestamp}.txt"
                    )

                    # Obtener análisis actual
                    context = get_market_context(st.session_state.current_symbol)

                    with open(filename, "w", encoding="utf-8") as f:
                        # Encabezado
                        f.write(f"=== InversorIA Pro: Análisis Técnico Avanzado ===\n")
                        f.write(f"Símbolo: {st.session_state.current_symbol}\n")
                        f.write(
                            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        )

                        # Datos técnicos
                        if context:
                            f.write("=== Análisis Técnico ===\n")
                            f.write(f"Precio: ${context['last_price']:.2f}\n")
                            f.write(f"Cambio: ${context['change']:.2f}\n\n")

                            f.write("=== Señales Técnicas ===\n")
                            f.write(
                                f"Tendencia: {context['signals']['trend']['sma_20_50']}\n"
                            )
                            f.write(
                                f"RSI: {context['signals']['momentum']['rsi']:.1f}\n"
                            )
                            f.write(
                                f"Volatilidad: {context['signals']['volatility']['bb_width']:.4f}\n\n"
                            )

                        # Conversación
                        f.write("=== Análisis del Trading Assistant ===\n")
                        for message in st.session_state.messages:
                            f.write(f"\n[{message['role'].upper()}]\n")
                            f.write(f"{message['content']}\n")

                        # Disclaimer
                        f.write("\n=== Disclaimer ===\n")
                        f.write(
                            "Este análisis es generado automáticamente y no constituye "
                            "asesoramiento financiero. Realice su propio due diligence "
                            "antes de tomar decisiones de inversión.\n"
                        )

                    st.success(f"Análisis guardado en {filename}")

                except Exception as e:
                    logger.error(f"Error exportando análisis: {str(e)}")
                    st.error("Error al exportar el análisis")

        # Información del sistema
        st.markdown("---")
        with st.expander("ℹ️ Información del Sistema"):
            st.markdown(f"""
            ### Sistema de Trading
            - **Versión:** 1.0.0
            - **Última actualización:** {datetime.now().strftime("%Y-%m-%d")}
            - **Símbolos activos:** {len([s for cats in SYMBOLS.values() for s in cats])}
            - **Indicadores técnicos:** 12
            - **Timeframes:** {sum(len(tfs) for tfs in TIMEFRAMES.values())}

            ### Capacidades
            - Análisis técnico multi-timeframe
            - Integración con IA para análisis avanzado
            - Procesamiento en tiempo real
            - Exportación de informes detallados

            ### Advertencia de Riesgo
            Este es un sistema profesional de análisis técnico. Las señales y
            recomendaciones generadas deben ser validadas con análisis adicional
            y gestión de riesgo apropiada.
            """)

    except Exception as e:
        logger.error(f"Error en aplicación principal: {str(e)}")
        st.error(
            "Error en la aplicación. Por favor, revise los logs para más detalles."
        )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error en aplicación principal: {str(e)}")
        st.error(
            "Error en la aplicación. Por favor, revise los logs para más detalles."
        )
