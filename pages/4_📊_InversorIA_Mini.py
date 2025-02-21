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

    def get_market_data(self, symbol, period):
        """Obtiene datos de mercado con manejo de errores mejorado"""
        try:
            data = yf.download(symbol, period=period, interval="1h")
            if data.empty:
                raise MarketDataError("No se obtuvieron datos")
            
            if len(data) < 20:  # Mínimo para cálculos técnicos
                raise MarketDataError("Datos insuficientes para análisis")
                
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            raise MarketDataError(f"Error en descarga de datos: {str(e)}")

    def analyze_trend(self, symbol):
        """Analiza tendencia en múltiples timeframes"""
        try:
            # Datos diarios para tendencia macro
            daily_data = yf.download(symbol, period="1y", interval="1d")
            if daily_data.empty:
                raise MarketDataError("No se obtuvieron datos diarios")
            
            # Calcular SMAs
            daily_data['SMA50'] = SMAIndicator(daily_data['Close'], window=50).sma_indicator()
            daily_data['SMA200'] = SMAIndicator(daily_data['Close'], window=200).sma_indicator()
            
            # Precios actuales
            current_price = daily_data['Close'].iloc[-1]
            sma50 = daily_data['SMA50'].iloc[-1]
            sma200 = daily_data['SMA200'].iloc[-1]
            
            # Determinar tendencia
            if current_price > sma200 and sma50 > sma200:
                trend = {
                    "direction": "ALCISTA",
                    "strength": "FUERTE" if current_price > sma50 else "MODERADA",
                    "description": "Tendencia alcista confirmada por SMA200 y SMA50",
                    "strategy_bias": "CALL"
                }
            elif current_price < sma200 and sma50 < sma200:
                trend = {
                    "direction": "BAJISTA",
                    "strength": "FUERTE" if current_price < sma50 else "MODERADA",
                    "description": "Tendencia bajista confirmada por SMA200 y SMA50",
                    "strategy_bias": "PUT"
                }
            else:
                trend = {
                    "direction": "LATERAL",
                    "strength": "INDEFINIDA",
                    "description": "Mercado en rango, sin tendencia clara",
                    "strategy_bias": "NEUTRAL"
                }
            
            return trend, daily_data
            
        except Exception as e:
            logger.error(f"Error en análisis de tendencia: {str(e)}")
            raise MarketDataError(f"Error analizando tendencia: {str(e)}")

    def identify_strategy(self, hourly_data, trend):
        """Identifica estrategias aplicables según condiciones actuales"""
        try:
            # Calcular indicadores horarios
            hourly_data['RSI'] = RSIIndicator(hourly_data['Close']).rsi()
            hourly_data['SMA40'] = SMAIndicator(hourly_data['Close'], window=40).sma_indicator()
            macd = MACD(hourly_data['Close'])
            hourly_data['MACD'] = macd.macd()
            hourly_data['MACD_Signal'] = macd.macd_signal()
            
            # Últimos valores
            current_price = hourly_data['Close'].iloc[-1]
            current_rsi = hourly_data['RSI'].iloc[-1]
            current_sma40 = hourly_data['SMA40'].iloc[-1]
            
            applicable_strategies = []
            
            # CALL Strategies
            if trend["strategy_bias"] in ["CALL", "NEUTRAL"]:
                # SMA40 Strategy
                if abs(current_price - current_sma40) / current_price < 0.01 and current_rsi < 30:
                    applicable_strategies.append({
                        "type": "CALL",
                        "strategy": self.strategies["CALL"]["SMA40"],
                        "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA"
                    })
                    
                # Normal Drop Strategy
                price_drop = (hourly_data['High'].iloc[-4:].max() - current_price) / current_price
                if 0.02 <= price_drop <= 0.03 and current_rsi < 40:
                    applicable_strategies.append({
                        "type": "CALL",
                        "strategy": self.strategies["CALL"]["NormalDrop"],
                        "confidence": "MEDIA"
                    })
            
            # PUT Strategies
            if trend["strategy_bias"] in ["PUT", "NEUTRAL"]:
                # First Red Candle Strategy
                if current_rsi > 70 and hourly_data['Close'].iloc[-1] < hourly_data['Open'].iloc[-1]:
                    applicable_strategies.append({
                        "type": "PUT",
                        "strategy": self.strategies["PUT"]["FirstRedCandle"],
                        "confidence": "ALTA" if trend["direction"] == "BAJISTA" else "MEDIA"
                    })
            
            return applicable_strategies
            
        except Exception as e:
            logger.error(f"Error identificando estrategias: {str(e)}")
            return []

def main():
    st.title("📊 InversorIA Mini")
    st.write("Análisis Técnico Horario Alineado con Tendencia Macro")
    
    # Categorías de trading
    symbols = {
        "Índices": ["SPY", "QQQ", "DIA", "IWM"],
        "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN"],
        "Finanzas": ["JPM", "BAC", "GS", "MS"]
    }
    
    # Selectores
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Categoría", list(symbols.keys()))
    with col2:
        symbol = st.selectbox("Símbolo", symbols[category])
    
    analyzer = TradingAnalyzer()
    
    try:
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
            st.metric("Sesgo", trend["strategy_bias"])
        
        st.info(trend["description"])
        
        # Datos horarios
        hourly_data = analyzer.get_market_data(symbol, "5d")
        
        # Identificar estrategias aplicables
        strategies = analyzer.identify_strategy(hourly_data, trend)
        
        if strategies:
            st.subheader("📈 Estrategias Aplicables")
            for strat in strategies:
                with st.expander(f"{strat['type']} - {strat['strategy']['name']} (Confianza: {strat['confidence']})"):
                    st.write(f"**Descripción:** {strat['strategy']['description']}")
                    st.write("**Condiciones necesarias:**")
                    for condition in strat['strategy']['conditions']:
                        st.write(f"✓ {condition}")
                    
                    if strat['confidence'] == "ALTA":
                        st.success("⭐ Estrategia alineada con tendencia macro")
                    else:
                        st.warning("⚠️ Validar señales adicionales")
        else:
            st.warning("No se identificaron estrategias aplicables en el momento")
        
        # Métricas técnicas actuales
        st.subheader("📊 Métricas Técnicas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("RSI", f"{hourly_data['RSI'].iloc[-1]:.1f}")
        with col2:
            st.metric("SMA40", f"${hourly_data['SMA40'].iloc[-1]:.2f}")
        with col3:
            st.metric("Precio", f"${hourly_data['Close'].iloc[-1]:.2f}")
        
        # Disclaimer
        st.caption("""
        **⚠️ Disclaimer:** Este análisis es generado automáticamente y debe ser validado.
        Las señales técnicas no garantizan resultados. Realizar análisis adicional y gestión de riesgo apropiada.
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