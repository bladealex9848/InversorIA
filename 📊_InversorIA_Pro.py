import os
import time
import streamlit as st
import openai
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback
import pytz

# Importar componentes personalizados
from market_utils import (
    get_market_context,
    fetch_market_data,
    TechnicalAnalyzer,
    OptionsParameterManager,
    clear_cache,
    get_vix_level,
    logger
)

from trading_dashboard import (
    render_dashboard,
    render_technical_tab,
    render_options_tab,
    render_multi_timeframe_tab,
    render_fundamental_tab,
    render_report_tab,
    render_risk_tab,
    TIMEFRAMES,
    COLORS
)

from authenticator import check_password, validate_session, clear_session

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Configuración de la página
st.set_page_config(
    page_title="InversorIA Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/support',
        'Report a bug': 'https://www.example.com/bug',
        'About': "InversorIA Pro: Plataforma avanzada de trading institucional con IA"
    }
)

# Universo de Trading
SYMBOLS = {
    "Índices": ["SPY", "QQQ", "DIA", "IWM", "EFA", "VWO", "IYR", "XLE", "XLF", "XLV"],
    "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "PYPL", "CRM"],
    "Finanzas": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK"],
    "Salud": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "AMGN", "BMY", "GILD", "TMO"],
    "Energía": ["XOM", "CVX", "SHEL", "TTE", "COP", "EOG", "PXD", "DVN", "MPC", "PSX"],
    "Consumo": ["MCD", "SBUX", "NKE", "TGT", "HD", "LOW", "TJX", "ROST", "CMG", "DHI"],
    "Volatilidad": ["VXX", "UVXY", "SVXY", "VIXY"],
    "Cripto ETFs": ["BITO", "GBTC", "ETHE", "ARKW", "BLOK"],
    "Materias Primas": ["GLD", "SLV", "USO", "UNG", "CORN", "SOYB", "WEAT"],
    "Bonos": ["AGG", "BND", "IEF", "TLT", "LQD", "HYG", "JNK", "TIP", "MUB", "SHY"],
    "Inmobiliario": ["VNQ", "XLRE", "IYR", "REIT", "HST", "EQR", "AVB", "PLD", "SPG", "AMT"]
}

#=================================================
# FUNCIONES DE OPENAI Y ASISTENTE
#=================================================

def setup_openai():
    """Configura credenciales de OpenAI"""
    try:
        API_KEY = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        ASSISTANT_ID = os.environ.get("ASSISTANT_ID") or st.secrets.get("ASSISTANT_ID")
        
        if not API_KEY or not ASSISTANT_ID:
            st.error("⚠️ Se requieren credenciales de OpenAI. Configure OPENAI_API_KEY y ASSISTANT_ID en secrets o variables de entorno.")
            st.stop()
            
        openai.api_key = API_KEY
        return ASSISTANT_ID
        
    except Exception as e:
        logger.error(f"Error configurando OpenAI: {str(e)}")
        st.error("Error al configurar OpenAI. Verifique las credenciales.")
        st.stop()

def process_tool_calls(tool_calls, symbol):
    """Procesa llamadas a herramientas desde OpenAI Assistant"""
    try:
        responses = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            try:
                arguments = tool_call.function.arguments
                if isinstance(arguments, str):
                    import json
                    arguments = json.loads(arguments)
                else:
                    arguments = arguments
                
                if function_name == "analyze_technical":
                    response = analyze_technical(arguments.get("symbol") or symbol)
                elif function_name == "get_multi_timeframe_analysis":
                    response = get_multi_timeframe_analysis(arguments.get("symbol") or symbol)
                elif function_name == "analyze_options_strategy":
                    response = analyze_options_strategy(
                        arguments.get("symbol") or symbol,
                        arguments.get("direction"),
                        arguments.get("option_type")
                    )
                else:
                    response = {"status": "error", "message": f"Función {function_name} no implementada"}
                
                responses.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(response)
                })
                
            except Exception as func_error:
                logger.error(f"Error procesando función {function_name}: {str(func_error)}")
                responses.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"status": "error", "message": str(func_error)})
                })
        
        return responses
        
    except Exception as e:
        logger.error(f"Error en process_tool_calls: {str(e)}")
        return []

def analyze_technical(symbol):
    """Obtiene análisis técnico actualizado"""
    try:
        context = get_market_context(symbol)
        if context and "error" not in context:
            return {
                "status": "success",
                "data": {
                    "last_price": context["last_price"],
                    "change": context["change"],
                    "change_percent": context["change_percent"],
                    "signals": context["signals"],
                    "patterns": context["candle_patterns"],
                    "support_resistance": context["support_resistance"],
                    "updated_at": context["updated_at"]
                }
            }
        return {"status": "error", "message": context.get("error", "Error obteniendo contexto del mercado")}
    except Exception as e:
        logger.error(f"Error en analyze_technical: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_multi_timeframe_analysis(symbol):
    """Análisis en múltiples timeframes"""
    try:
        context = get_market_context(symbol)
        if context and "error" not in context and "multi_timeframe" in context:
            return {
                "status": "success",
                "data": context["multi_timeframe"]
            }
        return {"status": "error", "message": context.get("error", "Error obteniendo análisis multi-timeframe")}
    except Exception as e:
        logger.error(f"Error en get_multi_timeframe_analysis: {str(e)}")
        return {"status": "error", "message": str(e)}

def analyze_options_strategy(symbol, direction=None, option_type=None):
    """Analiza estrategia de opciones para un símbolo"""
    try:
        context = get_market_context(symbol)
        if context and "error" not in context:
            # Obtener recomendación si no se especificó dirección
            if not direction and "signals" in context and "options" in context["signals"]:
                direction = context["signals"]["options"]["direction"]
                
            # Obtener datos relevantes
            price = context["last_price"]
            vix = context["vix_level"]
            options_params = context["options_params"]
            
            # Determinar tipo de opción
            if not option_type:
                option_type = "CALL" if direction == "CALL" else "PUT"
                
            # Calcular strike recomendado
            strike = None
            if options_params and "distance_spot_strike" in options_params:
                import re
                distance_values = re.findall(r'(\d+(?:\.\d+)?)', options_params["distance_spot_strike"])
                if distance_values:
                    distance = float(distance_values[0])
                    distance_pct = distance / 100
                    
                    if option_type == "CALL":
                        strike = price * (1 + distance_pct)
                    else:
                        strike = price * (1 - distance_pct)
            
            # Si no se pudo calcular, usar valor por defecto
            if not strike:
                strike = price * 1.05 if option_type == "CALL" else price * 0.95
                
            # Adaptar por volatilidad
            if vix > 25:  # Alta volatilidad
                strike = price * (1 + distance_pct * 1.2) if option_type == "CALL" else price * (1 - distance_pct * 1.2)
            elif vix < 15:  # Baja volatilidad
                strike = price * (1 + distance_pct * 0.9) if option_type == "CALL" else price * (1 - distance_pct * 0.9)
                
            # Calcular fechas de expiración estimadas
            current_date = datetime.now()
            short_exp = (current_date + timedelta(days=14)).strftime("%Y-%m-%d")
            medium_exp = (current_date + timedelta(days=30)).strftime("%Y-%m-%d")
            long_exp = (current_date + timedelta(days=60)).strftime("%Y-%m-%d")
            
            # Generar recomendaciones
            strategy = None
            if "signals" in context and "options" in context["signals"]:
                strategy = context["signals"]["options"]["strategy"]
            
            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "current_price": price,
                    "option_type": option_type,
                    "recommended_strike": round(strike, 2),
                    "expirations": {
                        "short": short_exp,
                        "medium": medium_exp,
                        "long": long_exp
                    },
                    "vix_level": vix,
                    "strategy": strategy,
                    "options_params": options_params
                }
            }
        
        return {"status": "error", "message": context.get("error", "Error analizando opciones")}
        
    except Exception as e:
        logger.error(f"Error en analyze_options_strategy: {str(e)}")
        return {"status": "error", "message": str(e)}

# Definición de herramientas
tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_technical",
            "description": "Obtiene análisis técnico actualizado de un símbolo",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Símbolo a analizar (ej: AAPL, SPY, MSFT)"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_multi_timeframe_analysis",
            "description": "Análisis en múltiples timeframes de un símbolo",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Símbolo a analizar (ej: AAPL, SPY, MSFT)"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_options_strategy",
            "description": "Analiza estrategia de opciones para un símbolo",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Símbolo a analizar (ej: AAPL, SPY, MSFT)"
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["CALL", "PUT", "NEUTRAL"],
                        "description": "Dirección de la estrategia"
                    },
                    "option_type": {
                        "type": "string",
                        "enum": ["CALL", "PUT", "SPREAD", "IRON_CONDOR", "BUTTERFLY", "CALENDAR"],
                        "description": "Tipo de opción o estrategia"
                    }
                },
                "required": ["symbol"]
            }
        }
    }
]

def process_chat_input(prompt, ASSISTANT_ID, symbol=None):
    """Procesa la entrada del chat con contexto institucional"""
    try:
        if not symbol:
            symbol = st.session_state.current_symbol
            
        if symbol:
            # Obtener datos de contexto
            with st.spinner("Analizando contexto de mercado..."):
                context = get_market_context(symbol)
            
            # Crear un prompt enriquecido si tenemos contexto
            if context and "error" not in context:
                price = context.get("last_price", 0)
                change = context.get("change", 0)
                change_pct = context.get("change_percent", 0)
                
                # Extraer señal general
                signal = "NEUTRAL"
                confidence = "BAJA"
                
                if "signals" in context and "overall" in context["signals"]:
                    signal = context["signals"]["overall"]["signal"].upper()
                    confidence = context["signals"]["overall"]["confidence"].upper()
                    
                # Extraer señal de opciones
                option_signal = "NEUTRAL"
                strategy = "N/A"
                    
                if "signals" in context and "options" in context["signals"]:
                    option_signal = context["signals"]["options"]["direction"]
                    strategy = context["signals"]["options"]["strategy"]
                
                # Construir prompt con contexto
                context_prompt = f"""
                Consulta sobre {symbol} a ${price:.2f} ({'+' if change > 0 else ''}{change_pct:.2f}%):
                
                Señales técnicas actuales:
                - Señal general: {signal} (Confianza: {confidence})
                - Opciones: {option_signal} ({strategy})
                - VIX: {context.get('vix_level', 'N/A')}
                
                Consulta del usuario: {prompt}
                
                Proporciona un análisis profesional y detallado, incluyendo:
                1. Análisis técnico relevante
                2. Estrategia de opciones si es apropiado
                3. Gestión de riesgo personalizada
                4. Timeframes recomendados
                
                Si compartes niveles específicos (entradas, stops, objetivos), asegúrate de que sean precisos y actualizados.
                """
            else:
                # Sin contexto, usar prompt original
                context_prompt = prompt
        else:
            # Sin símbolo seleccionado
            context_prompt = prompt

        # Crear mensaje en el thread
        thread_messages = openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=context_prompt
        )

        # Ejecutar con herramientas
        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
            tools=tools
        )
        
        # Monitorear la ejecución
        with st.spinner("Analizando mercado y generando respuesta..."):
            while True:
                run = openai.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
                
                # Verificar estado de ejecución
                if run.status == "completed":
                    break
                elif run.status == "requires_action":
                    # Procesar llamadas a herramientas
                    tool_outputs = process_tool_calls(
                        run.required_action.submit_tool_outputs.tool_calls,
                        symbol
                    )
                    
                    # Enviar resultados
                    run = openai.beta.threads.runs.submit_tool_outputs(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
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
                    if hasattr(message.content[0], 'text'):
                        return message.content[0].text.value
                    else:
                        return "Error: Formato de respuesta no reconocido"
                    
        return "No se pudo obtener una respuesta del asistente."
        
    except Exception as e:
        logger.error(f"Error procesando análisis: {str(e)}\n{traceback.format_exc()}")
        return f"Error procesando la consulta: {str(e)}"

#=================================================
# FUNCIONES DE AUTENTICACIÓN Y SESIÓN
#=================================================

def check_authentication():
    """Verifica autenticación del usuario"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        st.title("🔒 InversorIA Pro - Acceso Institucional")
        
        st.markdown("""
        ### Plataforma Profesional de Trading
        
        InversorIA Pro es una suite avanzada de trading que ofrece:
        
        - 📊 Análisis técnico multi-timeframe
        - 🎯 Trading de opciones y volatilidad
        - 🤖 Estrategias sistemáticas
        - ⚠️ Gestión de riesgo profesional
        - 📈 Análisis cuantitativo
        - 💹 Market making algorítmico
        
        #### Acceso Restringido
        Esta plataforma está diseñada para uso institucional y requiere autenticación.
        """)
        
        password = st.text_input("Ingrese su contraseña de acceso", type="password")
        
        if st.button("Acceder"):
            if check_password(password):
                st.session_state.authenticated = True
                st.rerun()
            
        st.markdown("---")
        st.markdown("© 2025 InversorIA Pro | Sistema de Trading Institucional")
        
        return False
        
    if not validate_session():
        clear_session()
        st.rerun()
        
    return True

def initialize_session_state():
    """Inicializa el estado de la sesión"""
    # Estado para chat de OpenAI
    if "thread_id" not in st.session_state:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Estado para activos seleccionados
    if "current_symbol" not in st.session_state:
        st.session_state.current_symbol = "SPY"
        
    if "current_timeframe" not in st.session_state:
        st.session_state.current_timeframe = "1d"
        
    # Estado para escaneo de mercado
    if "last_scan_time" not in st.session_state:
        st.session_state.last_scan_time = datetime.now() - timedelta(hours=1)
            
    if "last_scan_sectors" not in st.session_state:
        st.session_state.last_scan_sectors = ["Índices", "Tecnología"]
            
    if "scan_results" not in st.session_state:
        st.session_state.scan_results = pd.DataFrame()

def render_sidebar():
    """Renderiza el panel de información profesional"""
    with st.sidebar:
        st.title("🧑‍💻 Trading Specialist Pro")
        
        st.markdown("""
        ### Especialidades:
        - 📊 Análisis técnico avanzado
        - 📈 Estrategias de volatilidad
        - 🤖 Trading sistemático
        - 🎯 Market making
        - ⚠️ Risk management
        
        ### Certificaciones:
        - Chartered Market Technician (CMT)
        - Financial Risk Manager (FRM)
        - Chartered Financial Analyst (CFA)
        
        ### Tecnologías:
        - Bloomberg Terminal
        - Interactive Brokers TWS
        - Python Quant Suite
        - ML Trading Systems
        """)
        
        st.markdown("---")
        
        # Información de mercado
        try:
            st.subheader("📊 Estado del Mercado")
            
            # Obtener VIX
            vix_level = get_vix_level()
            
            # Determinar sesión de mercado
            ny_tz = pytz.timezone('America/New_York')
            now = datetime.now(ny_tz)
            
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
                st.metric("VIX", f"{vix_level:.2f}", 
                         delta="Volatilidad Alta" if vix_level > 25 else "Volatilidad Baja" if vix_level < 15 else "Normal",
                         delta_color="inverse" if vix_level > 25 else "normal" if vix_level < 15 else "off")
            with col2:
                st.metric("Sesión NY", session, now.strftime("%H:%M:%S"))
                
            # Mercados principales como referencia
            try:
                spy_data = fetch_market_data("SPY", "2d")
                qqq_data = fetch_market_data("QQQ", "2d")
                
                if not spy_data.empty and not qqq_data.empty:
                    spy_change = ((spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-2]) - 1) * 100
                    qqq_change = ((qqq_data['Close'].iloc[-1] / qqq_data['Close'].iloc[-2]) - 1) * 100
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("S&P 500", f"${spy_data['Close'].iloc[-1]:.2f}", f"{spy_change:.2f}%",
                                 delta_color="normal" if spy_change >= 0 else "inverse")
                    with col2:
                        st.metric("NASDAQ", f"${qqq_data['Close'].iloc[-1]:.2f}", f"{qqq_change:.2f}%",
                                 delta_color="normal" if qqq_change >= 0 else "inverse")
            except Exception as e:
                st.warning("No se pudieron cargar datos de mercado de referencia")
                
        except Exception as ex:
            st.warning("No se pudo obtener información de mercado")
            
        st.markdown("---")
        
        # Acciones rápidas de sistema
        st.subheader("⚙️ Acciones del Sistema")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Limpiar Caché", help="Limpiar caché de datos para obtener información fresca", use_container_width=True):
                cleared = clear_cache()
                st.success(f"Caché limpiado: {cleared} entradas eliminadas")
                time.sleep(1)
                st.rerun()
                
        with col2:
            if st.button("🔒 Cerrar Sesión", help="Cerrar sesión actual", use_container_width=True):
                clear_session()
                st.rerun()
                
        st.markdown("---")
        st.caption("InversorIA Pro v2.0 | © 2025")

def get_market_status():
    """Obtiene el estado actual del mercado"""
    try:
        # Determinar sesión de mercado
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(ny_tz)
        
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
            
        # Calcular próxima actualización
        next_update = "N/A"
        if hasattr(st.session_state, 'last_scan_time') and st.session_state.last_scan_time is not None:
            next_update = (st.session_state.last_scan_time + timedelta(minutes=5)).strftime("%H:%M:%S")
            
        return {
            "time": now.strftime("%H:%M:%S"),
            "session": session,
            "day": now.strftime("%d/%m/%Y"),
            "next_update": next_update
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del mercado: {str(e)}")
        return {
            "time": datetime.now().strftime("%H:%M:%S"),
            "session": "ERROR",
            "day": datetime.now().strftime("%d/%m/%Y"),
            "next_update": "N/A"
        }

#=================================================
# FUNCIÓN PRINCIPAL
#=================================================

def main():
    """Función principal de la aplicación"""
    try:
        # 1. Verificar autenticación
        if not check_authentication():
            return
            
        # 2. Inicialización de componentes
        initialize_session_state()
        ASSISTANT_ID = setup_openai()
        render_sidebar()

        # 3. Panel superior: Trading Dashboard
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.title("💹 Professional Trading Suite")

            # Selección de activo
            col_cat, col_sym = st.columns(2)
            with col_cat:
                category = st.selectbox("Sector", list(SYMBOLS.keys()), key="category_selector")
            with col_sym:
                symbol = st.selectbox("Activo", SYMBOLS[category], key="symbol_selector")

            # Actualizar símbolo actual si cambia
            if symbol != st.session_state.current_symbol:
                st.session_state.current_symbol = symbol
                
                # Limpiar mensajes anteriores si cambia el símbolo
                if "messages" in st.session_state:
                    st.session_state.messages = []
                
                # Crear nuevo thread
                thread = openai.beta.threads.create()
                st.session_state.thread_id = thread.id

            # Renderizar dashboard principal
            render_dashboard(symbol, st.session_state.current_timeframe)

        # 4. Panel lateral: Asistente de Trading
        with col2:
            st.title("💬 Trading Specialist")
            
            # 4.1 Panel de contexto actual
            if st.session_state.current_symbol:
                # Información actual del activo
                try:
                    with st.spinner(f"Obteniendo datos actualizados de {st.session_state.current_symbol}..."):
                        context = get_market_context(st.session_state.current_symbol)
                    
                    if context and "error" not in context:
                        # Extraer información clave
                        price = context.get("last_price", 0)
                        change = context.get("change", 0)
                        change_pct = context.get("change_percent", 0)
                        vix = context.get("vix_level", 0)
                        
                        # Mostrar tarjeta de información
                        st.markdown(f"""
                        <div style="
                            background-color: rgba(100, 100, 100, 0.2);
                            border-radius: 10px;
                            padding: 15px;
                            margin-bottom: 20px;">
                            <h3 style="margin-top: 0;">{st.session_state.current_symbol}</h3>
                            <h2 style="margin: 5px 0;">${price:.2f} <span style="color: {'green' if change >= 0 else 'red'}">
                                {'+' if change >= 0 else ''}{change_pct:.2f}%
                            </span></h2>
                            <p style="margin: 5px 0;">VIX: {vix:.2f} | Volatilidad: {
                                '<span style="color: red;">ALTA</span>' if vix > 25 else 
                                '<span style="color: green;">BAJA</span>' if vix < 15 else
                                '<span style="color: yellow;">NORMAL</span>'
                            }</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Mostrar señal principal
                        if "signals" in context and "options" in context["signals"]:
                            options_signal = context["signals"]["options"]
                            direction = options_signal["direction"]
                            confidence = options_signal["confidence"]
                            strategy = options_signal["strategy"]
                            
                            # Color según dirección
                            bg_color = "rgba(38, 166, 154, 0.2)" if direction == "CALL" else \
                                      "rgba(239, 83, 80, 0.2)" if direction == "PUT" else \
                                      "rgba(255, 255, 255, 0.1)"
                            
                            st.markdown(f"""
                            <div style="
                                background-color: {bg_color};
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 20px;
                                text-align: center;">
                                <h3 style="margin: 0;">Señal: {direction}</h3>
                                <p style="margin: 5px 0;">
                                    <strong>Confianza:</strong> {confidence}<br>
                                    <strong>Estrategia:</strong> {strategy}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning(f"No se pudieron obtener datos para {st.session_state.current_symbol}")
                        
                except Exception as e:
                    st.error(f"Error procesando datos: {str(e)}")
                
                # Panel de capacidades del asistente
                with st.expander("ℹ️ Capacidades del Asistente", expanded=False):
                    st.markdown("""
                    ### Capacidades del Trading Specialist
                    
                    - **Análisis Técnico**: Patrones avanzados, indicadores, niveles clave
                    - **Estrategias de Opciones**: Recomendaciones CALL/PUT, estrategias multi-pata
                    - **Multi-Timeframe**: Análisis de timeframes múltiples y divergencias
                    - **Gestión de Riesgo**: Tamaño de posición, R:R, escenarios
                    - **Trading Cuantitativo**: Volatilidad, Greeks, backtesting
                    
                    ### Ejemplos de Consultas:
                    
                    - "¿Cuál es el análisis técnico actual para AAPL?"
                    - "Recomienda una estrategia de opciones para TSLA"
                    - "Análisis multi-timeframe para SPY"
                    - "Calcula el tamaño de posición para un trade con 2% de riesgo"
                    - "Explica el patrón de velas japonesas en este gráfico"
                    """)
            
            # 4.2 Chat con el asistente
            chat_container = st.container(height=400, border=False)
            
            with chat_container:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                if prompt := st.chat_input("¿Qué deseas analizar?"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.spinner("Analizando..."):
                        response = process_chat_input(prompt, ASSISTANT_ID)
                        
                    if response:
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        with st.chat_message("assistant"):
                            st.markdown(response)
            
            # 4.3 Acciones de chat
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Limpiar Chat", use_container_width=True):
                    # Crear nuevo thread
                    thread = openai.beta.threads.create()
                    st.session_state.thread_id = thread.id
                    
                    # Limpiar mensajes
                    st.session_state.messages = []
                    st.rerun()
            
            with col2:
                if st.button("📋 Exportar Análisis", use_container_width=True):
                    try:
                        # Crear contenido de exportación
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"analisis_{st.session_state.current_symbol}_{timestamp}.txt"
                        
                        export_content = []
                        export_content.append(f"=== ANÁLISIS DE {st.session_state.current_symbol} ===")
                        export_content.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        export_content.append("")
                        
                        # Añadir contexto actual
                        try:
                            context = get_market_context(st.session_state.current_symbol)
                            if context and "error" not in context:
                                export_content.append(f"Precio: ${context['last_price']:.2f}")
                                export_content.append(f"Cambio: {context['change_percent']:.2f}%")
                                export_content.append(f"VIX: {context['vix_level']:.2f}")
                                export_content.append("")
                                
                                # Añadir señales
                                if "signals" in context and "overall" in context["signals"]:
                                    overall = context["signals"]["overall"]
                                    export_content.append(f"Señal General: {overall['signal']} (Confianza: {overall['confidence']})")
                                
                                if "signals" in context and "options" in context["signals"]:
                                    options = context["signals"]["options"]
                                    export_content.append(f"Señal Opciones: {options['direction']} (Estrategia: {options['strategy']})")
                                    
                                export_content.append("")
                        except Exception as ex:
                            export_content.append("Error obteniendo contexto de mercado")
                            
                        # Añadir conversación
                        export_content.append("=== CONVERSACIÓN ===")
                        for msg in st.session_state.messages:
                            export_content.append(f"[{msg['role'].upper()}]")
                            export_content.append(msg["content"])
                            export_content.append("")
                            
                        # Añadir disclaimer
                        export_content.append("=== DISCLAIMER ===")
                        export_content.append("Este análisis es generado automáticamente y no constituye asesoramiento financiero.")
                        export_content.append("Los datos son solo para fines informativos y educativos.")
                        export_content.append("Trading conlleva riesgo de pérdida. Realice su propia investigación.")
                        
                        # Unir todo el contenido
                        full_content = "\n".join(export_content)
                        
                        # Crear botón de descarga
                        st.download_button(
                            label="📥 Descargar",
                            data=full_content,
                            file_name=filename,
                            mime="text/plain",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"Error exportando análisis: {str(e)}")
            
            # 4.4 Pie de página
            st.markdown("---")
            st.caption("""
            **⚠️ Disclaimer:** Este sistema proporciona análisis técnico y asistencia de trading
            para fines informativos únicamente. No constituye asesoramiento financiero ni garantiza
            resultados específicos. El trading conlleva riesgo de pérdida sustancial.
            """)

    except Exception as e:
        logger.error(f"Error en aplicación principal: {str(e)}\n{traceback.format_exc()}")
        st.error(f"""
        ⚠️ Error en la aplicación: {str(e)}
        
        Por favor, intente lo siguiente:
        1. Recargar la página
        2. Limpiar la caché (botón en el panel lateral)
        3. Cerrar sesión y volver a iniciar
        
        Si el problema persiste, contacte al soporte técnico.
        """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}\n{traceback.format_exc()}")
        st.error(f"""
        ⚠️ Error crítico: {str(e)}
        
        La aplicación ha encontrado un error inesperado.
        Por favor, recargue la página o contacte al soporte técnico.
        """)