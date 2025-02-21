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
    def calculate_sma(series: pd.Series, window: int) -> pd.Series:
        """Calcula SMA con validación"""
        if len(series) < window:
            return pd.Series(np.nan, index=series.index)
        return series.rolling(window=window).mean()
    
    @staticmethod
    def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
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
        """Inicializa estrategias disponibles"""
        return {
            "CALL": {
                "SMA40": {
                    "name": "Promedio Móvil de 40 en Hora",
                    "description": "CALL cuando el precio toca SMA40 y rompe línea bajista",
                    "conditions": ["SMA40 como soporte", "RSI < 30", "Ruptura línea bajista"]
                },
                "NormalDrop": {
                    "name": "Caída Normal (2-3 puntos)",
                    "description": "CALL tras caída moderada con volumen",
                    "conditions": ["Caída de 2-3 puntos", "Volumen creciente", "RSI < 40"]
                }
            },
            "PUT": {
                "FirstRedCandle": {
                    "name": "Primera Vela Roja de Apertura",
                    "description": "PUT en primera vela roja con sobrecompra",
                    "conditions": ["Primera vela roja", "RSI > 70", "Cerca de resistencia"]
                }
            }
        }

    def get_market_data(self, symbol: str, period: str = "5d", interval: str = "1h") -> pd.DataFrame:
        """Obtiene datos de mercado con validación"""
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if data.empty:
                raise MarketDataError(f"No se obtuvieron datos para {symbol}")
            return data
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            raise MarketDataError(str(e))

    def analyze_trend(self, symbol: str):
        """Analiza tendencia del mercado"""
        try:
            data = self.get_market_data(symbol, period="1y", interval="1d")
            
            if len(data) < 200:
                raise MarketDataError("Datos insuficientes para análisis")
            
            # Calcular indicadores
            data['SMA20'] = self.indicators.calculate_sma(data['Close'], 20)
            data['SMA50'] = self.indicators.calculate_sma(data['Close'], 50)
            data['SMA200'] = self.indicators.calculate_sma(data['Close'], 200)
            data['RSI'] = self.indicators.calculate_rsi(data['Close'])
            
            # Obtener último registro usando .iloc[0]
            latest = data.iloc[-1]
            metrics = {
                "price": float(latest['Close'].iloc[0] if isinstance(latest['Close'], pd.Series) else latest['Close']),
                "sma20": float(latest['SMA20'].iloc[0] if isinstance(latest['SMA20'], pd.Series) else latest['SMA20']),
                "sma50": float(latest['SMA50'].iloc[0] if isinstance(latest['SMA50'], pd.Series) else latest['SMA50']),
                "sma200": float(latest['SMA200'].iloc[0] if isinstance(latest['SMA200'], pd.Series) else latest['SMA200']),
                "rsi": float(latest['RSI'].iloc[0] if isinstance(latest['RSI'], pd.Series) else latest['RSI'])
            }
            
            # Análisis de tendencia con valores numéricos
            trend = {
                "direction": "INDEFINIDA",
                "strength": "NEUTRAL",
                "bias": "NEUTRAL",
                "description": "Mercado sin tendencia clara",
                "metrics": metrics
            }
            
            # Determinar tendencia usando valores numéricos
            price = metrics["price"]
            sma50 = metrics["sma50"]
            sma200 = metrics["sma200"]
            
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

    def identify_strategy(self, hourly_data: pd.DataFrame, trend: dict):
        """
        Identifica estrategias de trading aplicables con manejo robusto de datos.
        
        Args:
            hourly_data (pd.DataFrame): Datos de precio horarios
            trend (dict): Información de tendencia actual
            
        Returns:
            list: Lista de estrategias aplicables con sus condiciones
        """
        try:
            # Validación inicial de datos
            if hourly_data.empty:
                logger.warning("Dataset vacío recibido")
                return []
            
            if len(hourly_data) < 5:
                logger.warning("Datos insuficientes para análisis")
                return []
                
            # Calcular indicadores técnicos
            hourly_data['RSI'] = self.indicators.calculate_rsi(hourly_data['Close'])
            hourly_data['SMA40'] = self.indicators.calculate_sma(hourly_data['Close'], 40)
            
            # Obtener datos más recientes
            latest_data = hourly_data.iloc[-1]
            logger.info("Procesando datos más recientes para análisis")
            
            try:
                # Extraer valores con manejo seguro
                current_price = latest_data['Close']
                current_rsi = latest_data['RSI']
                current_sma40 = latest_data['SMA40']
                
                # Convertir a valores escalares
                current_price = float(current_price) if not isinstance(current_price, float) else current_price
                current_rsi = float(current_rsi) if not isinstance(current_rsi, float) else current_rsi
                current_sma40 = float(current_sma40) if not isinstance(current_sma40, float) else current_sma40
                
                logger.info(f"Valores actuales - Precio: {current_price:.2f}, RSI: {current_rsi:.2f}, SMA40: {current_sma40:.2f}")
                
            except Exception as e:
                logger.error(f"Error procesando valores actuales: {str(e)}")
                return []
            
            # Inicializar lista de estrategias
            strategies = []
            
            # Validar tendencia
            bias = trend.get("bias", "NEUTRAL")
            
            # Analizar estrategias CALL
            if bias in ["CALL", "NEUTRAL"]:
                try:
                    # Estrategia SMA40
                    if (current_rsi < 30.0) and (current_price > current_sma40):
                        strategies.append({
                            "type": "CALL",
                            "name": "Estrategia SMA40",
                            "description": "CALL en soporte SMA40 con RSI sobrevendido",
                            "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA",
                            "conditions": [
                                "RSI en zona de sobreventa",
                                "Precio por encima de SMA40",
                                "Tendencia alcista de fondo"
                            ],
                            "metrics": {
                                "rsi": current_rsi,
                                "price_vs_sma40": f"{((current_price/current_sma40)-1)*100:.1f}%"
                            }
                        })
                        logger.info("Estrategia CALL SMA40 identificada")
                    
                    # Estrategia Caída Normal
                    recent_high = hourly_data['High'].iloc[-5:].max()
                    if isinstance(recent_high, pd.Series):
                        recent_high = recent_high.iloc[0]
                    price_drop = ((recent_high - current_price) / recent_high)
                    
                    if (0.02 <= price_drop <= 0.03) and (current_rsi < 40.0):
                        strategies.append({
                            "type": "CALL",
                            "name": "Caída Normal",
                            "description": "CALL tras corrección moderada",
                            "confidence": "MEDIA",
                            "conditions": [
                                "Caída de 2-3% desde máximos",
                                "RSI bajo 40",
                                "Volumen por encima de la media"
                            ],
                            "metrics": {
                                "drop": f"{price_drop*100:.1f}%",
                                "rsi": current_rsi
                            }
                        })
                        logger.info("Estrategia CALL Caída Normal identificada")
                        
                except Exception as e:
                    logger.error(f"Error procesando estrategias CALL: {str(e)}")
            
            # Analizar estrategias PUT
            if bias in ["PUT", "NEUTRAL"]:
                try:
                    if current_rsi > 70.0:
                        strategies.append({
                            "type": "PUT",
                            "name": "Sobrecompra RSI",
                            "description": "PUT en condición de sobrecompra",
                            "confidence": "ALTA" if trend["direction"] == "BAJISTA" else "MEDIA",
                            "conditions": [
                                "RSI en zona de sobrecompra",
                                "Tendencia bajista de fondo",
                                "Cerca de resistencia técnica"
                            ],
                            "metrics": {
                                "rsi": current_rsi
                            }
                        })
                        logger.info("Estrategia PUT RSI identificada")
                        
                except Exception as e:
                    logger.error(f"Error procesando estrategias PUT: {str(e)}")
            
            # Logging final
            if strategies:
                logger.info(f"Se identificaron {len(strategies)} estrategias válidas")
            else:
                logger.info("No se identificaron estrategias válidas")
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error en identificación de estrategias: {str(e)}")
            return []