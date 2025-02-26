import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import ta
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice, OnBalanceVolumeIndicator
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class MarketDataError(Exception):
    """Excepción personalizada para errores de datos de mercado"""
    pass

def validate_market_data(data):
    """Valida la integridad de los datos de mercado"""
    try:
        if data is None or len(data) == 0:
            return False

        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required_columns):
            return False

        # Verificar valores nulos
        if data[required_columns].isnull().any().any():
            return False

        # Verificar valores negativos
        if (data[required_columns] < 0).any().any():
            return False

        # Verificar coherencia OHLC
        if not all(data['High'] >= data['Low']) or \
           not all(data['High'] >= data['Open']) or \
           not all(data['High'] >= data['Close']) or \
           not all(data['Low'] <= data['Open']) or \
           not all(data['Low'] <= data['Close']):
            return False

        return True

    except Exception as e:
        logger.error(f"Error en validate_market_data: {str(e)}")
        return False

def fetch_market_data(symbol, period='6mo', interval='1d'):
    """Obtiene datos de mercado con validación mejorada"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)

        if not validate_market_data(data):
            logger.error(f"Datos inválidos para {symbol}")
            return None

        return data

    except Exception as e:
        logger.error(f"Error en fetch_market_data: {str(e)}")
        return None

class TechnicalAnalyzer:
    """Analizador técnico avanzado con manejo profesional de indicadores"""

    def __init__(self, data):
        """Inicializa el analizador con validación de datos"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Los datos deben ser un DataFrame")

        if len(data) < 20:
            raise ValueError("Se requieren al menos 20 períodos para análisis")

        self.data = data.copy()
        self.indicators = None
        self.signals = {}

    def calculate_indicators(self):
        """Calcula indicadores técnicos con validación avanzada"""
        try:
            if self.data is None or self.data.empty:
                raise ValueError("No hay datos disponibles")

            df = self.data.copy()

            # Validar y preparar precios
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_cols):
                raise ValueError("Faltan columnas requeridas")

            # Convertir a float con validación
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            if df['Close'].isnull().all():
                raise ValueError("No hay precios válidos")

            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume']

            # Tendencia
            macd = MACD(close)
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Hist'] = macd.macd_diff()

            # Medias Móviles con validación
            for period in [20, 50, 200]:
                if len(df) >= period:
                    df[f'SMA_{period}'] = SMAIndicator(close, window=period).sma_indicator()
                    df[f'EMA_{period}'] = EMAIndicator(close, window=period).ema_indicator()

            # Momentum con validación
            if len(df) >= 14:  # Período mínimo para RSI
                rsi = RSIIndicator(close)
                df['RSI'] = rsi.rsi()

                stoch = StochasticOscillator(high, low, close)
                df['Stoch_K'] = stoch.stoch()
                df['Stoch_D'] = stoch.stoch_signal()

            # Volatilidad
            bb = BollingerBands(close)
            df['BB_High'] = bb.bollinger_hband()
            df['BB_Mid'] = bb.bollinger_mavg()
            df['BB_Low'] = bb.bollinger_lband()
            df['BB_Width'] = (df['BB_High'] - df['BB_Low']) / df['BB_Mid']

            # Volumen
            df['Volume_SMA'] = SMAIndicator(volume, window=20).sma_indicator()
            df['Volume_Ratio'] = volume / df['Volume_SMA']

            vwap = VolumeWeightedAveragePrice(high, low, close, volume)
            df['VWAP'] = vwap.volume_weighted_average_price()

            # ATR para volatilidad
            atr = AverageTrueRange(high, low, close)
            df['ATR'] = atr.average_true_range()

            # Limpiar datos
            df = df.dropna()

            self.indicators = df
            return df

        except Exception as e:
            logger.error(f"Error en calculate_indicators: {str(e)}")
            return None

    def get_current_signals(self):
        """Obtiene señales actuales con validación robusta"""
        try:
            if self.indicators is None:
                self.calculate_indicators()

            if self.indicators is None or len(self.indicators) == 0:
                raise ValueError("No hay datos de indicadores válidos")

            df = self.indicators
            if len(df) < 2:
                raise ValueError("Datos insuficientes para análisis")

            # Obtener datos con validación
            current = df.iloc[-1].copy()
            previous = df.iloc[-2].copy()

            # Calcular promedios y referencias
            sma_trend = current.get('SMA_20', 0) > current.get('SMA_50', 0)
            volume_trend = current.get('Volume', 0) > current.get('Volume_SMA', 1)

            signals = {
                "trend": {
                    "sma_20_50": "alcista" if sma_trend else "bajista",
                    "macd": "alcista" if current.get('MACD', 0) > current.get('MACD_Signal', 0) else "bajista",
                    "ema_trend": "alcista" if current.get('EMA_20', 0) > current.get('EMA_50', 0) else "bajista"
                },
                "momentum": {
                    "rsi": float(current.get('RSI', 50)),
                    "rsi_condition": self._get_rsi_condition(current.get('RSI', 50)),
                    "stoch_k": float(current.get('Stoch_K', 50)),
                    "stoch_d": float(current.get('Stoch_D', 50))
                },
                "volatility": {
                    "bb_width": float(current.get('BB_Width', 0)),
                    "atr": float(current.get('ATR', 0)),
                    "price_position": self._get_price_position(current),
                    "volatility_state": self._get_volatility_state(current)
                },
                "volume": {
                    "trend": "alcista" if volume_trend else "bajista",
                    "ratio": float(current.get('Volume_Ratio', 1)),
                    "vwap_position": "por_encima" if current.get('Close', 0) > current.get('VWAP', 0) else "por_debajo"
                }
            }

            # Calcular señal agregada
            signals["overall"] = self._calculate_overall_signal(signals)

            return signals

        except Exception as e:
            logger.error(f"Error en get_current_signals: {str(e)}")
            return None

    def _get_rsi_condition(self, rsi):
        """Determina la condición del RSI"""
        if rsi > 70:
            return "sobrecomprado"
        elif rsi < 30:
            return "sobrevendido"
        else:
            return "neutral"

    def _get_price_position(self, current):
        """Determina la posición del precio respecto a las bandas"""
        if current.get('Close', 0) > current.get('BB_High', float('inf')):
            return "superior"
        elif current.get('Close', 0) < current.get('BB_Low', 0):
            return "inferior"
        else:
            return "medio"

    def _get_volatility_state(self, current):
        """Evalúa el estado de la volatilidad"""
        bb_width = current.get('BB_Width', 0)
        atr = current.get('ATR', 0)

        if bb_width > self.indicators['BB_Width'].mean() * 1.5:
            return "alta"
        elif bb_width < self.indicators['BB_Width'].mean() * 0.5:
            return "baja"
        else:
            return "normal"

    def _calculate_overall_signal(self, signals):
        """Calcula la señal general basada en todos los indicadores"""
        score = 0

        # Puntaje por tendencia
        if signals['trend']['sma_20_50'] == "alcista":
            score += 1
        else:
            score -= 1

        # Puntaje por momentum
        if signals['momentum']['rsi_condition'] == "sobrecomprado":
            score -= 1
        elif signals['momentum']['rsi_condition'] == "sobrevendido":
            score += 1

        # Puntaje por volatilidad
        if signals['volatility']['volatility_state'] == "alta":
            score *= 0.8  # Reducir confianza en alta volatilidad

        # Puntaje por volumen
        if signals['volume']['trend'] == "alcista" and signals['volume']['ratio'] > 1.5:
            score += 1

        # Determinar señal final
        if score >= 2:
            return {"signal": "compra_fuerte", "confidence": "alta"}
        elif score > 0:
            return {"signal": "compra", "confidence": "moderada"}
        elif score <= -2:
            return {"signal": "venta_fuerte", "confidence": "alta"}
        elif score < 0:
            return {"signal": "venta", "confidence": "moderada"}
        else:
            return {"signal": "neutral", "confidence": "baja"}

def get_market_context(symbol):
    """Obtiene contexto completo de mercado"""
    try:
        # Obtener datos
        data = fetch_market_data(symbol)
        if data is None:
            return None

        # Analizar datos
        analyzer = TechnicalAnalyzer(data)
        df_technical = analyzer.calculate_indicators()
        if df_technical is None:
            return None

        signals = analyzer.get_current_signals()
        if signals is None:
            return None

        context = {
            "last_price": float(df_technical['Close'].iloc[-1]),
            "change": float(df_technical['Close'].iloc[-1] - df_technical['Close'].iloc[-2]),
            "signals": signals,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return context

    except Exception as e:
        logger.error(f"Error en get_market_context: {str(e)}")
        return None