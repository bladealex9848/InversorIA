import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ta
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.utils import dropna

# Verificación de autenticación
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.title("🔒 Acceso Restringido")
    st.warning("Por favor, inicie sesión desde la página principal del sistema.")
    st.stop()

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Acciones Pro",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

def get_popular_symbols():
    """Retorna una lista de símbolos populares por categoría"""
    return {
        "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "PYPL", "CRM"],
        "Finanzas": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK"],
        "Salud": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "AMGN", "BMY", "GILD", "TMO"],
        "Energía": ["XOM", "CVX", "SHEL", "TTE", "COP", "EOG", "PXD", "DVN", "MPC", "PSX"],
        "Consumo Discrecional": ["MCD", "SBUX", "NKE", "TGT", "HD", "LOW", "TJX", "ROST", "CMG", "DHI"],
        "Índices": ["SPY", "QQQ", "DIA", "IWM", "EFA", "VWO", "IYR", "XLE", "XLF", "XLV"],
        "Cripto ETFs": ["BITO", "GBTC", "ETHE", "ARKW", "BLOK"],
        "Materias Primas": ["GLD", "SLV", "USO", "UNG", "CORN", "SOYB", "WEAT"],
        "Bonos": ["AGG", "BND", "IEF", "TLT", "LQD", "HYG", "JNK", "TIP", "MUB", "SHY"],
        "Inmobiliario": ["VNQ", "XLRE", "IYR", "REIT", "HST", "EQR", "AVB", "PLD", "SPG", "AMT"]
    }

@st.cache_data(ttl=300)
def fetch_stock_price(symbol):
    """Obtiene el precio actual de una acción"""
    try:
        ticker = yf.Ticker(symbol)
        todays_data = ticker.history(period="1d")
        if not todays_data.empty:
            return {
                "price": round(todays_data["Close"].iloc[-1], 2),
                "change": round(todays_data["Close"].iloc[-1] - todays_data["Open"].iloc[-1], 2),
                "change_percent": round(
                    ((todays_data["Close"].iloc[-1] - todays_data["Open"].iloc[-1])/todays_data["Open"].iloc[-1])*100,2),
            }
        return None
    except Exception as e:
        st.error(f"Error obteniendo datos para {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def fetch_stock_info(symbol):
    """Obtiene información general sobre una acción"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": f"${info.get('marketCap', 'N/A'):,}" if isinstance(info.get('marketCap'), (int, float)) else "N/A",
            "pe_ratio": round(info.get("trailingPE", "N/A"),2) if isinstance(info.get('trailingPE'), (int, float)) else "N/A",
            "dividend_yield": f"{round(info.get('dividendYield', 0)*100,2)}%" if isinstance(info.get('dividendYield'), (int, float)) else "N/A",
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A")
        }
    except Exception as e:
        st.error(f"Error obteniendo información para {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def fetch_stock_data(symbol, period="6mo", interval="1d"):
    """Descarga datos históricos de una acción"""
    try:
        data = yf.download(symbol, period=period, interval=interval, auto_adjust=True)
        return dropna(data) if not data.empty else None
    except Exception as e:
        st.error(f"Error descargando datos para {symbol}: {str(e)}")
        return None

def calculate_technical_indicators(data):
    """Calcula indicadores técnicos optimizados"""
    try:
        close_prices = data['Close'].squeeze()
        
        # Indicadores de tendencia
        data['SMA20'] = SMAIndicator(close_prices, window=20).sma_indicator()
        data['EMA20'] = EMAIndicator(close_prices, window=20).ema_indicator()
        
        # Momentum
        data['RSI'] = RSIIndicator(close_prices, window=14).rsi()
        
        # MACD
        macd = MACD(close_prices)
        data['MACD'] = macd.macd()
        data['MACD_signal'] = macd.macd_signal()
        data['MACD_diff'] = macd.macd_diff()
        
        return data.dropna().copy()
    except Exception as e:
        st.error(f"Error calculando indicadores técnicos: {str(e)}")
        return None

def create_price_chart(data):
    """Crea gráfico de precios interactivo"""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data.index, data['Close'], label='Precio de Cierre', color='#1f77b4', linewidth=2)
    
    # Configuración del gráfico
    ax.set_title('Análisis de Precios Históricos', fontsize=16, pad=20)
    ax.set_xlabel('Fecha', fontsize=12)
    ax.set_ylabel('Precio (USD)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    plt.tight_layout()
    return fig

def create_technical_charts(data):
    """Genera gráficos técnicos profesionales"""
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 1])
    
    # Gráfico de tendencia
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(data.index, data['Close'], label='Precio', color='#1f77b4', alpha=0.8)
    ax1.plot(data.index, data['SMA20'], label='SMA 20', color='#ff7f0e', linestyle='--')
    ax1.plot(data.index, data['EMA20'], label='EMA 20', color='#2ca02c', linestyle='-.')
    ax1.set_title('Indicadores de Tendencia', fontsize=14)
    ax1.legend(loc='upper left')
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Gráfico RSI
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(data.index, data['RSI'], label='RSI 14', color='#9467bd', alpha=0.8)
    ax2.fill_between(data.index, 70, 30, color='#d3d3d3', alpha=0.3)
    ax2.axhline(70, color='red', linestyle='--', alpha=0.7, linewidth=1)
    ax2.axhline(30, color='green', linestyle='--', alpha=0.7, linewidth=1)
    ax2.set_title('Índice de Fuerza Relativa (RSI)', fontsize=14)
    ax2.set_ylim(0, 100)
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # Gráfico MACD
    ax3 = fig.add_subplot(gs[2])
    colors = np.where(data['MACD_diff'] > 0, '#4dac26', '#d01c8b')
    ax3.bar(data.index, data['MACD_diff'], color=colors, alpha=0.6, width=0.8)
    ax3.plot(data.index, data['MACD'], label='MACD', color='#17becf', linewidth=1.5)
    ax3.plot(data.index, data['MACD_signal'], label='Señal', color='#e377c2', linewidth=1.5)
    ax3.set_title('MACD (Convergencia/Divergencia de Medias Móviles)', fontsize=14)
    ax3.legend(loc='upper left')
    ax3.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    return fig

@st.cache_data(ttl=3600)
def fetch_options_data(symbol):
    """Descarga datos de opciones con manejo de errores"""
    try:
        ticker = yf.Ticker(symbol)
        options = ticker.options
        if options:
            expiry = options[0]
            options_data = ticker.option_chain(expiry)
            return {
                "calls": options_data.calls,
                "puts": options_data.puts,
                "expiry": expiry
            }
        return None
    except Exception as e:
        st.error(f"Error obteniendo opciones: {str(e)}")
        return None

def main():
    st.title("🚀 Analizador de Mercado Profesional")
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("Parámetros de Análisis")
        popular_symbols = get_popular_symbols()
        category = st.selectbox("Categoría", list(popular_symbols.keys()))
        symbol = st.selectbox("Seleccionar Activo", popular_symbols[category])
        period = st.selectbox("Período Histórico", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
        analysis_type = st.radio("Tipo de Análisis", ["Básico", "Avanzado"])
    
    # Main Content Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Análisis Técnico", "Datos Históricos", "Opciones"])
    
    with tab1:
        # Resumen Ejecutivo
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Datos en Tiempo Real")
            price_data = fetch_stock_price(symbol)
            if price_data:
                delta_color = "inverse" if price_data['change'] < 0 else "normal"
                st.metric(
                    label="Precio Actual",
                    value=f"${price_data['price']}",
                    delta=f"{price_data['change']} ({price_data['change_percent']}%)",
                    delta_color=delta_color
                )
                st.progress(abs(price_data['change_percent'])/100 if price_data['change_percent'] else 0)
            else:
                st.warning("Datos de precio no disponibles")
        
        with col2:
            st.subheader("Información Fundamental")
            info_data = fetch_stock_info(symbol)
            if info_data:
                st.markdown(f"""
                - **Empresa:** {info_data['name']}
                - **Sector:** {info_data['sector']}
                - **Industria:** {info_data['industry']}
                - **Cap. Mercado:** {info_data['market_cap']}
                - **P/E Ratio:** {info_data['pe_ratio']}
                - **Dividend Yield:** {info_data['dividend_yield']}
                - **52 Sem. Alto:** ${info_data['52_week_high']}
                - **52 Sem. Bajo:** ${info_data['52_week_low']}
                """)
            else:
                st.warning("Información fundamental no disponible")
    
    with tab2:
        # Análisis Técnico
        st.subheader("Análisis Técnico Detallado")
        data = fetch_stock_data(symbol, period)
        if data is not None:
            tech_data = calculate_technical_indicators(data)
            if tech_data is not None:
                st.pyplot(create_technical_charts(tech_data))
                
                # Estadísticas Clave
                st.subheader("Estadísticas Técnicas")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("RSI Actual", f"{tech_data['RSI'].iloc[-1]:.2f}")
                with col2:
                    st.metric("MACD", f"{tech_data['MACD'].iloc[-1]:.2f}")
                with col3:
                    st.metric("SMA/EMA Diff", f"{(tech_data['SMA20'].iloc[-1] - tech_data['EMA20'].iloc[-1]):.2f}")
            else:
                st.error("Error en cálculo de indicadores")
        else:
            st.warning("Datos históricos no disponibles")
    
    with tab3:
        # Datos Históricos
        st.subheader("Datos Históricos Completos")
        data = fetch_stock_data(symbol, period)
        if data is not None:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write("**Últimos Registros**")
                st.dataframe(
                    data.tail(10).style.format("{:.2f}"),
                    height=400,
                    use_container_width=True
                )
            with col2:
                st.write("**Evolución de Precios**")
                st.pyplot(create_price_chart(data))
        else:
            st.warning("No se encontraron datos históricos")
    
    with tab4:
        # Opciones
        st.subheader("Datos de Opciones Financieras")
        options_data = fetch_options_data(symbol)
        if options_data:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Opciones Call ({options_data['expiry']})**")
                st.dataframe(
                    options_data["calls"].sort_values("volume", ascending=False).head(10),
                    column_config={
                        "strike": "Strike Price",
                        "lastPrice": "Último Precio",
                        "volume": "Volumen"
                    }
                )
            with col2:
                st.markdown(f"**Opciones Put ({options_data['expiry']})**")
                st.dataframe(
                    options_data["puts"].sort_values("volume", ascending=False).head(10),
                    column_config={
                        "strike": "Strike Price",
                        "lastPrice": "Último Precio",
                        "volume": "Volumen"
                    }
                )
        else:
            st.info("No hay datos de opciones disponibles")

if __name__ == "__main__":
    main()