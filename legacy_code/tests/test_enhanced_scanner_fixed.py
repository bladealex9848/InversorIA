"""
Test para el Enhanced Market Scanner (versión corregida)
-----------------------------------
Este script permite probar la implementación mejorada del scanner de mercado
sin necesidad de modificar el archivo principal.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Configuración de la página
st.set_page_config(
    page_title="Test Scanner Mejorado",
    page_icon="📊",
    layout="wide",
)

# Importar el módulo de scanner mejorado
from enhanced_market_scanner_fixed import render_enhanced_market_scanner

# Intentar importar las dependencias necesarias
try:
    from market_utils import get_market_context
    from trading_analyzer import TradingAnalyzer
    from market_scanner import MarketScanner
except ImportError as e:
    st.error(f"Error importando dependencias: {str(e)}")
    st.info(
        "Asegúrate de que los archivos market_utils.py, trading_analyzer.py y market_scanner.py están disponibles."
    )
    st.stop()

# Título de la aplicación
st.title("🔍 Test del Scanner de Mercado Mejorado")

# Información de símbolos y sectores (versión simplificada para pruebas)
SYMBOLS = {
    "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META"],
    "Finanzas": ["JPM", "BAC", "GS", "MS", "V", "MA"],
    "Energía": ["XOM", "CVX", "COP", "EOG", "PXD"],
    "Salud": ["JNJ", "PFE", "MRK", "ABBV", "LLY"],
    "ETF": ["SPY", "QQQ", "DIA", "IWM", "XLE", "XLF", "XLV"],
}

# Inicializar componentes si no existen en session_state
if "analyzer" not in st.session_state:
    st.session_state.analyzer = TradingAnalyzer()

if "scanner" not in st.session_state:
    st.session_state.scanner = MarketScanner(SYMBOLS, st.session_state.analyzer)

if "last_scan_sectors" not in st.session_state:
    st.session_state.last_scan_sectors = ["Tecnología", "Finanzas"]

# Renderizar el scanner mejorado
render_enhanced_market_scanner(
    st.session_state.scanner,
    st.session_state.analyzer,
    get_market_context,
    SYMBOLS,  # Pasar SYMBOLS directamente
)
