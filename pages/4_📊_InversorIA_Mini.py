import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

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

class MarketDataError(Exception):
    """Excepción personalizada para errores de datos de mercado"""
    pass

class TechnicalIndicators:
    @staticmethod
    def calculate_sma(series, window):
        """Calcula SMA con validación"""
        if len(series) < window:
            return pd.Series(np.nan, index=series.index)
        return series.rolling(window=window).mean()
    
    @staticmethod
    def calculate_rsi(series, window=14):
        """Calcula RSI con validación"""
        if len(series) < window:
            return pd.Series(np.nan, index=series.index)
            
        delta = series.diff()
        gain = delta.copy()
        loss = delta.copy()
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)
        
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class TradingAnalyzer:
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.strategies = {
            "CALL": {
                "SMA40": {
                    "name": "Promedio Móvil de 40 en Hora",
                    "description": "Comprar CALL cuando el precio, tras caída, toca SMA40 y rompe línea bajista",
                    "conditions": ["SMA40 actuando como soporte", "RSI < 30", "Ruptura de línea bajista"]
                },
                "NormalDrop": {
                    "name": "Caída Normal (2-3 puntos)",
                    "description": "Comprar CALL tras caída moderada y ruptura de línea bajista",
                    "conditions": ["Caída de 2-3 puntos", "Volumen creciente", "RSI < 40"]
                }
            },
            "PUT": {
                "FirstRedCandle": {
                    "name": "Primera Vela Roja de Apertura",
                    "description": "Comprar PUT en primera vela roja de apertura",
                    "conditions": ["Primera vela roja del día", "RSI > 70", "Cerca de resistencia"]
                }
            }
        }

    def get_market_data(self, symbol, period="5d", interval="1h"):
        """Obtiene y valida datos de mercado"""
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if data.empty:
                raise MarketDataError(f"No se obtuvieron datos para {symbol}")
            return data
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            raise MarketDataError(str(e))

    def analyze_trend(self, symbol):
        """Analiza tendencia con manejo mejorado de Series"""
        try:
            data = self.get_market_data(symbol, period="1y", interval="1d")
            
            if len(data) < 200:
                raise MarketDataError("Datos insuficientes para análisis")
            
            # Calcular indicadores
            close_series = data['Close']
            data['SMA20'] = self.indicators.calculate_sma(close_series, 20)
            data['SMA50'] = self.indicators.calculate_sma(close_series, 50)
            data['SMA200'] = self.indicators.calculate_sma(close_series, 200)
            data['RSI'] = self.indicators.calculate_rsi(close_series)
            
            # Obtener últimos valores correctamente
            latest = data.iloc[-1]
            price = latest['Close']
            sma50 = latest['SMA50']
            sma200 = latest['SMA200']
            
            # Inicializar tendencia
            trend = {
                "direction": "INDEFINIDA",
                "strength": "NEUTRAL",
                "bias": "NEUTRAL",
                "description": "",
                "metrics": {
                    "price": float(price),
                    "sma20": float(latest['SMA20']),
                    "sma50": float(sma50),
                    "sma200": float(sma200),
                    "rsi": float(latest['RSI'])
                }
            }
            
            # Análisis de tendencia con valores numéricos
            if not np.isnan([price, sma50, sma200]).any():
                if price > sma200:
                    if price > sma50:
                        trend.update({
                            "direction": "ALCISTA",
                            "strength": "FUERTE",
                            "bias": "CALL",
                            "description": "Tendencia alcista fuerte confirmada"
                        })
                    else:
                        trend.update({
                            "direction": "ALCISTA",
                            "strength": "MODERADA",
                            "bias": "CALL",
                            "description": "Tendencia alcista moderada"
                        })
                else:
                    if price < sma50:
                        trend.update({
                            "direction": "BAJISTA",
                            "strength": "FUERTE",
                            "bias": "PUT",
                            "description": "Tendencia bajista fuerte confirmada"
                        })
                    else:
                        trend.update({
                            "direction": "BAJISTA",
                            "strength": "MODERADA",
                            "bias": "PUT",
                            "description": "Tendencia bajista moderada"
                        })
            
            return trend, data
            
        except Exception as e:
            logger.error(f"Error en análisis de tendencia: {str(e)}")
            raise MarketDataError(str(e))

    def identify_strategy(self, hourly_data, trend):
        """Identifica estrategias aplicables"""
        try:
            close_series = hourly_data['Close']
            hourly_data['RSI'] = self.indicators.calculate_rsi(close_series)
            hourly_data['SMA40'] = self.indicators.calculate_sma(close_series, 40)
            
            latest = hourly_data.iloc[-1]
            applicable_strategies = []
            
            # Validar datos
            if np.isnan([latest['RSI'], latest['SMA40'], latest['Close']]).any():
                return []
            
            # Estrategias CALL
            if trend["bias"] in ["CALL", "NEUTRAL"]:
                if latest['RSI'] < 30 and latest['Close'] > latest['SMA40']:
                    applicable_strategies.append({
                        "type": "CALL",
                        "name": self.strategies["CALL"]["SMA40"]["name"],
                        "description": self.strategies["CALL"]["SMA40"]["description"],
                        "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA",
                        "conditions": self.strategies["CALL"]["SMA40"]["conditions"]
                    })
                
                if len(hourly_data) >= 5:
                    price_change = (hourly_data['High'].iloc[-5:].max() - latest['Close']) / latest['Close']
                    if 0.02 <= price_change <= 0.03 and latest['RSI'] < 40:
                        applicable_strategies.append({
                            "type": "CALL",
                            "name": self.strategies["CALL"]["NormalDrop"]["name"],
                            "description": self.strategies["CALL"]["NormalDrop"]["description"],
                            "confidence": "MEDIA",
                            "conditions": self.strategies["CALL"]["NormalDrop"]["conditions"]
                        })
            
            # Estrategias PUT
            if trend["bias"] in ["PUT", "NEUTRAL"]:
                if latest['RSI'] > 70:
                    applicable_strategies.append({
                        "type": "PUT",
                        "name": self.strategies["PUT"]["FirstRedCandle"]["name"],
                        "description": self.strategies["PUT"]["FirstRedCandle"]["description"],
                        "confidence": "ALTA" if trend["direction"] == "BAJISTA" else "MEDIA",
                        "conditions": self.strategies["PUT"]["FirstRedCandle"]["conditions"]
                    })
            
            return applicable_strategies
            
        except Exception as e:
            logger.error(f"Error identificando estrategias: {str(e)}")
            return []

def main():
    st.title("📊 InversorIA Mini")
    st.write("Sistema Profesional de Análisis Técnico")
    
    # Interfaz de selección
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Sector", list(SYMBOLS.keys()))
    with col2:
        symbol = st.selectbox("Activo", SYMBOLS[category])
    
    analyzer = TradingAnalyzer()
    
    try:
        with st.spinner("Analizando mercado..."):
            trend, daily_data = analyzer.analyze_trend(symbol)
            
            st.subheader("🎯 Análisis de Tendencia")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Dirección", trend["direction"])
            with col2:
                st.metric("Fuerza", trend["strength"])
            with col3:
                st.metric("Sesgo", trend["bias"])
            
            st.info(trend["description"])
            
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
            
            hourly_data = analyzer.get_market_data(symbol, period="5d", interval="1h")
            strategies = analyzer.identify_strategy(hourly_data, trend)
            
            if strategies:
                st.subheader("📈 Estrategias Activas")
                for strat in strategies:
                    with st.expander(f"{strat['type']} - {strat['name']} (Confianza: {strat['confidence']})"):
                        st.write(f"**Descripción:** {strat['description']}")
                        st.write("**Condiciones necesarias:**")
                        for condition in strat['conditions']:
                            st.write(f"✓ {condition}")
                        
                        if strat['confidence'] == "ALTA":
                            st.success("⭐ Estrategia alineada con tendencia principal")
                        else:
                            st.warning("⚠️ Validar señales adicionales")
            else:
                st.warning("No se identificaron estrategias aplicables")
            
            st.markdown("---")
            st.caption("""
            **⚠️ Disclaimer:** Este análisis es generado mediante algoritmos cuantitativos y requiere validación profesional.
            Las señales técnicas requieren confirmación adicional. Trading implica riesgo sustancial de pérdida.
            """)
            
    except MarketDataError as e:
        st.error(f"Error de datos: {str(e)}")
        logger.error(f"MarketDataError: {str(e)}")
        
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        logger.error(f"Error inesperado: {str(e)}")
        st.stop()

if __name__ == "__main__":
    main()