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
import openai

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

# Importar utilidades de OpenAI
try:
    from openai_utils import process_tool_calls, tools
except Exception as e:
    st.error(f"Error importando openai_utils: {str(e)}")

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

# =================================================
# CONFIGURACIÓN DE OPENAI
# =================================================


def setup_openai():
    """Configura credenciales de OpenAI"""
    try:
        API_KEY = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        ASSISTANT_ID = os.environ.get("ASSISTANT_ID") or st.secrets.get("ASSISTANT_ID")

        if not API_KEY:
            st.warning(
                "⚠️ La API key de OpenAI no está configurada. El chat funcionará en modo limitado."
            )
            return None, None

        if not ASSISTANT_ID:
            st.warning(
                "⚠️ El ID del asistente no está configurado. El chat funcionará en modo limitado."
            )
            return API_KEY, None

        openai.api_key = API_KEY
        return API_KEY, ASSISTANT_ID

    except Exception as e:
        st.error(f"Error configurando OpenAI: {str(e)}")
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
        "openai": "Inteligencia artificial",
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
# FUNCIONES DE ASISTENTE MEJORADAS
# =================================================


def process_chat_input_with_openai(
    prompt, symbol=None, api_key=None, assistant_id=None
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

        # Obtener contexto actualizado del mercado
        context = get_market_context(symbol)
        if not context or "error" in context:
            return f"❌ Error: No se pudo obtener el contexto de mercado para {symbol}."

        # Formatear el contexto para incluirlo en el mensaje
        price = context.get("last_price", 0)
        change = context.get("change_percent", 0)
        vix_level = context.get("vix_level", "N/A")

        # Crear una versión resumida del contexto
        context_summary = f"""
        Contexto actual: {symbol} a ${price:.2f} ({change:+.2f}%), VIX: {vix_level}
        """

        # Si tenemos un assistant_id, usar la API de asistentes
        if assistant_id:
            return process_with_assistant(prompt, symbol, context, assistant_id)
        else:
            # Usar la API de Chat Completion directamente
            return process_with_chat_completion(prompt, symbol, context, api_key)

    except Exception as e:
        return f"Error procesando consulta: {str(e)}"


def process_with_assistant(prompt, symbol, context, assistant_id):
    """Procesa el mensaje utilizando la API de Asistentes de OpenAI"""
    try:
        # Crear thread si no existe
        if "thread_id" not in st.session_state:
            thread = openai.beta.threads.create()
            st.session_state.thread_id = thread.id

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
            while True:
                run = openai.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id, run_id=run.id
                )

                # Verificar estado de ejecución
                if run.status == "completed":
                    break
                elif run.status == "requires_action":
                    # Procesar llamadas a herramientas
                    tool_outputs = process_tool_calls(
                        run.required_action.submit_tool_outputs.tool_calls, symbol
                    )

                    # Enviar resultados
                    run = openai.beta.threads.runs.submit_tool_outputs(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs,
                    )
                elif run.status in ["failed", "cancelled", "expired"]:
                    return f"Error en la ejecución: {run.status}"

                # Pequeña pausa para no sobrecargar la API
                time.sleep(0.5)

            # Obtener mensajes actualizados
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

    except Exception as e:
        st.error(f"Error en process_with_assistant: {str(e)}")
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

        # Realizar llamada a la API
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",  # Usar el modelo más avanzado
            messages=messages,
            temperature=0.7,  # Balancear creatividad y precisión
            max_tokens=1000,  # Respuesta detallada pero no excesiva
        )

        # Extraer la respuesta
        return response.choices[0].message.content

    except Exception as e:
        st.error(f"Error en process_with_chat_completion: {str(e)}")
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
            error_msg = (
                context.get("error", "Error desconocido")
                if context
                else "No hay datos disponibles"
            )
            return f"❌ No se pudo analizar {symbol}: {error_msg}"

    except Exception as e:
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
            st.error(f"Error creando thread: {str(e)}")
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


def render_sidebar():
    """Renderiza el panel lateral con información profesional"""
    with st.sidebar:
        st.title("🧑‍💻 Trading Specialist Pro")

        st.markdown(
            """
        ## Perfil Profesional
        Analista técnico y estratega de mercados con especialización en derivados financieros y más de 8 años de experiencia en trading institucional. Experto en el desarrollo e implementación de estrategias cuantitativas, análisis de volatilidad y gestión de riesgo algorítmica. Capacidad demostrada para integrar análisis técnico avanzado con fundamentos macroeconómicos.

        ## Áreas de Especialización Principal
        - Estrategias avanzadas de opciones y volatilidad
        - Trading sistemático y algorítmico
        - Análisis técnico y cuantitativo
        - Gestión de riesgo dinámica
        - Market Making y liquidez

        ## Competencias Técnicas Avanzadas
        - Modelado avanzado de volatilidad y superficies de volatilidad
        - Análisis de flujo de opciones y order flow
        - Desarrollo de indicadores propietarios
        - Machine Learning aplicado a trading
        - Análisis de microestructura de mercado
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

        # Información de sesión
        st.markdown("---")
        if "session_start" in st.session_state:
            session_duration = datetime.now() - st.session_state.session_start
            hours, remainder = divmod(session_duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            st.caption(f"Sesión activa: {hours}h {minutes}m {seconds}s")

            # Mostrar estado de OpenAI
            if st.session_state.get("openai_configured"):
                st.caption("✅ OpenAI conectado")
            else:
                st.caption("⚠️ OpenAI no configurado - Chat en modo básico")

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

                # Mostrar badge del modo de chat
                if st.session_state.get("openai_configured"):
                    st.markdown(
                        """
                    <div style="display:inline-block;background-color:rgba(25,118,210,0.2);color:white;padding:4px 8px;border-radius:4px;font-size:0.8em;margin-bottom:10px">
                    ✨ Modo Avanzado con IA
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """
                    <div style="display:inline-block;background-color:rgba(128,128,128,0.2);color:white;padding:4px 8px;border-radius:4px;font-size:0.8em;margin-bottom:10px">
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
