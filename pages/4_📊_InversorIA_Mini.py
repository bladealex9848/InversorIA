import streamlit as st
from trading_analyzer import TradingAnalyzer, MarketDataError
import logging

# Verificación de autenticación
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.title("🔒 Acceso Restringido")
    st.warning("Por favor, inicie sesión desde la página principal del sistema.")
    st.stop()

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

# Inicialización del estado
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None
if 'current_symbol' not in st.session_state:
    st.session_state.current_symbol = None

def main():
    st.title("📊 InversorIA Mini")
    st.write("Sistema Profesional de Trading")
    
    # Interfaz de selección
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Sector", list(SYMBOLS.keys()))
    with col2:
        symbol = st.selectbox("Activo", SYMBOLS[category])
    
    if symbol != st.session_state.current_symbol:
        st.session_state.current_symbol = symbol
        st.session_state.last_analysis = None
    
    analyzer = TradingAnalyzer()
    
    try:
        with st.spinner("Analizando mercado..."):
            # Análisis de tendencia
            trend, daily_data = analyzer.analyze_trend(symbol)
            
            # Mostrar análisis de tendencia
            st.subheader("🎯 Análisis de Tendencia")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Dirección", trend["direction"])
            with col2:
                st.metric("Fuerza", trend["strength"])
            with col3:
                st.metric("Sesgo", trend["bias"])
            
            st.info(trend["description"])
            
            # Métricas técnicas
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
                for strat in strategies:
                    with st.expander(f"{strat['type']} - {strat['name']} (Confianza: {strat['confidence']})"):
                        st.write(f"""
                        **Descripción:**
                        {strat['description']}
                        
                        **Condiciones necesarias:**
                        """)
                        for condition in strat['conditions']:
                            st.write(f"✓ {condition}")
                        
                        if strat['confidence'] == "ALTA":
                            st.success("""
                            ⭐ Señal de trading confirmada
                            - Alta probabilidad de éxito
                            - Alineación con tendencia principal
                            - Risk/Reward favorable
                            
                            Gestión de Riesgo:
                            1. Stop Loss: 1-2 puntos bajo soporte
                            2. Take Profit: 2-3x el riesgo
                            3. Sizing: 2-3% del capital
                            """)
                        else:
                            st.warning("""
                            ⚠️ Señal requiere confirmación
                            - Validar niveles técnicos
                            - Confirmar con volumen
                            - Esperar alineación con tendencia
                            """)
                
                # Resumen operativo
                st.subheader("🎯 Resumen Operativo")
                best_strategy = [s for s in strategies if s['confidence'] == "ALTA"]
                
                if best_strategy:
                    st.success(f"""
                    **Recomendación Principal:** {best_strategy[0]['type']}
                    - Estrategia: {best_strategy[0]['name']}
                    - Tendencia: {trend['direction']} {trend['strength']}
                    - Confianza: ALTA
                    
                    Próximos Pasos:
                    1. Validar niveles de entrada
                    2. Definir zona de stop loss
                    3. Calcular ratio riesgo/beneficio
                    4. Determinar tamaño de posición
                    """)
                else:
                    st.info("""
                    **Recomendación:** Esperar mejores condiciones
                    - Señales requieren confirmación
                    - Mantener disciplina operativa
                    - Vigilar próximos niveles
                    """)
            else:
                st.warning("""
                **No hay estrategias aplicables**
                - Mercado sin señales claras
                - Preservar capital
                - Esperar mejor setup
                """)
            
            # Niveles clave
            st.subheader("📍 Niveles Técnicos")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Soportes/Resistencias:**")
                st.write(f"• SMA200: ${trend['metrics']['sma200']:.2f}")
                st.write(f"• SMA50: ${trend['metrics']['sma50']:.2f}")
                st.write(f"• SMA20: ${trend['metrics']['sma20']:.2f}")
            
            with col2:
                st.markdown("**Niveles RSI:**")
                st.write("• Sobrecompra: RSI > 70")
                st.write("• Neutral: RSI 30-70")
                st.write("• Sobreventa: RSI < 30")
            
            # Disclaimer profesional
            st.markdown("---")
            st.caption("""
            **⚠️ Disclaimer Profesional:**
            Este análisis técnico es generado por algoritmos cuantitativos y requiere validación profesional.
            Las señales técnicas requieren confirmación adicional y gestión de riesgo apropiada.
            Trading implica riesgo sustancial de pérdida.
            """)
            
    except MarketDataError as e:
        st.error(f"""
        Error en datos de mercado: {str(e)}
        
        Posibles soluciones:
        1. Verificar conectividad
        2. Validar símbolo seleccionado
        3. Intentar con otro timeframe
        4. Actualizar la página
        """)
        logger.error(f"MarketDataError: {str(e)}")
        
    except Exception as e:
        st.error(f"""
        Error inesperado: {str(e)}
        
        Por favor:
        1. Reportar al equipo técnico
        2. Proporcionar detalles del error
        3. Intentar nuevamente
        """)
        logger.error(f"Error inesperado: {str(e)}")
        st.stop()

if __name__ == "__main__":
    main()