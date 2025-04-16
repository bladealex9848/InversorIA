"""
Componente de sidebar para InversorIA Pro
"""

import streamlit as st
from datetime import datetime
import logging
from company_data import SYMBOLS, get_company_info

logger = logging.getLogger(__name__)

def render_sidebar():
    """
    Renderiza la barra lateral de la aplicación
    """
    with st.sidebar:
        st.image("https://placehold.co/600x200/1E88E5/FFFFFF?text=InversorIA+Pro", use_container_width=True)
        
        # Perfil de usuario
        if st.session_state.authenticated:
            st.markdown(
                f"""
                <div class="sidebar-profile">
                    <h2>👤 {st.session_state.username}</h2>
                    <p>Último acceso: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # Selector de símbolo
        st.markdown("<div class='sidebar-section-title'>Seleccionar Activo</div>", unsafe_allow_html=True)
        
        # Selector de sector
        sectors = list(SYMBOLS.keys())
        selected_sector = st.selectbox("Sector", sectors, key="sidebar_sector")
        
        # Selector de símbolo basado en el sector
        symbols_in_sector = SYMBOLS.get(selected_sector, [])
        selected_symbol = st.selectbox(
            "Símbolo",
            symbols_in_sector,
            index=0 if st.session_state.current_symbol not in symbols_in_sector else symbols_in_sector.index(st.session_state.current_symbol),
            key="sidebar_symbol",
        )
        
        # Botón para cambiar el símbolo actual
        if st.button("Analizar", use_container_width=True):
            st.session_state.current_symbol = selected_symbol
            # Forzar recarga para actualizar la UI
            st.rerun()
        
        # Información del activo seleccionado
        company_info = get_company_info(selected_symbol)
        if company_info:
            st.markdown("### Información del Activo")
            st.markdown(f"**Nombre:** {company_info.get('name', 'N/A')}")
            st.markdown(f"**Sector:** {company_info.get('sector', 'N/A')}")
            st.markdown(f"**Industria:** {company_info.get('industry', 'N/A')}")
            
            # Mostrar descripción si está disponible
            if "description" in company_info:
                with st.expander("Descripción"):
                    st.write(company_info["description"])
        
        # Sección de configuración
        with st.expander("⚙️ Configuración"):
            st.slider("Días de Historial", min_value=30, max_value=365, value=180, step=30, key="history_days")
            st.checkbox("Modo Oscuro", value=False, key="dark_mode")
            st.checkbox("Mostrar Indicadores Avanzados", value=True, key="show_advanced_indicators")
        
        # Botón para cerrar sesión
        if st.session_state.authenticated:
            if st.button("Cerrar Sesión", type="primary", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.rerun()
