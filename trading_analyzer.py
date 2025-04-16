import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
import random  # Para simulación

logger = logging.getLogger(__name__)

class TradingAnalyzer:
    """Analizador de trading que proporciona análisis técnico y detección de estrategias"""
    
    def __init__(self):
        """Inicializa el analizador de trading"""
        self.data_cache = {}
        
    def get_market_data(self, symbol, period="1mo", interval="1d"):
        """
        Obtiene datos de mercado para un símbolo
        
        Args:
            symbol (str): Símbolo a analizar
            period (str): Período de tiempo (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval (str): Intervalo de tiempo (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            pd.DataFrame: DataFrame con datos de mercado
        """
        try:
            # Clave de caché
            cache_key = f"{symbol}_{period}_{interval}"
            
            # Verificar caché
            if cache_key in self.data_cache:
                return self.data_cache[cache_key]
            
            # Obtener datos
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            
            if data.empty:
                logger.warning(f"No se pudieron obtener datos para {symbol}")
                return None
                
            # Calcular indicadores técnicos
            data = self._calculate_indicators(data)
            
            # Guardar en caché
            self.data_cache[cache_key] = data
            
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            return None
            
    def _calculate_indicators(self, data):
        """
        Calcula indicadores técnicos para un DataFrame
        
        Args:
            data (pd.DataFrame): DataFrame con datos OHLCV
            
        Returns:
            pd.DataFrame: DataFrame con indicadores calculados
        """
        if data.empty:
            return data
            
        # Copiar datos para evitar SettingWithCopyWarning
        df = data.copy()
        
        # Medias móviles
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        df['BB_Std'] = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + 2 * df['BB_Std']
        df['BB_Lower'] = df['BB_Middle'] - 2 * df['BB_Std']
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        return df
        
    def analyze_trend(self, symbol):
        """
        Analiza la tendencia de un símbolo
        
        Args:
            symbol (str): Símbolo a analizar
            
        Returns:
            tuple: (dict con análisis de tendencia, DataFrame con datos)
        """
        # Obtener datos
        data = self.get_market_data(symbol)
        
        if data is None or data.empty:
            return None, None
            
        # Obtener última fila
        last_row = data.iloc[-1]
        
        # Determinar tendencia
        sma20 = last_row.get('SMA_20', None)
        sma50 = last_row.get('SMA_50', None)
        sma200 = last_row.get('SMA_200', None)
        
        price = last_row['Close']
        rsi = last_row.get('RSI', 50)
        macd = last_row.get('MACD', 0)
        macd_signal = last_row.get('MACD_Signal', 0)
        
        # Determinar dirección de tendencia
        trend_direction = "NEUTRAL"
        trend_strength = "MEDIA"
        
        # Análisis de tendencia basado en medias móviles
        if sma20 is not None and sma50 is not None:
            if price > sma20 and price > sma50 and sma20 > sma50:
                trend_direction = "ALCISTA"
                if sma200 is not None and price > sma200:
                    trend_strength = "ALTA"
            elif price < sma20 and price < sma50 and sma20 < sma50:
                trend_direction = "BAJISTA"
                if sma200 is not None and price < sma200:
                    trend_strength = "ALTA"
        
        # Refinar con RSI
        if rsi > 70:
            if trend_direction == "ALCISTA":
                trend_strength = "ALTA" if trend_strength != "ALTA" else trend_strength
            else:
                trend_direction = "ALCISTA"
                trend_strength = "MEDIA"
        elif rsi < 30:
            if trend_direction == "BAJISTA":
                trend_strength = "ALTA" if trend_strength != "ALTA" else trend_strength
            else:
                trend_direction = "BAJISTA"
                trend_strength = "MEDIA"
                
        # Refinar con MACD
        if macd > macd_signal and macd > 0:
            if trend_direction == "ALCISTA":
                trend_strength = "ALTA" if trend_strength != "ALTA" else trend_strength
        elif macd < macd_signal and macd < 0:
            if trend_direction == "BAJISTA":
                trend_strength = "ALTA" if trend_strength != "ALTA" else trend_strength
                
        # Calcular niveles de soporte y resistencia
        supports, resistances = self._find_support_resistance(data)
        
        # Crear resultado
        result = {
            "direction": trend_direction,
            "strength": trend_strength,
            "metrics": {
                "price": price,
                "rsi": rsi,
                "macd": macd,
                "sma20": sma20,
                "sma50": sma50,
                "sma200": sma200
            },
            "levels": {
                "supports": supports,
                "resistances": resistances
            }
        }
        
        return result, data
        
    def _find_support_resistance(self, data, window=10):
        """
        Encuentra niveles de soporte y resistencia
        
        Args:
            data (pd.DataFrame): DataFrame con datos OHLCV
            window (int): Ventana para buscar máximos y mínimos locales
            
        Returns:
            tuple: (soportes, resistencias)
        """
        if data is None or len(data) < window * 2:
            return [], []
            
        # Obtener precios
        df = data.copy()
        
        # Encontrar máximos y mínimos locales
        df['min'] = df['Low'].rolling(window=window, center=True).min()
        df['max'] = df['High'].rolling(window=window, center=True).max()
        
        # Identificar soportes (mínimos locales)
        supports = []
        for i in range(window, len(df) - window):
            if df['Low'].iloc[i] == df['min'].iloc[i] and df['Low'].iloc[i] not in supports:
                supports.append(df['Low'].iloc[i])
                
        # Identificar resistencias (máximos locales)
        resistances = []
        for i in range(window, len(df) - window):
            if df['High'].iloc[i] == df['max'].iloc[i] and df['High'].iloc[i] not in resistances:
                resistances.append(df['High'].iloc[i])
                
        # Filtrar niveles cercanos (dentro del 2%)
        filtered_supports = []
        for s in sorted(supports):
            if not filtered_supports or min(abs(s - fs) / s for fs in filtered_supports) > 0.02:
                filtered_supports.append(s)
                
        filtered_resistances = []
        for r in sorted(resistances):
            if not filtered_resistances or min(abs(r - fr) / r for fr in filtered_resistances) > 0.02:
                filtered_resistances.append(r)
                
        # Limitar a los 3 niveles más cercanos al precio actual
        current_price = data['Close'].iloc[-1]
        
        filtered_supports = sorted(filtered_supports, key=lambda x: abs(current_price - x))[:3]
        filtered_resistances = sorted(filtered_resistances, key=lambda x: abs(current_price - x))[:3]
        
        return filtered_supports, filtered_resistances
        
    def identify_strategy(self, data, trend):
        """
        Identifica estrategias de trading basadas en el análisis técnico
        
        Args:
            data (pd.DataFrame): DataFrame con datos e indicadores
            trend (dict): Análisis de tendencia
            
        Returns:
            list: Lista de estrategias identificadas
        """
        if data is None or data.empty or trend is None:
            return []
            
        strategies = []
        
        # Obtener datos relevantes
        price = trend["metrics"]["price"]
        direction = trend["direction"]
        strength = trend["strength"]
        supports = trend["levels"]["supports"]
        resistances = trend["levels"]["resistances"]
        
        # Determinar niveles de entrada, stop y target
        entry = price
        stop = None
        target = None
        r_r = 0
        
        if direction == "ALCISTA":
            # Para tendencia alcista
            if supports:
                stop = max(supports[0], price * 0.97)  # Soporte más cercano o 3% por debajo
            else:
                stop = price * 0.97  # 3% por debajo
                
            if resistances:
                target = min(resistances[0], price * 1.05)  # Resistencia más cercana o 5% por encima
            else:
                target = price * 1.05  # 5% por encima
                
            # Estrategias alcistas
            if strength == "ALTA":
                strategies.append({
                    "name": "Momentum Alcista",
                    "type": "CALL",
                    "confidence": "ALTA",
                    "description": "Tendencia alcista fuerte con momentum positivo",
                    "levels": {
                        "entry": entry,
                        "stop": stop,
                        "target": target,
                        "r_r": round((target - entry) / (entry - stop), 2) if stop < entry else 0
                    }
                })
            else:
                strategies.append({
                    "name": "Pullback Alcista",
                    "type": "CALL",
                    "confidence": "MEDIA",
                    "description": "Compra en retroceso dentro de tendencia alcista",
                    "levels": {
                        "entry": entry,
                        "stop": stop,
                        "target": target,
                        "r_r": round((target - entry) / (entry - stop), 2) if stop < entry else 0
                    }
                })
                
        elif direction == "BAJISTA":
            # Para tendencia bajista
            if resistances:
                stop = min(resistances[0], price * 1.03)  # Resistencia más cercana o 3% por encima
            else:
                stop = price * 1.03  # 3% por encima
                
            if supports:
                target = max(supports[0], price * 0.95)  # Soporte más cercano o 5% por debajo
            else:
                target = price * 0.95  # 5% por debajo
                
            # Estrategias bajistas
            if strength == "ALTA":
                strategies.append({
                    "name": "Momentum Bajista",
                    "type": "PUT",
                    "confidence": "ALTA",
                    "description": "Tendencia bajista fuerte con momentum negativo",
                    "levels": {
                        "entry": entry,
                        "stop": stop,
                        "target": target,
                        "r_r": round((entry - target) / (stop - entry), 2) if stop > entry else 0
                    }
                })
            else:
                strategies.append({
                    "name": "Pullback Bajista",
                    "type": "PUT",
                    "confidence": "MEDIA",
                    "description": "Venta en rebote dentro de tendencia bajista",
                    "levels": {
                        "entry": entry,
                        "stop": stop,
                        "target": target,
                        "r_r": round((entry - target) / (stop - entry), 2) if stop > entry else 0
                    }
                })
        else:
            # Para tendencia neutral, no generamos estrategias
            pass
            
        return strategies
