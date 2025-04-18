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

import streamlit as st

# Configuración de la página - DEBE SER EL PRIMER COMANDO DE STREAMLIT
st.set_page_config(
    page_title="InversorIA Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import os
import time
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
import mysql.connector

# Las importaciones relacionadas con el envío de correos electrónicos han sido eliminadas
# ya que esta funcionalidad se ha movido a la página de Notificaciones
from typing import Dict, List, Tuple, Any, Optional

# Importar configuración de pandas para mejorar rendimiento
try:
    import pandas_config
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Error importando pandas_config: {str(e)}")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Lista para almacenar errores de importación
import_errors = []

# Importar componentes personalizados
try:
    from market_utils import (
        fetch_market_data,
        TechnicalAnalyzer,
        MarketUtils,  # Actualizado de OptionsParameterManager a MarketUtils
        get_market_context,
        get_vix_level,
        clear_cache,
        _data_cache,
    )
except Exception as e:
    import_errors.append(f"Error importando market_utils: {str(e)}")

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

    # Importar el scanner mejorado
    from enhanced_market_scanner_fixed import render_enhanced_market_scanner
except Exception as e:
    import_errors.append(f"Error importando trading_dashboard: {str(e)}")

try:
    from authenticator import check_password, validate_session, clear_session
except Exception as e:
    import_errors.append(f"Error importando authenticator: {str(e)}")

try:
    from openai_utils import process_tool_calls, tools
except Exception as e:
    import_errors.append(f"Error importando openai_utils: {str(e)}")

try:
    from technical_analysis import (
        detect_support_resistance,
        detect_trend_lines,
        detect_channels,
        detect_candle_patterns,
    )
except Exception as e:
    import_errors.append(f"Error importando technical_analysis: {str(e)}")


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


# Importar información de símbolos y nombres completos desde company_data.py
from company_data import COMPANY_INFO, SYMBOLS, get_company_info

# Importar gestor de datos de mercado
try:
    from market_data_manager import MarketDataManager

    # Crear instancia del gestor de datos de mercado
    market_data_mgr = MarketDataManager()
    logger.info("Gestor de datos de mercado inicializado correctamente")
except ImportError:
    logger.warning(
        "No se pudo importar MarketDataManager. Se usarán funciones alternativas."
    )
    market_data_mgr = None
except Exception as e:
    logger.error(f"Error inicializando MarketDataManager: {str(e)}")
    market_data_mgr = None

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
        border: 1px solid var(--border-color, #EEEEEE);
        border-radius: 10px;
        padding: 1rem;
        background-color: var(--background-color, #FAFAFA);
        margin-top: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: var(--text-color, #333333);
    }

    .expert-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border-color, #EEEEEE);
        padding-bottom: 0.5rem;
    }

    .expert-avatar {
        background-color: var(--primary-color, #1E88E5);
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
        color: var(--primary-color, #1E88E5);
    }

    .expert-content {
        line-height: 1.6;
        color: var(--text-color, #333333);
    }

    /* Estilos para tablas en modo oscuro */
    .dataframe {
        color: var(--text-color, #333333);
        background-color: var(--background-color, #ffffff);
        border-color: var(--border-color, #e1e4e8);
    }

    .dataframe th {
        background-color: var(--header-bg-color, #f6f8fa);
        color: var(--header-text-color, #24292e);
        border-color: var(--border-color, #e1e4e8);
    }

    .dataframe td {
        border-color: var(--border-color, #e1e4e8);
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
        background-color: rgba(248, 249, 250, 0.1);
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #1E88E5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }

    .scanner-result.call {
        border-left: 4px solid #4CAF50;
        background-color: rgba(76, 175, 80, 0.1);
    }

    .scanner-result.put {
        border-left: 4px solid #F44336;
        background-color: rgba(244, 67, 54, 0.1);
    }

    /* Mejoras para modo oscuro */
    @media (prefers-color-scheme: dark) {
        .scanner-result {
            background-color: rgba(30, 30, 30, 0.6);
            border-color: #1E88E5;
        }

        .scanner-result.call {
            background-color: rgba(76, 175, 80, 0.15);
            border-color: #4CAF50;
        }

        .scanner-result.put {
            background-color: rgba(244, 67, 54, 0.15);
            border-color: #F44336;
        }

        .expert-container {
            background-color: rgba(30, 30, 30, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .expert-header {
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .expert-footer {
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
        }
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
# CLASES PARA EL SISTEMA DE NOTIFICACIONES
# =================================================


class DatabaseManager:
    """Gestiona la conexión y operaciones con la base de datos"""

    def __init__(self):
        """Inicializa el gestor de base de datos"""
        self.connection = None
        self.config = self._get_db_config()

    def _get_db_config(self):
        """Obtiene la configuración de la base de datos desde secrets.toml"""
        try:
            # Intentar obtener configuración desde secrets.toml con los nombres de variables correctos
            if hasattr(st, "secrets") and "db_host" in st.secrets:
                logger.info("Usando configuración de base de datos desde secrets.toml")
                return {
                    "host": st.secrets.get("db_host", "localhost"),
                    "port": st.secrets.get("db_port", 3306),
                    "user": st.secrets.get("db_user", "root"),
                    "password": st.secrets.get("db_password", ""),
                    "database": st.secrets.get("db_name", "inversoria"),
                }
            # Intentar con nombres alternativos
            elif hasattr(st, "secrets") and "mysql_host" in st.secrets:
                logger.info(
                    "Usando configuración alternativa de base de datos desde secrets.toml"
                )
                return {
                    "host": st.secrets.get("mysql_host", "localhost"),
                    "port": st.secrets.get("mysql_port", 3306),
                    "user": st.secrets.get("mysql_user", "root"),
                    "password": st.secrets.get("mysql_password", ""),
                    "database": st.secrets.get("mysql_database", "inversoria"),
                }
            else:
                logger.warning(
                    "No se encontró configuración de base de datos en secrets.toml, usando valores por defecto"
                )
                return {
                    "host": "localhost",
                    "port": 3306,
                    "user": "root",
                    "password": "",
                    "database": "inversoria",
                }
        except Exception as e:
            logger.error(f"Error obteniendo configuración de BD: {str(e)}")
            return {
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "",
                "database": "inversoria",
            }

    def connect(self):
        """Establece conexión con la base de datos"""
        try:
            # Primero intentar conectar sin especificar la base de datos
            config_without_db = self.config.copy()
            if "database" in config_without_db:
                del config_without_db["database"]

            # Conectar al servidor MySQL
            temp_connection = mysql.connector.connect(**config_without_db)
            temp_cursor = temp_connection.cursor()

            # Verificar si la base de datos existe
            temp_cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in temp_cursor]

            # Si la base de datos no existe, crearla
            if self.config["database"] not in databases:
                logger.info(f"Creando base de datos {self.config['database']}")
                temp_cursor.execute(f"CREATE DATABASE {self.config['database']}")
                temp_connection.commit()

                # Crear tablas necesarias
                temp_cursor.execute(f"USE {self.config['database']}")

                # Tabla de señales de trading con estructura mejorada
                temp_cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    direction ENUM('CALL', 'PUT', 'NEUTRAL') NOT NULL,
                    confidence_level ENUM('Alta', 'Media', 'Baja') NOT NULL,
                    timeframe VARCHAR(50) NOT NULL,
                    strategy VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    analysis TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_symbol (symbol),
                    INDEX idx_direction (direction),
                    INDEX idx_confidence (confidence_level),
                    INDEX idx_category (category),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                )

                # Tabla de logs de correos con estructura mejorada
                temp_cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS email_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    recipients TEXT NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    content_summary VARCHAR(255),
                    signals_included VARCHAR(255) COMMENT 'IDs de las señales incluidas en el boletín, separados por comas',
                    sent_at DATETIME NOT NULL,
                    status ENUM('success', 'error') DEFAULT 'success',
                    error_message TEXT,
                    INDEX idx_sent_at (sent_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                )

                # Tabla de sentimiento de mercado con estructura mejorada
                temp_cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS market_sentiment (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    overall ENUM('Alcista', 'Bajista', 'Neutral') NOT NULL,
                    vix VARCHAR(50),
                    sp500_trend VARCHAR(100),
                    technical_indicators VARCHAR(100),
                    volume VARCHAR(100),
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE INDEX idx_date (date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                )

                # Tabla de noticias de mercado con estructura mejorada
                temp_cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS market_news (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    summary TEXT,
                    source VARCHAR(100),
                    url VARCHAR(255),
                    news_date DATETIME NOT NULL,
                    impact ENUM('Alto', 'Medio', 'Bajo') DEFAULT 'Medio',
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_news_date (news_date),
                    INDEX idx_impact (impact)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                )

                temp_connection.commit()
                logger.info("Tablas creadas correctamente")

            # Cerrar conexión temporal
            temp_cursor.close()
            temp_connection.close()

            # Conectar a la base de datos
            self.connection = mysql.connector.connect(**self.config)
            logger.info(
                f"Conexión establecida con la base de datos {self.config['database']}"
            )
            return True
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {str(e)}")
            return False

    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def execute_query(self, query, params=None):
        """Ejecuta una consulta SQL y devuelve los resultados"""
        results = []
        try:
            if self.connect():
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(query, params or [])

                # Obtener resultados como diccionarios
                results = cursor.fetchall()

                # Si los resultados no son diccionarios, convertirlos
                if results and not isinstance(results[0], dict):
                    # Obtener nombres de columnas
                    column_names = [desc[0] for desc in cursor.description]

                    # Convertir cada fila a diccionario
                    dict_results = []
                    for row in results:
                        row_dict = {}
                        for i, value in enumerate(row):
                            if i < len(column_names):
                                row_dict[column_names[i]] = value
                        dict_results.append(row_dict)
                    results = dict_results

                cursor.close()
                self.disconnect()
                return results
            else:
                logger.warning("No se pudo conectar a la base de datos")
                return []
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {str(e)}")
            return []

    def get_signals(self, days_back=7, categories=None, confidence_levels=None):
        """Obtiene señales de trading filtradas"""
        query = """SELECT * FROM trading_signals
                  WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"""
        params = [days_back]

        # Añadir filtros adicionales
        if categories and "Todas" not in categories:
            placeholders = ", ".join(["%s"] * len(categories))
            query += f" AND category IN ({placeholders})"
            params.extend(categories)

        if confidence_levels and len(confidence_levels) > 0:
            placeholders = ", ".join(["%s"] * len(confidence_levels))
            query += f" AND confidence_level IN ({placeholders})"
            params.extend(confidence_levels)

        query += " ORDER BY created_at DESC"

        return self.execute_query(query, params)

    def save_signal(self, signal_data):
        """Guarda una señal de trading en la base de datos con información detallada"""
        try:
            if self.connect():
                cursor = self.connection.cursor()

                # Preparar consulta con todos los campos nuevos
                query = """INSERT INTO trading_signals
                          (symbol, price, direction, confidence_level, timeframe,
                           strategy, category, analysis, created_at,
                           entry_price, stop_loss, target_price, risk_reward, setup_type,
                           technical_analysis, support_level, resistance_level, rsi, trend, trend_strength,
                           volatility, options_signal, options_analysis, trading_specialist_signal,
                           trading_specialist_confidence, sentiment, sentiment_score, latest_news,
                           news_source, additional_news, expert_analysis, recommendation, mtf_analysis,
                           daily_trend, weekly_trend, monthly_trend, bullish_indicators, bearish_indicators,
                           is_high_confidence)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                # Preparar datos con todos los campos
                params = (
                    # Campos básicos
                    signal_data.get("symbol", ""),
                    signal_data.get("price", 0.0),
                    signal_data.get("direction", "NEUTRAL"),
                    signal_data.get("confidence_level", "Baja"),
                    signal_data.get("timeframe", "Corto Plazo"),
                    signal_data.get("strategy", "Análisis Técnico"),
                    signal_data.get("category", "General"),
                    signal_data.get("analysis", ""),
                    signal_data.get("created_at", datetime.now()),
                    # Campos para niveles de trading
                    signal_data.get("entry_price", signal_data.get("price", 0.0)),
                    signal_data.get("stop_loss", 0.0),
                    signal_data.get("target_price", 0.0),
                    signal_data.get("risk_reward", 0.0),
                    signal_data.get(
                        "setup_type", signal_data.get("strategy", "Análisis Técnico")
                    ),
                    # Campos para análisis técnico
                    signal_data.get("technical_analysis", ""),
                    signal_data.get("support_level", 0.0),
                    signal_data.get("resistance_level", 0.0),
                    signal_data.get("rsi", 0.0),
                    signal_data.get("trend", "NEUTRAL"),
                    signal_data.get("trend_strength", "MEDIA"),
                    # Campos para opciones
                    signal_data.get("volatility", 0.0),
                    signal_data.get("options_signal", ""),
                    signal_data.get("options_analysis", ""),
                    # Campos para Trading Specialist
                    signal_data.get("trading_specialist_signal", "NEUTRAL"),
                    signal_data.get("trading_specialist_confidence", "MEDIA"),
                    # Campos para sentimiento y noticias
                    signal_data.get("sentiment", "neutral"),
                    signal_data.get("sentiment_score", 0.5),
                    signal_data.get("latest_news", ""),
                    signal_data.get("news_source", ""),
                    signal_data.get("additional_news", ""),
                    # Campos para análisis experto y multi-timeframe
                    signal_data.get("expert_analysis", ""),
                    signal_data.get("recommendation", ""),
                    signal_data.get("mtf_analysis", ""),
                    signal_data.get("daily_trend", ""),
                    signal_data.get("weekly_trend", ""),
                    signal_data.get("monthly_trend", ""),
                    signal_data.get("bullish_indicators", ""),
                    signal_data.get("bearish_indicators", ""),
                    # Indicador de alta confianza
                    signal_data.get("is_high_confidence", False),
                )

                # Ejecutar consulta
                cursor.execute(query, params)
                self.connection.commit()

                # Obtener ID insertado
                signal_id = cursor.lastrowid
                cursor.close()
                self.disconnect()

                return signal_id
            else:
                logger.warning(
                    "No se pudo conectar a la base de datos para guardar la señal"
                )
                return None
        except Exception as e:
            logger.error(f"Error guardando señal: {str(e)}")
            return None

    def log_email_sent(self, email_data):
        """Registra el envío de un correo electrónico"""
        try:
            if self.connect():
                cursor = self.connection.cursor()

                # Preparar consulta
                query = """INSERT INTO email_logs
                          (recipients, subject, content_summary, signals_included, sent_at, status, error_message)
                          VALUES (%s, %s, %s, %s, NOW(), %s, %s)"""

                # Preparar datos
                params = (
                    email_data.get("recipients", ""),
                    email_data.get("subject", ""),
                    email_data.get("content_summary", ""),
                    email_data.get("signals_included", ""),
                    email_data.get("status", "success"),
                    email_data.get("error_message", ""),
                )

                # Ejecutar consulta
                cursor.execute(query, params)
                self.connection.commit()

                # Obtener ID insertado
                log_id = cursor.lastrowid
                cursor.close()
                self.disconnect()

                logger.info(f"Registro de correo guardado con ID: {log_id}")
                return log_id
            else:
                logger.warning(
                    "No se pudo conectar a la base de datos para registrar el correo"
                )
                return None
        except Exception as e:
            logger.error(f"Error registrando correo: {str(e)}")
            return None

    def save_market_sentiment(self, sentiment_data):
        """Guarda datos de sentimiento de mercado"""
        try:
            if self.connect():
                cursor = self.connection.cursor()

                # Preparar consulta
                query = """INSERT INTO market_sentiment
                          (date, overall, vix, sp500_trend, technical_indicators, volume, notes, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""

                # Preparar datos
                params = (
                    sentiment_data.get("date", datetime.now().date()),
                    sentiment_data.get("overall", "Neutral"),
                    sentiment_data.get("vix", "N/A"),
                    sentiment_data.get("sp500_trend", "N/A"),
                    sentiment_data.get("technical_indicators", "N/A"),
                    sentiment_data.get("volume", "N/A"),
                    sentiment_data.get("notes", ""),
                )

                # Ejecutar consulta
                cursor.execute(query, params)
                self.connection.commit()

                # Obtener ID insertado
                sentiment_id = cursor.lastrowid
                cursor.close()
                self.disconnect()

                return sentiment_id
            else:
                logger.warning(
                    "No se pudo conectar a la base de datos para guardar el sentimiento"
                )
                return None
        except Exception as e:
            logger.error(f"Error guardando sentimiento: {str(e)}")
            return None

    def save_market_news(self, news_data):
        """Guarda noticias de mercado"""
        try:
            if self.connect():
                cursor = self.connection.cursor()

                # Preparar consulta
                query = """INSERT INTO market_news
                          (title, summary, source, url, news_date, impact, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, NOW())"""

                # Preparar datos
                params = (
                    news_data.get("title", ""),
                    news_data.get("summary", ""),
                    news_data.get("source", ""),
                    news_data.get("url", ""),
                    news_data.get("news_date", datetime.now()),
                    news_data.get("impact", "Medio"),
                )

                # Ejecutar consulta
                cursor.execute(query, params)
                self.connection.commit()

                # Obtener ID insertado
                news_id = cursor.lastrowid
                cursor.close()
                self.disconnect()

                return news_id
            else:
                logger.warning(
                    "No se pudo conectar a la base de datos para guardar la noticia"
                )
                return None
        except Exception as e:
            logger.error(f"Error guardando noticia: {str(e)}")
            return None


# La clase EmailManager ha sido eliminada ya que esta funcionalidad
# se ha movido a la página de Notificaciones


class RealTimeSignalAnalyzer:
    """Analiza el mercado en tiempo real para generar señales de trading"""

    def __init__(self):
        """Inicializa el analizador de señales en tiempo real"""
        self.market_data_cache = {}
        self.analysis_cache = {}
        self.sectors = [
            "Tecnología",
            "Finanzas",
            "Salud",
            "Energía",
            "Consumo",
            "Índices",
            "Materias Primas",
        ]
        self.company_info = COMPANY_INFO
        self.import_success = True

    def scan_market_by_sector(
        self, sector="Todas", days=30, confidence_threshold="Media"
    ):
        """Escanea el mercado por sector para encontrar señales de trading en tiempo real"""
        try:
            logger.info(f"Escaneando sector: {sector} en tiempo real")
            st.session_state.scan_progress = 0

            # Usar el escaner de mercado del proyecto principal
            if sector == "Todas":
                sectors_to_scan = self.sectors
            else:
                sectors_to_scan = [sector]

            # Obtener el market_scanner
            market_scanner = None

            # Mostrar mensaje de estado
            status_placeholder = st.empty()
            status_placeholder.info("Inicializando escaner de mercado...")

            # 1. Primero intentar obtenerlo desde session_state si ya existe
            if "scanner" in st.session_state and st.session_state.scanner is not None:
                market_scanner = st.session_state.scanner
                logger.info("Usando market_scanner existente desde session_state")

            # Limpiar mensaje de estado
            status_placeholder.empty()

            all_signals = []
            total_symbols = 0
            processed_symbols = 0

            # Contar total de símbolos para la barra de progreso
            for current_sector in sectors_to_scan:
                symbols = [
                    symbol
                    for symbol, info in self.company_info.items()
                    if info.get("sector") == current_sector
                ]
                total_symbols += len(symbols)

            # Crear barra de progreso
            progress_text = "Escaneando mercado en busca de oportunidades..."
            progress_bar = st.progress(0, text=progress_text)

            # Escanear cada sector
            for current_sector in sectors_to_scan:
                # Obtener símbolos del sector
                symbols = [
                    symbol
                    for symbol, info in self.company_info.items()
                    if info.get("sector") == current_sector
                ]

                if not symbols:
                    logger.warning(
                        f"No se encontraron símbolos para el sector {current_sector}"
                    )
                    continue

                logger.info(
                    f"Escaneando {len(symbols)} símbolos del sector {current_sector}"
                )

                # Escanear cada símbolo
                for symbol in symbols:
                    try:
                        # Actualizar barra de progreso
                        processed_symbols += 1
                        progress = processed_symbols / total_symbols
                        progress_bar.progress(
                            progress,
                            text=f"{progress_text} ({processed_symbols}/{total_symbols}: {symbol})",
                        )

                        # Si tenemos un market_scanner, usarlo directamente
                        if market_scanner is not None:
                            # Intentar usar el método scan_symbol del market_scanner
                            try:
                                scan_result = market_scanner.scan_market(
                                    [current_sector]
                                )
                                if not scan_result.empty:
                                    # Filtrar por símbolo
                                    symbol_result = scan_result[
                                        scan_result["Symbol"] == symbol
                                    ]
                                    if not symbol_result.empty:
                                        # Mapear el formato del market_scanner al formato de señal
                                        row = symbol_result.iloc[0]
                                        direction = (
                                            "CALL"
                                            if row["Estrategia"] == "CALL"
                                            else (
                                                "PUT"
                                                if row["Estrategia"] == "PUT"
                                                else "NEUTRAL"
                                            )
                                        )
                                        confidence = row["Confianza"]
                                        price = row["Precio"]
                                        strategy = row["Setup"]
                                        timeframe = "Medio Plazo"
                                        analysis = f"Señal {direction} con confianza {confidence}. {strategy}."

                                        # Filtrar por nivel de confianza
                                        if (
                                            confidence in [confidence_threshold, "ALTA"]
                                            and direction != "NEUTRAL"
                                        ):
                                            signal = {
                                                "symbol": symbol,
                                                "price": price,
                                                "direction": direction,
                                                "confidence_level": confidence,
                                                "timeframe": timeframe,
                                                "strategy": strategy,
                                                "category": current_sector,
                                                "analysis": analysis,
                                                "created_at": datetime.now(),
                                                "detailed_analysis": row.to_dict(),
                                            }
                                            all_signals.append(signal)
                                            logger.info(
                                                f"Señal encontrada para {symbol}: {direction} con confianza {confidence}"
                                            )
                                continue
                            except Exception as scan_error:
                                logger.warning(
                                    f"Error usando scan_symbol: {str(scan_error)}"
                                )
                                # Continuar con el método alternativo

                        # Obtener datos de mercado en tiempo real
                        df = fetch_market_data(symbol, period=f"{days}d")

                        if df is None or df.empty:
                            logger.warning(
                                f"No se pudieron obtener datos para {symbol}"
                            )
                            continue

                        # Obtener contexto de mercado completo
                        market_context = get_market_context(symbol)

                        # Analizar el símbolo usando el contexto de mercado si está disponible
                        if market_context and "error" not in market_context:
                            # Extraer señales del contexto de mercado
                            signals = market_context.get("signals", {})
                            price = market_context.get(
                                "last_price", float(df["Close"].iloc[-1])
                            )
                            change = market_context.get("change_percent", 0)

                            # Determinar dirección y confianza
                            direction = "NEUTRAL"
                            confidence = "Baja"

                            if "overall" in signals:
                                signal_data = signals["overall"]
                                signal_type = signal_data.get("signal", "")
                                confidence = signal_data.get("confidence", "Baja")

                                if signal_type in ["compra", "compra_fuerte"]:
                                    direction = "CALL"
                                elif signal_type in ["venta", "venta_fuerte"]:
                                    direction = "PUT"

                                # Mapear confianza
                                if signal_data.get("confidence", "").lower() == "alta":
                                    confidence = "Alta"
                                elif (
                                    signal_data.get("confidence", "").lower()
                                    == "moderada"
                                ):
                                    confidence = "Media"

                            # Obtener estrategia
                            strategy = "Análisis Técnico"
                            if "options" in signals:
                                strategy = signals["options"].get(
                                    "strategy", "Análisis Técnico"
                                )
                            elif (
                                "support_resistance" in market_context
                                and direction == "CALL"
                            ):
                                strategy = "Tendencia + Soporte"
                            elif (
                                "support_resistance" in market_context
                                and direction == "PUT"
                            ):
                                strategy = "Tendencia + Resistencia"
                            elif "momentum" in signals and direction == "CALL":
                                strategy = "Impulso Alcista"
                            elif "momentum" in signals and direction == "PUT":
                                strategy = "Impulso Bajista"

                            # Obtener timeframe
                            timeframe = "Medio Plazo"
                            if direction == "CALL" and confidence == "Alta":
                                timeframe = "Medio-Largo Plazo"
                            elif direction == "PUT" and confidence == "Alta":
                                timeframe = "Medio-Largo Plazo"
                            elif confidence == "Media":
                                timeframe = "Corto-Medio Plazo"
                            else:
                                timeframe = "Corto Plazo"

                            # Crear resumen de análisis
                            analysis_summary = f"{symbol} muestra tendencia {'alcista' if direction == 'CALL' else 'bajista' if direction == 'PUT' else 'neutral'} "
                            analysis_summary += f"con confianza {confidence.lower()}. "

                            # Añadir detalles de indicadores
                            if "momentum" in signals:
                                rsi = signals["momentum"].get("rsi", 50)
                                analysis_summary += f"RSI en {rsi:.1f}. "

                            # Añadir detalles de soporte/resistencia
                            if "support_resistance" in market_context:
                                sr_data = market_context["support_resistance"]
                                supports = sr_data.get("supports", [])
                                resistances = sr_data.get("resistances", [])

                                if supports and direction == "CALL":
                                    analysis_summary += (
                                        f"Soporte clave en ${supports[0]:.2f}. "
                                    )
                                if resistances and direction == "PUT":
                                    analysis_summary += (
                                        f"Resistencia clave en ${resistances[0]:.2f}. "
                                    )

                            # Añadir detalles de tendencia
                            if "trend" in signals:
                                trend_data = signals["trend"]
                                trend_type = trend_data.get("type", "")
                                if trend_type:
                                    analysis_summary += f"Tendencia {trend_type}. "

                            # Añadir detalles de patrones de velas
                            if "patterns" in signals:
                                patterns = signals["patterns"]
                                if patterns:
                                    pattern_names = [
                                        p.get("name", "")
                                        for p in patterns
                                        if p.get("name")
                                    ]
                                    if pattern_names:
                                        analysis_summary += f"Patrones detectados: {', '.join(pattern_names)}. "

                            # Guardar análisis detallado para la ficha
                            detailed_analysis = {
                                "price": price,
                                "change": change,
                                "signals": signals,
                                "direction": direction,
                                "confidence": confidence,
                                "strategy": strategy,
                                "timeframe": timeframe,
                                "analysis": analysis_summary,
                            }

                            # Filtrar por nivel de confianza y dirección
                            if (
                                confidence in [confidence_threshold, "Alta"]
                                and direction != "NEUTRAL"
                            ):
                                # Crear señal
                                signal = {
                                    "symbol": symbol,
                                    "price": price,
                                    "direction": direction,
                                    "confidence_level": confidence,
                                    "timeframe": timeframe,
                                    "strategy": strategy,
                                    "category": current_sector,
                                    "analysis": analysis_summary,
                                    "created_at": datetime.now(),
                                    "detailed_analysis": detailed_analysis,  # Guardar análisis completo para fichas detalladas
                                }
                                all_signals.append(signal)
                                logger.info(
                                    f"Señal encontrada para {symbol}: {direction} con confianza {confidence}"
                                )
                    except Exception as symbol_error:
                        logger.error(f"Error analizando {symbol}: {str(symbol_error)}")
                        continue

            # Completar la barra de progreso
            progress_bar.progress(1.0, text="Escaneo completado")

            # Ordenar señales por confianza (Alta primero) y luego por fecha (más recientes primero)
            all_signals.sort(
                key=lambda x: (
                    0 if x.get("confidence_level") == "Alta" else 1,
                    (
                        -datetime.timestamp(x.get("created_at"))
                        if isinstance(x.get("created_at"), datetime)
                        else 0
                    ),
                )
            )

            logger.info(f"Se encontraron {len(all_signals)} señales en tiempo real")
            return all_signals
        except Exception as e:
            logger.error(f"Error escaneando mercado: {str(e)}")
            # No usar datos simulados, retornar lista vacía
            return []

    def get_real_time_market_sentiment(self):
        """Obtiene el sentimiento actual del mercado en tiempo real"""
        try:
            # Mostrar mensaje de estado
            status_placeholder = st.empty()
            status_placeholder.info("Analizando sentimiento de mercado...")

            # Inicializar variables
            overall = "Neutral"
            bullish_count = 0
            bearish_count = 0
            volume_status = "Normal"
            sp500_trend = "Neutral"

            # Obtener datos del VIX
            vix_value = "N/A"
            vix_status = "N/A"
            try:
                # Intentar importar get_vix_level desde market_utils
                vix_value = get_vix_level()

                # Interpretar el valor
                if vix_value < 15:
                    vix_status = "Volatilidad Muy Baja"
                elif vix_value < 20:
                    vix_status = "Volatilidad Baja"
                elif vix_value < 30:
                    vix_status = "Volatilidad Moderada"
                elif vix_value < 40:
                    vix_status = "Volatilidad Alta"
                else:
                    vix_status = "Volatilidad Extrema"
            except Exception as vix_error:
                logger.warning(f"Error obteniendo datos del VIX: {str(vix_error)}")
                # Intentar obtener datos del VIX directamente
                vix_df = fetch_market_data("^VIX", period="30d")
                if vix_df is not None and not vix_df.empty:
                    vix_value = round(float(vix_df["Close"].iloc[-1]), 2)
                    if vix_value < 20:
                        vix_status = "Volatilidad Baja"
                    elif vix_value < 30:
                        vix_status = "Volatilidad Moderada"
                    else:
                        vix_status = "Volatilidad Alta"

            # Obtener datos del S&P 500
            try:
                sp500_df = fetch_market_data("^GSPC", period="5d")
                if sp500_df is not None and not sp500_df.empty:
                    # Calcular cambio porcentual
                    current_price = sp500_df["Close"].iloc[-1]
                    prev_price = sp500_df["Close"].iloc[-2]
                    change_pct = ((current_price - prev_price) / prev_price) * 100

                    # Determinar tendencia
                    if change_pct > 1.0:
                        sp500_trend = "Fuertemente Alcista"
                    elif change_pct > 0.3:
                        sp500_trend = "Alcista"
                    elif change_pct < -1.0:
                        sp500_trend = "Fuertemente Bajista"
                    elif change_pct < -0.3:
                        sp500_trend = "Bajista"
                    else:
                        sp500_trend = "Neutral"

                    # Calcular volumen
                    if "Volume" in sp500_df.columns:
                        current_vol = sp500_df["Volume"].iloc[-1]
                        avg_vol = sp500_df["Volume"].mean()
                        vol_ratio = current_vol / avg_vol

                        if vol_ratio > 1.5:
                            volume_status = "Muy Alto"
                        elif vol_ratio > 1.2:
                            volume_status = "Alto"
                        elif vol_ratio < 0.8:
                            volume_status = "Bajo"
                        elif vol_ratio < 0.5:
                            volume_status = "Muy Bajo"
                        else:
                            volume_status = "Normal"
            except Exception as sp500_error:
                logger.warning(
                    f"Error obteniendo datos del S&P 500: {str(sp500_error)}"
                )

            # Escanear índices principales para determinar sentimiento general
            indices = ["^GSPC", "^DJI", "^IXIC", "^RUT"]
            for index in indices:
                try:
                    context = get_market_context(index)
                    if (
                        context
                        and "signals" in context
                        and "overall" in context["signals"]
                    ):
                        signal = context["signals"]["overall"]["signal"]
                        if signal in ["compra", "compra_fuerte"]:
                            bullish_count += 1
                        elif signal in ["venta", "venta_fuerte"]:
                            bearish_count += 1
                except Exception:
                    continue

            # Determinar sentimiento general basado en conteos
            if bullish_count > bearish_count:
                overall = "Alcista"
            elif bearish_count > bullish_count:
                overall = "Bajista"
            else:
                overall = "Neutral"

            # Limpiar mensaje de estado
            status_placeholder.empty()

            # Crear objeto de sentimiento
            sentiment = {
                "overall": overall,
                "vix": f"{vix_value} - {vix_status}",
                "sp500_trend": sp500_trend,
                "technical_indicators": f"{int(bullish_count/(bullish_count+bearish_count)*100) if (bullish_count+bearish_count) > 0 else 0}% Alcistas, {int(bearish_count/(bullish_count+bearish_count)*100) if (bullish_count+bearish_count) > 0 else 0}% Bajistas",
                "volume": volume_status,
                "notes": f"Datos en tiempo real - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            }

            return sentiment
        except Exception as e:
            logger.error(f"Error obteniendo sentimiento de mercado: {str(e)}")
            return {
                "overall": "Neutral",
                "vix": "N/A",
                "sp500_trend": "N/A",
                "technical_indicators": "N/A",
                "volume": "N/A",
                "notes": f"Error obteniendo datos - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            }

    def get_market_news(self):
        """Obtiene noticias relevantes del mercado en tiempo real"""
        try:
            # Mostrar mensaje de estado
            status_placeholder = st.empty()
            status_placeholder.info("Buscando noticias relevantes...")

            # Intentar obtener noticias desde el market_scanner
            if "scanner" in st.session_state and st.session_state.scanner is not None:
                market_scanner = st.session_state.scanner
                # Verificar si el market_scanner tiene método get_market_news
                if hasattr(market_scanner, "get_market_news"):
                    try:
                        news = market_scanner.get_market_news()
                        if news and isinstance(news, list) and len(news) > 0:
                            status_placeholder.empty()
                            return news
                    except Exception as scanner_error:
                        logger.warning(
                            f"Error usando market_scanner.get_market_news: {str(scanner_error)}"
                        )

            # Si no se pudieron obtener noticias del scanner, generar noticias básicas
            news_summary = []

            # Obtener datos del S&P 500 para generar noticias básicas
            try:
                sp500_df = fetch_market_data("^GSPC", period="5d")
                if sp500_df is not None and not sp500_df.empty:
                    # Calcular cambio porcentual
                    current_price = sp500_df["Close"].iloc[-1]
                    prev_price = sp500_df["Close"].iloc[-2]
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    change_sign = "+" if change_pct > 0 else ""

                    # Crear noticia sobre el S&P 500
                    news_summary.append(
                        {
                            "title": f"S&P 500 {change_sign}{change_pct:.2f}% en la última sesión",
                            "summary": f"El índice S&P 500 cerró en ${current_price:.2f}, un cambio de {change_sign}{change_pct:.2f}% respecto a la sesión anterior.",
                            "source": "InversorIA Pro",
                            "date": datetime.now(),
                        }
                    )

                    # Añadir noticia sobre el VIX si está disponible
                    try:
                        vix_df = fetch_market_data("^VIX", period="5d")
                        if vix_df is not None and not vix_df.empty:
                            vix_value = vix_df["Close"].iloc[-1]
                            vix_prev = vix_df["Close"].iloc[-2]
                            vix_change = ((vix_value - vix_prev) / vix_prev) * 100
                            vix_sign = "+" if vix_change > 0 else ""

                            news_summary.append(
                                {
                                    "title": f"VIX en {vix_value:.2f}, {vix_sign}{vix_change:.2f}%",
                                    "summary": f"El índice de volatilidad VIX se situó en {vix_value:.2f}, un cambio de {vix_sign}{vix_change:.2f}% respecto a la sesión anterior.",
                                    "source": "InversorIA Pro",
                                    "date": datetime.now(),
                                }
                            )
                    except Exception:
                        pass

                    # Añadir noticia sobre el mercado en general
                    if change_pct > 1.0:
                        news_summary.append(
                            {
                                "title": "Fuerte impulso alcista en los mercados",
                                "summary": "Los mercados muestran un fuerte impulso alcista con ganancias significativas en los principales índices.",
                                "source": "InversorIA Pro",
                                "date": datetime.now(),
                            }
                        )
                    elif change_pct < -1.0:
                        news_summary.append(
                            {
                                "title": "Presión vendedora domina los mercados",
                                "summary": "Los mercados experimentan una fuerte presión vendedora con caídas significativas en los principales índices.",
                                "source": "InversorIA Pro",
                                "date": datetime.now(),
                            }
                        )
                    else:
                        news_summary.append(
                            {
                                "title": "Mercados en consolidación",
                                "summary": "Los principales índices se mantienen en un rango estrecho mientras los inversores evalúan las condiciones actuales del mercado.",
                                "source": "InversorIA Pro",
                                "date": datetime.now(),
                            }
                        )
            except Exception as news_error:
                logger.warning(f"Error generando noticias básicas: {str(news_error)}")

            # Limpiar mensaje de estado
            status_placeholder.empty()

            return news_summary
        except Exception as e:
            logger.error(f"Error obteniendo noticias: {str(e)}")
            return []


class SignalManager:
    """Gestiona las señales de trading y su procesamiento"""

    def __init__(self):
        """Inicializa el gestor de señales"""
        self.db_manager = DatabaseManager()
        self.real_time_analyzer = RealTimeSignalAnalyzer()

    def get_active_signals(
        self, days_back=7, categories=None, confidence_levels=None, force_realtime=False
    ):
        """Obtiene las señales activas filtradas"""
        # Verificar si hay señales en caché de sesión
        if (
            "cached_signals" in st.session_state
            and st.session_state.cached_signals
            and not force_realtime
        ):
            logger.info(
                f"Usando {len(st.session_state.cached_signals)} señales desde la caché de sesión"
            )
            cached_signals = st.session_state.cached_signals

            # Aplicar filtros a las señales en caché
            filtered_signals = []
            for signal in cached_signals:
                # Filtrar por categoría
                if (
                    categories
                    and categories != "Todas"
                    and signal.get("category") not in categories
                ):
                    continue

                # Filtrar por nivel de confianza
                if (
                    confidence_levels
                    and signal.get("confidence_level") not in confidence_levels
                ):
                    continue

                # Filtrar por fecha
                created_at = signal.get("created_at")
                if isinstance(created_at, datetime):
                    if (datetime.now() - created_at).days > days_back:
                        continue

                filtered_signals.append(signal)

            if filtered_signals:
                logger.info(
                    f"Se encontraron {len(filtered_signals)} señales en caché que cumplen los filtros"
                )
                return filtered_signals

        # Si no hay señales en caché o se fuerza el escaneo en tiempo real, intentar obtener de la base de datos
        if not force_realtime:
            # Intentar obtener señales de la base de datos
            signals_from_db = self.db_manager.get_signals(
                days_back, categories, confidence_levels
            )

            # Si hay señales en la base de datos, usarlas y actualizar la caché
            if signals_from_db and len(signals_from_db) > 0:
                logger.info(
                    f"Se encontraron {len(signals_from_db)} señales en la base de datos"
                )

                # Verificar que las fechas no sean futuras
                for signal in signals_from_db:
                    if "created_at" in signal and isinstance(
                        signal["created_at"], datetime
                    ):
                        # Si la fecha es futura, corregirla a la fecha actual
                        if signal["created_at"] > datetime.now():
                            signal["created_at"] = datetime.now()
                            logger.warning(
                                f"Se corrigió una fecha futura para la señal {signal.get('symbol')}"
                            )

                # Actualizar la caché de sesión
                st.session_state.cached_signals = signals_from_db
                return signals_from_db

        # Generar señales en tiempo real
        logger.info("Generando señales en tiempo real...")

        # Verificar si hay resultados del scanner en session_state
        if (
            hasattr(st.session_state, "scan_results")
            and not st.session_state.scan_results.empty
        ):
            logger.info("Usando resultados del scanner para generar señales")

            # Convertir resultados del scanner a formato de señal
            scanner_signals = []
            scan_results = st.session_state.scan_results

            # Filtrar por categoría si es necesario
            if categories and categories != "Todas":
                scan_results = scan_results[scan_results["Sector"] == categories]

            # Filtrar por confianza si es necesario
            if confidence_levels:
                # Mapear confianza a formato del scanner (ALTA, MEDIA, BAJA)
                scanner_confidence = [c.upper() for c in confidence_levels]
                scan_results = scan_results[
                    scan_results["Confianza"].isin(scanner_confidence)
                ]

            # Convertir cada fila a formato de señal
            for _, row in scan_results.iterrows():
                try:
                    # Mapear dirección
                    direction = (
                        "CALL"
                        if row["Estrategia"] == "CALL"
                        else "PUT" if row["Estrategia"] == "PUT" else "NEUTRAL"
                    )

                    # Mapear confianza (convertir a formato de señal: Alta, Media, Baja)
                    confidence = (
                        row["Confianza"].capitalize()
                        if isinstance(row["Confianza"], str)
                        else "Media"
                    )
                    if confidence == "Alta" or confidence == "ALTA":
                        confidence = "Alta"
                    elif confidence == "Media" or confidence == "MEDIA":
                        confidence = "Media"
                    else:
                        confidence = "Baja"

                    # Crear señal
                    signal = {
                        "symbol": row["Symbol"],
                        "price": (
                            row["Precio"]
                            if isinstance(row["Precio"], (int, float))
                            else 0.0
                        ),
                        "direction": direction,
                        "confidence_level": confidence,
                        "timeframe": "Medio Plazo",
                        "strategy": (
                            row["Setup"] if "Setup" in row else "Análisis Técnico"
                        ),
                        "category": row["Sector"],
                        "analysis": f"Señal {direction} con confianza {confidence}. RSI: {row.get('RSI', 'N/A')}. R/R: {row.get('R/R', 'N/A')}",
                        "created_at": datetime.now(),
                    }
                    scanner_signals.append(signal)
                except Exception as e:
                    logger.error(
                        f"Error convirtiendo fila del scanner a señal: {str(e)}"
                    )
                    continue

            # Si se encontraron señales del scanner, usarlas
            if scanner_signals:
                logger.info(
                    f"Se encontraron {len(scanner_signals)} señales desde el scanner"
                )
                return scanner_signals
            else:
                logger.info(
                    "No se encontraron señales desde el scanner, usando analizador en tiempo real"
                )

        # Si no hay resultados del scanner o están vacíos, usar el analizador en tiempo real
        # Determinar sector y confianza para el escaneo
        sector = "Todas"
        if categories and categories != "Todas":
            sector = categories[0] if isinstance(categories, list) else categories

        confidence = "Media"
        if confidence_levels and len(confidence_levels) > 0:
            confidence = confidence_levels[0]

        # Escanear mercado en tiempo real
        real_time_signals = self.real_time_analyzer.scan_market_by_sector(
            sector=sector, days=days_back, confidence_threshold=confidence
        )

        # Si se encontraron señales en tiempo real, asignar IDs temporales
        if real_time_signals and len(real_time_signals) > 0:
            for i, signal in enumerate(real_time_signals):
                signal["id"] = i + 1
                # Asegurar que la fecha sea la actual
                signal["created_at"] = datetime.now()

            logger.info(f"Se generaron {len(real_time_signals)} señales en tiempo real")

            # Actualizar la caché de sesión con las nuevas señales
            # Combinar señales sin duplicados
            if "cached_signals" in st.session_state:
                existing_symbols = {
                    signal.get("symbol") for signal in st.session_state.cached_signals
                }
                for signal in real_time_signals:
                    if signal.get("symbol") not in existing_symbols:
                        st.session_state.cached_signals.append(signal)
                        existing_symbols.add(signal.get("symbol"))
            else:
                st.session_state.cached_signals = real_time_signals

            # Compartir señales con otras páginas
            st.session_state.market_signals = real_time_signals

            return real_time_signals

        # Si no se encontraron señales en tiempo real, devolver lista vacía
        logger.info("No se encontraron señales en tiempo real, devolviendo lista vacía")
        return []

    def get_market_sentiment(self):
        """Obtiene el sentimiento actual del mercado en tiempo real"""
        return self.real_time_analyzer.get_real_time_market_sentiment()

    def get_market_news(self):
        """Obtiene noticias relevantes del mercado"""
        return self.real_time_analyzer.get_market_news()

    # La función send_newsletter ha sido eliminada ya que esta funcionalidad
    # se ha movido a la página de Notificaciones


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

# La función get_company_info ha sido movida a company_data.py e importada al inicio del archivo


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

    # Cargar y almacenar el sentimiento de mercado diario al iniciar la aplicación
    if "market_sentiment_loaded" not in st.session_state:
        try:
            # Inicializar el analizador de señales en tiempo real
            real_time_analyzer = RealTimeSignalAnalyzer()

            # Obtener el sentimiento de mercado
            sentiment_data = real_time_analyzer.get_real_time_market_sentiment()

            # Guardar el sentimiento en la base de datos
            from database_utils import save_market_sentiment

            sentiment_id = save_market_sentiment(sentiment_data)

            if sentiment_id:
                logger.info(
                    f"Sentimiento de mercado diario cargado y almacenado con ID: {sentiment_id}"
                )

                # Ejecutar post_save_quality_check.py para asegurar que todos los campos estén completos
                try:
                    import post_save_quality_check

                    post_save_quality_check.process_quality_after_save(
                        table_name="market_sentiment", limit=1
                    )
                    logger.info(
                        f"Procesamiento de calidad completado para el sentimiento {sentiment_id}"
                    )
                except Exception as e:
                    logger.warning(f"Error en el procesamiento de calidad: {str(e)}")
            else:
                logger.info(
                    "El sentimiento de mercado diario ya existe en la base de datos"
                )

            # Marcar como cargado para no volver a intentarlo
            st.session_state.market_sentiment_loaded = True
        except Exception as e:
            logger.error(
                f"Error al cargar y almacenar el sentimiento de mercado diario: {str(e)}"
            )
            st.session_state.market_sentiment_loaded = False

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📊 Análisis Técnico",
            "🎯 Opciones",
            "⚙️ Multi-Timeframe",
            "🧠 Análisis Experto",
            "📰 Noticias y Sentimiento",
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
            options_manager = MarketUtils()
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
        st.dataframe(api_df.astype(str), use_container_width=True)
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
        st.dataframe(lib_df.astype(str), use_container_width=True)
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
                st.dataframe(test_data.tail(3).astype(str), use_container_width=True)

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
    # Importar get_company_info para asegurar que esté disponible en este ámbito
    from company_data import get_company_info

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
            [
                "📊 Análisis Individual",
                "🔍 Scanner de Mercado",
            ]
        )

        # Inicializar estado de sesión para señales
        if "cached_signals" not in st.session_state:
            st.session_state.cached_signals = []

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

                    # Mantener la parte superior como estaba (información principal)
                    card_html = f"""
                    <div style="background-color:rgba(70,70,70,0.1);padding:15px;border-radius:8px;margin-bottom:15px;border-left:5px solid {signal_color}">
                        <h3 style="margin-top:0; display: flex; justify-content: space-between;">
                            <span>{company_name}</span>
                            <span style="color:{'#4CAF50' if change >= 0 else '#F44336'}">${price:.2f} ({change:+.2f}%)</span>
                        </h3>
                        {strong_signal_block}
                        {option_signal_html}
                    </div>
                    """

                    # Mostrar la primera parte
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Para los parámetros del activo, usar componentes nativos de Streamlit
                    # Título con icono
                    st.markdown("### 📊 Parámetros del Activo")

                    # Obtener parámetros del activo
                    if "options_params" in context:
                        params = context.get("options_params", {})
                    else:
                        try:
                            options_manager = OptionsParameterManager()
                            params = options_manager.get_symbol_params(symbol)
                        except:
                            params = {}

                    # Mostrar parámetros como elementos de Streamlit
                    if params:
                        # Usar método nativo de Streamlit con columnas
                        for key, value in params.items():
                            col1, col2 = st.columns([3, 2])
                            with col1:
                                st.markdown(f"**{key}**")
                            with col2:
                                st.markdown(
                                    f"<div style='text-align:right'>{value}</div>",
                                    unsafe_allow_html=True,
                                )
                    else:
                        st.info("No hay parámetros disponibles para este símbolo")
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
            # Usar el scanner mejorado
            try:
                # Inicializar gestor de señales si no existe
                if "signal_manager" not in locals():
                    signal_manager = SignalManager()

                # Renderizar el scanner mejorado
                # Pasamos SYMBOLS como parámetro adicional para evitar problemas de importación
                render_enhanced_market_scanner(
                    st.session_state.scanner,
                    st.session_state.analyzer,
                    get_market_context,
                    SYMBOLS,  # Pasar SYMBOLS directamente
                )

                # Guardar señales en la base de datos cuando se escanea
                if (
                    "scan_results" in st.session_state
                    and not st.session_state.scan_results.empty
                ):
                    # Verificar si ya se guardaron las señales
                    if (
                        "signals_saved" not in st.session_state
                        or not st.session_state.signals_saved
                    ):
                        with st.spinner("Guardando señales en la base de datos..."):
                            signals_saved = 0
                            for _, row in st.session_state.scan_results.iterrows():
                                try:
                                    # Mapear dirección
                                    direction = (
                                        "CALL"
                                        if row["Estrategia"] == "CALL"
                                        else (
                                            "PUT"
                                            if row["Estrategia"] == "PUT"
                                            else "NEUTRAL"
                                        )
                                    )

                                    # Mapear confianza
                                    confidence = (
                                        row["Confianza"].capitalize()
                                        if isinstance(row["Confianza"], str)
                                        else "Media"
                                    )
                                    if confidence == "Alta" or confidence == "ALTA":
                                        confidence = "Alta"
                                    elif confidence == "Media" or confidence == "MEDIA":
                                        confidence = "Media"
                                    else:
                                        confidence = "Baja"

                                    # Generar análisis técnico si no existe
                                    if "Análisis_Técnico" not in row or not row.get(
                                        "Análisis_Técnico"
                                    ):
                                        technical_analysis = f"El activo {row['Symbol']} muestra una tendencia {row.get('Tendencia', 'NEUTRAL').lower()} "
                                        technical_analysis += f"con fuerza {row.get('Fuerza', 'moderada')}. "
                                        technical_analysis += (
                                            f"RSI en {row.get('RSI', 50):.2f} indica "
                                        )

                                        # Interpretar RSI
                                        rsi_value = row.get("RSI", 50)
                                        if rsi_value < 30:
                                            technical_analysis += (
                                                "condiciones de sobreventa. "
                                            )
                                        elif rsi_value > 70:
                                            technical_analysis += (
                                                "condiciones de sobrecompra. "
                                            )
                                        else:
                                            technical_analysis += (
                                                "condiciones neutras. "
                                            )

                                        # Añadir información de setup
                                        technical_analysis += f"El setup identificado es {row.get('Setup', 'Análisis Técnico')} "
                                        technical_analysis += f"con una relación riesgo/recompensa de {row.get('R/R', 0.0):.2f}."

                                        # Generar niveles de soporte y resistencia si no existen
                                        price = row.get("Precio", 0.0)
                                        if price > 0 and (
                                            row.get("Soporte", 0.0) == 0.0
                                            or row.get("Resistencia", 0.0) == 0.0
                                        ):
                                            # Calcular soporte y resistencia basados en el precio actual y la tendencia
                                            trend = row.get("Tendencia", "NEUTRAL")
                                            if trend == "ALCISTA":
                                                support_level = (
                                                    price * 0.95
                                                )  # 5% por debajo del precio actual
                                                resistance_level = (
                                                    price * 1.10
                                                )  # 10% por encima del precio actual
                                            elif trend == "BAJISTA":
                                                support_level = (
                                                    price * 0.90
                                                )  # 10% por debajo del precio actual
                                                resistance_level = (
                                                    price * 1.05
                                                )  # 5% por encima del precio actual
                                            else:  # NEUTRAL
                                                support_level = (
                                                    price * 0.97
                                                )  # 3% por debajo del precio actual
                                                resistance_level = (
                                                    price * 1.03
                                                )  # 3% por encima del precio actual

                                            technical_analysis += f" Niveles clave: Soporte en ${support_level:.2f} y resistencia en ${resistance_level:.2f}."
                                        else:
                                            support_level = row.get("Soporte", 0.0)
                                            resistance_level = row.get(
                                                "Resistencia", 0.0
                                            )
                                    else:
                                        technical_analysis = row.get(
                                            "Análisis_Técnico", ""
                                        )

                                    # Generar análisis de opciones si no existe
                                    if "Options_Analysis" not in row or not row.get(
                                        "Options_Analysis"
                                    ):
                                        # Generar volatilidad si no existe
                                        if (
                                            "Volatilidad" not in row
                                            or row.get("Volatilidad", 0) == 0
                                        ):
                                            # Estimar volatilidad basada en el sector y la tendencia
                                            sector = row.get("Sector", "")
                                            trend = row.get("Tendencia", "NEUTRAL")

                                            # Valores base de volatilidad por sector
                                            sector_volatility = {
                                                "Tecnología": 35.0,
                                                "Finanzas": 25.0,
                                                "Salud": 30.0,
                                                "Energía": 40.0,
                                                "Consumo": 20.0,
                                                "Volatilidad": 60.0,
                                                "Materias Primas": 35.0,
                                                "Comunicaciones": 28.0,
                                                "Industrial": 27.0,
                                                "Servicios": 22.0,
                                                "Utilidades": 18.0,
                                                "Inmobiliario": 23.0,
                                                "Índices": 20.0,
                                            }

                                            # Obtener volatilidad base del sector o valor predeterminado
                                            base_volatility = sector_volatility.get(
                                                sector, 30.0
                                            )

                                            # Ajustar por tendencia
                                            if (
                                                trend == "ALCISTA"
                                                and row.get("Fuerza", "") == "fuerte"
                                            ):
                                                volatility = (
                                                    base_volatility * 0.8
                                                )  # Menos volatilidad en tendencia alcista fuerte
                                            elif (
                                                trend == "BAJISTA"
                                                and row.get("Fuerza", "") == "fuerte"
                                            ):
                                                volatility = (
                                                    base_volatility * 1.3
                                                )  # Más volatilidad en tendencia bajista fuerte
                                            elif trend == "NEUTRAL":
                                                volatility = (
                                                    base_volatility * 1.1
                                                )  # Ligeramente más volatilidad en mercado neutral
                                            else:
                                                volatility = base_volatility

                                            # Ajustar por RSI
                                            rsi = row.get("RSI", 50)
                                            if rsi < 30 or rsi > 70:
                                                volatility *= 1.2  # Mayor volatilidad en condiciones extremas
                                        else:
                                            volatility = row.get("Volatilidad", 30.0)

                                        # Generar señal de opciones si no existe
                                        if "Options_Signal" not in row or not row.get(
                                            "Options_Signal"
                                        ):
                                            if direction == "CALL":
                                                if volatility > 40:
                                                    options_signal = "CALL SPREAD"  # Menos riesgo en alta volatilidad
                                                else:
                                                    options_signal = "CALL DIRECTO"
                                            elif direction == "PUT":
                                                if volatility > 40:
                                                    options_signal = "PUT SPREAD"  # Menos riesgo en alta volatilidad
                                                else:
                                                    options_signal = "PUT DIRECTO"
                                            else:
                                                if volatility > 35:
                                                    options_signal = "IRON CONDOR"  # Estrategia neutral para alta volatilidad
                                                else:
                                                    options_signal = "BUTTERFLY"
                                        else:
                                            options_signal = row.get(
                                                "Options_Signal", ""
                                            )

                                        # Generar análisis de opciones
                                        options_analysis = f"La volatilidad implícita de {row['Symbol']} es del {volatility:.2f}%, "
                                        if volatility > 50:
                                            options_analysis += "lo que indica alta incertidumbre en el mercado. "
                                        elif volatility > 30:
                                            options_analysis += (
                                                "lo que indica volatilidad moderada. "
                                            )
                                        else:
                                            options_analysis += (
                                                "lo que indica baja volatilidad. "
                                            )

                                        options_analysis += f"El análisis de opciones sugiere una estrategia {options_signal}. "

                                        # Añadir recomendaciones específicas basadas en la estrategia
                                        if options_signal == "CALL DIRECTO":
                                            options_analysis += f"Considerar compra de calls con strike cercano a ${row.get('Precio', 0.0):.2f} "
                                            options_analysis += (
                                                "con vencimiento de 30-45 días."
                                            )
                                        elif options_signal == "PUT DIRECTO":
                                            options_analysis += f"Considerar compra de puts con strike cercano a ${row.get('Precio', 0.0):.2f} "
                                            options_analysis += (
                                                "con vencimiento de 30-45 días."
                                            )
                                        elif "SPREAD" in options_signal:
                                            options_analysis += "Esta estrategia limita el riesgo y la recompensa, "
                                            options_analysis += "ideal para entornos de alta volatilidad."
                                        elif options_signal in [
                                            "IRON CONDOR",
                                            "BUTTERFLY",
                                        ]:
                                            options_analysis += "Estrategia neutral que se beneficia de baja volatilidad "
                                            options_analysis += (
                                                "o movimiento lateral del precio."
                                            )
                                    else:
                                        options_analysis = row.get(
                                            "Options_Analysis", ""
                                        )
                                        volatility = row.get("Volatilidad", 30.0)
                                        options_signal = row.get("Options_Signal", "")

                                    # Generar análisis multi-timeframe si no existe
                                    if "MTF_Analysis" not in row or not row.get(
                                        "MTF_Analysis"
                                    ):
                                        mtf_analysis = f"Análisis de {row['Symbol']} en múltiples marcos temporales: "

                                        # Tendencias por timeframe
                                        daily_trend = "NEUTRAL"
                                        weekly_trend = "NEUTRAL"
                                        monthly_trend = "NEUTRAL"

                                        # Determinar tendencias basadas en la tendencia principal y la fuerza
                                        main_trend = row.get("Tendencia", "NEUTRAL")
                                        strength = row.get("Fuerza", "moderada")

                                        if main_trend == "ALCISTA":
                                            if strength == "fuerte":
                                                daily_trend = "ALCISTA"
                                                weekly_trend = "ALCISTA"
                                                monthly_trend = "NEUTRAL"
                                            elif strength == "moderada":
                                                daily_trend = "ALCISTA"
                                                weekly_trend = "NEUTRAL"
                                                monthly_trend = "NEUTRAL"
                                            else:
                                                daily_trend = "ALCISTA"
                                                weekly_trend = "NEUTRAL"
                                                monthly_trend = "BAJISTA"
                                        elif main_trend == "BAJISTA":
                                            if strength == "fuerte":
                                                daily_trend = "BAJISTA"
                                                weekly_trend = "BAJISTA"
                                                monthly_trend = "NEUTRAL"
                                            elif strength == "moderada":
                                                daily_trend = "BAJISTA"
                                                weekly_trend = "NEUTRAL"
                                                monthly_trend = "NEUTRAL"
                                            else:
                                                daily_trend = "BAJISTA"
                                                weekly_trend = "NEUTRAL"
                                                monthly_trend = "ALCISTA"

                                        mtf_analysis += f"Diario: {daily_trend}, Semanal: {weekly_trend}, Mensual: {monthly_trend}. "

                                        # Añadir recomendación basada en tendencias
                                        if (
                                            daily_trend == weekly_trend
                                            and daily_trend != "NEUTRAL"
                                        ):
                                            mtf_analysis += f"Confirmación de tendencia {daily_trend.lower()} en múltiples timeframes."
                                        elif (
                                            daily_trend != weekly_trend
                                            and daily_trend != "NEUTRAL"
                                            and weekly_trend != "NEUTRAL"
                                        ):
                                            mtf_analysis += "Divergencia entre timeframes, se recomienda cautela."
                                        else:
                                            mtf_analysis += "Sin tendencia clara en múltiples timeframes."
                                    else:
                                        mtf_analysis = row.get("MTF_Analysis", "")
                                        daily_trend = row.get(
                                            "Tendencia_Diario", "NEUTRAL"
                                        )
                                        weekly_trend = row.get(
                                            "Tendencia_Semanal", "NEUTRAL"
                                        )
                                        monthly_trend = row.get(
                                            "Tendencia_Mensual", "NEUTRAL"
                                        )

                                    # Generar análisis experto si no existe
                                    if "Análisis_Experto" not in row or not row.get(
                                        "Análisis_Experto"
                                    ):
                                        expert_analysis = (
                                            f"Análisis experto para {row['Symbol']}: "
                                        )

                                        # Determinar recomendación basada en la dirección y confianza
                                        if direction == "CALL" and confidence == "Alta":
                                            recommendation = "COMPRAR"
                                            expert_analysis += "Se recomienda COMPRAR basado en fuerte señal alcista. "
                                        elif (
                                            direction == "PUT" and confidence == "Alta"
                                        ):
                                            recommendation = "VENDER"
                                            expert_analysis += "Se recomienda VENDER basado en fuerte señal bajista. "
                                        elif direction == "CALL":
                                            recommendation = "MANTENER/COMPRAR"
                                            expert_analysis += "Se recomienda MANTENER/COMPRAR con cautela. "
                                        elif direction == "PUT":
                                            recommendation = "MANTENER/VENDER"
                                            expert_analysis += "Se recomienda MANTENER/VENDER con cautela. "
                                        else:
                                            recommendation = "MANTENER"
                                            expert_analysis += "Se recomienda MANTENER y esperar mejor configuración. "

                                        # Añadir información de Trading Specialist si está disponible
                                        if (
                                            "Trading_Specialist" in row
                                            and row.get("Trading_Specialist")
                                            != "NEUTRAL"
                                        ):
                                            expert_analysis += f"El Trading Specialist indica {row.get('Trading_Specialist', '')} "
                                            expert_analysis += f"con confianza {row.get('TS_Confianza', 'MEDIA')}. "

                                        # Añadir información de riesgo/recompensa
                                        rr = row.get("R/R", 0.0)
                                        if rr > 3:
                                            expert_analysis += f"Excelente relación riesgo/recompensa de {rr:.2f}."
                                        elif rr > 2:
                                            expert_analysis += f"Buena relación riesgo/recompensa de {rr:.2f}."
                                        elif rr > 1:
                                            expert_analysis += f"Aceptable relación riesgo/recompensa de {rr:.2f}."
                                        else:
                                            expert_analysis += f"Baja relación riesgo/recompensa de {rr:.2f}, se recomienda cautela."
                                    else:
                                        expert_analysis = row.get(
                                            "Análisis_Experto", ""
                                        )
                                        recommendation = row.get("Recomendación", "")

                                    # Generar indicadores alcistas/bajistas si no existen
                                    if (
                                        "Indicadores_Alcistas" not in row
                                        or not row.get("Indicadores_Alcistas")
                                    ):
                                        # Indicadores alcistas básicos basados en RSI y tendencia
                                        bullish_indicators = []
                                        if row.get("RSI", 50) < 30:
                                            bullish_indicators.append(
                                                "RSI en sobreventa"
                                            )
                                        if row.get("Tendencia", "NEUTRAL") == "ALCISTA":
                                            bullish_indicators.append(
                                                "Tendencia alcista"
                                            )
                                        if (
                                            row.get("Precio", 0) > row.get("Soporte", 0)
                                            and row.get("Soporte", 0) > 0
                                        ):
                                            bullish_indicators.append(
                                                "Precio por encima del soporte"
                                            )

                                        bullish_indicators_str = (
                                            ", ".join(bullish_indicators)
                                            if bullish_indicators
                                            else "No se detectaron indicadores alcistas significativos"
                                        )
                                    else:
                                        bullish_indicators_str = row.get(
                                            "Indicadores_Alcistas", ""
                                        )

                                    if (
                                        "Indicadores_Bajistas" not in row
                                        or not row.get("Indicadores_Bajistas")
                                    ):
                                        # Indicadores bajistas básicos basados en RSI y tendencia
                                        bearish_indicators = []
                                        if row.get("RSI", 50) > 70:
                                            bearish_indicators.append(
                                                "RSI en sobrecompra"
                                            )
                                        if row.get("Tendencia", "NEUTRAL") == "BAJISTA":
                                            bearish_indicators.append(
                                                "Tendencia bajista"
                                            )
                                        if (
                                            row.get("Precio", 0)
                                            < row.get("Resistencia", 0)
                                            and row.get("Resistencia", 0) > 0
                                        ):
                                            bearish_indicators.append(
                                                "Precio por debajo de la resistencia"
                                            )

                                        bearish_indicators_str = (
                                            ", ".join(bearish_indicators)
                                            if bearish_indicators
                                            else "No se detectaron indicadores bajistas significativos"
                                        )
                                    else:
                                        bearish_indicators_str = row.get(
                                            "Indicadores_Bajistas", ""
                                        )

                                    # Crear señal con información detallada
                                    signal = {
                                        # Campos básicos
                                        "symbol": row["Symbol"],
                                        "price": (
                                            row["Precio"]
                                            if isinstance(row["Precio"], (int, float))
                                            else 0.0
                                        ),
                                        "direction": direction,
                                        "confidence_level": confidence,
                                        "timeframe": "Medio Plazo",
                                        "strategy": row.get("Estrategia", "NEUTRAL"),
                                        "category": row["Sector"],
                                        "analysis": f"Señal {direction} con confianza {confidence}. RSI: {row.get('RSI', 'N/A')}. R/R: {row.get('R/R', 'N/A')}",
                                        "created_at": datetime.now(),
                                        # Campos adicionales para niveles de trading
                                        "entry_price": row.get(
                                            "Entry", row.get("Precio", 0.0)
                                        ),
                                        "stop_loss": (
                                            row.get("Stop", 0.0)
                                            if row.get("Stop", 0.0) > 0
                                            else (
                                                # Calcular stop loss si no existe
                                                row.get("Precio", 0.0) * 1.02
                                                if direction
                                                == "PUT"  # 2% arriba para PUT
                                                else (
                                                    row.get("Precio", 0.0) * 0.98
                                                    if direction
                                                    == "CALL"  # 2% abajo para CALL
                                                    else 0.0
                                                )
                                            )
                                        ),
                                        "target_price": (
                                            row.get("Target", 0.0)
                                            if row.get("Target", 0.0) > 0
                                            else (
                                                # Calcular target price si no existe
                                                row.get("Precio", 0.0) * 0.95
                                                if direction
                                                == "PUT"  # 5% abajo para PUT
                                                else (
                                                    row.get("Precio", 0.0) * 1.05
                                                    if direction
                                                    == "CALL"  # 5% arriba para CALL
                                                    else 0.0
                                                )
                                            )
                                        ),
                                        "risk_reward": (
                                            row.get("R/R", 0.0)
                                            if row.get("R/R", 0.0) > 0
                                            else (
                                                # Calcular R/R si no existe y tenemos stop y target
                                                abs(
                                                    (
                                                        row.get("Precio", 0.0)
                                                        - (
                                                            row.get("Precio", 0.0)
                                                            * 0.95
                                                        )
                                                    )
                                                    / (
                                                        row.get("Precio", 0.0)
                                                        - (
                                                            row.get("Precio", 0.0)
                                                            * 1.02
                                                        )
                                                    )
                                                )
                                                if direction == "PUT"
                                                else (
                                                    abs(
                                                        (
                                                            row.get("Precio", 0.0)
                                                            * 1.05
                                                            - row.get("Precio", 0.0)
                                                        )
                                                        / (
                                                            row.get("Precio", 0.0)
                                                            - (
                                                                row.get("Precio", 0.0)
                                                                * 0.98
                                                            )
                                                        )
                                                    )
                                                    if direction == "CALL"
                                                    else 1.0
                                                )
                                            )
                                        ),
                                        "setup_type": row.get(
                                            "Setup", f"Estrategia {direction} genérica"
                                        ),
                                        # Campos para análisis técnico
                                        "technical_analysis": technical_analysis,
                                        "support_level": (
                                            support_level
                                            if "support_level" in locals()
                                            else row.get("Soporte", 0.0)
                                        ),
                                        "resistance_level": (
                                            resistance_level
                                            if "resistance_level" in locals()
                                            else row.get("Resistencia", 0.0)
                                        ),
                                        "rsi": row.get("RSI", 0.0),
                                        "trend": row.get("Tendencia", "NEUTRAL"),
                                        "trend_strength": row.get("Fuerza", "moderada"),
                                        # Campos para opciones
                                        "volatility": (
                                            volatility
                                            if "volatility" in locals()
                                            else row.get("Volatilidad", 0.0)
                                        ),
                                        "options_signal": (
                                            options_signal
                                            if "options_signal" in locals()
                                            else row.get("Options_Signal", "")
                                        ),
                                        "options_analysis": options_analysis,
                                        # Campos para Trading Specialist
                                        "trading_specialist_signal": row.get(
                                            "Trading_Specialist", "NEUTRAL"
                                        ),
                                        "trading_specialist_confidence": row.get(
                                            "TS_Confianza", "MEDIA"
                                        ),
                                        # Campos para sentimiento y noticias
                                        "sentiment": row.get("Sentimiento", "neutral"),
                                        "sentiment_score": row.get(
                                            "Sentimiento_Score", 0.5
                                        ),
                                        "latest_news": row.get("Última_Noticia", "")
                                        or (
                                            # Generar noticia si no existe
                                            f"Análisis técnico muestra {row.get('Tendencia', 'NEUTRAL').lower()} para {row['Symbol']} con RSI en {row.get('RSI', 50):.2f}"
                                        ),
                                        "news_source": row.get("Fuente_Noticia", "")
                                        or "InversorIA Analytics",
                                        "additional_news": row.get(
                                            "Noticias_Adicionales", ""
                                        )
                                        or (
                                            # Generar noticias adicionales si no existen
                                            f"El activo {row['Symbol']} del sector {row['Sector']} muestra una tendencia {row.get('Tendencia', 'NEUTRAL').lower()} "
                                            + f"con una relación riesgo/recompensa de {row.get('R/R', 1.0):.2f}. "
                                            + (
                                                "Se recomienda cautela debido a la volatilidad del mercado."
                                                if volatility > 35
                                                else "Las condiciones de mercado son favorables para esta operación."
                                            )
                                        ),
                                        # Campos para análisis experto y multi-timeframe
                                        "expert_analysis": expert_analysis,
                                        "recommendation": (
                                            recommendation
                                            if "recommendation" in locals()
                                            else ""
                                        ),
                                        "mtf_analysis": mtf_analysis,
                                        "daily_trend": daily_trend,
                                        "weekly_trend": weekly_trend,
                                        "monthly_trend": monthly_trend,
                                        "bullish_indicators": bullish_indicators_str,
                                        "bearish_indicators": bearish_indicators_str,
                                        # Indicador de alta confianza
                                        "is_high_confidence": confidence == "Alta"
                                        or (
                                            row.get("Trading_Specialist", "NEUTRAL")
                                            in ["COMPRA", "VENTA"]
                                            and row.get("TS_Confianza", "") == "ALTA"
                                        ),
                                    }

                                    # Verificar si la señal ya existe en la base de datos
                                    existing_signals = signal_manager.db_manager.execute_query(
                                        "SELECT id FROM trading_signals WHERE symbol = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)",
                                        [signal["symbol"]],
                                    )

                                    # Verificar que la señal tenga toda la información necesaria antes de guardarla
                                    is_complete = True

                                    # Verificar campos críticos
                                    required_fields = [
                                        "technical_analysis",
                                        "expert_analysis",
                                        "mtf_analysis",
                                        "options_analysis",
                                        "bullish_indicators",
                                        "bearish_indicators",
                                    ]

                                    for field in required_fields:
                                        if not signal.get(field):
                                            is_complete = False
                                            logger.warning(
                                                f"Señal para {signal['symbol']} incompleta: falta {field}"
                                            )

                                    # Verificar que tenga información de noticias y sentimiento
                                    if not signal.get("latest_news") or not signal.get(
                                        "sentiment"
                                    ):
                                        # Intentar obtener noticias y sentimiento actualizados
                                        try:
                                            from news_sentiment_analyzer import (
                                                NewsSentimentAnalyzer,
                                            )

                                            news_analyzer = NewsSentimentAnalyzer()
                                            fresh_news_sentiment = news_analyzer.get_consolidated_news_and_sentiment(
                                                signal["symbol"],
                                                row.get(
                                                    "company_name", signal["symbol"]
                                                ),
                                            )

                                            if fresh_news_sentiment:
                                                if (
                                                    "news" in fresh_news_sentiment
                                                    and fresh_news_sentiment["news"]
                                                ):
                                                    latest_news = fresh_news_sentiment[
                                                        "news"
                                                    ][0]
                                                    signal["latest_news"] = (
                                                        latest_news.get("title", "")
                                                    )
                                                    signal["news_source"] = (
                                                        latest_news.get("source", "")
                                                    )

                                                    # Agregar noticias adicionales
                                                    additional_news = "\n".join(
                                                        [
                                                            news.get("title", "")
                                                            for news in fresh_news_sentiment[
                                                                "news"
                                                            ][
                                                                1:3
                                                            ]
                                                        ]
                                                    )
                                                    if additional_news:
                                                        signal["additional_news"] = (
                                                            additional_news
                                                        )

                                                if "sentiment" in fresh_news_sentiment:
                                                    sentiment_data = (
                                                        fresh_news_sentiment[
                                                            "sentiment"
                                                        ]
                                                    )
                                                    signal["sentiment"] = (
                                                        sentiment_data.get(
                                                            "sentiment", "neutral"
                                                        )
                                                    )
                                                    signal["sentiment_score"] = (
                                                        sentiment_data.get("score", 0.5)
                                                    )
                                        except Exception as e:
                                            logger.warning(
                                                f"No se pudo obtener noticias actualizadas: {str(e)}"
                                            )

                                    # Procesar la señal con ai_utils para mejorar la calidad de la información
                                    try:
                                        # Importar utilidades de IA
                                        from ai_utils import (
                                            process_expert_analysis,
                                            process_content_with_ai,
                                        )
                                        from company_data import get_company_info

                                        # Obtener información completa de la empresa
                                        company_info = get_company_info(
                                            signal["symbol"]
                                        )
                                        company_name = company_info.get(
                                            "name", signal["symbol"]
                                        )
                                        company_description = company_info.get(
                                            "description", ""
                                        )

                                        # Añadir información de la empresa a la señal
                                        signal["company_name"] = company_name
                                        signal["company_description"] = (
                                            company_description
                                        )

                                        # Obtener parámetros de opciones si están disponibles
                                        try:
                                            from market_utils import MarketUtils

                                            options_manager = MarketUtils()
                                            options_params = (
                                                options_manager.get_symbol_params(
                                                    signal["symbol"]
                                                )
                                            )

                                            if options_params:
                                                signal["options_params"] = (
                                                    options_params
                                                )
                                                signal["costo_strike"] = (
                                                    options_params.get(
                                                        "costo_strike", "N/A"
                                                    )
                                                )
                                                signal["volumen_min"] = (
                                                    options_params.get(
                                                        "volumen_min", "N/A"
                                                    )
                                                )
                                                signal["distance_spot_strike"] = (
                                                    options_params.get(
                                                        "distance_spot_strike", "N/A"
                                                    )
                                                )
                                        except Exception as options_error:
                                            logger.warning(
                                                f"Error obteniendo parámetros de opciones: {str(options_error)}"
                                            )

                                        # Obtener contexto de mercado para el símbolo
                                        try:
                                            # Usar la función get_market_context ya importada al inicio del archivo
                                            context = get_market_context(
                                                signal["symbol"]
                                            )
                                        except Exception as context_error:
                                            logger.warning(
                                                f"Error obteniendo contexto de mercado: {str(context_error)}"
                                            )
                                            context = {
                                                "symbol": signal["symbol"],
                                                "last_price": signal.get("price", 0),
                                                "change_percent": 0,
                                                "signals": {},
                                            }

                                        # Si tenemos acceso a OpenAI, procesar con el experto
                                        if (
                                            "openai" in sys.modules
                                            and st.session_state.get("openai_api_key")
                                        ):
                                            import openai

                                            client = openai.OpenAI(
                                                api_key=st.session_state.get(
                                                    "openai_api_key"
                                                )
                                            )

                                            # Obtener ID del asistente
                                            assistant_id = st.session_state.get(
                                                "assistant_id"
                                            )

                                            if client and assistant_id and context:
                                                # Mostrar mensaje de procesamiento
                                                processing_msg = st.info(
                                                    f"Procesando análisis experto para {signal['symbol']}..."
                                                )

                                                # Procesar análisis experto
                                                expert_analysis = (
                                                    process_expert_analysis(
                                                        client,
                                                        assistant_id,
                                                        signal["symbol"],
                                                        context,
                                                    )
                                                )

                                                if (
                                                    expert_analysis
                                                    and len(expert_analysis) > 100
                                                ):
                                                    # Actualizar campos de la señal con el análisis experto
                                                    signal["expert_analysis"] = (
                                                        expert_analysis
                                                    )

                                                    # Mejorar otros campos de texto con IA si están disponibles
                                                    if signal.get("analysis"):
                                                        signal["analysis"] = (
                                                            process_content_with_ai(
                                                                client,
                                                                assistant_id,
                                                                "analysis",
                                                                signal["analysis"],
                                                                signal["symbol"],
                                                                f"Precio: ${signal.get('price', 0)}, Tendencia: {signal.get('trend', 'NEUTRAL')}",
                                                            )
                                                        )

                                                    if signal.get("technical_analysis"):
                                                        signal["technical_analysis"] = (
                                                            process_content_with_ai(
                                                                client,
                                                                assistant_id,
                                                                "technical_analysis",
                                                                signal[
                                                                    "technical_analysis"
                                                                ],
                                                                signal["symbol"],
                                                                f"RSI: {signal.get('rsi', 'N/A')}, MACD: {signal.get('macd', 'N/A')}, Soporte: {signal.get('support', 'N/A')}, Resistencia: {signal.get('resistance', 'N/A')}",
                                                            )
                                                        )

                                                    # Extraer recomendación final
                                                    if (
                                                        "RECOMENDACIÓN FINAL"
                                                        in expert_analysis
                                                    ):
                                                        recommendation_section = (
                                                            expert_analysis.split(
                                                                "RECOMENDACIÓN FINAL"
                                                            )[1].strip()
                                                        )
                                                        if (
                                                            "CALL"
                                                            in recommendation_section.upper()
                                                        ):
                                                            signal["recommendation"] = (
                                                                "COMPRAR"
                                                            )
                                                        elif (
                                                            "PUT"
                                                            in recommendation_section.upper()
                                                        ):
                                                            signal["recommendation"] = (
                                                                "VENDER"
                                                            )
                                                        else:
                                                            signal["recommendation"] = (
                                                                "MANTENER"
                                                            )

                                                # Eliminar mensaje de procesamiento
                                                processing_msg.empty()
                                    except Exception as ai_error:
                                        logger.warning(
                                            f"Error procesando análisis experto: {str(ai_error)}"
                                        )

                                    # Guardar la señal (permitir múltiples señales del mismo símbolo si la información está completa)
                                    if is_complete:
                                        try:
                                            # Guardar señal en la base de datos
                                            signal_id = (
                                                signal_manager.db_manager.save_signal(
                                                    signal
                                                )
                                            )
                                            if signal_id:
                                                signals_saved += 1
                                                logger.info(
                                                    f"Señal guardada para {signal['symbol']} con ID: {signal_id}"
                                                )
                                                # Acumular mensaje de éxito para mostrar al final
                                                if (
                                                    "saved_signals_info"
                                                    not in st.session_state
                                                ):
                                                    st.session_state.saved_signals_info = (
                                                        []
                                                    )

                                                st.session_state.saved_signals_info.append(
                                                    {
                                                        "symbol": signal["symbol"],
                                                        "id": signal_id,
                                                        "news_count": 0,  # Se actualizará después
                                                    }
                                                )

                                                # Guardar noticias (pero no sentimiento de mercado, ya que se carga al inicio)
                                                try:
                                                    # Usar database_utils en lugar de market_data_manager (que se movió a legacy_code)
                                                    from database_utils import (
                                                        save_market_news,
                                                        save_trading_signal,
                                                    )

                                                    # Procesar noticias con IA para mejorar calidad y asegurar fuentes confiables
                                                    news_ids = []
                                                    if (
                                                        signal.get("news")
                                                        and client
                                                        and assistant_id
                                                    ):
                                                        processed_news = []
                                                        for news_item in signal.get(
                                                            "news", []
                                                        ):
                                                            # Verificar si la noticia tiene URL y fuente
                                                            if (
                                                                not news_item.get("url")
                                                                or news_item.get("url")
                                                                == "#"
                                                            ):
                                                                # Buscar URL para la noticia
                                                                try:
                                                                    from news_sentiment_analyzer import (
                                                                        NewsSentimentAnalyzer,
                                                                    )

                                                                    news_analyzer = (
                                                                        NewsSentimentAnalyzer()
                                                                    )
                                                                    search_query = f"{signal['symbol']} {news_item.get('title', '')}"
                                                                    search_results = news_analyzer.get_news_from_web_search(
                                                                        search_query,
                                                                        signal.get(
                                                                            "company_name",
                                                                            "",
                                                                        ),
                                                                    )

                                                                    if (
                                                                        search_results
                                                                        and len(
                                                                            search_results
                                                                        )
                                                                        > 0
                                                                    ):
                                                                        # Encontrar la noticia más similar
                                                                        for (
                                                                            result
                                                                        ) in search_results:
                                                                            if (
                                                                                news_item.get(
                                                                                    "title",
                                                                                    "",
                                                                                ).lower()
                                                                                in result.get(
                                                                                    "title",
                                                                                    "",
                                                                                ).lower()
                                                                                or result.get(
                                                                                    "title",
                                                                                    "",
                                                                                ).lower()
                                                                                in news_item.get(
                                                                                    "title",
                                                                                    "",
                                                                                ).lower()
                                                                            ):
                                                                                news_item[
                                                                                    "url"
                                                                                ] = result.get(
                                                                                    "url",
                                                                                    news_item.get(
                                                                                        "url",
                                                                                        "#",
                                                                                    ),
                                                                                )
                                                                                news_item[
                                                                                    "source"
                                                                                ] = result.get(
                                                                                    "source",
                                                                                    news_item.get(
                                                                                        "source",
                                                                                        "Desconocida",
                                                                                    ),
                                                                                )
                                                                                break
                                                                except (
                                                                    Exception
                                                                ) as search_error:
                                                                    logger.warning(
                                                                        f"Error buscando URL para noticia: {str(search_error)}"
                                                                    )

                                                            # Mejorar contenido de la noticia con IA
                                                            if news_item.get(
                                                                "title"
                                                            ) and news_item.get(
                                                                "summary"
                                                            ):
                                                                improved_summary = process_content_with_ai(
                                                                    client,
                                                                    assistant_id,
                                                                    "news",
                                                                    news_item.get(
                                                                        "summary", ""
                                                                    ),
                                                                    signal["symbol"],
                                                                    f"Título: {news_item.get('title', '')}, Fuente: {news_item.get('source', 'Desconocida')}",
                                                                )
                                                                news_item["summary"] = (
                                                                    improved_summary
                                                                )

                                                            processed_news.append(
                                                                news_item
                                                            )

                                                        # Actualizar noticias en la señal
                                                        signal["news"] = processed_news

                                                    # Guardar noticias
                                                    news_ids = []
                                                    if market_data_mgr:
                                                        news_ids = market_data_mgr.save_news_from_signal(
                                                            signal
                                                        )
                                                    else:
                                                        # Alternativa usando database_utils directamente
                                                        try:
                                                            from database_utils import (
                                                                save_market_news,
                                                            )

                                                            # Guardar noticias si están disponibles
                                                            if signal.get(
                                                                "news"
                                                            ) and isinstance(
                                                                signal.get("news"), list
                                                            ):
                                                                for (
                                                                    news_item
                                                                ) in signal.get(
                                                                    "news", []
                                                                ):
                                                                    if isinstance(
                                                                        news_item, dict
                                                                    ) and news_item.get(
                                                                        "title"
                                                                    ):
                                                                        news_data = {
                                                                            "title": news_item.get(
                                                                                "title",
                                                                                "",
                                                                            ),
                                                                            "summary": news_item.get(
                                                                                "summary",
                                                                                news_item.get(
                                                                                    "description",
                                                                                    "",
                                                                                ),
                                                                            ),
                                                                            "source": news_item.get(
                                                                                "source",
                                                                                "Fuente Financiera",
                                                                            ),
                                                                            "url": news_item.get(
                                                                                "url",
                                                                                "",
                                                                            ),
                                                                            "news_date": datetime.now(),
                                                                            "impact": "Medio",
                                                                        }
                                                                        news_id = save_market_news(
                                                                            news_data
                                                                        )
                                                                        if news_id:
                                                                            news_ids.append(
                                                                                news_id
                                                                            )

                                                            # Si no hay noticias en la lista, intentar con latest_news
                                                            if (
                                                                not news_ids
                                                                and signal.get(
                                                                    "latest_news"
                                                                )
                                                            ):
                                                                news_data = {
                                                                    "title": signal.get(
                                                                        "latest_news",
                                                                        "",
                                                                    ),
                                                                    "summary": signal.get(
                                                                        "analysis", ""
                                                                    ),
                                                                    "source": signal.get(
                                                                        "news_source",
                                                                        "InversorIA Analytics",
                                                                    ),
                                                                    "url": "",
                                                                    "news_date": datetime.now(),
                                                                    "impact": "Medio",
                                                                }
                                                                news_id = (
                                                                    save_market_news(
                                                                        news_data
                                                                    )
                                                                )
                                                                if news_id:
                                                                    news_ids.append(
                                                                        news_id
                                                                    )
                                                        except Exception as news_error:
                                                            logger.warning(
                                                                f"No se pudieron guardar noticias para {signal.get('symbol', '')}: {str(news_error)}"
                                                            )
                                                    if news_ids:
                                                        logger.info(
                                                            f"Noticias guardadas para {signal['symbol']}: {len(news_ids)} registros"
                                                        )
                                                        # Actualizar contador de noticias en la información de señales guardadas
                                                        if (
                                                            "saved_signals_info"
                                                            in st.session_state
                                                            and st.session_state.saved_signals_info
                                                        ):
                                                            for i, info in enumerate(
                                                                st.session_state.saved_signals_info
                                                            ):
                                                                if (
                                                                    info["symbol"]
                                                                    == signal["symbol"]
                                                                    and info["id"]
                                                                    == signal_id
                                                                ):
                                                                    st.session_state.saved_signals_info[
                                                                        i
                                                                    ][
                                                                        "news_count"
                                                                    ] = len(
                                                                        news_ids
                                                                    )
                                                                    break

                                                    # Guardar sentimiento si es una señal de alta confianza o si tiene sentimiento
                                                    if signal.get(
                                                        "is_high_confidence"
                                                    ) or signal.get("sentiment"):
                                                        # Mejorar el sentimiento con IA si está disponible
                                                        if (
                                                            signal.get("sentiment")
                                                            and client
                                                            and assistant_id
                                                        ):
                                                            sentiment_context = f"Símbolo: {signal['symbol']}, Precio: ${signal.get('price', 0)}, Tendencia: {signal.get('trend', 'NEUTRAL')}"
                                                            sentiment_data = {
                                                                "sentiment": signal.get(
                                                                    "sentiment",
                                                                    "neutral",
                                                                ),
                                                                "score": signal.get(
                                                                    "sentiment_score",
                                                                    0.5,
                                                                ),
                                                                "positive_mentions": signal.get(
                                                                    "positive_mentions",
                                                                    0,
                                                                ),
                                                                "negative_mentions": signal.get(
                                                                    "negative_mentions",
                                                                    0,
                                                                ),
                                                            }

                                                            # Convertir a JSON para procesamiento
                                                            sentiment_json = json.dumps(
                                                                sentiment_data
                                                            )
                                                            improved_sentiment = (
                                                                process_content_with_ai(
                                                                    client,
                                                                    assistant_id,
                                                                    "sentiment",
                                                                    sentiment_json,
                                                                    signal["symbol"],
                                                                    sentiment_context,
                                                                )
                                                            )

                                                            # Intentar parsear el resultado mejorado
                                                            try:
                                                                # Usar la función safe_json_loads de utils/data_utils.py
                                                                from utils.data_utils import (
                                                                    safe_json_loads,
                                                                )

                                                                improved_data = safe_json_loads(
                                                                    improved_sentiment,
                                                                    default={},
                                                                )
                                                                if not improved_data:
                                                                    logger.warning(
                                                                        "No se pudo decodificar JSON, usando diccionario vacío"
                                                                    )
                                                                if (
                                                                    isinstance(
                                                                        improved_data,
                                                                        dict,
                                                                    )
                                                                    and "sentiment"
                                                                    in improved_data
                                                                ):
                                                                    signal[
                                                                        "sentiment"
                                                                    ] = improved_data.get(
                                                                        "sentiment",
                                                                        signal.get(
                                                                            "sentiment",
                                                                            "neutral",
                                                                        ),
                                                                    )
                                                                    signal[
                                                                        "sentiment_score"
                                                                    ] = improved_data.get(
                                                                        "score",
                                                                        signal.get(
                                                                            "sentiment_score",
                                                                            0.5,
                                                                        ),
                                                                    )
                                                                    signal[
                                                                        "positive_mentions"
                                                                    ] = improved_data.get(
                                                                        "positive_mentions",
                                                                        signal.get(
                                                                            "positive_mentions",
                                                                            0,
                                                                        ),
                                                                    )
                                                                    signal[
                                                                        "negative_mentions"
                                                                    ] = improved_data.get(
                                                                        "negative_mentions",
                                                                        signal.get(
                                                                            "negative_mentions",
                                                                            0,
                                                                        ),
                                                                    )
                                                            except (
                                                                Exception
                                                            ) as json_error:
                                                                logger.warning(
                                                                    f"Error procesando JSON de sentimiento: {str(json_error)}"
                                                                )
                                                                # Inicializar sentiment_data con valores por defecto
                                                                sentiment_data = {
                                                                    "overall": "neutral",
                                                                    "score": 0.5,
                                                                    "analysis": "No se pudo procesar el sentimiento de mercado",
                                                                    "date": datetime.now(),
                                                                }

                                                        sentiment_id = None
                                                        if market_data_mgr:
                                                            sentiment_id = market_data_mgr.save_sentiment_from_signal(
                                                                signal
                                                            )
                                                        else:
                                                            # Alternativa usando database_utils directamente
                                                            try:
                                                                from database_utils import (
                                                                    save_market_sentiment,
                                                                )

                                                                # Extraer datos de sentimiento de la señal
                                                                sentiment_data = {
                                                                    "symbol": signal.get(
                                                                        "symbol", ""
                                                                    ),
                                                                    "sentiment": signal.get(
                                                                        "sentiment",
                                                                        "neutral",
                                                                    ),
                                                                    "score": signal.get(
                                                                        "sentiment_score",
                                                                        0.5,
                                                                    ),
                                                                    "source": "InversorIA Analytics",
                                                                    "analysis": signal.get(
                                                                        "sentiment_analysis",
                                                                        signal.get(
                                                                            "analysis",
                                                                            "",
                                                                        ),
                                                                    ),
                                                                    "sentiment_date": datetime.now(),
                                                                }

                                                                # No guardamos el sentimiento de mercado aquí, ya que se carga al inicio de la aplicación
                                                                logger.info(
                                                                    "Omitiendo guardado de sentimiento de mercado, ya que se carga al inicio de la aplicación"
                                                                )
                                                                sentiment_id = None
                                                            except (
                                                                Exception
                                                            ) as sentiment_error:
                                                                logger.warning(
                                                                    f"No se pudo guardar sentimiento para {signal.get('symbol', '')}: {str(sentiment_error)}"
                                                                )
                                                except Exception as data_error:
                                                    logger.error(
                                                        f"Error guardando datos de mercado: {str(data_error)}"
                                                    )
                                                    st.warning(
                                                        f"No se pudieron guardar datos adicionales de mercado: {str(data_error)}"
                                                    )
                                            else:
                                                logger.error(
                                                    f"Error al guardar la señal para {signal['symbol']}: No se obtuvo ID"
                                                )
                                                # Mostrar mensaje de error en la interfaz
                                                st.error(
                                                    f"Error al guardar la señal para {signal['symbol']}: No se obtuvo ID"
                                                )
                                        except Exception as save_error:
                                            logger.error(
                                                f"Error al guardar la señal para {signal['symbol']}: {str(save_error)}"
                                            )
                                            # Mostrar mensaje de error en la interfaz
                                            st.error(
                                                f"Error al guardar la señal para {signal['symbol']}: {str(save_error)}"
                                            )
                                    elif not is_complete:
                                        missing_fields = [
                                            field
                                            for field in required_fields
                                            if not signal.get(field)
                                        ]
                                        logger.warning(
                                            f"No se guardó la señal para {signal['symbol']} porque está incompleta. Campos faltantes: {', '.join(missing_fields)}"
                                        )
                                        # Mostrar mensaje de advertencia en la interfaz
                                        st.warning(
                                            f"No se guardó la señal para {signal['symbol']} porque está incompleta. Campos faltantes: {', '.join(missing_fields)}"
                                        )
                                    elif existing_signals:
                                        logger.info(
                                            f"La señal para {signal['symbol']} ya existe en la base de datos con ID: {existing_signals[0]['id']}"
                                        )
                                        # Mostrar mensaje informativo en la interfaz
                                        st.info(
                                            f"La señal para {signal['symbol']} ya existe en la base de datos con ID: {existing_signals[0]['id']}"
                                        )
                                except Exception as e:
                                    logger.error(
                                        f"Error guardando señal en la base de datos: {str(e)}"
                                    )

                            if signals_saved > 0:
                                # Mostrar resumen completo de las señales guardadas
                                if (
                                    "saved_signals_info" in st.session_state
                                    and st.session_state.saved_signals_info
                                ):
                                    # Crear un mensaje de resumen más detallado y atractivo con soporte para modo oscuro
                                    summary_msg = f"""<div style='background-color: var(--background-color, #e6f7e6); color: var(--text-color, #333); padding: 15px; border-radius: 5px; border-left: 5px solid #28a745;'>
                                        <h4 style='color: #28a745; margin-top: 0;'>✅ Se guardaron {signals_saved} señales en la base de datos</h4>
                                        <div style='margin-top: 10px;'>"""

                                    # Añadir detalles de cada señal guardada en una tabla estilizada con soporte para modo oscuro
                                    summary_msg += """<table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
                                        <tr style='background-color: var(--header-bg-color, #f2f2f2); color: var(--header-text-color, #333);'>
                                            <th style='padding: 8px; text-align: left; border-bottom: 1px solid var(--border-color, #ddd);'>Símbolo</th>
                                            <th style='padding: 8px; text-align: center; border-bottom: 1px solid var(--border-color, #ddd);'>ID</th>
                                            <th style='padding: 8px; text-align: center; border-bottom: 1px solid var(--border-color, #ddd);'>Noticias</th>
                                        </tr>"""

                                    total_news = 0
                                    for info in st.session_state.saved_signals_info:
                                        # Alternar colores de fila para mejor legibilidad con soporte para modo oscuro
                                        row_style = (
                                            "background-color: var(--row-alt-bg-color, #f9f9f9);"
                                            if total_news % 2 == 0
                                            else "background-color: var(--row-bg-color, #ffffff);"
                                        )
                                        summary_msg += f"""<tr style='{row_style} color: var(--text-color, #333);'>
                                            <td style='padding: 8px; text-align: left; border-bottom: 1px solid var(--border-color, #ddd);'><b>{info['symbol']}</b></td>
                                            <td style='padding: 8px; text-align: center; border-bottom: 1px solid var(--border-color, #ddd);'>{info['id']}</td>
                                            <td style='padding: 8px; text-align: center; border-bottom: 1px solid var(--border-color, #ddd);'>{info['news_count']}</td>
                                        </tr>"""
                                        total_news += info["news_count"]

                                    summary_msg += "</table>"

                                    # Añadir resumen de noticias y sentimiento con mejor formato y soporte para modo oscuro
                                    if total_news > 0:
                                        summary_msg += f"""<div style='margin-top: 15px; padding: 10px; background-color: var(--info-bg-color, #f0f8ff); color: var(--info-text-color, #333); border-radius: 5px; border-left: 5px solid #007bff;'>
                                            <p style='margin: 0;'><b>📰 Total de noticias guardadas:</b> {total_news}</p>
                                        </div>"""

                                    # Añadir mensaje de cierre con soporte para modo oscuro
                                    summary_msg += """<div style='margin-top: 15px; font-size: 0.9em; color: var(--secondary-text-color, #666);'>
                                        <p>Los datos han sido almacenados correctamente en la base de datos y estarán disponibles para consultas futuras.</p>
                                    </div>"""

                                    # Cerrar el div principal
                                    summary_msg += "</div>"

                                    # Mostrar el resumen con formato HTML
                                    st.markdown(summary_msg, unsafe_allow_html=True)

                                    # Limpiar la información de señales guardadas
                                    st.session_state.saved_signals_info = []
                                else:
                                    # Crear un mensaje de éxito más atractivo cuando no hay detalles disponibles con soporte para modo oscuro
                                    success_msg = f"""<div style='background-color: var(--background-color, #e6f7e6); color: var(--text-color, #333); padding: 15px; border-radius: 5px; border-left: 5px solid #28a745;'>
                                        <h4 style='color: #28a745; margin-top: 0;'>✅ Se guardaron {signals_saved} señales en la base de datos</h4>
                                        <p>Los datos han sido almacenados correctamente y estarán disponibles para consultas futuras.</p>
                                    </div>"""
                                    st.markdown(success_msg, unsafe_allow_html=True)

                                    # Ejecutar post_save_quality_check.py para procesar la calidad de los datos
                                    try:
                                        import post_save_quality_check
                                        import sys
                                        import os

                                        # Asegurar que post_save_quality_check está en el path
                                        current_dir = os.path.dirname(
                                            os.path.abspath(__file__)
                                        )
                                        if current_dir not in sys.path:
                                            sys.path.append(current_dir)

                                        # Procesar la calidad de los datos
                                        result = post_save_quality_check.process_quality_after_save(
                                            table_name="trading_signals",
                                            limit=signals_saved,
                                        )

                                        if result:
                                            logger.info(
                                                f"Procesamiento de calidad completado para {signals_saved} señales. Resultado: {result}"
                                            )
                                    except Exception as e:
                                        logger.warning(
                                            f"Error en el procesamiento de calidad: {str(e)}"
                                        )
                                        logger.warning("Traza completa:", exc_info=True)

                                st.session_state.signals_saved = True
            except Exception as e:
                st.error(f"Error al renderizar el scanner mejorado: {str(e)}")
                st.error(traceback.format_exc())

                # Mostrar mensaje de error y sugerencia
                st.warning(
                    "No se pudo cargar el scanner mejorado. Por favor, asegúrate de que el archivo enhanced_market_scanner_fixed.py está disponible."
                )

    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        st.error(traceback.format_exc())


if __name__ == "__main__":
    main()
