"""
Componente de chat con IA para InversorIA Pro
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from ai_utils import (
    process_expert_analysis,
    process_message_with_citations,
    process_chat_input_with_openai,
)
from utils.session_state import add_chat_message, clear_chat_history

logger = logging.getLogger(__name__)

def render_ai_chat():
    """
    Renderiza la pestaña de chat con IA
    """
    st.markdown("## 🤖 Trading Specialist IA")
    
    # Inicializar historial de chat si no existe
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Mostrar mensaje de bienvenida si el historial está vacío
    if not st.session_state.chat_history:
        welcome_message = {
            "role": "assistant",
            "content": f"""
            # 👋 Bienvenido al Trading Specialist IA
            
            Soy tu asistente de trading personalizado. Puedo ayudarte con:
            
            - 📊 Análisis técnico de activos
            - 📈 Interpretación de patrones de mercado
            - 💰 Estrategias de opciones
            - 📰 Análisis de noticias y sentimiento
            - 📝 Recomendaciones personalizadas
            
            Estoy analizando datos en tiempo real para {st.session_state.current_symbol}. ¿En qué puedo ayudarte hoy?
            """
        }
        st.session_state.chat_history.append(welcome_message)
    
    # Mostrar historial de chat
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end;">
                        <div style="background-color: #DCF8C6; padding: 10px; border-radius: 10px; max-width: 80%;">
                            {message["content"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-start;">
                        <div style="background-color: white; padding: 10px; border-radius: 10px; max-width: 80%; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                            {message["content"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    
    # Input para nuevo mensaje
    with st.form(key="chat_form", clear_on_submit=True):
        cols = st.columns([4, 1])
        with cols[0]:
            user_input = st.text_area("Escribe tu mensaje", key="user_input", height=100)
        with cols[1]:
            submit_button = st.form_submit_button("Enviar", use_container_width=True)
            clear_button = st.form_submit_button("Limpiar Chat", use_container_width=True)
        
        if submit_button and user_input:
            # Añadir mensaje del usuario al historial
            add_chat_message("user", user_input)
            
            # Procesar mensaje con OpenAI
            with st.spinner("El Trading Specialist está analizando..."):
                try:
                    # Obtener contexto actual
                    symbol = st.session_state.current_symbol
                    
                    # Procesar mensaje con OpenAI
                    response = process_chat_input_with_openai(user_input, symbol)
                    
                    # Añadir respuesta al historial
                    add_chat_message("assistant", response)
                    
                    # Forzar actualización de la UI
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al procesar mensaje: {str(e)}")
                    logger.error(f"Error en chat IA: {str(e)}")
        
        if clear_button:
            clear_chat_history()
            st.rerun()
    
    # Mostrar información sobre el Trading Specialist
    with st.expander("ℹ️ Acerca del Trading Specialist"):
        st.markdown(
            """
            ### Trading Specialist IA
            
            El Trading Specialist es un asistente de trading avanzado que combina:
            
            - **Análisis técnico en tiempo real**: Evaluación de patrones, indicadores y niveles clave
            - **Análisis fundamental**: Evaluación de métricas financieras y valoración
            - **Análisis de sentimiento**: Procesamiento de noticias y redes sociales
            - **Datos de opciones**: Análisis de volatilidad implícita y flujo de opciones
            
            El asistente está diseñado para proporcionar análisis contextual y recomendaciones personalizadas basadas en tu estilo de trading y tolerancia al riesgo.
            
            **Nota**: Las recomendaciones proporcionadas son solo con fines informativos y no constituyen asesoramiento financiero.
            """
        )
