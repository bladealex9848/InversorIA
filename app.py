import os
import time
import streamlit as st
import openai
import logging
from datetime import datetime

from market_utils import get_market_context, logger
from openai_utils import process_tool_calls, tools
from trading_dashboard import render_dashboard

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
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.alexanderoviedofadul.dev/',
        'Report a bug': None,
        'About': "InversorIA Pro: Plataforma avanzada de trading institucional"
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

# Timeframes Institucionales
TIMEFRAMES = {
    "Intradía": ["1m", "5m", "15m", "30m", "1h"],
    "Swing": ["1d", "1wk"],
    "Posicional": ["1mo", "3mo"]
}

def setup_openai():
    """Configura credenciales de OpenAI"""
    try:
        API_KEY = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        ASSISTANT_ID = os.environ.get("ASSISTANT_ID") or st.secrets.get("ASSISTANT_ID")
        
        if not API_KEY or not ASSISTANT_ID:
            st.error("⚠️ Se requieren credenciales de OpenAI")
            st.stop()
            
        openai.api_key = API_KEY
        return ASSISTANT_ID
        
    except Exception as e:
        logger.error(f"Error configurando OpenAI: {str(e)}")
        st.error("Error al configurar OpenAI")
        st.stop()

def initialize_session_state():
    """Inicializa el estado de la sesión"""
    if "thread_id" not in st.session_state:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "current_symbol" not in st.session_state:
        st.session_state.current_symbol = "SPY"
        
    if "current_timeframe" not in st.session_state:
        st.session_state.current_timeframe = "1d"

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
        st.markdown("Alexander Oviedo Fadul")
        st.markdown("[💼 LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/)")
        st.markdown("[🌐 Website](https://alexanderoviedofadul.dev/)")
        st.markdown("---")
        
        with st.expander("📚 Recursos"):
            st.markdown("""
            - [Documentación API](https://docs.alexanderoviedofadul.dev)
            - [Trading Docs](https://docs.alexanderoviedofadul.dev/trading)
            - [Risk Management](https://docs.alexanderoviedofadul.dev/risk)
            """)
        
        st.markdown("v1.0.0 | © 2025 InversorIA Pro")

def process_chat_input(prompt, ASSISTANT_ID):
    """Procesa la entrada del chat con contexto institucional"""
    try:
        if st.session_state.current_symbol:
            context_prompt = f"""
            Analizando {st.session_state.current_symbol}:
            Timeframe: {st.session_state.current_timeframe}
            
            Consulta: {prompt}
            
            Por favor proporciona:
            1. Análisis Técnico
                - Tendencia y momentum
                - Niveles clave y pivots
                - Patrones y divergencias
                - Volatilidad y volumen
            
            2. Análisis Cuantitativo
                - Correlaciones relevantes
                - Métricas de riesgo (VaR, Beta)
                - Factores principales
            
            3. Opciones y Volatilidad
                - Superficie de volatilidad
                - Term structure
                - Put/Call skew
                - Greeks principales
            
            4. Gestión de Riesgo
                - Sizing sugerido
                - Stop loss dinámico
                - Escenarios y stress
                - Ratio Sharpe/Sortino
            """
        else:
            context_prompt = prompt

        openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=context_prompt
        )

        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
            tools=tools
        )

        with st.spinner("Análisis en proceso..."):
            while True:
                run = openai.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )

                if run.status == "completed":
                    break
                elif run.status == "requires_action":
                    tool_outputs = process_tool_calls(
                        run.required_action.submit_tool_outputs.tool_calls,
                        st.session_state.current_symbol
                    )
                    
                    run = openai.beta.threads.runs.submit_tool_outputs(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

                time.sleep(0.5)

            messages = openai.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )

            for message in messages:
                if message.run_id == run.id and message.role == "assistant":
                    return message.content[0].text.value
                    
        return None
        
    except Exception as e:
        logger.error(f"Error procesando análisis: {str(e)}")
        return None

def main():
    try:
        initialize_session_state()
        ASSISTANT_ID = setup_openai()
        render_sidebar()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.title("💹 Professional Trading Suite")

            col_cat, col_sym = st.columns(2)
            with col_cat:
                category = st.selectbox("Sector", list(SYMBOLS.keys()))
            with col_sym:
                symbol = st.selectbox("Activo", SYMBOLS[category])

            if symbol != st.session_state.current_symbol:
                st.session_state.current_symbol = symbol

            render_dashboard(symbol, st.session_state.current_timeframe)

        with col2:
            st.title("💬 Trading Specialist")
            
            if st.session_state.current_symbol:
                st.info(f"""
                ### 📊 Análisis Profesional: {st.session_state.current_symbol}
                
                **Capacidades Avanzadas:**
                
                📈 **Análisis Técnico**
                - Order flow y microestructura
                - Price action institucional
                - Análisis multi-timeframe
                - Correlaciones intermarket
                
                🎯 **Trading Cuantitativo**
                - Volatilidad y Greeks
                - Market making algorítmico
                - High-frequency signals
                - Statistical arbitrage
                
                📊 **Risk Management**
                - VaR y Expected Shortfall
                - Portfolio optimization
                - Dynamic hedging
                - Factor exposure
                
                ⚠️ **Ejecución**
                - Smart order routing
                - Impacto de mercado
                - Transaction cost analysis
                - Best execution
                """)
            
            chat_container = st.container()
            
            with chat_container:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                if prompt := st.chat_input("Solicite análisis profesional"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    response = process_chat_input(prompt, ASSISTANT_ID)
                    if response:
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        with st.chat_message("assistant"):
                            st.markdown(response)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear Analysis"):
                    st.session_state.messages = []
                    st.rerun()
            
            with col2:
                if st.button("📋 Export Report"):
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"analysis_{st.session_state.current_symbol}_{timestamp}.txt"
                        
                        context = get_market_context(st.session_state.current_symbol)
                        
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(f"=== InversorIA Pro: Análisis Institucional ===\n")
                            f.write(f"Instrumento: {st.session_state.current_symbol}\n")
                            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                            
                            if context:
                                f.write("=== Análisis Técnico ===\n")
                                f.write(f"Último: ${context['last_price']:.2f}\n")
                                f.write(f"Variación: ${context['change']:.2f}\n\n")
                                
                                f.write("=== Señales Técnicas ===\n")
                                f.write(f"Tendencia: {context['signals']['trend']['sma_20_50']}\n")
                                f.write(f"RSI: {context['signals']['momentum']['rsi']:.1f}\n")
                                f.write(f"Vol: {context['signals']['volatility']['bb_width']:.4f}\n\n")
                            
                            f.write("=== Análisis Cuantitativo ===\n")
                            for message in st.session_state.messages:
                                f.write(f"\n[{message['role'].upper()}]\n")
                                f.write(f"{message['content']}\n")
                            
                            f.write("\n=== Disclaimer ===\n")
                            f.write("Este análisis es generado mediante modelos cuantitativos "
                                   "y requiere validación profesional. No constituye "
                                   "asesoramiento financiero. Realizar due diligence "
                                   "exhaustivo antes de cualquier operación.\n")
                        
                        st.success(f"Análisis exportado: {filename}")
                        
                    except Exception as e:
                        logger.error(f"Error en exportación: {str(e)}")
                        st.error("Error exportando análisis")

            st.markdown("---")
            with st.expander("ℹ️ Trading System Info"):
                st.markdown(f"""
                ### Sistema Institucional

                #### Capacidades
                - **Build:** 1.0.0
                - **Update:** {datetime.now().strftime('%Y-%m-%d')}
                - **Cobertura:** {len([s for cats in SYMBOLS.values() for s in cats])} instrumentos
                - **Indicadores:** 12 sistemas propietarios
                - **Timeframes:** {sum(len(tfs) for tfs in TIMEFRAMES.values())} marcos temporales
                
                #### Tecnología
                - Order routing institucional
                - Smart order execution
                - Low-latency infrastructure
                - Real-time market data
                - Multi-venue connectivity
                
                #### Análisis Avanzado
                - Machine Learning models
                - Neural Networks
                - Statistical arbitrage
                - Volatility surface modeling
                - Options flow analysis
                
                #### Risk Suite
                - Portfolio optimization
                - Factor exposure
                - Greeks management
                - Stress testing
                - Scenario analysis
                
                ### Advertencia Profesional
                Este sistema está diseñado para uso institucional 
                y requiere expertise en mercados financieros. Las 
                estrategias y señales generadas deben ser validadas 
                mediante análisis riguroso y gestión de riesgo 
                profesional. Trading implica riesgo sustancial 
                de pérdida. Consulte con su asesor financiero 
                antes de implementar cualquier estrategia.
                """)

    except Exception as e:
        logger.error(f"Error en sistema principal: {str(e)}")
        st.error("""
        Error en el sistema de trading. 
        Por favor, revise los logs o contacte al equipo de soporte técnico.
            
        Sistema: InversorIA Pro
        Módulo: Trading Suite
        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error en sistema principal: {str(e)}")
        st.error("""
        Error en el sistema de trading. 
        Por favor, revise los logs o contacte al equipo de soporte técnico.
            
        Sistema: InversorIA Pro
        Módulo: Trading Suite
        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)