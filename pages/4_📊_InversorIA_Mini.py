import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Verificación de autenticación
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.title("🔒 Acceso Restringido")
    st.warning("Por favor, inicie sesión desde la página principal del sistema.")
    st.stop()

class TradingAnalyzer:
    def __init__(self):
        self.timeframes = {
            "Largo Plazo": "1y",
            "Medio Plazo": "6mo",
            "Corto Plazo": "1mo",
            "Intradía": "1d"
        }
        
    def get_trend_data(self, symbol, timeframe="1y"):
        """Obtiene datos y determina tendencia principal"""
        try:
            data = yf.download(symbol, period=timeframe, interval="1d")
            if data.empty:
                return None, "Sin datos disponibles"
                
            # Calcular SMAs
            data['SMA20'] = SMAIndicator(data['Close'], window=20).sma_indicator()
            data['SMA50'] = SMAIndicator(data['Close'], window=50).sma_indicator()
            data['SMA200'] = SMAIndicator(data['Close'], window=200).sma_indicator()
            
            # Determinar tendencia principal
            current_price = data['Close'].iloc[-1]
            sma200 = data['SMA200'].iloc[-1]
            sma50 = data['SMA50'].iloc[-1]
            
            if current_price > sma200 and sma50 > sma200:
                trend = "ALCISTA 📈"
            elif current_price < sma200 and sma50 < sma200:
                trend = "BAJISTA 📉"
            else:
                trend = "LATERAL ↔️"
                
            return data, trend
            
        except Exception as e:
            st.error(f"Error obteniendo datos: {str(e)}")
            return None, "Error"

    def analyze_signals(self, data):
        """Analiza señales técnicas para CALL/PUT"""
        try:
            # Calcular indicadores
            macd = MACD(data['Close'])
            data['MACD'] = macd.macd()
            data['MACD_Signal'] = macd.macd_signal()
            data['RSI'] = RSIIndicator(data['Close']).rsi()
            bb = BollingerBands(data['Close'])
            data['BB_High'] = bb.bollinger_hband()
            data['BB_Low'] = bb.bollinger_lband()
            
            # Últimos valores
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_macd = data['MACD'].iloc[-1]
            current_macd_signal = data['MACD_Signal'].iloc[-1]
            bb_high = data['BB_High'].iloc[-1]
            bb_low = data['BB_Low'].iloc[-1]
            
            # Señales para CALL
            call_signals = []
            if current_rsi < 30:
                call_signals.append("RSI en sobreventa")
            if current_price < bb_low:
                call_signals.append("Precio bajo Banda Inferior")
            if current_macd > current_macd_signal:
                call_signals.append("Cruce MACD alcista")
                
            # Señales para PUT
            put_signals = []
            if current_rsi > 70:
                put_signals.append("RSI en sobrecompra")
            if current_price > bb_high:
                put_signals.append("Precio sobre Banda Superior")
            if current_macd < current_macd_signal:
                put_signals.append("Cruce MACD bajista")
                
            # Evaluar señal dominante
            signal_strength = {
                "CALL": len(call_signals),
                "PUT": len(put_signals)
            }
            
            return {
                "signals": {
                    "CALL": call_signals,
                    "PUT": put_signals
                },
                "recommendation": max(signal_strength.items(), key=lambda x: x[1])[0] if max(signal_strength.values()) > 0 else "NEUTRAL",
                "metrics": {
                    "price": current_price,
                    "rsi": current_rsi,
                    "macd": current_macd,
                    "bb_high": bb_high,
                    "bb_low": bb_low
                }
            }
            
        except Exception as e:
            st.error(f"Error en análisis: {str(e)}")
            return None

    def plot_analysis(self, data, signals):
        """Genera gráfico interactivo con señales"""
        try:
            fig = go.Figure()
            
            # Precio y SMAs
            fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['Close'],
                name='Precio',
                line=dict(color='blue', width=1)
            ))
            
            fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['SMA20'],
                name='SMA20',
                line=dict(color='orange', width=1, dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['SMA50'],
                name='SMA50',
                line=dict(color='green', width=1, dash='dash')
            ))
            
            # Bandas de Bollinger
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['BB_High'],
                name='BB Superior',
                line=dict(color='gray', width=1, dash='dot')
            ))
            
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['BB_Low'],
                name='BB Inferior',
                line=dict(color='gray', width=1, dash='dot')
            ))
            
            # Configuración
            fig.update_layout(
                title='Análisis Técnico',
                yaxis_title='Precio',
                template='plotly_white',
                showlegend=True,
                height=600
            )
            
            return fig
            
        except Exception as e:
            st.error(f"Error en visualización: {str(e)}")
            return None

def main():
    st.title("📊 InversorIA Mini")
    
    analyzer = TradingAnalyzer()
    
    # Selector de categoría y símbolo
    categories = {
        "Índices": ["SPY", "QQQ", "DIA", "IWM", "EFA", "VWO", "IYR", "XLE", "XLF", "XLV"],
        "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "PYPL", "CRM"],
        "Finanzas": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK"]
    }
    
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Categoría", list(categories.keys()))
    with col2:
        symbol = st.selectbox("Símbolo", categories[category])
    
    # Análisis por timeframes
    col1, col2, col3 = st.columns(3)
    with col1:
        data_lp, trend_lp = analyzer.get_trend_data(symbol, "1y")
        st.metric("Tendencia Largo Plazo", trend_lp)
        
    with col2:
        data_mp, trend_mp = analyzer.get_trend_data(symbol, "6mo")
        st.metric("Tendencia Medio Plazo", trend_mp)
        
    with col3:
        data_cp, trend_cp = analyzer.get_trend_data(symbol, "1mo")
        st.metric("Tendencia Corto Plazo", trend_cp)
    
    # Análisis detallado del timeframe actual
    if data_cp is not None:
        signals = analyzer.analyze_signals(data_cp)
        
        if signals:
            st.subheader("Señales Activas")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Señales CALL:**")
                for signal in signals['signals']['CALL']:
                    st.write(f"✅ {signal}")
                    
            with col2:
                st.write("**Señales PUT:**")
                for signal in signals['signals']['PUT']:
                    st.write(f"🔴 {signal}")
            
            # Recomendación
            st.subheader("Recomendación")
            if signals['recommendation'] == "CALL":
                st.success("🟢 CALL - Oportunidad de Compra")
            elif signals['recommendation'] == "PUT":
                st.error("🔴 PUT - Oportunidad de Venta")
            else:
                st.warning("⚪ NEUTRAL - Esperar Confirmación")
            
            # Métricas
            st.subheader("Métricas Técnicas")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RSI", f"{signals['metrics']['rsi']:.2f}")
            with col2:
                st.metric("MACD", f"{signals['metrics']['macd']:.2f}")
            with col3:
                st.metric("Precio", f"${signals['metrics']['price']:.2f}")
            
            # Gráfico
            st.plotly_chart(analyzer.plot_analysis(data_cp, signals), use_container_width=True)
            
            # Disclaimer
            st.caption("""
            **Disclaimer:** Este análisis es generado automáticamente y debe ser validado con análisis adicional. 
            Las señales técnicas no garantizan resultados futuros. Trading implica riesgo de pérdida.
            """)

if __name__ == "__main__":
    main()