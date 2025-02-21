import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
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
                },
                "StrongDrop": {
                    "name": "Caída Fuerte (5-6 puntos)",
                    "description": "Comprar CALL tras caída fuerte cerca de soporte mayor",
                    "conditions": ["Caída de 5-6 puntos", "Cerca de SMA200 diario", "RSI < 30"]
                }
            },
            "PUT": {
                "FirstRedCandle": {
                    "name": "Primera Vela Roja de Apertura",
                    "description": "Comprar PUT en primera vela roja de apertura",
                    "conditions": ["Primera vela roja del día", "RSI > 70", "Cerca de resistencia"]
                },
                "GapBreak": {
                    "name": "Ruptura del Piso del Gap",
                    "description": "Comprar PUT en ruptura de piso de gap",
                    "conditions": ["Gap identificado", "Ruptura con volumen", "MACD cruce bajista"]
                }
            }
        }

    def validate_data(self, data):
        """Valida la integridad de los datos"""
        if data is None or data.empty:
            return False
        if not all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
            return False
        return True

    def get_market_data(self, symbol, period="5d", interval="1h"):
        """Obtiene datos de mercado con validación mejorada"""
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if not self.validate_data(data):
                raise MarketDataError(f"Datos inválidos para {symbol}")
            return data
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            raise MarketDataError(f"Error en descarga de datos: {str(e)}")

    def calculate_indicators(self, data):
        """Calcula indicadores técnicos con manejo de errores mejorado"""
        try:
            results = data.copy()
            
            # Convertir Close a serie unidimensional
            close_series = pd.Series(results['Close'].values, index=results.index)
            
            # Calcular indicadores
            results['SMA20'] = SMAIndicator(close_series, window=20).sma_indicator()
            results['SMA50'] = SMAIndicator(close_series, window=50).sma_indicator()
            results['SMA200'] = SMAIndicator(close_series, window=200).sma_indicator()
            results['RSI'] = RSIIndicator(close_series).rsi()
            
            macd = MACD(close_series)
            results['MACD'] = macd.macd()
            results['MACD_Signal'] = macd.macd_signal()
            
            return results
        except Exception as e:
            logger.error(f"Error calculando indicadores: {str(e)}")
            raise MarketDataError(f"Error en cálculo de indicadores: {str(e)}")

    def analyze_trend(self, symbol):
        """Analiza tendencia en múltiples timeframes"""
        try:
            # Obtener datos diarios
            daily_data = self.get_market_data(symbol, period="1y", interval="1d")
            
            # Calcular indicadores
            analysis = self.calculate_indicators(daily_data)
            
            # Obtener últimos valores
            current_price = analysis['Close'].iloc[-1]
            sma20 = analysis['SMA20'].iloc[-1]
            sma50 = analysis['SMA50'].iloc[-1]
            sma200 = analysis['SMA200'].iloc[-1]
            rsi = analysis['RSI'].iloc[-1]
            
            # Determinar tendencia
            trend = {
                "direction": "INDEFINIDA",
                "strength": "NEUTRAL",
                "bias": "NEUTRAL",
                "description": ""
            }
            
            # Análisis de tendencia
            if current_price > sma200:
                if current_price > sma50 and sma50 > sma200:
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
            elif current_price < sma200:
                if current_price < sma50 and sma50 < sma200:
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
                    
            # Añadir métricas actuales
            trend["metrics"] = {
                "price": current_price,
                "sma20": sma20,
                "sma50": sma50,
                "sma200": sma200,
                "rsi": rsi
            }
            
            return trend, analysis
            
        except Exception as e:
            logger.error(f"Error en análisis de tendencia: {str(e)}")
            raise MarketDataError(f"Error analizando tendencia: {str(e)}")

    def identify_strategy(self, hourly_data, trend):
        """Identifica estrategias aplicables según condiciones actuales"""
        try:
            # Calcular indicadores horarios
            analysis = self.calculate_indicators(hourly_data)
            
            current_price = analysis['Close'].iloc[-1]
            current_rsi = analysis['RSI'].iloc[-1]
            current_sma20 = analysis['SMA20'].iloc[-1]
            
            applicable_strategies = []
            
            # Evaluación de estrategias según tendencia
            if trend["bias"] in ["CALL", "NEUTRAL"]:
                # Estrategia SMA40
                if current_rsi < 30 and current_price > current_sma20:
                    applicable_strategies.append({
                        "type": "CALL",
                        "name": self.strategies["CALL"]["SMA40"]["name"],
                        "description": self.strategies["CALL"]["SMA40"]["description"],
                        "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA",
                        "conditions": self.strategies["CALL"]["SMA40"]["conditions"]
                    })
                
                # Estrategia Caída Normal
                price_change = (hourly_data['High'].max() - current_price) / current_price
                if 0.02 <= price_change <= 0.03 and current_rsi < 40:
                    applicable_strategies.append({
                        "type": "CALL",
                        "name": self.strategies["CALL"]["NormalDrop"]["name"],
                        "description": self.strategies["CALL"]["NormalDrop"]["description"],
                        "confidence": "MEDIA",
                        "conditions": self.strategies["CALL"]["NormalDrop"]["conditions"]
                    })
            
            # PUT strategies
            if trend["bias"] in ["PUT", "NEUTRAL"]:
                if current_rsi > 70:
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