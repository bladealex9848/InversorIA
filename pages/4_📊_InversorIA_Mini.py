import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from datetime import datetime, timedelta
import logging

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

# Inicialización del estado de la sesión
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None
if 'current_symbol' not in st.session_state:
    st.session_state.current_symbol = None

class MarketDataError(Exception):
    """Excepción personalizada para errores de datos de mercado"""
    pass

class TradingAnalyzer:
    def __init__(self):
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

    def calculate_sma(self, data, window):
        """Calcula SMA manualmente para evitar problemas de dimensionalidad"""
        return data['Close'].rolling(window=window).mean()

    def calculate_rsi(self, data, window=14):
        """Calcula RSI manualmente"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def get_market_data(self, symbol, period="5d", interval="1h"):
        """Obtiene datos de mercado con validación"""
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if data.empty:
                raise MarketDataError(f"No se obtuvieron datos para {symbol}")
            return data
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            raise MarketDataError(str(e))

    def analyze_trend(self, symbol):
        """Analiza tendencia con cálculos manuales optimizados"""
        try:
            # Obtener datos diarios
            daily_data = self.get_market_data(symbol, period="1y", interval="1d")
            
            # Calcular indicadores manualmente
            daily_data['SMA20'] = self.calculate_sma(daily_data, 20)
            daily_data['SMA50'] = self.calculate_sma(daily_data, 50)
            daily_data['SMA200'] = self.calculate_sma(daily_data, 200)
            daily_data['RSI'] = self.calculate_rsi(daily_data)
            
            # Obtener últimos valores
            current = daily_data.iloc[-1]
            
            # Determinar tendencia
            trend = {
                "direction": "INDEFINIDA",
                "strength": "NEUTRAL",
                "bias": "NEUTRAL",
                "description": ""
            }
            
            # Análisis de tendencia
            if current['Close'] > current['SMA200']:
                if current['Close'] > current['SMA50']:
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
                if current['Close'] < current['SMA50']:
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
                    
            # Añadir métricas
            trend["metrics"] = {
                "price": current['Close'],
                "sma20": current['SMA20'],
                "sma50": current['SMA50'],
                "sma200": current['SMA200'],
                "rsi": current['RSI']
            }
            
            return trend, daily_data
            
        except Exception as e:
            logger.error(f"Error en análisis de tendencia: {str(e)}")
            raise MarketDataError(str(e))

    def identify_strategy(self, hourly_data, trend):
        """Identifica estrategias aplicables"""
        try:
            # Calcular indicadores horarios
            hourly_data['RSI'] = self.calculate_rsi(hourly_data)
            hourly_data['SMA40'] = self.calculate_sma(hourly_data, 40)
            
            current = hourly_data.iloc[-1]
            applicable_strategies = []
            
            # Evaluación de estrategias según tendencia
            if trend["bias"] in ["CALL", "NEUTRAL"]:
                # Estrategia SMA40
                if current['RSI'] < 30 and current['Close'] > current['SMA40']:
                    applicable_strategies.append({
                        "type": "CALL",
                        "name": self.strategies["CALL"]["SMA40"]["name"],
                        "description": self.strategies["CALL"]["SMA40"]["description"],
                        "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA",
                        "conditions": self.strategies["CALL"]["SMA40"]["conditions"]
                    })
                
                # Estrategia Caída Normal
                price_change = (hourly_data['High'].max() - current['Close']) / current['Close']
                if 0.02 <= price_change <= 0.03 and current['RSI'] < 40:
                    applicable_strategies.append({
                        "type": "CALL",
                        "name": self.strategies["CALL"]["NormalDrop"]["name"],
                        "description": self.strategies["CALL"]["NormalDrop"]["description"],
                        "confidence": "MEDIA",
                        "conditions": self.strategies["CALL"]["NormalDrop"]["conditions"]
                    })
            
            # PUT strategies
            if trend["bias"] in ["PUT", "NEUTRAL"]:
                if current['RSI'] > 70:
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
            
            # Análisis horario
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
            **⚠️ Disclaimer:** Este análisis es generado mediante algoritmos cuantitativos y requiere validación profesional.
            Las señales técnicas deben ser confirmadas con análisis adicional y gestión de riesgo apropiada.
            Las operaciones en mercados financieros conllevan riesgo de pérdida.
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