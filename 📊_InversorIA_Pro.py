"""
InversorIA Pro - Terminal Institucional de Trading
--------------------------------------------------
Plataforma profesional que integra análisis técnico avanzado, estrategias de
opciones, análisis multiframe, scanner de mercado y asistencia IA para traders institucionales.

Características:
- Autenticación y permisos para usuarios institucionales
- Dashboard interactivo con múltiples módulos de análisis
- Detección avanzada de patrones técnicos y niveles clave
- Análisis de opciones con estrategias personalizadas
- Asistente IA con contexto de mercado en tiempo real
- Análisis de sentimiento, noticias y datos fundamentales
- Scanner de mercado con detección de oportunidades
"""

import os
import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pytz
import json
import importlib
import sys
import requests
import openai
import traceback
import logging
import base64
import re
from typing import Dict, List, Tuple, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Importar componentes personalizados
try:
    from market_utils import (
        fetch_market_data,
        TechnicalAnalyzer,
        OptionsParameterManager,
        get_market_context,
        get_vix_level,
        clear_cache,
        _data_cache,
    )
except Exception as e:
    st.error(f"Error importando market_utils: {str(e)}")

try:
    from trading_dashboard import (
        render_dashboard,
        render_technical_tab,
        render_options_tab,
        render_multiframe_tab,
        render_fundamental_tab,
        render_report_tab,
        render_risk_tab,
        TIMEFRAMES,
    )
except Exception as e:
    st.error(f"Error importando trading_dashboard: {str(e)}")

try:
    from authenticator import check_password, validate_session, clear_session
except Exception as e:
    st.error(f"Error importando authenticator: {str(e)}")

try:
    from openai_utils import process_tool_calls, tools
except Exception as e:
    st.error(f"Error importando openai_utils: {str(e)}")

try:
    from technical_analysis import (
        detect_support_resistance,
        detect_trend_lines,
        detect_channels,
        detect_candle_patterns,
    )
except Exception as e:
    st.error(f"Error importando technical_analysis: {str(e)}")

# Configuración de la página
st.set_page_config(
    page_title="InversorIA Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Clase para manejar la codificación JSON
class NumpyEncoder(json.JSONEncoder):
    """Encoder personalizado para manejar diversos tipos de datos NumPy y Pandas"""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif pd.isna(obj):
            return None
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super(NumpyEncoder, self).default(obj)


# Información de símbolos y nombres completos
COMPANY_INFO = {
    # Tecnología
    "AAPL": {
        "name": "Apple Inc.",
        "sector": "Tecnología",
        "description": "Fabricante de dispositivos electrónicos y software",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "sector": "Tecnología",
        "description": "Empresa de software y servicios en la nube",
    },
    "GOOGL": {
        "name": "Alphabet Inc. (Google)",
        "sector": "Tecnología",
        "description": "Conglomerado especializado en productos y servicios de Internet",
    },
    "AMZN": {
        "name": "Amazon.com Inc.",
        "sector": "Consumo Discrecional",
        "description": "Comercio electrónico y servicios en la nube",
    },
    "TSLA": {
        "name": "Tesla Inc.",
        "sector": "Automóviles",
        "description": "Fabricante de vehículos eléctricos y tecnología de energía limpia",
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "sector": "Tecnología",
        "description": "Fabricante de unidades de procesamiento gráfico",
    },
    "META": {
        "name": "Meta Platforms Inc.",
        "sector": "Tecnología",
        "description": "Empresa de redes sociales y tecnología",
    },
    "NFLX": {
        "name": "Netflix Inc.",
        "sector": "Comunicación",
        "description": "Servicio de streaming y producción de contenido",
    },
    "PYPL": {
        "name": "PayPal Holdings Inc.",
        "sector": "Servicios Financieros",
        "description": "Plataforma de pagos en línea",
    },
    "CRM": {
        "name": "Salesforce Inc.",
        "sector": "Tecnología",
        "description": "Software de gestión de relaciones con clientes",
    },
    # Finanzas
    "JPM": {
        "name": "JPMorgan Chase & Co.",
        "sector": "Finanzas",
        "description": "Banco multinacional y servicios financieros",
    },
    "BAC": {
        "name": "Bank of America Corp.",
        "sector": "Finanzas",
        "description": "Institución bancaria multinacional",
    },
    "WFC": {
        "name": "Wells Fargo & Co.",
        "sector": "Finanzas",
        "description": "Servicios bancarios y financieros",
    },
    "C": {
        "name": "Citigroup Inc.",
        "sector": "Finanzas",
        "description": "Banca de inversión y servicios financieros",
    },
    "GS": {
        "name": "Goldman Sachs Group Inc.",
        "sector": "Finanzas",
        "description": "Banca de inversión y gestión de activos",
    },
    "MS": {
        "name": "Morgan Stanley",
        "sector": "Finanzas",
        "description": "Servicios financieros y banca de inversión",
    },
    "V": {
        "name": "Visa Inc.",
        "sector": "Finanzas",
        "description": "Servicios de pagos electrónicos",
    },
    "MA": {
        "name": "Mastercard Inc.",
        "sector": "Finanzas",
        "description": "Tecnología de pagos globales",
    },
    "AXP": {
        "name": "American Express Co.",
        "sector": "Finanzas",
        "description": "Servicios financieros y tarjetas de crédito",
    },
    "BLK": {
        "name": "BlackRock Inc.",
        "sector": "Finanzas",
        "description": "Gestión de inversiones y servicios financieros",
    },
    # ETFs e Índices
    "SPY": {
        "name": "SPDR S&P 500 ETF Trust",
        "sector": "ETF",
        "description": "ETF que sigue el índice S&P 500",
    },
    "QQQ": {
        "name": "Invesco QQQ Trust",
        "sector": "ETF",
        "description": "ETF que sigue el índice Nasdaq-100",
    },
    "DIA": {
        "name": "SPDR Dow Jones Industrial Average ETF",
        "sector": "ETF",
        "description": "ETF que sigue el índice Dow Jones Industrial Average",
    },
    "IWM": {
        "name": "iShares Russell 2000 ETF",
        "sector": "ETF",
        "description": "ETF que sigue el índice Russell 2000 de small caps",
    },
    "EFA": {
        "name": "iShares MSCI EAFE ETF",
        "sector": "ETF",
        "description": "ETF que sigue acciones internacionales desarrolladas",
    },
    "VWO": {
        "name": "Vanguard FTSE Emerging Markets ETF",
        "sector": "ETF",
        "description": "ETF que sigue mercados emergentes",
    },
    "XLE": {
        "name": "Energy Select Sector SPDR Fund",
        "sector": "ETF",
        "description": "ETF del sector energético",
    },
    "XLF": {
        "name": "Financial Select Sector SPDR Fund",
        "sector": "ETF",
        "description": "ETF del sector financiero",
    },
    "XLV": {
        "name": "Health Care Select Sector SPDR Fund",
        "sector": "ETF",
        "description": "ETF del sector sanitario",
    },
    # Energía
    "XOM": {
        "name": "Exxon Mobil Corp.",
        "sector": "Energía",
        "description": "Compañía integrada de petróleo y gas",
    },
    "CVX": {
        "name": "Chevron Corporation",
        "sector": "Energía",
        "description": "Producción y refinación de petróleo",
    },
    "SHEL": {
        "name": "Shell PLC",
        "sector": "Energía",
        "description": "Multinacional energética integrada",
    },
    "TTE": {
        "name": "TotalEnergies SE",
        "sector": "Energía",
        "description": "Compañía energética multinacional",
    },
    "COP": {
        "name": "ConocoPhillips",
        "sector": "Energía",
        "description": "Exploración y producción de petróleo y gas",
    },
    "EOG": {
        "name": "EOG Resources Inc.",
        "sector": "Energía",
        "description": "Exploración y producción de petróleo",
    },
    "PXD": {
        "name": "Pioneer Natural Resources Co.",
        "sector": "Energía",
        "description": "Compañía de exploración y producción de petróleo",
    },
    "DVN": {
        "name": "Devon Energy Corp.",
        "sector": "Energía",
        "description": "Compañía independiente de petróleo y gas",
    },
    "MPC": {
        "name": "Marathon Petroleum Corp.",
        "sector": "Energía",
        "description": "Refinación y comercialización de petróleo",
    },
    "PSX": {
        "name": "Phillips 66",
        "sector": "Energía",
        "description": "Refinación de petróleo y productos químicos",
    },
    # Salud
    "JNJ": {
        "name": "Johnson & Johnson",
        "sector": "Salud",
        "description": "Productos farmacéuticos y dispositivos médicos",
    },
    "UNH": {
        "name": "UnitedHealth Group Inc.",
        "sector": "Salud",
        "description": "Seguros médicos y servicios de salud",
    },
    "PFE": {
        "name": "Pfizer Inc.",
        "sector": "Salud",
        "description": "Farmacéutica multinacional",
    },
    "MRK": {
        "name": "Merck & Co Inc.",
        "sector": "Salud",
        "description": "Compañía farmacéutica global",
    },
    "ABBV": {
        "name": "AbbVie Inc.",
        "sector": "Salud",
        "description": "Biotecnología y productos farmacéuticos",
    },
    "LLY": {
        "name": "Eli Lilly and Co.",
        "sector": "Salud",
        "description": "Farmacéutica especializada en medicamentos innovadores",
    },
    "AMGN": {
        "name": "Amgen Inc.",
        "sector": "Salud",
        "description": "Biotecnología y terapias médicas",
    },
    "BMY": {
        "name": "Bristol-Myers Squibb Co.",
        "sector": "Salud",
        "description": "Compañía biofarmacéutica global",
    },
    "GILD": {
        "name": "Gilead Sciences Inc.",
        "sector": "Salud",
        "description": "Biotecnología especializada en antivirales",
    },
    "TMO": {
        "name": "Thermo Fisher Scientific Inc.",
        "sector": "Salud",
        "description": "Equipamiento científico y servicios de laboratorio",
    },
    # Consumo Discrecional
    "MCD": {
        "name": "McDonald's Corp.",
        "sector": "Consumo Discrecional",
        "description": "Cadena mundial de restaurantes de comida rápida",
    },
    "SBUX": {
        "name": "Starbucks Corp.",
        "sector": "Consumo Discrecional",
        "description": "Cadena internacional de cafeterías",
    },
    "NKE": {
        "name": "Nike Inc.",
        "sector": "Consumo Discrecional",
        "description": "Fabricante de calzado y ropa deportiva",
    },
    "TGT": {
        "name": "Target Corporation",
        "sector": "Consumo Discrecional",
        "description": "Cadena minorista de grandes almacenes",
    },
    "HD": {
        "name": "Home Depot Inc.",
        "sector": "Consumo Discrecional",
        "description": "Minorista de mejoras para el hogar",
    },
    "LOW": {
        "name": "Lowe's Companies Inc.",
        "sector": "Consumo Discrecional",
        "description": "Minorista de artículos para el hogar",
    },
    "TJX": {
        "name": "TJX Companies Inc.",
        "sector": "Consumo Discrecional",
        "description": "Minorista de ropa y artículos para el hogar",
    },
    "ROST": {
        "name": "Ross Stores Inc.",
        "sector": "Consumo Discrecional",
        "description": "Minorista de descuento de ropa y hogar",
    },
    "CMG": {
        "name": "Chipotle Mexican Grill Inc.",
        "sector": "Consumo Discrecional",
        "description": "Cadena de restaurantes de comida rápida mexicana",
    },
    "DHI": {
        "name": "D.R. Horton Inc.",
        "sector": "Consumo Discrecional",
        "description": "Constructora residencial",
    },
    # Cripto ETFs
    "BITO": {
        "name": "ProShares Bitcoin Strategy ETF",
        "sector": "Cripto ETF",
        "description": "ETF vinculado a futuros de Bitcoin",
    },
    "GBTC": {
        "name": "Grayscale Bitcoin Trust",
        "sector": "Cripto ETF",
        "description": "Fideicomiso de inversión en Bitcoin",
    },
    "ETHE": {
        "name": "Grayscale Ethereum Trust",
        "sector": "Cripto ETF",
        "description": "Fideicomiso de inversión en Ethereum",
    },
    "ARKW": {
        "name": "ARK Next Generation Internet ETF",
        "sector": "Cripto ETF",
        "description": "ETF con exposición a blockchain y cripto",
    },
    "BLOK": {
        "name": "Amplify Transformational Data Sharing ETF",
        "sector": "Cripto ETF",
        "description": "ETF enfocado en tecnologías blockchain",
    },
    # Materias Primas
    "GLD": {
        "name": "SPDR Gold Shares",
        "sector": "Materias Primas",
        "description": "ETF respaldado por oro físico",
    },
    "SLV": {
        "name": "iShares Silver Trust",
        "sector": "Materias Primas",
        "description": "ETF respaldado por plata física",
    },
    "USO": {
        "name": "United States Oil Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado al precio del petróleo",
    },
    "UNG": {
        "name": "United States Natural Gas Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado al precio del gas natural",
    },
    "CORN": {
        "name": "Teucrium Corn Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado a futuros de maíz",
    },
    "SOYB": {
        "name": "Teucrium Soybean Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado a futuros de soja",
    },
    "WEAT": {
        "name": "Teucrium Wheat Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado a futuros de trigo",
    },
    # Bonos
    "AGG": {
        "name": "iShares Core U.S. Aggregate Bond ETF",
        "sector": "Bonos",
        "description": "ETF de bonos de grado de inversión",
    },
    "BND": {
        "name": "Vanguard Total Bond Market ETF",
        "sector": "Bonos",
        "description": "ETF de bonos de amplio mercado",
    },
    "IEF": {
        "name": "iShares 7-10 Year Treasury Bond ETF",
        "sector": "Bonos",
        "description": "ETF de bonos del Tesoro a 7-10 años",
    },
    "TLT": {
        "name": "iShares 20+ Year Treasury Bond ETF",
        "sector": "Bonos",
        "description": "ETF de bonos del Tesoro a largo plazo",
    },
    "LQD": {
        "name": "iShares iBoxx $ Investment Grade Corporate Bond ETF",
        "sector": "Bonos",
        "description": "ETF de bonos corporativos grado inversión",
    },
    "HYG": {
        "name": "iShares iBoxx $ High Yield Corporate Bond ETF",
        "sector": "Bonos",
        "description": "ETF de bonos de alto rendimiento",
    },
    "JNK": {
        "name": "SPDR Bloomberg High Yield Bond ETF",
        "sector": "Bonos",
        "description": "ETF de bonos basura",
    },
    "TIP": {
        "name": "iShares TIPS Bond ETF",
        "sector": "Bonos",
        "description": "ETF de bonos protegidos contra inflación",
    },
    "MUB": {
        "name": "iShares National Muni Bond ETF",
        "sector": "Bonos",
        "description": "ETF de bonos municipales",
    },
    "SHY": {
        "name": "iShares 1-3 Year Treasury Bond ETF",
        "sector": "Bonos",
        "description": "ETF de bonos del Tesoro a corto plazo",
    },
    # Inmobiliario
    "VNQ": {
        "name": "Vanguard Real Estate ETF",
        "sector": "Inmobiliario",
        "description": "ETF del sector inmobiliario",
    },
    "XLRE": {
        "name": "Real Estate Select Sector SPDR Fund",
        "sector": "Inmobiliario",
        "description": "ETF de bienes raíces",
    },
    "REIT": {
        "name": "iShares Global REIT ETF",
        "sector": "Inmobiliario",
        "description": "ETF global de REITs",
    },
    "HST": {
        "name": "Host Hotels & Resorts Inc.",
        "sector": "Inmobiliario",
        "description": "REIT de hoteles de lujo",
    },
    "EQR": {
        "name": "Equity Residential",
        "sector": "Inmobiliario",
        "description": "REIT de apartamentos residenciales",
    },
    "AVB": {
        "name": "AvalonBay Communities Inc.",
        "sector": "Inmobiliario",
        "description": "REIT de comunidades residenciales",
    },
    "PLD": {
        "name": "Prologis Inc.",
        "sector": "Inmobiliario",
        "description": "REIT de almacenes logísticos",
    },
    "SPG": {
        "name": "Simon Property Group Inc.",
        "sector": "Inmobiliario",
        "description": "REIT de centros comerciales",
    },
    "AMT": {
        "name": "American Tower Corporation",
        "sector": "Inmobiliario",
        "description": "REIT de torres de comunicaciones",
    },
    # Volatilidad
    "VXX": {
        "name": "iPath Series B S&P 500 VIX Short-Term Futures ETN",
        "sector": "Volatilidad",
        "description": "Vinculado a futuros de VIX a corto plazo",
    },
    "UVXY": {
        "name": "ProShares Ultra VIX Short-Term Futures ETF",
        "sector": "Volatilidad",
        "description": "ETF apalancado vinculado al VIX",
    },
    "SVXY": {
        "name": "ProShares Short VIX Short-Term Futures ETF",
        "sector": "Volatilidad",
        "description": "ETF inverso vinculado al VIX",
    },
    "VIXY": {
        "name": "ProShares VIX Short-Term Futures ETF",
        "sector": "Volatilidad",
        "description": "Exposición directa a futuros del VIX",
    },
    # Forex (Principales pares por volumen)
    "EURUSD": {
        "name": "Euro/Dólar Estadounidense",
        "sector": "Forex",
        "description": "Par más negociado del mundo",
    },
    "USDJPY": {
        "name": "Dólar Estadounidense/Yen Japonés",
        "sector": "Forex",
        "description": "Par clave de Asia con alta liquidez",
    },
    "GBPUSD": {
        "name": "Libra Esterlina/Dólar Estadounidense",
        "sector": "Forex",
        "description": "Volátil par influenciado por política del Reino Unido",
    },
    "USDCHF": {
        "name": "Dólar Estadounidense/Franco Suizo",
        "sector": "Forex",
        "description": "Par considerado 'refugio seguro'",
    },
    "AUDUSD": {
        "name": "Dólar Australiano/Dólar Estadounidense",
        "sector": "Forex",
        "description": "Vinculado a materias primas y China",
    },
    "USDCAD": {
        "name": "Dólar Estadounidense/Dólar Canadiense",
        "sector": "Forex",
        "description": "Par sensible al precio del petróleo",
    },
    "NZDUSD": {
        "name": "Dólar Neozelandés/Dólar Estadounidense",
        "sector": "Forex",
        "description": "Conocido como 'kiwi', volátil en sesiones asiáticas",
    },
    "EURGBP": {
        "name": "Euro/Libra Esterlina",
        "sector": "Forex",
        "description": "Par clave europeo con alta liquidez",
    },
    "EURJPY": {
        "name": "Euro/Yen Japonés",
        "sector": "Forex",
        "description": "Cruce importante entre economías principales",
    },
    "GBPJPY": {
        "name": "Libra Esterlina/Yen Japonés",
        "sector": "Forex",
        "description": "Par volátil popular entre traders intradía",
    },
    "USDCNH": {
        "name": "Dólar Estadounidense/Yuan Chino",
        "sector": "Forex",
        "description": "Par clave para exposición a China",
    },
    "USDINR": {
        "name": "Dólar Estadounidense/Rupia India",
        "sector": "Forex",
        "description": "Par emergente con creciente importancia",
    },
    "USDTRY": {
        "name": "Dólar Estadounidense/Lira Turca",
        "sector": "Forex",
        "description": "Par emergente de alta volatilidad",
    },
}

# Universo de Trading
SYMBOLS = {
    "Índices": ["SPY", "QQQ", "DIA", "IWM", "EFA", "VWO", "IYR", "XLE", "XLF", "XLV"],
    "Tecnología": [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "TSLA",
        "NVDA",
        "META",
        "NFLX",
        "PYPL",
        "CRM",
    ],
    "Finanzas": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK"],
    "Energía": ["XOM", "CVX", "SHEL", "TTE", "COP", "EOG", "PXD", "DVN", "MPC", "PSX"],
    "Salud": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "AMGN", "BMY", "GILD", "TMO"],
    "Consumo Discrecional": [
        "MCD",
        "SBUX",
        "NKE",
        "TGT",
        "HD",
        "LOW",
        "TJX",
        "ROST",
        "CMG",
        "DHI",
    ],
    "Cripto ETFs": ["BITO", "GBTC", "ETHE", "ARKW", "BLOK"],
    "Materias Primas": ["GLD", "SLV", "USO", "UNG", "CORN", "SOYB", "WEAT"],
    "Bonos": ["AGG", "BND", "IEF", "TLT", "LQD", "HYG", "JNK", "TIP", "MUB", "SHY"],
    "Inmobiliario": [
        "VNQ",
        "XLRE",
        "IYR",
        "REIT",
        "HST",
        "EQR",
        "AVB",
        "PLD",
        "SPG",
        "AMT",
    ],
    "Volatilidad": ["VXX", "UVXY", "SVXY", "VIXY"],
    "Forex": [
        "EURUSD",
        "USDJPY",
        "GBPUSD",
        "USDCHF",
        "AUDUSD",
        "USDCAD",
        "NZDUSD",
        "EURGBP",
        "EURJPY",
        "GBPJPY",
        "USDCNH",
        "USDINR",
        "USDTRY",
    ],
}

# Estilos personalizados
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 1rem;
    }

    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    .metric-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        text-align: center;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
    }

    .metric-label {
        font-size: 0.875rem;
        color: #6c757d;
    }

    .call-badge {
        background-color: rgba(0, 200, 0, 0.2);
        color: #006400;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
    }

    .put-badge {
        background-color: rgba(200, 0, 0, 0.2);
        color: #8B0000;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
    }

    .neutral-badge {
        background-color: rgba(128, 128, 128, 0.2);
        color: #696969;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
    }

    .news-card {
        border-left: 3px solid #1E88E5;
        padding-left: 0.75rem;
        margin-bottom: 0.75rem;
    }

    .news-date {
        font-size: 0.75rem;
        color: #6c757d;
    }

    .confidence-high {
        color: #28a745;
        font-weight: 600;
    }

    .confidence-medium {
        color: #ffc107;
        font-weight: 600;
    }

    .confidence-low {
        color: #6c757d;
        font-weight: 600;
    }

    /* Estilos para indicadores de análisis institucional */
    .institutional-insight {
        border-left: 4px solid #9C27B0;
        background-color: rgba(156, 39, 176, 0.05);
        padding: 0.5rem 1rem;
        margin-bottom: 1rem;
        border-radius: 0 0.25rem 0.25rem 0;
    }

    .risk-low {
        color: #4CAF50;
        font-weight: 600;
    }

    .risk-medium {
        color: #FF9800;
        font-weight: 600;
    }

    .risk-high {
        color: #F44336;
        font-weight: 600;
    }

    .pro-trading-tip {
        background-color: rgba(33, 150, 243, 0.1);
        border: 1px solid rgba(33, 150, 243, 0.3);
        border-radius: 0.25rem;
        padding: 0.75rem;
        margin: 1rem 0;
    }

    .strategy-card {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .strategy-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border-color: #bbdefb;
    }

    /* Estilos adicionales para el análisis del experto */
    .expert-container {
        border: 1px solid #EEEEEE;
        border-radius: 10px;
        padding: 1rem;
        background-color: #FAFAFA;
        margin-top: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .expert-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        border-bottom: 1px solid #EEEEEE;
        padding-bottom: 0.5rem;
    }

    .expert-avatar {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
    }

    .expert-title {
        font-weight: 600;
        font-size: 1.2rem;
        color: #1E88E5;
    }

    .expert-content {
        line-height: 1.6;
    }

    .expert-footer {
        margin-top: 1rem;
        font-size: 0.8rem;
        color: #9E9E9E;
        text-align: right;
        border-top: 1px solid #EEEEEE;
        padding-top: 0.5rem;
    }

    /* Estilos para chat mejorado */
    .chat-container {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        height: 500px;
        overflow-y: auto;
        background-color: #f9f9f9;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .chat-message {
        margin-bottom: 0.75rem;
        padding: 0.75rem;
        border-radius: 8px;
        max-width: 85%;
    }

    .chat-message-user {
        background-color: #DCF8C6;
        margin-left: auto;
        margin-right: 0;
    }

    .chat-message-assistant {
        background-color: #FFFFFF;
        margin-left: 0;
        margin-right: auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }

    .chat-input {
        display: flex;
    }

    /* Estilos para el dashboard */
    .dashboard-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }

    .dashboard-header {
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        font-weight: 600;
    }

    /* Estilos para pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
        font-weight: 600;
    }

    /* Estilos para sidebar mejorada */
    .sidebar-profile {
        padding: 1rem;
        background-color: rgba(30, 136, 229, 0.1);
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .sidebar-profile h2 {
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
        color: #1E88E5;
    }

    .sidebar-section {
        margin-bottom: 1.5rem;
    }

    .sidebar-section-title {
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #424242;
    }

    /* Estilos para tarjeta de activo */
    .asset-card {
        background-color: #f8f9fa;
        border-left: 4px solid #1E88E5;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .asset-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .asset-name {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }

    .asset-price {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }

    .asset-details {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin-top: 0.5rem;
    }

    .asset-detail-item {
        flex: 1;
        min-width: 120px;
    }

    .asset-detail-label {
        font-size: 0.8rem;
        color: #6c757d;
        margin-bottom: 0.25rem;
    }

    .asset-detail-value {
        font-size: 1rem;
        font-weight: 600;
    }

    /* Estilo para mensaje de error */
    .error-message {
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 4px solid #F44336;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }

    .info-message {
        background-color: rgba(33, 150, 243, 0.1);
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    
    /* Estilos para scanner de mercado */
    .scanner-result {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #1E88E5;
    }
    
    .scanner-result.call {
        border-left: 4px solid #4CAF50;
    }
    
    .scanner-result.put {
        border-left: 4px solid #F44336;
    }
    
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 2rem 0;
    }
    
    .login-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 2rem;
        font-weight: bold;
    }

    /* Estilos adicionales para análisis de sentimiento y noticias */
    .sentiment-gauge {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .web-insight {
        background-color: #f8f9fa;
        border-left: 3px solid #9C27B0;
        padding: 1rem;
        border-radius: 0 5px 5px 0;
        margin-bottom: 1rem;
    }
    
    .recommendation-box {
        background-color: rgba(0, 150, 136, 0.1);
        border: 2px solid #009688;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        text-align: center;
    }
    
    .recommendation-box.call {
        background-color: rgba(76, 175, 80, 0.1);
        border-color: #4CAF50;
    }
    
    .recommendation-box.put {
        background-color: rgba(244, 67, 54, 0.1);
        border-color: #F44336;
    }
    
    .recommendation-box h2 {
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
    }
    
    .recommendation-box.call h2 {
        color: #4CAF50;
    }
    
    .recommendation-box.put h2 {
        color: #F44336;
    }
</style>
""",
    unsafe_allow_html=True,
)


# =================================================
# CLASES DE SCANNER DE MERCADO (De InversorIA Mini)
# =================================================


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
        hit_rate = (
            (self.hit_counter / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "entradas": len(self.cache),
            "hit_rate": f"{hit_rate:.1f}%",
            "hits": self.hit_counter,
            "misses": self.miss_counter,
        }


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
                        # Obtener contexto de mercado
                        context = get_market_context(symbol)
                        if not context or "error" in context:
                            continue

                        # Extraer datos clave
                        price = context.get("last_price", 0)
                        change = context.get("change_percent", 0)
                        signals = context.get("signals", {})

                        # Obtener señal general
                        overall_signal = "NEUTRAL"
                        confidence = "MEDIA"
                        if "overall" in signals:
                            signal = signals["overall"]["signal"]
                            confidence = signals["overall"]["confidence"]
                            if signal in ["compra", "compra_fuerte"]:
                                overall_signal = "ALCISTA"
                            elif signal in ["venta", "venta_fuerte"]:
                                overall_signal = "BAJISTA"

                        # Obtener señal de opciones
                        option_signal = "NEUTRAL"
                        option_strategy = "N/A"
                        if "options" in signals:
                            option_signal = signals["options"]["direction"]
                            option_strategy = signals["options"]["strategy"]

                        # Calcular ratio riesgo/recompensa
                        support_resistance = context.get("support_resistance", {})
                        supports = sorted(
                            support_resistance.get("supports", []), reverse=True
                        )
                        resistances = sorted(support_resistance.get("resistances", []))

                        rr_ratio = 0
                        stop_level = 0
                        target_level = 0

                        if supports and resistances:
                            if overall_signal == "ALCISTA":
                                stop_level = (
                                    supports[0] if len(supports) > 0 else price * 0.97
                                )
                                target_level = (
                                    resistances[0]
                                    if len(resistances) > 0
                                    else price * 1.05
                                )
                            elif overall_signal == "BAJISTA":
                                stop_level = (
                                    resistances[0]
                                    if len(resistances) > 0
                                    else price * 1.03
                                )
                                target_level = (
                                    supports[0] if len(supports) > 0 else price * 0.95
                                )

                            # Evitar división por cero
                            risk = abs(price - stop_level)
                            reward = abs(target_level - price)
                            rr_ratio = reward / risk if risk > 0 else 0

                        # Añadir resultado al scanner
                        results.append(
                            {
                                "Symbol": symbol,
                                "Sector": sector,
                                "Tendencia": overall_signal,
                                "Fuerza": confidence,
                                "Precio": price,
                                "Cambio": change,
                                "RSI": signals.get("momentum", {}).get("rsi", 50),
                                "Estrategia": option_signal,
                                "Setup": option_strategy,
                                "Confianza": confidence,
                                "Entry": price,
                                "Stop": stop_level,
                                "Target": target_level,
                                "R/R": round(rr_ratio, 2),
                                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                            }
                        )

                        # Guardar en caché
                        self.cache[symbol] = {
                            "trend_data": signals,
                            "price": price,
                            "change": change,
                            "timestamp": datetime.now(),
                        }
                    except Exception as e:
                        logger.error(f"Error escaneando {symbol}: {str(e)}")
                        continue

            # Convertir a DataFrame
            if results:
                df = pd.DataFrame(results)
                # Filtrar señales vacías o neutras si hay suficientes resultados
                if len(df) > 5:
                    df = df[df["Tendencia"] != "NEUTRAL"]
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error en scan_market: {str(e)}")
            return pd.DataFrame()


# =================================================
# FUNCIONES DE ANÁLISIS TÉCNICO Y EXPERTO (De Technical Expert Analyzer)
# =================================================


def create_technical_chart(data, symbol):
    """Crea gráfico técnico avanzado con indicadores y patrones técnicos"""
    # Verificación adecuada de DataFrame vacío
    if (
        data is None
        or (isinstance(data, pd.DataFrame) and data.empty)
        or (isinstance(data, list) and (len(data) < 20))
    ):
        logger.warning(
            f"Datos insuficientes o inválidos para crear gráfico de {symbol}"
        )
        return None

    # Convertir a DataFrame si es necesario
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    # Asegurarse que las columnas necesarias existen
    required_cols = ["Open", "High", "Low", "Close"]
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Faltan columnas OHLC en los datos de {symbol}")
        return None

    # Crear figura con subplots
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("", "MACD", "RSI"),  # Quitar el título del primer subplot
    )

    # Determinar los datos del eje X
    if "Date" in df.columns:
        x_data = df["Date"]
        x_first = x_data.iloc[0] if len(x_data) > 0 else None
        x_last = x_data.iloc[-1] if len(x_data) > 0 else None
    else:
        x_data = df.index
        x_first = x_data[0] if len(x_data) > 0 else None
        x_last = x_data[-1] if len(x_data) > 0 else None

    # Añadir Candlestick
    fig.add_trace(
        go.Candlestick(
            x=x_data,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
        ),
        row=1,
        col=1,
    )

    # Añadir volumen como barras en la misma subplot que el precio, pero con eje y secundario
    if "Volume" in df.columns:
        # Normalizar volumen para mostrarlo en la misma escala
        max_price = df["High"].max()
        max_volume = df["Volume"].max()
        if max_volume > 0:  # Evitar división por cero
            scale_factor = (
                max_price / max_volume * 0.2
            )  # Ajustar para que el volumen ocupe ~20% del gráfico
        else:
            scale_factor = 0

        # Crear colores para el volumen (verde si el precio subió, rojo si bajó)
        colors = [
            (
                "rgba(0, 150, 0, 0.3)"
                if row["Close"] >= row["Open"]
                else "rgba(255, 0, 0, 0.3)"
            )
            for _, row in df.iterrows()
        ]

        fig.add_trace(
            go.Bar(
                x=x_data,
                y=df["Volume"] * scale_factor,
                name="Volumen",
                marker={"color": colors},
                opacity=0.3,
                showlegend=True,
                hovertemplate="Volumen: %{y:.0f}<extra></extra>",  # Mostrar volumen real en hover
            ),
            row=1,
            col=1,
        )

    # Añadir Medias Móviles
    for ma, color in [
        ("SMA_20", "rgba(13, 71, 161, 0.7)"),
        ("SMA_50", "rgba(141, 110, 99, 0.7)"),
        ("SMA_200", "rgba(183, 28, 28, 0.7)"),
    ]:
        if ma in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=df[ma],
                    name=ma,
                    line=dict(color=color, width=1.5),
                ),
                row=1,
                col=1,
            )

    # Añadir Bandas Bollinger
    for bb, color, fill in [
        ("BB_Upper", "rgba(0, 150, 136, 0.3)", None),
        ("BB_MA20", "rgba(0, 150, 136, 0.7)", None),  # Usar SMA_20 si BB_MA20 no existe
        ("BB_Lower", "rgba(0, 150, 136, 0.3)", "tonexty"),
    ]:
        y_col = bb
        if bb == "BB_MA20" and bb not in df.columns and "SMA_20" in df.columns:
            y_col = "SMA_20"  # Fallback a SMA_20

        if y_col in df.columns:
            y_data = df[y_col]
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    name=bb,
                    line=dict(color=color, width=1),
                    fill=fill,
                    fillcolor=(
                        color.replace("0.3)", "0.1)").replace("0.7)", "0.1)")
                        if fill
                        else None
                    ),  # Lighter fill color
                ),
                row=1,
                col=1,
            )

    # Añadir MACD
    if "MACD" in df.columns and "MACD_Signal" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=df["MACD"],
                name="MACD",
                line=dict(color="rgba(33, 150, 243, 0.7)", width=1.5),
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=df["MACD_Signal"],
                name="Señal MACD",
                line=dict(color="rgba(255, 87, 34, 0.7)", width=1.5),
            ),
            row=2,
            col=1,
        )

        # Añadir histograma MACD
        macd_hist = df["MACD"] - df["MACD_Signal"]
        colors = [
            "rgba(33, 150, 243, 0.7)" if val >= 0 else "rgba(255, 87, 34, 0.7)"
            for val in macd_hist
        ]

        fig.add_trace(
            go.Bar(
                x=x_data,
                y=macd_hist,
                name="Histograma MACD",
                marker_color=colors,
            ),
            row=2,
            col=1,
        )

    # Añadir RSI
    if "RSI" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=df["RSI"],
                name="RSI",
                line=dict(color="rgba(156, 39, 176, 0.7)", width=1.5),
            ),
            row=3,
            col=1,
        )

        # Líneas de referencia RSI
        for level, color in [
            (30, "rgba(76, 175, 80, 0.5)"),
            (50, "rgba(158, 158, 158, 0.5)"),
            (70, "rgba(255, 87, 34, 0.5)"),
        ]:
            if x_first is not None and x_last is not None:
                fig.add_shape(
                    type="line",
                    x0=x_first,
                    x1=x_last,
                    y0=level,
                    y1=level,
                    line=dict(color=color, width=1, dash="dash"),
                    row=3,
                    col=1,
                )

    # Detectar soportes y resistencias
    try:
        supports, resistances = detect_support_resistance(df)

        # Añadir líneas de soporte
        for level in supports:
            if x_first is not None and x_last is not None:
                fig.add_shape(
                    type="line",
                    x0=x_first,
                    x1=x_last,
                    y0=level,
                    y1=level,
                    line=dict(color="rgba(0, 128, 0, 0.7)", width=1, dash="dot"),
                    row=1,
                    col=1,
                )

                # Añadir etiqueta
                fig.add_annotation(
                    x=x_last,
                    y=level,
                    text=f"S: {level:.2f}",
                    showarrow=False,
                    xshift=10,
                    font=dict(color="rgba(0, 128, 0, 1)"),
                    row=1,
                    col=1,
                )

        # Añadir líneas de resistencia
        for level in resistances:
            if x_first is not None and x_last is not None:
                fig.add_shape(
                    type="line",
                    x0=x_first,
                    x1=x_last,
                    y0=level,
                    y1=level,
                    line=dict(color="rgba(255, 0, 0, 0.7)", width=1, dash="dot"),
                    row=1,
                    col=1,
                )

                # Añadir etiqueta
                fig.add_annotation(
                    x=x_last,
                    y=level,
                    text=f"R: {level:.2f}",
                    showarrow=False,
                    xshift=10,
                    font=dict(color="rgba(255, 0, 0, 1)"),
                    row=1,
                    col=1,
                )
    except Exception as e:
        logger.warning(
            f"No se pudieron detectar niveles de soporte/resistencia: {str(e)}"
        )

    # Detectar líneas de tendencia
    try:
        if "Date" in df.columns:
            # Si hay fechas, convertir a índices numéricos para cálculos de tendencia
            df_idx = df.copy()
            df_idx["idx"] = range(len(df))
            bullish_lines, bearish_lines = detect_trend_lines(df_idx)

            # Convertir índices de vuelta a fechas
            bullish_lines_dates = [
                (df["Date"].iloc[x1], y1, df["Date"].iloc[x2], y2)
                for x1, y1, x2, y2 in bullish_lines
                if x1 < len(df) and x2 < len(df)
            ]

            bearish_lines_dates = [
                (df["Date"].iloc[x1], y1, df["Date"].iloc[x2], y2)
                for x1, y1, x2, y2 in bearish_lines
                if x1 < len(df) and x2 < len(df)
            ]
        else:
            # Usar índices directamente
            bullish_lines, bearish_lines = detect_trend_lines(df)
            bullish_lines_dates = [
                (df.index[x1], y1, df.index[x2], y2)
                for x1, y1, x2, y2 in bullish_lines
                if x1 < len(df) and x2 < len(df)
            ]

            bearish_lines_dates = [
                (df.index[x1], y1, df.index[x2], y2)
                for x1, y1, x2, y2 in bearish_lines
                if x1 < len(df) and x2 < len(df)
            ]

        # Añadir líneas de tendencia alcistas
        for i, (x1, y1, x2, y2) in enumerate(bullish_lines_dates):
            fig.add_shape(
                type="line",
                x0=x1,
                y0=y1,
                x1=x2,
                y1=y2,
                line=dict(color="rgba(0, 128, 0, 0.7)", width=2),
                row=1,
                col=1,
            )

            # Añadir etiqueta solo para la primera línea (para no saturar)
            if i == 0:
                fig.add_annotation(
                    x=x2,
                    y=y2,
                    text=f"Tendencia Alcista",
                    showarrow=True,
                    arrowhead=1,
                    ax=20,
                    ay=-30,
                    font=dict(color="rgba(0, 128, 0, 1)"),
                    row=1,
                    col=1,
                )

        # Añadir líneas de tendencia bajistas
        for i, (x1, y1, x2, y2) in enumerate(bearish_lines_dates):
            fig.add_shape(
                type="line",
                x0=x1,
                y0=y1,
                x1=x2,
                y1=y2,
                line=dict(color="rgba(255, 0, 0, 0.7)", width=2),
                row=1,
                col=1,
            )

            # Añadir etiqueta solo para la primera línea
            if i == 0:
                fig.add_annotation(
                    x=x2,
                    y=y2,
                    text=f"Tendencia Bajista",
                    showarrow=True,
                    arrowhead=1,
                    ax=20,
                    ay=30,
                    font=dict(color="rgba(255, 0, 0, 1)"),
                    row=1,
                    col=1,
                )
    except Exception as e:
        logger.warning(f"No se pudieron detectar líneas de tendencia: {str(e)}")

    # Añadir patrones de velas japonesas
    try:
        candle_patterns = detect_candle_patterns(df.tail(20))

        # Mostrar solo los 3 patrones más recientes para no saturar el gráfico
        for i, pattern in enumerate(candle_patterns[:3]):
            pattern_idx = pattern.get("idx", -1)
            if pattern_idx >= 0 and pattern_idx < len(df):
                # Determinar color según tipo de patrón
                if pattern["type"] == "bullish":
                    color = "rgba(0, 128, 0, 0.7)"
                    arrow = "⬆"
                else:
                    color = "rgba(255, 0, 0, 0.7)"
                    arrow = "⬇"

                # Obtener la posición X
                x_pos = (
                    df["Date"].iloc[pattern_idx]
                    if "Date" in df.columns
                    else df.index[pattern_idx]
                )

                # Obtener la posición Y (depende del tipo de patrón)
                if pattern["type"] == "bullish":
                    y_pos = (
                        df["Low"].iloc[pattern_idx] * 0.995
                    )  # Ligeramente por debajo
                else:
                    y_pos = (
                        df["High"].iloc[pattern_idx] * 1.005
                    )  # Ligeramente por encima

                # Añadir anotación
                fig.add_annotation(
                    x=x_pos,
                    y=y_pos,
                    text=f"{arrow} {pattern['pattern']}",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=30 if pattern["type"] == "bullish" else -30,
                    font=dict(color=color, size=10),
                    bgcolor="rgba(255, 255, 255, 0.7)",
                    bordercolor=color,
                    borderwidth=1,
                    borderpad=4,
                    row=1,
                    col=1,
                )
    except Exception as e:
        logger.warning(f"No se pudieron detectar patrones de velas: {str(e)}")

    # Ajustar layout
    fig.update_layout(
        height=800,
        xaxis_rangeslider_visible=False,
        title={
            "text": f"Análisis Técnico de {symbol}",  # Título principal claro
            "y": 0.97,  # Posición elevada
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {
                "size": 24,  # Tamaño más grande para mejor visibilidad
                "color": "rgba(30, 136, 229, 0.9)",  # Color azul con 70% de opacidad
                "family": "Arial, sans-serif",
            },
        },
        template="plotly_white",
        showlegend=True,
        # Ajustar posición de la leyenda para evitar conflicto con el título
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",  # Cambiar a left para moverla al lado izquierdo
            x=0,  # Alinear al extremo izquierdo
            bgcolor="rgba(255, 255, 255, 0.8)",  # Fondo semitransparente para la leyenda
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
        margin=dict(
            l=50, r=50, t=120, b=50
        ),  # Aumentar margen superior para dar más espacio
    )

    # Configuración de ejes y rangos
    fig.update_yaxes(title_text="Precio", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])

    # Añadir crosshair
    fig.update_layout(
        xaxis=dict(
            showspikes=True,
            spikethickness=1,
            spikedash="solid",
            spikecolor="gray",
            spikemode="across",
        ),
        yaxis=dict(
            showspikes=True,
            spikethickness=1,
            spikedash="solid",
            spikecolor="gray",
            spikemode="across",
        ),
    )

    return fig


def format_patterns_for_prompt(patterns, symbol, price=None):
    """Formatea los patrones técnicos para incluirlos en el prompt del asistente IA"""
    if not patterns:
        return "No se detectaron patrones técnicos significativos."

    formatted_text = f"PATRONES TÉCNICOS DETECTADOS PARA {symbol}:\n\n"

    if price:
        formatted_text += f"Precio actual: ${price:.2f}\n\n"

    # Soportes y resistencias
    if "supports" in patterns and patterns["supports"]:
        formatted_text += "SOPORTES DETECTADOS:\n"
        for level in patterns["supports"]:
            dist = ((level / price) - 1) * 100 if price else 0
            formatted_text += f"- ${level:.2f} ({dist:.2f}% desde precio actual)\n"
        formatted_text += "\n"

    if "resistances" in patterns and patterns["resistances"]:
        formatted_text += "RESISTENCIAS DETECTADAS:\n"
        for level in patterns["resistances"]:
            dist = ((level / price) - 1) * 100 if price else 0
            formatted_text += f"- ${level:.2f} ({dist:.2f}% desde precio actual)\n"
        formatted_text += "\n"

    # Tendencias
    if "trend_lines" in patterns:
        if patterns["trend_lines"].get("bullish"):
            formatted_text += "LÍNEAS DE TENDENCIA ALCISTA: Identificadas\n"

        if patterns["trend_lines"].get("bearish"):
            formatted_text += "LÍNEAS DE TENDENCIA BAJISTA: Identificadas\n"

        if patterns["trend_lines"].get("bullish") or patterns["trend_lines"].get(
            "bearish"
        ):
            formatted_text += "\n"

    # Canales
    if "channels" in patterns and patterns["channels"]:
        formatted_text += "CANALES DE PRECIO:\n"
        for i, channel in enumerate(patterns["channels"]):
            formatted_text += (
                f"- Canal {i+1}: Tipo {channel.get('type', 'desconocido')}\n"
            )
        formatted_text += "\n"

    # Patrones de velas
    if "candle_patterns" in patterns and patterns["candle_patterns"]:
        formatted_text += "PATRONES DE VELAS JAPONESAS:\n"
        for pattern in patterns["candle_patterns"]:
            formatted_text += f"- {pattern['pattern']} ({pattern['type'].capitalize()}, fuerza {pattern.get('strength', 'media')})\n"
        formatted_text += "\n"

    # Si no se encontró ningún patrón específico
    if (
        not ("supports" in patterns and patterns["supports"])
        and not ("resistances" in patterns and patterns["resistances"])
        and not ("candle_patterns" in patterns and patterns["candle_patterns"])
    ):
        formatted_text += "No se detectaron patrones significativos en este período.\n"

    return formatted_text


def process_message_with_citations(message):
    """Extrae y devuelve el texto del mensaje del asistente con manejo mejorado de errores"""
    try:
        if hasattr(message, "content") and len(message.content) > 0:
            message_content = message.content[0]
            if hasattr(message_content, "text"):
                nested_text = message_content.text
                if hasattr(nested_text, "value"):
                    return nested_text.value
                elif isinstance(nested_text, str):
                    return nested_text
            elif isinstance(message_content, dict) and "text" in message_content:
                return message_content["text"].get("value", message_content["text"])
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")

    return "No se pudo procesar el mensaje del asistente"


def process_expert_analysis(client, assistant_id, symbol, context):
    """Procesa análisis experto con OpenAI asegurando una sección de análisis fundamental"""
    if not client or not assistant_id:
        return None

    # Formatear prompt para el asistente
    price = context.get("last_price", 0)
    change = context.get("change_percent", 0)
    vix_level = context.get("vix_level", "N/A")
    signals = context.get("signals", {})

    # Obtener señal general
    overall_signal = "NEUTRAL"
    if "overall" in signals:
        signal = signals["overall"]["signal"]
        if signal in ["compra", "compra_fuerte"]:
            overall_signal = "ALCISTA"
        elif signal in ["venta", "venta_fuerte"]:
            overall_signal = "BAJISTA"

    # Obtener señal de opciones
    option_signal = "NEUTRAL"
    if "options" in signals:
        option_signal = signals["options"]["direction"]

    # Extraer información fundamental si está disponible
    fundamental_data = context.get("fundamental_data", {})
    fundamentals_text = ""
    if fundamental_data:
        fundamentals_text = "DATOS FUNDAMENTALES:\n"
        for key, value in fundamental_data.items():
            fundamentals_text += f"- {key}: {value}\n"

    # Extraer información de noticias si está disponible
    news = context.get("news", [])
    news_text = ""
    if news:
        news_text = "NOTICIAS RECIENTES:\n"
        for i, item in enumerate(news[:5]):  # Limitar a 5 noticias principales
            sentiment_indicator = ""
            if item.get("sentiment", 0.5) > 0.6:
                sentiment_indicator = "📈 [POSITIVA]"
            elif item.get("sentiment", 0.5) < 0.4:
                sentiment_indicator = "📉 [NEGATIVA]"

            news_text += f"{i+1}. {sentiment_indicator} {item.get('title', '')}\n"
            if item.get("summary"):
                news_text += f"   Resumen: {item.get('summary')[:150]}...\n"
            news_text += f"   Fuente: {item.get('source', 'Desconocida')}\n\n"

    # Extraer sentimiento de noticias
    sentiment = context.get("news_sentiment", {})
    sentiment_text = ""
    if sentiment:
        sentiment_score = sentiment.get("score", 0.5) * 100
        sentiment_text = f"SENTIMIENTO: {sentiment.get('sentiment', 'neutral')} ({sentiment_score:.1f}%)\n"
        sentiment_text += (
            f"Menciones positivas: {sentiment.get('positive_mentions', 0)}\n"
        )
        sentiment_text += (
            f"Menciones negativas: {sentiment.get('negative_mentions', 0)}\n"
        )

        # Añadir ratio positivo/negativo
        total_mentions = sentiment.get("positive_mentions", 0) + sentiment.get(
            "negative_mentions", 0
        )
        if total_mentions > 0:
            positive_ratio = (
                sentiment.get("positive_mentions", 0) / total_mentions * 100
            )
            sentiment_text += f"Ratio positivo: {positive_ratio:.1f}%\n"

    # Extraer insights web del mercado
    web_analysis = context.get("web_analysis", {})
    web_insights_text = ""
    if web_analysis:
        web_results = web_analysis.get("web_results", [])
        if web_results:
            web_insights_text = "INSIGHTS DEL MERCADO:\n"
            for i, result in enumerate(web_results[:3]):  # Limitamos a 3 resultados
                web_insights_text += f"{i+1}. {result.get('title', 'Sin título')}\n"
                content = result.get("content", "")
                if content:
                    web_insights_text += f"   {content[:200]}...\n"
                web_insights_text += (
                    f"   Fuente: {result.get('source', 'Desconocida')}\n\n"
                )

    # Detectar patrones
    chart_data = pd.DataFrame(context.get("chart_data", []))
    patterns = {}

    if not chart_data.empty:
        try:
            supports, resistances = detect_support_resistance(chart_data)
            patterns["supports"] = supports
            patterns["resistances"] = resistances

            bullish_lines, bearish_lines = detect_trend_lines(chart_data)
            patterns["trend_lines"] = {
                "bullish": bullish_lines,
                "bearish": bearish_lines,
            }

            # Patrones de velas (últimas 20)
            candle_patterns = detect_candle_patterns(chart_data.tail(20))
            patterns["candle_patterns"] = candle_patterns

            # Formatear patrones para el prompt
            patterns_text = format_patterns_for_prompt(patterns, symbol, price)
        except Exception as e:
            logger.error(f"Error detectando patrones: {str(e)}")
            patterns_text = (
                "No se pudieron detectar patrones técnicos debido a un error."
            )
    else:
        patterns_text = "No hay datos suficientes para detectar patrones técnicos."

    # Ejemplo de estructura requerida
    example_structure = """
Ejemplo de estructura EXACTA requerida:

## EVALUACIÓN GENERAL
(Texto de evaluación general...)

## NIVELES CLAVE
(Texto de niveles clave...)

## ANÁLISIS TÉCNICO
(Texto de análisis técnico...)

## ANÁLISIS FUNDAMENTAL Y NOTICIAS
(Texto de análisis fundamental y noticias...)

## ESTRATEGIAS RECOMENDADAS
(Texto de estrategias recomendadas...)

## GESTIÓN DE RIESGO
(Texto de gestión de riesgo...)

## PROYECCIÓN DE MOVIMIENTO
(Texto de proyección de movimiento...)

## RECOMENDACIÓN FINAL: CALL/PUT/NEUTRAL
(Texto de recomendación final...)
"""

    # Crear contenido del prompt enriquecido con toda la información disponible
    prompt = f"""
    Como Especialista en Trading y Análisis Técnico Avanzado, realiza un análisis profesional integral del siguiente activo:

    SÍMBOLO: {symbol}

    DATOS DE MERCADO:
    - Precio actual: ${price:.2f} ({'+' if change > 0 else ''}{change:.2f}%)
    - VIX: {vix_level}
    - Señal técnica: {overall_signal}
    - Señal de opciones: {option_signal}

    INFORMACIÓN FUNDAMENTAL:
    {fundamentals_text}

    SENTIMIENTO DE MERCADO:
    {sentiment_text}

    NOTICIAS RELEVANTES:
    {news_text}

    ANÁLISIS DE ANALISTAS:
    {web_insights_text}

    PATRONES TÉCNICOS:
    {patterns_text}

    INSTRUCCIONES ESPECÍFICAS:
    1. Proporciona una evaluación integral que combine análisis técnico, fundamental y sentimiento de mercado.
    2. Identifica claramente los niveles de soporte y resistencia clave.
    3. Analiza los indicadores técnicos principales (RSI, MACD, medias móviles).
    4. INCLUYE OBLIGATORIAMENTE UNA SECCIÓN DEDICADA AL "ANÁLISIS FUNDAMENTAL Y NOTICIAS" QUE DEBE EVALUAR EL IMPACTO DE LAS NOTICIAS, SENTIMIENTO Y ANÁLISIS DE ANALISTAS EN EL PRECIO.
    5. Sugiere estrategias específicas para traders institucionales, especialmente con opciones.
    6. Indica riesgos clave y niveles de stop loss recomendados.
    7. Concluye con una proyección de movimiento y una RECOMENDACIÓN FINAL clara (CALL, PUT o NEUTRAL).

    FORMATO DE RESPUESTA:
    DEBES estructurar tu respuesta EXACTAMENTE con estos encabezados y en este orden:
    
    ## EVALUACIÓN GENERAL
    
    ## NIVELES CLAVE
    
    ## ANÁLISIS TÉCNICO
    
    ## ANÁLISIS FUNDAMENTAL Y NOTICIAS
    
    ## ESTRATEGIAS RECOMENDADAS
    
    ## GESTIÓN DE RIESGO
    
    ## PROYECCIÓN DE MOVIMIENTO
    
    ## RECOMENDACIÓN FINAL: (CALL/PUT/NEUTRAL)
    
    ES CRÍTICO QUE INCLUYAS LA SECCIÓN "ANÁLISIS FUNDAMENTAL Y NOTICIAS". No combinar esta información en otras secciones.
    El formato debe ser estrictamente Markdown, sin usar comillas triples ni marcas HTML. No uses asteriscos dobles en la recomendación final.
    
    {example_structure}
    """

    try:
        # Enviar mensaje al thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=prompt
        )

        # Crear una ejecución para el thread
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=assistant_id
        )

        # Mostrar progreso
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Esperar a que se complete la ejecución con timeout
        start_time = time.time()
        timeout = 45  # 45 segundos máximo

        while run.status not in ["completed", "failed", "cancelled", "expired"]:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                status_text.error(
                    "El análisis del experto está tardando demasiado. Por favor, inténtalo de nuevo."
                )
                return "Error: Timeout en la consulta al experto"

            # Actualizar progreso
            progress = min(0.9, elapsed / timeout)
            progress_bar.progress(progress)
            status_text.text(f"El experto está analizando {symbol}... ({run.status})")

            # Esperar antes de verificar de nuevo
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id, run_id=run.id
            )

        # Completar barra de progreso
        progress_bar.progress(1.0)
        status_text.empty()

        if run.status != "completed":
            return f"Error: La consulta al experto falló con estado {run.status}"

        # Recuperar mensajes
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Obtener respuesta
        for message in messages:
            if message.run_id == run.id and message.role == "assistant":
                # Extraer texto del mensaje
                return process_message_with_citations(message)

        return "No se recibió respuesta del experto."

    except Exception as e:
        logger.error(f"Error al consultar al experto: {str(e)}")
        return f"Error al consultar al experto: {str(e)}"


def display_expert_opinion(expert_opinion):
    """Muestra la opinión del experto IA con formato mejorado y opción de exportar a MD"""
    if not expert_opinion:
        return

    st.markdown("## 🧠 Análisis del Experto")

    # Procesamiento mejorado del texto: buscar secciones clave
    sections = {
        "evaluación": "",
        "niveles": "",
        "técnico": "",
        "fundamental": "",
        "estrategias": "",
        "riesgo": "",
        "proyección": "",
        "recomendación": "",
    }

    current_section = None
    final_recommendation = None
    recommendation_type = "NEUTRAL"

    try:
        # Limpiar el texto completo de marcadores de código, HTML y formateo markdown
        expert_opinion = re.sub(r"```.*?```", "", expert_opinion, flags=re.DOTALL)
        expert_opinion = expert_opinion.replace("```", "")
        expert_opinion = re.sub(r"<.*?>", "", expert_opinion)

        # Intentar identificar secciones en el texto
        lines = expert_opinion.split("\n")
        for line in lines:
            line = line.strip()

            # Detectar secciones por encabezados (más flexible ahora)
            if re.search(r"##?\s*EVALUACI[OÓ]N\s*GENERAL", line.upper()):
                current_section = "evaluación"
                continue
            elif re.search(r"##?\s*NIVELES\s*CLAVE", line.upper()):
                current_section = "niveles"
                continue
            elif re.search(r"##?\s*AN[AÁ]LISIS\s*T[EÉ]CNICO", line.upper()):
                current_section = "técnico"
                continue
            elif re.search(
                r"##?\s*AN[AÁ]LISIS\s*FUNDAMENTAL", line.upper()
            ) or re.search(r"##?\s*NOTICIAS", line.upper()):
                current_section = "fundamental"
                continue
            elif re.search(r"##?\s*ESTRATEGIAS", line.upper()):
                current_section = "estrategias"
                continue
            elif re.search(
                r"##?\s*GESTI[OÓ]N\s*DE\s*RIESGO", line.upper()
            ) or re.search(r"##?\s*STOP\s*LOSS", line.upper()):
                current_section = "riesgo"
                continue
            elif re.search(r"##?\s*PROYECCI[OÓ]N", line.upper()):
                current_section = "proyección"
                continue
            elif re.search(r"##?\s*RECOMENDACI[OÓ]N\s*FINAL", line.upper()):
                current_section = "recomendación"

                # Extraer la recomendación final (CALL, PUT o NEUTRAL)
                if "CALL" in line.upper():
                    recommendation_type = "CALL"
                elif "PUT" in line.upper():
                    recommendation_type = "PUT"
                continue

            # Agregar línea a la sección actual
            if current_section and line:
                sections[current_section] += line + "\n"

                # Guardar la recomendación final de forma completa
                if current_section == "recomendación":
                    final_recommendation = sections[current_section]

                    # Detectar si hay una recomendación explícita de CALL o PUT
                    if "CALL" in line.upper() and recommendation_type == "NEUTRAL":
                        recommendation_type = "CALL"
                    elif "PUT" in line.upper() and recommendation_type == "NEUTRAL":
                        recommendation_type = "PUT"
    except Exception as e:
        logger.error(f"Error al procesar la respuesta del experto: {str(e)}")

    # Determinar la clase de color para la recomendación
    recommendation_class = (
        "call"
        if recommendation_type == "CALL"
        else "put" if recommendation_type == "PUT" else ""
    )

    # Botón para exportar a Markdown
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("📥 Exportar MD", help="Descargar análisis en formato Markdown"):
            # Crear contenido Markdown para descargar
            markdown_content = f"# Análisis de Trading: {recommendation_type} - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"

            # Agregar secciones al markdown
            for section_name, section_content in sections.items():
                if section_content:
                    # Convertir nombre de sección a título
                    title_mapping = {
                        "evaluación": "## Evaluación General",
                        "niveles": "## Niveles Clave",
                        "técnico": "## Análisis Técnico",
                        "fundamental": "## Análisis Fundamental y Noticias",
                        "estrategias": "## Estrategias Recomendadas",
                        "riesgo": "## Gestión de Riesgo",
                        "proyección": "## Proyección de Movimiento",
                        "recomendación": f"## Recomendación Final: {recommendation_type}",
                    }

                    # Añadir título y contenido
                    markdown_content += f"{title_mapping.get(section_name, '## ' + section_name.capitalize())}\n\n"
                    markdown_content += f"{section_content}\n\n"

            # Añadir pie de página
            markdown_content += f"---\n*Análisis generado por InversorIA Pro - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*"

            # Convertir a bytes para descargar
            b64 = base64.b64encode(markdown_content.encode()).decode()

            # Crear enlace de descarga
            href = f'<a href="data:file/markdown;base64,{b64}" download="analisis_trading_{datetime.now().strftime("%Y%m%d_%H%M")}.md">Haga clic aquí si la descarga no comienza automáticamente</a>'

            # Mostrar enlace y disparar descarga
            st.markdown(href, unsafe_allow_html=True)
            st.markdown(
                f"""
                <script>
                    var link = document.createElement('a');
                    link.href = "data:file/markdown;base64,{b64}";
                    link.download = "analisis_trading_{datetime.now().strftime('%Y%m%d_%H%M')}.md";
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                </script>
                """,
                unsafe_allow_html=True,
            )

    # Mostrar recomendación final en un box destacado si existe
    if final_recommendation:
        # Limpiar posibles marcadores de código o formato no deseado
        clean_recommendation = re.sub(r"[\*\`]", "", final_recommendation)

        # Usar la recomendación como texto plano en el HTML
        st.markdown(
            f"""
            <div class="recommendation-box {recommendation_class}">
                <h2>RECOMENDACIÓN: {recommendation_type}</h2>
                <p>{clean_recommendation}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Si no se identificaron secciones, mostrar el texto completo
    if all(not v for v in sections.values()):
        # Limpiar el texto completo de marcadores de código
        cleaned_opinion = re.sub(r"[\*\`]", "", expert_opinion)

        st.markdown(
            f"""
            <div class="expert-container">
                <div class="expert-header">
                    <div class="expert-avatar">E</div>
                    <div class="expert-title">Analista de Mercados</div>
                </div>
                <div class="expert-content">
                    {cleaned_opinion}
                </div>
                <div class="expert-footer">
                    Análisis generado por IA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Mostrar secciones identificadas
        st.markdown(
            f"""
            <div class="expert-container">
                <div class="expert-header">
                    <div class="expert-avatar">E</div>
                    <div class="expert-title">Analista de Mercados</div>
                </div>
                <div class="expert-content">
            """,
            unsafe_allow_html=True,
        )

        # Mostrar cada sección identificada en un formato más estructurado
        # Limpiando posibles marcadores de código, utilizando regex para eliminar caracteres especiales
        if sections["evaluación"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["evaluación"])
            st.markdown("### 📊 Evaluación General")
            st.markdown(cleaned_text)

        if sections["niveles"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["niveles"])
            st.markdown("### 🔍 Niveles Clave")
            st.markdown(cleaned_text)

        if sections["técnico"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["técnico"])
            st.markdown("### 📈 Análisis Técnico")
            st.markdown(cleaned_text)

        if sections["fundamental"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["fundamental"])
            st.markdown("### 📰 Análisis Fundamental y Noticias")
            st.markdown(cleaned_text)

        if sections["estrategias"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["estrategias"])
            st.markdown("### 🎯 Estrategias Recomendadas")
            st.markdown(cleaned_text)

        if sections["riesgo"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["riesgo"])
            st.markdown("### ⚠️ Gestión de Riesgo")
            st.markdown(cleaned_text)

        if sections["proyección"]:
            cleaned_text = re.sub(r"[\*\`]", "", sections["proyección"])
            st.markdown("### 🔮 Proyección de Movimiento")
            st.markdown(cleaned_text)

        st.markdown(
            f"""
                </div>
                <div class="expert-footer">
                    Análisis generado por IA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =================================================
# FUNCIONES PARA MOSTRAR SENTIMIENTO Y NOTICIAS
# =================================================


def display_sentiment_analysis(context):
    """Muestra análisis de sentimiento integrado desde MarketIntel"""
    sentiment = context.get("news_sentiment", {})
    web_analysis = context.get("web_analysis", {})

    if not sentiment and not web_analysis:
        st.info(
            """
        No se encontró análisis de sentimiento disponible.
        
        **Posibles soluciones:**
        - Verifica la configuración de API keys en .streamlit/secrets.toml
        - Asegúrate de que las claves "you_api_key", "tavily_api_key" o "alpha_vantage_api_key" estén configuradas
        - Para evitar errores, puedes importar la función get_api_keys_from_secrets de market_utils
        """
        )
        return

    st.markdown(
        '<div class="sub-header">📊 Análisis de Sentimiento</div>',
        unsafe_allow_html=True,
    )

    # Mostrar sentimiento de noticias
    col1, col2 = st.columns(2)

    with col1:
        if sentiment:
            # Mostrar sentimiento
            sentiment_value = sentiment.get("sentiment", "neutral")
            sentiment_score = sentiment.get("score", 0.5)

            # Crear medidor
            st.markdown("### Sentimiento de Noticias")

            # Crear gráfico gauge con Plotly
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=sentiment_score * 100,
                    title={"text": "Sentimiento"},
                    gauge={
                        "axis": {"range": [0, 100], "tickwidth": 1},
                        "bar": {"color": "rgba(0,0,0,0)"},
                        "steps": [
                            {"range": [0, 40], "color": "rgba(255, 87, 34, 0.3)"},
                            {"range": [40, 60], "color": "rgba(158, 158, 158, 0.3)"},
                            {"range": [60, 100], "color": "rgba(76, 175, 80, 0.3)"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": sentiment_score * 100,
                        },
                    },
                )
            )

            fig.update_layout(
                height=250,
                margin=dict(l=10, r=10, t=50, b=10),
            )

            st.plotly_chart(fig, use_container_width=True)

            # Mostrar métricas adicionales
            pos = sentiment.get("positive_mentions", 0)
            neg = sentiment.get("negative_mentions", 0)
            total = sentiment.get("total_analyzed", 0)

            st.markdown(
                f"""
            **Menciones positivas:** {pos}  
            **Menciones negativas:** {neg}  
            **Total noticias analizadas:** {total}
            """
            )

    with col2:
        if web_analysis:
            # Mostrar análisis web
            bullish = web_analysis.get("bullish_mentions", 0)
            bearish = web_analysis.get("bearish_mentions", 0)
            total_mentions = bullish + bearish

            st.markdown("### Análisis Web")

            # Solo mostrar gráfico si hay datos reales
            if total_mentions > 0:
                # Crear gráfico de barras
                fig = go.Figure()

                fig.add_trace(
                    go.Bar(
                        x=["Alcista", "Bajista"],
                        y=[bullish, bearish],
                        text=[bullish, bearish],
                        textposition="auto",
                        marker_color=[
                            "rgba(76, 175, 80, 0.7)",
                            "rgba(255, 87, 34, 0.7)",
                        ],
                    )
                )

                fig.update_layout(
                    title="Menciones en Fuentes Web",
                    height=250,
                    margin=dict(l=10, r=10, t=50, b=10),
                    yaxis_title="Número de menciones",
                    xaxis_title="Sentimiento",
                )

                # Establecer rango mínimo para el eje Y
                fig.update_yaxes(range=[0, max(max(bullish, bearish) + 1, 5)])

                st.plotly_chart(fig, use_container_width=True)

                # Ratio de sentimiento
                bullish_ratio = bullish / total_mentions * 100
                st.markdown(
                    f"""
                **Ratio alcista:** {bullish_ratio:.1f}%  
                **Fuentes analizadas:** {len(context.get('web_results', []))}
                """
                )
            else:
                st.info("No se encontraron menciones relevantes en el análisis web.")


def display_news_feed(context):
    """Muestra feed de noticias integrado desde MarketIntel"""
    news = context.get("news", [])

    if not news:
        st.info(
            """
        No se encontraron noticias recientes.
        
        **Posibles soluciones:**
        - Verifica la configuración de Alpha Vantage API key
        - Asegúrate de que tienes acceso al endpoint de noticias de Alpha Vantage
        - Algunos símbolos pueden no tener cobertura de noticias
        """
        )
        return

    st.markdown(
        '<div class="sub-header">📰 Noticias Recientes</div>', unsafe_allow_html=True
    )

    # Mostrar noticias recientes
    for item in news:
        st.markdown(
            f"""
        <div class="news-card">
            <div class="news-date">{item.get('date', 'Fecha no disponible')}</div>
            <a href="{item.get('url', '#')}" target="_blank">{item.get('title', 'Sin título')}</a>
        </div>
        """,
            unsafe_allow_html=True,
        )


def display_web_insights(context):
    """Muestra insights de búsqueda web integrado desde MarketIntel"""
    web_results = context.get("web_results", [])

    if not web_results:
        st.info("No se encontraron resultados de búsqueda web.")
        return

    st.markdown(
        '<div class="sub-header">🌐 Insights de Mercado</div>', unsafe_allow_html=True
    )

    # Mostrar resultados de búsqueda web en un expander
    with st.expander("Ver fuentes de análisis"):
        for i, result in enumerate(web_results):
            st.markdown(
                f"""
            #### {result.get('title', 'Sin título')}
            {result.get('content', 'Sin contenido')}
            
            [Leer más en {result.get('source', 'Fuente')}]({result.get('url', '#')})
            """
            )

            if i < len(web_results) - 1:
                st.markdown("---")


# =================================================
# FUNCIONES DE VISUALIZACIÓN AVANZADA
# =================================================


def get_company_info(symbol):
    """Obtiene información completa de la empresa o activo"""
    # Si el símbolo está en nuestra base de datos de información de compañías
    if symbol in COMPANY_INFO:
        return COMPANY_INFO[symbol]

    # Información para símbolos no conocidos explícitamente
    # Determinar a qué categoría pertenece
    category = None
    for cat, symbols in SYMBOLS.items():
        if symbol in symbols:
            category = cat
            break

    if not category:
        category = "No categorizado"

    # Crear información básica
    return {
        "name": f"{symbol}",
        "sector": category,
        "description": f"Activo financiero negociado bajo el símbolo {symbol}",
    }


def display_technical_summary(symbol, technical_data):
    """Muestra resumen técnico en un formato mejorado"""
    st.markdown("### 📊 Resumen Técnico")

    # Crear columnas para mostrar datos clave
    col1, col2, col3, col4 = st.columns(4)

    # Extraer últimos valores
    if isinstance(technical_data, pd.DataFrame) and not technical_data.empty:
        last_row = technical_data.iloc[-1]
        last_price = last_row["Close"]

        # Calcular cambio porcentual
        if len(technical_data) > 1:
            prev_close = technical_data.iloc[-2]["Close"]
            change_pct = (last_price - prev_close) / prev_close * 100
        else:
            change_pct = 0

        # Extraer RSI y MA values si están disponibles
        rsi = last_row.get("RSI", None)
        sma20 = last_row.get("SMA_20", None)
        sma50 = last_row.get("SMA_50", None)
        sma200 = last_row.get("SMA_200", None)

        # Determinar condiciones de tendencia
        above_sma20 = last_price > sma20 if sma20 is not None else None
        above_sma50 = last_price > sma50 if sma50 is not None else None
        above_sma200 = last_price > sma200 if sma200 is not None else None

        # Métricas en columnas
        with col1:
            st.metric(
                label=f"{symbol} - Último",
                value=f"${last_price:.2f}",
                delta=f"{change_pct:+.2f}%",
            )

        with col2:
            if rsi is not None:
                rsi_status = (
                    "Sobrecompra"
                    if rsi > 70
                    else "Sobreventa" if rsi < 30 else "Neutral"
                )
                st.metric(
                    label="RSI", value=f"{rsi:.1f}", delta=rsi_status, delta_color="off"
                )
            else:
                st.metric(label="RSI", value="N/A")

        with col3:
            if sma20 is not None and sma50 is not None:
                ma_cross = (
                    "Alcista"
                    if sma20 > sma50
                    else "Bajista" if sma20 < sma50 else "Neutral"
                )
                st.metric(
                    label="Cruce MA20/50",
                    value=ma_cross,
                    delta=f"MA20: ${sma20:.2f}",
                    delta_color="off",
                )
            else:
                st.metric(label="Cruce MA", value="N/A")

        with col4:
            if above_sma200 is not None:
                trend = "Alcista LP" if above_sma200 else "Bajista LP"
                st.metric(
                    label="Tendencia LP",
                    value=trend,
                    delta=f"MA200: ${sma200:.2f}" if sma200 is not None else "N/A",
                    delta_color="normal" if above_sma200 else "inverse",
                )
            else:
                st.metric(label="Tendencia LP", value="N/A")
    else:
        st.warning(f"No hay datos técnicos disponibles para {symbol}")


def display_options_analysis(symbol, options_data):
    """Muestra análisis de opciones en formato mejorado"""
    st.markdown("### 🎯 Análisis de Opciones")

    if options_data is None or not options_data:
        st.warning(f"No hay datos de opciones disponibles para {symbol}")
        return

    # Extraer datos clave
    recommendation = options_data.get("recommendation", "NEUTRAL")
    confidence = options_data.get("confidence", "baja")
    strategy = options_data.get("strategy", "N/A")
    implied_vol = options_data.get("implied_volatility", 0)

    # Crear columnas para mostrar métricas clave
    col1, col2, col3 = st.columns(3)

    # Determinar clases CSS
    badge_class = (
        "call-badge"
        if recommendation == "CALL"
        else "put-badge" if recommendation == "PUT" else "neutral-badge"
    )
    confidence_class = f"confidence-{'high' if confidence == 'alta' else 'medium' if confidence == 'media' else 'low'}"

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value"><span class="{badge_class}">{recommendation}</span></div>
            <div class="metric-label">Recomendación</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value"><span class="{confidence_class}">{confidence.upper()}</span></div>
            <div class="metric-label">Confianza</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value">{implied_vol:.2f}%</div>
            <div class="metric-label">Volatilidad Implícita</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Mostrar estrategias recomendadas
    st.markdown("#### Estrategias Recomendadas")

    if recommendation == "CALL":
        st.markdown(
            """
            <div class="strategy-card">
                <h4>Call Debit Spread</h4>
                <p><strong>Descripción:</strong> Compra un CALL ATM y vende un CALL OTM con el mismo vencimiento.</p>
                <p><strong>Beneficio máximo:</strong> Limitado al diferencial entre strikes menos la prima pagada.</p>
                <p><strong>Pérdida máxima:</strong> Limitada a la prima neta pagada.</p>
                <p><strong>Volatilidad:</strong> Favorable en entorno de volatilidad baja a moderada.</p>
                <p><strong>Horizonte:</strong> 2-4 semanas.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif recommendation == "PUT":
        st.markdown(
            """
            <div class="strategy-card">
                <h4>Put Debit Spread</h4>
                <p><strong>Descripción:</strong> Compra un PUT ATM y vende un PUT OTM con el mismo vencimiento.</p>
                <p><strong>Beneficio máximo:</strong> Limitado al diferencial entre strikes menos la prima pagada.</p>
                <p><strong>Pérdida máxima:</strong> Limitada a la prima neta pagada.</p>
                <p><strong>Volatilidad:</strong> Favorable en entorno de volatilidad baja a moderada.</p>
                <p><strong>Horizonte:</strong> 2-4 semanas.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="strategy-card">
                <h4>Iron Condor</h4>
                <p><strong>Descripción:</strong> Combinación de un Bull Put Spread y un Bear Call Spread.</p>
                <p><strong>Beneficio máximo:</strong> Limitado a la prima neta recibida.</p>
                <p><strong>Pérdida máxima:</strong> Diferencia entre strikes del mismo lado menos prima recibida.</p>
                <p><strong>Volatilidad:</strong> Ideal para entornos de baja volatilidad y consolidación.</p>
                <p><strong>Horizonte:</strong> 2-5 semanas.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def display_asset_info(symbol, price=None, change=None):
    """Muestra información básica del activo compatible con modo claro y oscuro"""
    # Obtener información completa de la empresa/activo
    company_info = get_company_info(symbol)

    # Obtener nombre completo del activo
    full_name = company_info.get("name", symbol)
    sector = company_info.get("sector", "No especificado")
    description = company_info.get("description", "")

    # Estimar precio y cambio si no están disponibles
    price_display = f"${price:.2f}" if price is not None else "N/A"
    change_display = f"{change:+.2f}%" if change is not None else ""

    # Color condicional para cambio
    change_color = (
        "green"
        if change is not None and change >= 0
        else "red" if change is not None and change < 0 else "inherit"
    )

    # Usar st.container() con estilos nativos de Streamlit que se adaptan al modo oscuro/claro
    with st.container():
        # Encabezado del activo
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"## {full_name} ({symbol})")

        with col2:
            st.markdown(
                f"<h2 style='text-align: right; color: {change_color};'>{price_display} <span style='font-size: 0.8em;'>{change_display}</span></h2>",
                unsafe_allow_html=True,
            )

        # Descripción y detalles
        st.markdown(description)

        # Mostrar detalles adicionales
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Sector:** {sector}")

        with col2:
            st.markdown(
                f"**Última Actualización:** {datetime.now().strftime('%H:%M:%S')}"
            )

        # Línea separadora
        st.markdown("---")


# =================================================
# FUNCIONES DE ASISTENTE MEJORADAS
# =================================================


def process_chat_input_with_openai(
    prompt, symbol=None, api_key=None, assistant_id=None, context=None
):
    """
    Procesa la entrada del chat utilizando OpenAI para respuestas más naturales y variadas.
    """
    try:
        # Si no se proporciona símbolo, intentar detectarlo en el mensaje
        if not symbol:
            words = prompt.split()
            for word in words:
                word = word.strip(",.?!").upper()
                for category, symbols in SYMBOLS.items():
                    if word in symbols:
                        symbol = word
                        break

            if not symbol:
                symbol = st.session_state.get("current_symbol", "SPY")

        # Verificar si OpenAI está configurado correctamente
        if not api_key:
            # Modo fallback: generar respuesta basada en análisis local
            return fallback_analyze_symbol(symbol, prompt)

        # Si no se proporciona contexto, obtenerlo
        if not context:
            context = get_market_context(symbol)

        if not context or "error" in context:
            return f"❌ Error: No se pudo obtener el contexto de mercado para {symbol}."

        # Si tenemos un assistant_id, usar la API de asistentes
        if assistant_id:
            return process_with_assistant(prompt, symbol, context, assistant_id)
        else:
            # Usar la API de Chat Completion directamente
            return process_with_chat_completion(prompt, symbol, context, api_key)

    except Exception as e:
        logger.error(f"Error procesando consulta: {str(e)}")
        return f"Error procesando consulta: {str(e)}"


def process_with_assistant(prompt, symbol, context, assistant_id):
    """Procesa el mensaje utilizando la API de Asistentes de OpenAI con manejo mejorado"""
    try:
        # Crear thread si no existe
        if "thread_id" not in st.session_state:
            thread = openai.beta.threads.create()
            st.session_state.thread_id = thread.id
            logger.info(f"Nuevo thread creado: {thread.id}")

        # Formatear contexto para el mensaje
        price = context.get("last_price", 0)
        change = context.get("change_percent", 0)
        vix_level = context.get("vix_level", "N/A")

        signals = context.get("signals", {})

        # Obtener señal general
        overall_signal = "NEUTRAL"
        if "overall" in signals:
            signal = signals["overall"]["signal"]
            if signal in ["compra", "compra_fuerte"]:
                overall_signal = "ALCISTA"
            elif signal in ["venta", "venta_fuerte"]:
                overall_signal = "BAJISTA"

        # Obtener señal de opciones
        option_signal = "NEUTRAL"
        if "options" in signals:
            option_signal = signals["options"]["direction"]

        # Incluir información de noticias si está disponible
        news_info = ""
        if "news" in context and context["news"]:
            news_info = "\nNoticias recientes:\n"
            for item in context["news"][:3]:  # Mostrar hasta 3 noticias
                news_info += (
                    f"- {item.get('date', 'N/A')}: {item.get('title', 'N/A')}\n"
                )

        # Incluir información de sentimiento si está disponible
        sentiment_info = ""
        if "news_sentiment" in context and context["news_sentiment"]:
            sentiment = context["news_sentiment"]
            sentiment_info = f"\nSentimiento: {sentiment.get('sentiment', 'neutral')} ({sentiment.get('score', 0.5)*100:.1f}%)\n"

        # Crear mensaje enriquecido con contexto
        context_prompt = f"""
        Consulta sobre {symbol} a ${price:.2f} ({'+' if change > 0 else ''}{change:.2f}%):

        Señales técnicas actuales:
        - Tendencia general: {overall_signal}
        - Señal de opciones: {option_signal}
        - VIX: {vix_level}
        {sentiment_info}
        {news_info}

        Pregunta del usuario: {prompt}
        """

        # Crear mensaje en el thread
        thread_messages = openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=context_prompt
        )

        # Ejecutar con herramientas
        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=assistant_id, tools=tools
        )

        # Monitorear la ejecución
        with st.spinner("Analizando mercado y generando respuesta..."):
            run_status = "in_progress"
            start_time = time.time()
            timeout = 40  # 40 segundos de timeout

            while run_status not in ["completed", "failed", "cancelled", "expired"]:
                # Verificar timeout
                if time.time() - start_time > timeout:
                    logger.warning(f"Timeout al procesar consulta para {symbol}")
                    return f"La consulta está tomando demasiado tiempo. Por favor, inténtalo de nuevo o formula tu pregunta de otra manera."

                # Recuperar estado actual
                run = openai.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id, run_id=run.id
                )
                run_status = run.status

                # Verificar estado de ejecución
                if run_status == "completed":
                    break
                elif run_status == "requires_action":
                    # Procesar llamadas a herramientas
                    try:
                        tool_outputs = process_tool_calls(
                            run.required_action.submit_tool_outputs.tool_calls, symbol
                        )

                        # Enviar resultados
                        run = openai.beta.threads.runs.submit_tool_outputs(
                            thread_id=st.session_state.thread_id,
                            run_id=run.id,
                            tool_outputs=tool_outputs,
                        )
                    except Exception as tool_error:
                        logger.error(
                            f"Error procesando herramientas: {str(tool_error)}"
                        )
                        # Continuar con la ejecución incluso si falla el procesamiento de herramientas
                        run_status = "failed"
                        break
                elif run_status in ["failed", "cancelled", "expired"]:
                    logger.error(
                        f"Ejecución fallida con estado: {run_status}, error: {getattr(run, 'error', 'Desconocido')}"
                    )
                    return f"Error en la ejecución: {run_status}"

                # Pequeña pausa para no sobrecargar la API
                time.sleep(0.8)

            # Si falló la ejecución después del timeout
            if run_status in ["failed", "cancelled", "expired"]:
                return f"Error en la ejecución: {run_status}"

            # Obtener mensajes actualizados
            try:
                messages = openai.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )

                # Encontrar respuesta del asistente
                for message in messages:
                    if message.run_id == run.id and message.role == "assistant":
                        # Extraer texto de la respuesta
                        return process_message_with_citations(message)

                return "No se pudo obtener una respuesta del asistente."
            except Exception as msg_error:
                logger.error(f"Error obteniendo mensajes: {str(msg_error)}")
                return f"Error obteniendo respuesta: {str(msg_error)}"

    except Exception as e:
        logger.error(f"Error en process_with_assistant: {str(e)}")
        # En caso de error, caer en el modo fallback
        return fallback_analyze_symbol(symbol, prompt)


def process_with_chat_completion(prompt, symbol, context, api_key):
    """Procesa el mensaje utilizando la API de Chat Completion de OpenAI"""
    try:
        # Formatear contexto para el mensaje
        price = context.get("last_price", 0)
        change = context.get("change_percent", 0)
        vix_level = context.get("vix_level", "N/A")

        signals = context.get("signals", {})
        support_resistance = context.get("support_resistance", {})

        # Extraer información de noticias y sentimiento si está disponible
        news = context.get("news", [])
        sentiment = context.get("news_sentiment", {})

        news_text = ""
        if news:
            news_text = "\nNoticias recientes:\n"
            for item in news[:3]:  # Limitar a 3 noticias
                news_text += f"- {item.get('date', '')}: {item.get('title', '')}\n"

        sentiment_text = ""
        if sentiment:
            sentiment_score = sentiment.get("score", 0.5) * 100
            sentiment_text = f"\nSentimiento: {sentiment.get('sentiment', 'neutral')} ({sentiment_score:.1f}%)\n"

        # Preparar contexto resumido para el sistema
        system_prompt = """
        Eres un especialista en trading y análisis técnico avanzado con más de 8 años de experiencia en trading institucional.
        Tu expertise incluye análisis técnico, estrategias de opciones, volatilidad, y gestión de riesgo.
        Proporciona análisis claros, concisos y profesionales basados en los datos de mercado actuales.

        Cuando analices activos, considera:
        1. Tendencias de precios y patrones
        2. Indicadores técnicos (RSI, MACD, medias móviles)
        3. Niveles de soporte y resistencia
        4. Volatilidad del mercado y condiciones generales
        5. Estrategias de opciones recomendadas
        6. Noticias recientes y su impacto en el precio
        7. Sentimiento del mercado

        No te limites a repetir las señales automáticas. Aporta tu análisis profesional, busca divergencias y patrones que los indicadores básicos podrían no capturar. Tu valor está en proporcionar una perspectiva única basada en tu experiencia.
        """

        # Preparar un contexto más detallado pero conciso para usar como mensaje
        context_message = f"""
        Contexto actual para {symbol}:
        - Precio: ${price:.2f} ({change:+.2f}%)
        - VIX: {vix_level}

        Señales técnicas:
        - Tendencia general: {signals.get('overall', {}).get('signal', 'N/A')}
        - Confianza: {signals.get('overall', {}).get('confidence', 'N/A')}
        - Recomendación opciones: {signals.get('options', {}).get('direction', 'N/A')}

        Principales niveles:
        - Resistencias: {', '.join([f"${r:.2f}" for r in support_resistance.get('resistances', [])[:2]])}
        - Soportes: {', '.join([f"${s:.2f}" for s in support_resistance.get('supports', [])[:2]])}
        
        {sentiment_text}
        {news_text}
        """

        # Crear mensajes para la API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_message},
            {"role": "user", "content": prompt},
        ]

        # Realizar llamada a la API con manejo de errores
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",  # Usar el modelo más avanzado
                messages=messages,
                temperature=0.7,  # Balancear creatividad y precisión
                max_tokens=1000,  # Respuesta detallada pero no excesiva
            )

            # Extraer la respuesta
            return response.choices[0].message.content

        except openai.error.AuthenticationError:
            logger.error("Error de autenticación con OpenAI API")
            return "Error: No se pudo autenticar con OpenAI. Por favor, verifica tu API key."

        except openai.error.RateLimitError:
            logger.error("Límite de tasa excedido en OpenAI API")
            return "Error: Se ha excedido el límite de solicitudes a OpenAI. Por favor, intenta más tarde."

        except openai.error.APIError as api_err:
            logger.error(f"Error en API de OpenAI: {str(api_err)}")
            return f"Error en el servicio de OpenAI: {str(api_err)}"

        except Exception as general_err:
            logger.error(f"Error general en OpenAI: {str(general_err)}")
            return "Error al procesar la solicitud. Por favor, intenta más tarde."

    except Exception as e:
        logger.error(f"Error en process_with_chat_completion: {str(e)}")
        # En caso de error, caer en el modo fallback
        return fallback_analyze_symbol(symbol, prompt)


def fallback_analyze_symbol(symbol, question=None):
    """Función de respaldo para analizar símbolos cuando OpenAI no está disponible"""
    try:
        context = get_market_context(symbol)
        if context and "error" not in context:
            # Extraer información relevante
            price = context.get("last_price", 0)
            change = context.get("change_percent", 0)
            signals = context.get("signals", {})

            # Determinar señal general
            overall_signal = "NEUTRAL"
            if "overall" in signals:
                signal = signals["overall"]["signal"]
                if signal in ["compra", "compra_fuerte"]:
                    overall_signal = "ALCISTA"
                elif signal in ["venta", "venta_fuerte"]:
                    overall_signal = "BAJISTA"

            # Determinar recomendación de opciones
            option_signal = "NEUTRAL"
            option_strategy = "N/A"
            if "options" in signals:
                option_signal = signals["options"]["direction"]
                option_strategy = signals["options"]["strategy"]

            # Analizar niveles clave
            support_resistance = context.get("support_resistance", {})

            # Construir respuesta básica (modo de respaldo)
            response = f"## Análisis de {symbol} a ${price:.2f} ({change:+.2f}%)\n\n"

            # Determinar una respuesta más personalizada basada en la pregunta si está disponible
            if question:
                question_lower = question.lower()

                if any(
                    term in question_lower
                    for term in ["análisis", "resumen", "general", "situación"]
                ):
                    response += f"### Análisis General\n\n"
                    response += f"El activo {symbol} muestra una tendencia **{overall_signal}** en este momento. "

                    if "trend" in signals:
                        trend = signals["trend"]
                        response += f"Los indicadores de tendencia muestran: "
                        response += f"SMA 20-50 {trend.get('sma_20_50', 'N/A')}, "
                        response += f"MACD {trend.get('macd', 'N/A')}, "
                        response += (
                            f"y está {trend.get('sma_200', 'N/A')} de su SMA 200.\n\n"
                        )

                    # Incluir información de noticias y sentimiento si está disponible
                    if "news_sentiment" in context:
                        sentiment = context["news_sentiment"]
                        response += f"El sentimiento de mercado es **{sentiment.get('sentiment', 'neutral')}** con un score de {sentiment.get('score', 0.5)*100:.1f}%.\n\n"

                    response += f"### Recomendación de Trading\n\n"
                    if overall_signal == "ALCISTA":
                        response += f"Se recomienda considerar posiciones **LONG** con gestión adecuada del riesgo. "
                        response += f"Para opciones, la estrategia sugerida es **{option_signal}** con enfoque en {option_strategy}.\n\n"
                    elif overall_signal == "BAJISTA":
                        response += f"Se recomienda considerar posiciones **SHORT** con gestión adecuada del riesgo. "
                        response += f"Para opciones, la estrategia sugerida es **{option_signal}** con enfoque en {option_strategy}.\n\n"
                    else:
                        response += f"Se recomienda **NEUTRAL/CAUTELA** hasta una señal más clara. "
                        response += f"Para opciones, considerar estrategias de volatilidad no direccionales.\n\n"

                elif any(
                    term in question_lower
                    for term in ["nivel", "soporte", "resistencia", "precio", "target"]
                ):
                    response += f"### Niveles Clave para {symbol}\n\n"

                    if (
                        "resistances" in support_resistance
                        and support_resistance["resistances"]
                    ):
                        resistances = sorted(support_resistance["resistances"])
                        response += "**Resistencias clave:**\n"
                        for i, level in enumerate(resistances[:3]):
                            distance = ((level / price) - 1) * 100
                            response += f"- R{i+1}: ${level:.2f} ({distance:+.2f}% desde precio actual)\n"

                    response += "\n"

                    if (
                        "supports" in support_resistance
                        and support_resistance["supports"]
                    ):
                        supports = sorted(support_resistance["supports"], reverse=True)
                        response += "**Soportes clave:**\n"
                        for i, level in enumerate(supports[:3]):
                            distance = ((level / price) - 1) * 100
                            response += f"- S{i+1}: ${level:.2f} ({distance:+.2f}% desde precio actual)\n"

                    response += "\n"
                    response += f"Estos niveles son significativos para planificar entradas, salidas y gestión de riesgo. "
                    response += f"Considerar stop loss por debajo del soporte más cercano para posiciones largas, "
                    response += f"o por encima de la resistencia más cercana para posiciones cortas."

                elif any(
                    term in question_lower
                    for term in ["opcion", "opciones", "call", "put", "derivado"]
                ):
                    response += f"### Análisis de Opciones para {symbol}\n\n"

                    if "options" in signals:
                        options = signals["options"]
                        response += f"**Dirección recomendada: {options.get('direction', 'N/A')}**\n"
                        response += (
                            f"**Estrategia: {options.get('strategy', 'N/A')}**\n"
                        )
                        response += (
                            f"**Confianza: {options.get('confidence', 'N/A')}**\n"
                        )
                        response += (
                            f"**Timeframe: {options.get('timeframe', 'N/A')}**\n\n"
                        )

                    if "options_params" in context:
                        params = context["options_params"]
                        response += "**Parámetros recomendados:**\n"
                        for param, value in params.items():
                            response += f"- {param}: {value}\n"

                    if "volatility_adjustments" in context:
                        vix = context.get("vix_level", 0)
                        vol_state = (
                            "ALTA" if vix > 25 else "BAJA" if vix < 15 else "NORMAL"
                        )

                        response += f"\nCon VIX en {vix:.2f} (Volatilidad {vol_state}), se recomienda:\n"

                        if vix > 25:
                            response += (
                                "- Considerar spreads en lugar de opciones simples\n"
                            )
                            response += "- Reducir el tamaño de posición\n"
                            response += "- Strike más alejado para mayor seguridad\n"
                        elif vix < 15:
                            response += "- Estrategias direccionales simples\n"
                            response += "- Strike cercano al precio actual\n"
                            response += "- Considerar vencimientos más largos\n"
                        else:
                            response += "- Parámetros estándar\n"
                            response += (
                                "- Balance entre riesgo y recompensa tradicional\n"
                            )

                elif any(
                    term in question_lower
                    for term in ["rsi", "momentum", "indicador", "técnico", "macd"]
                ):
                    response += f"### Indicadores Técnicos para {symbol}\n\n"

                    if "momentum" in signals:
                        momentum = signals["momentum"]
                        rsi = momentum.get("rsi", 0)
                        condition = momentum.get("rsi_condition", "N/A")

                        response += f"**RSI:** {rsi:.1f} ({condition})\n"
                        response += (
                            f"**Tendencia RSI:** {momentum.get('rsi_trend', 'N/A')}\n"
                        )

                        if "stoch_k" in momentum and "stoch_d" in momentum:
                            response += f"**Estocástico:** %K={momentum['stoch_k']:.1f}, %D={momentum['stoch_d']:.1f}\n"

                    if "trend" in signals:
                        trend = signals["trend"]
                        response += f"\n**Indicadores de Tendencia:**\n"
                        response += f"- SMA 20-50: {trend.get('sma_20_50', 'N/A')}\n"
                        response += f"- MACD: {trend.get('macd', 'N/A')}\n"
                        response += f"- EMA Trend: {trend.get('ema_trend', 'N/A')}\n"
                        response += (
                            f"- Posición vs SMA 200: {trend.get('sma_200', 'N/A')}\n"
                        )

                    if "volatility" in signals:
                        volatility = signals["volatility"]
                        response += f"\n**Indicadores de Volatilidad:**\n"
                        response += f"- BB Width: {volatility.get('bb_width', 0):.3f}\n"
                        response += f"- ATR: {volatility.get('atr', 0):.3f}\n"
                        response += f"- Posición del precio: {volatility.get('price_position', 'N/A')}\n"
                        response += f"- Estado de volatilidad: {volatility.get('volatility_state', 'N/A')}\n"

                elif any(
                    term in question_lower
                    for term in ["noticias", "noticia", "sentimiento", "news"]
                ):
                    response += (
                        f"### Análisis de Noticias y Sentimiento para {symbol}\n\n"
                    )

                    # Añadir información de sentimiento si está disponible
                    if "news_sentiment" in context:
                        sentiment = context["news_sentiment"]
                        response += f"**Sentimiento general:** {sentiment.get('sentiment', 'neutral')}\n"
                        response += f"**Score de sentimiento:** {sentiment.get('score', 0.5)*100:.1f}%\n"
                        response += f"**Menciones positivas:** {sentiment.get('positive_mentions', 0)}\n"
                        response += f"**Menciones negativas:** {sentiment.get('negative_mentions', 0)}\n\n"

                    # Añadir noticias si están disponibles
                    if "news" in context and context["news"]:
                        news = context["news"]
                        response += "**Noticias recientes:**\n\n"
                        for item in news[:5]:  # Limitar a 5 noticias
                            response += (
                                f"- {item.get('date', '')}: {item.get('title', '')}\n"
                            )
                    else:
                        response += (
                            "No se encontraron noticias recientes para este activo.\n"
                        )

                elif any(
                    term in question_lower
                    for term in ["timeframe", "plazo", "corto", "largo", "medio"]
                ):
                    response += f"### Análisis Multi-Timeframe para {symbol}\n\n"

                    # Donde muestras la alineación de timeframes
                    if "multi_timeframe" in context:
                        multi_tf = context["multi_timeframe"]
                        if "consolidated" in multi_tf:
                            cons = multi_tf["consolidated"]
                            response += f"**Señal consolidada: {cons.get('signal', 'N/A').upper()}**\n"
                            response += (
                                f"**Confianza: {cons.get('confidence', 'N/A')}**\n"
                            )
                            response += f"**Alineación de timeframes: {cons.get('timeframe_alignment', 'N/A')}**\n"
                            response += f"**Recomendación: {cons.get('options_recommendation', 'N/A')}**\n\n"

                            # Añadir esta sección para mostrar todos los timeframes
                            response += "**Análisis por timeframe:**\n\n"

                            for tf, analysis in multi_tf.items():
                                if (
                                    tf != "consolidated"
                                    and isinstance(analysis, dict)
                                    and "overall" in analysis
                                ):
                                    response += (
                                        f"**{tf}:** {analysis['overall']['signal']} "
                                    )
                                    response += f"({analysis['overall']['confidence']})"
                                    if "options" in analysis:
                                        response += f" → Opciones: {analysis['options']['direction']}\n"
                                    else:
                                        response += "\n"
                    else:
                        response += "Información multi-timeframe no disponible para este activo."

                else:
                    # Si la pregunta no tiene términos específicos, dar un resumen general
                    response += f"### Análisis Técnico {symbol}\n\n"
                    response += f"El análisis actual muestra una tendencia **{overall_signal}** con una señal de opciones **{option_signal}**.\n\n"

                    if "momentum" in signals:
                        momentum = signals["momentum"]
                        rsi = momentum.get("rsi", 0)
                        condition = momentum.get("rsi_condition", "N/A")
                        response += f"**RSI:** {rsi:.1f} ({condition})\n"

                    if (
                        "supports" in support_resistance
                        and "resistances" in support_resistance
                    ):
                        supports = sorted(support_resistance["supports"], reverse=True)[
                            :1
                        ]
                        resistances = sorted(support_resistance["resistances"])[:1]

                        if supports:
                            support = supports[0]
                            support_dist = ((support / price) - 1) * 100
                            response += f"**Soporte clave:** ${support:.2f} ({support_dist:+.2f}%)\n"

                        if resistances:
                            resistance = resistances[0]
                            resistance_dist = ((resistance / price) - 1) * 100
                            response += f"**Resistencia clave:** ${resistance:.2f} ({resistance_dist:+.2f}%)\n"

                    # Incluir información de noticias y sentimiento si está disponible
                    if "news_sentiment" in context:
                        sentiment = context["news_sentiment"]
                        response += f"\n**Sentimiento de mercado:** {sentiment.get('sentiment', 'neutral')} ({sentiment.get('score', 0.5)*100:.1f}%)\n"

                    response += f"\nPara información específica, puedes preguntar sobre tendencia, opciones, RSI, volatilidad, niveles de soporte/resistencia, o noticias recientes."
            else:
                # Si no hay pregunta, dar un resumen estándar
                response += f"### Señal General: {overall_signal}\n"
                if "overall" in signals:
                    confidence = signals["overall"]["confidence"]
                    response += f"Confianza: {confidence}\n\n"

                response += f"### Recomendación de Opciones: {option_signal}\n"
                response += f"Estrategia: {option_strategy}\n\n"

                response += "### Niveles Clave\n"
                if (
                    "resistances" in support_resistance
                    and support_resistance["resistances"]
                ):
                    resistances = sorted(support_resistance["resistances"])[:2]
                    response += "**Resistencias:**\n"
                    for i, level in enumerate(resistances):
                        distance = ((level / price) - 1) * 100
                        response += f"- R{i+1}: ${level:.2f} ({distance:+.2f}%)\n"

                if "supports" in support_resistance and support_resistance["supports"]:
                    supports = sorted(support_resistance["supports"], reverse=True)[:2]
                    response += "**Soportes:**\n"
                    for i, level in enumerate(supports):
                        distance = ((level / price) - 1) * 100
                        response += f"- S{i+1}: ${level:.2f} ({distance:+.2f}%)\n"

                # Incluir información de noticias y sentimiento si está disponible
                if "news_sentiment" in context:
                    sentiment = context["news_sentiment"]
                    response += f"\n### Sentimiento de Mercado\n"
                    response += (
                        f"**Sentimiento:** {sentiment.get('sentiment', 'neutral')}\n"
                    )
                    response += f"**Score:** {sentiment.get('score', 0.5)*100:.1f}%\n"

            return response

        else:
            # Mensaje predeterminado para símbolos que no tienen datos disponibles
            company_info = get_company_info(symbol)
            name = company_info.get("name", symbol)
            sector = company_info.get("sector", "N/A")

            error_msg = (
                context.get("error", "Error desconocido")
                if context
                else "No hay datos disponibles"
            )

            response = f"""
            ## Información sobre {name} ({symbol})

            **Sector:** {sector}

            Lo siento, no se pudieron obtener datos actuales de mercado para {symbol}. {error_msg}

            Algunas posibles razones:

            - El símbolo puede no estar disponible en nuestras fuentes de datos
            - Puede haber una interrupción temporal en los servicios de datos
            - El mercado puede estar cerrado actualmente

            Recomendaciones:

            - Intenta con otro símbolo
            - Verifica que el símbolo esté escrito correctamente
            - Intenta nuevamente más tarde
            """
            return response

    except Exception as e:
        logger.error(f"Error analizando símbolo {symbol}: {str(e)}")
        return f"❌ Error analizando {symbol}: {str(e)}"


# =================================================
# FUNCIONES DE SESIÓN
# =================================================


def initialize_session_state():
    """Inicializa el estado de la sesión"""
    # Estado para OpenAI
    if "openai_configured" not in st.session_state:
        api_key, assistant_id = setup_openai()
        st.session_state.openai_api_key = api_key
        st.session_state.assistant_id = assistant_id
        st.session_state.openai_configured = bool(api_key)

    # Estado para chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Estado para thread de OpenAI
    if "thread_id" not in st.session_state and st.session_state.get(
        "openai_configured"
    ):
        try:
            thread = openai.beta.threads.create()
            st.session_state.thread_id = thread.id
        except Exception as e:
            logger.error(f"Error creando thread: {str(e)}")
            st.session_state.thread_id = None

    # Estado para activos seleccionados
    if "current_symbol" not in st.session_state:
        st.session_state.current_symbol = "SPY"

    if "current_timeframe" not in st.session_state:
        st.session_state.current_timeframe = "1d"

    # Estado para sesión de usuario
    if "session_start" not in st.session_state:
        st.session_state.session_start = datetime.now()

    # Comprobar APIs una sola vez al iniciar
    if "show_system_status" not in st.session_state:
        st.session_state.show_system_status = True

    # Estado para última consulta al experto
    if "last_expert_analysis" not in st.session_state:
        st.session_state.last_expert_analysis = {}

    # Estado para gráfico técnico activo
    if "active_chart" not in st.session_state:
        st.session_state.active_chart = None

    # Inicializar estado para el scanner de mercado
    if "data_cache" not in st.session_state:
        st.session_state.data_cache = DataCache()

    if "analyzer" not in st.session_state:
        st.session_state.analyzer = TechnicalAnalyzer(_data_cache)

    if "scanner" not in st.session_state:
        st.session_state.scanner = MarketScanner(SYMBOLS, st.session_state.analyzer)

    if "last_scan_time" not in st.session_state:
        st.session_state.last_scan_time = datetime.now() - timedelta(hours=1)

    if "last_scan_sectors" not in st.session_state:
        st.session_state.last_scan_sectors = ["Índices", "Tecnología"]

    if "scan_results" not in st.session_state:
        st.session_state.scan_results = pd.DataFrame()


def render_sidebar():
    """Renderiza el panel lateral con información profesional y estado del mercado"""
    with st.sidebar:
        st.markdown(
            '<h2 class="sidebar-section-title">🧑‍💻 Trading Specialist Pro</h2>',
            unsafe_allow_html=True,
        )

        # Perfil profesional en un contenedor con estilo
        st.markdown(
            """
            <div class="sidebar-profile">
                <h2>Perfil Profesional</h2>
                <p>Analista técnico y estratega de mercados con especialización en derivados financieros y más de 8 años de experiencia en trading institucional.</p>
                <p>Experto en estrategias cuantitativas, análisis de volatilidad y gestión de riesgo algorítmica.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Áreas de especialización colapsables
        with st.expander("📊 Áreas de Especialización"):
            st.markdown(
                """
                - Estrategias avanzadas de opciones y volatilidad
                - Trading sistemático y algorítmico
                - Análisis técnico y cuantitativo
                - Gestión de riesgo dinámica
                - Market Making y liquidez

                **Competencias Técnicas:**
                - Modelado de volatilidad y superficies
                - Análisis de flujo de opciones y order flow
                - Desarrollo de indicadores propietarios
                - Machine Learning aplicado a trading
                - Análisis de microestructura de mercado
                """
            )

        st.markdown('<hr style="margin: 1.5rem 0;">', unsafe_allow_html=True)

        # Información de mercado
        st.markdown(
            '<div class="sidebar-section-title">📊 Estado del Mercado</div>',
            unsafe_allow_html=True,
        )

        try:
            # Obtener VIX
            vix_level = get_vix_level()

            # Determinar sesión de mercado
            now = datetime.now()
            hour = now.hour
            weekday = now.weekday()

            if weekday >= 5:  # Fin de semana
                session = "CERRADO"
                session_color = "red"
            elif 4 <= hour < 9:
                session = "PRE-MARKET"
                session_color = "orange"
            elif 9 <= hour < 16:
                session = "REGULAR"
                session_color = "green"
            elif 16 <= hour < 20:
                session = "AFTER-HOURS"
                session_color = "blue"
            else:
                session = "CERRADO"
                session_color = "red"

            # Mostrar información en dos columnas
            col1, col2 = st.columns(2)

            with col1:
                # Determinar delta y color basado en nivel VIX
                if vix_level > 25:
                    vix_status = "Volatilidad Alta"
                    delta_color = "inverse"
                elif vix_level < 15:
                    vix_status = "Volatilidad Baja"
                    delta_color = "normal"
                else:
                    vix_status = "Normal"
                    delta_color = "off"

                st.metric(
                    "VIX",
                    f"{vix_level:.2f}",
                    delta=vix_status,
                    delta_color=delta_color,
                )

            with col2:
                # Crear métrica personalizada para la sesión con color
                st.markdown(
                    f"""
                    <div style="padding: 0.5rem; border-radius: 0.5rem; background-color: rgba(0,0,0,0.05);">
                        <div style="font-size: 0.875rem; color: #6c757d;">Sesión</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: {session_color};">{session}</div>
                        <div style="font-size: 0.75rem; color: #6c757d;">{now.strftime("%H:%M:%S")}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Mercados principales como referencia
            try:
                spy_data = fetch_market_data("SPY", "2d")
                qqq_data = fetch_market_data("QQQ", "2d")

                if not spy_data.empty and not qqq_data.empty:
                    spy_change = (
                        (spy_data["Close"].iloc[-1] / spy_data["Close"].iloc[-2]) - 1
                    ) * 100
                    qqq_change = (
                        (qqq_data["Close"].iloc[-1] / qqq_data["Close"].iloc[-2]) - 1
                    ) * 100

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "S&P 500",
                            f"${spy_data['Close'].iloc[-1]:.2f}",
                            f"{spy_change:.2f}%",
                            delta_color="normal" if spy_change >= 0 else "inverse",
                        )
                    with col2:
                        st.metric(
                            "NASDAQ",
                            f"${qqq_data['Close'].iloc[-1]:.2f}",
                            f"{qqq_change:.2f}%",
                            delta_color="normal" if qqq_change >= 0 else "inverse",
                        )

                    # Mostrar gráfico mini de SPY
                    with st.expander("📈 Vista rápida S&P 500"):
                        # Crear un gráfico simplificado
                        fig = go.Figure()
                        fig.add_trace(
                            go.Scatter(
                                x=(
                                    spy_data.index
                                    if isinstance(spy_data.index, pd.DatetimeIndex)
                                    else range(len(spy_data))
                                ),
                                y=spy_data["Close"],
                                line=dict(color="#1E88E5", width=2),
                                name="SPY",
                            )
                        )

                        # Configurar layout minimalista
                        fig.update_layout(
                            height=200,
                            margin=dict(l=10, r=10, t=10, b=10),
                            showlegend=False,
                            xaxis=dict(
                                showgrid=False, zeroline=False, showticklabels=False
                            ),
                            yaxis=dict(
                                showgrid=True, zeroline=False, showticklabels=True
                            ),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            config={"displayModeBar": False},
                        )

            except Exception as e:
                st.warning("No se pudieron cargar datos de referencia")

        except Exception as ex:
            st.warning("No se pudo obtener información de mercado")

        st.markdown('<hr style="margin: 1.5rem 0;">', unsafe_allow_html=True)

        # Acciones rápidas
        st.markdown(
            '<div class="sidebar-section-title">⚙️ Acciones</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "🔄 Limpiar Caché",
                help="Limpiar caché de datos para obtener información actualizada",
                use_container_width=True,
            ):
                cleared = clear_cache()
                st.success(f"Caché limpiado: {cleared} entradas eliminadas")
                time.sleep(1)
                st.rerun()

            if st.button(
                "🖥️ Estado Sistema",
                help="Mostrar estado del sistema, APIs y librerías",
                use_container_width=True,
            ):
                st.session_state.show_system_status = True
                st.rerun()

        with col2:
            if st.button(
                "🧹 Limpiar Chat",
                help="Borrar historial de chat",
                use_container_width=True,
            ):
                st.session_state.messages = []

                # Crear nuevo thread si OpenAI está disponible
                if st.session_state.get("openai_configured"):
                    try:
                        thread = openai.beta.threads.create()
                        st.session_state.thread_id = thread.id
                    except:
                        pass

                st.rerun()

            # Botón de cierre de sesión
            if st.button(
                "🔒 Cerrar Sesión",
                help="Cerrar sesión actual",
                use_container_width=True,
            ):
                clear_session()
                st.rerun()

        # Mostrar estadísticas de caché
        stats = _data_cache.get_stats()

        st.markdown(
            '<div class="sidebar-section-title">💾 Caché</div>', unsafe_allow_html=True
        )
        st.text(f"Entradas: {stats['entradas']}")
        st.text(f"Hit rate: {stats['hit_rate']}")
        st.text(f"Hits/Misses: {stats['hits']}/{stats['misses']}")

        # Disclaimer
        st.markdown('<hr style="margin: 1.5rem 0;">', unsafe_allow_html=True)
        st.caption(
            """
            **⚠️ Disclaimer:** Este sistema proporciona análisis técnico avanzado
            para fines informativos únicamente. No constituye asesoramiento financiero
            ni garantiza resultados. El trading conlleva riesgo significativo de pérdida.
            """
        )

        # Información de sesión
        st.markdown('<hr style="margin: 1rem 0 0.5rem 0;">', unsafe_allow_html=True)
        if "session_start" in st.session_state:
            session_duration = datetime.now() - st.session_state.session_start
            hours, remainder = divmod(session_duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Mostrar duración de sesión con formato mejorado
            st.markdown(
                f"""
                <div style="font-size: 0.75rem; color: #6c757d; display: flex; justify-content: space-between;">
                    <span>Sesión activa: {hours}h {minutes}m</span>
                    <span>v2.0.3</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Mostrar estado de OpenAI
            openai_status = (
                "✅ OpenAI conectado"
                if st.session_state.get("openai_configured")
                else "⚠️ OpenAI no configurado - Chat en modo básico"
            )
            st.markdown(
                f"""
                <div style="font-size: 0.75rem; color: #6c757d; margin-top: 0.25rem;">
                    {openai_status}
                </div>
                """,
                unsafe_allow_html=True,
            )


# =================================================
# FUNCIONES DE ANÁLISIS DE MERCADO
# =================================================


def analyze_market_data(symbol, timeframe="1d", period="6mo", indicators=True):
    """
    Analiza datos de mercado con indicadores técnicos avanzados
    y manejo robusto de errores
    """
    try:
        # Obtener datos de mercado con manejo mejorado de errores
        try:
            data = fetch_market_data(symbol, period, interval=timeframe)
            logger.info(
                f"Datos obtenidos para {symbol}: {data.shape if isinstance(data, pd.DataFrame) else 'No data'}"
            )

            if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                logger.warning(f"No se pudieron obtener datos para {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            return None

        # Añadir indicadores técnicos si se solicita
        if indicators and data is not None and not data.empty:
            try:
                # Calcular RSI
                delta = data["Close"].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)

                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()

                rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
                data["RSI"] = 100 - (100 / (1 + rs))

                # Calcular medias móviles
                data["SMA_20"] = data["Close"].rolling(window=20).mean()
                data["SMA_50"] = data["Close"].rolling(window=50).mean()
                data["SMA_200"] = data["Close"].rolling(window=200).mean()

                # Calcular MACD
                ema12 = data["Close"].ewm(span=12, adjust=False).mean()
                ema26 = data["Close"].ewm(span=26, adjust=False).mean()
                data["MACD"] = ema12 - ema26
                data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

                # Calcular Bandas de Bollinger
                data["BB_MA20"] = data["SMA_20"]  # Usar SMA20 como línea media
                rolling_std = data["Close"].rolling(window=20).std()
                data["BB_Upper"] = data["BB_MA20"] + (2 * rolling_std)
                data["BB_Lower"] = data["BB_MA20"] - (2 * rolling_std)
                data["BB_Width"] = (data["BB_Upper"] - data["BB_Lower"]) / data[
                    "BB_MA20"
                ]

                # Calcular ATR
                high_low = data["High"] - data["Low"]
                high_close = (data["High"] - data["Close"].shift()).abs()
                low_close = (data["Low"] - data["Close"].shift()).abs()

                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                data["ATR"] = tr.rolling(window=14).mean()

                # Detectar patrones si es posible
                try:
                    # Patrones de vela (solo en los últimos 20 períodos para eficiencia)
                    candle_patterns = detect_candle_patterns(data.tail(30))

                    # Añadir columnas para patrones detectados
                    for pattern in candle_patterns:
                        idx = pattern.get("idx", -1)
                        if 0 <= idx < len(data):
                            pattern_name = pattern.get("pattern", "unknown")
                            pattern_type = pattern.get("type", "neutral")

                            # Crear columna para el patrón si no existe
                            col_name = f"Pattern_{pattern_name}"
                            if col_name not in data.columns:
                                data[col_name] = None

                            # Marcar el patrón en el índice correspondiente
                            data.iloc[idx, data.columns.get_loc(col_name)] = (
                                pattern_type
                            )
                except Exception as e:
                    logger.warning(
                        f"No se pudieron detectar patrones de velas para {symbol}: {str(e)}"
                    )
            except Exception as e:
                logger.error(f"Error calculando indicadores para {symbol}: {str(e)}")
                # Al menos retornar los datos sin indicadores
                return data

        return data
    except Exception as e:
        logger.error(
            f"Error general analizando datos de mercado para {symbol}: {str(e)}"
        )
        return None


def render_enhanced_dashboard(symbol, timeframe="1d"):
    """Renderiza un dashboard mejorado con análisis técnico avanzado y manejo de fallos"""
    # Obtener información del activo (nombre completo, sector, etc.)
    company_info = get_company_info(symbol)
    company_name = company_info.get("name", symbol)

    # Intentar obtener contexto de mercado primero
    context = get_market_context(symbol)
    price = None
    change = None

    if context and "error" not in context:
        price = context.get("last_price")
        change = context.get("change_percent")

    # Mostrar la información del activo, incluso si no hay datos de mercado
    display_asset_info(symbol, price, change)

    # Obtener datos y analizarlos
    data = analyze_market_data(symbol, timeframe)

    # Si no tenemos datos, mostrar un mensaje y terminar
    if data is None or (isinstance(data, pd.DataFrame) and data.empty):
        st.warning(
            f"No se pudieron obtener datos para {symbol} en timeframe {timeframe}"
        )

        # Mostrar información alternativa para que el usuario tenga contexto
        st.markdown(
            f"""
            <div class="info-message">
                <h3>Información</h3>
                <p>No se pudieron cargar datos de mercado para {company_name} ({symbol}) en el timeframe {timeframe}.</p>
                <p>Esto puede deberse a diferentes razones:</p>
                <ul>
                    <li>El símbolo puede no estar disponible en nuestras fuentes de datos</li>
                    <li>El mercado puede estar cerrado actualmente</li>
                    <li>Puede haber un problema temporal con los servicios de datos</li>
                </ul>
                <p>Intenta con otro símbolo o timeframe, o vuelve a intentarlo más tarde.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # A pesar de no tener datos, mostramos el panel de chat para que el usuario pueda hacer consultas
        return

    # Si llegamos aquí, tenemos datos para mostrar

    # Crear pestañas para diferentes tipos de análisis
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📊 Análisis Técnico",
            "🎯 Opciones",
            "⚙️ Multi-Timeframe",
            "🧠 Análisis Experto",
            "📰 Noticias y Sentimiento",
            "🔍 Scanner",
        ]
    )

    with tab1:
        # Mostrar resumen técnico
        display_technical_summary(symbol, data)

        # Mostrar gráfico técnico
        st.markdown(f"### 📈 Gráfico Técnico de {symbol}")
        fig = create_technical_chart(data, symbol)
        if fig:
            st.plotly_chart(
                fig, use_container_width=True, height=800
            )  # Especificar altura
            # Guardar el gráfico activo en el estado
            st.session_state.active_chart = fig
        else:
            st.warning("No se pudo crear el gráfico técnico")

        # Mostrar detalles de indicadores
        with st.expander("📊 Detalles de Indicadores"):
            if data is not None and not data.empty and len(data) > 0:
                try:
                    last_row = data.iloc[-1]

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("#### Momentum")
                        # Verificar que RSI existe y no es None antes de formatear
                        if "RSI" in data.columns and last_row["RSI"] is not None:
                            rsi = last_row["RSI"]
                            rsi_status = (
                                "Sobrecompra"
                                if rsi > 70
                                else "Sobreventa" if rsi < 30 else "Neutral"
                            )
                            st.metric("RSI", f"{rsi:.2f}", rsi_status)
                        else:
                            st.metric("RSI", "N/A", "Sin datos")

                        # Manejar valores nulos para estocástico
                        if (
                            "STOCH_K" in data.columns
                            and "STOCH_D" in data.columns
                            and last_row["STOCH_K"] is not None
                            and last_row["STOCH_D"] is not None
                        ):
                            st.metric(
                                "Estocástico",
                                f"%K:{last_row['STOCH_K']:.2f} %D:{last_row['STOCH_D']:.2f}",
                            )
                        else:
                            st.metric("Estocástico", "N/A")

                        # Manejar valores nulos para CCI
                        if "CCI" in data.columns and last_row["CCI"] is not None:
                            st.metric("CCI", f"{last_row['CCI']:.2f}")
                        else:
                            st.metric("CCI", "N/A")

                    with col2:
                        st.markdown("#### Tendencia")
                        # Verificar valores nulos para SMA
                        if (
                            "SMA_20" in data.columns
                            and "SMA_50" in data.columns
                            and last_row["SMA_20"] is not None
                            and last_row["SMA_50"] is not None
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
                            and last_row["MACD"] is not None
                            and last_row["MACD_Signal"] is not None
                        ):
                            macd = last_row["MACD"]
                            macd_signal = last_row["MACD_Signal"]
                            macd_hist = macd - macd_signal
                            st.metric(
                                "MACD Hist",
                                f"{macd_hist:.3f}",
                                "Alcista" if macd_hist > 0 else "Bajista",
                            )
                        else:
                            st.metric("MACD Hist", "N/A")

                        # Verificar valores nulos para SMA_200
                        if (
                            "SMA_200" in data.columns
                            and "Close" in data.columns
                            and last_row["SMA_200"] is not None
                            and last_row["Close"] is not None
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
                            st.metric("Precio vs SMA200", "N/A")

                    with col3:
                        st.markdown("#### Volatilidad")
                        # Verificar valores nulos para BB_Width
                        if (
                            "BB_Width" in data.columns
                            and last_row["BB_Width"] is not None
                        ):
                            st.metric("Ancho BB", f"{last_row['BB_Width']:.3f}")
                        else:
                            st.metric("Ancho BB", "N/A")

                        # Verificar valores nulos para ATR
                        if "ATR" in data.columns and last_row["ATR"] is not None:
                            st.metric("ATR", f"{last_row['ATR']:.3f}")
                        else:
                            st.metric("ATR", "N/A")

                        # Verificar valores nulos para ATR como porcentaje
                        if (
                            "ATR" in data.columns
                            and "Close" in data.columns
                            and last_row["ATR"] is not None
                            and last_row["Close"] is not None
                            and last_row["Close"] > 0
                        ):
                            atr_pct = (last_row["ATR"] / last_row["Close"]) * 100
                            st.metric("ATR %", f"{atr_pct:.2f}%")
                        else:
                            st.metric("ATR %", "N/A")
                except Exception as e:
                    logger.error(f"Error mostrando detalles de indicadores: {str(e)}")
                    st.error(f"Error al mostrar indicadores técnicos: {str(e)}")
            else:
                st.info("No hay datos disponibles para mostrar indicadores técnicos.")

    # Código para la pestaña de opciones
    with tab2:
        # Obtener datos de opciones
        option_data = (
            context.get("options", {}) if context and "error" not in context else {}
        )
        option_signal = (
            context.get("signals", {}).get("options", {})
            if context and "error" not in context
            else {}
        )

        # Combinar datos
        combined_options = {
            "recommendation": option_signal.get("direction", "NEUTRAL"),
            "confidence": option_signal.get("confidence", "baja"),
            "strategy": option_signal.get("strategy", "N/A"),
            "implied_volatility": option_data.get("implied_volatility", 0) * 100,
            "historical_volatility": option_data.get("historical_volatility", 0) * 100,
        }

        # Mostrar análisis de opciones
        display_options_analysis(symbol, combined_options)

        try:
            # Mostrar superficie de volatilidad
            st.markdown("### 📊 Superficie de Volatilidad")

            # Datos de ejemplo para la superficie de volatilidad
            if data is not None and not data.empty:
                # Asegurarse de que last_row existe y tiene Close
                last_row = data.iloc[-1] if not data.empty else None
                price = (
                    last_row["Close"]
                    if last_row is not None and "Close" in last_row
                    else 100
                )
            else:
                price = 100  # Valor por defecto si no hay datos

            strikes = np.linspace(price * 0.8, price * 1.2, 11)
            expirations = [30, 60, 90, 180, 270]

            # Modelar la superficie con un sesgo ligeramente negativo (volatility skew)
            vol_surface = []
            for days in expirations:
                row = []
                for strike in strikes:
                    # Modelar skew (mayor volatilidad para puts, menor para calls)
                    moneyness = strike / price
                    skew = -0.2 * (1 - moneyness)
                    # Modelar term structure (mayor volatilidad para vencimientos largos)
                    term_effect = 0.02 * np.log(days / 30)
                    # Volatilidad base
                    base_vol = combined_options.get("implied_volatility", 20)
                    # Volatilidad final
                    vol = max(5, base_vol / 100 + skew + term_effect) * 100
                    row.append(vol)
                vol_surface.append(row)

            # Crear figura 3D
            fig = go.Figure(
                data=[
                    go.Surface(
                        z=vol_surface,
                        x=strikes,
                        y=expirations,
                        colorscale="Viridis",
                        colorbar=dict(title="Vol. Implícita (%)"),
                    )
                ]
            )

            fig.update_layout(
                title="Superficie de Volatilidad",
                scene=dict(
                    xaxis_title="Strike",
                    yaxis_title="Días a vencimiento",
                    zaxis_title="Volatilidad Implícita (%)",
                ),
                height=600,
                margin=dict(l=10, r=10, b=10, t=30),
            )

            st.plotly_chart(
                fig, use_container_width=True, height=800
            )  # Especificar altura
        except Exception as e:
            logger.error(f"Error creando superficie de volatilidad: {str(e)}")
            st.warning(f"No se pudo generar la superficie de volatilidad: {str(e)}")

        # Mostrar estrategias de opciones
        st.markdown("### 🎯 Estrategias Recomendadas")

        # Determinar qué estrategias mostrar según la señal
        recommendation = combined_options.get("recommendation", "NEUTRAL")

        if recommendation == "CALL":
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    """
                    <div class="strategy-card">
                        <h4>🔵 Call Debit Spread</h4>
                        <p><strong>Objetivo:</strong> Beneficiarse de un movimiento alcista moderado con riesgo limitado.</p>
                        <p><strong>Implementación:</strong> Comprar un call ATM y vender un call OTM con el mismo vencimiento.</p>
                        <p><strong>Riesgo Máximo:</strong> Limitado a la prima neta pagada.</p>
                        <p><strong>Recompensa Máxima:</strong> Diferencia entre strikes menos prima neta.</p>
                        <p><strong>Volatilidad Ideal:</strong> Baja a moderada.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    """
                    <div class="strategy-card">
                        <h4>🔵 Bull Call Ladder</h4>
                        <p><strong>Objetivo:</strong> Posición alcista agresiva con protección contra movimientos muy fuertes.</p>
                        <p><strong>Implementación:</strong> Comprar un call ITM, vender un call ATM y vender otro call muy OTM.</p>
                        <p><strong>Riesgo Máximo:</strong> Diferencia entre strikes menos primas recibidas.</p>
                        <p><strong>Recompensa Máxima:</strong> Ilimitada en ciertos rangos de precio.</p>
                        <p><strong>Volatilidad Ideal:</strong> Alta.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        elif recommendation == "PUT":
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    """
                    <div class="strategy-card">
                        <h4>🔴 Put Debit Spread</h4>
                        <p><strong>Objetivo:</strong> Beneficiarse de un movimiento bajista moderado con riesgo limitado.</p>
                        <p><strong>Implementación:</strong> Comprar un put ATM y vender un put OTM con el mismo vencimiento.</p>
                        <p><strong>Riesgo Máximo:</strong> Limitado a la prima neta pagada.</p>
                        <p><strong>Recompensa Máxima:</strong> Diferencia entre strikes menos prima neta.</p>
                        <p><strong>Volatilidad Ideal:</strong> Baja a moderada.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    """
                    <div class="strategy-card">
                        <h4>🔴 Bear Put Ladder</h4>
                        <p><strong>Objetivo:</strong> Posición bajista agresiva con protección contra movimientos muy fuertes.</p>
                        <p><strong>Implementación:</strong> Comprar un put ITM, vender un put ATM y vender otro put muy OTM.</p>
                        <p><strong>Riesgo Máximo:</strong> Diferencia entre strikes menos primas recibidas.</p>
                        <p><strong>Recompensa Máxima:</strong> Ilimitada en ciertos rangos de precio.</p>
                        <p><strong>Volatilidad Ideal:</strong> Alta.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    """
                    <div class="strategy-card">
                        <h4>⚪ Iron Condor</h4>
                        <p><strong>Objetivo:</strong> Beneficiarse de un rango de precios estable con volatilidad decreciente.</p>
                        <p><strong>Implementación:</strong> Vender un put spread y un call spread OTM con el mismo vencimiento.</p>
                        <p><strong>Riesgo Máximo:</strong> Diferencia entre strikes de un lado menos prima neta.</p>
                        <p><strong>Recompensa Máxima:</strong> Limitada a la prima neta recibida.</p>
                        <p><strong>Volatilidad Ideal:</strong> Alta pero esperando que disminuya.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    """
                    <div class="strategy-card">
                        <h4>⚪ Calendar Spread</h4>
                        <p><strong>Objetivo:</strong> Aprovechar el paso del tiempo y cambios en volatilidad.</p>
                        <p><strong>Implementación:</strong> Vender opciones de corto plazo y comprar de largo plazo al mismo strike.</p>
                        <p><strong>Riesgo Máximo:</strong> Limitado a la prima neta pagada.</p>
                        <p><strong>Recompensa Máxima:</strong> Varía según la evolución de la volatilidad y el subyacente.</p>
                        <p><strong>Volatilidad Ideal:</strong> Baja en corto plazo, alta en largo plazo.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Estilos para parámetros del activo
        st.markdown(
            """
            <style>
            /* Estilos adaptados para modo claro y oscuro */
            .parameter-container {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .parameter-title {
                color: #1E88E5;
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 15px;
            }
            
            .parameter-item {
                background-color: rgba(255, 255, 255, 0.05);
                padding: 10px;
                border-radius: 5px;
                margin: 8px 0;
                border-left: 4px solid #1E88E5;
            }
            
            /* Estilos para parámetros recomendados */
            .recommendation-box {
                background-color: rgba(255, 255, 255, 0.05);
                padding: 15px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                margin: 10px 0;
            }
            
            .recommendation-title {
                color: #2196F3;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .recommendation-content {
                color: inherit;
            }
            
            .reasoning {
                font-size: 0.9em;
                color: rgba(255, 255, 255, 0.6);
                font-style: italic;
                margin-top: 8px;
            }
            
            /* En modo oscuro, asegurarse de que los valores sean legibles */
            .dark-mode .parameter-item strong,
            .dark-mode .recommendation-content strong {
                color: rgba(255, 255, 255, 0.9);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Luego usa el mismo código para mostrar los parámetros
        st.markdown("<div class='parameter-container'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='parameter-title'>📊 Parámetros del Activo</div>",
            unsafe_allow_html=True,
        )

        if "options_params" in context:
            params = context.get("options_params", {})
        else:
            options_manager = OptionsParameterManager()
            params = options_manager.get_symbol_params(symbol)

        if params:
            for key, value in params.items():
                st.markdown(
                    f"<div class='parameter-item'><strong>{key}:</strong> {value}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No hay parámetros disponibles para este símbolo")

        st.markdown("</div>", unsafe_allow_html=True)

        # Para los parámetros recomendados, usa este estilo modificado
        with st.expander("⚙️ Parámetros Recomendados"):
            # El CSS ya está incluido en el bloque anterior

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("<div class='recommendation-box'>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='recommendation-title'>⏳ Vencimiento</div>",
                    unsafe_allow_html=True,
                )
                vencimiento = "45 días" if recommendation != "NEUTRAL" else "30-60 días"
                st.markdown(
                    f"<div class='recommendation-content'>Recomendado: <strong>{vencimiento}</strong></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div class='reasoning'>Balance óptimo entre theta decay y tiempo para que se desarrolle el movimiento.</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div class='recommendation-box'>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='recommendation-title'>🎯 Strikes</div>",
                    unsafe_allow_html=True,
                )
                try:
                    if data is not None and not data.empty:
                        current_price = data["Close"].iloc[-1]
                        if recommendation == "CALL":
                            strikes = f"Comprar: ${current_price:.2f} (ATM)<br>Vender: ${current_price * 1.05:.2f} (5% OTM)"
                        elif recommendation == "PUT":
                            strikes = f"Comprar: ${current_price:.2f} (ATM)<br>Vender: ${current_price * 0.95:.2f} (5% OTM)"
                        else:
                            strikes = f"Put spread: ${current_price * 0.90:.2f}-${current_price * 0.95:.2f}<br>Call spread: ${current_price * 1.05:.2f}-${current_price * 1.10:.2f}"
                    else:
                        strikes = "No se pueden calcular sin precio actual"
                except Exception as e:
                    logger.error(f"Error calculando strikes: {str(e)}")
                    strikes = "Error calculando strikes"

                st.markdown(
                    f"<div class='recommendation-content'>{strikes}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

            with col3:
                st.markdown("<div class='recommendation-box'>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='recommendation-title'>🛡️ Gestión de Riesgo</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    """
                    <div class='recommendation-content'>
                        <strong>Tamaño de posición:</strong> 2-3% del capital<br>
                        <strong>Stop loss:</strong> -50% del valor de la posición<br>
                        <strong>Take profit:</strong> 25-30% del beneficio máximo potencial
                    </div>
                """,
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

    # Código para la pestaña Multi-Timeframe
    with tab3:
        st.markdown("### ⚙️ Análisis Multi-Timeframe")

        # Mostrar resultados de diferentes timeframes
        col1, col2, col3 = st.columns(3)

        timeframes = ["1d", "1wk", "1mo"]
        labels = ["Diario", "Semanal", "Mensual"]

        multi_timeframe_data = {}

        for i, (tf, label) in enumerate(zip(timeframes, labels)):
            try:
                # Obtener datos para este timeframe de manera robusta
                tf_data = analyze_market_data(symbol, tf, "1y")
                multi_timeframe_data[tf] = tf_data

                if tf_data is not None and not tf_data.empty:
                    last_row = tf_data.iloc[-1]

                    # Determinar señal basada en indicadores con manejo mejorado de valores nulos
                    rsi = last_row.get("RSI")
                    rsi_value = (
                        float(rsi) if rsi is not None and not pd.isna(rsi) else None
                    )

                    macd = last_row.get("MACD")
                    macd_signal = last_row.get("MACD_Signal")
                    macd_value = (
                        float(macd) if macd is not None and not pd.isna(macd) else None
                    )
                    macd_signal_value = (
                        float(macd_signal)
                        if macd_signal is not None and not pd.isna(macd_signal)
                        else None
                    )

                    sma_20 = last_row.get("SMA_20")
                    sma_50 = last_row.get("SMA_50")
                    sma_20_value = (
                        float(sma_20)
                        if sma_20 is not None and not pd.isna(sma_20)
                        else None
                    )
                    sma_50_value = (
                        float(sma_50)
                        if sma_50 is not None and not pd.isna(sma_50)
                        else None
                    )

                    # Inicializar señales con valores por defecto
                    momentum = "Neutral"
                    trend = "Neutral"
                    signal = "NEUTRAL"
                    signal_color = "#9E9E9E"  # Gris por defecto

                    # Determinar momentum solo si el RSI está disponible
                    if rsi_value is not None:
                        if rsi_value > 70:
                            momentum = "Sobrecompra"
                        elif rsi_value < 30:
                            momentum = "Sobreventa"

                    # Determinar tendencia solo si MACD y Signal están disponibles
                    if macd_value is not None and macd_signal_value is not None:
                        trend = (
                            "Alcista" if macd_value > macd_signal_value else "Bajista"
                        )

                    # Determinar señal general
                    sma_cross = "N/A"
                    if sma_20_value is not None and sma_50_value is not None:
                        sma_cross = (
                            "Alcista" if sma_20_value > sma_50_value else "Bajista"
                        )

                        # Actualizar señal basada en cruce de SMA
                        if sma_20_value > sma_50_value:
                            signal = "ALCISTA"
                            signal_color = "#4CAF50"  # Verde
                        else:
                            signal = "BAJISTA"
                            signal_color = "#F44336"  # Rojo

                    # O si al menos tenemos MACD, usar eso para la señal
                    elif trend != "Neutral":
                        if trend == "Alcista":
                            signal = "ALCISTA"
                            signal_color = "#4CAF50"  # Verde
                        else:
                            signal = "BAJISTA"
                            signal_color = "#F44336"  # Rojo

                    # Mostrar en columna con manejo mejorado de valores nulos
                    with [col1, col2, col3][i]:
                        st.markdown(f"#### {label}")

                        # Mostrar señal principal
                        st.markdown(
                            f"""
                            <div style="background-color: {signal_color}33; padding: 0.5rem; border-radius: 0.5rem; text-align: center; margin-bottom: 0.5rem;">
                                <div style="font-size: 1.25rem; font-weight: 700; color: {signal_color};">{signal}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Mostrar indicadores con manejo seguro de valores nulos
                        if rsi_value is not None:
                            st.markdown(f"**RSI:** {rsi_value:.1f} ({momentum})")
                        else:
                            st.markdown("**RSI:** N/A")

                        st.markdown(f"**MACD:** {trend}")
                        st.markdown(f"**SMA Cross:** {sma_cross}")

                        # Mostrar botón para ver gráfico
                        if st.button(
                            f"📈 Ver Gráfico {label}", key=f"btn_tf_{tf}_{i}"
                        ):  # Añadir índice para hacer key única
                            st.session_state.current_timeframe = tf
                            st.rerun()
                else:
                    with [col1, col2, col3][i]:
                        st.markdown(f"#### {label}")
                        st.warning(f"No hay datos disponibles para {tf}")
            except Exception as e:
                logger.error(f"Error procesando timeframe {tf}: {str(e)}")
                with [col1, col2, col3][i]:
                    st.markdown(f"#### {label}")
                    st.error(f"Error procesando datos: {str(e)}")

        # Mostrar alineación de timeframes
        st.markdown("### 📊 Alineación de Timeframes")

        daily = multi_timeframe_data.get("1d")
        weekly = multi_timeframe_data.get("1wk")
        monthly = multi_timeframe_data.get("1mo")

        # Modificar la parte de la tabla de alineación de timeframes
        try:
            if (
                daily is not None
                and weekly is not None
                and monthly is not None
                and not daily.empty
                and not weekly.empty
                and not monthly.empty
            ):
                # Extraer señales de cada timeframe
                # Obtener último valor de cada dataframe
                daily_last = daily.iloc[-1]
                weekly_last = weekly.iloc[-1]
                monthly_last = monthly.iloc[-1]

                # Manejar valores nulos para MACD
                daily_trend = (
                    "alcista"
                    if (
                        daily_last.get("MACD", 0) is not None
                        and daily_last.get("MACD_Signal", 0) is not None
                        and daily_last.get("MACD", 0) > daily_last.get("MACD_Signal", 0)
                    )
                    else "bajista"
                )
                weekly_trend = (
                    "alcista"
                    if (
                        weekly_last.get("MACD", 0) is not None
                        and weekly_last.get("MACD_Signal", 0) is not None
                        and weekly_last.get("MACD", 0)
                        > weekly_last.get("MACD_Signal", 0)
                    )
                    else "bajista"
                )
                monthly_trend = (
                    "alcista"
                    if (
                        monthly_last.get("MACD", 0) is not None
                        and monthly_last.get("MACD_Signal", 0) is not None
                        and monthly_last.get("MACD", 0)
                        > monthly_last.get("MACD_Signal", 0)
                    )
                    else "bajista"
                )

                # Determinar alineación
                if daily_trend == weekly_trend == monthly_trend:
                    alignment = "FUERTE"
                    alignment_color = (
                        "#4CAF50" if daily_trend == "alcista" else "#F44336"
                    )
                elif weekly_trend == monthly_trend:
                    alignment = "MODERADA"
                    alignment_color = (
                        "#66BB6A" if weekly_trend == "alcista" else "#EF5350"
                    )
                else:
                    alignment = "DÉBIL"
                    alignment_color = "#9E9E9E"

                # Obtener valores de RSI y BB_Width con manejo de nulos
                daily_rsi = daily_last.get("RSI", None)
                daily_rsi_condition = "Neutral"
                if daily_rsi is not None:
                    if daily_rsi > 70:
                        daily_rsi_condition = "Sobrecompra"
                    elif daily_rsi < 30:
                        daily_rsi_condition = "Sobreventa"

                weekly_rsi = weekly_last.get("RSI", None)
                weekly_rsi_condition = "Neutral"
                if weekly_rsi is not None:
                    if weekly_rsi > 70:
                        weekly_rsi_condition = "Sobrecompra"
                    elif weekly_rsi < 30:
                        weekly_rsi_condition = "Sobreventa"

                monthly_rsi = monthly_last.get("RSI", None)
                monthly_rsi_condition = "Neutral"
                if monthly_rsi is not None:
                    if monthly_rsi > 70:
                        monthly_rsi_condition = "Sobrecompra"
                    elif monthly_rsi < 30:
                        monthly_rsi_condition = "Sobreventa"

                monthly_bb_width = monthly_last.get("BB_Width", 0.04)
                volatility_condition = "Normal"
                if monthly_bb_width is not None:
                    if monthly_bb_width > 0.05:
                        volatility_condition = "Alta"
                    elif monthly_bb_width < 0.03:
                        volatility_condition = "Baja"

                # Mostrar matriz de alineación con TODOS los timeframes
                st.markdown(
                    f"""
                    <div style="background-color: {alignment_color}22; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
                        <h4 style="margin-top: 0; color: {alignment_color};">Alineación {alignment}</h4>
                        <table style="width: 100%; text-align: center;">
                            <tr style="font-weight: bold;">
                                <td>Timeframe</td>
                                <td>Tendencia</td>
                                <td>Momentum</td>
                                <td>Volatilidad</td>
                            </tr>
                            <tr>
                                <td><strong>Diario</strong></td>
                                <td style="color: {'green' if daily_trend == 'alcista' else 'red'};">{daily_trend.upper()}</td>
                                <td>{daily_rsi_condition}</td>                                
                                <td>{volatility_condition}</td>
                            </tr>
                            <tr>
                                <td><strong>Semanal</strong></td>
                                <td style="color: {'green' if weekly_trend == 'alcista' else 'red'};">{weekly_trend.upper()}</td>
                                <td>{weekly_rsi_condition}</td>                                
                                <td>{volatility_condition}</td>
                            </tr>
                            <tr>
                                <td><strong>Mensual</strong></td>
                                <td style="color: {'green' if monthly_trend == 'alcista' else 'red'};">{monthly_trend.upper()}</td>
                                <td>{monthly_rsi_condition}</td>                                
                                <td>{volatility_condition}</td>
                            </tr>
                        </table>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Mostrar recomendación basada en alineación
                st.markdown("#### 🎯 Recomendación Multi-Timeframe")

                if alignment == "FUERTE":
                    if daily_trend == "alcista":
                        st.success(
                            """
                            **Alineación Alcista Fuerte**: Los tres timeframes muestran señal alcista, lo que indica una tendencia sólida.
                            
                            **Estrategia recomendada:** Posiciones largas con horizonte de medio a largo plazo. Considerar estrategias direccionales como Call Debit Spreads o Bull Call Spreads con vencimiento de 60-90 días.
                            """
                        )
                    else:
                        st.error(
                            """
                            **Alineación Bajista Fuerte**: Los tres timeframes muestran señal bajista, lo que indica una tendencia sólida a la baja.
                            
                            **Estrategia recomendada:** Posiciones cortas con horizonte de medio plazo. Considerar Put Debit Spreads o Bull Put Spreads con vencimiento de 45-60 días.
                            """
                        )
                elif alignment == "MODERADA":
                    if weekly_trend == "alcista":
                        st.info(
                            """
                            **Alineación Alcista Moderada**: Los timeframes semanal y mensual están alineados alcistas, pero el diario muestra divergencia.
                            
                            **Estrategia recomendada:** Buscar oportunidades de compra en retrocesos. Considerar estrategias con sesgo alcista pero protección a la baja como Bull Put Spreads.
                            """
                        )
                    else:
                        st.warning(
                            """
                            **Alineación Bajista Moderada**: Los timeframes semanal y mensual están alineados bajistas, pero el diario muestra divergencia.
                            
                            **Estrategia recomendada:** Mantener cautela en posiciones largas. Considerar protección con Bear Call Spreads o reducir exposición alcista.
                            """
                        )
                else:
                    st.info(
                        """
                        **Alineación Débil**: Los timeframes muestran señales mixtas sin una dirección clara.
                        
                        **Estrategia recomendada:** Estrategias neutrales como Iron Condors o Calendar Spreads. Evitar posiciones direccionales agresivas y reducir tamaño de posición.
                        """
                    )
            else:
                st.warning(
                    "No hay datos suficientes para calcular la alineación de timeframes"
                )
        except Exception as e:
            logger.error(f"Error calculando alineación de timeframes: {str(e)}")
            st.warning(f"No se pudo calcular la alineación de timeframes: {str(e)}")

    # Código para la pestaña Análisis Experto
    with tab4:
        st.markdown("### 🧠 Análisis del Experto")

        # Botón para solicitar análisis experto
        if st.button(
            "🔍 Solicitar Análisis del Experto",
            type="primary",
            use_container_width=True,
        ):
            # Verificar si OpenAI está configurado
            if st.session_state.get("openai_configured"):
                with st.spinner("Consultando al experto de trading..."):
                    try:
                        # Obtener análisis experto
                        expert_analysis = process_expert_analysis(
                            openai,
                            st.session_state.assistant_id,
                            symbol,
                            (
                                context
                                if context and "error" not in context
                                else {"last_price": price, "change_percent": change}
                            ),
                        )

                        # Guardar el análisis en el estado de la sesión
                        if expert_analysis:
                            st.session_state.last_expert_analysis[symbol] = {
                                "analysis": expert_analysis,
                                "timestamp": datetime.now().isoformat(),
                                "price": (
                                    price
                                    if price is not None
                                    else (
                                        data["Close"].iloc[-1]
                                        if data is not None and not data.empty
                                        else 0
                                    )
                                ),
                                "change": change if change is not None else 0,
                            }
                    except Exception as e:
                        logger.error(f"Error obteniendo análisis experto: {str(e)}")
                        st.error(f"Error consultando al experto: {str(e)}")
            else:
                st.error(
                    "OpenAI no está configurado. No se puede generar análisis experto."
                )

        # Mostrar análisis guardado si existe
        if symbol in st.session_state.last_expert_analysis:
            try:
                expert_data = st.session_state.last_expert_analysis[symbol]

                # Calcular tiempo transcurrido
                analysis_time = datetime.fromisoformat(expert_data["timestamp"])
                elapsed = datetime.now() - analysis_time

                # Mostrar información del análisis
                st.markdown(
                    f"""
                    <div style="background-color: rgba(0,0,0,0.05); padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                        <p style="margin: 0; font-size: 0.8rem; color: #666;">
                            Análisis generado hace {elapsed.seconds // 60} minutos
                            | Precio: ${expert_data["price"]:.2f} ({expert_data["change"]:+.2f}%)
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Mostrar el análisis
                display_expert_opinion(expert_data["analysis"])
            except Exception as e:
                logger.error(f"Error mostrando análisis guardado: {str(e)}")
                st.error(f"Error al mostrar análisis guardado: {str(e)}")
                # Si hay error mostrando el análisis guardado, eliminarlo para evitar errores futuros
                if symbol in st.session_state.last_expert_analysis:
                    del st.session_state.last_expert_analysis[symbol]
        else:
            st.info("Solicita un nuevo análisis usando el botón superior")

        # Añadir sección de preguntas específicas
        with st.expander("❓ Preguntas Específicas al Experto"):
            question = st.text_input(
                "Pregunta sobre este activo:",
                placeholder="Ej: ¿Cuáles son los niveles de soporte clave? o ¿Qué estrategia de opciones recomiendas?",
            )

            if st.button("Preguntar", key="ask_specific"):
                if question and st.session_state.get("openai_configured"):
                    with st.spinner("Consultando al experto..."):
                        try:
                            answer = process_chat_input_with_openai(
                                question,
                                symbol,
                                st.session_state.openai_api_key,
                                st.session_state.assistant_id,
                                context,
                            )

                            st.markdown(f"**Respuesta del experto:**")
                            st.markdown(answer)
                        except Exception as e:
                            logger.error(
                                f"Error procesando pregunta específica: {str(e)}"
                            )
                            st.error(f"Error al procesar tu pregunta: {str(e)}")
                else:
                    st.warning(
                        "Por favor, ingresa una pregunta y asegúrate de que OpenAI esté configurado."
                    )

    # Pestaña de Noticias y Sentimiento (Nueva)
    with tab5:
        st.markdown("## 📰 Noticias y Análisis de Sentimiento")

        # Analizar si tenemos datos de noticias o sentimiento
        has_sentiment = "news_sentiment" in context
        has_news = "news" in context and context["news"]
        has_web = "web_results" in context and context["web_results"]

        if not has_sentiment and not has_news and not has_web:
            st.info(
                f"No se encontraron noticias o análisis de sentimiento para {symbol}. Esto puede deberse a que el símbolo es poco cubierto por medios o no hay datos disponibles."
            )

            # Ofrecer una opción para buscar manualmente
            if st.button("Intentar Análisis Manual de Sentimiento", key="try_manual"):
                st.warning(
                    "Esta funcionalidad requiere fuentes de datos adicionales. Por favor, configura las APIs necesarias en la configuración."
                )
        else:
            # Mostrar sentimiento si existe
            if has_sentiment:
                display_sentiment_analysis(context)

            # Mostrar feed de noticias si existe
            if has_news:
                display_news_feed(context)

            # Mostrar insights web si existen
            if has_web:
                display_web_insights(context)

            # Añadir un análisis de impacto de noticias
            with st.expander("📊 Análisis de Impacto de Noticias en Precio"):
                st.markdown(
                    """
                    ### Análisis de Correlación Noticias-Precio
                    
                    El análisis de correlación entre noticias y movimientos de precio ayuda a entender cómo el sentimiento mediático puede influir en la acción del precio.
                    
                    **Principales observaciones:**
                    - Las noticias con sentimiento muy negativo suelen tener un impacto inmediato en el precio
                    - El efecto de noticias positivas tiende a ser más gradual y sostenido
                    - La volatilidad aumenta significativamente después de noticias inesperadas
                    
                    **Recomendación para traders:**
                    Considere el contexto de las noticias recientes al establecer niveles de stop loss, ya que la volatilidad post-noticia puede desencadenar stops demasiado ajustados.
                """
                )

                # Crear gráfico de ejemplo de impacto de noticias
                try:
                    if data is not None and not data.empty and len(data) > 20:
                        # Crear datos de impacto de noticias (simulados)
                        news_dates = [10, 25, 40]  # índices en los datos
                        news_impacts = [
                            1,
                            -1,
                            0.5,
                        ]  # impacto positivo, negativo, neutral
                        news_titles = [
                            "Resultados superan expectativas",
                            "Preocupaciones regulatorias afectan perspectivas",
                            "Nuevo lanzamiento de producto recibido con optimismo moderado",
                        ]

                        # Gráfico de precio con marcadores de noticias
                        fig = go.Figure()

                        # Línea de precio
                        fig.add_trace(
                            go.Scatter(
                                x=list(range(len(data[-60:]))),
                                y=data["Close"][-60:].values,
                                mode="lines",
                                name="Precio",
                                line=dict(color="#1E88E5"),
                            )
                        )

                        # Marcadores de noticias
                        colors = [
                            "#4CAF50",
                            "#F44336",
                            "#FF9800",
                        ]  # verde, rojo, naranja
                        for i, (idx, impact, title) in enumerate(
                            zip(news_dates, news_impacts, news_titles)
                        ):
                            if idx < len(data[-60:]):
                                fig.add_trace(
                                    go.Scatter(
                                        x=[idx],
                                        y=[data["Close"][-60:].iloc[idx]],
                                        mode="markers",
                                        marker=dict(
                                            color=colors[i], size=10, symbol="diamond"
                                        ),
                                        name=title,
                                        hoverinfo="text",
                                        hovertext=title,
                                    )
                                )

                        fig.update_layout(
                            title="Impacto de Noticias en el Precio",
                            xaxis_title="Días",
                            yaxis_title="Precio",
                            height=400,
                            margin=dict(l=10, r=10, t=40, b=10),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                            ),
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(
                            "Datos insuficientes para el análisis de impacto de noticias."
                        )
                except Exception as e:
                    logger.error(
                        f"Error creando gráfico de impacto de noticias: {str(e)}"
                    )
                    st.warning("No se pudo generar el gráfico de impacto de noticias.")

    # Código para la pestaña Scanner de Mercado
    with tab6:
        st.markdown("### 🔍 Scanner de Mercado")

        # Selección de sectores para escanear
        selected_sectors = st.multiselect(
            "Sectores a Escanear",
            list(SYMBOLS.keys()),
            default=st.session_state.last_scan_sectors,
            help="Seleccione sectores para buscar oportunidades",
            key="scanner_tab_sectors",  # Añadir key única
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            # Filtro de señales
            filtro = st.selectbox(
                "Filtrar Señales",
                ["Todas", "ALCISTA", "BAJISTA", "Solo Alta Confianza"],
                index=0,
            )

        with col2:
            if st.button("🔍 Escanear Mercado", use_container_width=True):
                with st.spinner("Escaneando mercado en busca de oportunidades..."):
                    st.session_state.last_scan_sectors = selected_sectors
                    st.session_state.scan_results = (
                        st.session_state.scanner.scan_market(selected_sectors)
                    )
                    st.session_state.last_scan_time = datetime.now()

        # Mostrar resultados del scanner
        if (
            hasattr(st.session_state, "scan_results")
            and not st.session_state.scan_results.empty
        ):
            # Estadísticas resumen
            st.markdown("#### Resumen de Oportunidades")

            calls_count = len(
                st.session_state.scan_results[
                    st.session_state.scan_results["Tendencia"] == "ALCISTA"
                ]
            )
            puts_count = len(
                st.session_state.scan_results[
                    st.session_state.scan_results["Tendencia"] == "BAJISTA"
                ]
            )
            neutral_count = len(
                st.session_state.scan_results[
                    st.session_state.scan_results["Tendencia"] == "NEUTRAL"
                ]
            )

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Señales Alcistas",
                    calls_count,
                    delta=(
                        f"{calls_count/(calls_count+puts_count+neutral_count)*100:.1f}%"
                        if (calls_count + puts_count + neutral_count) > 0
                        else "0%"
                    ),
                )
            with col2:
                st.metric(
                    "Señales Bajistas",
                    puts_count,
                    delta=(
                        f"{puts_count/(calls_count+puts_count+neutral_count)*100:.1f}%"
                        if (calls_count + puts_count + neutral_count) > 0
                        else "0%"
                    ),
                )
            with col3:
                st.metric(
                    "Señales Neutrales",
                    neutral_count,
                    delta=(
                        f"{neutral_count/(calls_count+puts_count+neutral_count)*100:.1f}%"
                        if (calls_count + puts_count + neutral_count) > 0
                        else "0%"
                    ),
                )
            with col4:
                st.metric("Total Señales", len(st.session_state.scan_results))

            # Aplicar filtro
            filtered_results = st.session_state.scan_results
            if filtro == "ALCISTA":
                filtered_results = filtered_results[
                    filtered_results["Tendencia"] == "ALCISTA"
                ]
            elif filtro == "BAJISTA":
                filtered_results = filtered_results[
                    filtered_results["Tendencia"] == "BAJISTA"
                ]
            elif filtro == "Solo Alta Confianza":
                filtered_results = filtered_results[
                    filtered_results["Confianza"] == "ALTA"
                ]

            if not filtered_results.empty:
                # Optimizar tamaño de tabla
                display_cols = [
                    "Symbol",
                    "Sector",
                    "Tendencia",
                    "Precio",
                    "RSI",
                    "Estrategia",
                    "Confianza",
                    "Entry",
                    "Stop",
                    "Target",
                    "R/R",
                ]

                # Personalizar formato de la tabla
                styled_df = filtered_results[display_cols].style.format(
                    {
                        "Precio": "${:.2f}",
                        "RSI": "{:.1f}",
                        "Entry": "${:.2f}",
                        "Stop": "${:.2f}",
                        "Target": "${:.2f}",
                        "R/R": "{:.2f}",
                    }
                )

                # Colorear filas según tendencia
                def color_rows(row):
                    if row["Tendencia"] == "ALCISTA":
                        return ["background-color: rgba(0,128,0,0.1)"] * len(row)
                    elif row["Tendencia"] == "BAJISTA":
                        return ["background-color: rgba(255,0,0,0.1)"] * len(row)
                    else:
                        return [""] * len(row)

                styled_df = styled_df.apply(color_rows, axis=1)

                # Mostrar tabla con resultados
                st.dataframe(styled_df, use_container_width=True, height=400)

                # Mostrar timestamp
                st.caption(
                    f"Última actualización: {st.session_state.last_scan_time.strftime('%d/%m/%Y %H:%M:%S')}"
                )

                # Sección para analizar activos del scanner
                # st.markdown("#### 🔍 Analizar Activo del Scanner")

                # Lista de símbolos del scanner como selectbox
                # symbol_list = filtered_results["Symbol"].unique().tolist()
                # selected_scanner_symbol = st.selectbox(
                #    "Seleccionar activo para análisis", symbol_list
                # )

                # if st.button("Ver Análisis Detallado", key="scanner_analyze_btn"):
                # Cambiar símbolo activo y recargar la página
                #    st.session_state.current_symbol = selected_scanner_symbol
                #    st.rerun()
            else:
                st.info(
                    "No hay resultados que coincidan con el filtro seleccionado. Prueba con otro filtro o escanea más sectores."
                )
        else:
            st.info(
                """
            ### Sin datos de escaneo reciente
            
            Para obtener señales actualizadas:
            1. Selecciona los sectores que deseas monitorear
            2. Pulsa el botón "Escanear Mercado"
            3. Los resultados aparecerán en esta sección
            """
            )


# =================================================
# CONFIGURACIÓN DE OPENAI
# =================================================


def setup_openai():
    """Configura credenciales de OpenAI con manejo mejorado de errores"""
    try:
        # Estrategia de búsqueda de credenciales en múltiples ubicaciones
        credential_sources = [
            # Nivel principal
            {
                "container": st.secrets if hasattr(st, "secrets") else {},
                "key": "OPENAI_API_KEY",
                "target": "OPENAI_API_KEY",
            },
            {
                "container": st.secrets if hasattr(st, "secrets") else {},
                "key": "ASSISTANT_ID",
                "target": "ASSISTANT_ID",
            },
            # Variables de entorno
            {
                "container": os.environ,
                "key": "OPENAI_API_KEY",
                "target": "OPENAI_API_KEY",
            },
            {
                "container": os.environ,
                "key": "ASSISTANT_ID",
                "target": "ASSISTANT_ID",
            },
            # Sección api_keys en secrets
            {
                "container": (
                    st.secrets.get("api_keys", {}) if hasattr(st, "secrets") else {}
                ),
                "key": "OPENAI_API_KEY",
                "target": "OPENAI_API_KEY",
            },
            {
                "container": (
                    st.secrets.get("api_keys", {}) if hasattr(st, "secrets") else {}
                ),
                "key": "ASSISTANT_ID",
                "target": "ASSISTANT_ID",
            },
        ]

        # Nombres alternativos
        api_key_alternatives = ["openai_api_key", "OpenAIAPIKey", "OPENAI_KEY"]
        assistant_id_alternatives = ["assistant_id", "AssistantID", "ASSISTANT"]

        API_KEY = None
        ASSISTANT_ID = None

        # Buscar en todas las posibles ubicaciones
        for source in credential_sources:
            container = source["container"]
            key = source["key"]
            target = source["target"]

            if key in container:
                if target == "OPENAI_API_KEY":
                    API_KEY = container[key]
                    logger.info(f"✅ OPENAI_API_KEY encontrada en {key}")
                elif target == "ASSISTANT_ID":
                    ASSISTANT_ID = container[key]
                    logger.info(f"✅ ASSISTANT_ID encontrado en {key}")

        # Buscar nombres alternativos si aún no encontramos las credenciales
        if not API_KEY and hasattr(st, "secrets"):
            for alt_key in api_key_alternatives:
                if alt_key in st.secrets:
                    API_KEY = st.secrets[alt_key]
                    logger.info(f"✅ API Key encontrada como {alt_key}")
                    break
                elif "api_keys" in st.secrets and alt_key in st.secrets["api_keys"]:
                    API_KEY = st.secrets["api_keys"][alt_key]
                    logger.info(f"✅ API Key encontrada en api_keys.{alt_key}")
                    break

        if not ASSISTANT_ID and hasattr(st, "secrets"):
            for alt_id in assistant_id_alternatives:
                if alt_id in st.secrets:
                    ASSISTANT_ID = st.secrets[alt_id]
                    logger.info(f"✅ Assistant ID encontrado como {alt_id}")
                    break
                elif "api_keys" in st.secrets and alt_id in st.secrets["api_keys"]:
                    ASSISTANT_ID = st.secrets["api_keys"][alt_id]
                    logger.info(f"✅ Assistant ID encontrado en api_keys.{alt_id}")
                    break

        if not API_KEY:
            logger.warning("⚠️ No se encontró OPENAI_API_KEY en ninguna ubicación")
            return None, None

        if not ASSISTANT_ID:
            logger.warning("⚠️ No se encontró ASSISTANT_ID en ninguna ubicación")
            return API_KEY, None

        openai.api_key = API_KEY
        return API_KEY, ASSISTANT_ID

    except Exception as e:
        logger.error(f"Error configurando OpenAI: {str(e)}")
        return None, None


# =================================================
# VERIFICACIÓN DE APIS Y LIBRERÍAS
# =================================================


def check_api_keys():
    """Verifica las API keys disponibles en secret.toml o env vars"""
    apis_status = {}

    # Verificar API keys comunes para datos financieros
    keys_to_check = [
        "alpha_vantage_api_key",
        "finnhub_api_key",
        "marketstack_api_key",
        "openai_api_key",
        "assistant_id",
        "you_api_key",
        "tavily_api_key",
    ]

    for key in keys_to_check:
        # Intentar obtener desde Streamlit secrets o variables de entorno
        try:
            value = None
            # Primero verificar en streamlit secrets
            if hasattr(st, "secrets"):
                value = st.secrets.get(key, None)
                if value is None and "api_keys" in st.secrets:
                    value = st.secrets["api_keys"].get(key, None)

            # Si no se encuentra en secrets, verificar variables de entorno
            if value is None:
                env_key = key.upper()
                value = os.environ.get(env_key, "")

            is_present = bool(value)

            # Mostrar solo una indicación de si está presente, no el valor real
            source = "No encontrada"
            if hasattr(st, "secrets") and key in st.secrets:
                source = "Streamlit secrets"
            elif (
                hasattr(st, "secrets")
                and "api_keys" in st.secrets
                and key in st.secrets["api_keys"]
            ):
                source = "Streamlit secrets (api_keys)"
            elif key.upper() in os.environ:
                source = "Variables de entorno"

            apis_status[key] = {
                "status": "✅ Disponible" if is_present else "❌ No configurada",
                "source": source,
            }
        except Exception as e:
            apis_status[key] = {
                "status": "❌ Error accediendo",
                "source": f"Error: {str(e)}",
            }

    # Verificar si se puede acceder a APIs externas
    api_endpoints = {
        "Alpha Vantage": "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo",
        "Yahoo Finance": "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d",
        "Finnhub": "https://finnhub.io/api/v1/quote?symbol=AAPL&token=demo",
    }

    for name, url in api_endpoints.items():
        try:
            response = requests.get(url, timeout=5)
            status_code = response.status_code
            apis_status[name] = {
                "status": (
                    "✅ Accesible" if status_code == 200 else f"⚠️ Error {status_code}"
                ),
                "response_time": f"{response.elapsed.total_seconds():.2f}s",
            }
        except Exception as e:
            apis_status[name] = {"status": "❌ No accesible", "error": str(e)}

    return apis_status


def check_libraries():
    """Verifica la disponibilidad de las bibliotecas necesarias"""
    libraries = {
        "pandas": "Análisis de datos",
        "numpy": "Operaciones numéricas",
        "yfinance": "Datos de Yahoo Finance",
        "plotly": "Visualización",
        "streamlit": "Interfaz de usuario",
        "ta": "Indicadores técnicos",
        "sklearn": "Machine Learning",
        "scipy": "Cálculos científicos",
        "statsmodels": "Análisis estadístico",
        "requests": "API HTTP",
        "pytz": "Zonas horarias",
        "openai": "Inteligencia artificial",
        "beautifulsoup4": "Web scraping",
        "tavily_python": "Búsqueda web",
    }

    libraries_status = {}

    for lib, description in libraries.items():
        try:
            # Intentar importar la biblioteca
            if lib == "tavily_python":
                try:
                    from tavily import TavilyClient

                    version = "Instalada"
                except ImportError:
                    raise ImportError("No instalada")
            else:
                module = importlib.import_module(lib)
                version = getattr(module, "__version__", "versión desconocida")

            libraries_status[lib] = {
                "status": "✅ Instalada",
                "version": version,
                "description": description,
            }
        except ImportError:
            libraries_status[lib] = {
                "status": "❌ No instalada",
                "description": description,
            }
        except Exception as e:
            libraries_status[lib] = {
                "status": "⚠️ Error",
                "error": str(e),
                "description": description,
            }

    return libraries_status


def display_system_status():
    """Muestra el estado del sistema, APIs y librerías con diseño mejorado"""
    st.markdown(
        '<h1 class="main-header">🛠️ Estado del Sistema</h1>', unsafe_allow_html=True
    )

    # Información del sistema en tarjeta
    st.markdown(
        """
        <div class="dashboard-card">
            <div class="dashboard-header">Información del Sistema</div>
            <div style="display: flex; flex-wrap: wrap;">
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Información Técnica")
        st.write(f"**Python versión:** {sys.version.split(' ')[0]}")
        st.write(f"**Streamlit versión:** {st.__version__}")
        st.write(f"**Fecha y hora:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**Zona horaria:** {time.tzname[0]}")
        st.write(f"**Sistema operativo:** {os.name.upper()}")

    with col2:
        st.subheader("Estado de la Caché")
        try:
            cache_stats = _data_cache.get_stats()
            st.write(f"**Entradas en caché:** {cache_stats.get('entradas', 'N/A')}")
            st.write(f"**Hit rate:** {cache_stats.get('hit_rate', 'N/A')}")
            st.write(
                f"**Hits/Misses:** {cache_stats.get('hits', 0)}/{cache_stats.get('misses', 0)}"
            )

            # Mostrar gráfico de uso de caché
            if cache_stats.get("hits", 0) > 0 or cache_stats.get("misses", 0) > 0:
                labels = ["Hits", "Misses"]
                values = [cache_stats.get("hits", 0), cache_stats.get("misses", 0)]

                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=labels,
                            values=values,
                            hole=0.3,
                            marker_colors=["#4CAF50", "#F44336"],
                        )
                    ]
                )

                fig.update_layout(
                    title="Eficiencia de Caché",
                    height=300,
                    margin=dict(l=10, r=10, t=30, b=10),
                )

                st.plotly_chart(
                    fig, use_container_width=True, height=800
                )  # Especificar altura
        except Exception as e:
            st.write("**Error accediendo a estadísticas de caché:**", str(e))

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Estado de APIs
    st.markdown(
        """
        <div class="dashboard-card">
            <div class="dashboard-header">Estado de APIs</div>
        """,
        unsafe_allow_html=True,
    )

    apis_status = check_api_keys()

    # Crear tabla de estados de API
    api_data = []
    for api, details in apis_status.items():
        row = {"API/Key": api}
        row.update(details)
        api_data.append(row)

    # Mostrar como dataframe
    if api_data:
        api_df = pd.DataFrame(api_data)
        st.dataframe(api_df, use_container_width=True)
    else:
        st.warning("No se pudo obtener información de APIs")

    st.markdown("</div>", unsafe_allow_html=True)

    # Estado de librerías
    st.markdown(
        """
        <div class="dashboard-card">
            <div class="dashboard-header">Estado de Librerías</div>
        """,
        unsafe_allow_html=True,
    )

    libraries_status = check_libraries()

    # Crear tabla de estados de librerías
    lib_data = []
    for lib, details in libraries_status.items():
        row = {"Librería": lib}
        row.update(details)
        lib_data.append(row)

    # Mostrar como dataframe
    if lib_data:
        lib_df = pd.DataFrame(lib_data)
        st.dataframe(lib_df, use_container_width=True)
    else:
        st.warning("No se pudo obtener información de librerías")

    st.markdown("</div>", unsafe_allow_html=True)

    # Prueba de conexión a datos
    st.markdown(
        """
        <div class="dashboard-card">
            <div class="dashboard-header">Prueba de Datos</div>
        """,
        unsafe_allow_html=True,
    )

    try:
        with st.spinner("Probando acceso a datos de mercado..."):
            test_data = fetch_market_data("SPY", "2d")
            if test_data is not None and not test_data.empty:
                st.success(f"✅ Datos disponibles para SPY: {len(test_data)} registros")

                # Mostrar datos recientes
                st.dataframe(test_data.tail(3), use_container_width=True)

                # Crear un gráfico rápido para visualizar
                fig = go.Figure()

                fig.add_trace(
                    go.Candlestick(
                        x=(
                            test_data.index
                            if isinstance(test_data.index, pd.DatetimeIndex)
                            else test_data["Date"]
                        ),
                        open=test_data["Open"],
                        high=test_data["High"],
                        low=test_data["Low"],
                        close=test_data["Close"],
                        name="OHLC",
                    )
                )

                fig.update_layout(
                    title="Prueba de Datos SPY",
                    xaxis_title="Fecha",
                    yaxis_title="Precio",
                    height=400,
                    xaxis_rangeslider_visible=False,
                )

                st.plotly_chart(
                    fig, use_container_width=True, height=800
                )  # Especificar altura
            else:
                st.error("❌ No se pudieron obtener datos para SPY")
    except Exception as e:
        st.error(f"❌ Error en prueba de datos: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Botón para continuar
    if st.button("Continuar al Dashboard", type="primary", use_container_width=True):
        st.session_state.show_system_status = False
        st.rerun()


# =================================================
# FUNCIONES DE AUTENTICACIÓN Y SEGURIDAD
# =================================================


def check_authentication():
    """Verifica autenticación del usuario con interfaz mejorada"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown(
            '<h1 class="main-header">🔒 InversorIA Pro - Terminal Institucional</h1>',
            unsafe_allow_html=True,
        )

        # Mostrar información del producto en columnas
        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown(
                """
                ### Plataforma Profesional de Trading

                InversorIA Pro es una terminal avanzada de trading que ofrece:

                - 📊 Análisis técnico multi-timeframe con detección de patrones
                - 🎯 Estrategias de volatilidad y opciones con modelos avanzados
                - 📈 Surface analytics y volatilidad implícita institucional
                - ⚠️ Gestión de riesgo con métricas profesionales
                - 🤖 Trading algorítmico y asistente IA especializado
                - 📰 Análisis de sentimiento de mercado y noticias
                """
            )

        with col2:
            # Usar un contenedor con estilo para el formulario de login
            st.markdown(
                """
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; color: #1E88E5;">Acceso Restringido</h3>
                    <p>Esta plataforma está diseñada para uso institucional y requiere autenticación.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Formulario de login
            with st.form("login_form"):
                password = st.text_input("Contraseña de acceso", type="password")
                submitted = st.form_submit_button("Acceder", use_container_width=True)

                if submitted:
                    if check_password(password):
                        st.session_state.authenticated = True
                        st.session_state.show_system_status = True
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta. Intente nuevamente.")

        # Imagen o gráfico de muestra
        st.image(
            "https://placehold.co/1200x400/1E88E5/ffffff?text=Terminal+Profesional+de+Trading",
            use_container_width=True,
        )

        st.markdown("---")
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; color: #6c757d; font-size: 0.8rem;">
                <span>© 2025 InversorIA Pro | Plataforma Institucional de Trading</span>
                <span>v2.0.3</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return False

    if not validate_session():
        clear_session()
        st.rerun()

    return True


# =================================================
# FUNCIÓN PRINCIPAL
# =================================================


def main():
    """Función principal de la aplicación"""
    try:
        # Verificar autenticación primero
        if not check_authentication():
            return

        # Inicialización para usuario autenticado
        initialize_session_state()

        # Inicializar/actualizar scanner de mercado si es necesario
        if "scanner" not in st.session_state or st.session_state.scanner is None:
            try:
                # Asegurar que analyzer está disponible
                if "analyzer" not in st.session_state:
                    st.session_state.analyzer = TechnicalAnalyzer(_data_cache)

                # Crear scanner con SYMBOLS (universo de trading definido)
                st.session_state.scanner = MarketScanner(
                    SYMBOLS, st.session_state.analyzer
                )

                # Si no hay resultados previos, dar valores iniciales
                if "scan_results" not in st.session_state:
                    st.session_state.scan_results = pd.DataFrame()

                logger.info("Scanner de mercado inicializado correctamente")
            except Exception as scanner_error:
                logger.error(f"Error inicializando scanner: {str(scanner_error)}")
                st.error(f"Error inicializando scanner: {str(scanner_error)}")

            # Mostrar el estado del sistema al iniciar sesión y luego desactivarlo
            if st.session_state.get("show_system_status", False):
                display_system_status()
                return

        # Renderizar sidebar después de mostrar el estado del sistema
        render_sidebar()

        # Panel principal
        st.markdown(
            '<h1 class="main-header">💹 InversorIA Pro - Terminal de Trading</h1>',
            unsafe_allow_html=True,
        )

        # Crear pestañas principales de la aplicación
        main_tab1, main_tab2 = st.tabs(
            ["📊 Análisis Individual", "🔍 Scanner de Mercado"]
        )

        # Pestaña de análisis individual
        with main_tab1:
            # Selección de activo
            col_cat, col_sym, col_tf = st.columns([1, 1, 1])
            with col_cat:
                category = st.selectbox(
                    "Sector", list(SYMBOLS.keys()), key="category_selector"
                )
            with col_sym:
                symbol = st.selectbox(
                    "Activo", SYMBOLS[category], key="symbol_selector"
                )
            with col_tf:
                timeframe = st.selectbox(
                    "Timeframe",
                    ["1d", "1wk", "1mo"],
                    key="timeframe_selector",
                    index=["1d", "1wk", "1mo"].index(
                        st.session_state.current_timeframe
                    ),
                )

            # Actualizar símbolo actual si cambia
            if symbol != st.session_state.current_symbol:
                st.session_state.current_symbol = symbol

                # Crear nuevo thread para OpenAI si cambió el símbolo
                if st.session_state.get("openai_configured"):
                    try:
                        thread = openai.beta.threads.create()
                        st.session_state.thread_id = thread.id
                    except:
                        pass

            # Actualizar timeframe si cambia
            if timeframe != st.session_state.current_timeframe:
                st.session_state.current_timeframe = timeframe

            # Panel de Contenido y Chat
            col1, col2 = st.columns([2, 1])

            # Panel de Dashboard en columna 1
            with col1:
                # Renderizar dashboard mejorado
                render_enhanced_dashboard(symbol, timeframe)

            # Panel de Chat en columna 2
            with col2:
                st.markdown(
                    '<h2 class="sub-header">💬 Trading Specialist</h2>',
                    unsafe_allow_html=True,
                )

                # Obtener contexto para información del símbolo
                context = get_market_context(symbol)
                company_info = get_company_info(symbol)
                company_name = company_info.get("name", symbol)

                # Variables para la tarjeta de información
                price = None
                change = None
                signals = {}
                option_signal = "NEUTRAL"
                option_strategy = "N/A"
                vix_level = "N/A"
                overall_signal = "NEUTRAL"

                # Mostrar tarjeta de contexto
                if context and "error" not in context:
                    price = context.get("last_price", 0)
                    change = context.get("change_percent", 0)
                    signals = context.get("signals", {})
                    vix_level = context.get("vix_level", "N/A")

                    # Obtener señal general (overall)
                    if "overall" in signals:
                        overall_signal = signals["overall"]["signal"]

                    # Determinar señal de opciones
                    if "options" in signals:
                        option_signal = signals["options"]["direction"]
                        option_strategy = signals["options"]["strategy"]

                    # Colores dinámicos según señal
                    signal_color = "#9E9E9E"  # gris por defecto
                    if option_signal == "CALL":
                        signal_color = "#4CAF50"  # verde
                    elif option_signal == "PUT":
                        signal_color = "#F44336"  # rojo

                    # Definir HTML para la señal estándar primero
                    option_signal_html = f"""
                    <p><strong>Señal:</strong> <span style="color:{signal_color}">{option_signal}</span> ({option_strategy})</p>
                    <p><strong>VIX:</strong> {vix_level} | <strong>Volatilidad:</strong> {signals.get('volatility', {}).get('volatility_state', 'Normal')}</p>
                    """

                    # Crear HTML para la señal general fuerte si corresponde
                    strong_signal_block = ""
                    if overall_signal in ["compra_fuerte", "venta_fuerte"]:
                        strong_signal_type = (
                            "COMPRA FUERTE"
                            if overall_signal == "compra_fuerte"
                            else "VENTA FUERTE"
                        )
                        strong_signal_color = (
                            "#4CAF50"
                            if overall_signal == "compra_fuerte"
                            else "#F44336"
                        )
                        strong_signal_bg = (
                            "#E8F5E9"
                            if overall_signal == "compra_fuerte"
                            else "#FFEBEE"
                        )

                        # Versión simplificada usando una única línea de HTML
                        strong_signal_block = f'<div style="background-color: {strong_signal_bg}; margin-bottom: 10px; padding: 8px; border-radius: 4px; border-left: 3px solid {strong_signal_color};"><p style="margin: 0; font-weight: 600; color: {strong_signal_color};">⚠️ Señal General: {strong_signal_type}</p></div>'

                    # Construir el HTML completo para la tarjeta
                    card_html = f"""
                    <div style="background-color:rgba(70,70,70,0.1);padding:15px;border-radius:8px;margin-bottom:15px;border-left:5px solid {signal_color}">
                        <h3 style="margin-top:0; display: flex; justify-content: space-between;">
                            <span>{company_name}</span> 
                            <span style="color:{'#4CAF50' if change >= 0 else '#F44336'}">${price:.2f} ({change:+.2f}%)</span>
                        </h3>
                        {strong_signal_block}
                        {option_signal_html}
                        
                        <hr style="border: 0; height: 1px; background-color: rgba(255, 255, 255, 0.1); margin: 10px 0;">
                        <div style="margin-top: 10px;">
                            <div style="color: #1E88E5; font-weight: bold; margin-bottom: 8px;">📊 Parámetros del Activo</div>
                    """

                    # Obtener los parámetros del activo
                    if "options_params" in context:
                        params = context.get("options_params", {})
                    else:
                        try:
                            options_manager = OptionsParameterManager()
                            params = options_manager.get_symbol_params(symbol)
                        except:
                            params = {}

                    # Si hay parámetros, mostrarlos
                    if params:
                        for key, value in params.items():
                            card_html += f"""
                            <div style="background-color: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 5px; margin: 5px 0; 
                                    border-left: 3px solid #1E88E5; font-size: 0.9rem;">
                                <span style="font-weight: 600;">{key}:</span>
                                <span style="float: right;">{value}</span>
                            </div>
                            """
                    else:
                        card_html += """
                            <div style="padding: 8px; text-align: center; color: rgba(255, 255, 255, 0.6);">
                                No hay parámetros disponibles para este símbolo
                            </div>
                        """

                    # Cerrar la sección de parámetros y el div principal
                    card_html += """
                        </div>
                    </div>
                    """

                    # Mostrar la tarjeta usando markdown
                    st.markdown(card_html, unsafe_allow_html=True)
                else:
                    # Mostrar tarjeta con información mínima cuando no hay contexto
                    st.markdown(
                        f"""
                        <div style="background-color:rgba(70,70,70,0.1);padding:15px;border-radius:8px;margin-bottom:15px;border-left:5px solid #9E9E9E">
                            <h3 style="margin-top:0; display: flex; justify-content: space-between;">
                                <span>{company_name} ({symbol})</span> 
                            </h3>
                            <p>No se pudieron obtener datos de mercado actualizados para este activo.</p>
                            <p>Puedes consultar información general o preguntar sobre estrategias típicas.</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Mostrar badge del modo de chat
                if st.session_state.get("openai_configured"):
                    st.markdown(
                        """
                        <div style="display:inline-block;background-color:rgba(25,118,210,0.1);color:#1976D2;padding:4px 8px;border-radius:4px;font-size:0.8em;margin-bottom:10px; font-weight: 600;">
                        ✨ Modo Avanzado con IA
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """
                        <div style="display:inline-block;background-color:rgba(128,128,128,0.1);color:#9E9E9E;padding:4px 8px;border-radius:4px;font-size:0.8em;margin-bottom:10px; font-weight: 600;">
                        ⚠️ Modo Básico
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Contenedor para mensajes de chat
                chat_container = st.container(height=500)

                with chat_container:
                    # Mostrar mensajes existentes
                    for message in st.session_state.messages:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                    # Campo de entrada para nuevos mensajes
                    if prompt := st.chat_input("Pregunta sobre análisis o trading..."):
                        # Agregar mensaje del usuario
                        st.session_state.messages.append(
                            {"role": "user", "content": prompt}
                        )

                        with st.chat_message("user"):
                            st.markdown(prompt)

                        # Generar y mostrar respuesta con OpenAI si está configurado
                        with st.spinner("Analizando..."):
                            if st.session_state.get("openai_configured"):
                                response = process_chat_input_with_openai(
                                    prompt,
                                    symbol,
                                    st.session_state.openai_api_key,
                                    st.session_state.assistant_id,
                                    context,
                                )
                            else:
                                # Usar modo fallback si OpenAI no está configurado
                                response = fallback_analyze_symbol(symbol, prompt)

                        # Agregar respuesta del asistente
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )

                        with st.chat_message("assistant"):
                            st.markdown(response)

                # Disclaimer
                st.markdown("---")
                st.caption(
                    """
                    **⚠️ Disclaimer:** Este sistema proporciona análisis técnico avanzado
                    para fines informativos únicamente. No constituye asesoramiento financiero 
                    ni garantiza resultados. El trading conlleva riesgo significativo de pérdida.
                    """
                )

        # Pestaña de Scanner de Mercado
        with main_tab2:
            st.markdown("## 🔍 Scanner de Mercado")

            # Sección para selección de sectores y configuración
            st.markdown("### Configuración del Scanner")

            # Configuración en dos columnas
            col1, col2 = st.columns([3, 1])

            with col1:
                # Selección de sectores para escanear
                selected_sectors = st.multiselect(
                    "Sectores a Escanear",
                    list(SYMBOLS.keys()),
                    default=st.session_state.last_scan_sectors,
                    help="Seleccione sectores para buscar oportunidades",
                    key="scanner_main_sectors",  # Añadir key única
                )

                # Filtro de señales
                filtro = st.selectbox(
                    "Filtrar Señales",
                    ["Todas", "ALCISTA", "BAJISTA", "CALL", "PUT", "Alta Confianza"],
                    index=0,
                )

            with col2:
                # Botón para ejecutar scanner
                if st.button(
                    "🔍 Escanear Mercado", type="primary", use_container_width=True
                ):
                    with st.spinner("Escaneando mercado en busca de oportunidades..."):
                        st.session_state.last_scan_sectors = selected_sectors
                        st.session_state.scan_results = (
                            st.session_state.scanner.scan_market(selected_sectors)
                        )
                        st.session_state.last_scan_time = datetime.now()

                # Mostrar última actualización
                if hasattr(st.session_state, "last_scan_time"):
                    st.caption(
                        f"Última actualización: {st.session_state.last_scan_time.strftime('%H:%M:%S')}"
                    )

            # Mostrar resultados del scanner
            if (
                hasattr(st.session_state, "scan_results")
                and not st.session_state.scan_results.empty
            ):
                # Estadísticas resumen
                st.markdown("### Resumen de Oportunidades")

                # Conteo de señales por tipo
                calls_count = len(
                    st.session_state.scan_results[
                        st.session_state.scan_results["Estrategia"] == "CALL"
                    ]
                )
                puts_count = len(
                    st.session_state.scan_results[
                        st.session_state.scan_results["Estrategia"] == "PUT"
                    ]
                )
                neutral_count = len(
                    st.session_state.scan_results[
                        st.session_state.scan_results["Estrategia"] == "NEUTRAL"
                    ]
                )

                # Conteo por tendencia
                alcista_count = len(
                    st.session_state.scan_results[
                        st.session_state.scan_results["Tendencia"] == "ALCISTA"
                    ]
                )
                bajista_count = len(
                    st.session_state.scan_results[
                        st.session_state.scan_results["Tendencia"] == "BAJISTA"
                    ]
                )

                # Conteo por confianza
                alta_conf = len(
                    st.session_state.scan_results[
                        st.session_state.scan_results["Confianza"] == "ALTA"
                    ]
                )
                media_conf = len(
                    st.session_state.scan_results[
                        st.session_state.scan_results["Confianza"] == "MEDIA"
                    ]
                )
                baja_conf = len(
                    st.session_state.scan_results[
                        st.session_state.scan_results["Confianza"] == "BAJA"
                    ]
                )

                # Métricas en filas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Alcistas", alcista_count)
                with col2:
                    st.metric("Bajistas", bajista_count)
                with col3:
                    st.metric("Alta Confianza", alta_conf)
                with col4:
                    st.metric("Total Señales", len(st.session_state.scan_results))

                # Nueva fila para opciones
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "CALL",
                        calls_count,
                        delta=(
                            f"{calls_count/len(st.session_state.scan_results)*100:.1f}%"
                            if len(st.session_state.scan_results) > 0
                            else "0%"
                        ),
                    )
                with col2:
                    st.metric(
                        "PUT",
                        puts_count,
                        delta=(
                            f"{puts_count/len(st.session_state.scan_results)*100:.1f}%"
                            if len(st.session_state.scan_results) > 0
                            else "0%"
                        ),
                    )
                with col3:
                    # Calcular ratio R/R promedio
                    avg_rr = st.session_state.scan_results["R/R"].mean()
                    st.metric("R/R Promedio", f"{avg_rr:.2f}")
                with col4:
                    # Volatilidad promedio o algún otro indicador interesante
                    vix = get_vix_level()
                    st.metric("VIX Actual", f"{vix:.2f}")

                # Aplicar filtro
                filtered_results = st.session_state.scan_results
                if filtro == "ALCISTA":
                    filtered_results = filtered_results[
                        filtered_results["Tendencia"] == "ALCISTA"
                    ]
                elif filtro == "BAJISTA":
                    filtered_results = filtered_results[
                        filtered_results["Tendencia"] == "BAJISTA"
                    ]
                elif filtro == "CALL":
                    filtered_results = filtered_results[
                        filtered_results["Estrategia"] == "CALL"
                    ]
                elif filtro == "PUT":
                    filtered_results = filtered_results[
                        filtered_results["Estrategia"] == "PUT"
                    ]
                elif filtro == "Alta Confianza":
                    filtered_results = filtered_results[
                        filtered_results["Confianza"] == "ALTA"
                    ]

                if not filtered_results.empty:
                    # Tabla con resultados
                    st.markdown("### Oportunidades Detectadas")

                    # Columnas a mostrar
                    display_cols = [
                        "Symbol",
                        "Sector",
                        "Tendencia",
                        "Precio",
                        "Cambio",
                        "RSI",
                        "Estrategia",
                        "Confianza",
                        "Entry",
                        "Stop",
                        "Target",
                        "R/R",
                    ]

                    # Formatear la tabla
                    styled_df = filtered_results[
                        (
                            display_cols
                            if all(
                                col in filtered_results.columns for col in display_cols
                            )
                            else filtered_results.columns
                        )
                    ].style.format(
                        {
                            "Precio": "${:.2f}",
                            "Cambio": "{:+.2f}%",
                            "RSI": "{:.1f}",
                            "Entry": "${:.2f}",
                            "Stop": "${:.2f}",
                            "Target": "${:.2f}",
                            "R/R": "{:.2f}",
                        }
                    )

                    # Colorear filas según tendencia o estrategia
                    def highlight_rows(row):
                        if row["Estrategia"] == "CALL":
                            return ["background-color: rgba(0,200,0,0.1)"] * len(row)
                        elif row["Estrategia"] == "PUT":
                            return ["background-color: rgba(255,0,0,0.1)"] * len(row)
                        else:
                            return [""] * len(row)

                    styled_df = styled_df.apply(highlight_rows, axis=1)

                    # Mostrar tabla
                    st.dataframe(styled_df, use_container_width=True, height=400)

                    # Sección para analizar símbolos del scanner
                    # st.markdown("### 🔬 Análisis Detallado")

                    # Seleccionar símbolo para análisis detallado
                    # selected_symbol = st.selectbox(
                    #    "Seleccionar activo para análisis detallado",
                    #    filtered_results["Symbol"].unique().tolist(),
                    # )

                    # if st.button(
                    #    "Analizar", key="scanner_main_analyze_btn"
                    # ):  # Key única
                    # Actualizar símbolo actual y redirigir a la pestaña de análisis
                    #    st.session_state.current_symbol = selected_symbol
                    # Redirigir a la primera pestaña (Análisis Individual)
                    #    st.experimental_set_query_params(tab="análisis")
                    #    st.rerun()

                    # Tabla de comparación entre sectores
                    if len(selected_sectors) > 1:
                        st.markdown("### 📊 Análisis Sectorial")

                        # Agrupar por sector
                        sector_stats = (
                            filtered_results.groupby("Sector")
                            .agg({"Symbol": "count", "R/R": "mean", "RSI": "mean"})
                            .reset_index()
                        )

                        sector_stats.rename(
                            columns={
                                "Symbol": "Señales",
                                "R/R": "R/R Promedio",
                                "RSI": "RSI Promedio",
                            },
                            inplace=True,
                        )

                        # Aplicar formato
                        sector_styled = sector_stats.style.format(
                            {"R/R Promedio": "{:.2f}", "RSI Promedio": "{:.1f}"}
                        )

                        st.dataframe(sector_styled, use_container_width=True)

                        # Gráfico de barras con conteo por sector
                        fig = go.Figure()
                        fig.add_trace(
                            go.Bar(
                                x=sector_stats["Sector"],
                                y=sector_stats["Señales"],
                                marker_color="#1E88E5",
                            )
                        )

                        fig.update_layout(
                            title="Señales por Sector",
                            xaxis_title="Sector",
                            yaxis_title="Número de Señales",
                            height=400,
                            margin=dict(l=20, r=20, t=40, b=20),
                        )

                        st.plotly_chart(
                            fig, use_container_width=True, height=800
                        )  # Especificar altura
                else:
                    st.info(
                        "No hay resultados que coincidan con los filtros seleccionados."
                    )
            else:
                st.info(
                    """
                ### No hay datos de scanner disponibles
                
                Para obtener señales de trading:
                1. Selecciona los sectores que deseas monitorear
                2. Pulsa el botón "Escanear Mercado"
                3. Los resultados aparecerán en esta sección
                """
                )

                # Mostrar gráfico de ejemplo
                st.image(
                    "https://placehold.co/800x400/1E88E5/FFFFFF?text=Scanner+de+Mercado+InversorIA+Pro",
                    use_container_width=True,
                )

            # Sección de información
            with st.expander("ℹ️ Acerca del Scanner"):
                st.markdown(
                    """
                ### Algoritmo de Scanner
                
                El scanner de mercado de InversorIA Pro utiliza un enfoque multifactorial que evalúa:
                
                - **Análisis técnico**: Medias móviles, RSI, MACD, patrones de velas y tendencias
                - **Opciones**: Flujo de opciones, volatilidad implícita y superficie de volatilidad
                - **Niveles clave**: Soportes, resistencias y zonas de interés
                
                Cada oportunidad es calificada con un nivel de confianza basado en la alineación de factores y la calidad de la configuración.
                
                ### Interpretación de las Señales
                
                - **Alta Confianza**: Fuerte alineación de múltiples factores
                - **Media Confianza**: Buena configuración con algunos factores contradictorios
                - **Baja Confianza**: Configuración básica que requiere más análisis
                
                El ratio R/R (Riesgo/Recompensa) se calcula automáticamente basado en niveles técnicos y volatilidad del activo.
                """
                )

    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        st.error(traceback.format_exc())


if __name__ == "__main__":
    main()
