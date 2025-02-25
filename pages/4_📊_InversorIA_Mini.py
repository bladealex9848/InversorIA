import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import traceback
import time
import requests
import os
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple

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

# Excepción personalizada para datos de mercado
class MarketDataError(Exception):
    """Excepción para errores en datos de mercado"""
    pass

# Clase de caché para datos
class DataCache:
    """Sistema de caché con invalidación por tiempo"""
    
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
        hit_rate = (self.hit_counter / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "entradas": len(self.cache),
            "hit_rate": f"{hit_rate:.1f}%",
            "hits": self.hit_counter,
            "misses": self.miss_counter
        }

# Proveedor de datos de mercado
class MarketDataProvider:
    """Proveedor de datos de mercado con manejo de errores y limitación de tasa"""
    
    def __init__(self, cache: DataCache):
        self.cache = cache
        self.alpha_vantage_key = self._get_api_key("alpha_vantage_api_key")
        self.last_request = datetime.now() - timedelta(seconds=10)
        self.request_count = 0
        self.max_requests_per_minute = 5  # Muy conservador para evitar rate limiting
    
    def _get_api_key(self, key_name: str) -> str:
        """Obtiene clave de API desde secrets o variables de entorno"""
        try:
            return st.secrets.get(key_name, os.environ.get(key_name.upper(), ""))
        except Exception:
            return ""
    
    def _rate_limit(self):
        """Controla la tasa de solicitudes"""
        now = datetime.now()
        time_since_last = (now - self.last_request).total_seconds()
        
        # Reset counter cada minuto
        if time_since_last > 60:
            self.request_count = 0
        
        # Incrementar contador
        self.request_count += 1
        
        # Si excedemos el límite, esperamos
        if self.request_count > self.max_requests_per_minute:
            sleep_time = max(5, 60 - time_since_last)
            logger.info(f"Rate limiting aplicado, esperando {sleep_time:.1f}s")
            time.sleep(sleep_time)
            self.request_count = 1
        
        # Siempre asegurar al menos 2 segundos entre solicitudes
        elif time_since_last < 2:
            time.sleep(2 - time_since_last)
        
        self.last_request = datetime.now()
    
    def get_market_data(self, symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        """Obtiene datos de mercado con manejo de errores"""
        # Clave de caché
        cache_key = f"market_data_{symbol}_{period}_{interval}"
        
        # Intentar obtener de caché
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Controlar frecuencia de solicitudes
        if not self.cache.can_request(symbol):
            logger.info(f"Limitando solicitudes para {symbol}, usando datos sintéticos temporales")
            return self._generate_synthetic_data(symbol)
        
        try:
            # Aplicar rate limiting
            self._rate_limit()
            
            # Obtener datos con YFinance
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            
            # Validar datos
            if data is None or data.empty or len(data) < 5:
                logger.warning(f"Datos insuficientes para {symbol}, usando Alpha Vantage como respaldo")
                
                # Intentar con Alpha Vantage si está configurado
                if self.alpha_vantage_key:
                    data = self._get_alpha_vantage_data(symbol, interval)
                
                # Si aún no hay datos, generar sintéticos
                if data is None or data.empty or len(data) < 5:
                    logger.warning(f"Fallback a datos sintéticos para {symbol}")
                    data = self._generate_synthetic_data(symbol)
            
            # Validación y corrección de tipos
            data = self._validate_and_fix_data(data)
            
            # Guardar en caché
            self.cache.set(cache_key, data)
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            
            # Intentar con Alpha Vantage como respaldo
            if self.alpha_vantage_key:
                try:
                    data = self._get_alpha_vantage_data(symbol, interval)
                    if data is not None and not data.empty:
                        self.cache.set(cache_key, data)
                        return data
                except Exception as av_e:
                    logger.error(f"Error en Alpha Vantage para {symbol}: {str(av_e)}")
            
            # Si todo falla, usar datos sintéticos
            synth_data = self._generate_synthetic_data(symbol)
            self.cache.set(cache_key, synth_data)
            return synth_data
    
    def _validate_and_fix_data(self, data: pd.DataFrame) -> pd.DataFrame:
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
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in data.columns:
                if col == 'Volume':
                    data[col] = 0  # Valor por defecto para volumen
                else:
                    # Si falta una columna crítica, usar Close
                    data[col] = data['Close'] if 'Close' in data.columns else 0
        
        # Convertir a tipos numéricos
        for col in required_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Rellenar valores NaN
        data = data.fillna(method='ffill').fillna(method='bfill').fillna(0)
        
        return data
    
    def _get_alpha_vantage_data(self, symbol: str, interval: str) -> pd.DataFrame:
        """Obtiene datos desde Alpha Vantage como respaldo"""
        if not self.alpha_vantage_key:
            return None
            
        try:
            # Mapear intervalo
            av_function = "TIME_SERIES_DAILY"
            av_interval = None
            
            if interval in ["1m", "5m", "15m", "30m", "60m", "1h"]:
                av_function = "TIME_SERIES_INTRADAY"
                av_interval = interval.replace("m", "min").replace("h", "min").replace("60min", "60min")
            
            # Construir URL
            url_params = f"&interval={av_interval}" if av_interval else ""
            url = f"https://www.alphavantage.co/query?function={av_function}&symbol={symbol}&outputsize=full{url_params}&apikey={self.alpha_vantage_key}"
            
            # Realizar solicitud
            response = requests.get(url)
            data = response.json()
            
            # Parsear respuesta
            time_series_key = next((k for k in data.keys() if "Time Series" in k), None)
            
            if not time_series_key or time_series_key not in data:
                raise ValueError(f"Datos no encontrados en Alpha Vantage para {symbol}")
                
            # Convertir a DataFrame
            time_series = data[time_series_key]
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Renombrar columnas
            column_map = {
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close",
                "5. volume": "Volume"
            }
            
            df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
            
            # Convertir a tipos numéricos
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            # Establecer índice de tiempo
            df.index = pd.to_datetime(df.index)
            
            # Añadir columna Adj Close si no existe
            if 'Adj Close' not in df.columns:
                df['Adj Close'] = df['Close']
                
            return df
            
        except Exception as e:
            logger.error(f"Error en Alpha Vantage: {str(e)}")
            return None
    
    def _generate_synthetic_data(self, symbol: str) -> pd.DataFrame:
        """Genera datos sintéticos para fallback de interfaz"""
        try:
            # Crear datos determinísticos pero realistas
            np.random.seed(sum(ord(c) for c in symbol))
            
            # Fechas para 180 días hasta hoy
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Precio base variable según símbolo
            base_price = 100 + sum(ord(c) for c in symbol) % 900
            
            # Generar precios con tendencia y volatilidad realista
            prices = []
            price = base_price
            
            # Volatilidad dependiente del símbolo
            volatility = 0.01 + (sum(ord(c) for c in symbol) % 10) / 100
            trend = 0.0005 * (sum(ord(c) for c in symbol[:3]) % 10 - 5)  # Entre -0.0025 y +0.0025
            
            # Generar serie de precios
            for _ in range(len(dates)):
                noise = np.random.normal(trend, volatility)
                price *= (1 + noise)
                prices.append(price)
            
            # Crear DataFrame OHLCV sintético
            df = pd.DataFrame(index=dates)
            df['Close'] = prices
            df['Open'] = [p * (1 - np.random.uniform(0, volatility)) for p in prices]
            df['High'] = [max(o, c) * (1 + np.random.uniform(0, volatility)) 
                         for o, c in zip(df['Open'], df['Close'])]
            df['Low'] = [min(o, c) * (1 - np.random.uniform(0, volatility))
                        for o, c in zip(df['Open'], df['Close'])]
            df['Volume'] = [int(1e6 * (1 + np.random.normal(0, 0.3))) for _ in prices]
            df['Adj Close'] = df['Close']
            
            # Flag para identificar como sintético
            df.attrs['synthetic'] = True
            logger.info(f"Datos sintéticos generados para {symbol}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error generando datos sintéticos: {str(e)}")
            
            # Crear un DataFrame mínimo para evitar errores
            df = pd.DataFrame(index=pd.date_range(end=datetime.now(), periods=30))
            df['Close'] = np.linspace(100, 110, 30)
            df['Open'] = df['Close'] * 0.99
            df['High'] = df['Close'] * 1.01
            df['Low'] = df['Open'] * 0.99
            df['Volume'] = 1000000
            df['Adj Close'] = df['Close']
            return df

# Clase para análisis técnico corregido
class TechnicalAnalyzer:
    """Analizador técnico con cálculo de indicadores robustos"""
    
    def __init__(self, data_provider: MarketDataProvider):
        self.data_provider = data_provider
    
    def get_market_data(self, symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        """Obtiene datos de mercado a través del proveedor"""
        return self.data_provider.get_market_data(symbol, period, interval)
    
    def analyze_trend(self, symbol: str) -> Tuple[Dict, pd.DataFrame]:
        """Analiza tendencia de un símbolo con manejo de errores"""
        try:
            # Obtener datos
            data = self.get_market_data(symbol)
            
            # Verificar datos mínimos
            if data is None or data.empty or len(data) < 10:
                raise MarketDataError(f"Datos insuficientes para analizar {symbol}")
                
            # Calcular indicadores
            data_with_indicators = self._calculate_indicators(data)
            
            # Determinar tendencia
            trend = self._determine_trend(data_with_indicators)
            
            # Añadir métricas
            trend["metrics"] = {
                "price": float(data["Close"].iloc[-1]),
                "sma20": float(data_with_indicators["SMA20"].iloc[-1]) if "SMA20" in data_with_indicators.columns else 0,
                "sma50": float(data_with_indicators["SMA50"].iloc[-1]) if "SMA50" in data_with_indicators.columns else 0,
                "sma200": float(data_with_indicators["SMA200"].iloc[-1]) if "SMA200" in data_with_indicators.columns else 0,
                "rsi": float(data_with_indicators["RSI"].iloc[-1]) if "RSI" in data_with_indicators.columns else 50,
                "volume": float(data["Volume"].iloc[-1])
            }
            
            return trend, data_with_indicators
            
        except Exception as e:
            logger.error(f"Error en analyze_trend para {symbol}: {str(e)}")
            
            # Crear tendencia vacía para manejo de errores en UI
            empty_trend = {
                "direction": "ERROR",
                "strength": "N/A",
                "bias": "N/A",
                "description": f"Error analizando tendencia de {symbol}. {str(e)}",
                "metrics": {
                    "price": 0,
                    "sma20": 0,
                    "sma50": 0,
                    "sma200": 0,
                    "rsi": 50,
                    "volume": 0
                }
            }
            
            return empty_trend, pd.DataFrame()
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos con manejo seguro de errores"""
        df = data.copy()
        
        try:
            # Medias Móviles Simples - SMA
            for period in [20, 50, 200]:
                if len(df) >= period:
                    df[f"SMA{period}"] = df["Close"].rolling(window=period).mean()
            
            # RSI - Índice de Fuerza Relativa
            if len(df) >= 14:
                delta = df["Close"].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                
                rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)  # Evitar división por cero
                df["RSI"] = 100 - (100 / (1 + rs))
            
            # Bandas de Bollinger - Corregido
            if len(df) >= 20:
                df["BB_Middle"] = df["Close"].rolling(window=20).mean()
                rolling_std = df["Close"].rolling(window=20).std()
                
                # Asignar las bandas individualmente para evitar error de columnas múltiples
                df["BB_Upper"] = df["BB_Middle"] + (rolling_std * 2)
                df["BB_Lower"] = df["BB_Middle"] - (rolling_std * 2)
            
            # MACD - Moving Average Convergence Divergence
            if len(df) >= 26:
                ema12 = df["Close"].ewm(span=12, adjust=False).mean()
                ema26 = df["Close"].ewm(span=26, adjust=False).mean()
                df["MACD"] = ema12 - ema26
                df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
                df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
            
            # ATR - Average True Range
            if len(df) >= 14:
                high_low = df["High"] - df["Low"]
                high_close = (df["High"] - df["Close"].shift()).abs()
                low_close = (df["Low"] - df["Close"].shift()).abs()
                
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                df["ATR"] = tr.rolling(window=14).mean()
            
            # Volumen relativo
            if len(df) >= 20:
                df["Volume_SMA"] = df["Volume"].rolling(window=20).mean()
                df["Volume_Ratio"] = df["Volume"] / df["Volume_SMA"].replace(0, 1)  # Evitar división por cero
            
            # Eliminar valores NaN
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            # Añadir fecha para referencia
            df["Date_Str"] = df.index.strftime('%Y-%m-%d')
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores: {str(e)}")
            
            # En caso de error, retornar el dataframe original para evitar fallos en UI
            return df
    
    def _determine_trend(self, data: pd.DataFrame) -> Dict:
        """Determina tendencia basada en indicadores con manejo seguro"""
        # Asegurar que data no esté vacío
        if data is None or data.empty:
            return {
                "direction": "NEUTRAL",
                "strength": "BAJA",
                "bias": "NEUTRAL",
                "description": "Análisis no disponible. Datos insuficientes."
            }
            
        try:
            # Último precio
            last_close = data["Close"].iloc[-1]
            
            # Extraer valores de indicadores con protección contra KeyError
            sma20 = data["SMA20"].iloc[-1] if "SMA20" in data.columns else last_close
            sma50 = data["SMA50"].iloc[-1] if "SMA50" in data.columns else last_close
            sma200 = data["SMA200"].iloc[-1] if "SMA200" in data.columns else last_close
            
            # Verificación de tendencia con indicadores disponibles
            above_sma20 = last_close > sma20
            above_sma50 = last_close > sma50
            above_sma200 = last_close > sma200
            
            # Determinar dirección de tendencia
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
                
            # RSI para momentum
            rsi = data["RSI"].iloc[-1] if "RSI" in data.columns else 50
            overbought = rsi > 70
            oversold = rsi < 30
            
            # Fuerza de tendencia
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
                
            # Descripción textual
            if direction == "ALCISTA":
                if strength == "ALTA":
                    desc = "Tendencia alcista fuerte con momentum positivo."
                else:
                    desc = "Tendencia alcista moderada con potencial de continuación."
            elif direction == "BAJISTA":
                if strength == "ALTA":
                    desc = "Tendencia bajista fuerte con momentum negativo."
                else:
                    desc = "Tendencia bajista moderada en desarrollo."
            else:
                desc = "Mercado en consolidación sin dirección clara."
                
            # Añadir contexto según sesgo
            if bias == "SOBRECOMPRADO":
                desc += " Indicadores muestran condición de sobrecompra, posible corrección."
            elif bias == "SOBREVENDIDO":
                desc += " Indicadores muestran condición de sobreventa, posible rebote."
                
            if "SMA200" in data.columns:
                pct_from_sma200 = ((last_close / sma200) - 1) * 100
                desc += f" Precio {abs(pct_from_sma200):.1f}% {'por encima' if pct_from_sma200 > 0 else 'por debajo'} de SMA200."
                
            return {
                "direction": direction,
                "strength": strength,
                "bias": bias,
                "description": desc
            }
            
        except Exception as e:
            logger.error(f"Error determinando tendencia: {str(e)}")
            return {
                "direction": "ERROR",
                "strength": "N/A",
                "bias": "N/A",
                "description": f"Error en análisis: {str(e)}"
            }
    
    def identify_strategy(self, data: pd.DataFrame, trend: Dict) -> List[Dict]:
        """Identifica estrategias basadas en el análisis técnico"""
        # Validar datos
        if data is None or data.empty or len(data) < 20:
            return []
            
        try:
            # Asegurar que tenemos indicadores
            if not any(col.startswith('SMA') for col in data.columns):
                data = self._calculate_indicators(data)
                
            # Extraer datos relevantes
            direction = trend["direction"]
            strength = trend["strength"]
            
            strategies = []
            
            # Si los datos son sintéticos, no sugerir estrategias
            if hasattr(data, 'attrs') and data.attrs.get('synthetic', False):
                return []
                
            # Estrategias según tendencia
            if direction == "ALCISTA" and strength != "BAJA":
                last_close = data["Close"].iloc[-1]
                
                # Estrategia de Pullback a SMA20 en tendencia alcista
                if self._check_sma_pullback(data):
                    strategies.append({
                        "type": "CALL",
                        "name": "Pullback a SMA20",
                        "confidence": "ALTA" if strength == "ALTA" else "MEDIA",
                        "description": "Retroceso técnico a la media móvil de 20 períodos en tendencia alcista.",
                        "conditions": [
                            "Precio tocando SMA20 desde arriba",
                            "Tendencia general alcista",
                            "Pullback con menor volumen"
                        ],
                        "levels": {
                            "entry": last_close,
                            "stop": last_close * 0.97,
                            "target": last_close * 1.05
                        }
                    })
            
            elif direction == "BAJISTA" and strength != "BAJA":
                last_close = data["Close"].iloc[-1]
                
                # Estrategia de Rechazo en Resistencia
                if self._check_resistance_rejection(data):
                    strategies.append({
                        "type": "PUT",
                        "name": "Rechazo en Resistencia",
                        "confidence": "ALTA" if strength == "ALTA" else "MEDIA",
                        "description": "Precio rechazado en nivel de resistencia en tendencia bajista.",
                        "conditions": [
                            "Resistencia técnica confirmada",
                            "Vela de rechazo formada",
                            "Tendencia bajista dominante"
                        ],
                        "levels": {
                            "entry": last_close,
                            "stop": last_close * 1.03,
                            "target": last_close * 0.93
                        }
                    })
            
            # Estrategias basadas en momentum (RSI)
            if "RSI" in data.columns:
                rsi = data["RSI"].iloc[-1]
                last_close = data["Close"].iloc[-1]
                
                if rsi < 30 and direction != "BAJISTA":
                    strategies.append({
                        "type": "CALL",
                        "name": "RSI Sobrevendido",
                        "confidence": "MEDIA",
                        "description": "RSI en zona de sobreventa sugiere posible rebote técnico.",
                        "conditions": [
                            f"RSI en {rsi:.1f} (zona de sobreventa)",
                            "Posible reversión técnica",
                            "Entrada contraria"
                        ],
                        "levels": {
                            "entry": last_close,
                            "stop": last_close * 0.97,
                            "target": last_close * 1.05
                        }
                    })
                elif rsi > 70 and direction != "ALCISTA":
                    strategies.append({
                        "type": "PUT",
                        "name": "RSI Sobrecomprado",
                        "confidence": "MEDIA",
                        "description": "RSI en zona de sobrecompra sugiere posible corrección técnica.",
                        "conditions": [
                            f"RSI en {rsi:.1f} (zona de sobrecompra)",
                            "Posible agotamiento alcista",
                            "Entrada contraria"
                        ],
                        "levels": {
                            "entry": last_close,
                            "stop": last_close * 1.03,
                            "target": last_close * 0.95
                        }
                    })
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error identificando estrategias: {str(e)}")
            return []
    
    def _check_sma_pullback(self, data: pd.DataFrame) -> bool:
        """Verifica patrón de pullback a SMA20"""
        try:
            if "SMA20" not in data.columns or len(data) < 20:
                return False
                
            # Últimas barras
            recent = data.iloc[-5:]
            
            # Comprobar si el precio está cerca de la SMA20
            last_close = recent["Close"].iloc[-1]
            sma20 = recent["SMA20"].iloc[-1]
            
            # Cercanía dentro del 1%
            is_near_sma = abs(last_close / sma20 - 1) < 0.01
            
            # Precio por encima de SMA20 en barras anteriores
            was_above = data["Close"].iloc[-6:-2].mean() > data["SMA20"].iloc[-6:-2].mean()
            
            return is_near_sma and was_above
        except Exception:
            return False
    
    def _check_resistance_rejection(self, data: pd.DataFrame) -> bool:
        """Verifica rechazo en nivel de resistencia"""
        try:
            if len(data) < 20:
                return False
                
            # Últimas barras
            recent = data.iloc[-10:].copy()
            
            # Buscar máximos recientes
            high_max = recent["High"].max()
            last_high = recent["High"].iloc[-1]
            
            # Verificar si el precio alcanzó máximo reciente
            reached_high = last_high > high_max * 0.98
            
            # Comprobar patrón de rechazo (bajó desde máximo)
            rejected = reached_high and recent["Close"].iloc[-1] < recent["Open"].iloc[-1]
            
            return rejected
        except Exception:
            return False

# Clase Scanner de Mercado
class MarketScanner:
    """Escáner de mercado con detección de estrategias"""
    
    def __init__(self, symbols: Dict[str, List[str]], analyzer: TechnicalAnalyzer):
        self.symbols = symbols
        self.analyzer = analyzer
        self.cache = {}
        self.last_scan_time = None
    
    def get_cached_analysis(self, symbol: str) -> Optional[Dict]:
        """Obtiene análisis cacheado si existe"""
        if symbol in self.cache:
            return self.cache[symbol]
        return None
    
    def scan_market(self, selected_sectors: Optional[List[str]] = None) -> pd.DataFrame:
        """Ejecuta escaneo de mercado enfocado en sectores seleccionados"""
        try:
            self.last_scan_time = datetime.now()
            results = []
            
            # Filtrar símbolos por sectores
            symbols_to_scan = {}
            if selected_sectors:
                for sector in selected_sectors:
                    if sector in self.symbols:
                        symbols_to_scan[sector] = self.symbols[sector]
            else:
                symbols_to_scan = self.symbols
                
            # Procesar símbolos
            for sector, symbols in symbols_to_scan.items():
                for symbol in symbols:
                    try:
                        # Analizar tendencia
                        trend, data = self.analyzer.analyze_trend(symbol)
                        
                        # Buscar estrategias
                        strategies = self.analyzer.identify_strategy(data, trend)
                        
                        # Guardar en caché
                        self.cache[symbol] = {
                            "trend_data": trend,
                            "strategies": strategies,
                            "timestamp": datetime.now()
                        }
                        
                        # Añadir cada estrategia al resultado
                        for strategy in strategies:
                            # Calcular ratio riesgo/recompensa
                            try:
                                risk = strategy["levels"]["entry"] - strategy["levels"]["stop"]
                                reward = strategy["levels"]["target"] - strategy["levels"]["entry"]
                                rr_ratio = reward / risk if risk > 0 else 0
                            except (KeyError, ZeroDivisionError):
                                rr_ratio = 0
                                
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
                                "R/R": round(rr_ratio, 2),
                                "Timestamp": datetime.now().strftime("%H:%M:%S")
                            })
                    except Exception as e:
                        logger.error(f"Error escaneando {symbol}: {str(e)}")
                        continue
                        
            # Convertir a DataFrame
            if results:
                df = pd.DataFrame(results)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error en scan_market: {str(e)}")
            return pd.DataFrame()

# Funciones de utilidad
def get_market_status() -> Dict:
    """Obtiene el estado actual del mercado con manejo seguro de errores"""
    try:
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(ny_tz)
        
        # Determinar sesión
        hour = now.hour
        weekday = now.weekday()  # 0-6 = Lunes-Domingo
        
        # Verificar fin de semana
        if weekday >= 5:  # Sábado o Domingo
            session = "CERRADO"
        elif 4 <= hour < 9:  # 4:00 AM - 9:00 AM NY
            session = "PRE-MARKET"
        elif 9 <= hour < 16:  # 9:00 AM - 4:00 PM NY
            session = "REGULAR"
        elif 16 <= hour < 20:  # 4:00 PM - 8:00 PM NY
            session = "AFTER-HOURS"
        else:
            session = "CERRADO"
            
        # Calcular próxima actualización - con manejo seguro de NoneType
        next_update = "N/A"
        if hasattr(st.session_state, 'last_scan_time') and st.session_state.last_scan_time is not None:
            next_update = (st.session_state.last_scan_time + timedelta(minutes=5)).strftime("%H:%M:%S")
            
        return {
            "time": now.strftime("%H:%M:%S"),
            "session": session,
            "day": now.strftime("%d/%m/%Y"),
            "next_update": next_update
        }
    except Exception as e:
        logger.error(f"Error en market_status: {str(e)}")
        return {
            "time": datetime.now().strftime("%H:%M:%S"),
            "session": "ERROR",
            "day": datetime.now().strftime("%d/%m/%Y"),
            "next_update": "N/A"
        }

# Inicialización del estado de sesión
def initialize_session_state():
    """Inicializa el estado de la sesión con manejo de errores"""
    try:
        if 'data_cache' not in st.session_state:
            st.session_state.data_cache = DataCache()
            
        if 'data_provider' not in st.session_state:
            st.session_state.data_provider = MarketDataProvider(st.session_state.data_cache)
            
        if 'analyzer' not in st.session_state:
            st.session_state.analyzer = TechnicalAnalyzer(st.session_state.data_provider)
            
        if 'scanner' not in st.session_state:
            st.session_state.scanner = MarketScanner(SYMBOLS, st.session_state.analyzer)
            
        if 'current_symbol' not in st.session_state:
            st.session_state.current_symbol = "SPY"
            
        if 'last_scan_time' not in st.session_state:
            st.session_state.last_scan_time = datetime.now() - timedelta(hours=1)
            
        if 'last_scan_sectors' not in st.session_state:
            st.session_state.last_scan_sectors = ["Índices", "Tecnología"]
            
        if 'scan_results' not in st.session_state:
            st.session_state.scan_results = pd.DataFrame()
    except Exception as e:
        logger.error(f"Error inicializando estado de sesión: {str(e)}")

# Función principal
def main():
    # Configuración de página
    st.set_page_config(
        page_title="InversorIA Mini Pro",
        page_icon="📊",
        layout="wide"
    )
    
    # Inicializar estado
    initialize_session_state()
    
    # Obtener información de mercado para la barra superior
    market_status = get_market_status()
    
    # Interfaz integrada en espacio único
    # Barra superior con métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Hora NY", market_status["time"])
    with col2:
        st.metric("Sesión", market_status["session"])
    with col3:
        st.metric("Caché", f"{len(st.session_state.data_cache.cache)} items")
    with col4:
        cache_stats = st.session_state.data_cache.get_stats()
        hit_rate = "0.0%" if "hit_rate" not in cache_stats else cache_stats["hit_rate"]
        st.metric("Hit Rate", hit_rate)
    
    # Título de la aplicación
    st.title("📊 InversorIA Mini Pro")
    
    # Workspace unificado
    # Selección de sectores y controles
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_sectors = st.multiselect(
            "Sectores a Monitorear",
            list(SYMBOLS.keys()),
            default=st.session_state.last_scan_sectors,
            help="Seleccione sectores para análisis"
        )
    
    with col2:
        filtro = st.selectbox(
            "Filtro de Confianza",
            ["Todas", "Alta", "Media"],
            index=0
        )
    
    with col3:
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
                st.experimental_rerun()
    
    # Tabs para navegar entre análisis
    scanner_tab, analysis_tab = st.tabs(["📡 Scanner de Mercado", "🔬 Análisis Individual"])
    
    # Tab 1: Scanner de mercado
    with scanner_tab:
        # Verificar si hay resultados
        if hasattr(st.session_state, 'scan_results') and not st.session_state.scan_results.empty:
            # Estadísticas de resultados
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                total_calls = len(st.session_state.scan_results[st.session_state.scan_results["Estrategia"] == "CALL"])
                st.metric("Señales CALL", total_calls)
            with stats_col2:
                total_puts = len(st.session_state.scan_results[st.session_state.scan_results["Estrategia"] == "PUT"])
                st.metric("Señales PUT", total_puts)
            with stats_col3:
                st.metric("Total Oportunidades", len(st.session_state.scan_results))
            
            # Aplicar filtro si es necesario
            filtered_results = st.session_state.scan_results
            if filtro != "Todas":
                filtered_results = filtered_results[filtered_results["Confianza"] == filtro.upper()]
            
            # Mostrar tabla con resultados formateados
            if not filtered_results.empty:
                columns = ["Symbol", "Sector", "Estrategia", "Setup", "Confianza", 
                          "Precio", "RSI", "Entry", "Stop", "Target", "R/R"]
                
                st.dataframe(
                    filtered_results[columns].style
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
                    height=400
                )
                
                # Resumen por sector con distribución en columnas
                st.markdown("##### Análisis por Sector")
                sector_columns = st.columns(min(3, len(selected_sectors)))
                
                for i, sector in enumerate(selected_sectors):
                    col = sector_columns[i % len(sector_columns)]
                    with col:
                        sector_data = filtered_results[filtered_results["Sector"] == sector]
                        if not sector_data.empty:
                            with st.expander(f"{sector} ({len(sector_data)} señales)"):
                                calls = len(sector_data[sector_data["Estrategia"] == "CALL"])
                                puts = len(sector_data[sector_data["Estrategia"] == "PUT"])
                                high_conf = len(sector_data[sector_data["Confianza"] == "ALTA"])
                                
                                st.info(f"""
                                **Distribución:**
                                - CALL: {calls} ({calls/len(sector_data)*100:.0f}%)
                                - PUT: {puts} ({puts/len(sector_data)*100:.0f}%)
                                - Alta Confianza: {high_conf} ({high_conf/len(sector_data)*100:.0f}%)
                                """)
                                
                                st.markdown(f"**Símbolos:** {', '.join(sector_data['Symbol'].unique())}")
                        else:
                            st.info(f"No hay señales para {sector}")
            else:
                st.info("No hay resultados con este filtro de confianza.")
        else:
            st.info("""
            ### Sin datos de escaneo reciente
            
            Para obtener señales actualizadas:
            1. Seleccione los sectores que desea monitorear
            2. Pulse el botón "Escanear"
            3. Los resultados aparecerán en esta sección
            """)
    
    # Tab 2: Análisis Individual
    with analysis_tab:
        # Selector de símbolo
        col1, col2 = st.columns(2)
        with col1:
            sector = st.selectbox("Sector", list(SYMBOLS.keys()))
        with col2:
            symbol = st.selectbox("Activo", SYMBOLS[sector])
        
        # Actualizar símbolo actual
        if symbol != st.session_state.current_symbol:
            st.session_state.current_symbol = symbol
        
        # Análisis del símbolo
        try:
            with st.spinner("Analizando..."):
                # Verificar caché
                cached_analysis = st.session_state.scanner.get_cached_analysis(symbol)
                
                if cached_analysis:
                    trend = cached_analysis["trend_data"]
                    strategies = cached_analysis["strategies"]
                else:
                    # Realizar análisis
                    trend, data = st.session_state.analyzer.analyze_trend(symbol)
                    strategies = st.session_state.analyzer.identify_strategy(data, trend)
                
                # Mostrar resultados
                st.markdown(f"#### Análisis Técnico: {symbol}")
                
                # Métricas principales
                col1, col2, col3 = st.columns(3)
                with col1:
                    direction = trend["direction"]
                    direction_arrow = "↑" if direction == "ALCISTA" else "↓" if direction == "BAJISTA" else "→"
                    st.metric("Tendencia", f"{direction} {direction_arrow}")
                with col2:
                    st.metric("Fuerza", trend["strength"])
                with col3:
                    st.metric("Sesgo", trend["bias"])
                
                # Descripción
                st.info(trend["description"])
                
                # Métricas técnicas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    price = trend["metrics"]["price"]
                    st.metric("Precio", f"${price:.2f}")
                with col2:
                    sma200 = trend["metrics"]["sma200"]
                    st.metric("SMA200", f"${sma200:.2f}")
                with col3:
                    rsi = trend["metrics"]["rsi"]
                    st.metric("RSI", f"{rsi:.1f}")
                with col4:
                    try:
                        dist = ((price / sma200) - 1) * 100 if sma200 > 0 else 0
                        st.metric("Dist. SMA200", f"{dist:.1f}%")
                    except ZeroDivisionError:
                        st.metric("Dist. SMA200", "N/A")
                
                # Mostrar estrategias
                if strategies:
                    st.markdown("##### Señales Activas")
                    
                    for strat in strategies:
                        with st.expander(f"{strat['type']} - {strat['name']} (Confianza: {strat['confidence']})"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Descripción:**")
                                st.write(strat['description'])
                                
                                st.markdown("**Condiciones:**")
                                for condition in strat['conditions']:
                                    st.write(f"✓ {condition}")
                            
                            with col2:
                                if 'levels' in strat:
                                    st.markdown("**Niveles Operativos:**")
                                    
                                    entry = strat['levels']['entry']
                                    stop = strat['levels']['stop']
                                    target = strat['levels']['target']
                                    
                                    st.metric("Entrada", f"${entry:.2f}")
                                    st.metric("Stop Loss", f"${stop:.2f}")
                                    st.metric("Objetivo", f"${target:.2f}")
                                    
                                    try:
                                        rr = (target - entry) / (entry - stop)
                                        st.metric("Ratio R/R", f"{rr:.2f}")
                                    except ZeroDivisionError:
                                        st.metric("Ratio R/R", "N/A")
                    
                    # Gestión de riesgo
                    st.markdown("##### Gestión de Riesgo")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        position_size = st.slider(
                            "Tamaño de Posición (%)",
                            min_value=0.5,
                            max_value=5.0,
                            value=2.0,
                            step=0.5
                        )
                    with col2:
                        account_size = st.number_input(
                            "Tamaño de Cuenta ($)",
                            min_value=1000,
                            max_value=1000000,
                            value=10000,
                            step=1000
                        )
                    with col3:
                        risk_amount = account_size * position_size / 100
                        st.metric(
                            "Riesgo Máximo",
                            f"${risk_amount:.2f}",
                            delta=f"{position_size}% del capital"
                        )
                        
                else:
                    st.warning("""
                    **Sin Señales Activas**
                    - No hay setup válido actualmente
                    - Mantener disciplina operativa
                    - Esperar mejor entrada
                    """)
                    
        except Exception as e:
            st.error(f"Error en análisis: {str(e)}")
    
    # Disclaimer
    st.markdown("---")
    st.caption("""
    **⚠️ Disclaimer:** Este sistema proporciona análisis técnico cuantitativo y requiere validación profesional.
    Trading implica riesgo sustancial de pérdida. Realizar due diligence exhaustivo.
    """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error crítico: {str(e)}")
        with st.expander("Detalles técnicos"):
            st.code(traceback.format_exc())