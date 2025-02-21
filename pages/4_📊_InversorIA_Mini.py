import streamlit as st
from trading_analyzer import TradingAnalyzer, MarketDataError
from market_scanner import MarketScanner
import pandas as pd
import logging
from datetime import datetime
import pytz
from typing import Dict, List, Optional

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

# Inicialización del estado de sesión
if 'market_scanner' not in st.session_state:
    st.session_state.market_scanner = None
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None
if 'current_symbol' not in st.session_state:
    st.session_state.current_symbol = None
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None

def get_market_status() -> Dict:
    """
    Obtiene el estado actual del mercado.
    
    Returns:
        dict: Estado actual del mercado
    """
    ny_tz = pytz.timezone('America/New_York')
    now = datetime.now(ny_tz)
    
    analyzer = TradingAnalyzer()
    session = analyzer._get_market_session()
    
    return {
        "time": now.strftime("%H:%M:%S"),
        "session": session,
        "next_update": (st.session_state.last_scan_time + pd.Timedelta(minutes=5)).strftime("%H:%M:%S") 
            if st.session_state.last_scan_time else "NA"
    }

def display_technical_analysis(symbol: str, cached_data: Optional[Dict] = None) -> None:
    """
    Muestra análisis técnico detallado de un símbolo.
    
    Args:
        symbol: Símbolo a analizar
        cached_data: Datos cacheados del scanner si existen
    """
    try:
        with st.spinner("Analizando mercado..."):
            # Usar datos cacheados o realizar nuevo análisis
            if cached_data:
                trend = cached_data["trend_data"]
                strategies = cached_data["strategies"]
            else:
                analyzer = TradingAnalyzer()
                trend, _ = analyzer.analyze_trend(symbol)
                hourly_data = analyzer.get_market_data(symbol, period="5d", interval="1h")
                strategies = analyzer.identify_strategy(hourly_data, trend)
            
            # Mostrar análisis de tendencia
            st.subheader("🎯 Análisis Técnico")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Dirección",
                    trend["direction"],
                    delta="↑" if trend["direction"] == "ALCISTA" else "↓" if trend["direction"] == "BAJISTA" else "→"
                )
            with col2:
                st.metric("Fuerza", trend["strength"])
            with col3:
                st.metric("Sesgo", trend["bias"])
            
            st.info(trend["description"])
            
            # Métricas técnicas
            st.subheader("📊 Indicadores")
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
            
            # Estrategias identificadas
            if strategies:
                st.subheader("📈 Señales Activas")
                for strat in strategies:
                    with st.expander(f"{strat['type']} - {strat['name']} (Confianza: {strat['confidence']})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Descripción:**")
                            st.write(strat['description'])
                            st.write("**Condiciones:**")
                            for condition in strat['conditions']:
                                st.write(f"✓ {condition}")
                        with col2:
                            if 'levels' in strat:
                                st.write("**Niveles Operativos:**")
                                st.metric("Entry", f"${strat['levels']['entry']:.2f}")
                                st.metric("Stop", f"${strat['levels']['stop']:.2f}")
                                st.metric("Target", f"${strat['levels']['target']:.2f}")
                        
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
                **Sin Señales Activas**
                - Mercado sin setup válido
                - Mantener disciplina operativa
                - Esperar mejor oportunidad
                """)
    
    except Exception as e:
        logger.error(f"Error en análisis técnico: {str(e)}")
        st.error("Error procesando análisis técnico")

def run_market_scanner(selected_sectors: Optional[List[str]] = None) -> None:
    """
    Ejecuta scanner de mercado con filtros.
    
    Args:
        selected_sectors: Lista de sectores a analizar
    """
    try:
        if not st.session_state.market_scanner:
            st.session_state.market_scanner = MarketScanner(SYMBOLS)
        
        with st.spinner("Escaneando mercado..."):
            opportunities = st.session_state.market_scanner.scan_market(
                selected_sectors=selected_sectors
            )
            
            if not opportunities.empty:
                # Métricas del scan
                total_calls = len(opportunities[opportunities["Estrategia"] == "CALL"])
                total_puts = len(opportunities[opportunities["Estrategia"] == "PUT"])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Señales CALL", total_calls)
                with col2:
                    st.metric("Señales PUT", total_puts)
                with col3:
                    st.metric("Total Oportunidades", len(opportunities))
                
                # Mostrar oportunidades
                st.dataframe(
                    opportunities.style.apply(lambda x: [
                        "background-color: #c8e6c9" if x["Estrategia"] == "CALL" else
                        "background-color: #ffcdd2" if x["Estrategia"] == "PUT" else
                        "" for i in range(len(x))
                    ], axis=1),
                    use_container_width=True
                )
                
                # Actualizar timestamp
                st.session_state.last_scan_time = pd.Timestamp.now()
            else:
                st.warning("No se identificaron oportunidades que cumplan los criterios")
    
    except Exception as e:
        logger.error(f"Error en scanner: {str(e)}")
        st.error("Error ejecutando scanner de mercado")

def main():
    # Configuración de página
    st.set_page_config(
        page_title="InversorIA Mini Pro",
        page_icon="📊",
        layout="wide"
    )
    
    # Header
    st.title("📊 InversorIA Mini Pro")
    
    # Estado del mercado
    market_status = get_market_status()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hora NY", market_status["time"])
    with col2:
        st.metric("Sesión", market_status["session"])
    with col3:
        st.metric("Próx. Update", market_status["next_update"])
    
    # Navegación principal
    tab1, tab2 = st.tabs(["🔍 Análisis Individual", "📡 Scanner de Mercado"])
    
    with tab1:
        # Selector de símbolo
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Sector", list(SYMBOLS.keys()))
        with col2:
            symbol = st.selectbox("Activo", SYMBOLS[category])
        
        if symbol != st.session_state.current_symbol:
            st.session_state.current_symbol = symbol
            st.session_state.last_analysis = None
        
        # Obtener datos cacheados si existen
        cached_data = None
        if st.session_state.market_scanner:
            cached_data = st.session_state.market_scanner.get_cached_analysis(symbol)
        
        # Mostrar análisis
        display_technical_analysis(symbol, cached_data)
    
    with tab2:
        st.subheader("📡 Scanner de Mercado")
        
        # Controles del scanner
        col1, col2 = st.columns(2)
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
        
        selected_sectors = st.multiselect(
            "Filtrar por Sectores",
            list(SYMBOLS.keys()),
            default=None,
            help="Seleccione sectores específicos o deje vacío para analizar todos"
        )
        
        if st.button("🔄 Actualizar Scanner"):
            run_market_scanner(selected_sectors if selected_sectors else None)
    
    # Disclaimer
    st.markdown("---")
    st.caption("""
    **⚠️ Disclaimer:**
    Este sistema proporciona análisis técnico cuantitativo y requiere validación profesional.
    Trading implica riesgo sustancial de pérdida. Realizar due diligence exhaustivo.
    """)

if __name__ == "__main__":
    main()