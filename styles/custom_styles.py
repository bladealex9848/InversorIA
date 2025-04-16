"""
Estilos CSS personalizados para InversorIA Pro
"""

import streamlit as st

def load_custom_styles():
    """
    Carga los estilos CSS personalizados para la aplicación
    """
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
