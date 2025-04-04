"""
InversorIA Pro - Terminal Institucional de Trading
--------------------------------------------------
Plataforma profesional que integra análisis técnico avanzado, estrategias de
opciones, análisis multiframe y asistencia IA para traders institucionales.

Características:
- Autenticación y permisos para usuarios institucionales
- Dashboard interactivo con múltiples módulos de análisis
- Detección avanzada de patrones técnicos y niveles clave
- Análisis de opciones con estrategias personalizadas
- Asistente IA con contexto de mercado en tiempo real
- Análisis de sentimiento, noticias y datos fundamentales
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
    initial_sidebar_state="expanded",
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
    "AAPL": {"name": "Apple Inc.", "sector": "Tecnología", "description": "Fabricante de dispositivos electrónicos y software"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Tecnología", "description": "Empresa de software y servicios en la nube"},
    "GOOGL": {"name": "Alphabet Inc. (Google)", "sector": "Tecnología", "description": "Conglomerado especializado en productos y servicios de Internet"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumo Discrecional", "description": "Comercio electrónico y servicios en la nube"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Automóviles", "description": "Fabricante de vehículos eléctricos y tecnología de energía limpia"},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Tecnología", "description": "Fabricante de unidades de procesamiento gráfico"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Tecnología", "description": "Empresa de redes sociales y tecnología"},
    "NFLX": {"name": "Netflix Inc.", "sector": "Comunicación", "description": "Servicio de streaming y producción de contenido"},
    "PYPL": {"name": "PayPal Holdings Inc.", "sector": "Servicios Financieros", "description": "Plataforma de pagos en línea"},
    "CRM": {"name": "Salesforce Inc.", "sector": "Tecnología", "description": "Software de gestión de relaciones con clientes"},
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Finanzas", "description": "Banco multinacional y servicios financieros"},
    "BAC": {"name": "Bank of America Corp.", "sector": "Finanzas", "description": "Institución bancaria multinacional"},
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "sector": "ETF", "description": "ETF que sigue el índice S&P 500"},
    "QQQ": {"name": "Invesco QQQ Trust", "sector": "ETF", "description": "ETF que sigue el índice Nasdaq-100"},
    "DIA": {"name": "SPDR Dow Jones Industrial Average ETF", "sector": "ETF", "description": "ETF que sigue el índice Dow Jones Industrial Average"},
    "IWM": {"name": "iShares Russell 2000 ETF", "sector": "ETF", "description": "ETF que sigue el índice Russell 2000 de small caps"},
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
</style>
""",
    unsafe_allow_html=True,
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
                "container": st.secrets.get("api_keys", {}) if hasattr(st, "secrets") else {},
                "key": "OPENAI_API_KEY",
                "target": "OPENAI_API_KEY",
            },
            {
                "container": st.secrets.get("api_keys", {}) if hasattr(st, "secrets") else {},
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
            elif hasattr(st, "secrets") and "api_keys" in st.secrets and key in st.secrets["api_keys"]:
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
    st.markdown('<h1 class="main-header">🛠️ Estado del Sistema</h1>', unsafe_allow_html=True)

    # Información del sistema en tarjeta
    st.markdown(
        """
        <div class="dashboard-card">
            <div class="dashboard-header">Información del Sistema</div>
            <div style="display: flex; flex-wrap: wrap;">
        """,
        unsafe_allow_html=True
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
            if cache_stats.get('hits', 0) > 0 or cache_stats.get('misses', 0) > 0:
                labels = ['Hits', 'Misses']
                values = [cache_stats.get('hits', 0), cache_stats.get('misses', 0)]

                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=.3,
                    marker_colors=['#4CAF50', '#F44336']
                )])

                fig.update_layout(
                    title="Eficiencia de Caché",
                    height=300,
                    margin=dict(l=10, r=10, t=30, b=10),
                )

                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.write("**Error accediendo a estadísticas de caché:**", str(e))

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Estado de APIs
    st.markdown(
        """
        <div class="dashboard-card">
            <div class="dashboard-header">Estado de APIs</div>
        """,
        unsafe_allow_html=True
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
        unsafe_allow_html=True
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
        unsafe_allow_html=True
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
                        x=test_data.index if isinstance(test_data.index, pd.DatetimeIndex) else test_data['Date'],
                        open=test_data['Open'],
                        high=test_data['High'],
                        low=test_data['Low'],
                        close=test_data['Close'],
                        name="OHLC"
                    )
                )

                fig.update_layout(
                    title="Prueba de Datos SPY",
                    xaxis_title="Fecha",
                    yaxis_title="Precio",
                    height=400,
                    xaxis_rangeslider_visible=False
                )

                st.plotly_chart(fig, use_container_width=True)
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
        st.markdown('<h1 class="main-header">🔒 InversorIA Pro - Terminal Institucional</h1>', unsafe_allow_html=True)

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
                unsafe_allow_html=True
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
        st.image("https://placehold.co/1200x400/1E88E5/ffffff?text=Terminal+Profesional+de+Trading", use_column_width=True)

        st.markdown("---")
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; color: #6c757d; font-size: 0.8rem;">
                <span>© 2025 InversorIA Pro | Plataforma Institucional de Trading</span>
                <span>v2.0.3</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        return False

    if not validate_session():
        clear_session()
        st.rerun()

    return True


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
        "description": f"Activo financiero negociado bajo el símbolo {symbol}"
    }


def create_technical_chart(data, symbol):
    """Crea gráfico técnico avanzado con indicadores y patrones técnicos"""
    # Verificación adecuada de DataFrame vacío
    if (
        data is None
        or (isinstance(data, pd.DataFrame) and data.empty)
        or (isinstance(data, list) and (len(data) < 20))
    ):
        logger.warning(f"Datos insuficientes o inválidos para crear gráfico de {symbol}")
        return None

    # Convertir a DataFrame si es necesario
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    # Asegurarse que las columnas necesarias existen
    required_cols = ['Open', 'High', 'Low', 'Close']
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
        subplot_titles=(f"{symbol} - OHLC con Medias Móviles y Bandas Bollinger", "MACD", "RSI"),
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
        if max_volume > 0: # Evitar división por cero
            scale_factor = max_price / max_volume * 0.2  # Ajustar para que el volumen ocupe ~20% del gráfico
        else:
            scale_factor = 0

        # Crear colores para el volumen (verde si el precio subió, rojo si bajó)
        colors = ['rgba(0, 150, 0, 0.3)' if row['Close'] >= row['Open'] else 'rgba(255, 0, 0, 0.3)'
                  for _, row in df.iterrows()]

        fig.add_trace(
            go.Bar(
                x=x_data,
                y=df["Volume"] * scale_factor,
                name="Volumen",
                marker={'color': colors},
                opacity=0.3,
                showlegend=True,
                hovertemplate="Volumen: %{y:.0f}<extra></extra>", # Mostrar volumen real en hover
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
        ("BB_MA20", "rgba(0, 150, 136, 0.7)", None), # Usar SMA_20 si BB_MA20 no existe
        ("BB_Lower", "rgba(0, 150, 136, 0.3)", "tonexty"),
    ]:
        y_col = bb
        if bb == "BB_MA20" and bb not in df.columns and "SMA_20" in df.columns:
            y_col = "SMA_20" # Fallback a SMA_20

        if y_col in df.columns:
            y_data = df[y_col]
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    name=bb,
                    line=dict(color=color, width=1),
                    fill=fill,
                    fillcolor=color.replace('0.3)', '0.1)').replace('0.7)', '0.1)') if fill else None # Lighter fill color
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
        logger.warning(f"No se pudieron detectar niveles de soporte/resistencia: {str(e)}")

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
                x_pos = df["Date"].iloc[pattern_idx] if "Date" in df.columns else df.index[pattern_idx]

                # Obtener la posición Y (depende del tipo de patrón)
                if pattern["type"] == "bullish":
                    y_pos = df["Low"].iloc[pattern_idx] * 0.995  # Ligeramente por debajo
                else:
                    y_pos = df["High"].iloc[pattern_idx] * 1.005 # Ligeramente por encima

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
        title=f"Análisis Técnico de {symbol}",
        template="plotly_white",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        ),
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
            spikemode="across"
        ),
        yaxis=dict(
            showspikes=True,
            spikethickness=1,
            spikedash="solid",
            spikecolor="gray",
            spikemode="across"
        )
    )

    return fig


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
                delta=f"{change_pct:+.2f}%"
            )

        with col2:
            if rsi is not None:
                rsi_status = "Sobrecompra" if rsi > 70 else "Sobreventa" if rsi < 30 else "Neutral"
                st.metric(
                    label="RSI",
                    value=f"{rsi:.1f}",
                    delta=rsi_status,
                    delta_color="off"
                )
            else:
                st.metric(label="RSI", value="N/A")

        with col3:
            if sma20 is not None and sma50 is not None:
                ma_cross = "Alcista" if sma20 > sma50 else "Bajista" if sma20 < sma50 else "Neutral"
                st.metric(
                    label="Cruce MA20/50",
                    value=ma_cross,
                    delta=f"MA20: ${sma20:.2f}",
                    delta_color="off"
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
                    delta_color="normal" if above_sma200 else "inverse"
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
    """Muestra información básica del activo incluso cuando no hay datos de mercado"""
    # Obtener información completa de la empresa/activo
    company_info = get_company_info(symbol)

    # Obtener nombre completo del activo
    full_name = company_info.get("name", symbol)
    sector = company_info.get("sector", "No especificado")
    description = company_info.get("description", "")

    # Estimar precio y cambio si no están disponibles
    price_display = f"${price:.2f}" if price is not None else "N/A"
    change_display = f"{change:+.2f}%" if change is not None else ""
    change_color = "green" if change is not None and change >= 0 else "red" if change is not None else "inherit"

    # Mostrar tarjeta de información del activo
    st.markdown(
        f"""
        <div class="asset-card">
            <div class="asset-header">
                <h2 class="asset-name">{full_name} ({symbol})</h2>
                <h2 class="asset-price" style="color: {change_color};">{price_display} <span style="font-size: 0.8em;">{change_display}</span></h2>
            </div>
            <p>{description}</p>
            <div class="asset-details">
                <div class="asset-detail-item">
                    <div class="asset-detail-label">Sector</div>
                    <div class="asset-detail-value">{sector}</div>
                </div>
                <div class="asset-detail-item">
                    <div class="asset-detail-label">Última Actualización</div>
                    <div class="asset-detail-value">{datetime.now().strftime('%H:%M:%S')}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def process_expert_analysis(client, assistant_id, symbol, context):
    """Procesa análisis experto con OpenAI"""
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

    # Crear contenido del prompt
    prompt = f"""
    Como Especialista en Trading y Análisis Técnico Avanzado, realiza un análisis profesional del siguiente activo:

    SÍMBOLO: {symbol}

    DATOS DE MERCADO:
    - Precio actual: ${price:.2f} ({'+' if change > 0 else ''}{change:.2f}%)
    - VIX: {vix_level}
    - Señal técnica: {overall_signal}
    - Señal de opciones: {option_signal}

    INSTRUCCIONES ESPECÍFICAS:
    1. Proporciona una evaluación integral basada en el contexto técnico y de mercado actual.
    2. Identifica los niveles de soporte y resistencia clave.
    3. Analiza los indicadores técnicos principales (RSI, MACD, medias móviles).
    4. Sugiere estrategias específicas para traders institucionales.
    5. Indica riesgos clave y niveles de stop loss recomendados.
    6. Concluye con una proyección de movimiento con rangos de precio.

    El análisis debe ser conciso, directo y con información accionable específica para un trader profesional.
    """

    try:
        # Enviar mensaje al thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=prompt
        )

        # Crear una ejecución para el thread
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id
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
                if hasattr(message, "content") and len(message.content) > 0:
                    message_content = message.content[0]
                    if hasattr(message_content, "text"):
                        nested_text = message_content.text
                        if hasattr(nested_text, "value"):
                            return nested_text.value
                        elif isinstance(nested_text, str):
                            return nested_text

                return "No se pudo procesar la respuesta del asistente"

        return "No se recibió respuesta del experto."

    except Exception as e:
        logger.error(f"Error al consultar al experto: {str(e)}")
        return f"Error al consultar al experto: {str(e)}"


def display_expert_opinion(expert_opinion):
    """Muestra la opinión del experto IA con formato mejorado"""
    if not expert_opinion:
        return

    st.markdown("## 🧠 Análisis del Experto")

    # Procesamiento mejorado del texto: buscar secciones clave
    sections = {
        "evaluación": "",
        "soporte": "",
        "indicadores": "",
        "estrategias": "",
        "riesgos": "",
        "proyección": "",
    }

    current_section = None

    try:
        # Intentar identificar secciones en el texto
        lines = expert_opinion.split("\n")
        for line in lines:
            line = line.strip()

            # Detectar secciones por encabezados
            if any(keyword in line.upper() for keyword in ["EVALUACIÓN", "ANÁLISIS", "PANORAMA"]):
                current_section = "evaluación"
                continue
            elif any(keyword in line.upper() for keyword in ["SOPORTE", "RESISTENCIA", "NIVELES"]):
                current_section = "soporte"
                continue
            elif any(keyword in line.upper() for keyword in ["INDICADOR", "TÉCNICO", "RSI", "MACD"]):
                current_section = "indicadores"
                continue
            elif any(keyword in line.upper() for keyword in ["ESTRATEGIA", "OPERATIVA", "TRADING", "RECOMENDACIÓN"]):
                current_section = "estrategias"
                continue
            elif any(keyword in line.upper() for keyword in ["RIESGO", "STOP", "CAUTELA"]):
                current_section = "riesgos"
                continue
            elif any(keyword in line.upper() for keyword in ["PROYECCIÓN", "PRONÓSTICO", "ESCENARIO", "TARGET"]):
                current_section = "proyección"
                continue

            # Agregar línea a la sección actual
            if current_section and line:
                sections[current_section] += line + "\n"
    except Exception as e:
        logger.error(f"Error al procesar la respuesta del experto: {str(e)}")

    # Si no se identificaron secciones, mostrar el texto completo
    if all(not v for v in sections.values()):
        st.markdown(
            f"""
            <div class="expert-container">
                <div class="expert-header">
                    <div class="expert-avatar">E</div>
                    <div class="expert-title">Analista de Mercados</div>
                </div>
                <div class="expert-content">
                    {expert_opinion}
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
        if sections["evaluación"]:
            st.markdown("### 📊 Evaluación General")
            st.markdown(sections["evaluación"])

        if sections["soporte"]:
            st.markdown("### 🔍 Niveles Clave")
            st.markdown(sections["soporte"])

        if sections["indicadores"]:
            st.markdown("### 📈 Análisis de Indicadores")
            st.markdown(sections["indicadores"])

        if sections["estrategias"]:
            st.markdown("### 🎯 Estrategias Recomendadas")
            st.markdown(sections["estrategias"])

        if sections["riesgos"]:
            st.markdown("### ⚠️ Gestión de Riesgo")
            st.markdown(sections["riesgos"])

        if sections["proyección"]:
            st.markdown("### 🔮 Proyección de Movimiento")
            st.markdown(sections["proyección"])

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

        # Crear mensaje enriquecido con contexto
        context_prompt = f"""
        Consulta sobre {symbol} a ${price:.2f} ({'+' if change > 0 else ''}{change:.2f}%):

        Señales técnicas actuales:
        - Tendencia general: {overall_signal}
        - Señal de opciones: {option_signal}
        - VIX: {vix_level}

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
                        logger.error(f"Error procesando herramientas: {str(tool_error)}")
                        # Continuar con la ejecución incluso si falla el procesamiento de herramientas
                        run_status = "failed"
                        break
                elif run_status in ["failed", "cancelled", "expired"]:
                    logger.error(f"Ejecución fallida con estado: {run_status}, error: {getattr(run, 'error', 'Desconocido')}")
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
                        if hasattr(message.content[0], "text"):
                            return message.content[0].text.value
                        else:
                            return "Error: Formato de respuesta no reconocido"

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
                        for term in ["timeframe", "plazo", "corto", "largo", "medio"]
                    ):
                        response += f"### Análisis Multi-Timeframe para {symbol}\n\n"

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

                        response += f"\nPara información específica, puedes preguntar sobre tendencia, opciones, RSI, volatilidad o niveles de soporte/resistencia."
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


def render_sidebar():
    """Renderiza el panel lateral con información profesional y estado del mercado"""
    with st.sidebar:
        st.markdown('<h2 class="sidebar-section-title">🧑‍💻 Trading Specialist Pro</h2>', unsafe_allow_html=True)

        # Perfil profesional en un contenedor con estilo
        st.markdown(
            """
            <div class="sidebar-profile">
                <h2>Perfil Profesional</h2>
                <p>Analista técnico y estratega de mercados con especialización en derivados financieros y más de 8 años de experiencia en trading institucional.</p>
                <p>Experto en estrategias cuantitativas, análisis de volatilidad y gestión de riesgo algorítmica.</p>
            </div>
            """,
            unsafe_allow_html=True
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
        st.markdown('<div class="sidebar-section-title">📊 Estado del Mercado</div>', unsafe_allow_html=True)

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
                    unsafe_allow_html=True
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
                        fig.add_trace(go.Scatter(
                            x=spy_data.index if isinstance(spy_data.index, pd.DatetimeIndex) else range(len(spy_data)),
                            y=spy_data['Close'],
                            line=dict(color='#1E88E5', width=2),
                            name="SPY"
                        ))

                        # Configurar layout minimalista
                        fig.update_layout(
                            height=200,
                            margin=dict(l=10, r=10, t=10, b=10),
                            showlegend=False,
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=True, zeroline=False, showticklabels=True),
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                        )

                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            except Exception as e:
                st.warning("No se pudieron cargar datos de referencia")

        except Exception as ex:
            st.warning("No se pudo obtener información de mercado")

        st.markdown('<hr style="margin: 1.5rem 0;">', unsafe_allow_html=True)

        # Acciones rápidas
        st.markdown('<div class="sidebar-section-title">⚙️ Acciones</div>', unsafe_allow_html=True)

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

        st.markdown('<div class="sidebar-section-title">💾 Caché</div>', unsafe_allow_html=True)
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
                unsafe_allow_html=True
            )

            # Mostrar estado de OpenAI
            openai_status = "✅ OpenAI conectado" if st.session_state.get("openai_configured") else "⚠️ OpenAI no configurado - Chat en modo básico"
            st.markdown(
                f"""
                <div style="font-size: 0.75rem; color: #6c757d; margin-top: 0.25rem;">
                    {openai_status}
                </div>
                """,
                unsafe_allow_html=True
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
            logger.info(f"Datos obtenidos para {symbol}: {data.shape if isinstance(data, pd.DataFrame) else 'No data'}")

            if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                logger.warning(f"No se pudieron obtener datos para {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            return None

        # Añadir indicadores técnicos si se solicita
        if indicators and data is not None and not data.empty:
            try:
                # Crear instancia del analizador técnico
                analyzer = TechnicalAnalyzer(data)

                # Calcular indicadores
                data = analyzer.add_all_indicators()

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
                            data.iloc[idx, data.columns.get_loc(col_name)] = pattern_type
                except Exception as e:
                    logger.warning(f"No se pudieron detectar patrones de velas para {symbol}: {str(e)}")
            except Exception as e:
                logger.error(f"Error calculando indicadores para {symbol}: {str(e)}")
                # Al menos retornar los datos sin indicadores
                return data

        return data
    except Exception as e:
        logger.error(f"Error general analizando datos de mercado para {symbol}: {str(e)}")
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
        st.warning(f"No se pudieron obtener datos para {symbol} en timeframe {timeframe}")

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
            unsafe_allow_html=True
        )

        # A pesar de no tener datos, mostramos el panel de chat para que el usuario pueda hacer consultas
        return

    # Si llegamos aquí, tenemos datos para mostrar

    # Crear pestañas para diferentes tipos de análisis
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Análisis Técnico",
        "🎯 Opciones",
        "⚙️ Multi-Timeframe",
        "🧠 Análisis Experto"
    ])

    with tab1:
        # Mostrar resumen técnico
        display_technical_summary(symbol, data)

        # Mostrar gráfico técnico
        st.markdown("### 📈 Gráfico Técnico")
        fig = create_technical_chart(data, symbol)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            # Guardar el gráfico activo en el estado
            st.session_state.active_chart = fig
        else:
            st.warning("No se pudo crear el gráfico técnico")

        # Mostrar detalles de indicadores
        with st.expander("📊 Detalles de Indicadores"):
            last_row = data.iloc[-1]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### Momentum")
                if "RSI" in data.columns:
                    rsi = last_row["RSI"]
                    st.metric("RSI", f"{rsi:.2f}",
                              "Sobrecompra" if rsi > 70 else "Sobreventa" if rsi < 30 else "Neutral")

                if "STOCH_K" in data.columns and "STOCH_D" in data.columns:
                    st.metric("Estocástico",
                              f"%K:{last_row['STOCH_K']:.2f} %D:{last_row['STOCH_D']:.2f}")

                if "CCI" in data.columns:
                    st.metric("CCI", f"{last_row['CCI']:.2f}")

            with col2:
                st.markdown("#### Tendencia")
                if "SMA_20" in data.columns and "SMA_50" in data.columns:
                    sma_20 = last_row["SMA_20"]
                    sma_50 = last_row["SMA_50"]
                    sma_diff = ((sma_20 / sma_50) - 1) * 100
                    st.metric("SMA 20/50", f"{sma_diff:+.2f}%",
                              "Alcista" if sma_diff > 0 else "Bajista")

                if "MACD" in data.columns and "MACD_Signal" in data.columns:
                    macd = last_row["MACD"]
                    macd_signal = last_row["MACD_Signal"]
                    macd_hist = macd - macd_signal
                    st.metric("MACD Hist", f"{macd_hist:.3f}",
                              "Alcista" if macd_hist > 0 else "Bajista")

                if "SMA_200" in data.columns:
                    price = last_row["Close"]
                    sma_200 = last_row["SMA_200"]
                    price_vs_sma = ((price / sma_200) - 1) * 100
                    st.metric("Precio vs SMA200", f"{price_vs_sma:+.2f}%",
                              "Por encima" if price_vs_sma > 0 else "Por debajo")

            with col3:
                st.markdown("#### Volatilidad")
                if "BB_Width" in data.columns:
                    st.metric("Ancho BB", f"{last_row['BB_Width']:.3f}")

                if "ATR" in data.columns:
                    st.metric("ATR", f"{last_row['ATR']:.3f}")

                # ATR como porcentaje del precio
                if "ATR" in data.columns and "Close" in data.columns:
                    atr_pct = (last_row["ATR"] / last_row["Close"]) * 100
                    st.metric("ATR %", f"{atr_pct:.2f}%")

    with tab2:
        # Obtener datos de opciones
        option_data = context.get("options", {}) if context and "error" not in context else {}
        option_signal = context.get("signals", {}).get("options", {}) if context and "error" not in context else {}

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

        # Mostrar superficie de volatilidad
        st.markdown("### 📊 Superficie de Volatilidad")

        # Datos de ejemplo para la superficie de volatilidad
        try:
            # Crear datos para la superficie
            price = last_row["Close"] if data is not None and not data.empty else 100
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
            fig = go.Figure(data=[go.Surface(
                z=vol_surface,
                x=strikes,
                y=expirations,
                colorscale='Viridis',
                colorbar=dict(title="Vol. Implícita (%)")
            )])

            fig.update_layout(
                title='Superficie de Volatilidad',
                scene=dict(
                    xaxis_title='Strike',
                    yaxis_title='Días a vencimiento',
                    zaxis_title='Volatilidad Implícita (%)'
                ),
                height=600,
                margin=dict(l=10, r=10, b=10, t=30)
            )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
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

        # Mostrar parámetros de opciones recomendados
        with st.expander("⚙️ Parámetros Recomendados"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### Vencimiento")
                vencimiento = "45 días" if recommendation != "NEUTRAL" else "30-60 días"
                st.info(f"Recomendado: **{vencimiento}**")
                st.text("Razonamiento: Balance óptimo entre theta decay y tiempo para que se desarrolle el movimiento.")

            with col2:
                st.markdown("#### Strikes")
                if data is not None and not data.empty:
                    current_price = data["Close"].iloc[-1]
                    if recommendation == "CALL":
                        strikes = f"Comprar: ${current_price:.2f} (ATM)\nVender: ${current_price * 1.05:.2f} (5% OTM)"
                    elif recommendation == "PUT":
                        strikes = f"Comprar: ${current_price:.2f} (ATM)\nVender: ${current_price * 0.95:.2f} (5% OTM)"
                    else:
                        strikes = f"Put spread: ${current_price * 0.90:.2f}-${current_price * 0.95:.2f}\nCall spread: ${current_price * 1.05:.2f}-${current_price * 1.10:.2f}"
                else:
                    strikes = "No se pueden calcular sin precio actual"

                st.info("Recomendados:")
                st.text(strikes)

            with col3:
                st.markdown("#### Gestión de Riesgo")
                st.info("Tamaño de posición: 2-3% del capital")
                st.text(f"Stop loss: -50% del valor de la posición\nTake profit: 25-30% del beneficio máximo potencial")

    with tab3:
        st.markdown("### ⚙️ Análisis Multi-Timeframe")

        # Mostrar resultados de diferentes timeframes
        col1, col2, col3 = st.columns(3)

        timeframes = ["1d", "1wk", "1mo"]
        labels = ["Diario", "Semanal", "Mensual"]

        multi_timeframe_data = {}

        for i, (tf, label) in enumerate(zip(timeframes, labels)):
            # Obtener datos para este timeframe
            tf_data = analyze_market_data(symbol, tf, "1y")
            multi_timeframe_data[tf] = tf_data

            if tf_data is not None and not tf_data.empty:
                last_row = tf_data.iloc[-1]

                # Determinar señal basada en indicadores
                rsi = last_row.get("RSI")
                macd = last_row.get("MACD")
                macd_signal = last_row.get("MACD_Signal")
                sma_20 = last_row.get("SMA_20")
                sma_50 = last_row.get("SMA_50")

                # Inicializar señales
                momentum = "Neutral"
                trend = "Neutral"

                # Determinar momentum
                if rsi is not None:
                    if rsi > 70:
                        momentum = "Sobrecompra"
                    elif rsi < 30:
                        momentum = "Sobreventa"

                # Determinar tendencia
                if macd is not None and macd_signal is not None:
                    trend = "Alcista" if macd > macd_signal else "Bajista"

                # Determinar señal general
                if sma_20 is not None and sma_50 is not None:
                    sma_cross = "Alcista" if sma_20 > sma_50 else "Bajista"
                else:
                    sma_cross = "N/A"

                # Mostrar en columna
                with [col1, col2, col3][i]:
                    st.markdown(f"#### {label}")

                    # Color para la señal general
                    if trend == "Alcista" and momentum != "Sobrecompra":
                        signal_color = "#4CAF50"  # Verde
                        signal = "ALCISTA"
                    elif trend == "Bajista" and momentum != "Sobreventa":
                        signal_color = "#F44336"  # Rojo
                        signal = "BAJISTA"
                    else:
                        signal_color = "#9E9E9E"  # Gris
                        signal = "NEUTRAL"

                    # Mostrar señal principal
                    st.markdown(
                        f"""
                        <div style="background-color: {signal_color}33; padding: 0.5rem; border-radius: 0.5rem; text-align: center; margin-bottom: 0.5rem;">
                            <div style="font-size: 1.25rem; font-weight: 700; color: {signal_color};">{signal}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Mostrar indicadores
                    st.markdown(f"**RSI:** {rsi:.1f} ({momentum})")
                    st.markdown(f"**MACD:** {trend}")
                    st.markdown(f"**SMA Cross:** {sma_cross}")

                    # Mostrar botón para ver gráfico
                    if st.button(f"📈 Ver Gráfico {label}", key=f"btn_tf_{tf}"):
                        st.session_state.current_timeframe = tf
                        st.rerun()
            else:
                with [col1, col2, col3][i]:
                    st.markdown(f"#### {label}")
                    st.warning(f"No hay datos disponibles para {tf}")

        # Mostrar alineación de timeframes
        st.markdown("### 📊 Alineación de Timeframes")

        daily = multi_timeframe_data.get("1d")
        weekly = multi_timeframe_data.get("1wk")
        monthly = multi_timeframe_data.get("1mo")

        if daily is not None and weekly is not None and monthly is not None:
            # Extraer señales de cada timeframe
            try:
                # Obtener último valor de cada dataframe
                daily_last = daily.iloc[-1]
                weekly_last = weekly.iloc[-1]
                monthly_last = monthly.iloc[-1]

                # Determinar tendencia basada en MACD y SMAs
                daily_trend = "alcista" if daily_last.get("MACD", 0) > daily_last.get("MACD_Signal", 0) else "bajista"
                weekly_trend = "alcista" if weekly_last.get("MACD", 0) > weekly_last.get("MACD_Signal", 0) else "bajista"
                monthly_trend = "alcista" if monthly_last.get("MACD", 0) > monthly_last.get("MACD_Signal", 0) else "bajista"

                # Determinar alineación
                if daily_trend == weekly_trend == monthly_trend:
                    alignment = "FUERTE"
                    alignment_color = "#4CAF50" if daily_trend == "alcista" else "#F44336"
                elif weekly_trend == monthly_trend:
                    alignment = "MODERADA"
                    alignment_color = "#66BB6A" if weekly_trend == "alcista" else "#EF5350"
                else:
                    alignment = "DÉBIL"
                    alignment_color = "#9E9E9E"

                # Mostrar matriz de alineación
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
                                <td>{('Neutral' if 30 <= daily_last.get('RSI', 50) <= 70 else 'Sobrecompra' if daily_last.get('RSI', 50) > 70 else 'Sobreventa')}</td>                                
                                <td>{('Alta' if monthly_last.get('BB_Width', 0) > 0.05 else 'Baja' if monthly_last.get('BB_Width', 0) < 0.03 else 'Normal')}</td>
                            </tr>
                        </table>
                    </div>
                    """,
                    unsafe_allow_html=True
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
            except Exception as e:
                st.warning(f"No se pudo calcular la alineación de timeframes: {str(e)}")
        else:
            st.warning("No hay datos suficientes para calcular la alineación de timeframes")

    with tab4:
        st.markdown("### 🧠 Análisis del Experto")
        
        # Botón para solicitar análisis experto
        if st.button("🔍 Solicitar Análisis del Experto", type="primary", use_container_width=True):
            # Verificar si OpenAI está configurado
            if st.session_state.get("openai_configured"):
                with st.spinner("Consultando al experto de trading..."):
                    # Obtener análisis experto
                    expert_analysis = process_expert_analysis(
                        openai, 
                        st.session_state.assistant_id, 
                        symbol, 
                        context if context and "error" not in context else {"last_price": price, "change_percent": change}
                    )
                    
                    # Guardar el análisis en el estado de la sesión
                    if expert_analysis:
                        st.session_state.last_expert_analysis[symbol] = {
                            "analysis": expert_analysis,
                            "timestamp": datetime.now().isoformat(),
                            "price": price if price is not None else (data["Close"].iloc[-1] if data is not None and not data.empty else 0),
                            "change": change if change is not None else 0
                        }
            else:
                st.error("OpenAI no está configurado. No se puede generar análisis experto.")
        
        # Mostrar análisis guardado si existe
        if symbol in st.session_state.last_expert_analysis:
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
                unsafe_allow_html=True
            )
            
            # Mostrar el análisis
            display_expert_opinion(expert_data["analysis"])
        else:
            st.info("Solicita un nuevo análisis usando el botón superior")
        
        # Añadir sección de preguntas específicas
        with st.expander("❓ Preguntas Específicas al Experto"):
            question = st.text_input("Pregunta sobre este activo:", placeholder="Ej: ¿Cuáles son los niveles de soporte clave? o ¿Qué estrategia de opciones recomiendas?")
            
            if st.button("Preguntar", key="ask_specific"):
                if question and st.session_state.get("openai_configured"):
                    with st.spinner("Consultando al experto..."):
                        answer = process_chat_input_with_openai(
                            question,
                            symbol,
                            st.session_state.openai_api_key,
                            st.session_state.assistant_id,
                            context
                        )
                        
                        st.markdown(f"**Respuesta del experto:**")
                        st.markdown(answer)
                else:
                    st.warning("Por favor, ingresa una pregunta y asegúrate de que OpenAI esté configurado.")


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

        # Mostrar el estado del sistema al iniciar sesión y luego desactivarlo
        if st.session_state.get("show_system_status", False):
            display_system_status()
            return

        # Renderizar sidebar después de mostrar el estado del sistema
        render_sidebar()

        # Panel principal
        st.markdown('<h1 class="main-header">💹 InversorIA Pro - Terminal de Trading</h1>', unsafe_allow_html=True)

        # Selección de activo
        col_cat, col_sym, col_tf = st.columns([1, 1, 1])
        with col_cat:
            category = st.selectbox(
                "Sector", list(SYMBOLS.keys()), key="category_selector"
            )
        with col_sym:
            symbol = st.selectbox("Activo", SYMBOLS[category], key="symbol_selector")
        with col_tf:
            timeframe = st.selectbox(
                "Timeframe",
                ["1d", "1wk", "1mo"],
                key="timeframe_selector",
                index=["1d", "1wk", "1mo"].index(st.session_state.current_timeframe),
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
            st.markdown('<h2 class="sub-header">💬 Trading Specialist</h2>', unsafe_allow_html=True)

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
            
            # Mostrar tarjeta de contexto
            if context and "error" not in context:
                price = context.get("last_price", 0)
                change = context.get("change_percent", 0)
                signals = context.get("signals", {})
                vix_level = context.get("vix_level", "N/A")

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

                # Mostrar tarjeta con contexto actual
                st.markdown(
                    f"""
                    <div style="background-color:rgba(70,70,70,0.1);padding:15px;border-radius:8px;margin-bottom:15px;border-left:5px solid {signal_color}">
                        <h3 style="margin-top:0; display: flex; justify-content: space-between;">
                            <span>{company_name}</span> 
                            <span style="color:{'#4CAF50' if change >= 0 else '#F44336'}">${price:.2f} ({change:+.2f}%)</span>
                        </h3>
                        <p><strong>Señal:</strong> <span style="color:{signal_color}">{option_signal}</span> ({option_strategy})</p>
                        <p><strong>VIX:</strong> {vix_level} | <strong>Volatilidad:</strong> {signals.get('volatility', {}).get('volatility_state', 'Normal')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
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
                                context
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

    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        st.error(traceback.format_exc())


if __name__ == "__main__":
    main()