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

# Inicialización del estado de la sesión
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
            return pd.Series(index=series.index)
        return series.rolling(window=window).mean()
    
    @staticmethod
    def calculate_rsi(series, window=14):
        """Calcula RSI con validación"""
        if len(series) < window:
            return pd.Series(index=series.index)
            
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
        """Analiza tendencia con alineación de series mejorada"""
        try:
            # Obtener datos diarios
            data = self.get_market_data(symbol, period="1y", interval="1d")
            
            # Asegurar que tenemos suficientes datos
            if len(data) < 200:
                raise MarketDataError("Datos insuficientes para análisis de tendencia")
            
            # Calcular indicadores sobre la serie de precios
            close_series = data['Close']
            data['SMA20'] = self.indicators.calculate_sma(close_series, 20)
            data['SMA50'] = self.indicators.calculate_sma(close_series, 50)
            data['SMA200'] = self.indicators.calculate_sma(close_series, 200)
            data['RSI'] = self.indicators.calculate_rsi(close_series)
            
            # Obtener últimos valores alineados
            latest = data.iloc[-1]
            
            # Análisis de tendencia
            trend = {
                "direction": "INDEFINIDA",
                "strength": "NEUTRAL",
                "bias": "NEUTRAL",
                "description": "",
                "metrics": {
                    "price": latest['Close'],
                    "sma20": latest['SMA20'],
                    "sma50": latest['SMA50'],
                    "sma200": latest['SMA200'],
                    "rsi": latest['RSI']
                }
            }
            
            # Determinar tendencia usando valores alineados
            price = float(latest['Close'])
            sma50 = float(latest['SMA50'])
            sma200 = float(latest['SMA200'])
            
            if not (np.isnan(price) or np.isnan(sma50) or np.isnan(sma200)):
                if price > sma200:
                    if price > sma50:
                        trend.update({
                            "direction": "ALCISTA",
                            "strength": "FUERTE",
                            "bias": "CALL",
                            "description": "Tendencia alcista fuerte confirmada por todas las medias móviles"
                        })
                    else:
                        trend.update({
                            "direction": "ALCISTA",
                            "strength": "MODERADA",
                            "bias": "CALL",
                            "description": "Tendencia alcista moderada sobre SMA200"
                        })
                else:
                    if price < sma50:
                        trend.update({
                            "direction": "BAJISTA",
                            "strength": "FUERTE",
                            "bias": "PUT",
                            "description": "Tendencia bajista fuerte confirmada por todas las medias móviles"
                        })
                    else:
                        trend.update({
                            "direction": "BAJISTA",
                            "strength": "MODERADA",
                            "bias": "PUT",
                            "description": "Tendencia bajista moderada bajo SMA200"
                        })
            
            return trend, data
            
        except Exception as e:
            logger.error(f"Error en análisis de tendencia: {str(e)}")
            raise MarketDataError(str(e))

    def identify_strategy(self, hourly_data, trend):
        """Identifica estrategias con validación mejorada"""
        try:
            # Calcular indicadores horarios con alineación
            close_series = hourly_data['Close']
            hourly_data['RSI'] = self.indicators.calculate_rsi(close_series)
            hourly_data['SMA40'] = self.indicators.calculate_sma(close_series, 40)
            
            # Obtener último valor alineado
            latest = hourly_data.iloc[-1]
            
            applicable_strategies = []
            
            # Validar tendencia y bias
            if trend["bias"] in ["CALL", "NEUTRAL"]:
                # Estrategia SMA40
                if latest['RSI'] < 30 and latest['Close'] > latest['SMA40']:
                    applicable_strategies.append({
                        "type": "CALL",
                        "name": self.strategies["CALL"]["SMA40"]["name"],
                        "description": self.strategies["CALL"]["SMA40"]["description"],
                        "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA",
                        "conditions": self.strategies["CALL"]["SMA40"]["conditions"]
                    })
                
                # Estrategia Caída Normal
                if len(hourly_data) >= 5:  # Asegurar suficientes datos
                    high_5d = hourly_data['High'].iloc[-5:].max()
                    price_change = (high_5d - latest['Close']) / latest['Close']
                    if 0.02 <= price_change <= 0.03 and latest['RSI'] < 40:
                        applicable_strategies.append({
                            "type": "CALL",
                            "name": self.strategies["CALL"]["NormalDrop"]["name"],
                            "description": self.strategies["CALL"]["NormalDrop"]["description"],
                            "confidence": "MEDIA",
                            "conditions": self.strategies["CALL"]["NormalDrop"]["conditions"]
                        })
            
            # PUT strategies
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
    
    # Universo de trading
    symbols = {
        "Índices": ["SPY", "QQQ", "DIA", "IWM"],
        "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN"],
        "Finanzas": ["JPM", "BAC", "GS", "MS"]
    }
    
    # Interfaz de selección
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Sector", list(symbols.keys()))
    with col2:
        symbol = st.selectbox("Activo", symbols[category])
    
    if symbol != st.session_state.current_symbol:
        st.session_state.current_symbol = symbol
        st.session_state.last_analysis = None
    
    analyzer = TradingAnalyzer()
    
    try:
        with st.spinner("Analizando mercado..."):
            # Análisis de tendencia
            trend, daily_data = analyzer.analyze_trend(symbol)
            
            # Mostrar análisis de tendencia
            st.subheader("🎯 Análisis de Tendencia Principal")
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
                distance_to_sma200 = ((trend['metrics']['price'] / trend['metrics']['sma200']) - 1) * 100
                st.metric("Dist. SMA200", f"{distance_to_sma200:.1f}%")
            
            # Análisis horario y estrategias
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
                st.warning("No se identificaron estrategias aplicables en este momento")
            
            # Disclaimer profesional
            st.markdown("---")
            st.caption("""
            **⚠️ Disclaimer:** Este análisis técnico es generado mediante algoritmos cuantitativos y requiere validación profesional.
            Las señales deben ser confirmadas con análisis adicional y gestión de riesgo apropiada.
            Trading implica riesgo sustancial de pérdida. Realizar due diligence exhaustivo.
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