"""
Gestión del estado de la sesión para InversorIA Pro
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
    
    if "last_scan_time" not in st.session_state:
        st.session_state.last_scan_time = datetime.now()

def get_current_symbol():
    """
    Obtiene el símbolo actual seleccionado
    """
    return st.session_state.current_symbol

def set_current_symbol(symbol):
    """
    Establece el símbolo actual
    """
    st.session_state.current_symbol = symbol
    logger.info(f"Símbolo actual cambiado a: {symbol}")

def update_scan_results(results):
    """
    Actualiza los resultados del scanner
    """
    st.session_state.scan_results = results
    st.session_state.last_scan_time = datetime.now()
    logger.info(f"Resultados del scanner actualizados: {len(results)} oportunidades")

def add_chat_message(role, content):
    """
    Añade un mensaje al historial de chat
    """
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    st.session_state.chat_history.append({"role": role, "content": content})
    
def clear_chat_history():
    """
    Limpia el historial de chat
    """
    st.session_state.chat_history = []
