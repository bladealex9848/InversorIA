"""
Configuración general para InversorIA Pro
"""

import streamlit as st
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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

def setup_page_config():
    """
    Configura la página de Streamlit
    """
    st.set_page_config(
        page_title="InversorIA Pro",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

def initialize_session_state():
    """
    Inicializa el estado de la sesión con valores por defecto
    """
    # Inicializar variables de sesión si no existen
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "username" not in st.session_state:
        st.session_state.username = ""
    
    if "current_symbol" not in st.session_state:
        st.session_state.current_symbol = "AAPL"
    
    if "last_scan_sectors" not in st.session_state:
        st.session_state.last_scan_sectors = ["Tecnología", "Finanzas"]
    
    if "scan_results" not in st.session_state:
        st.session_state.scan_results = pd.DataFrame()
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "scanner" not in st.session_state:
        st.session_state.scanner = None
