import streamlit as st
from trading_analyzer import TradingAnalyzer, MarketDataError
from market_scanner import run_scanner
import logging
from datetime import datetime
import pytz

# Verificación de autenticación
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.title("🔒 Acceso Restringido")
    st.warning("Por favor, inicie sesión desde la página principal del sistema.")
    st.stop()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Universo de Trading
SYMBOLS = {
    "Índices": ["SPY", "QQQ", "DIA", "IWM", "EFA", "VWO", "IYR", "XLE", "XLF", "XLV"],
    "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "PYPL", "CRM"],
    "Finanzas": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK"],
    "Salud": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "AMGN", "BMY", "GILD", "TMO"],
    "Energía": ["XOM", "CVX", "SHEL", "TTE", "COP", "EOG", "PXD", "DVN", "MPC", "PSX"],
    "Consumo": ["MCD", "SBUX", "NKE", "TGT", "HD", "LOW", "TJX", "ROST", "CMG", "DHI"],
    "Volatilidad": ["VXX", "UVXY", "SVXY", "VIXY"],
    "Cripto ETFs": ["BITO", "GBTC", "ETHE", "ARKW", "BLOK"],
    "Materias Primas": ["GLD", "SLV", "USO", "UNG", "CORN", "SOYB", "WEAT"],
    "Bonos": ["AGG", "BND", "IEF", "TLT", "LQD", "HYG", "JNK", "TIP", "MUB", "SHY"],
    "Inmobiliario": ["VNQ", "XLRE", "IYR", "REIT", "HST", "EQR", "AVB", "PLD", "SPG", "AMT"]
}

# Inicialización de estado
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None
if 'current_symbol' not in st.session_state:
    st.session_state.current_symbol = None
if 'scanner_last_update' not in st.session_state:
    st.session_state.scanner_last_update = None

def get_ny_time():
    """Obtiene hora actual en NY"""
    ny_tz = pytz.timezone('America/New_York')
    return datetime.now(ny_tz)

def display_market_status():
    """Muestra estado del mercado"""
    ny_time = get_ny_time()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hora NY", ny_time.strftime("%H:%M:%S"))
    with col2:
        analyzer = TradingAnalyzer()
        session = analyzer._get_market_session()
        st.metric("Sesión", session)
    with col3:
        next_update = "NA" if not st.session_state.scanner_last_update else \
            (st.session_state.scanner_last_update + pd.Timedelta(minutes=5)).strftime("%H:%M:%S")
        st.metric("Próx. Update", next_update)

def display_single_analysis(symbol, analyzer):
    """Muestra análisis de símbolo individual"""
    try:
        with st.spinner("Analizando mercado..."):
            trend, daily_data = analyzer.analyze_trend(symbol)
            
            # Análisis de Tendencia
            st.subheader("🎯 Análisis de Tendencia")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Dirección", trend["direction"], 
                    delta="↑" if trend["direction"] == "ALCISTA" else "↓" if trend["direction"] == "BAJISTA" else "→",
                    delta_color="normal" if trend["direction"] == "ALCISTA" else "inverse" if trend["direction"] == "BAJISTA" else "off")
            with col2:
                st.metric("Fuerza", trend["strength"])
            with col3:
                st.metric("Sesgo", trend["bias"])
            
            st.info(trend["description"])
            
            # Métricas Técnicas
            st.subheader("📊 Métricas Técnicas")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Precio", f"${trend['metrics']['price']:.2f}")
            with col2:
                st.metric("SMA200", f"${trend['metrics']['sma200']:.2f}")
            with col3:
                st.metric("RSI", f"{trend['metrics']['rsi']:.1f}")
            with col4:
                dist = ((trend['metrics']['price'] / trend['metrics']['sma200']) - 1) * 100
                st.metric("Dist. SMA200", f"{dist:.1f}%")
            
            # Análisis horario y estrategias
            hourly_data = analyzer.get_market_data(symbol, period="5d", interval="1h")
            strategies = analyzer.identify_strategy(hourly_data, trend)
            
            if strategies:
                st.subheader("📈 Estrategias Activas")
                
                for idx, strat in enumerate(strategies):
                    with st.expander(f"{strat['type']} - {strat['name']} (Confianza: {strat['confidence']})"):
                        st.write("**Descripción:**")
                        st.write(strat['description'])
                        
                        st.write("**Condiciones Técnicas:**")
                        for condition in strat['conditions']:
                            st.write(f"✓ {condition}")
                        
                        if 'levels' in strat:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Entry", f"${strat['levels']['entry']:.2f}")
                            with col2:
                                st.metric("Stop", f"${strat['levels']['stop']:.2f}")
                            with col3:
                                st.metric("Target", f"${strat['levels']['target']:.2f}")
                        
                        if strat['confidence'] == "ALTA":
                            st.success("""
                            ⭐ Oportunidad Confirmada
                            - Setup alineado con tendencia
                            - Condiciones técnicas óptimas
                            - Risk/Reward favorable
                            """)
                        else:
                            st.warning("""
                            ⚠️ Requiere Confirmación
                            - Validar niveles clave
                            - Confirmar volumen
                            - Monitorear momentum
                            """)
                
                # Risk Management
                st.subheader("⚠️ Gestión de Riesgo")
                col1, col2 = st.columns(2)
                with col1:
                    position_size = st.slider(
                        "Tamaño de Posición (%)",
                        min_value=1.0,
                        max_value=5.0,
                        value=2.0,
                        step=0.5
                    )
                with col2:
                    st.metric(
                        "Capital en Riesgo ($)",
                        f"${position_size * 1000:.2f}",
                        delta=f"{position_size}% del capital"
                    )
            else:
                st.warning("""
                **No hay estrategias activas**
                - Mercado sin señales claras
                - Mantener capital preservado
                - Esperar mejor setup
                """)
            
            # Niveles Técnicos
            st.subheader("📍 Niveles Técnicos")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Soportes/Resistencias:**")
                st.write(f"• SMA200: ${trend['metrics']['sma200']:.2f}")
                st.write(f"• SMA50: ${trend['metrics']['sma50']:.2f}")
                st.write(f"• SMA20: ${trend['metrics']['sma20']:.2f}")
            with col2:
                st.markdown("**Zonas RSI:**")
                rsi_current = trend['metrics']['rsi']
                st.write("• Sobrecompra: RSI > 70")
                st.write("• Neutral: RSI 30-70")
                st.write("• Sobreventa: RSI < 30")
                st.progress(min(rsi_current/100, 1.0))
            
    except MarketDataError as e:
        st.error(f"Error en datos de mercado: {str(e)}")
        logger.error(f"MarketDataError: {str(e)}")
        
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        logger.error(f"Error inesperado: {str(e)}")
        st.stop()

def main():
    st.set_page_config(
        page_title="InversorIA Mini Pro",
        page_icon="📊",
        layout="wide"
    )
    
    # Header Principal
    st.title("📊 InversorIA Mini Pro")
    display_market_status()
    
    # Navegación Principal
    tab1, tab2 = st.tabs(["🔍 Análisis Individual", "📡 Scanner de Mercado"])
    
    with tab1:
        # Análisis Individual
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Sector", list(SYMBOLS.keys()))
        with col2:
            symbol = st.selectbox("Activo", SYMBOLS[category])
        
        if symbol != st.session_state.current_symbol:
            st.session_state.current_symbol = symbol
            st.session_state.last_analysis = None
        
        analyzer = TradingAnalyzer()
        display_single_analysis(symbol, analyzer)
        
    with tab2:
        # Scanner de Mercado
        st.subheader("📡 Scanner de Mercado")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            scan_interval = st.selectbox(
                "Intervalo",
                ["1 min", "5 min", "15 min"],
                index=1
            )
        with col2:
            confidence_filter = st.selectbox(
                "Confianza",
                ["Todas", "Alta", "Media"],
                index=0
            )
        with col3:
            sector_filter = st.multiselect(
                "Sectores",
                list(SYMBOLS.keys()),
                default=list(SYMBOLS.keys())
            )
        
        if st.button("🔄 Actualizar Scanner"):
            run_scanner(SYMBOLS)
    
    # Disclaimer profesional
    st.markdown("---")
    st.caption("""
    **⚠️ Disclaimer Profesional:**
    Este sistema provee análisis técnico cuantitativo y requiere validación profesional.
    Las señales identificadas deben ser confirmadas con análisis adicional y gestión de riesgo apropiada.
    Trading implica riesgo sustancial de pérdida. Realizar due diligence exhaustivo.
    """)

if __name__ == "__main__":
    main()