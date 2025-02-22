import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import logging
from typing import Dict, List, Optional, Tuple
from ta.trend import MACD, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice

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
    """Clase para cálculo de indicadores técnicos"""
    
    @staticmethod
    def calculate_sma(series: pd.Series, window: int) -> pd.Series:
        """Calcula Media Móvil Simple"""
        return SMAIndicator(close=series, window=window).sma_indicator()
    
    @staticmethod
    def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
        """Calcula RSI"""
        return RSIIndicator(close=series, window=window).rsi()
        
    @staticmethod
    def calculate_bollinger(series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calcula Bandas de Bollinger"""
        bb = BollingerBands(close=series)
        return bb.bollinger_hband(), bb.bollinger_mavg(), bb.bollinger_lband()
        
    @staticmethod
    def calculate_macd(series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calcula MACD"""
        macd = MACD(close=series)
        return macd.macd(), macd.macd_signal(), macd.macd_diff()
        
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Calcula Estocástico"""
        stoch = StochasticOscillator(high=high, low=low, close=close)
        return stoch.stoch(), stoch.stoch_signal()
        
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Calcula ATR"""
        return AverageTrueRange(high=high, low=low, close=close).average_true_range()

class TradingAnalyzer:
    """Analizador principal de trading"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.strategies = self._initialize_strategies()

    def _initialize_strategies(self) -> Dict:
        """Inicializa catálogo de estrategias"""
        return {
            "CALL": {
                "SMA40": {
                    "name": "Promedio Móvil de 40",
                    "description": "CALL en soporte SMA40 con RSI sobrevendido",
                    "timeframe": "1h",
                    "indicators": {
                        "required": ["SMA20", "SMA40", "RSI", "MACD", "BB"],
                        "optional": ["Volume", "VWAP"]
                    },
                    "conditions": [
                        "SMA20 > SMA40 (tendencia alcista)",
                        "Precio cerca de SMA40",
                        "RSI < 30",
                        "Después de 11:00 AM ET",
                        "MACD convergencia alcista"
                    ],
                    "stop_rules": "Mínimo de vela de entrada",
                    "target_rules": "2R mínimo"
                },
                "NormalDrop": {
                    "name": "Caída Normal",
                    "description": "CALL tras corrección 2-3 puntos",
                    "timeframe": "1h",
                    "indicators": {
                        "required": ["SMA40", "RSI", "ATR"],
                        "optional": ["VWAP", "OBV"]
                    },
                    "conditions": [
                        "Caída 2-3%",
                        "RSI < 40",
                        "ATR > Media ATR(20)",
                        "Volumen creciente"
                    ],
                    "stop_rules": "Bajo swing previo",
                    "target_rules": "1.5R mínimo"
                },
                "StrongDrop": {
                    "name": "Caída Fuerte",
                    "description": "CALL tras corrección 5-6 puntos",
                    "timeframe": "1h",
                    "indicators": {
                        "required": ["SMA200", "RSI", "ATR"],
                        "optional": ["VWAP"]
                    },
                    "conditions": [
                        "Caída 5-6%",
                        "RSI < 30",
                        "Cerca de SMA200",
                        "Volumen alto"
                    ],
                    "stop_rules": "1% bajo SMA200",
                    "target_rules": "2R mínimo"
                },
                "GapUp": {
                    "name": "Gap Normal Alcista",
                    "description": "CALL en gap alcista con volumen",
                    "timeframe": "1h",
                    "indicators": {
                        "required": ["VWAP", "Volume"],
                        "optional": ["Delta"]
                    },
                    "conditions": [
                        "Gap alcista pre-market",
                        "Velas 10-11 AM verdes",
                        "Volumen > 150% promedio",
                        "VWAP soporte"
                    ],
                    "stop_rules": "Bajo VWAP",
                    "target_rules": "2R mínimo"
                }
            },
            "PUT": {
                "FirstRedCandle": {
                    "name": "Primera Vela Roja",
                    "description": "PUT en primera vela roja con sobrecompra",
                    "timeframe": "1h",
                    "indicators": {
                        "required": ["RSI", "MACD", "Volume"],
                        "optional": ["MFI"]
                    },
                    "conditions": [
                        "Vela roja en apertura",
                        "RSI > 70",
                        "Zona de resistencia",
                        "Volumen alto"
                    ],
                    "stop_rules": "Alto de apertura",
                    "target_rules": "2R mínimo"
                },
                "GapBreak": {
                    "name": "Ruptura de Gap",
                    "description": "PUT en ruptura de gap con volumen",
                    "timeframe": "1h",
                    "indicators": {
                        "required": ["Gap", "Volume", "Momentum"],
                        "optional": ["Delta"]
                    },
                    "conditions": [
                        "Gap identificado",
                        "Ruptura confirmada",
                        "Momentum negativo",
                        "Volumen > promedio"
                    ],
                    "stop_rules": "Alto del gap",
                    "target_rules": "1.5R mínimo"
                },
                "FourSteps": {
                    "name": "Modelo 4 Pasos",
                    "description": "PUT en patrón de 4 pasos bajista",
                    "timeframe": "1h",
                    "indicators": {
                        "required": ["Channel", "RSI", "MACD"],
                        "optional": ["BB"]
                    },
                    "conditions": [
                        "Canal bajista activo",
                        "Techo/resistencia",
                        "Vela verde borrada",
                        "Ruptura soporte"
                    ],
                    "stop_rules": "Alto de vela verde",
                    "target_rules": "2R mínimo"
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

    def analyze_trend(self, symbol: str) -> Tuple[Dict, pd.DataFrame]:
        """Analiza tendencia del mercado"""
        try:
            # Obtener datos diarios y horarios
            daily_data = self.get_market_data(symbol, period="1y", interval="1d")
            hourly_data = self.get_market_data(symbol, period="5d", interval="1h")
            
            if len(daily_data) < 200:
                raise MarketDataError("Datos insuficientes para análisis")
            
            # Calcular indicadores diarios
            daily_data = self._calculate_indicators(daily_data)
            latest = daily_data.iloc[-1]
            
            # Determinar tendencia
            trend = {
                "direction": "INDEFINIDA",
                "strength": "NEUTRAL",
                "bias": "NEUTRAL",
                "description": "Mercado sin tendencia clara",
                "metrics": {
                    "price": float(latest['Close']),
                    "sma20": float(latest['SMA20']),
                    "sma50": float(latest['SMA50']),
                    "sma200": float(latest['SMA200']),
                    "rsi": float(latest['RSI'])
                }
            }
            
            # Análisis de tendencia
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
            
            return trend, daily_data
            
        except Exception as e:
            logger.error(f"Error en análisis de tendencia: {str(e)}")
            raise MarketDataError(str(e))

    def identify_strategy(self, hourly_data: pd.DataFrame, trend: Dict) -> List[Dict]:
        """Identifica estrategias aplicables"""
        try:
            strategies = []
            # Calcular indicadores horarios
            indicators = self._calculate_indicators(hourly_data)
            latest = indicators.iloc[-1]
            
            # Validar estrategias según el contexto de mercado
            session = self._get_market_session()
            if session not in ["REGULAR", "PRE_MARKET"]:
                return []
            
            # Estrategias CALL
            if trend["bias"] in ["CALL", "NEUTRAL"]:
                # SMA40 Strategy
                if (latest['RSI'] < 30 and
                    latest['SMA20'] > latest['SMA40'] and
                    abs(latest['Close'] - latest['SMA40'])/latest['SMA40'] < 0.01):
                    
                    strategies.append(self._create_strategy_signal(
                        "CALL", "SMA40", latest, trend["direction"],
                        stop_pct=0.01, target_pct=0.02
                    ))
                
                # NormalDrop Strategy
                price_drop = (indicators['High'].rolling(5).max().iloc[-1] - latest['Close']) / latest['Close']
                if (0.02 <= price_drop <= 0.03 and latest['RSI'] < 40):
                    strategies.append(self._create_strategy_signal(
                        "CALL", "NormalDrop", latest, trend["direction"],
                        stop_pct=0.015, target_pct=0.03
                    ))
                
                # StrongDrop Strategy
                if (price_drop >= 0.05 and latest['RSI'] < 30 and
                    abs(latest['Close'] - latest['SMA200'])/latest['SMA200'] < 0.02):
                    
                    strategies.append(self._create_strategy_signal(
                        "CALL", "StrongDrop", latest, trend["direction"],
                        stop_pct=0.02, target_pct=0.04
                    ))
            
            # Estrategias PUT
            if trend["bias"] in ["PUT", "NEUTRAL"]:
                # FirstRedCandle Strategy
                if (latest['RSI'] > 70 and
                    latest['Close'] < latest['Open'] and
                    latest['Volume'] > indicators['Volume'].rolling(20).mean().iloc[-1]):
                    
                    strategies.append(self._create_strategy_signal(
                        "PUT", "FirstRedCandle", latest, trend["direction"],
                        stop_pct=0.01, target_pct=0.02
                    ))
                
                # GapBreak Strategy
                if (self._is_gap_down(indicators) and
                    latest['Close'] < indicators['Low'].rolling(20).min().iloc[-1]):
                    
                    strategies.append(self._create_strategy_signal(
                        "PUT", "GapBreak", latest, trend["direction"],
                        stop_pct=0.015, target_pct=0.03
                    ))
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error identificando estrategias: {str(e)}")
            return []

    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos"""
        df = data.copy()
        
        # Medias Móviles
        df['SMA20'] = self.indicators.calculate_sma(df['Close'], 20)
        df['SMA40'] = self.indicators.calculate_sma(df['Close'], 40)
        df['SMA50'] = self.indicators.calculate_sma(df['Close'], 50)
        df['SMA200'] = self.indicators.calculate_sma(df['Close'], 200)
        
        # RSI
        df['RSI'] = self.indicators.calculate_rsi(df['Close'])
        
        # MACD
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = self.indicators.calculate_macd(df['Close'])
        
        # Bollinger Bands
        df['BB_High'], df['BB_Mid'], df['BB_Low'] = self.indicators.calculate_bollinger(df['Close'])
        df['BB_Width'] = (df['BB_High'] - df['BB_Low']) / df['BB_Mid']
        
        # ATR
        df['ATR'] = self.indicators.calculate_atr(df['High'], df['Low'], df['Close'])
        
        # Volumen Relativo
        df['Volume_SMA20'] = self.indicators.calculate_sma(df['Volume'], 20)
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA20']
        
        # Stochastic
        df['Stoch_K'], df['Stoch_D'] = self.indicators.calculate_stochastic(
            df['High'], df['Low'], df['Close']
        )
        
        return df

    def _get_market_session(self) -> str:
        """Determina la sesión actual del mercado"""
        try:
            ny_tz = pytz.timezone('America/New_York')
            now = datetime.now(ny_tz)
            
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
            logger.error(f"Error determinando sesión: {str(e)}")
            return "UNKNOWN"

    def _create_strategy_signal(
        self, 
        type: str, 
        strategy: str, 
        data: pd.Series, 
        trend: str,
        stop_pct: float,
        target_pct: float
    ) -> Dict:
        """
        Crea señal de estrategia con niveles operativos.
        
        Args:
            type: Tipo de estrategia (CALL/PUT)
            strategy: Nombre de la estrategia
            data: Datos técnicos actuales
            trend: Tendencia del mercado
            stop_pct: Porcentaje para stop loss
            target_pct: Porcentaje para take profit
        """
        current_price = float(data['Close'])
        
        # Ajustar stop y target según dirección
        if type == "CALL":
            stop_price = current_price * (1 - stop_pct)
            target_price = current_price * (1 + target_pct)
        else:  # PUT
            stop_price = current_price * (1 + stop_pct)
            target_price = current_price * (1 - target_pct)
        
        # Calcular R/R
        risk = abs(current_price - stop_price)
        reward = abs(target_price - current_price)
        rr_ratio = f"1:{reward/risk:.1f}"
        
        return {
            "type": type,
            "name": self.strategies[type][strategy]["name"],
            "description": self.strategies[type][strategy]["description"],
            "confidence": "ALTA" if trend == type.replace("CALL", "ALCISTA").replace("PUT", "BAJISTA") else "MEDIA",
            "conditions": self.strategies[type][strategy]["conditions"],
            "levels": {
                "entry": current_price,
                "stop": stop_price,
                "target": target_price,
                "r_r": rr_ratio
            }
        }

    def _is_gap_down(self, data: pd.DataFrame) -> bool:
        """
        Verifica si hay gap bajista.
        
        Args:
            data: DataFrame con datos OHLCV
        """
        try:
            today_open = data['Open'].iloc[-1]
            prev_close = data['Close'].iloc[-2]
            return today_open < prev_close * 0.99  # Gap > 1%
        except:
            return False

    def get_strategy_details(self, type: str, name: str) -> Dict:
        """
        Obtiene detalles completos de una estrategia.
        
        Args:
            type: Tipo de estrategia (CALL/PUT)
            name: Nombre de la estrategia
        """
        try:
            return self.strategies[type][name]
        except KeyError:
            logger.error(f"Estrategia no encontrada: {type} - {name}")
            return None

    def validate_session_rules(self, strategy: Dict) -> bool:
        """
        Valida reglas específicas de sesión para una estrategia.
        
        Args:
            strategy: Configuración de la estrategia
        """
        current_session = self._get_market_session()
        
        # Reglas específicas por sesión
        if strategy.get("timeframe") == "1h":
            if current_session not in ["REGULAR", "PRE_MARKET"]:
                return False
                
            # Validar hora para estrategias intradía
            ny_time = datetime.now(pytz.timezone('America/New_York'))
            if "después de 11:00 AM" in str(strategy.get("conditions", [])):
                return ny_time.hour >= 11
        
        return True

    def get_session_message(self, session: str) -> str:
        """
        Genera mensaje informativo según la sesión.
        
        Args:
            session: Sesión actual del mercado
        """
        messages = {
            "PRE_MARKET": "Sesión Pre-Market - Análisis preliminar disponible",
            "REGULAR": "Sesión Regular - Análisis completo disponible",
            "AFTER_HOURS": "Sesión After-Hours - Análisis limitado disponible",
            "CLOSED": "Mercado Cerrado - Análisis informativo solamente",
            "UNKNOWN": "Estado de mercado indeterminado"
        }
        return messages.get(session, "Estado de sesión desconocido")