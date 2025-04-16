import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
import traceback
import time
import requests
import os
import pytz
from typing import Dict, List, Optional, Union, Tuple, Any
import functools
import json
from io import StringIO

# Importaciones de biblioteca 'ta'
import ta
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice, OnBalanceVolumeIndicator

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# Excepción personalizada
class MarketDataError(Exception):
    """Excepción personalizada para errores de datos de mercado"""

    pass


# =================================================
# SISTEMA DE CACHÉ
# =================================================


class DataCache:
    """Sistema avanzado de caché con invalidación por tiempo"""

    def __init__(self, ttl_minutes=30):
        self.cache = {}
        self.ttl_minutes = ttl_minutes
        self.request_timestamps = {}
        self.hit_counter = 0
        self.miss_counter = 0

    def get(self, key):
        """Obtiene dato del caché si es válido"""
        if key in self.cache:
            timestamp, data = self.cache[key]
            if (datetime.now() - timestamp).total_seconds() < (self.ttl_minutes * 60):
                self.hit_counter += 1
                return data
        self.miss_counter += 1
        return None

    def set(self, key, data):
        """Almacena dato en caché con timestamp"""
        self.cache[key] = (datetime.now(), data)

    def clear(self):
        """Limpia caché completo"""
        old_count = len(self.cache)
        self.cache = {}
        logger.info(f"Caché limpiado. {old_count} entradas eliminadas.")
        return old_count

    def can_request(self, symbol: str, min_interval_sec: int = 2) -> bool:
        """Controla frecuencia de solicitudes por símbolo"""
        now = datetime.now()

        if symbol in self.request_timestamps:
            elapsed = (now - self.request_timestamps[symbol]).total_seconds()
            if elapsed < min_interval_sec:
                return False

        self.request_timestamps[symbol] = now
        return True

    def get_stats(self) -> Dict:
        """Retorna estadísticas del caché"""
        total_requests = self.hit_counter + self.miss_counter
        hit_rate = (
            (self.hit_counter / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "entradas": len(self.cache),
            "hit_rate": f"{hit_rate:.1f}%",
            "hits": self.hit_counter,
            "misses": self.miss_counter,
        }


# Inicializar caché global
_data_cache = DataCache()

# =================================================
# UTILIDADES DE VALIDACIÓN
# =================================================


def validate_market_data(data: pd.DataFrame) -> bool:
    """Valida la integridad de los datos de mercado"""
    try:
        if data is None or len(data) == 0:
            return False

        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in data.columns for col in required_columns):
            return False

        # Verificar valores nulos
        if data[required_columns].isnull().any().any():
            # Intentar reparar datos nulos
            data.fillna(method="ffill", inplace=True)
            data.fillna(method="bfill", inplace=True)
            # Verificar si aún hay nulos después de reparar
            if data[required_columns].isnull().any().any():
                return False

        # Verificar valores negativos en precio
        price_cols = ["Open", "High", "Low", "Close"]
        if (data[price_cols] <= 0).any().any():
            return False

        # Verificar coherencia OHLC (con pequeña tolerancia)
        if (
            not all(data["High"] >= data["Low"])
            or not all(data["High"] >= data["Open"] * 0.99)
            or not all(data["High"] >= data["Close"] * 0.99)
            or not all(data["Low"] <= data["Open"] * 1.01)
            or not all(data["Low"] <= data["Close"] * 1.01)
        ):
            return False

        return True

    except Exception as e:
        logger.error(f"Error en validate_market_data: {str(e)}")
        return False


def validate_and_fix_data(data: pd.DataFrame) -> pd.DataFrame:
    """Valida y corrige problemas en datos de mercado"""
    if data is None or data.empty:
        return pd.DataFrame()

    # Asegurar índice de tiempo
    if not isinstance(data.index, pd.DatetimeIndex):
        try:
            data.index = pd.to_datetime(data.index)
        except Exception as e:
            logger.warning(f"Error al convertir índice: {str(e)}")

    # Asegurar columnas OHLCV
    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in data.columns:
            if col == "Volume":
                data[col] = 0  # Valor por defecto para volumen
            elif "Close" in data.columns:
                # Si falta una columna crítica pero hay Close, usar Close como base
                if col == "Open":
                    data[col] = data["Close"].shift(1).fillna(data["Close"])
                elif col == "High":
                    data[col] = data["Close"] * 1.001  # Leve ajuste para High
                elif col == "Low":
                    data[col] = data["Close"] * 0.999  # Leve ajuste para Low
            else:
                # Último recurso, crear datos sintéticos
                data[col] = np.random.normal(100, 1, len(data))

    # Convertir a tipos numéricos
    for col in required_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    # Asegurarnos que High siempre es el máximo y Low siempre es el mínimo
    if all(col in data.columns for col in ["Open", "Close", "High", "Low"]):
        data["High"] = data[["Open", "Close", "High"]].max(axis=1)
        data["Low"] = data[["Open", "Close", "Low"]].min(axis=1)

    # Asegurar que el volumen es no-negativo
    if "Volume" in data.columns:
        data["Volume"] = data["Volume"].abs()

    # Rellenar valores NaN
    data = data.ffill().bfill().fillna(0)

    return data


# =================================================
# OBTENCIÓN DE DATOS DE MERCADO
# =================================================


def _get_api_key(key_name: str) -> str:
    """Obtiene clave de API desde secrets o variables de entorno"""
    try:
        # Intentar obtener de Streamlit secrets
        if hasattr(os, "streamlit"):
            import streamlit as st

            return st.secrets.get(key_name, os.environ.get(key_name.upper(), ""))
        # Intentar obtener de variables de entorno
        return os.environ.get(key_name.upper(), "")
    except Exception:
        return ""


def _generate_synthetic_data(symbol: str, periods: int = 180) -> pd.DataFrame:
    """Genera datos sintéticos robustos para fallback de interfaz"""
    try:
        # Crear datos determinísticos pero realistas basados en el símbolo
        seed_value = sum(ord(c) for c in symbol)
        np.random.seed(seed_value)

        # Asegurar un mínimo de períodos para evitar advertencias de datos insuficientes
        min_periods = max(periods, 250)  # Al menos 250 días para cubrir SMA200

        # Fechas para los días solicitados hasta hoy
        end_date = datetime.now()
        start_date = end_date - timedelta(days=min_periods)
        dates = pd.date_range(start=start_date, end=end_date, freq="D")

        # Precio base variable según símbolo
        base_price = 100 + (seed_value % 900)

        # Generar precios con tendencia y volatilidad realista
        prices = []
        price = base_price

        # Volatilidad dependiente del símbolo
        volatility = 0.01 + (seed_value % 10) / 100
        trend = 0.0005 * ((seed_value % 10) - 5)  # Entre -0.0025 y +0.0025

        # Generar serie de precios con ciclos y patrones realistas
        for i in range(len(dates)):
            # Añadir ciclos y estacionalidad
            cycle1 = 0.001 * np.sin(i / 20)  # Ciclo de 20 días
            cycle2 = 0.002 * np.sin(i / 60)  # Ciclo de 60 días
            cycle3 = 0.003 * np.sin(i / 120)  # Ciclo de 120 días

            # Ruido aleatorio con tendencia
            noise = np.random.normal(trend, volatility)

            # Combinar todos los factores
            daily_change = noise + cycle1 + cycle2 + cycle3
            price *= 1 + daily_change
            prices.append(max(price, 0.01))  # Evitar precios negativos

        # Crear DataFrame OHLCV sintético
        df = pd.DataFrame(index=dates)
        df["Close"] = prices
        df["Open"] = [p * (1 - np.random.uniform(0, volatility)) for p in prices]
        df["High"] = [
            max(o, c) * (1 + np.random.uniform(0, volatility))
            for o, c in zip(df["Open"], df["Close"])
        ]
        df["Low"] = [
            min(o, c) * (1 - np.random.uniform(0, volatility))
            for o, c in zip(df["Open"], df["Close"])
        ]
        df["Volume"] = [int(1e6 * (1 + np.random.normal(0, 0.3))) for _ in prices]
        df["Adj Close"] = df["Close"]

        # Precalcular algunos indicadores técnicos básicos para evitar cálculos posteriores
        # SMA
        for period in [20, 50, 200]:
            df[f"SMA_{period}"] = df["Close"].rolling(window=period).mean()

        # RSI
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # Flag para identificar como sintético
        df.attrs["synthetic"] = True
        logger.info(
            f"Datos sintéticos robustos generados para {symbol} con {len(df)} períodos"
        )

        return df

    except Exception as e:
        logger.error(f"Error generando datos sintéticos: {str(e)}")

        # Crear un DataFrame mínimo para evitar errores
        df = pd.DataFrame(index=pd.date_range(end=datetime.now(), periods=250))
        df["Close"] = np.linspace(100, 110, 250)
        df["Open"] = df["Close"] * 0.99
        df["High"] = df["Close"] * 1.01
        df["Low"] = df["Open"] * 0.99
        df["Volume"] = 1000000
        df["Adj Close"] = df["Close"]

        # Añadir indicadores básicos
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["SMA_200"] = df["Close"].rolling(window=200).mean()
        df["RSI"] = 50  # Valor neutral
        df["MACD"] = 0
        df["MACD_signal"] = 0

        df.attrs["synthetic"] = True
        return df


def _get_alpha_vantage_data(symbol: str, interval: str = "1d") -> pd.DataFrame:
    """Obtiene datos desde Alpha Vantage como respaldo"""
    alpha_vantage_key = _get_api_key("alpha_vantage_api_key")
    if not alpha_vantage_key:
        logger.warning("Alpha Vantage API key no disponible")
        return None

    try:
        # Mapear intervalo
        av_function = "TIME_SERIES_DAILY"
        av_interval = None

        if interval in ["1m", "5m", "15m", "30m", "60m", "1h"]:
            av_function = "TIME_SERIES_INTRADAY"
            av_interval = (
                interval.replace("m", "min")
                .replace("h", "min")
                .replace("60min", "60min")
            )

        # Construir URL
        url_params = f"&interval={av_interval}" if av_interval else ""
        url = f"https://www.alphavantage.co/query?function={av_function}&symbol={symbol}&outputsize=full{url_params}&apikey={alpha_vantage_key}"

        # Realizar solicitud con timeout
        response = requests.get(url, timeout=10)
        data = response.json()

        # Parsear respuesta
        time_series_key = next((k for k in data.keys() if "Time Series" in k), None)

        if not time_series_key or time_series_key not in data:
            raise ValueError(f"Datos no encontrados en Alpha Vantage para {symbol}")

        # Convertir a DataFrame
        time_series = data[time_series_key]
        df = pd.DataFrame.from_dict(time_series, orient="index")

        # Renombrar columnas
        column_map = {
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
            "5. volume": "Volume",
        }

        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})

        # Convertir a tipos numéricos
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Establecer índice de tiempo
        df.index = pd.to_datetime(df.index)

        # Añadir columna Adj Close si no existe
        if "Adj Close" not in df.columns:
            df["Adj Close"] = df["Close"]

        return df

    except Exception as e:
        logger.error(f"Error en Alpha Vantage para {symbol}: {str(e)}")
        return None


def _get_finnhub_data(symbol: str, resolution: str = "D") -> pd.DataFrame:
    """Obtiene datos desde Finnhub como respaldo adicional"""
    finnhub_key = _get_api_key("finnhub_api_key")
    if not finnhub_key:
        logger.warning("Finnhub API key no disponible")
        return None

    try:
        # Convertir período a resolución Finnhub
        resolution_map = {
            "1d": "D",
            "1h": "60",
            "30m": "30",
            "15m": "15",
            "5m": "5",
            "1m": "1",
        }
        finnhub_resolution = resolution_map.get(resolution, "D")

        # Calcular fechas (unix timestamp)
        end_time = int(time.time())
        # 6 meses de datos
        start_time = end_time - (180 * 24 * 60 * 60)

        # Construir URL
        url = f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution={finnhub_resolution}&from={start_time}&to={end_time}&token={finnhub_key}"

        # Realizar solicitud
        response = requests.get(url, timeout=10)
        data = response.json()

        # Verificar si hay datos válidos
        if data.get("s") != "ok":
            logger.warning(f"Finnhub no retornó datos válidos para {symbol}")
            return None

        # Construir DataFrame
        df = pd.DataFrame(
            {
                "Open": data["o"],
                "High": data["h"],
                "Low": data["l"],
                "Close": data["c"],
                "Volume": data["v"],
            },
            index=pd.to_datetime([datetime.fromtimestamp(ts) for ts in data["t"]]),
        )

        # Añadir Adj Close
        df["Adj Close"] = df["Close"]

        return df

    except Exception as e:
        logger.error(f"Error en Finnhub para {symbol}: {str(e)}")
        return None


def _get_marketstack_data(symbol: str) -> pd.DataFrame:
    """Obtiene datos desde MarketStack como otra fuente alternativa"""
    marketstack_key = _get_api_key("marketstack_api_key")
    if not marketstack_key:
        logger.warning("MarketStack API key no disponible")
        return None

    try:
        # Calcular fechas
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

        # Construir URL
        url = f"http://api.marketstack.com/v1/eod?access_key={marketstack_key}&symbols={symbol}&date_from={start_date}&date_to={end_date}&limit=1000"

        # Realizar solicitud
        response = requests.get(url, timeout=10)
        data = response.json()

        # Verificar datos válidos
        if "data" not in data or not data["data"]:
            logger.warning(f"MarketStack no retornó datos válidos para {symbol}")
            return None

        # Construir DataFrame
        df = pd.DataFrame(data["data"])

        # Convertir columnas y formato
        df = df.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
                "adj_close": "Adj Close",
                "date": "Date",
            }
        )

        # Establecer fecha como índice
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")

        # Invertir orden para tener el más reciente al final
        df = df.sort_index()

        return df

    except Exception as e:
        logger.error(f"Error en MarketStack para {symbol}: {str(e)}")
        return None


def fetch_market_data(
    symbol: str, period: str = "6mo", interval: str = "1d"
) -> pd.DataFrame:
    """
    Obtiene datos de mercado con múltiples fallbacks y validación.

    Args:
        symbol (str): Símbolo de la acción o ETF
        period (str): Período de tiempo ('1d', '1mo', '3mo', '6mo', '1y', '2y', '5y')
        interval (str): Intervalo de velas ('1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo')

    Returns:
        pd.DataFrame: DataFrame con datos OHLCV
    """
    # Clave de caché
    cache_key = f"market_data_{symbol}_{period}_{interval}"

    # Verificar caché
    cached_data = _data_cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Control de frecuencia de solicitudes
    if not _data_cache.can_request(symbol):
        logger.info(
            f"Limitando solicitudes para {symbol}, retornando últimos datos conocidos o sintéticos"
        )
        # Buscar cualquier dato previo para este símbolo
        for k, v in _data_cache.cache.items():
            if symbol in k and k.startswith("market_data_"):
                return v[1]  # v[1] contiene los datos, v[0] el timestamp
        # Si no hay datos previos, generar sintéticos
        synthetic_data = _generate_synthetic_data(symbol)
        _data_cache.set(cache_key, synthetic_data)
        return synthetic_data

    try:
        # Intentar obtener datos con yfinance
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)

        # Validar datos obtenidos
        if not validate_market_data(data):
            logger.warning(
                f"Datos inválidos para {symbol} en yfinance, intentando fuentes alternativas"
            )

            # Intentar con Alpha Vantage
            data = _get_alpha_vantage_data(symbol, interval)

            # Si Alpha Vantage falla, intentar con Finnhub
            if data is None or not validate_market_data(data):
                data = _get_finnhub_data(symbol, interval)

                # Si Finnhub falla, intentar con MarketStack
                if data is None or not validate_market_data(data):
                    data = _get_marketstack_data(symbol)

                    # Si todo falla, generar datos sintéticos
                    if data is None or not validate_market_data(data):
                        logger.warning(
                            f"Todas las fuentes fallaron para {symbol}, generando datos sintéticos"
                        )
                        data = _generate_synthetic_data(symbol)

        # Corrección final de datos
        data = validate_and_fix_data(data)

        # Guardar en caché
        _data_cache.set(cache_key, data)
        return data

    except Exception as e:
        logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
        traceback.print_exc()

        # Intentar todas las fuentes alternativas secuencialmente
        for data_source in [
            lambda: _get_alpha_vantage_data(symbol, interval),
            lambda: _get_finnhub_data(symbol, interval),
            lambda: _get_marketstack_data(symbol),
            lambda: _generate_synthetic_data(symbol),
        ]:
            try:
                data = data_source()
                if data is not None and not data.empty:
                    data = validate_and_fix_data(data)
                    _data_cache.set(cache_key, data)
                    return data
            except Exception as source_error:
                logger.error(f"Error en fuente alternativa: {str(source_error)}")
                continue

        # Si todo falla, retornar DataFrame vacío
        return pd.DataFrame()


# =================================================
# ESTRATEGIAS DE TRADING
# =================================================


class OptionsParameterManager:
    """Gestiona parámetros para trading de opciones basados en categoría de activo"""

    def __init__(self):
        self.options_params = {
            # Índices
            "SPY": {
                "costo_strike": "$0.25-$0.30",
                "volumen_min": "20M",
                "distance_spot_strike": "10 puntos",
            },
            "QQQ": {
                "costo_strike": "$0.25-$0.30",
                "volumen_min": "20M",
                "distance_spot_strike": "10 puntos",
            },
            "DIA": {
                "costo_strike": "$0.30-$0.40",
                "volumen_min": "5M",
                "distance_spot_strike": "8-12 puntos",
            },
            "IWM": {
                "costo_strike": "$0.30-$0.40",
                "volumen_min": "5M",
                "distance_spot_strike": "5-8 puntos",
            },
            "EFA": {
                "costo_strike": "$0.20-$0.30",
                "volumen_min": "3M",
                "distance_spot_strike": "3-5 puntos",
            },
            "VWO": {
                "costo_strike": "$0.20-$0.30",
                "volumen_min": "2M",
                "distance_spot_strike": "2-4 puntos",
            },
            "IYR": {
                "costo_strike": "$0.25-$0.35",
                "volumen_min": "2M",
                "distance_spot_strike": "3-5 puntos",
            },
            "XLE": {
                "costo_strike": "$0.30-$0.40",
                "volumen_min": "3M",
                "distance_spot_strike": "4-6 puntos",
            },
            "XLF": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "5M",
                "distance_spot_strike": "2-3 puntos",
            },
            "XLV": {
                "costo_strike": "$0.25-$0.35",
                "volumen_min": "3M",
                "distance_spot_strike": "3-5 puntos",
            },
            # Tecnología
            "AAPL": {
                "costo_strike": "$0.45-$0.80",
                "volumen_min": "20-25M",
                "distance_spot_strike": "2-4 puntos",
            },
            "MSFT": {
                "costo_strike": "$0.50-$0.85",
                "volumen_min": "15M",
                "distance_spot_strike": "3-5 puntos",
            },
            "GOOGL": {
                "costo_strike": "$0.80-$1.20",
                "volumen_min": "10M",
                "distance_spot_strike": "15-20 puntos",
            },
            "AMZN": {
                "costo_strike": "$0.60-$0.80",
                "volumen_min": "16M",
                "distance_spot_strike": "7-8 puntos",
            },
            "TSLA": {
                "costo_strike": "$2.50",
                "volumen_min": "15M",
                "distance_spot_strike": "8-10 puntos",
            },
            "NVDA": {
                "costo_strike": "$0.80-$1.20",
                "volumen_min": "12M",
                "distance_spot_strike": "10-15 puntos",
            },
            "META": {
                "costo_strike": "$0.45-$0.80",
                "volumen_min": "3M",
                "distance_spot_strike": "20-25 puntos",
            },
            "NFLX": {
                "costo_strike": "$1.50-$2.50",
                "volumen_min": "1M",
                "distance_spot_strike": "12-15 puntos",
            },
            "PYPL": {
                "costo_strike": "$0.40-$0.60",
                "volumen_min": "3M",
                "distance_spot_strike": "5-8 puntos",
            },
            "CRM": {
                "costo_strike": "$0.50-$0.70",
                "volumen_min": "2M",
                "distance_spot_strike": "8-12 puntos",
            },
            # Finanzas
            "JPM": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "8M",
                "distance_spot_strike": "3-5 puntos",
            },
            "BAC": {
                "costo_strike": "$0.10-$0.20",
                "volumen_min": "10M",
                "distance_spot_strike": "1-2 puntos",
            },
            "WFC": {
                "costo_strike": "$0.20-$0.35",
                "volumen_min": "5M",
                "distance_spot_strike": "2-3 puntos",
            },
            "C": {
                "costo_strike": "$0.20-$0.35",
                "volumen_min": "5M",
                "distance_spot_strike": "2-3 puntos",
            },
            "GS": {
                "costo_strike": "$0.80-$1.20",
                "volumen_min": "2M",
                "distance_spot_strike": "10-15 puntos",
            },
            "MS": {
                "costo_strike": "$0.25-$0.40",
                "volumen_min": "3M",
                "distance_spot_strike": "2-4 puntos",
            },
            "V": {
                "costo_strike": "$0.40-$0.60",
                "volumen_min": "4M",
                "distance_spot_strike": "4-6 puntos",
            },
            "MA": {
                "costo_strike": "$0.50-$0.70",
                "volumen_min": "3M",
                "distance_spot_strike": "5-8 puntos",
            },
            "AXP": {
                "costo_strike": "$0.40-$0.60",
                "volumen_min": "2M",
                "distance_spot_strike": "4-6 puntos",
            },
            "BLK": {
                "costo_strike": "$1.00-$1.50",
                "volumen_min": "1M",
                "distance_spot_strike": "15-20 puntos",
            },
            # Materias Primas y ETFs
            "GLD": {
                "costo_strike": "$0.60-$0.80",
                "volumen_min": "2M",
                "distance_spot_strike": "2-4 puntos",
            },
            "SLV": {
                "costo_strike": "$0.10-$0.20",
                "volumen_min": "10M",
                "distance_spot_strike": "1-2 puntos",
            },
            "USO": {
                "costo_strike": "$0.10-$0.20",
                "volumen_min": "1M",
                "distance_spot_strike": "2-3 puntos",
            },
            "BITO": {
                "costo_strike": "$0.20-$0.30",
                "volumen_min": "2M",
                "distance_spot_strike": "2-3 puntos",
            },
            "GBTC": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "2M",
                "distance_spot_strike": "1-2 puntos",
            },
            # Energía
            "XOM": {
                "costo_strike": "$0.60-$0.80",
                "volumen_min": "4M",
                "distance_spot_strike": "3-5 puntos",
            },
            "CVX": {
                "costo_strike": "$0.60-$0.80",
                "volumen_min": "2M",
                "distance_spot_strike": "3-5 puntos",
            },
            "SHEL": {
                "costo_strike": "$0.40-$0.60",
                "volumen_min": "2M",
                "distance_spot_strike": "3-4 puntos",
            },
            "TTE": {
                "costo_strike": "$0.40-$0.60",
                "volumen_min": "1M",
                "distance_spot_strike": "3-4 puntos",
            },
            "COP": {
                "costo_strike": "$0.35-$0.55",
                "volumen_min": "2M",
                "distance_spot_strike": "2-4 puntos",
            },
            "EOG": {
                "costo_strike": "$0.50-$0.70",
                "volumen_min": "4M",
                "distance_spot_strike": "3-5 puntos",
            },
            "PXD": {
                "costo_strike": "$0.45-$0.65",
                "volumen_min": "2.5M",
                "distance_spot_strike": "3-5 puntos",
            },
            "DVN": {
                "costo_strike": "$0.55-$0.75",
                "volumen_min": "3.5M",
                "distance_spot_strike": "3-5 puntos",
            },
            "MPC": {
                "costo_strike": "$0.50-$0.70",
                "volumen_min": "3M",
                "distance_spot_strike": "3-5 puntos",
            },
            "PSX": {
                "costo_strike": "$0.50-$0.70",
                "volumen_min": "2.5M",
                "distance_spot_strike": "3-5 puntos",
            },
            # Salud
            "JNJ": {
                "costo_strike": "$0.40-$0.60",
                "volumen_min": "6M",
                "distance_spot_strike": "4-6 puntos",
            },
            "UNH": {
                "costo_strike": "$1.00-$1.50",
                "volumen_min": "5M",
                "distance_spot_strike": "10-15 puntos",
            },
            "PFE": {
                "costo_strike": "$0.20-$0.35",
                "volumen_min": "5M",
                "distance_spot_strike": "2-3 puntos",
            },
            "MRK": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "4M",
                "distance_spot_strike": "3-5 puntos",
            },
            "ABBV": {
                "costo_strike": "$0.40-$0.60",
                "volumen_min": "3M",
                "distance_spot_strike": "4-6 puntos",
            },
            "LLY": {
                "costo_strike": "$1.20-$1.80",
                "volumen_min": "2.5M",
                "distance_spot_strike": "10-15 puntos",
            },
            "AMGN": {
                "costo_strike": "$0.50-$0.70",
                "volumen_min": "2.5M",
                "distance_spot_strike": "5-8 puntos",
            },
            "BMY": {
                "costo_strike": "$0.25-$0.45",
                "volumen_min": "3M",
                "distance_spot_strike": "2-4 puntos",
            },
            "GILD": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "2.5M",
                "distance_spot_strike": "3-5 puntos",
            },
            "TMO": {
                "costo_strike": "$0.70-$1.00",
                "volumen_min": "1.5M",
                "distance_spot_strike": "6-10 puntos",
            },
            # Consumo Discrecional
            "MCD": {
                "costo_strike": "$0.40-$0.60",
                "volumen_min": "3.5M",
                "distance_spot_strike": "4-6 puntos",
            },
            "SBUX": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "4M",
                "distance_spot_strike": "3-5 puntos",
            },
            "NKE": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "3.5M",
                "distance_spot_strike": "2-4 puntos",
            },
            "TGT": {
                "costo_strike": "$0.40-$0.60",
                "volumen_min": "2.5M",
                "distance_spot_strike": "3-5 puntos",
            },
            "HD": {
                "costo_strike": "$0.60-$0.80",
                "volumen_min": "2.5M",
                "distance_spot_strike": "5-8 puntos",
            },
            "LOW": {
                "costo_strike": "$0.50-$0.70",
                "volumen_min": "2M",
                "distance_spot_strike": "4-6 puntos",
            },
            "TJX": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "2.5M",
                "distance_spot_strike": "3-5 puntos",
            },
            "ROST": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "1.5M",
                "distance_spot_strike": "3-5 puntos",
            },
            "CMG": {
                "costo_strike": "$0.80-$1.20",
                "volumen_min": "1.5M",
                "distance_spot_strike": "8-12 puntos",
            },
            "DHI": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "1.5M",
                "distance_spot_strike": "3-5 puntos",
            },
            # Cripto ETFs
            "ETHE": {
                "costo_strike": "$0.25-$0.40",
                "volumen_min": "1M",
                "distance_spot_strike": "3-5 puntos",
            },
            "ARKW": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "750K",
                "distance_spot_strike": "4-6 puntos",
            },
            "BLOK": {
                "costo_strike": "$0.20-$0.35",
                "volumen_min": "1.5M",
                "distance_spot_strike": "2-4 puntos",
            },
            # Materias Primas
            "UNG": {
                "costo_strike": "$0.20-$0.35",
                "volumen_min": "2M",
                "distance_spot_strike": "2-4 puntos",
            },
            "CORN": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "750K",
                "distance_spot_strike": "1-3 puntos",
            },
            "SOYB": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "750K",
                "distance_spot_strike": "1-3 puntos",
            },
            "WEAT": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "750K",
                "distance_spot_strike": "1-3 puntos",
            },
            # Bonos
            "AGG": {
                "costo_strike": "$0.10-$0.20",
                "volumen_min": "1.5M",
                "distance_spot_strike": "1-2 puntos",
            },
            "BND": {
                "costo_strike": "$0.10-$0.20",
                "volumen_min": "1M",
                "distance_spot_strike": "1-2 puntos",
            },
            "IEF": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "1M",
                "distance_spot_strike": "1-2 puntos",
            },
            "TLT": {
                "costo_strike": "$0.20-$0.30",
                "volumen_min": "2.5M",
                "distance_spot_strike": "2-3 puntos",
            },
            "LQD": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "1.5M",
                "distance_spot_strike": "1-2 puntos",
            },
            "HYG": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "2.5M",
                "distance_spot_strike": "1-2 puntos",
            },
            "JNK": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "1.5M",
                "distance_spot_strike": "1-2 puntos",
            },
            "TIP": {
                "costo_strike": "$0.10-$0.20",
                "volumen_min": "1M",
                "distance_spot_strike": "1-2 puntos",
            },
            "MUB": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "1M",
                "distance_spot_strike": "1-2 puntos",
            },
            "SHY": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "1M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            # Inmobiliario
            "VNQ": {
                "costo_strike": "$0.25-$0.40",
                "volumen_min": "2M",
                "distance_spot_strike": "2-4 puntos",
            },
            "XLRE": {
                "costo_strike": "$0.20-$0.35",
                "volumen_min": "1.5M",
                "distance_spot_strike": "2-3 puntos",
            },
            "REIT": {
                "costo_strike": "$0.20-$0.35",
                "volumen_min": "1M",
                "distance_spot_strike": "2-3 puntos",
            },
            "HST": {
                "costo_strike": "$0.15-$0.25",
                "volumen_min": "1M",
                "distance_spot_strike": "1-2 puntos",
            },
            "EQR": {
                "costo_strike": "$0.20-$0.35",
                "volumen_min": "1M",
                "distance_spot_strike": "2-3 puntos",
            },
            "AVB": {
                "costo_strike": "$0.30-$0.45",
                "volumen_min": "750K",
                "distance_spot_strike": "3-5 puntos",
            },
            "PLD": {
                "costo_strike": "$0.25-$0.40",
                "volumen_min": "1M",
                "distance_spot_strike": "2-4 puntos",
            },
            "SPG": {
                "costo_strike": "$0.30-$0.45",
                "volumen_min": "1M",
                "distance_spot_strike": "3-5 puntos",
            },
            "AMT": {
                "costo_strike": "$0.35-$0.50",
                "volumen_min": "1M",
                "distance_spot_strike": "3-5 puntos",
            },
            # Volatilidad
            "VXX": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "3M",
                "distance_spot_strike": "4-8 puntos",
            },
            "UVXY": {
                "costo_strike": "$0.35-$0.55",
                "volumen_min": "4M",
                "distance_spot_strike": "5-10 puntos",
            },
            "SVXY": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "2M",
                "distance_spot_strike": "4-8 puntos",
            },
            "VIXY": {
                "costo_strike": "$0.30-$0.50",
                "volumen_min": "2.5M",
                "distance_spot_strike": "4-8 puntos",
            },
            # Forex
            "EURUSD": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "30M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "USDJPY": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "25M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "GBPUSD": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "20M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "USDCHF": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "15M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "AUDUSD": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "15M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "USDCAD": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "15M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "NZDUSD": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "10M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "EURGBP": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "15M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "EURJPY": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "20M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "GBPJPY": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "15M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "USDCNH": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "10M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "USDINR": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "8M",
                "distance_spot_strike": "0.5-1 puntos",
            },
            "USDTRY": {
                "costo_strike": "$0.05-$0.15",
                "volumen_min": "8M",
                "distance_spot_strike": "0.5-1 puntos",
            },
        }

        # Recomendaciones generales
        self.general_recommendations = {
            "volumen": {
                "alto": ">10M: Óptimo para day trading",
                "medio": "3-10M: Aceptable para swing trading",
                "bajo": "<3M: Requiere precaución",
            },
            "costo_strike": {
                "bajo": "<$0.30: Ideal para estrategias de alta frecuencia",
                "medio": "$0.30-$0.80: Balanced risk/reward",
                "alto": ">$0.80: Requiere mayor capital, menor frecuencia",
            },
            "distance": {
                "corta": "1-5 puntos: Mayor probabilidad, menor retorno",
                "media": "5-10 puntos: Balance riesgo/retorno",
                "larga": ">10 puntos: Mayor retorno potencial, menor probabilidad",
            },
            "volatilidad": {
                "alta": "VIX > 25: Aumentar distance en 20%, considerar spreads",
                "baja": "VIX < 15: Reducir distance en 10%, favorecer direccionales",
            },
            "risk_management": [
                "Máximo 10% del capital por trade",
                "Stop Loss en 50% del premium pagado",
                "Take Profit en 100% del premium pagado",
                "Evitar hold overnight sin hedge",
                "Usar siempre options chain con mayor liquidez",
            ],
        }

        # Estrategias por categoría
        self.strategies_catalog = {
            "alcistas": [
                {
                    "name": "Promedio Móvil de 40 (Timeframe Horario)",
                    "setup": "SMA(20) > SMA(40), tocar SMA(40), ruptura línea bajista",
                    "timeframe": "Horario",
                    "confirmacion": "Vela alcista, RSI>40, MACD cruzando al alza",
                    "stop_loss": "Mínimo de vela de entrada",
                    "indicators": {
                        "required": ["SMA20", "SMA40", "RSI", "MACD"],
                        "complementary": ["BB", "Volume_Profile"],
                    },
                    "rules": [
                        "SMA(20) > SMA(40) tendencia alcista",
                        "Tocar o acercarse al SMA(40)",
                        "Ruptura de línea bajista con vela alcista",
                        "Entrada después de 11:00 AM",
                        "Stop Loss: Mínimo de la vela de entrada",
                    ],
                },
                {
                    "name": "Caída Normal y Caída Fuerte (Timeframe Horario)",
                    "setup": "Caída y ruptura de línea bajista",
                    "timeframe": "Horario",
                    "confirmacion": "Vela fuerte con volumen, ATR elevado",
                    "stop_loss": "Por debajo del swing bajo previo",
                    "indicators": {
                        "required": ["SMA40", "ATR", "Stochastic_RSI"],
                        "complementary": ["VWAP", "OBV"],
                    },
                    "rules": [
                        "Caída Normal: No toca SMA(40)",
                        "Caída Fuerte: Supera SMA(40)",
                        "Ruptura de línea bajista",
                        "ATR > Media ATR 20 períodos",
                        "Stop Loss: Por debajo del swing bajo previo",
                    ],
                },
                {
                    "name": "Ruptura del Techo del Canal Bajista (Timeframe Horario)",
                    "setup": "Canal bajista identificado, ruptura de techo",
                    "timeframe": "Horario",
                    "confirmacion": "Vela fuerte, ADX>25",
                    "stop_loss": "50% del último swing",
                    "indicators": {
                        "required": ["SMA20", "SMA40", "SMA200", "RSI", "ADX"],
                        "complementary": ["Ichimoku", "MFI"],
                    },
                    "rules": [
                        "Identificar canal con mínimo 2 puntos",
                        "SMA(40) > SMA(20) confirma canal bajista",
                        "Ruptura con vela alcista",
                        "ADX > 25 para confirmar fuerza",
                        "Stop Loss: 50% del último swing",
                    ],
                },
                {
                    "name": "Gap Normal al Alza",
                    "setup": "Gap alcista en pre-market, primeras velas verdes",
                    "timeframe": "Horario",
                    "confirmacion": "Velas 10-11AM verdes, volumen >150% promedio",
                    "stop_loss": "Por debajo del VWAP",
                    "indicators": {
                        "required": ["Gap_Analysis", "Volume", "VWAP"],
                        "complementary": ["Market_Profile", "Cumulative_Delta"],
                    },
                    "rules": [
                        "Gap alcista en pre-market",
                        "Primeras velas 10-11 AM verdes",
                        "Volumen > 150% promedio",
                        "VWAP como soporte",
                        "Stop Loss: Por debajo del VWAP",
                    ],
                },
            ],
            "bajistas": [
                {
                    "name": "Primera Vela Roja de Apertura",
                    "setup": "Vela roja 10AM en zona de resistencia, RSI>70",
                    "timeframe": "Horario",
                    "confirmacion": "Volumen alto, MACD divergente",
                    "stop_loss": "Por encima del high de apertura",
                    "indicators": {
                        "required": ["10AM_Candle", "RSI", "MACD_Divergence"],
                        "complementary": ["Volume_Profile", "PMO"],
                    },
                    "rules": [
                        "Vela roja en apertura",
                        "Zona de techo/resistencia",
                        "RSI > 70",
                        "Volumen alto",
                        "Stop Loss: Por encima del high de apertura",
                    ],
                },
                {
                    "name": "Ruptura de Piso del Gap",
                    "setup": "Gap identificado, ruptura con vela roja",
                    "timeframe": "Horario",
                    "confirmacion": "Confirmación con volumen",
                    "stop_loss": "Por encima del gap high",
                    "indicators": {
                        "required": ["Gap_Analysis", "Support_Resistance", "Momentum"],
                        "complementary": ["Market_Profile", "Cumulative_Volume_Delta"],
                    },
                    "rules": [
                        "Gap identificado",
                        "Vela verde 10 AM",
                        "Ruptura con vela roja",
                        "Confirmación con volumen",
                        "Stop Loss: Por encima del gap high",
                    ],
                },
                {
                    "name": "Modelo 4 Pasos",
                    "setup": "Canal bajista, techo, vela verde borrada, ruptura",
                    "timeframe": "Horario",
                    "confirmacion": "Vela fuerte con volumen",
                    "stop_loss": "Por encima de la vela verde borrada",
                    "indicators": {
                        "required": [
                            "Bearish_Channel",
                            "RSI",
                            "Stochastic",
                            "MACD_Histogram",
                        ],
                        "complementary": ["Bollinger_Bands", "Volume_Analysis"],
                    },
                    "rules": [
                        "Canal bajista activo",
                        "Zona de techo/resistencia",
                        "Vela verde borrada",
                        "Ruptura de soporte",
                        "Stop Loss: Por encima de la vela verde borrada",
                    ],
                },
                {
                    "name": "Hanger en Diario",
                    "setup": "Hanger en zona de techo, SMA distantes",
                    "timeframe": "Diario",
                    "confirmacion": "Entrada 3:55-3:58PM",
                    "stop_loss": "Por encima del high del Hanger",
                    "indicators": {
                        "required": ["Candlestick_Pattern", "SMA100", "SMA200"],
                        "complementary": ["ATR", "Elder_Force_Index"],
                    },
                    "rules": [
                        "Formación de Hanger",
                        "Zona de techo",
                        "SMA distantes",
                        "Entrada 3:55-3:58 PM",
                        "Stop Loss: Por encima del high del Hanger",
                    ],
                },
            ],
        }

    def get_symbol_params(self, symbol: str) -> Dict:
        """Obtiene parámetros específicos para un símbolo"""
        return self.options_params.get(symbol.upper(), {})

    def get_strategy_recommendations(self, trend_direction: str) -> List[Dict]:
        """Obtiene estrategias recomendadas según tendencia"""
        if trend_direction == "ALCISTA":
            return self.strategies_catalog["alcistas"]
        elif trend_direction == "BAJISTA":
            return self.strategies_catalog["bajistas"]
        else:
            # Para tendencia neutral o desconocida, devolver todas
            return (
                self.strategies_catalog["alcistas"]
                + self.strategies_catalog["bajistas"]
            )

    def get_volatility_adjustments(self, vix_level: float) -> Dict:
        """Obtiene ajustes recomendados según nivel de VIX"""
        if vix_level > 25:
            return {
                "category": "alta",
                "description": self.general_recommendations["volatilidad"]["alta"],
                "adjustments": [
                    "Aumentar Distance Spot-Strike en 20%",
                    "Considerar spreads en lugar de opciones simples",
                    "Reducir tamaño de posición",
                ],
            }
        elif vix_level < 15:
            return {
                "category": "baja",
                "description": self.general_recommendations["volatilidad"]["baja"],
                "adjustments": [
                    "Reducir Distance Spot-Strike en 10%",
                    "Favorecer estrategias direccionales",
                    "Aumentar duración de trades",
                ],
            }
        else:
            return {
                "category": "normal",
                "description": "Volatilidad en rango normal",
                "adjustments": [
                    "Parámetros estándar",
                    "Balance entre opciones y spreads",
                    "Tamaño de posición estándar",
                ],
            }


# =================================================
# ANÁLISIS TÉCNICO Y CUANTITATIVO
# =================================================


class TechnicalAnalyzer:
    """Analizador técnico avanzado con manejo profesional de indicadores"""

    def __init__(self, data=None):
        """Inicializa el analizador con validación de datos"""
        self.data = data
        self.indicators = None
        self.signals = {}
        self.options_manager = OptionsParameterManager()

    def calculate_indicators(self, data=None):
        """Calcula indicadores técnicos con validación avanzada"""
        try:
            # Usar datos proporcionados o los de la instancia
            df = data.copy() if data is not None else self.data.copy()

            if df is None or df.empty:
                raise ValueError("No hay datos disponibles")

            # Verificar si tenemos suficientes datos para calcular indicadores
            if (
                len(df) < 15
            ):  # Necesitamos al menos 15 puntos para la mayoría de indicadores
                logger.warning(
                    f"Datos insuficientes para calcular indicadores: solo {len(df)} filas disponibles"
                )
                return df  # Devolver los datos sin procesar si son insuficientes

            # Validar y preparar precios
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            if not all(col in df.columns for col in required_cols):
                raise ValueError("Faltan columnas requeridas")

            # Convertir a float con validación
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            if df["Close"].isnull().all():
                raise ValueError("No hay precios válidos")

            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            volume = df["Volume"]

            # ===== INDICADORES DE TENDENCIA =====

            # MACD
            macd = MACD(close)
            df["MACD"] = macd.macd()
            df["MACD_Signal"] = macd.macd_signal()
            df["MACD_Hist"] = macd.macd_diff()

            # Medias Móviles con validación
            for period in [20, 40, 50, 100, 200]:
                if len(df) >= period:
                    df[f"SMA_{period}"] = SMAIndicator(
                        close, window=period
                    ).sma_indicator()
                    df[f"EMA_{period}"] = EMAIndicator(
                        close, window=period
                    ).ema_indicator()

            # ===== INDICADORES DE MOMENTUM =====

            # RSI
            if len(df) >= 14:  # Período mínimo para RSI
                rsi = RSIIndicator(close)
                df["RSI"] = rsi.rsi()

            # Estocástico
            if len(df) >= 14:
                stoch = StochasticOscillator(high, low, close)
                df["Stoch_K"] = stoch.stoch()
                df["Stoch_D"] = stoch.stoch_signal()

                # Estocástico RSI
                if "RSI" in df.columns:
                    stoch_rsi = StochasticOscillator(
                        pd.Series(df["RSI"]), pd.Series(df["RSI"]), pd.Series(df["RSI"])
                    )
                    df["Stoch_RSI"] = stoch_rsi.stoch()

            # ===== INDICADORES DE VOLATILIDAD =====

            # Bandas de Bollinger
            bb = BollingerBands(close)
            df["BB_High"] = bb.bollinger_hband()
            df["BB_Mid"] = bb.bollinger_mavg()
            df["BB_Low"] = bb.bollinger_lband()
            df["BB_Width"] = (df["BB_High"] - df["BB_Low"]) / df["BB_Mid"]

            # ATR para volatilidad - Añadir verificación de longitud
            if len(df) >= 14:  # ATR suele usar window=14 por defecto
                try:
                    atr = AverageTrueRange(high, low, close)
                    df["ATR"] = atr.average_true_range()

                    # ATR relativo (solo si pudimos calcular ATR)
                    if len(df) >= 20 and "ATR" in df.columns:
                        df["ATR_Pct"] = df["ATR"] / close * 100
                        df["ATR_Ratio"] = (
                            df["ATR"] / df["ATR"].rolling(window=20).mean()
                        )
                except Exception as e:
                    logger.warning(f"No se pudo calcular ATR: {str(e)}")
                    # Crear ATR sintético simple para evitar errores
                    df["ATR"] = (high - low).rolling(window=min(14, len(df) - 1)).mean()
            else:
                # En datasets muy pequeños, usar un cálculo básico
                df["ATR"] = (high - low).mean()

            # ===== INDICADORES DE VOLUMEN =====

            # Media móvil de volumen
            vol_window = min(20, len(df) - 1)  # Evitar window > len(df)
            df["Volume_SMA"] = SMAIndicator(volume, window=vol_window).sma_indicator()
            df["Volume_Ratio"] = volume / df["Volume_SMA"]

            # VWAP
            try:
                vwap = VolumeWeightedAveragePrice(high, low, close, volume)
                df["VWAP"] = vwap.volume_weighted_average_price()
            except Exception as e:
                logger.warning(f"Error calculando VWAP: {str(e)}")

            # OBV (On-Balance Volume)
            try:
                obv = OnBalanceVolumeIndicator(close, volume)
                df["OBV"] = obv.on_balance_volume()
            except Exception as e:
                logger.warning(f"Error calculando OBV: {str(e)}")
                # Calcularlo manualmente
                df["OBV"] = 0
                for i in range(1, len(df)):
                    if df["Close"].iloc[i] > df["Close"].iloc[i - 1]:
                        df.loc[df.index[i], "OBV"] = (
                            df["OBV"].iloc[i - 1] + df["Volume"].iloc[i]
                        )
                    elif df["Close"].iloc[i] < df["Close"].iloc[i - 1]:
                        df.loc[df.index[i], "OBV"] = (
                            df["OBV"].iloc[i - 1] - df["Volume"].iloc[i]
                        )
                    else:
                        df.loc[df.index[i], "OBV"] = df["OBV"].iloc[i - 1]

            # ===== INDICADORES DE GAP =====

            # Detectar gaps
            df["Gap"] = 0.0
            for i in range(1, len(df)):
                if df.index[i].date() > df.index[i - 1].date() + timedelta(days=1):
                    # Salto en fechas (datos no consecutivos), no es un gap
                    continue

                # Gap alcista
                if df["Low"].iloc[i] > df["High"].iloc[i - 1]:
                    gap_value = (df["Low"].iloc[i] / df["High"].iloc[i - 1] - 1) * 100
                    df.loc[df.index[i], "Gap"] = gap_value
                # Gap bajista
                elif df["High"].iloc[i] < df["Low"].iloc[i - 1]:
                    gap_value = (df["High"].iloc[i] / df["Low"].iloc[i - 1] - 1) * 100
                    df.loc[df.index[i], "Gap"] = gap_value

            # ===== INDICADORES DE PATRÓN DE VELAS =====

            # Detectar patrón Hammer/Hanger
            df["Hammer"] = False
            df["Hanger"] = False

            for i in range(len(df)):
                body_size = abs(df["Close"].iloc[i] - df["Open"].iloc[i])
                total_range = df["High"].iloc[i] - df["Low"].iloc[i]

                if total_range > 0:  # Evitar división por cero
                    upper_shadow = df["High"].iloc[i] - max(
                        df["Open"].iloc[i], df["Close"].iloc[i]
                    )
                    lower_shadow = (
                        min(df["Open"].iloc[i], df["Close"].iloc[i]) - df["Low"].iloc[i]
                    )

                    # Hammer: sombra inferior larga, sombra superior pequeña, cuerpo pequeño
                    if (
                        lower_shadow > 2 * body_size
                        and upper_shadow < 0.1 * total_range
                        and lower_shadow > 0.6 * total_range
                    ):

                        # Es un Hanger si está en una tendencia alcista
                        if (
                            i > 20
                            and df["Close"].iloc[i - 20 : i].mean()
                            < df["Close"].iloc[i]
                        ):
                            df.loc[df.index[i], "Hanger"] = True
                        # Es un Hammer si está en una tendencia bajista
                        elif (
                            i > 20
                            and df["Close"].iloc[i - 20 : i].mean()
                            > df["Close"].iloc[i]
                        ):
                            df.loc[df.index[i], "Hammer"] = True

            # Limpiar datos
            df = df.replace([np.inf, -np.inf], np.nan).dropna(how="all")

            # Guardar en la instancia
            self.indicators = df
            return df

        except Exception as e:
            logger.error(f"Error en calculate_indicators: {str(e)}")
            traceback.print_exc()
            return None

    def get_current_signals(self, data=None):
        """Obtiene señales actuales con validación robusta"""
        try:
            # Usar datos proporcionados, indicadores calculados, o calcular indicadores
            if data is not None:
                df = self.calculate_indicators(data)
            elif self.indicators is not None:
                df = self.indicators
            elif self.data is not None:
                df = self.calculate_indicators(self.data)
            else:
                raise ValueError("No hay datos de indicadores válidos")

            # Verificar si tenemos datos suficientes
            if df is None or len(df) < 2:
                logger.warning(
                    "Datos insuficientes para análisis, generando señal por defecto"
                )
                # Proporcionar una señal por defecto en lugar de fallar
                return {
                    "trend": {
                        "sma_20_50": "neutral",
                        "macd": "neutral",
                        "ema_trend": "neutral",
                        "sma_200": "neutral",
                    },
                    "momentum": {
                        "rsi": 50.0,
                        "rsi_condition": "neutral",
                        "rsi_trend": "neutral",
                        "stoch_k": 50.0,
                        "stoch_d": 50.0,
                        "stoch_trend": "neutral",
                    },
                    "volatility": {
                        "bb_width": 0.05,
                        "atr": 0.0,
                        "atr_pct": 0.0,
                        "price_position": "medio",
                        "volatility_state": "normal",
                    },
                    "volume": {
                        "trend": "neutral",
                        "ratio": 1.0,
                        "obv_trend": "neutral",
                        "vwap_position": "neutral",
                    },
                    "patterns": {
                        "gap": 0.0,
                        "gap_direction": "ninguno",
                        "hammer": False,
                        "hanger": False,
                    },
                    "overall": {
                        "signal": "neutral",
                        "confidence": "baja",
                        "score": 0.0,
                    },
                    "options": {
                        "direction": "NEUTRAL",
                        "confidence": "BAJA",
                        "timeframe": "INDEFINIDO",
                        "strategy": "Datos insuficientes",
                        "confidence_score": 0.0,
                    },
                }

            # Obtener datos con validación
            current = df.iloc[-1].copy() if not df.empty else pd.Series()
            previous = df.iloc[-2].copy() if len(df) > 1 else pd.Series()

            # Calcular promedios y referencias con verificación de existencia
            sma20_exists = "SMA_20" in df.columns
            sma50_exists = "SMA_50" in df.columns
            sma200_exists = "SMA_200" in df.columns

            sma_trend = False
            if sma20_exists and sma50_exists and not df.empty:
                sma20_value = current.get("SMA_20", None)
                sma50_value = current.get("SMA_50", None)
                if sma20_value is not None and sma50_value is not None:
                    sma_trend = sma20_value > sma50_value

            volume_trend = False
            if "Volume" in df.columns and "Volume_SMA" in df.columns and not df.empty:
                volume_value = current.get("Volume", None)
                volume_sma = current.get("Volume_SMA", None)
                if (
                    volume_value is not None
                    and volume_sma is not None
                    and volume_sma > 0
                ):
                    volume_trend = volume_value > volume_sma

            signals = {
                "trend": {
                    "sma_20_50": "alcista" if sma_trend else "bajista",
                    "macd": (
                        "alcista"
                        if current.get("MACD", 0) > current.get("MACD_Signal", 0)
                        else "bajista"
                    ),
                    "ema_trend": (
                        "alcista"
                        if (
                            "EMA_20" in df.columns
                            and "EMA_50" in df.columns
                            and current.get("EMA_20", 0) > current.get("EMA_50", 0)
                        )
                        else "bajista"
                    ),
                    "sma_200": (
                        "por_encima"
                        if (
                            "Close" in df.columns
                            and "SMA_200" in df.columns
                            and current.get("Close", 0) > current.get("SMA_200", 0)
                        )
                        else "por_debajo"
                    ),
                },
                "momentum": {
                    "rsi": float(current.get("RSI", 50)),
                    "rsi_condition": self._get_rsi_condition(current.get("RSI", 50)),
                    "rsi_trend": (
                        "alcista"
                        if (
                            "RSI" in df.columns
                            and current.get("RSI", 50) > previous.get("RSI", 50)
                        )
                        else "bajista"
                    ),
                    "stoch_k": float(current.get("Stoch_K", 50)),
                    "stoch_d": float(current.get("Stoch_D", 50)),
                    "stoch_trend": (
                        "alcista"
                        if (
                            "Stoch_K" in df.columns
                            and "Stoch_D" in df.columns
                            and current.get("Stoch_K", 0) > current.get("Stoch_D", 0)
                        )
                        else "bajista"
                    ),
                },
                "volatility": {
                    "bb_width": float(current.get("BB_Width", 0)),
                    "atr": float(current.get("ATR", 0)),
                    "atr_pct": float(current.get("ATR_Pct", 0)),
                    "price_position": self._get_price_position(current),
                    "volatility_state": self._get_volatility_state(current, df),
                },
                "volume": {
                    "trend": "alcista" if volume_trend else "bajista",
                    "ratio": float(current.get("Volume_Ratio", 1)),
                    "obv_trend": (
                        "alcista"
                        if (
                            "OBV" in df.columns
                            and previous.get("OBV", 0) < current.get("OBV", 0)
                        )
                        else "bajista"
                    ),
                    "vwap_position": (
                        "por_encima"
                        if (
                            "Close" in df.columns
                            and "VWAP" in df.columns
                            and current.get("Close", 0) > current.get("VWAP", 0)
                        )
                        else "por_debajo"
                    ),
                },
                "patterns": {
                    "gap": float(current.get("Gap", 0)),
                    "gap_direction": (
                        "alcista"
                        if current.get("Gap", 0) > 0
                        else "bajista" if current.get("Gap", 0) < 0 else "ninguno"
                    ),
                    "hammer": bool(current.get("Hammer", False)),
                    "hanger": bool(current.get("Hanger", False)),
                },
            }

            # Calcular señal agregada
            signals["overall"] = self._calculate_overall_signal(signals)

            # Calcular señales de opciones
            signals["options"] = self._analyze_options_strategy(signals)

            return signals

        except Exception as e:
            logger.error(f"Error en get_current_signals: {str(e)}")
            traceback.print_exc()

            # Proporcionar una señal por defecto en caso de error
            return {
                "trend": {
                    "sma_20_50": "neutral",
                    "macd": "neutral",
                    "ema_trend": "neutral",
                    "sma_200": "neutral",
                },
                "momentum": {
                    "rsi": 50.0,
                    "rsi_condition": "neutral",
                    "rsi_trend": "neutral",
                    "stoch_k": 50.0,
                    "stoch_d": 50.0,
                },
                "volatility": {
                    "bb_width": 0.05,
                    "atr": 0.0,
                    "atr_pct": 0.0,
                    "price_position": "medio",
                    "volatility_state": "normal",
                },
                "volume": {
                    "trend": "neutral",
                    "ratio": 1.0,
                    "obv_trend": "neutral",
                    "vwap_position": "neutral",
                },
                "patterns": {
                    "gap": 0.0,
                    "gap_direction": "ninguno",
                    "hammer": False,
                    "hanger": False,
                },
                "overall": {"signal": "neutral", "confidence": "baja", "score": 0.0},
                "options": {
                    "direction": "NEUTRAL",
                    "confidence": "BAJA",
                    "timeframe": "INDEFINIDO",
                    "strategy": "Error en análisis",
                    "confidence_score": 0.0,
                },
            }

    def _analyze_options_strategy(self, signals):
        """Recomienda estrategia de opciones basada en señales"""
        try:
            # Determinar dirección básica
            direction = (
                "CALL"
                if signals["overall"]["signal"] in ["compra", "compra_fuerte"]
                else "PUT"
            )

            # Calcular nivel de confianza basado en la confluencia de señales
            confidence_factors = []

            # Factores para CALL (alcista)
            if direction == "CALL":
                if signals["trend"]["sma_20_50"] == "alcista":
                    confidence_factors.append(0.2)
                if signals["trend"]["macd"] == "alcista":
                    confidence_factors.append(0.15)
                if signals["trend"]["sma_200"] == "por_encima":
                    confidence_factors.append(0.25)
                if signals["momentum"]["rsi_condition"] == "sobrevendido":
                    confidence_factors.append(0.15)
                elif 40 <= signals["momentum"]["rsi"] <= 60:
                    confidence_factors.append(0.1)
                if signals["volume"]["trend"] == "alcista":
                    confidence_factors.append(0.15)
                if signals["patterns"]["gap_direction"] == "alcista":
                    confidence_factors.append(0.1)
                if signals["patterns"]["hammer"]:
                    confidence_factors.append(0.1)

            # Factores para PUT (bajista)
            else:
                if signals["trend"]["sma_20_50"] == "bajista":
                    confidence_factors.append(0.2)
                if signals["trend"]["macd"] == "bajista":
                    confidence_factors.append(0.15)
                if signals["trend"]["sma_200"] == "por_debajo":
                    confidence_factors.append(0.25)
                if signals["momentum"]["rsi_condition"] == "sobrecomprado":
                    confidence_factors.append(0.15)
                elif 40 <= signals["momentum"]["rsi"] <= 60:
                    confidence_factors.append(0.1)
                if signals["volume"]["trend"] == "bajista":
                    confidence_factors.append(0.15)
                if signals["patterns"]["gap_direction"] == "bajista":
                    confidence_factors.append(0.1)
                if signals["patterns"]["hanger"]:
                    confidence_factors.append(0.1)

            # Calcular confianza total
            confidence_score = sum(confidence_factors)

            # Convertir a categorías
            if confidence_score >= 0.7:
                confidence = "ALTA"
            elif confidence_score >= 0.4:
                confidence = "MEDIA"
            else:
                confidence = "BAJA"

            # Determinar timeframe basado en signos
            if signals["volatility"]["volatility_state"] == "alta":
                timeframe = "CORTO"  # Alta volatilidad -> operaciones cortas
            elif signals["trend"]["sma_20_50"] != signals["trend"]["sma_200"]:
                timeframe = "MEDIO"  # Divergencia entre tendencias -> plazo medio
            else:
                timeframe = (
                    "MEDIO-LARGO"  # Convergencia de tendencias -> plazo más largo
                )

            # Determinar estrategia según la dirección y señales
            if direction == "CALL":
                if signals["patterns"]["gap_direction"] == "alcista":
                    strategy = "Gap Normal al Alza"
                elif signals["momentum"]["rsi_condition"] == "sobrevendido":
                    strategy = "Caída Normal/Fuerte (Horario)"
                elif (
                    signals["trend"]["sma_20_50"] == "alcista"
                    and signals["momentum"]["rsi_trend"] == "alcista"
                ):
                    strategy = "Promedio Móvil de 40 (Horario)"
                else:
                    strategy = "Estrategia CALL genérica"
            else:  # PUT
                if signals["patterns"]["gap_direction"] == "bajista":
                    strategy = "Ruptura de Piso del Gap"
                elif signals["momentum"]["rsi_condition"] == "sobrecomprado":
                    strategy = "Primera Vela Roja de Apertura"
                elif signals["patterns"]["hanger"]:
                    strategy = "Hanger en Diario"
                else:
                    strategy = "Estrategia PUT genérica"

            return {
                "direction": direction,
                "confidence": confidence,
                "timeframe": timeframe,
                "strategy": strategy,
                "confidence_score": round(confidence_score, 2),
            }

        except Exception as e:
            logger.error(f"Error analizando estrategia de opciones: {str(e)}")
            return {
                "direction": "NEUTRAL",
                "confidence": "BAJA",
                "timeframe": "INDEFINIDO",
                "strategy": "Error en análisis",
                "confidence_score": 0.0,
            }

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
        try:
            close = current.get("Close", 0)
            bb_high = current.get("BB_High", float("inf"))
            bb_low = current.get("BB_Low", 0)

            if close > bb_high:
                return "superior"
            elif close < bb_low:
                return "inferior"
            else:
                return "medio"
        except Exception:
            return "medio"

    def _get_volatility_state(self, current, df):
        """Evalúa el estado de la volatilidad"""
        try:
            bb_width = current.get("BB_Width", 0)
            bb_width_mean = df["BB_Width"].mean() if "BB_Width" in df.columns else 0
            atr = current.get("ATR", 0)
            atr_mean = df["ATR"].mean() if "ATR" in df.columns else 1

            # Usar ambos indicadores de volatilidad
            bb_volatility = (bb_width / bb_width_mean) if bb_width_mean > 0 else 1
            atr_volatility = (atr / atr_mean) if atr_mean > 0 else 1

            # Combinar señales
            volatility_score = (bb_volatility * 0.6) + (atr_volatility * 0.4)

            if volatility_score > 1.5:
                return "alta"
            elif volatility_score < 0.7:
                return "baja"
            else:
                return "normal"
        except Exception:
            return "normal"

    def _calculate_overall_signal(self, signals):
        """Calcula la señal general basada en todos los indicadores"""
        try:
            score = 0

            # Puntaje por tendencia
            if signals["trend"]["sma_20_50"] == "alcista":
                score += 1
            else:
                score -= 1

            if signals["trend"]["macd"] == "alcista":
                score += 0.5
            else:
                score -= 0.5

            if signals["trend"]["sma_200"] == "por_encima":
                score += 1
            else:
                score -= 1

            # Puntaje por momentum
            if signals["momentum"]["rsi_condition"] == "sobrecomprado":
                score -= 1.5
            elif signals["momentum"]["rsi_condition"] == "sobrevendido":
                score += 1.5

            if signals["momentum"]["stoch_trend"] == "alcista":
                score += 0.5
            else:
                score -= 0.5

            # Puntaje por volatilidad
            if signals["volatility"]["volatility_state"] == "alta":
                score *= 0.8  # Reducir confianza en alta volatilidad

            # Puntaje por volumen
            if signals["volume"]["trend"] == "alcista":
                score += 0.5
            else:
                score -= 0.5

            if signals["volume"]["obv_trend"] == "alcista":
                score += 0.5
            else:
                score -= 0.5

            # Puntaje por patrones
            if signals["patterns"]["gap"] > 0:
                score += 0.5
            elif signals["patterns"]["gap"] < 0:
                score -= 0.5

            if signals["patterns"]["hammer"]:
                score += 1
            if signals["patterns"]["hanger"]:
                score -= 1

            # Determinar señal final
            signal = ""
            confidence = ""

            if score >= 2.5:
                signal = "compra_fuerte"
                confidence = "alta"
            elif score >= 1:
                signal = "compra"
                confidence = "moderada"
            elif score <= -2.5:
                signal = "venta_fuerte"
                confidence = "alta"
            elif score <= -1:
                signal = "venta"
                confidence = "moderada"
            else:
                signal = "neutral"
                confidence = "baja"

            return {
                "signal": signal,
                "confidence": confidence,
                "score": round(score, 2),
            }
        except Exception as e:
            logger.error(f"Error calculando señal general: {str(e)}")
            return {"signal": "error", "confidence": "error", "score": 0}

    def analyze_multi_timeframe(
        self, symbol: str, timeframes: List[str] = ["1d", "1wk", "1mo"]
    ) -> Dict:
        """Analiza múltiples timeframes para un símbolo"""
        results = {}

        try:
            # Obtener análisis para cada timeframe
            for tf in timeframes:
                try:
                    # Obtener datos para este timeframe
                    data = fetch_market_data(symbol, "1y", tf)

                    # Verificar datos suficientes
                    if data is None or len(data) < 20:
                        logger.warning(
                            f"Datos insuficientes para {symbol} en timeframe {tf}"
                        )
                        continue

                    # Análisis técnico
                    self.data = data
                    self.calculate_indicators()
                    signals = self.get_current_signals()

                    if signals:
                        results[tf] = signals
                except Exception as tf_error:
                    logger.error(
                        f"Error analizando {symbol} en timeframe {tf}: {str(tf_error)}"
                    )

            # Calcular señal consolidada multi-timeframe
            if results:
                # Inicializar puntuaciones para cada señal
                score_buy = 0
                score_sell = 0
                weight_sum = 0

                # Pesos por timeframe
                weights = {
                    "1m": 0.2,
                    "5m": 0.3,
                    "15m": 0.4,
                    "30m": 0.5,
                    "1h": 0.6,
                    "1d": 1.0,
                    "1wk": 1.5,
                    "1mo": 2.0,
                }

                # Sumar puntuaciones ponderadas
                for tf, signals in results.items():
                    weight = weights.get(tf, 1.0)
                    weight_sum += weight

                    # Convertir señal a puntaje
                    overall_signal = signals["overall"]["signal"]
                    signal_score = 0

                    if overall_signal == "compra_fuerte":
                        signal_score = 2
                    elif overall_signal == "compra":
                        signal_score = 1
                    elif overall_signal == "venta_fuerte":
                        signal_score = -2
                    elif overall_signal == "venta":
                        signal_score = -1

                    # Aplicar a puntuación total
                    if signal_score > 0:
                        score_buy += signal_score * weight
                    elif signal_score < 0:
                        score_sell += abs(signal_score) * weight

                # Normalizar puntuaciones
                if weight_sum > 0:
                    score_buy /= weight_sum
                    score_sell /= weight_sum

                # Determinar señal consolidada
                if score_buy > score_sell * 1.5:
                    consolidated = {
                        "signal": "compra_fuerte" if score_buy > 1.5 else "compra",
                        "confidence": "alta" if score_buy > 1.5 else "moderada",
                        "timeframe_alignment": (
                            "fuerte" if len(results) >= 2 else "moderada"
                        ),
                    }
                elif score_sell > score_buy * 1.5:
                    consolidated = {
                        "signal": "venta_fuerte" if score_sell > 1.5 else "venta",
                        "confidence": "alta" if score_sell > 1.5 else "moderada",
                        "timeframe_alignment": (
                            "fuerte" if len(results) >= 2 else "moderada"
                        ),
                    }
                else:
                    consolidated = {
                        "signal": "neutral",
                        "confidence": "baja",
                        "timeframe_alignment": "débil",
                    }

                # Añadir puntuaciones
                consolidated["score_buy"] = round(score_buy, 2)
                consolidated["score_sell"] = round(score_sell, 2)

                # Añadir recomendación de opciones
                if consolidated["signal"] in ["compra", "compra_fuerte"]:
                    consolidated["options_recommendation"] = "CALL"
                elif consolidated["signal"] in ["venta", "venta_fuerte"]:
                    consolidated["options_recommendation"] = "PUT"
                else:
                    consolidated["options_recommendation"] = "NEUTRAL"

                # Añadir resultado consolidado
                results["consolidated"] = consolidated

            return results

        except Exception as e:
            logger.error(f"Error en análisis multi-timeframe para {symbol}: {str(e)}")
            return {"error": str(e)}

    def get_candle_patterns(self, data: pd.DataFrame = None) -> List[Dict]:
        """Identifica patrones de velas comunes en los datos"""
        try:
            df = data if data is not None else self.data
            if df is None or len(df) < 5:
                return []

            patterns = []

            # Buscar patrones en las últimas 5 velas
            for i in range(-5, 0):
                idx = i if i < 0 else len(df) - 5 + i
                if idx < 0 or idx >= len(df):
                    continue

                vela = df.iloc[idx]

                # Estructura de vela
                open_price = vela["Open"]
                close_price = vela["Close"]
                high = vela["High"]
                low = vela["Low"]

                body_size = abs(close_price - open_price)
                total_range = high - low
                body_percent = (body_size / total_range) * 100 if total_range > 0 else 0

                upper_shadow = high - max(open_price, close_price)
                lower_shadow = min(open_price, close_price) - low

                # Determinar si es alcista o bajista
                is_bullish = close_price > open_price

                # Patrón: Doji
                if body_percent < 5:
                    patterns.append(
                        {
                            "pattern": "Doji",
                            "position": idx,
                            "date": df.index[idx],
                            "type": "reversal",
                            "strength": "medium",
                            "description": "Indecisión en el mercado",
                        }
                    )

                # Patrón: Martillo (alcista en tendencia bajista)
                elif (
                    lower_shadow > 2 * body_size
                    and upper_shadow < 0.1 * total_range
                    and lower_shadow > 0.6 * total_range
                ):

                    # Verificar tendencia previa
                    if (
                        idx > 10
                        and df["Close"].iloc[idx - 10 : idx].mean() < open_price
                    ):
                        patterns.append(
                            {
                                "pattern": "Martillo",
                                "position": idx,
                                "date": df.index[idx],
                                "type": "bullish reversal",
                                "strength": "strong",
                                "description": "Posible fin de tendencia bajista",
                            }
                        )

                # Patrón: Hombre Colgado (bajista en tendencia alcista)
                elif (
                    lower_shadow > 2 * body_size
                    and upper_shadow < 0.1 * total_range
                    and lower_shadow > 0.6 * total_range
                ):

                    # Verificar tendencia previa
                    if (
                        idx > 10
                        and df["Close"].iloc[idx - 10 : idx].mean() > open_price
                    ):
                        patterns.append(
                            {
                                "pattern": "Hombre Colgado",
                                "position": idx,
                                "date": df.index[idx],
                                "type": "bearish reversal",
                                "strength": "strong",
                                "description": "Posible fin de tendencia alcista",
                            }
                        )

                # Patrón: Vela Marubozu (cuerpo largo, sin sombras)
                elif (
                    body_percent > 80
                    and upper_shadow < 0.1 * body_size
                    and lower_shadow < 0.1 * body_size
                ):

                    pattern_type = (
                        "bullish continuation" if is_bullish else "bearish continuation"
                    )
                    pattern_desc = (
                        "Fuerte presión compradora"
                        if is_bullish
                        else "Fuerte presión vendedora"
                    )

                    patterns.append(
                        {
                            "pattern": "Marubozu",
                            "position": idx,
                            "date": df.index[idx],
                            "type": pattern_type,
                            "strength": "strong",
                            "description": pattern_desc,
                        }
                    )

                # Patrón: Estrella Fugaz (bajista)
                elif (
                    upper_shadow > 2 * body_size
                    and lower_shadow < 0.1 * total_range
                    and upper_shadow > 0.6 * total_range
                ):

                    patterns.append(
                        {
                            "pattern": "Estrella Fugaz",
                            "position": idx,
                            "date": df.index[idx],
                            "type": "bearish reversal",
                            "strength": "medium",
                            "description": "Posible techo o resistencia",
                        }
                    )

            # Buscar patrones de múltiples velas
            if len(df) >= 3:
                # Patrón: Envolvente Alcista
                last_two = df.iloc[-2:]
                if (
                    last_two["Close"].iloc[0]
                    < last_two["Open"].iloc[0]  # Primera vela bajista
                    and last_two["Close"].iloc[1]
                    > last_two["Open"].iloc[1]  # Segunda vela alcista
                    and last_two["Close"].iloc[1]
                    > last_two["Open"].iloc[0]  # Envuelve el cuerpo
                    and last_two["Open"].iloc[1] < last_two["Close"].iloc[0]
                ):

                    patterns.append(
                        {
                            "pattern": "Envolvente Alcista",
                            "position": -1,
                            "date": df.index[-1],
                            "type": "bullish reversal",
                            "strength": "strong",
                            "description": "Fuerte señal de cambio alcista",
                        }
                    )

                # Patrón: Envolvente Bajista
                elif (
                    last_two["Close"].iloc[0]
                    > last_two["Open"].iloc[0]  # Primera vela alcista
                    and last_two["Close"].iloc[1]
                    < last_two["Open"].iloc[1]  # Segunda vela bajista
                    and last_two["Close"].iloc[1]
                    < last_two["Open"].iloc[0]  # Envuelve el cuerpo
                    and last_two["Open"].iloc[1] > last_two["Close"].iloc[0]
                ):

                    patterns.append(
                        {
                            "pattern": "Envolvente Bajista",
                            "position": -1,
                            "date": df.index[-1],
                            "type": "bearish reversal",
                            "strength": "strong",
                            "description": "Fuerte señal de cambio bajista",
                        }
                    )

            return patterns

        except Exception as e:
            logger.error(f"Error identificando patrones de velas: {str(e)}")
            return []

    def get_support_resistance(
        self, data: pd.DataFrame = None, n_levels: int = 3
    ) -> Dict:
        """Calcula niveles de soporte y resistencia relevantes"""
        try:
            df = data if data is not None else self.data
            if df is None or len(df) < 20:
                return {"supports": [], "resistances": []}

            # Obtener precios
            close = df["Close"].iloc[-1]

            # Método 1: Swing highs/lows
            highs = []
            lows = []

            for i in range(1, len(df) - 1):
                # Swing high
                if (
                    df["High"].iloc[i] > df["High"].iloc[i - 1]
                    and df["High"].iloc[i] > df["High"].iloc[i + 1]
                ):
                    highs.append(df["High"].iloc[i])

                # Swing low
                if (
                    df["Low"].iloc[i] < df["Low"].iloc[i - 1]
                    and df["Low"].iloc[i] < df["Low"].iloc[i + 1]
                ):
                    lows.append(df["Low"].iloc[i])

            # Método 2: Medias móviles clave
            ma_levels = []
            for period in [20, 50, 100, 200]:
                col = f"SMA_{period}"
                if col in df.columns:
                    ma_levels.append(df[col].iloc[-1])

            # Método 3: Fibonacci desde máximo/mínimo reciente
            recent_high = df["High"].max()
            recent_low = df["Low"].min()
            range_price = recent_high - recent_low

            fib_levels = {
                "0": recent_low,
                "0.236": recent_low + 0.236 * range_price,
                "0.382": recent_low + 0.382 * range_price,
                "0.5": recent_low + 0.5 * range_price,
                "0.618": recent_low + 0.618 * range_price,
                "0.786": recent_low + 0.786 * range_price,
                "1": recent_high,
            }

            # Combinar todos los niveles
            all_supports = sorted(
                [l for l in lows + ma_levels + list(fib_levels.values()) if l < close]
            )
            all_resistances = sorted(
                [l for l in highs + ma_levels + list(fib_levels.values()) if l > close]
            )

            # Agrupar niveles cercanos (dentro del 0.5%)
            grouped_supports = []
            for level in all_supports:
                if (
                    not grouped_supports
                    or abs(level - grouped_supports[-1]) / level > 0.005
                ):
                    grouped_supports.append(level)

            grouped_resistances = []
            for level in all_resistances:
                if (
                    not grouped_resistances
                    or abs(level - grouped_resistances[-1]) / level > 0.005
                ):
                    grouped_resistances.append(level)

            # Obtener los n_levels más cercanos al precio actual
            supports = sorted(grouped_supports, key=lambda x: abs(close - x))[:n_levels]
            resistances = sorted(grouped_resistances, key=lambda x: abs(close - x))[
                :n_levels
            ]

            return {
                "supports": supports,
                "resistances": resistances,
                "fibonacci": fib_levels,
            }

        except Exception as e:
            logger.error(f"Error calculando soportes y resistencias: {str(e)}")
            return {"supports": [], "resistances": []}


# =================================================
# FUNCIONES DE UTILIDAD ADICIONAL
# =================================================


def get_vix_level() -> float:
    """Obtiene el nivel actual del VIX con manejo de errores"""
    try:
        vix_data = fetch_market_data("^VIX", period="1d", interval="1d")
        if vix_data is not None and not vix_data.empty:
            return vix_data["Close"].iloc[-1]
        return 15.0  # Valor por defecto si no hay datos
    except Exception as e:
        logger.error(f"Error obteniendo nivel VIX: {str(e)}")
        return 15.0


def get_api_keys_from_secrets():
    """Obtiene claves API de secrets.toml con manejo mejorado"""
    try:
        # Importar streamlit
        import streamlit as st

        # Inicializar diccionario de claves
        api_keys = {}

        # Verificar si existe la sección api_keys en secrets
        if hasattr(st, "secrets"):
            # Comprobar claves en el nivel api_keys
            if "api_keys" in st.secrets:
                # YOU API
                if "you_api_key" in st.secrets.api_keys:
                    api_keys["you"] = st.secrets.api_keys.you_api_key

                # Tavily API
                if "tavily_api_key" in st.secrets.api_keys:
                    api_keys["tavily"] = st.secrets.api_keys.tavily_api_key

                # Alpha Vantage API
                if "alpha_vantage_api_key" in st.secrets.api_keys:
                    api_keys["alpha_vantage"] = (
                        st.secrets.api_keys.alpha_vantage_api_key
                    )

                # Finnhub API
                if "finnhub_api_key" in st.secrets.api_keys:
                    api_keys["finnhub"] = st.secrets.api_keys.finnhub_api_key

                # MarketStack API
                if "marketstack_api_key" in st.secrets.api_keys:
                    api_keys["marketstack"] = st.secrets.api_keys.marketstack_api_key

            # Comprobar claves en el nivel principal (para retrocompatibilidad)
            # YOU API - alternate names
            for key in ["YOU_API_KEY", "you_api_key", "YOU_KEY"]:
                if key in st.secrets:
                    api_keys["you"] = st.secrets[key]
                    break

            # Tavily API - alternate names
            for key in ["TAVILY_API_KEY", "tavily_api_key", "TAVILY_KEY"]:
                if key in st.secrets:
                    api_keys["tavily"] = st.secrets[key]
                    break

            # Alpha Vantage API - alternate names
            for key in [
                "ALPHA_VANTAGE_API_KEY",
                "alpha_vantage_api_key",
                "ALPHAVANTAGE_KEY",
            ]:
                if key in st.secrets:
                    api_keys["alpha_vantage"] = st.secrets[key]
                    break

            # Finnhub API - alternate names
            for key in ["FINNHUB_API_KEY", "finnhub_api_key", "FINNHUB_KEY"]:
                if key in st.secrets:
                    api_keys["finnhub"] = st.secrets[key]
                    break

            # MarketStack API - alternate names
            for key in [
                "MARKETSTACK_API_KEY",
                "marketstack_api_key",
                "MARKETSTACK_KEY",
            ]:
                if key in st.secrets:
                    api_keys["marketstack"] = st.secrets[key]
                    break

        # Comprobar variables de entorno como última opción
        import os

        for env_name, key_name in [
            ("YOU_API_KEY", "you"),
            ("TAVILY_API_KEY", "tavily"),
            ("ALPHA_VANTAGE_API_KEY", "alpha_vantage"),
            ("FINNHUB_API_KEY", "finnhub"),
            ("MARKETSTACK_API_KEY", "marketstack"),
        ]:
            if env_name in os.environ and key_name not in api_keys:
                api_keys[key_name] = os.environ[env_name]

        return api_keys

    except Exception as e:
        import logging

        logging.error(f"Error obteniendo API keys: {str(e)}")
        return {}


def get_market_context(symbol: str) -> Dict:
    """Obtiene contexto completo de mercado para un símbolo"""
    try:
        # Obtener claves API directamente
        api_keys = get_api_keys_from_secrets()

        # Definir timeframes a analizar
        timeframes = ["1d", "1wk", "1mo"]

        # Obtener datos para el timeframe principal (diario)
        data = fetch_market_data(symbol, period="6mo", interval="1d")
        if data is None or data.empty:
            return {"error": "No hay datos disponibles para este símbolo"}

        # Crear analizador técnico
        analyzer = TechnicalAnalyzer(data)

        # Calcular indicadores
        analyzer.calculate_indicators()

        # Obtener señales
        signals = analyzer.get_current_signals()
        if signals is None:
            return {"error": "Error calculando señales técnicas"}

        # Obtener patrones de velas
        candle_patterns = analyzer.get_candle_patterns()

        # Obtener niveles de soporte/resistencia
        levels = analyzer.get_support_resistance()

        # Obtener análisis multi-timeframe
        multi_tf_analysis = analyzer.analyze_multi_timeframe(symbol, timeframes)

        # Obtener nivel VIX para ajustes de volatilidad
        vix_level = get_vix_level()

        # Obtener parámetros de opciones
        options_manager = OptionsParameterManager()
        options_params = options_manager.get_symbol_params(symbol)
        volatility_adjustments = options_manager.get_volatility_adjustments(vix_level)

        # Integrar noticias y análisis de sentimiento con las claves obtenidas
        news_data = fetch_news_data(symbol, api_keys)
        sentiment_data = analyze_sentiment(symbol, news_data)
        web_analysis = get_web_insights(symbol, api_keys)

        # Construir respuesta
        context = {
            "symbol": symbol,
            "last_price": float(data["Close"].iloc[-1]),
            "change": (
                float(data["Close"].iloc[-1] - data["Close"].iloc[-2])
                if len(data) > 1
                else 0.0
            ),
            "change_percent": (
                float((data["Close"].iloc[-1] / data["Close"].iloc[-2] - 1) * 100)
                if len(data) > 1
                else 0.0
            ),
            "signals": signals,
            "candle_patterns": candle_patterns,
            "support_resistance": levels,
            "multi_timeframe": multi_tf_analysis,
            "vix_level": vix_level,
            "options_params": options_params,
            "volatility_adjustments": volatility_adjustments,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "news": news_data,
            "news_sentiment": sentiment_data,
            "web_analysis": web_analysis,
            "web_results": web_analysis.get("web_results", []),
            "chart_data": data.reset_index().to_dict(orient="records"),
        }

        return context

    except Exception as e:
        logger.error(f"Error en get_market_context: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}


def fetch_news_data(symbol: str, api_keys: Dict = None) -> List:
    """Obtiene noticias recientes para un símbolo usando múltiples fuentes con respaldo de Yahoo Finance"""
    # Verificar si hay datos en caché
    cache_key = f"news_{symbol}"
    cached_data = _data_cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Intentar obtener claves API
    try:
        import streamlit as st

        # Intentar obtener claves de configuración
        alpha_key = None
        finnhub_key = None

        # Utilizar claves proporcionadas en el parámetro api_keys
        if api_keys:
            alpha_key = api_keys.get("alpha_vantage")
            finnhub_key = api_keys.get("finnhub")

        # Buscar en secrets.toml si no se proporcionaron claves
        if hasattr(st, "secrets"):
            if "api_keys" in st.secrets:
                if not alpha_key:
                    alpha_key = st.secrets.api_keys.get("alpha_vantage_api_key", None)
                if not finnhub_key:
                    finnhub_key = st.secrets.api_keys.get("finnhub_api_key", None)

            # Buscar en nivel principal
            if not alpha_key:
                alpha_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", None)
            if not finnhub_key:
                finnhub_key = st.secrets.get("FINNHUB_API_KEY", None)

        # Buscar en variables de entorno
        if not alpha_key or not finnhub_key:
            import os

            if not alpha_key:
                alpha_key = os.environ.get("ALPHA_VANTAGE_API_KEY", None)
            if not finnhub_key:
                finnhub_key = os.environ.get("FINNHUB_API_KEY", None)

        # Intentar Alpha Vantage primero
        if alpha_key:
            try:
                import requests

                url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={alpha_key}"
                response = requests.get(url, timeout=10)
                data = response.json()

                if "feed" in data and data["feed"]:
                    news = []
                    for item in data["feed"][:10]:  # Limitar a 10 noticias
                        news.append(
                            {
                                "title": item.get("title", "Sin título"),
                                "summary": item.get("summary", ""),
                                "url": item.get("url", "#"),
                                "date": item.get("time_published", ""),
                                "source": item.get("source", "Alpha Vantage"),
                                "sentiment": item.get("overall_sentiment_score", 0.5),
                            }
                        )

                    # Guardar en caché
                    _data_cache.set(cache_key, news)
                    return news
            except Exception as e:
                logger.warning(f"Error obteniendo noticias de Alpha Vantage: {str(e)}")

        # Intentar Finnhub como respaldo
        if finnhub_key:
            try:
                import requests
                import time

                current_time = int(time.time())
                week_ago = current_time - 7 * 24 * 60 * 60
                url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2023-01-01&to=2023-04-30&token={finnhub_key}"
                response = requests.get(url, timeout=10)
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    news = []
                    for item in data[:10]:  # Limitar a 10 noticias
                        news.append(
                            {
                                "title": item.get("headline", "Sin título"),
                                "summary": item.get("summary", ""),
                                "url": item.get("url", "#"),
                                "date": item.get("datetime", ""),
                                "source": item.get("source", "Finnhub"),
                                "sentiment": 0.5,  # Valor por defecto
                            }
                        )

                    # Guardar en caché
                    _data_cache.set(cache_key, news)
                    return news
            except Exception as e:
                logger.warning(f"Error obteniendo noticias de Finnhub: {str(e)}")

        # Intentar obtener noticias directamente de Yahoo Finance
        try:
            import requests
            from bs4 import BeautifulSoup
            from datetime import datetime

            # Construir URL de noticias de Yahoo Finance
            yahoo_url = f"https://finance.yahoo.com/quote/{symbol}/news"

            # Simular un navegador para evitar bloqueos
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # Realizar solicitud
            response = requests.get(yahoo_url, headers=headers, timeout=10)

            # Verificar respuesta exitosa
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Buscar elementos de noticia - ajustar selectores según la estructura actual de Yahoo Finance
                news_items = soup.select("li.js-stream-content")

                if news_items:
                    news = []
                    for item in news_items[:10]:  # Limitar a 10 noticias
                        # Extraer título, normalmente en un h3
                        title_element = item.select_one("h3")
                        title = (
                            title_element.text.strip()
                            if title_element
                            else "Sin título"
                        )

                        # Extraer enlace
                        link_element = item.select_one("a")
                        url = (
                            link_element["href"]
                            if link_element and "href" in link_element.attrs
                            else "#"
                        )
                        # Convertir enlaces relativos a absolutos
                        if url.startswith("/"):
                            url = f"https://finance.yahoo.com{url}"

                        # Extraer descripción
                        summary_element = item.select_one("p")
                        summary = (
                            summary_element.text.strip() if summary_element else ""
                        )

                        # Extraer fecha
                        date_element = item.select_one("span")
                        date_str = date_element.text.strip() if date_element else ""

                        # Análisis simple de sentimiento
                        sentiment_value = 0.5  # Neutral por defecto
                        text_for_sentiment = f"{title} {summary}".lower()

                        # Palabras positivas y negativas
                        positive_words = [
                            "buy",
                            "bullish",
                            "up",
                            "surge",
                            "growth",
                            "positive",
                            "rise",
                            "gain",
                        ]
                        negative_words = [
                            "sell",
                            "bearish",
                            "down",
                            "fall",
                            "drop",
                            "decline",
                            "negative",
                            "loss",
                        ]

                        # Contar palabras
                        positive_count = sum(
                            1 for word in positive_words if word in text_for_sentiment
                        )
                        negative_count = sum(
                            1 for word in negative_words if word in text_for_sentiment
                        )

                        # Ajustar sentimiento
                        if positive_count > negative_count:
                            sentiment_value = 0.7
                        elif negative_count > positive_count:
                            sentiment_value = 0.3

                        # Añadir noticia
                        news.append(
                            {
                                "title": title,
                                "summary": summary,
                                "url": url,
                                "date": date_str,
                                "source": "Yahoo Finance",
                                "sentiment": sentiment_value,
                            }
                        )

                    # Si encontramos noticias, guardar en caché y retornar
                    if news:
                        _data_cache.set(cache_key, news)
                        return news

        except Exception as e:
            logger.warning(f"Error obteniendo noticias de Yahoo Finance: {str(e)}")

        # Intentar DuckDuckGo Search como último respaldo
        try:
            # Intentar importar duckduckgo_search
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                logger.warning(
                    "duckduckgo_search no está instalado. Intenta pip install duckduckgo-search"
                )
                raise ImportError("duckduckgo_search no está instalado")

            # Crear cliente DDGS
            ddgs = DDGS()

            # Realizar búsqueda de noticias
            keywords = f"{symbol} stock news financial"
            results = list(ddgs.news(keywords, max_results=10))

            if results:
                news = []
                for item in results:
                    # Calcular un sentimiento básico (neutral por defecto)
                    sentiment_value = 0.5

                    # Análisis simple de sentimiento basado en palabras clave
                    title_lower = item.get("title", "").lower()
                    if any(
                        word in title_lower
                        for word in ["up", "rise", "gain", "bull", "positive", "growth"]
                    ):
                        sentiment_value = 0.7  # Positivo
                    elif any(
                        word in title_lower
                        for word in ["down", "fall", "drop", "bear", "negative", "loss"]
                    ):
                        sentiment_value = 0.3  # Negativo

                    news.append(
                        {
                            "title": item.get("title", "Sin título"),
                            "summary": item.get("body", ""),
                            "url": item.get("url", "#"),
                            "date": item.get("date", ""),
                            "source": item.get("source", "DuckDuckGo"),
                            "sentiment": sentiment_value,
                        }
                    )

                # Guardar en caché
                _data_cache.set(cache_key, news)
                return news

        except Exception as e:
            logger.warning(f"Error obteniendo noticias de DuckDuckGo: {str(e)}")

    except Exception as e:
        logger.error(f"Error en fetch_news_data: {str(e)}")

    # Retornar lista vacía si todo falla
    _data_cache.set(cache_key, [])
    return []


def analyze_sentiment(symbol: str, news_data: List = None) -> Dict:
    """Analiza el sentimiento para un símbolo basado en noticias"""
    # Verificar si hay datos en caché
    cache_key = f"sentiment_{symbol}"
    cached_data = _data_cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Si no se proporcionaron noticias, obtenerlas
    if news_data is None or len(news_data) == 0:
        news_data = fetch_news_data(symbol)

    # Si no hay noticias, return un objeto vacío
    if not news_data:
        return {}

    # Extraer y promediar puntuaciones de sentimiento de las noticias
    positive_mentions = 0
    negative_mentions = 0
    total_score = 0

    for item in news_data:
        sentiment_score = item.get("sentiment", 0.5)
        total_score += sentiment_score

        if sentiment_score > 0.6:
            positive_mentions += 1
        elif sentiment_score < 0.4:
            negative_mentions += 1

    # Calcular puntuación media
    avg_sentiment = total_score / len(news_data) if news_data else 0.5

    # Determinar etiqueta de sentimiento
    if avg_sentiment > 0.6:
        sentiment_label = "bullish"
    elif avg_sentiment < 0.4:
        sentiment_label = "bearish"
    else:
        sentiment_label = "neutral"

    # Crear resultado de sentimiento
    sentiment_result = {
        "score": avg_sentiment,
        "sentiment": sentiment_label,
        "positive_mentions": positive_mentions,
        "negative_mentions": negative_mentions,
        "total_analyzed": len(news_data),
        "sector_avg_bullish": 0.55,  # Valores de ejemplo
        "sector_avg_bearish": 0.45,
    }

    # Guardar en caché
    _data_cache.set(cache_key, sentiment_result)
    return sentiment_result


def get_web_insights(symbol: str, api_keys: Dict = None) -> Dict:
    """Obtiene análisis de fuentes web sobre un símbolo mediante consultas a múltiples APIs con respaldo de Yahoo Finance"""
    # Verificar si hay datos en caché
    cache_key = f"web_insights_{symbol}"
    cached_data = _data_cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    web_results = []
    bullish_mentions = 0
    bearish_mentions = 0

    # Palabras alcistas y bajistas para análisis de sentimiento
    bullish_words = [
        "alcista",
        "alcanza",
        "subida",
        "crecimiento",
        "positivo",
        "optimista",
        "aumenta",
        "compra",
        "oportunidad",
        "superará",
        "supera",
        "mejor",
        "ganancias",
        "fuerte",
        "rali",
        "rally",
        "bull",
        "bullish",
        "up",
        "higher",
        "gain",
        "upgrade",
        "surges",
        "rises",
        "climbing",
        "jumped",
        "outperform",
    ]

    bearish_words = [
        "bajista",
        "caída",
        "desciende",
        "negativo",
        "pesimista",
        "disminuye",
        "venta",
        "riesgo",
        "peor",
        "pérdidas",
        "débil",
        "bear",
        "bearish",
        "corrección",
        "advertencia",
        "precaución",
        "preocupación",
        "down",
        "fall",
        "drop",
        "decline",
        "plunge",
        "downgrade",
        "underperform",
        "lower",
        "loss",
        "crash",
        "risk",
        "sell",
        "warning",
    ]

    # Función para analizar sentimiento en texto
    def analyze_text_sentiment(text):
        if not text:
            return 0, 0

        text = text.lower()
        bull_count = sum(1 for word in bullish_words if word in text)
        bear_count = sum(1 for word in bearish_words if word in text)
        return bull_count, bear_count

    # Intentar obtener datos de Yahoo Finance primero
    try:
        import requests
        from bs4 import BeautifulSoup
        import re

        # URLs para obtener análisis de Yahoo Finance
        urls = [
            f"https://finance.yahoo.com/quote/{symbol}/analysis",  # Página de análisis
            f"https://finance.yahoo.com/quote/{symbol}",  # Página principal que contiene resumen
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        for yahoo_url in urls:
            try:
                response = requests.get(yahoo_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Extraer información relevante según la URL
                    if "analysis" in yahoo_url:
                        # Buscar secciones de análisis como recomendaciones de analistas
                        analysis_sections = soup.select(
                            'section[data-test="analyst-rating-section"]'
                        )

                        for section in analysis_sections:
                            title_element = section.select_one("h2")
                            title = (
                                title_element.text.strip()
                                if title_element
                                else "Análisis de Yahoo Finance"
                            )

                            # Extraer contenido de análisis
                            content_elements = section.select(
                                "p, span.Fz\(m\)"
                            )  # Ajustar selectores según la estructura
                            content = " ".join(
                                [
                                    el.text.strip()
                                    for el in content_elements
                                    if el.text.strip()
                                ]
                            )

                            if content:
                                web_results.append(
                                    {
                                        "title": title,
                                        "content": content,
                                        "url": yahoo_url,
                                        "source": "Yahoo Finance Analysis",
                                    }
                                )

                                # Analizar sentimiento
                                bull_count, bear_count = analyze_text_sentiment(content)
                                if bull_count > bear_count:
                                    bullish_mentions += 1
                                elif bear_count > bull_count:
                                    bearish_mentions += 1

                    else:  # Página principal
                        # Extraer información del resumen y recomendaciones
                        summary_sections = soup.select(
                            'div#quote-summary, div[data-test="summary-section"]'
                        )

                        for section in summary_sections:
                            # Buscar tabla de resumen
                            rows = section.select("tr")

                            summary_content = []
                            for row in rows:
                                label = row.select_one("td:nth-child(1)")
                                value = row.select_one("td:nth-child(2)")

                                if label and value:
                                    summary_content.append(
                                        f"{label.text.strip()}: {value.text.strip()}"
                                    )

                            if summary_content:
                                content_text = "\n".join(summary_content)
                                web_results.append(
                                    {
                                        "title": f"Resumen de {symbol}",
                                        "content": content_text,
                                        "url": yahoo_url,
                                        "source": "Yahoo Finance Summary",
                                    }
                                )

                                # Analizar sentimiento
                                bull_count, bear_count = analyze_text_sentiment(
                                    content_text
                                )
                                if bull_count > bear_count:
                                    bullish_mentions += 1
                                elif bear_count > bull_count:
                                    bearish_mentions += 1

            except Exception as yahoo_error:
                logger.warning(
                    f"Error obteniendo datos de {yahoo_url}: {str(yahoo_error)}"
                )
                continue

    except Exception as e:
        logger.warning(f"Error general accediendo a Yahoo Finance: {str(e)}")

    # Intentar obtener claves API
    try:
        import streamlit as st
        import requests
        import json
        import re

        # Obtener claves de API
        you_key = None
        tavily_key = None

        # Utilizar claves proporcionadas en el parámetro api_keys
        if api_keys:
            you_key = api_keys.get("you")
            tavily_key = api_keys.get("tavily")

        # Buscar en secrets.toml si no se proporcionaron claves
        if hasattr(st, "secrets"):
            if "api_keys" in st.secrets:
                if not you_key:
                    you_key = st.secrets.api_keys.get("you_api_key", None)
                if not tavily_key:
                    tavily_key = st.secrets.api_keys.get("tavily_api_key", None)

            # Buscar en nivel principal
            if not you_key:
                you_key = st.secrets.get("YOU_API_KEY", None)
            if not tavily_key:
                tavily_key = st.secrets.get("TAVILY_API_KEY", None)

        # Buscar en variables de entorno
        if not you_key or not tavily_key:
            import os

            if not you_key:
                you_key = os.environ.get("YOU_API_KEY", None)
            if not tavily_key:
                tavily_key = os.environ.get("TAVILY_API_KEY", None)

        # Consulta usando YOU API si está disponible
        if you_key:
            try:
                # Preparar la consulta para obtener análisis actual
                query = f"últimas perspectivas y análisis para el activo {symbol} en bolsa. Quiero conocer la opinión de expertos sobre su tendencia actual"

                # Endpoint de la API
                url = "https://api.you.com/api/search"

                # Parámetros de la consulta
                params = {
                    "q": query,
                    "api_key": you_key,
                }

                # Realizar la solicitud
                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                # Procesar resultados
                if "hits" in data and len(data["hits"]) > 0:
                    for hit in data["hits"][:5]:  # Limitar a 5 resultados
                        if "title" in hit and "snippet" in hit:
                            web_results.append(
                                {
                                    "title": hit.get("title", "Sin título"),
                                    "content": hit.get("snippet", ""),
                                    "url": hit.get("url", "#"),
                                    "source": hit.get("source", "YOU Search"),
                                }
                            )

                            # Análisis de sentimiento simple basado en palabras clave
                            content = (
                                hit.get("title", "") + " " + hit.get("snippet", "")
                            )
                            bull_count, bear_count = analyze_text_sentiment(content)

                            # Actualizar contadores
                            if bull_count > bear_count:
                                bullish_mentions += 1
                            elif bear_count > bull_count:
                                bearish_mentions += 1
            except Exception as e:
                logger.warning(f"Error obteniendo datos de YOU API: {str(e)}")

        # Consulta usando Tavily API si está disponible
        if tavily_key and (not web_results or len(web_results) < 3):
            try:
                # Import condicional para Tavily (si está instalado)
                try:
                    from tavily import TavilyClient

                    tavily_client = TavilyClient(api_key=tavily_key)

                    # Realizar búsqueda
                    query = f"análisis técnico reciente y perspectivas para {symbol} en bolsa"
                    search_result = tavily_client.search(
                        query=query,
                        search_depth="advanced",
                        include_domains=[
                            "finance.yahoo.com",
                            "seekingalpha.com",
                            "fool.com",
                            "marketwatch.com",
                            "bloomberg.com",
                            "cnbc.com",
                        ],
                        max_results=5,
                    )

                    # Procesar resultados
                    if "results" in search_result and len(search_result["results"]) > 0:
                        for result in search_result["results"]:
                            web_results.append(
                                {
                                    "title": result.get("title", "Sin título"),
                                    "content": result.get("content", ""),
                                    "url": result.get("url", "#"),
                                    "source": result.get("source", "Tavily Search"),
                                }
                            )

                            # Análisis de sentimiento simple basado en palabras clave
                            content = (
                                result.get("title", "")
                                + " "
                                + result.get("content", "")
                            )
                            bull_count, bear_count = analyze_text_sentiment(content)

                            # Actualizar contadores
                            if bull_count > bear_count:
                                bullish_mentions += 1
                            elif bear_count > bull_count:
                                bearish_mentions += 1
                except ImportError:
                    # Fallback usando requests si tavily-python no está instalado
                    url = "https://api.tavily.com/search"
                    headers = {
                        "content-type": "application/json",
                        "x-api-key": tavily_key,
                    }
                    payload = {
                        "query": f"análisis técnico reciente y perspectivas para {symbol} en bolsa",
                        "search_depth": "advanced",
                        "include_domains": [
                            "finance.yahoo.com",
                            "seekingalpha.com",
                            "fool.com",
                            "marketwatch.com",
                            "bloomberg.com",
                            "cnbc.com",
                        ],
                        "max_results": 5,
                    }

                    response = requests.post(
                        url, json=payload, headers=headers, timeout=10
                    )
                    search_result = response.json()

                    # Procesar resultados
                    if "results" in search_result and len(search_result["results"]) > 0:
                        for result in search_result["results"]:
                            web_results.append(
                                {
                                    "title": result.get("title", "Sin título"),
                                    "content": result.get("content", ""),
                                    "url": result.get("url", "#"),
                                    "source": result.get("source", "Tavily Search"),
                                }
                            )

                            # Análisis de sentimiento simple basado en palabras clave
                            content = (
                                result.get("title", "")
                                + " "
                                + result.get("content", "")
                            )
                            bull_count, bear_count = analyze_text_sentiment(content)

                            # Actualizar contadores
                            if bull_count > bear_count:
                                bullish_mentions += 1
                            elif bear_count > bull_count:
                                bearish_mentions += 1
            except Exception as e:
                logger.warning(f"Error obteniendo datos de Tavily API: {str(e)}")

        # Intentar DuckDuckGo como último respaldo antes de usar datos simulados
        if not web_results or len(web_results) < 3:
            try:
                # Intentar importar duckduckgo_search
                try:
                    from duckduckgo_search import DDGS
                except ImportError:
                    logger.warning(
                        "duckduckgo_search no está instalado. Intenta pip install duckduckgo-search"
                    )
                    raise ImportError("duckduckgo_search no está instalado")

                ddgs = DDGS()

                # Buscar en la web análisis financieros del símbolo
                keywords = f"{symbol} stock market analysis forecast outlook"
                # Primero intentar con búsqueda web normal
                web_search_results = list(
                    ddgs.text(keywords, region="wt-wt", safesearch="off", max_results=5)
                )

                if web_search_results:
                    for result in web_search_results:
                        # Extraer información
                        title = result.get("title", "Sin título")
                        content = result.get(
                            "body", ""
                        )  # DuckDuckGo usa 'body' para el contenido
                        url = result.get(
                            "href", "#"
                        )  # DuckDuckGo usa 'href' para la URL
                        source = result.get("source", "DuckDuckGo")

                        web_results.append(
                            {
                                "title": title,
                                "content": content,
                                "url": url,
                                "source": source,
                            }
                        )

                        # Análisis de sentimiento
                        bull_count, bear_count = analyze_text_sentiment(
                            title + " " + content
                        )

                        # Actualizar contadores
                        if bull_count > bear_count:
                            bullish_mentions += 1
                        elif bear_count > bull_count:
                            bearish_mentions += 1

                # Si aún necesitamos más resultados, probar búsqueda de noticias
                if len(web_results) < 3:
                    news_keywords = f"{symbol} stock price analysis"
                    news_results = list(
                        ddgs.news(news_keywords, region="wt-wt", max_results=3)
                    )

                    if news_results:
                        for result in news_results:
                            title = result.get("title", "Sin título")
                            content = result.get("body", "")
                            url = result.get("url", "#")
                            source = result.get("source", "DuckDuckGo News")

                            web_results.append(
                                {
                                    "title": title,
                                    "content": content,
                                    "url": url,
                                    "source": source,
                                }
                            )

                            # Análisis de sentimiento
                            bull_count, bear_count = analyze_text_sentiment(
                                title + " " + content
                            )

                            # Actualizar contadores
                            if bull_count > bear_count:
                                bullish_mentions += 1
                            elif bear_count > bull_count:
                                bearish_mentions += 1

            except Exception as e:
                logger.warning(f"Error obteniendo datos de DuckDuckGo: {str(e)}")

        # Si no se obtuvieron resultados de ninguna fuente, proporcionar un resultado simulado
        if not web_results:
            logger.warning(
                f"Todas las fuentes fallaron para {symbol}, usando datos simulados"
            )
            web_results.append(
                {
                    "title": f"Perspectivas del mercado para {symbol}",
                    "content": f"Los analistas tienen opiniones mixtas sobre {symbol}, con ligero sesgo alcista.",
                    "url": "https://example.com/market",
                    "source": "Market Insights (Simulado)",
                }
            )

            import random

            bullish_mentions = random.randint(1, 5)
            bearish_mentions = random.randint(1, 5)
            logger.warning(
                f"Usando datos simulados para {symbol} debido a falta de resultados de APIs"
            )

        # Crear objeto de análisis web
        web_analysis = {
            "bullish_mentions": bullish_mentions,
            "bearish_mentions": bearish_mentions,
            "sources_count": len(web_results),
            "web_results": web_results,
        }

        # Guardar en caché
        _data_cache.set(cache_key, web_analysis)
        return web_analysis

    except Exception as e:
        logger.error(f"Error en get_web_insights: {str(e)}")
        traceback.print_exc()

        # Crear un resultado mínimo para evitar errores
        web_results = [
            {
                "title": f"Información para {symbol}",
                "content": "No se pudieron obtener análisis adicionales en este momento.",
                "url": "#",
                "source": "Sistema",
            }
        ]

        web_analysis = {
            "bullish_mentions": 1,
            "bearish_mentions": 1,
            "sources_count": 1,
            "web_results": web_results,
        }

        # Guardar en caché
        _data_cache.set(cache_key, web_analysis)
        return web_analysis


def clear_cache():
    """Limpia el caché global"""
    return _data_cache.clear()


# =================================================
# COMPATIBILIDAD CON CÓDIGO LEGADO
# =================================================


def validate_market_data_legacy(data):
    """Versión legada de validate_market_data para compatibilidad"""
    return validate_market_data(data)


def fetch_market_data_legacy(symbol, period="6mo", interval="1d"):
    """Versión legada de fetch_market_data para compatibilidad"""
    return fetch_market_data(symbol, period, interval)


class TechnicalAnalyzer_Legacy:
    """Versión legada de TechnicalAnalyzer para compatibilidad"""

    def __init__(self, data):
        self.data = data
        self.indicators = None
        self.signals = {}

    def calculate_indicators(self):
        """Versión legada compatible con TechnicalAnalyzer original"""
        analyzer = TechnicalAnalyzer(self.data)
        self.indicators = analyzer.calculate_indicators()
        return self.indicators

    def get_current_signals(self):
        """Versión legada compatible con TechnicalAnalyzer original"""
        if self.indicators is None:
            self.calculate_indicators()

        analyzer = TechnicalAnalyzer(self.data)
        self.signals = analyzer.get_current_signals()
        return self.signals
