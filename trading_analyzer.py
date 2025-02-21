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
        Análisis técnico profesional con manejo de sesiones de mercado.
        
        Parameters:
            hourly_data (pd.DataFrame): Datos OHLCV
            trend (dict): Análisis de tendencia macro
            
        Returns:
            list: Estrategias identificadas con niveles operativos
        """
        try:
            # Validación inicial de datos
            if hourly_data.empty:
                logger.warning("Dataset vacío")
                return []
            
            if len(hourly_data) < 5:
                logger.warning("Serie temporal insuficiente para análisis")
                return []

            # Determinar sesión de mercado
            current_session = self._get_market_session()
            logger.info(f"Sesión actual: {current_session}")

            # Calcular indicadores técnicos
            hourly_data['RSI'] = self.indicators.calculate_rsi(hourly_data['Close'])
            hourly_data['SMA40'] = self.indicators.calculate_sma(hourly_data['Close'], 40)
            
            # Obtener datos más recientes con validación
            latest_data = hourly_data.iloc[-1]
            
            # Extraer valores con manejo seguro
            try:
                current_price = latest_data['Close'].iloc[0] if isinstance(latest_data['Close'], pd.Series) else latest_data['Close']
                current_rsi = latest_data['RSI'].iloc[0] if isinstance(latest_data['RSI'], pd.Series) else latest_data['RSI']
                current_sma40 = latest_data['SMA40'].iloc[0] if isinstance(latest_data['SMA40'], pd.Series) else latest_data['SMA40']
                
                # Validación de datos
                if pd.isna([current_price, current_rsi, current_sma40]).any():
                    message = self._get_session_message(current_session)
                    logger.warning(message)
                    return []

                logger.info(f"Análisis Técnico - Precio: ${current_price:.2f} | RSI: {current_rsi:.1f} | SMA40: ${current_sma40:.2f}")
                
            except Exception as e:
                logger.error(f"Error procesando datos técnicos: {str(e)}")
                return []
            
            # Inicializar estrategias
            strategies = []
            bias = trend.get("bias", "NEUTRAL")
            
            # Ajustar análisis según sesión
            if current_session == "PRE_MARKET":
                return self._analyze_pre_market(current_price, current_rsi, current_sma40, trend)
            elif current_session == "AFTER_HOURS":
                return self._analyze_after_hours(current_price, current_rsi, current_sma40, trend)
            elif current_session == "CLOSED":
                logger.info("Mercado cerrado - Solo análisis informativo disponible")
                return []
            
            # Análisis en horario regular
            if bias in ["CALL", "NEUTRAL"]:
                # Estrategia SMA40
                if (current_rsi < 30.0) and (current_price > current_sma40):
                    strategies.append({
                        "type": "CALL",
                        "name": "Rebote en SMA40",
                        "description": "CALL en soporte dinámico con RSI sobrevendido",
                        "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA",
                        "conditions": [
                            "RSI en zona de sobreventa",
                            "Precio confirmando soporte en SMA40",
                            "Alineación con tendencia alcista"
                        ],
                        "levels": {
                            "entry": current_price,
                            "stop": current_sma40 * 0.99,  # 1% bajo SMA40
                            "target": current_price * 1.02,  # Objetivo inicial 2%
                            "r_r": "1:2"  # Ratio Riesgo/Recompensa
                        }
                    })
                    logger.info("Señal CALL identificada - Soporte SMA40")
                
                # Estrategia Pullback
                recent_high = hourly_data['High'].iloc[-5:].max()
                if isinstance(recent_high, pd.Series):
                    recent_high = recent_high.iloc[0]
                price_drop = ((recent_high - current_price) / recent_high)
                
                if (0.02 <= price_drop <= 0.03) and (current_rsi < 40.0):
                    strategies.append({
                        "type": "CALL",
                        "name": "Pullback Técnico",
                        "description": "CALL en corrección moderada de tendencia",
                        "confidence": "MEDIA",
                        "conditions": [
                            "Retroceso técnico 2-3%",
                            "RSI en zona neutral-baja",
                            "Volumen confirmatorio"
                        ],
                        "levels": {
                            "entry": current_price,
                            "stop": current_price * 0.985,  # Stop 1.5%
                            "target": recent_high,  # Objetivo en máximo reciente
                            "r_r": "1:1.5"
                        }
                    })
                    logger.info("Señal CALL identificada - Pullback")
            
            # Estrategias PUT
            if bias in ["PUT", "NEUTRAL"]:
                if current_rsi > 70.0:
                    strategies.append({
                        "type": "PUT",
                        "name": "Divergencia RSI",
                        "description": "PUT en sobrecompra técnica",
                        "confidence": "ALTA" if trend["direction"] == "BAJISTA" else "MEDIA",
                        "conditions": [
                            "RSI en zona de sobrecompra",
                            "Momentum bajista",
                            "Niveles técnicos relevantes"
                        ],
                        "levels": {
                            "entry": current_price,
                            "stop": current_price * 1.015,  # Stop 1.5%
                            "target": current_price * 0.97,  # Objetivo 3%
                            "r_r": "1:2"
                        }
                    })
                    logger.info("Señal PUT identificada - Sobrecompra RSI")
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error en análisis técnico: {str(e)}")
            return []

    def _get_market_session(self) -> str:
        """Determina la sesión actual del mercado."""
        try:
            now = pd.Timestamp.now('America/New_York')
            
            # Verificar fin de semana
            if now.weekday() > 4:
                return "CLOSED"
            
            # Definir horarios
            pre_market_start = now.replace(hour=4, minute=0)
            market_open = now.replace(hour=9, minute=30)
            market_close = now.replace(hour=16, minute=0)
            after_hours_close = now.replace(hour=20, minute=0)
            
            if pre_market_start <= now < market_open:
                return "PRE_MARKET"
            elif market_open <= now < market_close:
                return "REGULAR"
            elif market_close <= now < after_hours_close:
                return "AFTER_HOURS"
            else:
                return "CLOSED"
                
        except Exception as e:
            logger.error(f"Error determinando sesión de mercado: {str(e)}")
            return "UNKNOWN"

    def _get_session_message(self, session: str) -> str:
        """Genera mensaje informativo según la sesión."""
        messages = {
            "PRE_MARKET": "Sesión Pre-Market - Análisis preliminar disponible",
            "REGULAR": "Sesión Regular - Análisis completo disponible",
            "AFTER_HOURS": "Sesión After-Hours - Análisis limitado disponible",
            "CLOSED": "Mercado Cerrado - Análisis informativo solamente",
            "UNKNOWN": "Estado de mercado indeterminado"
        }
        return messages.get(session, "Estado de sesión desconocido")

    def _analyze_pre_market(self, price: float, rsi: float, sma40: float, trend: dict) -> list:
        """
        Análisis especializado para sesión pre-market.
        
        La sesión pre-market (4:00 AM - 9:30 AM ET) requiere consideraciones especiales:
        - Menor liquidez y mayor volatilidad
        - Gaps y movimientos bruscos más frecuentes
        - Reacción a noticias overnight y mercados internacionales
        
        Parameters:
            price (float): Precio actual
            rsi (float): RSI actual
            sma40 (float): SMA 40 actual
            trend (dict): Análisis de tendencia macro
            
        Returns:
            list: Estrategias identificadas para pre-market
        """
        strategies = []
        try:
            bias = trend.get("bias", "NEUTRAL")
            
            # Estrategias CALL Pre-Market
            if bias in ["CALL", "NEUTRAL"]:
                # 1. Gap Fill Setup
                if price < sma40 and rsi < 35.0:
                    strategies.append({
                        "type": "CALL",
                        "name": "Gap Fill Pre-Market",
                        "description": "Oportunidad de CALL en gap bajista con oversold",
                        "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA",
                        "conditions": [
                            "Gap bajista en pre-market",
                            "RSI < 35",
                            "Precio bajo SMA40"
                        ],
                        "levels": {
                            "entry": price,
                            "stop": price * 0.995,  # Stop ajustado por volatilidad
                            "target": sma40,  # Objetivo en SMA40
                            "r_r": "1:1.5"
                        },
                        "session_notes": [
                            "Confirmar volumen pre-market > 25% promedio",
                            "Validar noticias corporativas",
                            "Monitorear futures relacionados"
                        ]
                    })
                
                # 2. Pre-Market Momentum Setup
                if price > sma40 and 40 <= rsi <= 60:
                    strategies.append({
                        "type": "CALL",
                        "name": "Momentum Pre-Market",
                        "description": "CALL en tendencia alcista pre-market con momentum neutro",
                        "confidence": "MEDIA",
                        "conditions": [
                            "Precio sobre SMA40",
                            "RSI en zona neutral",
                            "Pre-market alcista"
                        ],
                        "levels": {
                            "entry": price,
                            "stop": sma40,  # Stop en SMA40
                            "target": price * 1.015,  # Target 1.5%
                            "r_r": "1:2"
                        },
                        "session_notes": [
                            "Esperar confirmación en apertura",
                            "Validar correlación con índices",
                            "Monitorear volumen pre-market"
                        ]
                    })
            
            # Estrategias PUT Pre-Market
            if bias in ["PUT", "NEUTRAL"]:
                # 1. Reversal Setup
                if price > sma40 and rsi > 75.0:
                    strategies.append({
                        "type": "PUT",
                        "name": "Reversal Pre-Market",
                        "description": "PUT en sobrecompra técnica pre-market",
                        "confidence": "ALTA" if trend["direction"] == "BAJISTA" else "MEDIA",
                        "conditions": [
                            "RSI > 75 en pre-market",
                            "Precio extendido sobre SMA40",
                            "Posible reversión en apertura"
                        ],
                        "levels": {
                            "entry": price,
                            "stop": price * 1.01,  # Stop 1%
                            "target": sma40,  # Target en SMA40
                            "r_r": "1:2"
                        },
                        "session_notes": [
                            "Validar resistencias técnicas",
                            "Monitorear flujo de órdenes",
                            "Evaluar gaps en relacionados"
                        ]
                    })
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error en análisis pre-market: {str(e)}")
            return []

    def _analyze_after_hours(self, price: float, rsi: float, sma40: float, trend: dict) -> list:
        """
        Análisis especializado para sesión after-hours.
        
        La sesión after-hours (4:00 PM - 8:00 PM ET) tiene características únicas:
        - Reacción a earnings y noticias post-cierre
        - Menor liquidez pero movimientos significativos
        - Mayor importancia de volumen confirmatorio
        
        Parameters:
            price (float): Precio actual
            rsi (float): RSI actual
            sma40 (float): SMA 40 actual
            trend (dict): Análisis de tendencia macro
            
        Returns:
            list: Estrategias identificadas para after-hours
        """
        strategies = []
        try:
            bias = trend.get("bias", "NEUTRAL")
            
            # Estrategias CALL After-Hours
            if bias in ["CALL", "NEUTRAL"]:
                # 1. Post-Earnings Setup
                if price < sma40 and rsi < 30.0:
                    strategies.append({
                        "type": "CALL",
                        "name": "Post-Earnings Recovery",
                        "description": "CALL en sobreventa post-earnings",
                        "confidence": "ALTA" if trend["direction"] == "ALCISTA" else "MEDIA",
                        "conditions": [
                            "Sobreventa post-earnings",
                            "RSI < 30",
                            "Soporte en niveles clave"
                        ],
                        "levels": {
                            "entry": price,
                            "stop": price * 0.98,  # Stop amplio por volatilidad
                            "target": sma40,  # Target en SMA40
                            "r_r": "1:2"
                        },
                        "session_notes": [
                            "Revisar detalles de earnings",
                            "Monitorear guía forward",
                            "Validar reacción institucional"
                        ]
                    })
                
                # 2. Late Session Reversal
                if 40 <= rsi <= 50 and price > sma40 * 0.995:
                    strategies.append({
                        "type": "CALL",
                        "name": "Late Recovery Setup",
                        "description": "CALL en recuperación late session",
                        "confidence": "MEDIA",
                        "conditions": [
                            "RSI saliendo de sobreventa",
                            "Precio cerca de SMA40",
                            "Volumen confirmatorio"
                        ],
                        "levels": {
                            "entry": price,
                            "stop": price * 0.99,  # Stop 1%
                            "target": price * 1.02,  # Target 2%
                            "r_r": "1:2"
                        },
                        "session_notes": [
                            "Confirmar volumen after-hours",
                            "Revisar noticias pendientes",
                            "Evaluar correlación sectorial"
                        ]
                    })
            
            # Estrategias PUT After-Hours
            if bias in ["PUT", "NEUTRAL"]:
                # 1. Extended Hours Fade
                if rsi > 70.0 and price > sma40 * 1.02:
                    strategies.append({
                        "type": "PUT",
                        "name": "Extended Hours Fade",
                        "description": "PUT en sobreextensión after-hours",
                        "confidence": "ALTA" if trend["direction"] == "BAJISTA" else "MEDIA",
                        "conditions": [
                            "RSI > 70 en after-hours",
                            "Precio extendido > 2% sobre SMA40",
                            "Posible fade en siguiente sesión"
                        ],
                        "levels": {
                            "entry": price,
                            "stop": price * 1.015,  # Stop 1.5%
                            "target": sma40,  # Target en SMA40
                            "r_r": "1:2"
                        },
                        "session_notes": [
                            "Validar volumen after-hours",
                            "Monitorear futures overnight",
                            "Revisar eventos próxima sesión"
                        ]
                    })
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error en análisis after-hours: {str(e)}")
            return []