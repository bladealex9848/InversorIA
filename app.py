import os
import openai
import streamlit as st
import time
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import ta
from ta.trend import MACD, SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from scipy.stats import norm
import logging
import warnings
warnings.filterwarnings('ignore')

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Función para verificar secrets.toml
def secrets_file_exists():
    """Verifica la existencia del archivo secrets.toml"""
    try:
        secrets_path = os.path.join('.streamlit', 'secrets.toml')
        return os.path.isfile(secrets_path)
    except Exception as e:
        logger.error(f"Error verificando secrets.toml: {str(e)}")
        return False

# Función para obtener credenciales
def get_credentials():
    """Obtiene las credenciales de OpenAI"""
    try:
        if secrets_file_exists():
            return st.secrets.get("OPENAI_API_KEY"), st.secrets.get("ASSISTANT_ID")
        return None, None
    except Exception as e:
        logger.error(f"Error obteniendo credenciales: {str(e)}")
        return None, None

# Configuración de OpenAI
API_KEY, ASSISTANT_ID = get_credentials()

if not API_KEY:
    API_KEY = os.environ.get("OPENAI_API_KEY") or st.sidebar.text_input(
        "OpenAI API Key", type="password"
    )

if not ASSISTANT_ID:
    ASSISTANT_ID = os.environ.get("ASSISTANT_ID") or st.sidebar.text_input(
        "ID del Asistente", type="password"
    )

if not API_KEY or not ASSISTANT_ID:
    st.error("⚠️ Se requieren credenciales de OpenAI")
    st.stop()

openai.api_key = API_KEY

# Configuración de la página
st.set_page_config(
    page_title="InversorIA Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.alexanderoviedofadul.dev/',
        'Report a bug': None,
        'About': "InversorIA: Plataforma avanzada de trading con IA"
    }
)

def get_popular_symbols():
    """Retorna lista completa de símbolos por categoría"""
    return {
        "Tecnología": [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "NVDA",
            "META",
            "NFLX",
            "PYPL",
            "CRM",
        ],
        "Finanzas": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK"],
        "Salud": [
            "JNJ",
            "UNH",
            "PFE",
            "MRK",
            "ABBV",
            "LLY",
            "AMGN",
            "BMY",
            "GILD",
            "TMO",
        ],
        "Energía": [
            "XOM",
            "CVX",
            "SHEL",
            "TTE",
            "COP",
            "EOG",
            "PXD",
            "DVN",
            "MPC",
            "PSX",
        ],
        "Índices": [
            "SPY",
            "QQQ",
            "DIA",
            "IWM",
            "EFA",
            "VWO",
            "IYR",
            "XLE",
            "XLF",
            "XLV",
        ],
        "ETFs Volatilidad": ["VXX", "UVXY", "SVXY", "VIXY"],
        "Cripto ETFs": ["BITO", "GBTC", "ETHE", "ARKW", "BLOK"],
        "Opciones Populares": ["SPY", "QQQ", "IWM", "AAPL", "TSLA", "NVDA", "AMD"],
    }


@st.cache_data(ttl=300)
def fetch_market_data(symbol, period='6mo', interval='1d'):
    """Obtiene datos de mercado con manejo mejorado de errores"""
    try:
        # Descargar datos con yfinance
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        
        if data.empty:
            logger.error(f"No se encontraron datos para {symbol}")
            return None
            
        # Validar estructura de datos
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required_columns):
            logger.error(f"Datos incompletos para {symbol}")
            return None
            
        # Convertir a DataFrame y limpiar datos
        df = pd.DataFrame(data)
        
        # Convertir columnas a tipo float
        for col in required_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Eliminar filas con valores NaN
        df = df.dropna()
        
        # Validar índice temporal
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
            
        # Validar que tenemos suficientes datos
        if len(df) < 20:
            logger.error(f"Insuficientes datos para {symbol}")
            return None
            
        return df
        
    except Exception as e:
        logger.error(f"Error cargando datos: {str(e)}")
        return None


class MarketAnalyzer:
    """Clase para análisis de mercado con manejo mejorado de errores"""
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.data = None
        self.technical_data = None
        self.ticker = yf.Ticker(symbol)
        
    def load_data(self, period='6mo', interval='1d'):
        """Carga datos de mercado usando la función mejorada"""
        try:
            self.data = fetch_market_data(self.symbol, period, interval)
            return self.data is not None
        except Exception as e:
            logger.error(f"Error en load_data: {str(e)}")
            return False
            
    def calculate_indicators(self):
        """Calcula indicadores técnicos con validación mejorada"""
        try:
            if self.data is None or self.data.empty:
                logger.error("No hay datos disponibles para calcular indicadores")
                return None
                
            df = self.data.copy()
            
            # Verificar que tenemos precios de cierre
            if 'Close' not in df.columns:
                logger.error("No se encontraron precios de cierre")
                return None
                
            close_prices = df['Close'].astype(float)
            
            # MACD
            macd = MACD(close_prices)
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Hist'] = macd.macd_diff()
            
            # RSI
            rsi = RSIIndicator(close_prices)
            df['RSI'] = rsi.rsi()
            
            # Bollinger Bands
            bb = BollingerBands(close_prices)
            df['BB_High'] = bb.bollinger_hband()
            df['BB_Low'] = bb.bollinger_lband()
            df['BB_Mid'] = bb.bollinger_mavg()
            
            # Moving Averages
            for period in [20, 50, 200]:
                df[f'SMA_{period}'] = SMAIndicator(
                    close_prices, 
                    window=period
                ).sma_indicator()
            
            self.technical_data = df
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores: {str(e)}")
            return None

    def get_market_profile(self):
        """Obtiene perfil completo del mercado"""
        try:
            info = self.ticker.info
            return {
                "name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "volume": info.get("volume", "N/A"),
                "beta": info.get("beta", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "forward_pe": info.get("forwardPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
                "avg_volume": info.get("averageVolume", "N/A"),
                "return_on_equity": info.get("returnOnEquity", "N/A"),
                "profit_margins": info.get("profitMargins", "N/A"),
            }
        except Exception as e:
            logger.error(f"Error en perfil: {str(e)}")
            return None

    def get_options_chain(self):
        """Obtiene datos de opciones con Greeks"""
        try:
            expirations = self.ticker.options
            if not expirations:
                return None

            chains = {}
            current_price = self.data["Close"].iloc[-1]

            for expiry in expirations:
                opt = self.ticker.option_chain(expiry)

                # Calcular Greeks para calls y puts
                calls = self.calculate_greeks(opt.calls, current_price, expiry)
                puts = self.calculate_greeks(opt.puts, current_price, expiry)

                chains[expiry] = {"calls": calls, "puts": puts}

            return chains
        except Exception as e:
            logger.error(f"Error en opciones: {str(e)}")
            return None

    @staticmethod
    def calculate_greeks(options_data, spot_price, expiry_date, risk_free_rate=0.02):
        """Calcula Greeks para opciones"""
        try:
            expiry = pd.to_datetime(expiry_date)
            options = options_data.copy()

            for idx, option in options.iterrows():
                T = (expiry - datetime.now()).days / 365
                if T <= 0:
                    continue

                K = option["strike"]
                sigma = option["impliedVolatility"]
                S = spot_price
                r = risk_free_rate

                d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
                d2 = d1 - sigma * np.sqrt(T)

                is_call = "C" in option["contractSymbol"]

                # Delta
                options.loc[idx, "delta"] = norm.cdf(d1) if is_call else -norm.cdf(-d1)

                # Gamma
                options.loc[idx, "gamma"] = norm.pdf(d1) / (S * sigma * np.sqrt(T))

                # Theta
                if is_call:
                    theta = -S * norm.pdf(d1) * sigma / (
                        2 * np.sqrt(T)
                    ) - r * K * np.exp(-r * T) * norm.cdf(d2)
                else:
                    theta = -S * norm.pdf(d1) * sigma / (
                        2 * np.sqrt(T)
                    ) + r * K * np.exp(-r * T) * norm.cdf(-d2)
                options.loc[idx, "theta"] = theta / 365

                # Vega
                options.loc[idx, "vega"] = S * np.sqrt(T) * norm.pdf(d1) / 100

            return options

        except Exception as e:
            logger.error(f"Error en Greeks: {str(e)}")
            return options_data


def create_technical_chart(data):
    """Crea gráfico técnico avanzado"""
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=("Precio y Tendencias", "MACD", "RSI"),
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="OHLC",
        ),
        row=1,
        col=1,
    )

    # Medias móviles y Bandas de Bollinger
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_High"],
            name="BB Superior",
            line=dict(color="gray", dash="dash"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["BB_Low"],
            name="BB Inferior",
            line=dict(color="gray", dash="dash"),
            fill="tonexty",
        ),
        row=1,
        col=1,
    )

    for period in [20, 50, 200]:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data[f"SMA_{period}"],
                name=f"SMA {period}",
                line=dict(width=1),
            ),
            row=1,
            col=1,
        )

    # MACD
    fig.add_trace(
        go.Scatter(x=data.index, y=data["MACD"], name="MACD", line=dict(color="blue")),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MACD_Signal"],
            name="Señal MACD",
            line=dict(color="orange"),
        ),
        row=2,
        col=1,
    )

    # Histograma MACD
    colors = np.where(data["MACD_Hist"] >= 0, "green", "red")
    fig.add_trace(
        go.Bar(
            x=data.index, y=data["MACD_Hist"], name="MACD Hist", marker_color=colors
        ),
        row=2,
        col=1,
    )

    # RSI
    fig.add_trace(
        go.Scatter(x=data.index, y=data["RSI"], name="RSI", line=dict(color="purple")),
        row=3,
        col=1,
    )

    # Líneas RSI
    fig.add_hline(y=70, line_color="red", line_dash="dash", row=3, col=1)
    fig.add_hline(y=30, line_color="green", line_dash="dash", row=3, col=1)

    # Diseño
    fig.update_layout(
        height=900,
        title_text=f"Análisis Técnico Avanzado",
        showlegend=True,
        xaxis_rangeslider_visible=False,
    )

    return fig


def create_options_table(options_data):
    """Formatea tabla de opciones"""
    columns = {
        "strike": "Strike",
        "lastPrice": "Último",
        "bid": "Bid",
        "ask": "Ask",
        "volume": "Volumen",
        "openInterest": "Open Int.",
        "impliedVolatility": "Vol. Impl.",
        "delta": "Delta",
        "gamma": "Gamma",
        "theta": "Theta",
        "vega": "Vega",
    }

    formatted = options_data[columns.keys()].copy()
    formatted.columns = columns.values()

    # Formato números
    formatted["Vol. Impl."] = formatted["Vol. Impl."].map("{:.2%}".format)
    for col in ["Delta", "Gamma", "Theta", "Vega"]:
        formatted[col] = formatted[col].map("{:.4f}".format)

    return formatted


# Configuración de la barra lateral
with st.sidebar:
    st.subheader("🧑‍💻 Experto en Trading")
    st.markdown("""
    ### Especialidades:
    - 📊 Análisis técnico avanzado
    - 📈 Trading de opciones y volatilidad
    - 🤖 Estrategias cuantitativas
    - ⚠️ Risk management profesional
    - 📉 Market microstructure
    """)

    st.markdown("---")
    st.markdown("ℹ️ Información de Contacto")
    st.markdown("Alexander Oviedo Fadul")
    st.markdown(
        "[💼 LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/) | [🌐 Website](https://alexanderoviedofadul.dev/)"
    )

    st.markdown("---")
    st.markdown("Version: 1.0.0")
    st.markdown("© 2025 Todos los derechos reservados")

    # Configuración de OpenAI
    st.markdown("---")
    st.subheader("⚙️ Configuración")
    if secrets_file_exists():
        try:
            ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
        except KeyError:
            ASSISTANT_ID = None
    else:
        ASSISTANT_ID = None

    if not ASSISTANT_ID:
        ASSISTANT_ID = st.text_input("ID del Asistente de OpenAI", type="password")

    API_KEY = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    if not API_KEY:
        API_KEY = st.text_input("OpenAI API Key", type="password")

    if not ASSISTANT_ID or not API_KEY:
        st.error("⚠️ Se requieren las credenciales de OpenAI")
        st.stop()

    openai.api_key = API_KEY

# Herramientas para el asistente
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_market_data",
            "description": "Obtiene datos de mercado actualizados",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Símbolo del activo (ej: AAPL, MSFT)",
                    }
                },
                "required": ["symbol"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]


def main():
    # Inicialización del estado
    if "thread_id" not in st.session_state:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "current_symbol" not in st.session_state:
        st.session_state.current_symbol = "AAPL"

    # Layout principal: dos columnas
    col1, col2 = st.columns([2, 1])

    # Columna del Chat
    with col1:
        st.title("💬 Trading Assistant Pro")

        # Contador de visitantes
        st.write("""
                ![Visitantes](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Finversoria.streamlit.app&label=Visitantes&labelColor=%235d5d5d&countColor=%231e7ebf&style=flat)
                """)

        # Área de chat
        chat_container = st.container()

        with chat_container:
            # Mostrar mensajes
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Input del usuario
            if prompt := st.chat_input("¿Qué análisis necesitas hoy?"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Procesar con OpenAI
                openai.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id, role="user", content=prompt
                )

                run = openai.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=ASSISTANT_ID,
                    tools=tools,
                )

                # Procesar respuesta
                with st.spinner("Analizando mercado..."):
                    while True:
                        run = openai.beta.threads.runs.retrieve(
                            thread_id=st.session_state.thread_id, run_id=run.id
                        )

                        if run.status == "completed":
                            break
                        elif run.status == "requires_action":
                            # Procesar llamadas a funciones
                            tool_outputs = []
                            for (
                                tool_call
                            ) in run.required_action.submit_tool_outputs.tool_calls:
                                function_args = eval(tool_call.function.arguments)

                                # Inicializar analizador
                                market = MarketAnalyzer(function_args["symbol"])
                                if market.load_data():
                                    result = market.get_market_profile()
                                else:
                                    result = "Error cargando datos"

                                tool_outputs.append(
                                    {
                                        "tool_call_id": tool_call.id,
                                        "output": str(result),
                                    }
                                )

                            run = openai.beta.threads.runs.submit_tool_outputs(
                                thread_id=st.session_state.thread_id,
                                run_id=run.id,
                                tool_outputs=tool_outputs,
                            )

                        time.sleep(0.5)

                    # Mostrar respuesta
                    messages = openai.beta.threads.messages.list(
                        thread_id=st.session_state.thread_id
                    )

                    for message in messages:
                        if message.run_id == run.id and message.role == "assistant":
                            response = message.content[0].text.value
                            st.session_state.messages.append(
                                {"role": "assistant", "content": response}
                            )
                            with st.chat_message("assistant"):
                                st.markdown(response)

    # Columna de Análisis
    with col2:
        st.title("📊 Market Analysis")

        # Selector de categoría y símbolo
        popular_symbols = get_popular_symbols()

        symbol_category = st.selectbox(
            "Categoría", options=list(popular_symbols.keys()), key="symbol_category"
        )

        symbol = st.selectbox(
            "Activo", options=popular_symbols[symbol_category], key="symbol_select"
        )

        if symbol:
            st.session_state.current_symbol = symbol

            # Pestañas de análisis
            tab1, tab2, tab3 = st.tabs(["📈 Técnico", "🎯 Opciones", "📊 Señales"])

            # Inicializar analizador
            market = MarketAnalyzer(symbol)

            if market.load_data():
                # Calcular indicadores
                df_technical = market.calculate_indicators()

                if df_technical is not None:
                    # Tab Técnico
                    with tab1:
                        fig = create_technical_chart(df_technical)
                        st.plotly_chart(fig, use_container_width=True)

                        # Métricas
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "Precio",
                                f"${df_technical['Close'].iloc[-1]:.2f}",
                                f"{(df_technical['Close'].iloc[-1] - df_technical['Close'].iloc[-2]):.2f}",
                            )
                        with col2:
                            st.metric("RSI", f"{df_technical['RSI'].iloc[-1]:.2f}")

                    # Tab Opciones
                    with tab2:
                        options_chain = market.get_options_chain()
                        if options_chain:
                            expiry = st.selectbox(
                                "Vencimiento", options=list(options_chain.keys())
                            )

                            if expiry in options_chain:
                                st.subheader("Calls")
                                st.dataframe(
                                    create_options_table(
                                        options_chain[expiry]["calls"]
                                    ),
                                    use_container_width=True,
                                )

                                st.subheader("Puts")
                                st.dataframe(
                                    create_options_table(options_chain[expiry]["puts"]),
                                    use_container_width=True,
                                )
                        else:
                            st.warning("No hay opciones disponibles")

                    # Tab Señales
                    with tab3:
                        # Análisis de tendencia
                        trend = (
                            "alcista"
                            if df_technical["SMA_20"].iloc[-1]
                            > df_technical["SMA_50"].iloc[-1]
                            else "bajista"
                        )
                        rsi = df_technical["RSI"].iloc[-1]

                        st.info(f"""
                        ### Análisis Técnico
                        
                        📈 **Tendencia:** {trend.upper()}
                        📊 **RSI:** {rsi:.2f}
                        💰 **Precio:** ${df_technical["Close"].iloc[-1]:.2f}
                        """)

                        with st.expander("🔍 Análisis Detallado"):
                            st.markdown(f"""
                            ### Indicadores
                            - **MACD:** {"Alcista" if df_technical["MACD"].iloc[-1] > df_technical["MACD_Signal"].iloc[-1] else "Bajista"}
                            - **Volatilidad:** {((df_technical["BB_High"].iloc[-1] - df_technical["BB_Low"].iloc[-1]) / df_technical["Close"].iloc[-1] * 100):.2f}%
                            - **SMA 200:** {"Por encima" if df_technical["Close"].iloc[-1] > df_technical["SMA_200"].iloc[-1] else "Por debajo"}
                            """)

                        with st.expander("📋 Recomendaciones"):
                            if trend == "alcista":
                                if rsi < 70:
                                    st.markdown("""
                                    ### Estrategia CALL
                                    1. Comprar CALL ATM/OTM
                                    2. Stop: -50% premium
                                    3. Target: BB Superior
                                    """)
                                else:
                                    st.markdown("""
                                    ### PUT Credit Spread
                                    1. Vender PUT OTM
                                    2. Target: 50% beneficio
                                    3. Gestionar en earnings
                                    """)
                            else:
                                if rsi > 30:
                                    st.markdown("""
                                    ### Estrategia PUT
                                    1. Comprar PUT ATM/OTM
                                    2. Stop: -50% premium
                                    3. Target: BB Inferior
                                    """)
                                else:
                                    st.markdown("""
                                    ### CALL Credit Spread
                                    1. Vender CALL OTM
                                    2. Target: 50% beneficio
                                    3. Gestionar en earnings
                                    """)

                        st.warning("""
                        ⚠️ **Aviso de Riesgo**
                        
                        Este análisis es informativo y no constituye asesoramiento financiero.
                        Las operaciones con opciones conllevan alto riesgo.
                        """)
                else:
                    st.error("Error en indicadores técnicos")
            else:
                st.error("Error cargando datos de mercado")

        # Botón limpiar chat
        if st.button("🗑️ Limpiar Chat"):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    main()
