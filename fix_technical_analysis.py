"""
Script para mejorar el manejo de valores NaN en el análisis técnico
"""

import pandas as pd
import numpy as np
import logging
import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def calculate_technical_indicators(df):
    """Calcula indicadores técnicos con manejo mejorado de valores NaN"""
    if df is None or df.empty:
        logger.warning("No hay datos para calcular indicadores técnicos")
        return None
    
    # Hacer una copia para evitar SettingWithCopyWarning
    df = df.copy()
    
    try:
        # Calcular RSI con manejo de NaN
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Usar un valor pequeño para evitar división por cero
        epsilon = 1e-10
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean().clip(lower=epsilon)  # Evitar división por cero
        
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))
        
        # Calcular medias móviles con manejo de NaN
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["SMA_200"] = df["Close"].rolling(window=200).mean()
        
        # Calcular Estocástico
        low_14 = df["Low"].rolling(window=14).min()
        high_14 = df["High"].rolling(window=14).max()
        
        # Evitar división por cero
        denom = high_14 - low_14
        denom = denom.replace(0, epsilon)
        
        df["K"] = 100 * ((df["Close"] - low_14) / denom)
        df["D"] = df["K"].rolling(window=3).mean()
        
        # Calcular CCI (Commodity Channel Index)
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        ma_tp = typical_price.rolling(window=20).mean()
        mean_deviation = abs(typical_price - ma_tp).rolling(window=20).mean()
        
        # Evitar división por cero
        mean_deviation = mean_deviation.replace(0, epsilon)
        
        df["CCI"] = (typical_price - ma_tp) / (0.015 * mean_deviation)
        
        # Calcular MACD
        ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema_12 - ema_26
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
        
        # Calcular ATR (Average True Range)
        df["TR"] = np.maximum(
            np.maximum(
                df["High"] - df["Low"],
                np.abs(df["High"] - df["Close"].shift()),
            ),
            np.abs(df["Low"] - df["Close"].shift()),
        )
        df["ATR"] = df["TR"].rolling(window=14).mean()
        
        # Calcular Bollinger Bands
        df["BB_Middle"] = df["Close"].rolling(window=20).mean()
        df["BB_Std"] = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["BB_Middle"] + (df["BB_Std"] * 2)
        df["BB_Lower"] = df["BB_Middle"] - (df["BB_Std"] * 2)
        
        # Reemplazar NaN con valores predeterminados
        df["RSI"] = df["RSI"].fillna(50)  # Valor neutral
        df["K"] = df["K"].fillna(50)
        df["D"] = df["D"].fillna(50)
        df["CCI"] = df["CCI"].fillna(0)
        df["MACD"] = df["MACD"].fillna(0)
        df["MACD_Signal"] = df["MACD_Signal"].fillna(0)
        df["MACD_Hist"] = df["MACD_Hist"].fillna(0)
        df["ATR"] = df["ATR"].fillna(df["Close"].pct_change().abs().mean() * df["Close"])
        
        # No reemplazar SMA con valores predeterminados para mantener la integridad del análisis
        
        logger.info("Indicadores técnicos calculados correctamente")
        return df
    
    except Exception as e:
        logger.error(f"Error calculando indicadores técnicos: {str(e)}")
        return df

def get_stock_data(symbol, period="1y", interval="1d"):
    """Obtiene datos de acciones con manejo mejorado de errores"""
    try:
        # Intentar obtener datos con yfinance
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if data.empty:
            logger.warning(f"No se encontraron datos para {symbol}")
            return None
        
        # Verificar si hay suficientes datos
        if len(data) < 20:
            logger.warning(f"No hay suficientes datos para {symbol} (solo {len(data)} barras)")
            return data
        
        # Calcular indicadores técnicos
        data = calculate_technical_indicators(data)
        
        return data
    
    except Exception as e:
        logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
        return None

def display_technical_summary(symbol, data):
    """Muestra un resumen técnico con manejo mejorado de valores NaN"""
    if data is None or data.empty:
        st.warning(f"No hay datos técnicos disponibles para {symbol}")
        return
    
    try:
        # Obtener la última fila de datos
        last_row = data.iloc[-1].copy()
        
        # Obtener el precio de cierre y el cambio porcentual
        last_price = last_row["Close"]
        prev_close = data.iloc[-2]["Close"] if len(data) > 1 else last_price
        change_pct = ((last_price / prev_close) - 1) * 100 if prev_close != 0 else 0
        
        # Extraer RSI y MA values con manejo de NaN
        rsi = last_row.get("RSI", None)
        sma20 = last_row.get("SMA_20", None)
        sma50 = last_row.get("SMA_50", None)
        sma200 = last_row.get("SMA_200", None)
        
        # Determinar condiciones de tendencia con manejo de NaN
        above_sma20 = last_price > sma20 if pd.notna(sma20) else None
        above_sma50 = last_price > sma50 if pd.notna(sma50) else None
        above_sma200 = last_price > sma200 if pd.notna(sma200) else None
        
        # Crear columnas para mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        
        # Métricas en columnas con manejo de NaN
        with col1:
            st.metric(
                label=f"{symbol} - Último",
                value=f"${last_price:.2f}" if pd.notna(last_price) else "N/A",
                delta=f"{change_pct:+.2f}%" if pd.notna(change_pct) else "N/A",
            )
        
        with col2:
            if pd.notna(rsi):
                rsi_color = "normal" if 40 <= rsi <= 60 else ("off" if rsi < 40 else "inverse")
                st.metric(
                    label="RSI",
                    value=f"{rsi:.1f}" if pd.notna(rsi) else "N/A",
                    delta="Neutral" if 40 <= rsi <= 60 else ("Sobrevendido" if rsi < 40 else "Sobrecomprado"),
                    delta_color=rsi_color,
                )
            else:
                st.metric(label="RSI", value="N/A")
        
        with col3:
            if above_sma50 is not None:
                trend = "Alcista" if above_sma50 else "Bajista"
                st.metric(
                    label="Tendencia",
                    value=trend,
                    delta=f"MA50: ${sma50:.2f}" if pd.notna(sma50) else "N/A",
                    delta_color="normal" if above_sma50 else "inverse",
                )
            else:
                st.metric(label="Tendencia", value="N/A")
        
        with col4:
            if above_sma200 is not None:
                trend = "Alcista LP" if above_sma200 else "Bajista LP"
                st.metric(
                    label="Tendencia LP",
                    value=trend,
                    delta=f"MA200: ${sma200:.2f}" if pd.notna(sma200) else "N/A",
                    delta_color="normal" if above_sma200 else "inverse",
                )
            else:
                st.metric(label="Tendencia LP", value="N/A", delta="Datos insuficientes")
        
        # Mostrar detalles adicionales
        st.markdown("### Detalles de Indicadores")
        
        # Crear columnas para detalles
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Osciladores")
            
            # Manejar valores nulos para RSI
            if "RSI" in data.columns and pd.notna(last_row["RSI"]):
                st.metric("RSI (14)", f"{last_row['RSI']:.2f}")
            else:
                st.metric("RSI (14)", "N/A")
            
            # Manejar valores nulos para Estocástico
            if "K" in data.columns and "D" in data.columns and pd.notna(last_row["K"]) and pd.notna(last_row["D"]):
                st.metric("Estocástico", f"K: {last_row['K']:.2f}, D: {last_row['D']:.2f}")
            else:
                st.metric("Estocástico", "N/A")
            
            # Manejar valores nulos para CCI
            if "CCI" in data.columns and pd.notna(last_row["CCI"]):
                st.metric("CCI", f"{last_row['CCI']:.2f}")
            else:
                st.metric("CCI", "N/A")
        
        with col2:
            st.markdown("#### Tendencia")
            
            # Verificar valores nulos para SMA
            if (
                "SMA_20" in data.columns
                and "SMA_50" in data.columns
                and pd.notna(last_row["SMA_20"])
                and pd.notna(last_row["SMA_50"])
            ):
                sma_20 = last_row["SMA_20"]
                sma_50 = last_row["SMA_50"]
                sma_diff = ((sma_20 / sma_50) - 1) * 100
                st.metric(
                    "SMA 20/50",
                    f"{sma_diff:+.2f}%",
                    "Alcista" if sma_diff > 0 else "Bajista",
                )
            else:
                st.metric("SMA 20/50", "N/A")
            
            # Verificar valores nulos para MACD
            if (
                "MACD" in data.columns
                and "MACD_Signal" in data.columns
                and pd.notna(last_row["MACD"])
                and pd.notna(last_row["MACD_Signal"])
            ):
                macd = last_row["MACD"]
                macd_signal = last_row["MACD_Signal"]
                macd_diff = macd - macd_signal
                st.metric(
                    "MACD",
                    f"{macd:.4f}",
                    f"Señal: {macd_signal:.4f} ({macd_diff:+.4f})",
                )
            else:
                st.metric("MACD", "N/A")
            
            # Verificar valores nulos para SMA_200
            if (
                "SMA_200" in data.columns
                and "Close" in data.columns
                and pd.notna(last_row["SMA_200"])
                and pd.notna(last_row["Close"])
            ):
                price = last_row["Close"]
                sma_200 = last_row["SMA_200"]
                price_vs_sma = ((price / sma_200) - 1) * 100
                st.metric(
                    "Precio vs SMA200",
                    f"{price_vs_sma:+.2f}%",
                    "Por encima" if price_vs_sma > 0 else "Por debajo",
                )
            else:
                st.metric("Precio vs SMA200", "N/A", "Datos insuficientes")
        
        with col3:
            st.markdown("#### Volatilidad")
            
            # Verificar valores nulos para ATR
            if "ATR" in data.columns and pd.notna(last_row["ATR"]):
                atr = last_row["ATR"]
                atr_pct = (atr / last_row["Close"]) * 100
                st.metric("ATR", f"${atr:.2f}", f"{atr_pct:.2f}% del precio")
            else:
                st.metric("ATR", "N/A")
            
            # Verificar valores nulos para Bollinger Bands
            if (
                "BB_Upper" in data.columns
                and "BB_Lower" in data.columns
                and "Close" in data.columns
                and pd.notna(last_row["BB_Upper"])
                and pd.notna(last_row["BB_Lower"])
                and pd.notna(last_row["Close"])
            ):
                bb_width = (last_row["BB_Upper"] - last_row["BB_Lower"]) / last_row["Close"] * 100
                price_in_bb = (last_row["Close"] - last_row["BB_Lower"]) / (
                    last_row["BB_Upper"] - last_row["BB_Lower"]
                ) * 100
                st.metric(
                    "Bandas Bollinger",
                    f"Ancho: {bb_width:.2f}%",
                    f"Posición: {price_in_bb:.2f}%",
                )
            else:
                st.metric("Bandas Bollinger", "N/A")
            
            # Mostrar volumen
            if "Volume" in data.columns and pd.notna(last_row["Volume"]):
                avg_vol = data["Volume"].rolling(window=20).mean().iloc[-1]
                vol_ratio = last_row["Volume"] / avg_vol if avg_vol > 0 else 0
                vol_formatted = f"{last_row['Volume']:,.0f}"
                st.metric(
                    "Volumen",
                    vol_formatted,
                    f"{vol_ratio:.2f}x promedio" if vol_ratio > 0 else "N/A",
                )
            else:
                st.metric("Volumen", "N/A")
    
    except Exception as e:
        logger.error(f"Error mostrando resumen técnico: {str(e)}")
        st.error(f"Error mostrando resumen técnico: {str(e)}")

def main():
    """Función principal"""
    st.set_page_config(page_title="Fix Technical Analysis", layout="wide")
    
    st.title("Fix Technical Analysis")
    
    # Seleccionar símbolo
    symbol = st.text_input("Símbolo", value="AAPL")
    
    if st.button("Analizar"):
        with st.spinner(f"Analizando {symbol}..."):
            # Obtener datos
            data = get_stock_data(symbol)
            
            if data is not None and not data.empty:
                # Mostrar resumen técnico
                display_technical_summary(symbol, data)
                
                # Mostrar datos
                st.subheader("Datos")
                st.dataframe(data.tail(.astype(str)))
            else:
                st.error(f"No se pudieron obtener datos para {symbol}")

if __name__ == "__main__":
    main()
