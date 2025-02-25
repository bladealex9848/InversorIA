import streamlit as st
from trading_analyzer import TradingAnalyzer, MarketDataError
from market_scanner import MarketScanner
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import pytz
import time
import requests
import os
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración de logging con más detalles
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verificación de autenticación
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.title("🔒 Acceso Restringido")
    st.warning("Por favor, inicie sesión desde la página principal del sistema.")
    st.stop()

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

# Clase para implementar caché de datos
class DataCache:
    """Implementa caché de datos con invalidación por tiempo"""
    
    def __init__(self, expiry_minutes=15):
        self.cache = {}
        self.expiry_minutes = expiry_minutes
    
    def get(self, key):
        """Obtiene dato del caché si es válido"""
        if key in self.cache:
            timestamp, data = self.cache[key]
            now = datetime.now()
            if (now - timestamp).total_seconds() < (self.expiry_minutes * 60):
                return data
        return None
    
    def set(self, key, data):
        """Almacena dato en caché con timestamp"""
        self.cache[key] = (datetime.now(), data)
    
    def clear(self):
        """Limpia caché completo"""
        self.cache = {}

# Adaptador para fuentes de datos alternativas
class DataProvider:
    """Proveedor de datos con manejo de errores y fallbacks"""
    
    def __init__(self):
        # Intentar obtener Alpha Vantage API key
        try:
            self.alpha_vantage_key = st.secrets.get("alpha_vantage_api_key", 
                                                   os.environ.get("ALPHA_VANTAGE_API_KEY"))
        except Exception:
            self.alpha_vantage_key = None
            
        self.last_request_time = datetime.now()
        self.request_counter = 0
        self.max_requests_per_minute = 50  # Límite para evitar throttling
    
    def get_market_data(self, symbol, period="6mo", interval="1d"):
        """Obtiene datos de mercado con fallbacks"""
        # Control de tasa de solicitudes
        self._rate_limit()
        
        # Intento con TradingAnalyzer
        try:
            analyzer = TradingAnalyzer()
            data = analyzer.get_market_data(symbol, period=period, interval=interval)
            
            # Validar y corregir dimensiones de datos
            if data is not None and not data.empty:
                # Corregir dimensionalidad
                for col in ['Close', 'Open', 'High', 'Low']:
                    if col in data.columns:
                        if isinstance(data[col], pd.DataFrame) or (isinstance(data[col], np.ndarray) and len(data[col].shape) > 1):
                            # Convertir a serie unidimensional
                            data[col] = data[col].iloc[:, 0] if isinstance(data[col], pd.DataFrame) else data[col].flatten()
                return data
        except Exception as e:
            logger.warning(f"Error en TradingAnalyzer para {symbol}: {str(e)}")
        
        # Fallback a Alpha Vantage si está disponible
        if self.alpha_vantage_key:
            try:
                return self._get_alpha_vantage_data(symbol, interval)
            except Exception as e:
                logger.warning(f"Error en Alpha Vantage para {symbol}: {str(e)}")
        
        # Fallback final: datos sintéticos para la UI
        logger.warning(f"Generando datos sintéticos para {symbol}")
        return self._generate_synthetic_data(symbol)
    
    def _rate_limit(self):
        """Implementa limitación de tasa de solicitudes"""
        current_time = datetime.now()
        time_diff = (current_time - self.last_request_time).total_seconds()
        
        # Reiniciar contador cada minuto
        if time_diff > 60:
            self.request_counter = 0
            self.last_request_time = current_time
        
        # Incrementar contador
        self.request_counter += 1
        
        # Aplicar throttling si es necesario
        if self.request_counter > self.max_requests_per_minute:
            sleep_time = max(0.1, 60 - time_diff)
            logger.info(f"Rate limiting aplicado, esperando {sleep_time:.2f}s")
            time.sleep(sleep_time)
            self.request_counter = 0
            self.last_request_time = datetime.now()
        
        # Delay mínimo entre solicitudes
        elif time_diff < 0.2:  # Máximo 5 solicitudes por segundo
            time.sleep(0.2 - time_diff)
    
    def _get_alpha_vantage_data(self, symbol, interval):
        """Obtiene datos desde Alpha Vantage"""
        function = "TIME_SERIES_DAILY" if interval == "1d" else "TIME_SERIES_INTRADAY"
        interval_param = "&interval=60min" if interval != "1d" else ""
        
        url = f"https://www.alphavantage.co/query?function={function}{interval_param}&symbol={symbol}&apikey={self.alpha_vantage_key}&outputsize=compact"
        response = requests.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Error en Alpha Vantage API: {response.status_code}")
        
        data = response.json()
        
        # Identificar la clave de series temporales
        time_series_key = next((k for k in data.keys() if "Time Series" in k), None)
        if not time_series_key or not data.get(time_series_key):
            raise Exception("Respuesta de Alpha Vantage sin datos de series temporales")
        
        # Convertir a DataFrame
        time_series = data[time_series_key]
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Renombrar columnas para compatibilidad
        df = df.rename(columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
            "5. volume": "Volume"
        })
        
        # Convertir a tipos numéricos
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = pd.to_numeric(df[col])
        
        # Establecer índice de tiempo y ordenar
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        return df
    
    def _generate_synthetic_data(self, symbol):
        """Genera datos sintéticos para fallback"""
        # Crear datos determinísticos basados en el símbolo
        np.random.seed(hash(symbol) % 10000)
        
        # Fechas para 100 días
        end_date = datetime.now()
        start_date = end_date - pd.Timedelta(days=100)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Precio base según iniciales del símbolo
        base_price = 100 + sum(ord(c) for c in symbol) % 400
        
        # Generar precios con tendencia y volatilidad realista
        prices = []
        price = base_price
        for _ in range(len(dates)):
            change = np.random.normal(0, 1) * 0.01  # Cambio diario aleatorio
            price *= (1 + change)
            prices.append(price)
        
        # Crear DataFrame con formato compatible
        df = pd.DataFrame({
            'Open': prices,
            'High': [p * (1 + abs(np.random.normal(0, 1) * 0.005)) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 1) * 0.005)) for p in prices],
            'Close': prices,
            'Volume': [int(np.random.normal(1000000, 200000)) for _ in prices]
        }, index=dates)
        
        # Marcar como sintético
        df.attrs['synthetic'] = True
        
        return df

# Inicialización del estado de sesión
if 'market_scanner' not in st.session_state:
    st.session_state.market_scanner = None
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None
if 'current_symbol' not in st.session_state:
    st.session_state.current_symbol = None
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = DataCache()
if 'data_provider' not in st.session_state:
    st.session_state.data_provider = DataProvider()

def get_market_status() -> Dict:
    """
    Obtiene el estado del mercado con manejo de errores.
    """
    try:
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(ny_tz)
        
        # Obtener sesión con manejo de fallos
        try:
            analyzer = TradingAnalyzer()
            session = analyzer._get_market_session()
        except Exception as e:
            logger.warning(f"Error obteniendo sesión: {str(e)}")
            # Fallback: calcular sesión por hora
            hour = now.hour
            if 9 <= hour < 16:
                session = "REGULAR"
            elif 4 <= hour < 9:
                session = "PRE-MARKET"
            elif 16 <= hour < 20:
                session = "AFTER-HOURS"
            else:
                session = "CLOSED"
        
        return {
            "time": now.strftime("%H:%M:%S"),
            "session": session,
            "next_update": (st.session_state.last_scan_time + pd.Timedelta(minutes=5)).strftime("%H:%M:%S") 
                if st.session_state.last_scan_time else "NA"
        }
    except Exception as e:
        logger.error(f"Error en market_status: {str(e)}")
        return {"time": datetime.now().strftime("%H:%M:%S"), "session": "ERROR", "next_update": "NA"}

def display_technical_analysis(symbol: str, cached_data: Optional[Dict] = None) -> None:
    """
    Muestra análisis técnico con manejo robusto de errores.
    """
    try:
        with st.spinner("Analizando mercado..."):
            # Usar caché o realizar análisis nuevo
            if cached_data:
                trend = cached_data["trend_data"]
                strategies = cached_data["strategies"]
                logger.info(f"Usando datos en caché para {symbol}")
            else:
                try:
                    # Obtener datos del mercado con el proveedor mejorado
                    daily_data = st.session_state.data_provider.get_market_data(symbol, period="6mo", interval="1d")
                    
                    # Validar datos mínimos
                    if daily_data is None or daily_data.empty or len(daily_data) < 20:
                        raise MarketDataError(f"Datos insuficientes para {symbol}")
                    
                    # Ejecutar análisis de tendencia con manejo de errores
                    try:
                        analyzer = TradingAnalyzer()
                        # Proporcionar datos ya validados
                        trend, _ = analyzer.analyze_trend(symbol, data=daily_data)
                    except Exception as trend_err:
                        logger.error(f"Error en analyze_trend: {str(trend_err)}")
                        # Construir tendencia básica si falla
                        trend = {
                            "direction": "NEUTRAL",
                            "strength": "MEDIA",
                            "bias": "NEUTRAL",
                            "description": "Análisis limitado debido a errores en el procesamiento de datos.",
                            "metrics": {
                                "price": daily_data['Close'].iloc[-1] if not daily_data.empty else 0,
                                "sma200": daily_data['Close'].rolling(window=200, min_periods=20).mean().iloc[-1] 
                                          if len(daily_data) >= 20 else 0,
                                "rsi": 50.0  # Neutral
                            }
                        }
                    
                    # Identificar estrategias con manejo de errores
                    try:
                        hourly_data = st.session_state.data_provider.get_market_data(
                            symbol, period="5d", interval="1h")
                        
                        # Corregir dimensionalidad antes de procesar
                        for col in ['Close', 'Open', 'High', 'Low']:
                            if col in hourly_data.columns and isinstance(hourly_data[col], np.ndarray) and len(hourly_data[col].shape) > 1:
                                hourly_data[col] = hourly_data[col].flatten()
                        
                        strategies = analyzer.identify_strategy(hourly_data, trend)
                    except Exception as strat_err:
                        logger.error(f"Error en identify_strategy: {str(strat_err)}")
                        strategies = []
                
                except Exception as e:
                    logger.error(f"Error en análisis principal: {str(e)}")
                    # Fallback para UI
                    trend = {
                        "direction": "ERROR",
                        "strength": "N/A",
                        "bias": "N/A",
                        "description": f"Error analizando {symbol}. Intente más tarde o seleccione otro activo.",
                        "metrics": {"price": 0.0, "sma200": 0.0, "rsi": 0.0}
                    }
                    strategies = []
            
            # Mostrar análisis de tendencia en UI
            st.subheader("🎯 Análisis Técnico")
            col1, col2, col3 = st.columns(3)
            with col1:
                direction_arrow = "↑" if trend["direction"] == "ALCISTA" else "↓" if trend["direction"] == "BAJISTA" else "→"
                st.metric("Dirección", trend["direction"], delta=direction_arrow)
            with col2:
                st.metric("Fuerza", trend["strength"])
            with col3:
                st.metric("Sesgo", trend["bias"])
            
            st.info(trend["description"])
            
            # Métricas con manejo seguro de errores
            st.subheader("📊 Indicadores")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                price_val = trend['metrics'].get('price', 0)
                st.metric("Precio", f"${price_val:.2f}" if isinstance(price_val, (int, float)) else "N/A")
            with col2:
                sma_val = trend['metrics'].get('sma200', 0)
                st.metric("SMA200", f"${sma_val:.2f}" if isinstance(sma_val, (int, float)) else "N/A")
            with col3:
                rsi_val = trend['metrics'].get('rsi', 0)
                st.metric("RSI", f"{rsi_val:.1f}" if isinstance(rsi_val, (int, float)) else "N/A")
            with col4:
                try:
                    if price_val > 0 and sma_val > 0:
                        dist = ((price_val / sma_val) - 1) * 100
                        dist_val = f"{dist:.1f}%" if not pd.isna(dist) and abs(dist) < 1000 else "N/A"
                    else:
                        dist_val = "N/A"
                except (ZeroDivisionError, TypeError, ValueError):
                    dist_val = "N/A"
                st.metric("Dist. SMA200", dist_val)
            
            # Mostrar estrategias
            if strategies:
                st.subheader("📈 Señales Activas")
                for strat in strategies:
                    with st.expander(f"{strat.get('type', 'N/A')} - {strat.get('name', 'N/A')} (Confianza: {strat.get('confidence', 'N/A')})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Descripción:**")
                            st.write(strat.get('description', 'No disponible'))
                            st.write("**Condiciones:**")
                            for condition in strat.get('conditions', ['No disponible']):
                                st.write(f"✓ {condition}")
                        with col2:
                            if 'levels' in strat:
                                st.write("**Niveles Operativos:**")
                                entry_val = strat['levels'].get('entry', 0)
                                stop_val = strat['levels'].get('stop', 0)
                                target_val = strat['levels'].get('target', 0)
                                st.metric("Entry", f"${entry_val:.2f}" if isinstance(entry_val, (int, float)) else "N/A")
                                st.metric("Stop", f"${stop_val:.2f}" if isinstance(stop_val, (int, float)) else "N/A")
                                st.metric("Target", f"${target_val:.2f}" if isinstance(target_val, (int, float)) else "N/A")
                
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
        logger.error(f"Error crítico: {str(e)}", exc_info=True)
        st.error("Error procesando análisis técnico")
        with st.expander("Detalles del error (Debug)"):
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())

def run_market_scanner(selected_sectors: Optional[List[str]] = None) -> None:
    """
    Ejecuta scanner de mercado con mejor gestión de errores y limitación de conexiones.
    """
    try:
        # Inicializar scanner mejorado
        if not st.session_state.market_scanner:
            st.session_state.market_scanner = MarketScanner(SYMBOLS)
        
        with st.spinner("Escaneando mercado..."):
            try:
                # Limitar símbolos según selección
                symbols_to_scan = {}
                if selected_sectors:
                    for sector in selected_sectors:
                        if sector in SYMBOLS:
                            symbols_to_scan[sector] = SYMBOLS[sector]
                else:
                    symbols_to_scan = SYMBOLS
                
                # Actualizar scanner con símbolos filtrados
                st.session_state.market_scanner.symbols = symbols_to_scan
                
                # Configurar opciones para evitar conexiones excesivas
                scan_options = {
                    "max_workers": 5,       # Limitar workers en paralelo
                    "connection_timeout": 5, # Timeout en segundos
                    "max_retries": 2,       # Intentos por símbolo
                    "use_cache": True       # Usar caché cuando sea posible
                }
                
                # Ejecutar escaneo con opciones seguras
                opportunities = st.session_state.market_scanner.scan_market(
                    selected_sectors=selected_sectors,
                    options=scan_options
                )
                
                # Procesar resultados
                if not opportunities.empty:
                    # Mostrar métricas del escaneo
                    total_calls = len(opportunities[opportunities["Estrategia"] == "CALL"])
                    total_puts = len(opportunities[opportunities["Estrategia"] == "PUT"])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Señales CALL", total_calls)
                    with col2:
                        st.metric("Señales PUT", total_puts)
                    with col3:
                        st.metric("Total Oportunidades", len(opportunities))
                    
                    # Preparar datos para mostrar
                    display_columns = [
                        "Symbol", "Sector", "Tendencia", "Fuerza", "Precio", 
                        "RSI", "Estrategia", "Setup", "Confianza", 
                        "Entry", "Stop", "Target", "R/R", "Timestamp"
                    ]
                    
                    # Asegurar que todas las columnas existen
                    for col in display_columns:
                        if col not in opportunities.columns:
                            opportunities[col] = "N/A"
                    
                    display_df = opportunities[display_columns].copy()
                    
                    # Formatear para la visualización
                    display_df = display_df.rename(columns={
                        "Symbol": "Símbolo",
                        "Entry": "Entrada",
                        "Stop": "Stop Loss",
                        "Target": "Objetivo",
                        "Timestamp": "Hora"
                    })
                    
                    # Mostrar tabla de oportunidades
                    st.dataframe(
                        display_df.style
                        .format({
                            "Precio": "${:.2f}",
                            "RSI": "{:.1f}",
                            "Entrada": "${:.2f}",
                            "Stop Loss": "${:.2f}",
                            "Objetivo": "${:.2f}"
                        })
                        .apply(lambda x: [
                            "background-color: #c8e6c9" if x["Estrategia"] == "CALL" else
                            "background-color: #ffcdd2" if x["Estrategia"] == "PUT" else
                            "" for i in range(len(x))
                        ], axis=1),
                        use_container_width=True
                    )
                    
                    # Actualizar timestamp
                    st.session_state.last_scan_time = pd.Timestamp.now()
                    
                    # Análisis por sector
                    if selected_sectors:
                        st.subheader("📊 Análisis por Sector")
                        for sector in selected_sectors:
                            sector_opps = display_df[display_df["Sector"] == sector]
                            if not sector_opps.empty:
                                with st.expander(f"{sector} ({len(sector_opps)} señales)"):
                                    st.write(f"""
                                    **Señales Identificadas:**
                                    - CALLS: {len(sector_opps[sector_opps['Estrategia'] == 'CALL'])}
                                    - PUTS: {len(sector_opps[sector_opps['Estrategia'] == 'PUT'])}
                                    - Alta Confianza: {len(sector_opps[sector_opps['Confianza'] == 'ALTA'])}
                                    """)
                else:
                    st.warning("No se identificaron oportunidades que cumplan los criterios")
            
            except Exception as e:
                logger.error(f"Error en scanner: {str(e)}", exc_info=True)
                st.error("Error en scanner de mercado")
                
                # Detalles técnicos para debug
                with st.expander("Detalles técnicos"):
                    st.code(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Error crítico en scanner: {str(e)}", exc_info=True)
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
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Actualizar Scanner"):
                run_market_scanner(selected_sectors if selected_sectors else None)
        with col2:
            if st.button("🗑️ Limpiar Caché"):
                st.session_state.data_cache.clear()
                st.success("Caché de datos limpiado")
                time.sleep(1)
                st.experimental_rerun()
    
    # Disclaimer
    st.markdown("---")
    st.caption("""
    **⚠️ Disclaimer:**
    Este sistema proporciona análisis técnico cuantitativo y requiere validación profesional.
    Trading implica riesgo sustancial de pérdida. Realizar due diligence exhaustivo.
    """)

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception as e:
        logger.error(f"Error fatal en aplicación: {str(e)}", exc_info=True)
        st.error("Error crítico en la aplicación. Por favor, contacte al administrador.")
        with st.expander("Detalles técnicos"):
            st.code(traceback.format_exc())