import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import traceback
import time
import requests
import os
import json
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from io import StringIO

# Configuración de logging mejorada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verificación de autenticación
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.title("🔒 Acceso Restringido")
    st.warning("Por favor, inicie sesión desde la página principal del sistema.")
    st.stop()

# Universo de Trading
SYMBOLS = {
    "Índices": ["SPY", "QQQ", "DIA", "IWM", "EFA", "VWO", "IYR", "XLE", "XLF", "XLV"],
    "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "PYPL", "CRM"],
    "Finanzas": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK"],
    "Salud": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "AMGN", "BMY", "GILD", "TMO"],
    "Energía": ["XOM", "CVX", "SHEL", "TTE", "COP", "EOG", "PXD", "DVN", "MPC", "PSX"],
    "Consumo": ["MCD", "SBUX", "NKE", "TGT", "HD", "LOW", "TJX", "ROST", "CMG", "DHI"],
    "Volatilidad": ["VXX", "UVXY", "SVXY", "VIXY"],
    "Cripto ETFs": ["BITO", "GBTC", "ETHE", "ARKW", "BLOK"],
    "Materias Primas": ["GLD", "SLV", "USO", "UNG", "CORN", "SOYB", "WEAT"],
    "Bonos": ["AGG", "BND", "IEF", "TLT", "LQD", "HYG", "JNK", "TIP", "MUB", "SHY"],
    "Inmobiliario": ["VNQ", "XLRE", "IYR", "REIT", "HST", "EQR", "AVB", "PLD", "SPG", "AMT"]
}

# Excepción personalizada
class MarketDataError(Exception):
    """Excepción para errores en datos de mercado"""
    pass

# Clase de caché mejorada
class DataCache:
    """Sistema de caché con invalidación por tiempo y múltiples niveles"""
    
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
    
    def can_request(self, provider: str, symbol: str, min_interval_sec: int = 2) -> bool:
        """Controla frecuencia de solicitudes por proveedor/símbolo"""
        key = f"{provider}_{symbol}"
        now = datetime.now()
        
        if key in self.request_timestamps:
            elapsed = (now - self.request_timestamps[key]).total_seconds()
            if elapsed < min_interval_sec:
                return False
        
        self.request_timestamps[key] = now
        return True
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del caché"""
        total_requests = self.hit_counter + self.miss_counter
        hit_rate = (self.hit_counter / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "entradas": len(self.cache),
            "hit_rate": f"{hit_rate:.1f}%",
            "hits": self.hit_counter,
            "misses": self.miss_counter
        }

# Proveedor de datos con múltiples fuentes
class MultiSourceDataProvider:
    """Sistema de obtención de datos con múltiples fuentes y fallbacks"""
    
    def __init__(self, cache: DataCache):
        self.cache = cache
        self.setup_api_keys()
        self.yf_last_request = datetime.now() - timedelta(seconds=10)
        self.yf_semaphore = 0  # Control simple de concurrencia
        
        # Proveedores de datos disponibles (orden de prioridad)
        self.providers = ["yfinance", "alphavantage", "fcsapi", "stockdata"]
        
        # Intentos máximos por símbolo
        self.max_retries = 3
    
    def setup_api_keys(self):
        """Configura claves de API desde secrets o variables de entorno"""
        # Alpha Vantage
        try:
            self.alpha_vantage_key = st.secrets.get("alpha_vantage_api_key", 
                                                  os.environ.get("ALPHA_VANTAGE_API_KEY", ""))
        except Exception:
            self.alpha_vantage_key = ""
            
        # FCS API
        try:
            self.fcsapi_key = st.secrets.get("fcsapi_key", 
                                           os.environ.get("FCSAPI_KEY", ""))
        except Exception:
            self.fcsapi_key = ""
            
        # StockData.org
        try:
            self.stockdata_key = st.secrets.get("stockdata_key", 
                                              os.environ.get("STOCKDATA_KEY", ""))
        except Exception:
            self.stockdata_key = ""
    
    def get_market_data(self, symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        """Obtiene datos de mercado intentando múltiples fuentes"""
        # Generar clave de caché única
        cache_key = f"market_data_{symbol}_{period}_{interval}"
        
        # Verificar caché primero
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Variables para manejo de errores
        last_error = None
        tried_providers = []
        
        # Intentar cada proveedor en orden
        for provider in self.providers:
            if not self._has_credentials(provider):
                continue
                
            tried_providers.append(provider)
            try:
                # Controlar tasa de solicitudes
                if not self.cache.can_request(provider, symbol, min_interval_sec=2):
                    logger.info(f"Rate limiting para {provider}_{symbol}, saltando...")
                    continue
                
                # Obtener datos según proveedor
                if provider == "yfinance":
                    data = self._get_yfinance_data(symbol, period, interval)
                elif provider == "alphavantage":
                    data = self._get_alphavantage_data(symbol, interval)
                elif provider == "fcsapi":
                    data = self._get_fcsapi_data(symbol, interval)
                elif provider == "stockdata":
                    data = self._get_stockdata_data(symbol, interval)
                else:
                    continue
                
                # Validar resultados
                if data is not None and not data.empty and len(data) >= 5:
                    # Guardar en caché
                    self.cache.set(cache_key, data)
                    return data
            
            except Exception as e:
                logger.warning(f"Error con {provider} para {symbol}: {str(e)}")
                last_error = e
        
        # Si llegamos aquí, todos los proveedores fallaron
        logger.error(f"Todos los proveedores fallaron para {symbol}. Proveedores intentados: {tried_providers}")
        
        # Generar datos sintéticos como último recurso
        synthetic_data = self._generate_synthetic_data(symbol)
        if synthetic_data is not None:
            self.cache.set(cache_key, synthetic_data)
            return synthetic_data
        
        # Error final si no hay datos
        if last_error:
            raise last_error
        else:
            raise MarketDataError(f"No se pudieron obtener datos para {symbol} de ninguna fuente")
    
    def _has_credentials(self, provider: str) -> bool:
        """Verifica si el proveedor tiene credenciales configuradas"""
        if provider == "yfinance":
            return True  # No requiere API key
        elif provider == "alphavantage":
            return bool(self.alpha_vantage_key)
        elif provider == "fcsapi":
            return bool(self.fcsapi_key)
        elif provider == "stockdata":
            return bool(self.stockdata_key)
        return False
    
    def _get_yfinance_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Obtiene datos de Yahoo Finance con control de tasa"""
        # Control simple de concurrencia
        while self.yf_semaphore > 2:  # Máximo 3 solicitudes simultáneas
            time.sleep(0.5)
            
        # Controlar tasa de solicitudes
        time_since_last = (datetime.now() - self.yf_last_request).total_seconds()
        if time_since_last < 1.0:  # Mínimo 1 segundo entre solicitudes
            time.sleep(1.0 - time_since_last)
            
        self.yf_semaphore += 1
        self.yf_last_request = datetime.now()
        
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            
            # Normalizar estructura
            if not data.empty:
                # Corregir índice de tiempo si es necesario
                if not isinstance(data.index, pd.DatetimeIndex):
                    data.index = pd.to_datetime(data.index)
                
                # Convertir columnas a tipos numéricos si es necesario
                for col in data.columns:
                    if col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
                        data[col] = pd.to_numeric(data[col], errors="coerce")
            
            return data
        
        except Exception as e:
            logger.error(f"Error en yfinance para {symbol}: {str(e)}")
            raise e
        finally:
            self.yf_semaphore -= 1
    
    def _get_alphavantage_data(self, symbol: str, interval: str) -> pd.DataFrame:
        """Obtiene datos desde Alpha Vantage"""
        if not self.alpha_vantage_key:
            raise ValueError("API key de Alpha Vantage no configurada")
            
        # Mapear intervalo de yfinance a Alpha Vantage
        av_interval = "daily"
        if interval in ["1m", "2m", "5m", "15m", "30m", "60m", "1h"]:
            av_interval = interval.replace("m", "min").replace("h", "min").replace("1min", "1min")
            function = "TIME_SERIES_INTRADAY"
            params = f"&interval={av_interval}"
        else:
            function = "TIME_SERIES_DAILY_ADJUSTED"
            params = ""
            
        url = f"https://www.alphavantage.co/query?function={function}{params}&symbol={symbol}&outputsize=full&apikey={self.alpha_vantage_key}"
        
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"Error en Alpha Vantage API: {response.status_code}")
                
            data = response.json()
            
            # Identificar la clave de series temporales
            time_series_key = next((k for k in data.keys() if "Time Series" in k), None)
            if not time_series_key or not data.get(time_series_key):
                if "Error Message" in data:
                    raise Exception(f"Error de Alpha Vantage: {data['Error Message']}")
                raise Exception("Respuesta de Alpha Vantage sin datos de series temporales")
                
            # Convertir a DataFrame
            time_series = data[time_series_key]
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Renombrar columnas para compatibilidad con yfinance
            column_map = {
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close",
                "5. volume": "Volume",
                "5. adjusted close": "Adj Close",
                "6. volume": "Volume"
            }
            
            df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
            
            # Añadir Adj Close si no existe
            if "Adj Close" not in df.columns and "Close" in df.columns:
                df["Adj Close"] = df["Close"]
                
            # Convertir a tipos numéricos
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                
            # Establecer índice de tiempo y ordenar
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            logger.error(f"Error en Alpha Vantage para {symbol}: {str(e)}")
            raise e
    
    def _get_fcsapi_data(self, symbol: str, interval: str) -> pd.DataFrame:
        """Obtiene datos de FCS API como respaldo"""
        if not self.fcsapi_key:
            raise ValueError("API key de FCS API no configurada")
            
        # Mapear intervalo a formato FCS API
        fcs_period = "1D"
        if interval in ["1d"]:
            fcs_period = "1D"
        elif interval in ["1wk"]:
            fcs_period = "1W"
        elif interval in ["1mo"]:
            fcs_period = "1M"
        elif interval in ["1h"]:
            fcs_period = "1H"
            
        url = f"https://fcsapi.com/api-v3/stock/history?symbol={symbol}&period={fcs_period}&access_key={self.fcsapi_key}"
        
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"Error en FCS API: {response.status_code}")
                
            data = response.json()
            
            if "response" not in data or not data["response"]:
                if "msg" in data:
                    raise Exception(f"Error de FCS API: {data['msg']}")
                raise Exception("Respuesta de FCS API sin datos")
                
            # Crear DataFrame
            df = pd.DataFrame(data["response"])
            
            # Renombrar columnas para compatibilidad
            df = df.rename(columns={
                "o": "Open",
                "h": "High",
                "l": "Low",
                "c": "Close", 
                "v": "Volume",
                "tm": "Date"
            })
            
            # Añadir Adj Close
            df["Adj Close"] = df["Close"]
            
            # Convertir a tipos numéricos
            for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    
            # Establecer índice
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            logger.error(f"Error en FCS API para {symbol}: {str(e)}")
            raise e
    
    def _get_stockdata_data(self, symbol: str, interval: str) -> pd.DataFrame:
        """Obtiene datos de StockData.org API como respaldo"""
        if not self.stockdata_key:
            raise ValueError("API key de StockData.org no configurada")
            
        # Mapear intervalo
        sd_interval = "day"
        if interval in ["1d"]:
            sd_interval = "day"
        elif interval in ["1wk"]:
            sd_interval = "week"
        elif interval in ["1mo"]:
            sd_interval = "month"
            
        url = f"https://api.stockdata.org/v1/data/eod?symbols={symbol}&interval={sd_interval}&api_token={self.stockdata_key}"
        
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"Error en StockData API: {response.status_code}")
                
            data = response.json()
            
            if "data" not in data or not data["data"]:
                if "message" in data:
                    raise Exception(f"Error de StockData API: {data['message']}")
                raise Exception("Respuesta de StockData API sin datos")
                
            # Crear DataFrame
            df = pd.DataFrame(data["data"])
            
            # Expandir la columna 'values'
            if "values" in df.columns:
                values_df = pd.json_normalize(df["values"])
                df = pd.concat([df.drop("values", axis=1), values_df], axis=1)
                
            # Renombrar columnas para compatibilidad
            df = df.rename(columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
                "date": "Date"
            })
            
            # Añadir Adj Close
            df["Adj Close"] = df["Close"]
            
            # Convertir a tipos numéricos
            for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    
            # Establecer índice
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            logger.error(f"Error en StockData API para {symbol}: {str(e)}")
            raise e
    
    def _generate_synthetic_data(self, symbol: str) -> pd.DataFrame:
        """Genera datos sintéticos para fallback de UI"""
        try:
            # Crear datos determinísticos basados en el símbolo
            np.random.seed(sum(ord(c) for c in symbol))
            
            # Crear fechas para 180 días
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Precio base según iniciales del símbolo
            base_price = 50 + sum(ord(c) for c in symbol[:3]) % 950
            
            # Tendencia y volatilidad basada en el símbolo
            trend = 0.0002 * (sum(ord(c) for c in symbol) % 21 - 10)  # Entre -0.001 y 0.001
            volatility = 0.01 + 0.01 * (ord(symbol[0]) % 10) / 10  # Entre 0.01 y 0.02
            
            # Generar precios
            closes = []
            price = base_price
            
            for _ in range(len(dates)):
                change = np.random.normal(trend, volatility)
                price *= (1 + change)
                closes.append(price)
                
            # Crear OHLCV sintético realista
            df = pd.DataFrame({
                'Close': closes,
                'Adj Close': closes,
                'Open': [c * (1 - np.random.normal(0, volatility/2)) for c in closes],
                'High': [c * (1 + abs(np.random.normal(0, volatility))) for c in closes],
                'Low': [c * (1 - abs(np.random.normal(0, volatility))) for c in closes],
                'Volume': [int(np.random.normal(1e6, 2e5) * (1 + abs(np.random.normal(0, 0.3)))) for _ in closes]
            }, index=dates)
            
            # Marcar como sintético para UI
            df.attrs['synthetic'] = True
            logger.info(f"Datos sintéticos generados para {symbol}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error generando datos sintéticos: {str(e)}")
            return None

# Clase para análisis técnico
class TechnicalAnalysis:
    """Analizador técnico con implementación local para reducir dependencias"""
    
    def __init__(self, data_provider: MultiSourceDataProvider):
        self.data_provider = data_provider
    
    def get_market_data(self, symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        """Obtiene datos de mercado delegando al proveedor"""
        return self.data_provider.get_market_data(symbol, period, interval)
    
    def analyze_trend(self, symbol: str) -> Tuple[Dict, pd.DataFrame]:
        """Analiza tendencia de un símbolo"""
        try:
            # Obtener datos
            data = self.get_market_data(symbol, period="6mo", interval="1d")
            
            if data is None or data.empty or len(data) < 20:
                raise MarketDataError(f"Datos insuficientes para analizar {symbol}")
                
            # Calcular indicadores
            data = self._calculate_indicators(data)
            
            # Determinar tendencia
            trend = self._determine_trend(data)
            
            # Añadir métricas clave
            trend["metrics"] = {
                "price": float(data["Close"].iloc[-1]),
                "sma20": float(data["SMA20"].iloc[-1]) if "SMA20" in data.columns else float(data["Close"].iloc[-1]),
                "sma50": float(data["SMA50"].iloc[-1]) if "SMA50" in data.columns else float(data["Close"].iloc[-1]),
                "sma200": float(data["SMA200"].iloc[-1]) if "SMA200" in data.columns else float(data["Close"].iloc[-1]),
                "rsi": float(data["RSI"].iloc[-1]) if "RSI" in data.columns else 50.0,
                "atr": float(data["ATR"].iloc[-1]) if "ATR" in data.columns else 1.0,
                "volume": float(data["Volume"].iloc[-1])
            }
            
            return trend, data
            
        except Exception as e:
            logger.error(f"Error en analyze_trend para {symbol}: {str(e)}")
            
            # Crear trend básico para UI cuando hay errores
            empty_trend = {
                "direction": "ERROR",
                "strength": "N/A",
                "bias": "N/A",
                "description": f"Error analizando tendencia de {symbol}. {str(e)}",
                "metrics": {
                    "price": 0.0,
                    "sma20": 0.0,
                    "sma50": 0.0,
                    "sma200": 0.0,
                    "rsi": 50.0,
                    "atr": 1.0,
                    "volume": 0
                }
            }
            
            return empty_trend, pd.DataFrame()
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos básicos"""
        df = data.copy()
        
        # Medias móviles
        for period in [20, 50, 200]:
            if len(df) >= period:
                df[f"SMA{period}"] = df["Close"].rolling(window=period).mean()
        
        # RSI
        if len(df) >= 14:
            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            rs = avg_gain / avg_loss
            df["RSI"] = 100 - (100 / (1 + rs))
        
        # MACD
        if len(df) >= 26:
            ema12 = df["Close"].ewm(span=12, adjust=False).mean()
            ema26 = df["Close"].ewm(span=26, adjust=False).mean()
            df["MACD"] = ema12 - ema26
            df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
            df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
        
        # ATR
        if len(df) >= 14:
            high_low = df["High"] - df["Low"]
            high_close = (df["High"] - df["Close"].shift()).abs()
            low_close = (df["Low"] - df["Close"].shift()).abs()
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df["ATR"] = true_range.rolling(14).mean()
        
        # Bollinger Bands
        if len(df) >= 20:
            df["BB_Middle"] = df["Close"].rolling(window=20).mean()
            std = df["Close"].rolling(window=20).std()
            df["BB_Upper"] = df["BB_Middle"] + 2 * std
            df["BB_Lower"] = df["BB_Middle"] - 2 * std
        
        # Volumen relativo
        if len(df) >= 20:
            df["Volume_SMA"] = df["Volume"].rolling(window=20).mean()
            df["Volume_Ratio"] = df["Volume"] / df["Volume_SMA"]
        
        return df
    
    def _determine_trend(self, data: pd.DataFrame) -> Dict:
        """Determina tendencia y fuerza basado en indicadores"""
        # Asegurar que data no esté vacío
        if data.empty:
            return {
                "direction": "NEUTRAL",
                "strength": "BAJA",
                "bias": "NEUTRAL",
                "description": "Análisis no disponible. Datos insuficientes."
            }
            
        # Último precio
        last_close = data["Close"].iloc[-1]
        
        # Dirección basada en medias móviles
        above_sma20 = "SMA20" in data.columns and last_close > data["SMA20"].iloc[-1]
        above_sma50 = "SMA50" in data.columns and last_close > data["SMA50"].iloc[-1]
        above_sma200 = "SMA200" in data.columns and last_close > data["SMA200"].iloc[-1]
        
        # Determinar dirección
        if above_sma20 and above_sma50 and above_sma200:
            direction = "ALCISTA"
        elif not above_sma20 and not above_sma50 and not above_sma200:
            direction = "BAJISTA"
        elif above_sma200:
            direction = "ALCISTA"
        elif not above_sma200:
            direction = "BAJISTA"
        else:
            direction = "NEUTRAL"
            
        # Indicadores adicionales
        if "RSI" in data.columns:
            rsi = data["RSI"].iloc[-1]
            overbought = rsi > 70
            oversold = rsi < 30
        else:
            rsi = 50
            overbought = False
            oversold = False
            
        # Determinar fuerza
        sma_aligned = (above_sma20 and above_sma50 and above_sma200) or (not above_sma20 and not above_sma50 and not above_sma200)
        
        if sma_aligned and ((direction == "ALCISTA" and rsi > 60) or (direction == "BAJISTA" and rsi < 40)):
            strength = "ALTA"
        elif sma_aligned:
            strength = "MEDIA"
        else:
            strength = "BAJA"
            
        # Determinar sesgo
        if direction == "ALCISTA":
            if overbought:
                bias = "SOBRECOMPRADO"
            elif above_sma20 and above_sma50:
                bias = "ALCISTA"
            else:
                bias = "NEUTRO-ALCISTA"
        elif direction == "BAJISTA":
            if oversold:
                bias = "SOBREVENDIDO"
            elif not above_sma20 and not above_sma50:
                bias = "BAJISTA"
            else:
                bias = "NEUTRO-BAJISTA"
        else:
            bias = "NEUTRAL"
            
        # Crear descripción
        description = self._create_trend_description(direction, strength, bias, {
            "price": last_close,
            "sma20": data["SMA20"].iloc[-1] if "SMA20" in data.columns else None,
            "sma50": data["SMA50"].iloc[-1] if "SMA50" in data.columns else None,
            "sma200": data["SMA200"].iloc[-1] if "SMA200" in data.columns else None,
            "rsi": rsi
        })
        
        return {
            "direction": direction,
            "strength": strength,
            "bias": bias,
            "description": description
        }
    
    def _create_trend_description(self, direction: str, strength: str, bias: str, metrics: Dict) -> str:
        """Crea descripción textual de la tendencia"""
        descriptions = {
            "ALCISTA": {
                "ALTA": "Tendencia alcista fuerte y sostenida.",
                "MEDIA": "Tendencia alcista moderada con posible continuación.",
                "BAJA": "Tendencia alcista débil o en desarrollo."
            },
            "BAJISTA": {
                "ALTA": "Tendencia bajista fuerte y sostenida.",
                "MEDIA": "Tendencia bajista moderada con posible continuación.",
                "BAJA": "Tendencia bajista débil o en desarrollo."
            },
            "NEUTRAL": {
                "ALTA": "Mercado en consolidación con alta presión compradora/vendedora.",
                "MEDIA": "Mercado en rango con presión equilibrada.",
                "BAJA": "Mercado sin dirección clara, esperando catalizador."
            }
        }
        
        # Descripción base
        base = descriptions.get(direction, {}).get(strength, "Análisis no disponible.")
        
        # Añadir contexto de sesgo
        if bias == "SOBRECOMPRADO":
            context = " Indicadores muestran condición de sobrecompra, posible corrección."
        elif bias == "SOBREVENDIDO":
            context = " Indicadores muestran condición de sobreventa, posible rebote."
        elif bias.startswith("NEUTRO"):
            context = " Indicadores en zona neutral con sesgo " + bias.split("-")[1].lower() + "."
        else:
            context = ""
            
        # Añadir detalles técnicos si están disponibles
        details = ""
        if all(v is not None for v in [metrics.get("price"), metrics.get("sma200")]):
            price = metrics["price"]
            sma200 = metrics["sma200"]
            pct_diff = (price / sma200 - 1) * 100
            
            if abs(pct_diff) < 3:
                details = f" Precio cerca de SMA200 ({pct_diff:.1f}%)."
            elif pct_diff > 0:
                details = f" Precio {pct_diff:.1f}% por encima de SMA200."
            else:
                details = f" Precio {abs(pct_diff):.1f}% por debajo de SMA200."
                
        # Combinar todo
        return base + context + details
    
    def identify_strategy(self, data: pd.DataFrame, trend: Dict) -> List[Dict]:
        """Identifica estrategias operativas basadas en tendencia y datos"""
        if data is None or data.empty or len(data) < 20:
            return []
            
        # Calcular indicadores si no existen
        if "SMA20" not in data.columns:
            data = self._calculate_indicators(data)
            
        strategies = []
        last_close = data["Close"].iloc[-1]
        
        # Fuerza de tendencia
        trend_direction = trend["direction"]
        trend_strength = trend["strength"]
        trend_bias = trend["bias"]
        
        # Detectar estrategias según condiciones
        if trend_direction == "ALCISTA":
            # Estrategia: Gap al Alza
            if self._check_gap_up_pattern(data):
                strategies.append({
                    "type": "CALL",
                    "name": "Gap al Alza",
                    "confidence": "ALTA" if trend_strength == "ALTA" else "MEDIA",
                    "description": "Gap alcista en zona de soporte como señal de continuación.",
                    "conditions": [
                        "Gap alcista identificado",
                        "Precio por encima de SMA20",
                        "RSI con momentum positivo"
                    ],
                    "levels": {
                        "entry": last_close,
                        "stop": last_close * 0.98,  # 2% por debajo
                        "target": last_close * 1.06  # 6% por encima
                    }
                })
                
            # Estrategia: Pullback a SMA20
            elif self._check_pullback_to_sma(data):
                strategies.append({
                    "type": "CALL",
                    "name": "Pullback a SMA20",
                    "confidence": "ALTA" if trend_strength == "ALTA" else "MEDIA",
                    "description": "Corrección técnica hacia soporte de SMA20 en tendencia alcista.",
                    "conditions": [
                        "Precio tocando SMA20",
                        "Tendencia general alcista",
                        "Volumen decreciente en pullback"
                    ],
                    "levels": {
                        "entry": last_close,
                        "stop": last_close * 0.97,  # 3% por debajo
                        "target": last_close * 1.05  # 5% por encima
                    }
                })
                
        elif trend_direction == "BAJISTA":
            # Estrategia: Ruptura de Soporte
            if self._check_support_breakdown(data):
                strategies.append({
                    "type": "PUT",
                    "name": "Ruptura de Soporte",
                    "confidence": "ALTA" if trend_strength == "ALTA" else "MEDIA",
                    "description": "Ruptura de nivel de soporte clave en tendencia bajista.",
                    "conditions": [
                        "Precio rompe por debajo de soporte",
                        "Tendencia general bajista",
                        "Incremento de volumen en ruptura"
                    ],
                    "levels": {
                        "entry": last_close,
                        "stop": last_close * 1.03,  # 3% por encima
                        "target": last_close * 0.94  # 6% por debajo
                    }
                })
                
            # Estrategia: Rechazo de Resistencia
            elif self._check_resistance_rejection(data):
                strategies.append({
                    "type": "PUT",
                    "name": "Rechazo de Resistencia",
                    "confidence": "ALTA" if trend_strength == "ALTA" else "MEDIA",
                    "description": "Precio rechazado en zona de resistencia en tendencia bajista.",
                    "conditions": [
                        "Resistencia claramente definida",
                        "Patrón de rechazo formado",
                        "Momentum bajista confirmado"
                    ],
                    "levels": {
                        "entry": last_close,
                        "stop": last_close * 1.04,  # 4% por encima
                        "target": last_close * 0.93  # 7% por debajo
                    }
                })
        
        # Estrategias adicionales independientes de la tendencia
        
        # RSI divergencias
        if self._check_rsi_divergence(data):
            div_type = "Positiva" if self._is_bullish_divergence(data) else "Negativa"
            
            strategies.append({
                "type": "CALL" if div_type == "Positiva" else "PUT",
                "name": f"Divergencia {div_type}",
                "confidence": "MEDIA",
                "description": f"Divergencia {div_type.lower()} entre precio y RSI sugiriendo posible cambio de tendencia.",
                "conditions": [
                    f"Divergencia {div_type.lower()} confirmada",
                    "RSI mostrando pérdida de momentum",
                    "Patrón de velas confirmatorio"
                ],
                "levels": {
                    "entry": last_close,
                    "stop": last_close * 0.96 if div_type == "Positiva" else last_close * 1.04,
                    "target": last_close * 1.08 if div_type == "Positiva" else last_close * 0.92
                }
            })
            
        return strategies
    
    def _check_gap_up_pattern(self, data: pd.DataFrame) -> bool:
        """Verifica patrón de gap alcista"""
        try:
            if len(data) < 5:
                return False
                
            # Últimas 5 barras
            recent = data.iloc[-5:]
            
            # Verificar gap
            for i in range(1, len(recent)):
                gap_up = recent["Open"].iloc[i] > recent["Close"].iloc[i-1]
                if gap_up:
                    return True
                    
            return False
        except Exception:
            return False
    
    def _check_pullback_to_sma(self, data: pd.DataFrame) -> bool:
        """Verifica pullback a SMA20"""
        try:
            if "SMA20" not in data.columns or len(data) < 10:
                return False
                
            # Últimas 10 barras
            recent = data.iloc[-10:]
            
            # Precio cercano a SMA20
            last_close = recent["Close"].iloc[-1]
            last_sma20 = recent["SMA20"].iloc[-1]
            
            # Dentro de 1% de SMA20
            close_to_sma = abs(last_close / last_sma20 - 1) < 0.01
            
            if close_to_sma:
                return True
                
            return False
        except Exception:
            return False
    
    def _check_support_breakdown(self, data: pd.DataFrame) -> bool:
        """Verifica ruptura de soporte"""
        try:
            if len(data) < 20:
                return False
                
            # Últimos 20 barras
            recent = data.iloc[-20:]
            
            # Calcular mínimos recientes
            lows = recent["Low"].rolling(window=2).min()
            
            # Últimos 3 mínimos
            recent_lows = lows.dropna().iloc[-3:].values
            
            # Si el último mínimo es menor que los anteriores
            if recent_lows[-1] < min(recent_lows[:-1]):
                return True
                
            return False
        except Exception:
            return False
    
    def _check_resistance_rejection(self, data: pd.DataFrame) -> bool:
        """Verifica rechazo en resistencia"""
        try:
            if len(data) < 20:
                return False
                
            # Últimos 20 barras
            recent = data.iloc[-20:]
            
            # Calcular máximos recientes
            highs = recent["High"].rolling(window=2).max()
            
            # Últimos 3 máximos
            recent_highs = highs.dropna().iloc[-3:].values
            
            # Si el último precio cerró por debajo del último máximo
            last_close = recent["Close"].iloc[-1]
            last_high = recent["High"].iloc[-1]
            
            rejection = (last_high >= max(recent_highs[:-1])) and (last_close < last_high * 0.99)
            
            return rejection
        except Exception:
            return False
    
    def _check_rsi_divergence(self, data: pd.DataFrame) -> bool:
        """Verifica divergencias de RSI"""
        try:
            if "RSI" not in data.columns or len(data) < 20:
                return False
                
            return self._is_bullish_divergence(data) or self._is_bearish_divergence(data)
        except Exception:
            return False
    
    def _is_bullish_divergence(self, data: pd.DataFrame) -> bool:
        """Verifica divergencia alcista (precios hacen mínimos más bajos, RSI hace mínimos más altos)"""
        try:
            # Últimos 20 barras
            recent = data.iloc[-20:]
            
            # Encontrar mínimos en precio
            price_min1 = recent["Low"].iloc[-10:-5].min()
            price_min2 = recent["Low"].iloc[-5:].min()
            
            # Encontrar mínimos en RSI correspondientes
            price_min1_idx = recent["Low"].iloc[-10:-5].idxmin()
            price_min2_idx = recent["Low"].iloc[-5:].idxmin()
            
            rsi_min1 = data.loc[price_min1_idx, "RSI"]
            rsi_min2 = data.loc[price_min2_idx, "RSI"]
            
            # Divergencia alcista: precio hace mínimos más bajos, RSI hace mínimos más altos
            return (price_min2 < price_min1) and (rsi_min2 > rsi_min1)
        except Exception:
            return False
    
    def _is_bearish_divergence(self, data: pd.DataFrame) -> bool:
        """Verifica divergencia bajista (precios hacen máximos más altos, RSI hace máximos más bajos)"""
        try:
            # Últimos 20 barras
            recent = data.iloc[-20:]
            
            # Encontrar máximos en precio
            price_max1 = recent["High"].iloc[-10:-5].max()
            price_max2 = recent["High"].iloc[-5:].max()
            
            # Encontrar máximos en RSI correspondientes
            price_max1_idx = recent["High"].iloc[-10:-5].idxmax()
            price_max2_idx = recent["High"].iloc[-5:].idxmax()
            
            rsi_max1 = data.loc[price_max1_idx, "RSI"]
            rsi_max2 = data.loc[price_max2_idx, "RSI"]
            
            # Divergencia bajista: precio hace máximos más altos, RSI hace máximos más bajos
            return (price_max2 > price_max1) and (rsi_max2 < rsi_max1)
        except Exception:
            return False

# Clase para escaneo de mercado
class MarketScanner:
    """Escáner de mercado con múltiples criterios y optimizado"""
    
    def __init__(self, symbols: Dict[str, List[str]], technical_analyzer: TechnicalAnalysis):
        self.symbols = symbols
        self.analyzer = technical_analyzer
        self.cache = {}  # Caché de análisis recientes
        self.last_scan_time = None
    
    def get_cached_analysis(self, symbol: str) -> Optional[Dict]:
        """Obtiene análisis cacheado si existe"""
        if symbol in self.cache:
            return self.cache[symbol]
        return None
    
    def scan_market(self, selected_sectors: Optional[List[str]] = None) -> pd.DataFrame:
        """Ejecuta escaneo de mercado con criterios especificados"""
        try:
            # Actualizar timestamp
            self.last_scan_time = datetime.now()
            
            # Preparar símbolos a escanear
            symbols_to_scan = {}
            if selected_sectors:
                for sector in selected_sectors:
                    if sector in self.symbols:
                        symbols_to_scan[sector] = self.symbols[sector]
            else:
                symbols_to_scan = self.symbols
                
            results = []
            
            # Procesar cada sector y símbolo
            for sector, symbols in symbols_to_scan.items():
                for symbol in symbols:
                    try:
                        # Obtener análisis de tendencia
                        trend, data = self.analyzer.analyze_trend(symbol)
                        
                        # Encontrar estrategias
                        if not data.empty:
                            strategies = self.analyzer.identify_strategy(data, trend)
                        else:
                            strategies = []
                            
                        # Cachear resultados
                        self.cache[symbol] = {
                            "trend_data": trend,
                            "price_data": data,
                            "strategies": strategies,
                            "timestamp": datetime.now()
                        }
                        
                        # Añadir cada estrategia al resultado
                        for strategy in strategies:
                            results.append({
                                "Symbol": symbol,
                                "Sector": sector,
                                "Tendencia": trend["direction"],
                                "Fuerza": trend["strength"],
                                "Precio": trend["metrics"]["price"],
                                "RSI": trend["metrics"]["rsi"],
                                "Estrategia": strategy["type"],
                                "Setup": strategy["name"],
                                "Confianza": strategy["confidence"],
                                "Entry": strategy["levels"]["entry"],
                                "Stop": strategy["levels"]["stop"],
                                "Target": strategy["levels"]["target"],
                                "R/R": round((strategy["levels"]["target"] - strategy["levels"]["entry"]) / 
                                           (strategy["levels"]["entry"] - strategy["levels"]["stop"]), 2),
                                "Timestamp": datetime.now().strftime("%H:%M:%S")
                            })
                            
                    except Exception as e:
                        logger.error(f"Error escaneando {symbol}: {str(e)}")
                        continue
                        
            # Convertir resultados a DataFrame
            if results:
                df = pd.DataFrame(results)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error en scan_market: {str(e)}")
            return pd.DataFrame()

# Funciones auxiliares
def get_market_status() -> Dict:
    """
    Obtiene el estado del mercado actual
    """
    try:
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(ny_tz)
        
        # Determinar sesión por hora NY
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()  # 0-6 = Lunes-Domingo
        
        # Verificar si es fin de semana
        if weekday >= 5:  # Sábado o Domingo
            session = "CERRADO"
        elif 4 <= hour < 9:  # 4:00 AM - 9:00 AM
            session = "PRE-MARKET"
        elif 9 <= hour < 16:  # 9:00 AM - 4:00 PM
            session = "REGULAR"
        elif 16 <= hour < 20:  # 4:00 PM - 8:00 PM
            session = "AFTER-HOURS"
        else:
            session = "CERRADO"
            
        return {
            "time": now.strftime("%H:%M:%S"),
            "session": session,
            "day": now.strftime("%d/%m/%Y"),
            "weekday": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][weekday],
            "next_update": st.session_state.get("last_scan_time", datetime.now()).strftime("%H:%M:%S") if "last_scan_time" in st.session_state else "N/A"
        }
    except Exception as e:
        logger.error(f"Error en market_status: {str(e)}")
        return {
            "time": datetime.now().strftime("%H:%M:%S"),
            "session": "ERROR",
            "day": datetime.now().strftime("%d/%m/%Y"),
            "weekday": "Error",
            "next_update": "N/A"
        }

# Inicialización de estado de sesión
def initialize_session():
    """Inicializa el estado de la sesión"""
    if 'data_cache' not in st.session_state:
        st.session_state.data_cache = DataCache()
        
    if 'data_provider' not in st.session_state:
        st.session_state.data_provider = MultiSourceDataProvider(st.session_state.data_cache)
        
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = TechnicalAnalysis(st.session_state.data_provider)
        
    if 'scanner' not in st.session_state:
        st.session_state.scanner = MarketScanner(SYMBOLS, st.session_state.analyzer)
        
    if 'current_symbol' not in st.session_state:
        st.session_state.current_symbol = "SPY"
        
    if 'last_scan_time' not in st.session_state:
        st.session_state.last_scan_time = None
        
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = pd.DataFrame()
        
    if 'last_scan_sectors' not in st.session_state:
        st.session_state.last_scan_sectors = None
        
# Función principal
def main():
    # Configuración de página
    st.set_page_config(
        page_title="InversorIA Mini Pro",
        page_icon="📊",
        layout="wide"
    )
    
    # Inicializar estado de sesión
    initialize_session()
    
    # Cabecera y barra superior
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    # Información de mercado
    market_status = get_market_status()
    with col1:
        st.metric("Hora NY", market_status["time"])
    with col2:
        st.metric("Sesión", market_status["session"], 
                 help="Pre-market: 4:00-9:30 AM NY\nRegular: 9:30 AM-4:00 PM NY\nAfter-Hours: 4:00-8:00 PM NY")
    with col3:
        st.metric("Caché", f"{len(st.session_state.data_cache.cache)} items", 
                 help="Elementos en caché para optimizar rendimiento y evitar rate limiting")
    with col4:
        cache_stats = st.session_state.data_cache.get_stats()
        st.metric("Hit Rate", cache_stats["hit_rate"],
                 help="Porcentaje de solicitudes servidas desde caché")
    
    # Interface principal con dashboard unificado
    st.title("📊 InversorIA Mini Pro")
    
    # Contenedor principal
    main_container = st.container()
    
    with main_container:
        # Panel de control superior
        control_col1, control_col2, control_col3 = st.columns([2, 1, 1])
        
        with control_col1:
            selected_sectors = st.multiselect(
                "Sectores a Monitorear",
                list(SYMBOLS.keys()),
                default=["Índices", "Tecnología"] if st.session_state.last_scan_sectors is None else st.session_state.last_scan_sectors,
                help="Seleccione sectores para análisis y escaneo"
            )
            
        with control_col2:
            confidence_filter = st.selectbox(
                "Filtro de Confianza",
                ["Todas", "Alta", "Media"],
                index=0,
                help="Filtrar señales por nivel de confianza"
            )
            
        with control_col3:
            scan_col1, scan_col2 = st.columns(2)
            with scan_col1:
                if st.button("🔍 Escanear", use_container_width=True):
                    with st.spinner("Escaneando mercado..."):
                        st.session_state.last_scan_sectors = selected_sectors
                        st.session_state.scan_results = st.session_state.scanner.scan_market(selected_sectors)
                        st.session_state.last_scan_time = datetime.now()
                        
            with scan_col2:
                if st.button("🗑️ Limpiar", use_container_width=True):
                    st.session_state.data_cache.clear()
                    st.success("Caché limpiado correctamente")
                    time.sleep(0.5)
                    st.experimental_rerun()
        
        # Panel principal dividido en dos secciones
        results_col, details_col = st.columns([1.4, 1])
        
        # Panel de resultados del scanner (izquierda)
        with results_col:
            st.subheader("📡 Scanner de Mercado")
            
            # Verificar si hay resultados
            if hasattr(st.session_state, 'scan_results') and not st.session_state.scan_results.empty:
                # Mostrar estadísticas
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                
                with stats_col1:
                    total_calls = len(st.session_state.scan_results[st.session_state.scan_results["Estrategia"] == "CALL"])
                    st.metric("Señales CALL", total_calls, help="Oportunidades alcistas detectadas")
                    
                with stats_col2:
                    total_puts = len(st.session_state.scan_results[st.session_state.scan_results["Estrategia"] == "PUT"])
                    st.metric("Señales PUT", total_puts, help="Oportunidades bajistas detectadas")
                    
                with stats_col3:
                    st.metric("Total Oportunidades", len(st.session_state.scan_results),
                             help="Total de señales operativas detectadas")
                
                # Aplicar filtro de confianza si corresponde
                filtered_results = st.session_state.scan_results
                if confidence_filter != "Todas":
                    filtered_results = filtered_results[filtered_results["Confianza"] == confidence_filter.upper()]
                
                # Mostrar tabla de resultados
                if not filtered_results.empty:
                    # Columnas a mostrar
                    display_columns = [
                        "Symbol", "Sector", "Estrategia", "Setup", "Confianza", 
                        "Precio", "RSI", "Entry", "Stop", "Target", "R/R"
                    ]
                    
                    # Asegurar que todas las columnas existen
                    for col in display_columns:
                        if col not in filtered_results.columns:
                            filtered_results[col] = "N/A"
                    
                    # Tabla interactiva con colores y formato
                    st.dataframe(
                        filtered_results[display_columns].style
                        .format({
                            "Precio": "${:.2f}",
                            "RSI": "{:.1f}",
                            "Entry": "${:.2f}",
                            "Stop": "${:.2f}",
                            "Target": "${:.2f}",
                            "R/R": "{:.2f}"
                        })
                        .apply(lambda x: [
                            "background-color: #c8e6c9" if x["Estrategia"] == "CALL" else
                            "background-color: #ffcdd2" if x["Estrategia"] == "PUT" else
                            "" for i in range(len(x))
                        ], axis=1),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Symbol": "Símbolo",
                            "Estrategia": st.column_config.SelectboxColumn(
                                "Tipo",
                                options=["CALL", "PUT"],
                                required=True,
                            ),
                            "Setup": "Estrategia",
                            "Entry": "Entrada",
                            "Stop": "Stop Loss",
                            "Target": "Objetivo"
                        }
                    )
                    
                    # Análisis por sector si hay sectores seleccionados
                    if selected_sectors:
                        st.markdown("---")
                        st.markdown("### 📈 Análisis por Sector")
                        
                        sector_cols = st.columns(min(3, len(selected_sectors)))
                        for i, sector in enumerate(selected_sectors):
                            col = sector_cols[i % len(sector_cols)]
                            with col:
                                sector_data = filtered_results[filtered_results["Sector"] == sector]
                                if not sector_data.empty:
                                    with st.expander(f"{sector} ({len(sector_data)} señales)"):
                                        call_count = len(sector_data[sector_data["Estrategia"] == "CALL"])
                                        put_count = len(sector_data[sector_data["Estrategia"] == "PUT"])
                                        high_conf = len(sector_data[sector_data["Confianza"] == "ALTA"])
                                        
                                        st.info(f"""
                                        **Señales:** {len(sector_data)}
                                        - CALL: {call_count} ({call_count/len(sector_data)*100:.0f}%)
                                        - PUT: {put_count} ({put_count/len(sector_data)*100:.0f}%)
                                        - Alta Confianza: {high_conf} ({high_conf/len(sector_data)*100:.0f}%)
                                        """)
                                        
                                        symbols = sector_data["Symbol"].unique()
                                        st.markdown(f"**Símbolos con señales:** {', '.join(symbols)}")
                                else:
                                    st.info(f"No hay señales para {sector} con los filtros actuales")
                else:
                    st.warning("No hay resultados que cumplan con los criterios de filtrado")
            else:
                # Mensaje si no hay escaneo reciente
                st.info("""
                ### Sin datos de escaneo reciente
                
                Realice un escaneo para identificar señales de trading en los mercados seleccionados.
                
                **Recomendaciones:**
                - Seleccione los sectores que desea analizar
                - Pulse el botón "Escanear" para iniciar el análisis
                - Los resultados se mostrarán en esta sección
                """)
        
        # Panel de análisis individual (derecha)
        with details_col:
            st.subheader("🔬 Análisis Individual")
            
            # Selector de símbolo y sector
            symbol_col1, symbol_col2 = st.columns(2)
            
            with symbol_col1:
                category = st.selectbox("Sector", list(SYMBOLS.keys()))
                
            with symbol_col2:
                symbol = st.selectbox("Activo", SYMBOLS[category])
                
            if symbol != st.session_state.current_symbol:
                st.session_state.current_symbol = symbol
            
            # Análisis del símbolo seleccionado
            try:
                with st.spinner("Analizando..."):
                    # Verificar caché
                    cached_analysis = st.session_state.scanner.get_cached_analysis(symbol)
                    
                    if cached_analysis:
                        trend = cached_analysis["trend_data"]
                        data = cached_analysis.get("price_data", pd.DataFrame())
                        strategies = cached_analysis["strategies"]
                        timestamp = cached_analysis["timestamp"]
                        from_cache = True
                    else:
                        # Obtener nuevo análisis
                        trend, data = st.session_state.analyzer.analyze_trend(symbol)
                        strategies = st.session_state.analyzer.identify_strategy(data, trend)
                        timestamp = datetime.now()
                        from_cache = False
                    
                    # Mostrar indicadores clave
                    st.markdown(f"#### Análisis Técnico: {symbol}")
                    
                    if from_cache:
                        st.caption(f"Datos de caché: {(datetime.now() - timestamp).total_seconds():.0f} segundos atrás")
                    
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    with metric_col1:
                        direction_arrow = "↑" if trend["direction"] == "ALCISTA" else "↓" if trend["direction"] == "BAJISTA" else "→"
                        st.metric("Tendencia", f"{trend['direction']} {direction_arrow}")
                        
                    with metric_col2:
                        st.metric("Fuerza", trend["strength"])
                        
                    with metric_col3:
                        st.metric("Sesgo", trend["bias"])
                    
                    # Descripción de tendencia
                    st.info(trend["description"])
                    
                    # Métricas técnicas detalladas
                    st.markdown("##### Métricas Técnicas")
                    tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
                    
                    with tech_col1:
                        price_val = trend["metrics"].get("price", 0)
                        st.metric("Precio", f"${price_val:.2f}" if isinstance(price_val, (int, float)) else "N/A")
                        
                    with tech_col2:
                        sma_val = trend["metrics"].get("sma200", 0)
                        st.metric("SMA200", f"${sma_val:.2f}" if isinstance(sma_val, (int, float)) else "N/A")
                        
                    with tech_col3:
                        rsi_val = trend["metrics"].get("rsi", 0)
                        
                        # Color según rango de RSI
                        rsi_color = "#d32f2f" if rsi_val > 70 else "#388e3c" if rsi_val < 30 else "#1976d2"
                        
                        st.markdown(
                            f"""<div style="background-color: {rsi_color}; 
                                 padding: 10px; border-radius: 5px; color: white; 
                                 text-align: center; font-weight: bold;">
                                 RSI: {rsi_val:.1f}
                                 </div>""", 
                            unsafe_allow_html=True
                        )
                        
                    with tech_col4:
                        try:
                            if price_val > 0 and sma_val > 0:
                                dist = ((price_val / sma_val) - 1) * 100
                                dist_color = "#388e3c" if dist > 0 else "#d32f2f"
                                
                                st.markdown(
                                    f"""<div style="background-color: {dist_color}; 
                                         padding: 10px; border-radius: 5px; color: white; 
                                         text-align: center; font-weight: bold;">
                                         {dist:.1f}% vs SMA200
                                         </div>""", 
                                    unsafe_allow_html=True
                                )
                            else:
                                st.metric("Dist. SMA200", "N/A")
                        except (ZeroDivisionError, TypeError):
                            st.metric("Dist. SMA200", "N/A")
                    
                    # Estrategias operativas
                    if strategies:
                        st.markdown("##### Señales Activas")
                        
                        for strat in strategies:
                            with st.expander(f"{strat.get('type', 'N/A')} - {strat.get('name', 'N/A')} (Confianza: {strat.get('confidence', 'N/A')})"):
                                # Panel de estrategia
                                strat_col1, strat_col2 = st.columns([1, 1])
                                
                                with strat_col1:
                                    st.markdown("**Descripción:**")
                                    st.write(strat.get('description', 'No disponible'))
                                    
                                    st.markdown("**Condiciones:**")
                                    for condition in strat.get('conditions', ['No disponible']):
                                        st.write(f"✓ {condition}")
                                
                                with strat_col2:
                                    if 'levels' in strat:
                                        # Formatear niveles como tarjetas
                                        entry_val = strat['levels'].get('entry', 0)
                                        stop_val = strat['levels'].get('stop', 0)
                                        target_val = strat['levels'].get('target', 0)
                                        
                                        # Calcular R/R
                                        try:
                                            r_r = (target_val - entry_val) / (entry_val - stop_val)
                                        except (ZeroDivisionError, TypeError):
                                            r_r = 0
                                        
                                        # Colores según tipo
                                        header_color = "#388e3c" if strat['type'] == "CALL" else "#d32f2f"
                                        
                                        st.markdown(
                                            f"""<div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                                                <div style="background-color: {header_color}; color: white; padding: 5px; border-radius: 3px; text-align: center; margin-bottom: 10px;">
                                                    <strong>NIVELES OPERATIVOS</strong>
                                                </div>
                                                <table style="width: 100%;">
                                                    <tr>
                                                        <td style="padding: 5px; text-align: right;"><strong>Entrada:</strong></td>
                                                        <td style="padding: 5px;">${entry_val:.2f}</td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 5px; text-align: right;"><strong>Stop Loss:</strong></td>
                                                        <td style="padding: 5px;">${stop_val:.2f}</td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 5px; text-align: right;"><strong>Objetivo:</strong></td>
                                                        <td style="padding: 5px;">${target_val:.2f}</td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding: 5px; text-align: right;"><strong>Ratio R/R:</strong></td>
                                                        <td style="padding: 5px;">{r_r:.2f}</td>
                                                    </tr>
                                                </table>
                                            </div>""",
                                            unsafe_allow_html=True
                                        )
                        
                        # Panel de gestión de riesgo
                        st.markdown("##### Gestión de Riesgo")
                        
                        # Calculadora de riesgo
                        risk_col1, risk_col2, risk_col3 = st.columns([1, 1, 1])
                        
                        with risk_col1:
                            position_size = st.slider(
                                "Capital en Riesgo (%)",
                                min_value=0.5,
                                max_value=5.0,
                                value=2.0,
                                step=0.5
                            )
                            
                        with risk_col2:
                            account_size = st.number_input(
                                "Tamaño de Cuenta ($)",
                                min_value=1000,
                                max_value=1000000,
                                value=10000,
                                step=1000
                            )
                            
                        with risk_col3:
                            risk_amount = position_size / 100 * account_size
                            st.metric(
                                "Riesgo Máximo ($)",
                                f"${risk_amount:.2f}",
                                delta=f"{position_size}% del capital"
                            )
                            
                    else:
                        st.warning("""
                        **Sin Señales Activas**
                        - No hay setup válido actualmente
                        - Mantener disciplina y esperar mejor oportunidad
                        - Continuar monitoreando para nuevas señales
                        """)
                        
            except Exception as e:
                st.error(f"Error en análisis: {str(e)}")
                
                # Mostrar detalles del error si está en modo depuración
                with st.expander("Detalles técnicos"):
                    st.code(traceback.format_exc())
    
    # Footer con disclaimer
    st.markdown("---")
    st.caption("""
    **⚠️ Disclaimer:** Este sistema proporciona análisis técnico cuantitativo y requiere validación profesional.
    Trading implica riesgo sustancial de pérdida. Realizar due diligence exhaustivo antes de cualquier operación.
    La información presentada no constituye asesoramiento financiero.
    """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error crítico: {str(e)}")
        
        with st.expander("Detalles técnicos"):
            st.code(traceback.format_exc())