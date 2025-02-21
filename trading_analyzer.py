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
        self.strategies = self._initialize_strategies()

    def _initialize_strategies(self):
        """Inicializa todas las estrategias disponibles"""
        return {
            "CALL": {
                "SMA40": {
                    "name": "Promedio Móvil de 40 en Hora",
                    "description": "CALL cuando el precio toca SMA40 y rompe línea bajista",
                    "conditions": ["SMA40 actuando como soporte", "RSI < 30", "Ruptura de línea bajista"]
                },
                "NormalDrop": {
                    "name": "Caída Normal (2-3 puntos)",
                    "description": "CALL tras caída moderada con volumen",
                    "conditions": ["Caída de 2-3 puntos", "Volumen creciente", "RSI < 40"]
                },
                "StrongDrop": {
                    "name": "Caída Fuerte (5-6 puntos)",
                    "description": "CALL tras caída fuerte cerca de soporte mayor",
                    "conditions": ["Caída de 5-6 puntos", "Cerca de SMA200 diario", "RSI < 30"]
                },
                "GapUp": {
                    "name": "Gap Normal al Alza",
                    "description": "CALL en gap alcista con volumen",
                    "conditions": ["Gap alcista", "Volumen alto", "Primera vela verde"]
                }
            },
            "PUT": {
                "FirstRedCandle": {
                    "name": "Primera Vela Roja de Apertura",
                    "description": "PUT en primera vela roja con sobrecompra",
                    "conditions": ["Primera vela roja", "RSI > 70", "Cerca de resistencia"]
                },
                "GapBreak": {
                    "name": "Ruptura del Piso del Gap",
                    "description": "PUT en ruptura de gap con volumen",
                    "conditions": ["Gap identificado", "Ruptura con volumen", "MACD bajista"]
                },
                "StrongResistance": {
                    "name": "Resistencia Fuerte",
                    "description": "PUT en rechazo de resistencia importante",
                    "conditions": ["Toque de resistencia", "RSI > 70", "Vela de rechazo"]
                }
            }
        }

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
            
            # Obtener último registro
            latest = data.iloc[-1]
            
            # Extraer valores con iloc[0]
            trend = {
                "direction": "INDEFINIDA",
                "strength": "NEUTRAL",
                "bias": "NEUTRAL",
                "description": "",
                "metrics": {
                    "price": float(latest['Close']),
                    "sma20": float(latest['SMA20']),
                    "sma50": float(latest['SMA50']),
                    "sma200": float(latest['SMA200']),
                    "rsi": float(latest['RSI'])
                }
            }
            
            # Análisis usando valores ya convertidos a float
            price = trend["metrics"]["price"]
            sma50 = trend["metrics"]["sma50"]
            sma200 = trend["metrics"]["sma200"]
            
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
            
            # Extraer valores con iloc[0]
            rsi = float(latest['RSI'])
            price = float(latest['Close'])
            sma40 = float(latest['SMA40'])
            
            # Estrategias CALL
            if trend["bias"] in ["CALL", "NEUTRAL"]:
                if rsi < 30 and price > sma40:
                    applicable_strategies.append({
                        "type": "CALL",
                        "name": self.strategies["CALL"]["SMA40"]["name"],
                        "description": self.strategies["CALL"]["SMA40"]["description"],
                        "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA",
                        "conditions": self.strategies["CALL"]["SMA40"]["conditions"]
                    })
                
                if len(hourly_data) >= 5:
                    high_5d = hourly_data['High'].iloc[-5:].max()
                    price_change = (high_5d - price) / price
                    if 0.02 <= price_change <= 0.03 and rsi < 40:
                        applicable_strategies.append({
                            "type": "CALL",
                            "name": self.strategies["CALL"]["NormalDrop"]["name"],
                            "description": self.strategies["CALL"]["NormalDrop"]["description"],
                            "confidence": "MEDIA",
                            "conditions": self.strategies["CALL"]["NormalDrop"]["conditions"]
                        })
            
            # Estrategias PUT
            if trend["bias"] in ["PUT", "NEUTRAL"]:
                if rsi > 70:
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