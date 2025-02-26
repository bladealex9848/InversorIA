import os
import time
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback
import pytz
import json
import importlib
import sys
import requests

# Importar componentes personalizados
try:
    from market_utils import (
        fetch_market_data,
        TechnicalAnalyzer,
        OptionsParameterManager,
        get_market_context,
        get_vix_level,
        clear_cache,
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

# Importar sistema de autenticación
try:
    from authenticator import check_password, validate_session, clear_session
except Exception as e:
    st.error(f"Error importando authenticator: {str(e)}")

# Configuración de la página
st.set_page_config(
    page_title="InversorIA Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
}

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
    ]

    for key in keys_to_check:
        # Intentar obtener desde Streamlit secrets
        try:
            value = st.secrets.get(key, os.environ.get(key.upper(), ""))
            is_present = bool(value)

            # Mostrar solo una indicación de si está presente, no el valor real
            apis_status[key] = {
                "status": "✅ Disponible" if is_present else "❌ No configurada",
                "source": (
                    "Streamlit secrets"
                    if key in st.secrets
                    else (
                        "Variables de entorno"
                        if key.upper() in os.environ
                        else "No encontrada"
                    )
                ),
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
    }

    libraries_status = {}

    for lib, description in libraries.items():
        try:
            # Intentar importar la biblioteca
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
    """Muestra el estado del sistema, APIs y librerías"""
    st.header("🛠️ Estado del Sistema")

    # Información del sistema
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Información del Sistema")
        st.write(f"**Python versión:** {sys.version.split(' ')[0]}")
        st.write(f"**Streamlit versión:** {st.__version__}")
        st.write(f"**Fecha y hora:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    with col2:
        st.subheader("Estado de la Caché")
        try:
            from market_utils import _data_cache

            cache_stats = _data_cache.get_stats()
            st.write(f"**Entradas en caché:** {cache_stats.get('entradas', 'N/A')}")
            st.write(f"**Hit rate:** {cache_stats.get('hit_rate', 'N/A')}")
            st.write(
                f"**Hits/Misses:** {cache_stats.get('hits', 0)}/{cache_stats.get('misses', 0)}"
            )
        except Exception as e:
            st.write("**Error accediendo a estadísticas de caché:**", str(e))

    # Estado de APIs
    st.subheader("Estado de APIs")
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

    # Estado de librerías
    st.subheader("Estado de Librerías")
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

    # Prueba de conexión a datos
    st.subheader("Prueba de Datos")
    try:
        with st.spinner("Probando acceso a datos de mercado..."):
            test_data = fetch_market_data("SPY", "2d")
            if test_data is not None and not test_data.empty:
                st.success(f"✅ Datos disponibles para SPY: {len(test_data)} registros")
                st.dataframe(test_data.tail(3), use_container_width=True)
            else:
                st.error("❌ No se pudieron obtener datos para SPY")
    except Exception as e:
        st.error(f"❌ Error en prueba de datos: {str(e)}")


# =================================================
# FUNCIONES DE AUTENTICACIÓN Y SEGURIDAD
# =================================================


def check_authentication():
    """Verifica autenticación del usuario"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔒 InversorIA Pro - Terminal Institucional")

        st.markdown(
            """
        ### Plataforma Profesional de Trading
        
        InversorIA Pro es una terminal avanzada de trading que ofrece:
        
        - 📊 Análisis técnico multi-timeframe
        - 🎯 Estrategias de volatilidad y opciones
        - 📈 Surface analytics y volatilidad implícita
        - ⚠️ Gestión de riesgo institucional
        - 🤖 Trading algorítmico
        
        #### Acceso Restringido
        Esta plataforma está diseñada para uso institucional y requiere autenticación.
        """
        )

        password = st.text_input("Ingrese su contraseña de acceso", type="password")

        if st.button("Acceder"):
            if check_password(password):
                st.session_state.authenticated = True
                st.session_state.show_system_status = (
                    True  # Mostrar status de sistema al iniciar sesión
                )
                st.rerun()

        st.markdown("---")
        st.markdown("© 2025 InversorIA Pro | Plataforma Institucional de Trading")

        return False

    if not validate_session():
        clear_session()
        st.rerun()

    return True


# =================================================
# FUNCIONES DE ASISTENTE
# =================================================


def analyze_symbol(symbol, question=None):
    """Analiza un símbolo y genera respuesta basada en datos"""
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

            # Construir respuesta
            response = f"## Análisis de {symbol} a ${price:.2f} ({change:+.2f}%)\n\n"

            # Señal general
            response += f"### Señal General: {overall_signal}\n"
            if "overall" in signals:
                confidence = signals["overall"]["confidence"]
                response += f"Confianza: {confidence}\n\n"

            # Opciones
            response += f"### Recomendación de Opciones: {option_signal}\n"
            response += f"Estrategia: {option_strategy}\n\n"

            # Niveles clave (primeros 2)
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

            # Análisis de timeframes
            response += "\n### Análisis Multi-Timeframe\n"
            if (
                "multi_timeframe" in context
                and "consolidated" in context["multi_timeframe"]
            ):
                consolidated = context["multi_timeframe"]["consolidated"]
                response += (
                    f"Alineación: {consolidated.get('timeframe_alignment', 'N/A')}\n"
                )
                response += f"Dirección: {consolidated.get('options_recommendation', 'NEUTRAL')}\n\n"

            # Responder a la pregunta específica si existe
            if question:
                response += f"\n### Respuesta a tu pregunta\n"

                # Analizar pregunta para determinar respuesta
                question_lower = question.lower()

                if "tendencia" in question_lower or "dirección" in question_lower:
                    response += (
                        f"La tendencia actual de {symbol} es {overall_signal}.\n"
                    )

                    # Añadir detalle sobre la tendencia
                    if "trend" in signals:
                        trend = signals["trend"]
                        response += f"- SMA 20-50: {trend.get('sma_20_50', 'N/A')}\n"
                        response += f"- MACD: {trend.get('macd', 'N/A')}\n"
                        response += (
                            f"- Posición vs SMA 200: {trend.get('sma_200', 'N/A')}\n"
                        )

                elif (
                    "opciones" in question_lower
                    or "call" in question_lower
                    or "put" in question_lower
                ):
                    response += f"Para {symbol}, se recomienda estrategia de **{option_signal}**.\n"

                    # Detalles de la estrategia
                    if "options" in signals:
                        options = signals["options"]
                        response += f"- Estrategia: {options.get('strategy', 'N/A')}\n"
                        response += f"- Confianza: {options.get('confidence', 'N/A')}\n"
                        response += f"- Timeframe: {options.get('timeframe', 'N/A')}\n"

                    # Agregar parámetros específicos
                    if "options_params" in context:
                        params = context["options_params"]
                        response += "\n**Parámetros recomendados:**\n"
                        for param, value in params.items():
                            response += f"- {param}: {value}\n"

                elif "rsi" in question_lower or "momentum" in question_lower:
                    if "momentum" in signals:
                        momentum = signals["momentum"]
                        rsi = momentum.get("rsi", 0)
                        condition = momentum.get("rsi_condition", "N/A")

                        response += f"El RSI actual de {symbol} es **{rsi:.1f}** ({condition}).\n"
                        response += (
                            f"Tendencia RSI: {momentum.get('rsi_trend', 'N/A')}\n"
                        )

                        if "stoch_k" in momentum and "stoch_d" in momentum:
                            response += f"Estocástico: %K={momentum['stoch_k']:.1f}, %D={momentum['stoch_d']:.1f}\n"

                elif (
                    "soporte" in question_lower
                    or "resistencia" in question_lower
                    or "nivel" in question_lower
                ):
                    response += "**Niveles de soporte y resistencia principales:**\n\n"

                    if (
                        "resistances" in support_resistance
                        and support_resistance["resistances"]
                    ):
                        resistances = sorted(support_resistance["resistances"])
                        response += "Resistencias:\n"
                        for i, level in enumerate(resistances):
                            distance = ((level / price) - 1) * 100
                            response += f"- R{i+1}: ${level:.2f} ({distance:+.2f}%)\n"

                    if (
                        "supports" in support_resistance
                        and support_resistance["supports"]
                    ):
                        supports = sorted(support_resistance["supports"], reverse=True)
                        response += "\nSoportes:\n"
                        for i, level in enumerate(supports):
                            distance = ((level / price) - 1) * 100
                            response += f"- S{i+1}: ${level:.2f} ({distance:+.2f}%)\n"

                elif "volatilidad" in question_lower or "vix" in question_lower:
                    vix = context.get("vix_level", 0)
                    vol_state = "ALTA" if vix > 25 else "BAJA" if vix < 15 else "NORMAL"

                    response += (
                        f"El VIX actual es **{vix:.2f}** (Volatilidad {vol_state}).\n\n"
                    )

                    if "volatility" in signals:
                        volatility = signals["volatility"]
                        response += f"- Estado de volatilidad: {volatility.get('volatility_state', 'N/A')}\n"
                        response += f"- BB Width: {volatility.get('bb_width', 0):.3f}\n"
                        response += f"- ATR: {volatility.get('atr', 0):.3f}\n"
                        response += f"- Posición del precio: {volatility.get('price_position', 'N/A')}\n"

                    # Añadir recomendaciones de ajuste para opciones
                    if "volatility_adjustments" in context:
                        adj = context["volatility_adjustments"]
                        response += "\n**Ajustes recomendados:**\n"
                        for adjustment in adj.get("adjustments", []):
                            response += f"- {adjustment}\n"

                else:
                    # Respuesta general
                    response += f"El análisis de {symbol} muestra una tendencia {overall_signal} con una señal de {option_signal} para opciones.\n\n"
                    response += "Consulta las secciones anteriores para más detalles sobre el análisis técnico, niveles clave y estrategias recomendadas.\n"
                    response += "Si necesitas información específica, puedes preguntar sobre tendencia, opciones, RSI, volatilidad o niveles de soporte/resistencia."

            return response

        else:
            error_msg = (
                context.get("error", "Error desconocido")
                if context
                else "No hay datos disponibles"
            )
            return f"❌ No se pudo analizar {symbol}: {error_msg}"

    except Exception as e:
        return f"❌ Error analizando {symbol}: {str(e)}"


def process_chat_input(prompt, symbol=None):
    """Procesa la entrada del chat con análisis para el símbolo actual"""
    try:
        if not symbol:
            # Buscar si hay un ticker mencionado en el mensaje
            words = prompt.split()
            for word in words:
                word = word.strip(",.?!").upper()
                for category, symbols in SYMBOLS.items():
                    if word in symbols:
                        symbol = word
                        break

            if not symbol:
                # Usar símbolo actual si existe
                symbol = st.session_state.get("current_symbol", "SPY")

        # Generar respuesta basada en el análisis
        response = analyze_symbol(symbol, prompt)
        return response

    except Exception as e:
        return f"Error procesando consulta: {str(e)}"


# =================================================
# FUNCIONES DE SESIÓN
# =================================================


def initialize_session_state():
    """Inicializa el estado de la sesión"""
    # Estado para chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

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


def render_sidebar():
    """Renderiza el panel lateral con información profesional"""
    with st.sidebar:
        st.title("🧑‍💻 Trading Specialist Pro")

        st.markdown(
            """
        ## Perfil Profesional
        Analista técnico y estratega de mercados con especialización en derivados financieros y más de 8 años de experiencia en trading institucional. Experto en el desarrollo e implementación de estrategias cuantitativas, análisis de volatilidad y gestión de riesgo algorítmica.

        ## Áreas de Especialización Principal
        - Estrategias avanzadas de opciones y volatilidad
        - Trading sistemático y algorítmico
        - Análisis técnico y cuantitativo
        - Gestión de riesgo dinámica
        - Market Making y liquidez

        ## Competencias Técnicas Avanzadas
        - Modelado de volatilidad y superficies
        - Análisis de flujo de opciones y order flow
        - Desarrollo de indicadores propietarios
        - Machine Learning aplicado a trading
        - Análisis de microestructura de mercado
        
        ## Certificaciones Profesionales
        - Chartered Market Technician (CMT)
        - Financial Risk Manager (FRM)
        - Chartered Financial Analyst (CFA)
        - Series 7, 63, & 3 Licensed
        """
        )

        st.markdown("---")

        # Información de mercado
        try:
            st.subheader("📊 Estado del Mercado")

            # Obtener VIX
            vix_level = get_vix_level()

            # Determinar sesión de mercado
            now = datetime.now()

            hour = now.hour
            weekday = now.weekday()

            if weekday >= 5:  # Fin de semana
                session = "CERRADO"
            elif 4 <= hour < 9:
                session = "PRE-MARKET"
            elif 9 <= hour < 16:
                session = "REGULAR"
            elif 16 <= hour < 20:
                session = "AFTER-HOURS"
            else:
                session = "CERRADO"

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "VIX",
                    f"{vix_level:.2f}",
                    delta=(
                        "Volatilidad Alta"
                        if vix_level > 25
                        else "Volatilidad Baja" if vix_level < 15 else "Normal"
                    ),
                    delta_color=(
                        "inverse"
                        if vix_level > 25
                        else "normal" if vix_level < 15 else "off"
                    ),
                )
            with col2:
                st.metric("Sesión", session, now.strftime("%H:%M:%S"))

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
            except Exception as e:
                st.warning("No se pudieron cargar datos de referencia")

        except Exception as ex:
            st.warning("No se pudo obtener información de mercado")

        st.markdown("---")

        # Acciones rápidas
        st.subheader("⚙️ Acciones")

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
                st.rerun()

            # Botón de cierre de sesión
            if st.button(
                "🔒 Cerrar Sesión",
                help="Cerrar sesión actual",
                use_container_width=True,
            ):
                clear_session()
                st.rerun()

        # Información de sesión
        st.markdown("---")
        if "session_start" in st.session_state:
            session_duration = datetime.now() - st.session_state.session_start
            hours, remainder = divmod(session_duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            st.caption(f"Sesión activa: {hours}h {minutes}m {seconds}s")

        st.caption("InversorIA Pro v1.0 | © 2025")


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
            # Botón para cerrar el panel de estado
            if st.button("Continuar al Dashboard", use_container_width=True):
                st.session_state.show_system_status = False
                st.rerun()
            return

        # Renderizar sidebar después de mostrar el estado del sistema
        render_sidebar()

        # Panel principal
        st.title("💹 Análisis Profesional de Trading")

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

        # Actualizar timeframe si cambia
        if timeframe != st.session_state.current_timeframe:
            st.session_state.current_timeframe = timeframe

        # Panel de Contenido y Chat
        col1, col2 = st.columns([2, 1])

        # Panel de Dashboard en columna 1
        with col1:
            # Pestañas para diferentes vistas
            tab1, tab2, tab3 = st.tabs(
                ["📈 Análisis Técnico", "🎯 Opciones", "⏱️ Multi-Timeframe"]
            )

            with tab1:
                render_technical_tab(symbol, timeframe)

            with tab2:
                render_options_tab(symbol)

            with tab3:
                render_multiframe_tab(symbol)

        # Panel de Chat en columna 2
        with col2:
            st.header("💬 Trading Specialist")

            # Mostrar tarjeta de contexto
            from market_utils import get_market_context

            context = get_market_context(symbol)

            if context and "error" not in context:
                price = context.get("last_price", 0)
                change = context.get("change_percent", 0)
                signals = context.get("signals", {})

                # Determinar señal de opciones
                option_signal = "NEUTRAL"
                option_strategy = "N/A"
                if "options" in signals:
                    option_signal = signals["options"]["direction"]
                    option_strategy = signals["options"]["strategy"]

                # Colores dinámicos según señal
                signal_color = "gray"
                if option_signal == "CALL":
                    signal_color = "green"
                elif option_signal == "PUT":
                    signal_color = "red"

                # Mostrar tarjeta con contexto actual
                st.markdown(
                    f"""
                <div style="background-color:rgba(70,70,70,0.2);padding:15px;border-radius:8px;margin-bottom:15px;border-left:5px solid {signal_color}">
                <h3 style="margin-top:0">{symbol} ${price:.2f} <span style="color:{'green' if change >= 0 else 'red'}">{change:+.2f}%</span></h3>
                <p><strong>Señal:</strong> <span style="color:{signal_color}">{option_signal}</span> ({option_strategy})</p>
                <p><strong>VIX:</strong> {context.get('vix_level', 'N/A')} | <strong>Volatilidad:</strong> {signals.get('volatility', {}).get('volatility_state', 'Normal')}</p>
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

                    # Generar y mostrar respuesta
                    with st.spinner("Analizando..."):
                        response = process_chat_input(prompt, symbol)

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
