import streamlit as st
import pandas as pd
import logging
import socket
import time
import smtplib
import mysql.connector
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,  # Usar INFO para reducir mensajes de depuración
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configurar nivel de logging para bibliotecas externas
logging.getLogger("mysql").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)
logging.getLogger("streamlit").setLevel(logging.INFO)

# Verificación de autenticación
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.title("🔒 Acceso Restringido")
    st.warning("Por favor, inicie sesión desde la página principal del sistema.")
    st.stop()

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Notificaciones",
    layout="wide",
    page_icon="🔔",
    initial_sidebar_state="expanded",
)

# Título principal
st.title("🔔 Sistema de Notificaciones y Seguimiento")

# Barra lateral para configuración
with st.sidebar:
    st.header("Configuración")

    # Filtros para señales
    st.subheader("Filtros de Señales")
    categoria = st.selectbox(
        "Categoría",
        [
            "Todas",
            "Tecnología",
            "Finanzas",
            "Salud",
            "Energía",
            "Consumo",
            "Índices",
            "Materias Primas",
        ],
    )

    confianza = st.multiselect(
        "Nivel de Confianza", ["Alta", "Media", "Baja"], default=["Alta", "Media"]
    )

    dias_atras = st.slider("Días a mostrar", min_value=1, max_value=30, value=7)

    # Configuración de correo
    st.subheader("Configuración de Correo")
    destinatarios = st.text_area(
        "Destinatarios (separados por coma)",
        placeholder="ejemplo@correo.com, otro@correo.com",
    )

    # Botón para limpiar caché
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.success("Caché limpiado correctamente")


# Añadir directorio raíz al path para importar módulos del proyecto principal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Clase para el análisis de señales en tiempo real
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

        # Intentar importar funciones de análisis del proyecto principal
        try:
            from market_utils import (
                fetch_market_data,
                get_market_context,
                get_vix_level,
                _data_cache,
            )
            from technical_analysis import (
                detect_support_resistance,
                detect_trend_lines,
                detect_candle_patterns,
                improve_technical_analysis,
                improve_sentiment_analysis,
            )

            # Importar información de símbolos
            # Importar información de símbolos y escaner de mercado
            # Usar nombre de archivo compatible
            import sys

            main_module = sys.modules.get("__main__")
            if hasattr(main_module, "COMPANY_INFO"):
                self.company_info = main_module.COMPANY_INFO
                self.market_scanner = main_module.MarketScanner()
            else:
                # Alternativa: crear diccionarios de ejemplo
                self.company_info = {
                    "AAPL": {
                        "name": "Apple Inc.",
                        "sector": "Tecnología",
                        "description": "Fabricante de dispositivos electrónicos y software",
                    },
                    "MSFT": {
                        "name": "Microsoft Corporation",
                        "sector": "Tecnología",
                        "description": "Empresa de software y servicios en la nube",
                    },
                    "GOOGL": {
                        "name": "Alphabet Inc.",
                        "sector": "Tecnología",
                        "description": "Conglomerado especializado en productos y servicios de Internet",
                    },
                }
                self.market_scanner = None

            self.fetch_market_data = fetch_market_data
            self.get_market_context = get_market_context
            self.get_vix_level = get_vix_level
            self.data_cache = _data_cache
            self.detect_support_resistance = detect_support_resistance
            self.detect_trend_lines = detect_trend_lines
            self.detect_candle_patterns = detect_candle_patterns
            self.improve_technical_analysis = improve_technical_analysis
            self.improve_sentiment_analysis = improve_sentiment_analysis
            # Ya se inicializaron en el bloque anterior

            self.import_success = True
            logger.info("Módulos de análisis importados correctamente")
        except Exception as e:
            self.import_success = False
            logger.error(f"Error importando módulos de análisis: {str(e)}")

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
            if (
                "market_scanner" in st.session_state
                and st.session_state.market_scanner is not None
            ):
                market_scanner = st.session_state.market_scanner
                logger.info("Usando market_scanner existente desde session_state")
            else:
                # 2. Si no existe, intentar importarlo desde market_scanner.py
                try:
                    # Importar directamente (asumiendo que está en el path)
                    try:
                        # Intentar importar desde el archivo principal
                        logger.info(
                            "Intentando importar MarketScanner desde el archivo principal..."
                        )
                        # Asegurar que el directorio raíz está en el path
                        root_dir = os.path.dirname(
                            os.path.dirname(os.path.abspath(__file__))
                        )
                        if root_dir not in sys.path:
                            sys.path.append(root_dir)

                        # Intentar importar desde 📊_InversorIA_Pro.py
                        main_file = os.path.join(root_dir, "📊_InversorIA_Pro.py")
                        if os.path.exists(main_file):
                            status_placeholder.info(
                                "Importando MarketScanner desde InversorIA Pro..."
                            )
                            # Usar importlib para cargar el módulo
                            import importlib.util

                            spec = importlib.util.spec_from_file_location(
                                "main_module", main_file
                            )
                            main_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(main_module)

                            # Verificar si existe la clase MarketScanner
                            if hasattr(main_module, "MarketScanner"):
                                MarketScanner = main_module.MarketScanner
                                logger.info(
                                    "MarketScanner importado correctamente desde el archivo principal"
                                )

                                # Crear instancia con el diccionario de símbolos
                                symbols_dict = {
                                    sector: [
                                        symbol
                                        for symbol, info in self.company_info.items()
                                        if info.get("sector") == sector
                                    ]
                                    for sector in self.sectors
                                }

                                market_scanner = MarketScanner()
                                st.session_state.market_scanner = market_scanner
                                logger.info(
                                    "Creado nuevo market_scanner desde archivo principal"
                                )
                            else:
                                logger.warning(
                                    "No se encontró la clase MarketScanner en el archivo principal"
                                )
                        else:
                            logger.warning(
                                f"No se encontró el archivo principal en {main_file}"
                            )
                    except Exception as main_error:
                        logger.warning(
                            f"Error importando desde archivo principal: {str(main_error)}"
                        )

                        # Si falla, intentar importar desde market_scanner.py
                        try:
                            status_placeholder.info(
                                "Importando MarketScanner desde market_scanner.py..."
                            )
                            from market_scanner import MarketScanner

                            # Crear instancia con el diccionario de símbolos
                            symbols_dict = {
                                sector: [
                                    symbol
                                    for symbol, info in self.company_info.items()
                                    if info.get("sector") == sector
                                ]
                                for sector in self.sectors
                            }

                            market_scanner = MarketScanner(symbols_dict)
                            st.session_state.market_scanner = market_scanner
                            logger.info(
                                "Creado nuevo market_scanner desde market_scanner.py"
                            )
                        except Exception as scanner_error:
                            logger.error(
                                f"Error importando MarketScanner desde market_scanner.py: {str(scanner_error)}"
                            )
                            status_placeholder.error(
                                "No se pudo inicializar el escaner de mercado. Verifique los logs para más detalles."
                            )
                except Exception as import_error:
                    logger.error(
                        f"Error general importando MarketScanner: {str(import_error)}"
                    )
                    status_placeholder.error(
                        "Error inicializando el escaner de mercado. Verifique los logs para más detalles."
                    )
                    market_scanner = None

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
                                scan_result = market_scanner.scan_symbol(symbol)
                                if scan_result and "recommendation" in scan_result:
                                    # Mapear el formato del market_scanner al formato de señal
                                    direction = scan_result.get("recommendation")
                                    confidence = scan_result.get("confidence", "Media")
                                    price = scan_result.get("price", 0.0)
                                    strategy = scan_result.get(
                                        "strategy", "Análisis Técnico"
                                    )
                                    timeframe = scan_result.get(
                                        "timeframe", "Medio Plazo"
                                    )
                                    analysis = scan_result.get("summary", "")

                                    # Filtrar por nivel de confianza
                                    if (
                                        confidence in [confidence_threshold, "Alta"]
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
                                            "detailed_analysis": scan_result,
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
                        df = self.fetch_market_data(symbol, period=f"{days}d")

                        if df is None or df.empty:
                            logger.warning(
                                f"No se pudieron obtener datos para {symbol}"
                            )
                            continue

                        # Obtener contexto de mercado completo
                        market_context = (
                            self.get_market_context(symbol)
                            if hasattr(self, "get_market_context")
                            else None
                        )

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

                            # Crear objeto de análisis detallado
                            detailed_analysis = {
                                "symbol": symbol,
                                "recommendation": direction,
                                "confidence_level": confidence,
                                "timeframe": timeframe,
                                "strategy": strategy,
                                "analysis_summary": analysis_summary,
                                "price": price,
                                "change_percent": change,
                                "signals": signals,
                                "support_levels": market_context.get(
                                    "support_resistance", {}
                                ).get("supports", []),
                                "resistance_levels": market_context.get(
                                    "support_resistance", {}
                                ).get("resistances", []),
                                "market_context": market_context,
                                "company_info": self.company_info.get(symbol, {}),
                            }

                        else:
                            # Si no hay contexto de mercado, usar análisis básico
                            detailed_analysis = self._create_basic_analysis(symbol, df)
                            direction = detailed_analysis.get(
                                "recommendation", "NEUTRAL"
                            )
                            confidence = detailed_analysis.get(
                                "confidence_level", "Baja"
                            )
                            timeframe = detailed_analysis.get(
                                "timeframe", "Medio Plazo"
                            )
                            strategy = detailed_analysis.get(
                                "strategy", "Análisis Técnico"
                            )
                            analysis_summary = detailed_analysis.get(
                                "analysis_summary", "Análisis no disponible"
                            )
                            price = float(df["Close"].iloc[-1])

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

    def get_detailed_analysis(self, symbol):
        """Genera un análisis detallado para un símbolo específico en tiempo real"""
        try:
            logger.info(f"Generando análisis detallado en tiempo real para {symbol}")

            # Obtener datos de mercado para análisis detallado (90 días)
            df = self.fetch_market_data(symbol, period="90d")

            if df is None or df.empty:
                logger.warning(f"No se pudieron obtener datos para {symbol}")
                return {"error": f"No hay datos disponibles para {symbol}"}

            # Obtener contexto de mercado completo
            market_context = (
                self.get_market_context(symbol)
                if hasattr(self, "get_market_context")
                else None
            )

            # Crear análisis detallado
            if market_context and "error" not in market_context:
                # Extraer información relevante del contexto de mercado
                signals = market_context.get("signals", {})
                price = market_context.get("last_price", float(df["Close"].iloc[-1]))
                change = market_context.get("change_percent", 0)

                # Obtener señal general
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
                    elif signal_data.get("confidence", "").lower() == "moderada":
                        confidence = "Media"

                # Obtener estrategia
                strategy = "Análisis Técnico"
                if "options" in signals:
                    strategy = signals["options"].get("strategy", "Análisis Técnico")

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

                # Obtener soportes y resistencias del contexto de mercado
                support_levels = market_context.get("support_resistance", {}).get(
                    "supports", []
                )
                resistance_levels = market_context.get("support_resistance", {}).get(
                    "resistances", []
                )

                # Si no hay soportes/resistencias en el contexto, calcularlos
                if not support_levels or not resistance_levels:
                    try:
                        support_levels, resistance_levels = (
                            self.detect_support_resistance(df)
                        )
                    except Exception as sr_error:
                        logger.warning(
                            f"Error detectando soportes/resistencias: {str(sr_error)}"
                        )
                        support_levels = []
                        resistance_levels = []

                # Obtener líneas de tendencia
                trend_lines = {"bullish": [], "bearish": []}
                try:
                    bullish_lines, bearish_lines = self.detect_trend_lines(df)
                    trend_lines = {"bullish": bullish_lines, "bearish": bearish_lines}
                except Exception as tl_error:
                    logger.warning(
                        f"Error detectando líneas de tendencia: {str(tl_error)}"
                    )

                # Obtener patrones de velas
                candle_patterns = []
                try:
                    if hasattr(self, "detect_candle_patterns"):
                        candle_patterns = self.detect_candle_patterns(df)
                except Exception as cp_error:
                    logger.warning(
                        f"Error detectando patrones de velas: {str(cp_error)}"
                    )

                # Obtener análisis multi-timeframe si está disponible
                multi_timeframe = market_context.get("multi_timeframe", {})

                # Obtener análisis web si está disponible
                web_insights = market_context.get("web_insights", {})

                # Crear objeto de análisis detallado
                analysis = {
                    "symbol": symbol,
                    "recommendation": direction,
                    "confidence_level": confidence,
                    "timeframe": timeframe,
                    "strategy": strategy,
                    "analysis_summary": analysis_summary,
                    "price": price,
                    "change_percent": change,
                    "signals": signals,
                    "support_levels": support_levels,
                    "resistance_levels": resistance_levels,
                    "trend_lines": trend_lines,
                    "candle_patterns": candle_patterns,
                    "multi_timeframe": multi_timeframe,
                    "web_insights": web_insights,
                    "market_context": market_context,
                    "company_info": self.company_info.get(symbol, {}),
                }

                # Mejorar análisis si está disponible la función
                if hasattr(self, "improve_technical_analysis"):
                    try:
                        analysis = self.improve_technical_analysis(df, analysis)
                    except Exception as improve_error:
                        logger.warning(
                            f"Error mejorando análisis: {str(improve_error)}"
                        )

                # Añadir análisis experto para señales de alta confianza
                if confidence == "Alta":
                    # 1. Intentar obtener análisis experto usando process_expert_analysis
                    if hasattr(self, "process_expert_analysis"):
                        try:
                            logger.info(f"Generando análisis experto para {symbol}")
                            expert_analysis = self.process_expert_analysis(
                                symbol, market_context
                            )
                            if expert_analysis and "error" not in expert_analysis:
                                analysis["expert_analysis"] = expert_analysis
                                logger.info(f"Análisis experto generado para {symbol}")
                        except Exception as expert_error:
                            logger.warning(
                                f"Error generando análisis experto: {str(expert_error)}"
                            )

                    # 2. Intentar obtener análisis del Trading Specialist
                    try:
                        if "trading_specialist" in st.session_state:
                            trading_specialist = st.session_state.trading_specialist
                            logger.info(
                                f"Obteniendo análisis del Trading Specialist para {symbol}"
                            )

                            # Intentar obtener análisis del Trading Specialist
                            specialist_analysis = (
                                trading_specialist.get_analysis(symbol)
                                if hasattr(trading_specialist, "get_analysis")
                                else None
                            )

                            if specialist_analysis and isinstance(
                                specialist_analysis, dict
                            ):
                                analysis["trading_specialist"] = specialist_analysis
                                logger.info(
                                    f"Análisis del Trading Specialist obtenido para {symbol}"
                                )
                        else:
                            # Intentar importar el Trading Specialist
                            try:
                                import sys
                                import os

                                # Asegurar que el directorio raíz está en el path
                                root_dir = os.path.dirname(
                                    os.path.dirname(os.path.abspath(__file__))
                                )
                                if root_dir not in sys.path:
                                    sys.path.append(root_dir)

                                # Intentar importar el Trading Specialist
                                try:
                                    # Verificar si ya existe en session_state
                                    if (
                                        "trading_specialist" in st.session_state
                                        and st.session_state.trading_specialist
                                        is not None
                                    ):
                                        trading_specialist = (
                                            st.session_state.trading_specialist
                                        )
                                        logger.info(
                                            "Usando Trading Specialist existente desde session_state"
                                        )
                                    else:
                                        # Intentar importar desde el archivo principal
                                        try:
                                            # Asegurar que el directorio raíz está en el path
                                            root_dir = os.path.dirname(
                                                os.path.dirname(
                                                    os.path.abspath(__file__)
                                                )
                                            )
                                            if root_dir not in sys.path:
                                                sys.path.append(root_dir)

                                            # Buscar el archivo trading_specialist.py
                                            specialist_file = os.path.join(
                                                root_dir, "trading_specialist.py"
                                            )
                                            if os.path.exists(specialist_file):
                                                # Usar importlib para cargar el módulo
                                                import importlib.util

                                                spec = importlib.util.spec_from_file_location(
                                                    "trading_specialist_module",
                                                    specialist_file,
                                                )
                                                specialist_module = (
                                                    importlib.util.module_from_spec(
                                                        spec
                                                    )
                                                )
                                                spec.loader.exec_module(
                                                    specialist_module
                                                )

                                                # Verificar si existe la clase TradingSpecialist
                                                if hasattr(
                                                    specialist_module,
                                                    "TradingSpecialist",
                                                ):
                                                    TradingSpecialist = (
                                                        specialist_module.TradingSpecialist
                                                    )
                                                    trading_specialist = (
                                                        TradingSpecialist()
                                                    )
                                                    st.session_state.trading_specialist = (
                                                        trading_specialist
                                                    )
                                                    logger.info(
                                                        "Trading Specialist importado correctamente"
                                                    )
                                                else:
                                                    logger.warning(
                                                        "No se encontró la clase TradingSpecialist en el módulo"
                                                    )
                                            else:
                                                logger.warning(
                                                    f"No se encontró el archivo trading_specialist.py en {root_dir}"
                                                )
                                        except Exception as import_error:
                                            logger.warning(
                                                f"Error importando Trading Specialist: {str(import_error)}"
                                            )

                                    # Obtener análisis si se pudo cargar el Trading Specialist
                                    if (
                                        "trading_specialist" in locals()
                                        and trading_specialist is not None
                                    ):
                                        specialist_analysis = (
                                            trading_specialist.get_analysis(symbol)
                                        )
                                        if specialist_analysis:
                                            analysis["trading_specialist"] = (
                                                specialist_analysis
                                            )
                                            logger.info(
                                                f"Análisis del Trading Specialist obtenido para {symbol}"
                                            )
                                except ImportError:
                                    logger.warning(
                                        "No se pudo importar TradingSpecialist"
                                    )
                            except Exception as import_error:
                                logger.warning(
                                    f"Error importando Trading Specialist: {str(import_error)}"
                                )
                    except Exception as specialist_error:
                        logger.warning(
                            f"Error obteniendo análisis del Trading Specialist: {str(specialist_error)}"
                        )

                    # 3. Obtener resumen técnico si está disponible
                    try:
                        if hasattr(self, "get_technical_summary"):
                            technical_summary = self.get_technical_summary(
                                symbol, market_context
                            )
                            if technical_summary and "error" not in technical_summary:
                                analysis["technical_summary"] = technical_summary
                                logger.info(f"Resumen técnico generado para {symbol}")
                    except Exception as summary_error:
                        logger.warning(
                            f"Error generando resumen técnico: {str(summary_error)}"
                        )

                return analysis
            else:
                # Si no hay contexto de mercado, usar análisis básico
                analysis = self._create_basic_analysis(symbol, df)

                # Añadir soportes y resistencias
                try:
                    supports, resistances = self.detect_support_resistance(df)
                    analysis["support_levels"] = supports
                    analysis["resistance_levels"] = resistances
                except Exception as sr_error:
                    logger.warning(
                        f"Error detectando soportes/resistencias: {str(sr_error)}"
                    )
                    analysis["support_levels"] = []
                    analysis["resistance_levels"] = []

                # Añadir líneas de tendencia
                try:
                    bullish_lines, bearish_lines = self.detect_trend_lines(df)
                    analysis["trend_lines"] = {
                        "bullish": bullish_lines,
                        "bearish": bearish_lines,
                    }
                except Exception as tl_error:
                    logger.warning(
                        f"Error detectando líneas de tendencia: {str(tl_error)}"
                    )
                    analysis["trend_lines"] = {"bullish": [], "bearish": []}

                # Añadir patrones de velas
                try:
                    if hasattr(self, "detect_candle_patterns"):
                        analysis["candle_patterns"] = self.detect_candle_patterns(df)
                    else:
                        analysis["candle_patterns"] = []
                except Exception as cp_error:
                    logger.warning(
                        f"Error detectando patrones de velas: {str(cp_error)}"
                    )
                    analysis["candle_patterns"] = []

                # Añadir información de la empresa
                analysis["company_info"] = self.company_info.get(symbol, {})

                return analysis
        except Exception as e:
            logger.error(f"Error generando análisis detallado para {symbol}: {str(e)}")
            # No usar datos simulados, retornar error
            return {"error": f"Error analizando {symbol}: {str(e)}"}

    def get_real_time_market_sentiment(self):
        """Obtiene el sentimiento actual del mercado en tiempo real"""
        try:
            logger.info("Obteniendo sentimiento de mercado en tiempo real")

            # Mostrar mensaje de estado
            status_placeholder = st.empty()
            status_placeholder.info("Analizando sentimiento de mercado...")

            # Intentar obtener datos del contexto de mercado global
            market_context = None
            try:
                # Intentar obtener datos desde el archivo principal
                if (
                    "market_scanner" in st.session_state
                    and st.session_state.market_scanner is not None
                ):
                    market_scanner = st.session_state.market_scanner
                    # Verificar si el market_scanner tiene método get_market_sentiment
                    if hasattr(market_scanner, "get_market_sentiment"):
                        try:
                            sentiment = market_scanner.get_market_sentiment()
                            if sentiment and isinstance(sentiment, dict):
                                status_placeholder.empty()
                                return sentiment
                        except Exception as scanner_error:
                            logger.warning(
                                f"Error usando market_scanner.get_market_sentiment: {str(scanner_error)}"
                            )

                # Si no se pudo obtener desde market_scanner, intentar con get_market_context
                # Obtener contexto de mercado del S&P 500 como referencia
                market_context = (
                    self.get_market_context("^GSPC")
                    if hasattr(self, "get_market_context")
                    else None
                )
            except Exception as context_error:
                logger.warning(
                    f"Error obteniendo contexto de mercado global: {str(context_error)}"
                )

            # Si tenemos contexto de mercado, extraer información relevante
            if market_context and "error" not in market_context:
                # Extraer datos de sentimiento si están disponibles
                market_sentiment = market_context.get("market_sentiment", {})
                if market_sentiment:
                    # Usar datos de sentimiento del contexto
                    status_placeholder.empty()
                    return {
                        "overall": market_sentiment.get("overall", "Neutral"),
                        "vix": market_sentiment.get("vix", "N/A"),
                        "sp500_trend": market_sentiment.get("sp500_trend", "N/A"),
                        "technical_indicators": market_sentiment.get(
                            "technical_indicators", "N/A"
                        ),
                        "volume": market_sentiment.get("volume", "N/A"),
                        "notes": f"Datos en tiempo real - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    }

            # Si no hay datos de sentimiento en el contexto, calcularlos manualmente
            # Obtener datos del VIX
            vix_value = "N/A"
            vix_status = "N/A"
            try:
                # Intentar importar get_vix_level desde market_utils
                try:
                    from market_utils import get_vix_level

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
                except Exception as import_error:
                    logger.warning(
                        f"Error importando get_vix_level: {str(import_error)}"
                    )
                    # Intentar obtener datos del VIX directamente
                    vix_df = self.fetch_market_data("^VIX", period="30d")
                    if vix_df is not None and not vix_df.empty:
                        vix_value = round(float(vix_df["Close"].iloc[-1]), 2)
                        if vix_value < 20:
                            vix_status = "Volatilidad Baja"
                        elif vix_value < 30:
                            vix_status = "Volatilidad Moderada"
                        else:
                            vix_status = "Volatilidad Alta"
            except Exception as vix_error:
                logger.warning(f"Error obteniendo datos del VIX: {str(vix_error)}")

            # Obtener datos del S&P 500
            try:
                sp500_df = self.fetch_market_data("^GSPC", period="200d")

                if sp500_df is None or sp500_df.empty:
                    raise ValueError("No se pudieron obtener datos del S&P 500")

                # Calcular tendencia del S&P 500
                current_price = sp500_df["Close"].iloc[-1]
                sma50 = sp500_df["Close"].rolling(window=50).mean().iloc[-1]
                sma200 = sp500_df["Close"].rolling(window=200).mean().iloc[-1]

                if current_price > sma50 and current_price > sma200:
                    sp500_trend = "Alcista - Por encima de SMA 50 y 200"
                elif current_price > sma50:
                    sp500_trend = "Alcista - Por encima de SMA 50"
                elif current_price > sma200:
                    sp500_trend = "Mixto - Por encima de SMA 200"
                else:
                    sp500_trend = "Bajista - Por debajo de SMA 50 y 200"

                # Calcular indicadores técnicos
                bullish_count = 0
                bearish_count = 0

                # RSI
                rsi = self._calculate_rsi(sp500_df)
                if rsi > 50:
                    bullish_count += 1
                else:
                    bearish_count += 1

                # MACD
                macd, signal = self._calculate_macd(sp500_df)
                if macd > signal:
                    bullish_count += 1
                else:
                    bearish_count += 1

                # Tendencia de precio
                if current_price > sp500_df["Close"].iloc[-10]:
                    bullish_count += 1
                else:
                    bearish_count += 1

                # Volumen
                avg_volume = sp500_df["Volume"].rolling(window=30).mean().iloc[-1]
                current_volume = sp500_df["Volume"].iloc[-1]

                if current_volume > avg_volume:
                    volume_status = "Por encima del promedio de 30 días"
                else:
                    volume_status = "Por debajo del promedio de 30 días"

                # Determinar sentimiento general
                if bullish_count > bearish_count:
                    overall = "Alcista"
                elif bearish_count > bullish_count:
                    overall = "Bajista"
                else:
                    overall = "Neutral"

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
            except Exception as sp500_error:
                logger.error(f"Error analizando S&P 500: {str(sp500_error)}")

                # Crear objeto de sentimiento con datos limitados
                return {
                    "overall": "Neutral",
                    "vix": f"{vix_value} - {vix_status}",
                    "sp500_trend": "No disponible",
                    "technical_indicators": "No disponible",
                    "volume": "No disponible",
                    "notes": f"Datos parciales - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                }

        except Exception as e:
            logger.error(f"Error obteniendo sentimiento de mercado: {str(e)}")
            # No usar datos simulados, retornar datos básicos
            return {
                "overall": "Neutral",
                "vix": "N/A",
                "sp500_trend": "No disponible",
                "technical_indicators": "No disponible",
                "volume": "No disponible",
                "notes": f"Error obteniendo datos - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            }

    def get_real_time_market_news(self):
        """Obtiene noticias relevantes del mercado en tiempo real"""
        try:
            logger.info("Obteniendo noticias de mercado en tiempo real")

            # Mostrar mensaje de estado
            status_placeholder = st.empty()
            status_placeholder.info("Buscando noticias de mercado...")

            # Intentar obtener noticias desde el market_scanner
            if (
                "market_scanner" in st.session_state
                and st.session_state.market_scanner is not None
            ):
                market_scanner = st.session_state.market_scanner
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

            # Intentar obtener noticias del contexto de mercado global
            market_context = None
            try:
                # Obtener contexto de mercado del S&P 500 como referencia
                market_context = (
                    self.get_market_context("^GSPC")
                    if hasattr(self, "get_market_context")
                    else None
                )
            except Exception as context_error:
                logger.warning(
                    f"Error obteniendo contexto de mercado global: {str(context_error)}"
                )

            # Si tenemos contexto de mercado, extraer noticias si están disponibles
            if market_context and "error" not in market_context:
                # Extraer noticias si están disponibles
                news_data = market_context.get("news", [])
                if news_data and len(news_data) > 0:
                    # Formatear noticias del contexto
                    formatted_news = []
                    for news in news_data:
                        formatted_news.append(
                            {
                                "title": news.get("title", "Sin título"),
                                "summary": news.get(
                                    "summary",
                                    news.get("description", "Sin descripción"),
                                ),
                                "source": news.get("source", "Fuente desconocida"),
                                "url": news.get("url", ""),
                                "date": news.get(
                                    "date", datetime.now() - timedelta(days=1)
                                ),
                                "impact": news.get("impact", "Medio"),
                            }
                        )

                    logger.info(
                        f"Se encontraron {len(formatted_news)} noticias en tiempo real"
                    )
                    status_placeholder.empty()
                    return formatted_news

            # Si no hay noticias en el contexto, intentar obtenerlas de otras fuentes
            # Intentar obtener noticias para símbolos importantes
            important_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY"]
            all_news = []

            for symbol in important_symbols:
                try:
                    # Obtener contexto específico del símbolo
                    symbol_context = (
                        self.get_market_context(symbol)
                        if hasattr(self, "get_market_context")
                        else None
                    )

                    if symbol_context and "error" not in symbol_context:
                        # Extraer noticias específicas del símbolo
                        symbol_news = symbol_context.get("news", [])

                        if symbol_news and len(symbol_news) > 0:
                            # Formatear y añadir noticias
                            for news in symbol_news:
                                # Evitar duplicados verificando títulos
                                if not any(
                                    existing["title"] == news.get("title", "")
                                    for existing in all_news
                                ):
                                    all_news.append(
                                        {
                                            "title": news.get("title", "Sin título"),
                                            "summary": news.get(
                                                "summary",
                                                news.get(
                                                    "description", "Sin descripción"
                                                ),
                                            ),
                                            "source": news.get(
                                                "source", "Fuente desconocida"
                                            ),
                                            "url": news.get("url", ""),
                                            "date": news.get(
                                                "date",
                                                datetime.now() - timedelta(days=1),
                                            ),
                                            "impact": news.get("impact", "Medio"),
                                        }
                                    )
                except Exception as symbol_error:
                    logger.warning(
                        f"Error obteniendo noticias para {symbol}: {str(symbol_error)}"
                    )

            # Si encontramos noticias, devolverlas
            if all_news and len(all_news) > 0:
                logger.info(
                    f"Se encontraron {len(all_news)} noticias de símbolos específicos"
                )
                return all_news

            # Si no hay noticias disponibles, crear algunas noticias básicas basadas en el mercado actual
            logger.warning(
                "No se encontraron noticias en tiempo real, generando noticias básicas"
            )

            # Obtener datos del S&P 500 para generar noticias básicas
            try:
                sp500_df = self.fetch_market_data("^GSPC", period="5d")
                if sp500_df is not None and not sp500_df.empty:
                    # Calcular cambio porcentual
                    current_price = sp500_df["Close"].iloc[-1]
                    prev_price = sp500_df["Close"].iloc[-2]
                    change_pct = ((current_price - prev_price) / prev_price) * 100

                    # Generar noticia basada en el movimiento del mercado
                    market_news = [
                        {
                            "title": f"S&P 500 {'+' if change_pct >= 0 else '-'}{abs(change_pct):.2f}%: {self._get_market_headline(change_pct)}",
                            "summary": f"El índice S&P 500 cerró en {current_price:.2f} puntos, {'+' if change_pct >= 0 else '-'}{abs(change_pct):.2f}% respecto al cierre anterior. {self._get_market_analysis(change_pct)}",
                            "source": "Análisis de Mercado",
                            "url": "",
                            "date": datetime.now(),
                            "impact": "Alto" if abs(change_pct) > 1 else "Medio",
                        }
                    ]

                    # Añadir noticia sobre el VIX si está disponible
                    try:
                        vix_df = self.fetch_market_data("^VIX", period="5d")
                        if vix_df is not None and not vix_df.empty:
                            vix_value = vix_df["Close"].iloc[-1]
                            vix_prev = vix_df["Close"].iloc[-2]
                            vix_change = ((vix_value - vix_prev) / vix_prev) * 100

                            vix_news = {
                                "title": f"VIX {'+' if vix_change >= 0 else '-'}{abs(vix_change):.2f}%: {self._get_vix_headline(vix_value, vix_change)}",
                                "summary": f"El índice de volatilidad VIX se situó en {vix_value:.2f} puntos, {'+' if vix_change >= 0 else '-'}{abs(vix_change):.2f}% respecto al día anterior. {self._get_vix_analysis(vix_value)}",
                                "source": "Análisis de Volatilidad",
                                "url": "",
                                "date": datetime.now(),
                                "impact": (
                                    "Alto"
                                    if vix_value > 25 or abs(vix_change) > 10
                                    else "Medio"
                                ),
                            }

                            market_news.append(vix_news)
                    except Exception as vix_error:
                        logger.warning(
                            f"Error generando noticia del VIX: {str(vix_error)}"
                        )

                    return market_news
            except Exception as market_error:
                logger.warning(f"Error generando noticias básicas: {str(market_error)}")

            # Si todo lo demás falla, devolver una lista vacía
            logger.warning("No se pudieron generar noticias, devolviendo lista vacía")
            return []

        except Exception as e:
            logger.error(f"Error obteniendo noticias de mercado: {str(e)}")
            # No usar datos simulados, devolver lista vacía
            return []

    def _get_market_headline(self, change_pct):
        """Genera un titular basado en el cambio porcentual del mercado"""
        if change_pct > 2:
            return "Fuerte repunte en Wall Street"
        elif change_pct > 1:
            return "Mercado cierra con ganancias sólidas"
        elif change_pct > 0.2:
            return "Mercado avanza moderadamente"
        elif change_pct > -0.2:
            return "Mercado cierra sin cambios significativos"
        elif change_pct > -1:
            return "Mercado retrocede ligeramente"
        elif change_pct > -2:
            return "Mercado registra pérdidas moderadas"
        else:
            return "Fuerte caída en Wall Street"

    def _get_market_analysis(self, change_pct):
        """Genera un análisis basado en el cambio porcentual del mercado"""
        if change_pct > 1.5:
            return "Los inversores muestran optimismo ante las perspectivas económicas y los resultados corporativos positivos."
        elif change_pct > 0.5:
            return "El sentimiento positivo predomina en el mercado, impulsado por datos económicos favorables."
        elif change_pct > -0.5:
            return "Los inversores se mantienen cautelosos mientras evalúan los próximos movimientos de la Fed y los datos económicos."
        elif change_pct > -1.5:
            return "La incertidumbre sobre las políticas monetarias y las tensiones geoeconómicas presionan al mercado."
        else:
            return "Los temores sobre la inflación y una posible recesión generan ventas masivas en el mercado."

    def _get_vix_headline(self, vix_value, vix_change):
        """Genera un titular basado en el valor y cambio del VIX"""
        # Usar tanto el valor como el cambio para generar un titular más informativo
        if vix_value > 30:
            if vix_change > 10:
                return "Fuerte aumento de volatilidad sacude los mercados"
            else:
                return "Alta volatilidad continúa presionando los mercados"
        elif vix_value > 20:
            if vix_change > 5:
                return "Aumenta la incertidumbre en Wall Street"
            else:
                return "Incertidumbre moderada persiste en los mercados"
        elif vix_value > 15:
            if vix_change > 0:
                return "Ligero incremento de volatilidad en los mercados"
            else:
                return "Volatilidad moderada en los mercados"
        else:
            if vix_change < -5:
                return "La volatilidad cae a mínimos, reflejando optimismo"
            else:
                return "Baja volatilidad refleja calma en los mercados"

    def _get_vix_analysis(self, vix_value):
        """Genera un análisis basado en el valor del VIX"""
        if vix_value > 30:
            return "Los niveles elevados del VIX indican un alto grado de nerviosismo entre los inversores, quienes buscan protección ante posibles caídas del mercado."
        elif vix_value > 20:
            return "El incremento en el VIX sugiere que los inversores están aumentando sus coberturas ante la incertidumbre en el mercado."
        elif vix_value > 15:
            return "Los niveles moderados del VIX reflejan un equilibrio entre optimismo y cautela en el mercado."
        else:
            return "El bajo nivel del VIX indica complacencia en el mercado, con inversores mostrando poca preocupación por riesgos a corto plazo."

    def _calculate_rsi(self, df, window=14):
        """Calcula el RSI para un DataFrame"""
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=window).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        return rsi

    def _calculate_macd(self, df):
        """Calcula el MACD para un DataFrame"""
        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd.iloc[-1], signal.iloc[-1]

    def _create_basic_analysis(self, symbol, df):
        """Crea un análisis básico cuando no hay market_scanner disponible"""
        try:
            # Calcular indicadores básicos
            current_price = df["Close"].iloc[-1]
            prev_price = df["Close"].iloc[-2] if len(df) > 1 else current_price
            price_change = ((current_price - prev_price) / prev_price) * 100

            # Calcular medias móviles
            sma20 = (
                df["Close"].rolling(window=20).mean().iloc[-1]
                if len(df) >= 20
                else current_price
            )
            sma50 = (
                df["Close"].rolling(window=50).mean().iloc[-1]
                if len(df) >= 50
                else current_price
            )
            sma200 = (
                df["Close"].rolling(window=200).mean().iloc[-1]
                if len(df) >= 200
                else current_price
            )

            # Calcular RSI
            rsi = self._calculate_rsi(df) if len(df) >= 14 else 50

            # Calcular MACD
            macd, signal = self._calculate_macd(df) if len(df) >= 26 else (0, 0)

            # Intentar detectar soportes y resistencias
            support_levels = []
            resistance_levels = []
            try:
                if hasattr(self, "detect_support_resistance"):
                    support_levels, resistance_levels = self.detect_support_resistance(
                        df
                    )
            except Exception as sr_error:
                logger.warning(
                    f"Error detectando soportes/resistencias: {str(sr_error)}"
                )

            # Intentar detectar patrones de velas
            candle_patterns = []
            try:
                if hasattr(self, "detect_candle_patterns"):
                    candle_patterns = self.detect_candle_patterns(df)
            except Exception as cp_error:
                logger.warning(f"Error detectando patrones de velas: {str(cp_error)}")

            # Determinar tendencia
            if (
                current_price > sma20
                and current_price > sma50
                and current_price > sma200
            ):
                trend = "ALCISTA_FUERTE"
                confidence = "Alta"
                recommendation = "CALL"
            elif current_price > sma20 and current_price > sma50:
                trend = "ALCISTA"
                confidence = "Media"
                recommendation = "CALL"
            elif (
                current_price < sma20
                and current_price < sma50
                and current_price < sma200
            ):
                trend = "BAJISTA_FUERTE"
                confidence = "Alta"
                recommendation = "PUT"
            elif current_price < sma20 and current_price < sma50:
                trend = "BAJISTA"
                confidence = "Media"
                recommendation = "PUT"
            else:
                trend = "LATERAL"
                confidence = "Baja"
                recommendation = "NEUTRAL"

            # Ajustar por RSI y MACD
            if rsi > 70 and trend.startswith("ALCISTA"):
                confidence = "Alta" if trend == "ALCISTA_FUERTE" else "Media"
            elif rsi < 30 and trend.startswith("BAJISTA"):
                confidence = "Alta" if trend == "BAJISTA_FUERTE" else "Media"

            if macd > signal and trend.startswith("ALCISTA"):
                confidence = "Alta" if trend == "ALCISTA_FUERTE" else "Media"
            elif macd < signal and trend.startswith("BAJISTA"):
                confidence = "Alta" if trend == "BAJISTA_FUERTE" else "Media"

            # Determinar estrategia
            if trend.startswith("ALCISTA"):
                if current_price > sma20 * 1.05:  # 5% por encima de SMA20
                    strategy = "Sobrecompra - Posible Corrección"
                else:
                    strategy = "Tendencia Alcista"
            elif trend.startswith("BAJISTA"):
                if current_price < sma20 * 0.95:  # 5% por debajo de SMA20
                    strategy = "Sobreventa - Posible Rebote"
                else:
                    strategy = "Tendencia Bajista"
            else:
                strategy = "Rango Lateral"

            # Determinar timeframe
            if trend.endswith("FUERTE"):
                timeframe = "Medio Plazo"
            else:
                timeframe = "Corto Plazo"

            # Crear resumen de análisis
            if recommendation == "CALL":
                analysis_summary = f"{symbol} muestra tendencia alcista con precio actual de ${current_price:.2f}, un {price_change:.2f}% por encima del cierre anterior. RSI en {rsi:.1f} indica {' sobrecompra' if rsi > 70 else ' impulso alcista'}."

                # Añadir información de soportes si están disponibles
                if support_levels and len(support_levels) > 0:
                    analysis_summary += f" Soporte clave en ${support_levels[0]:.2f}."

            elif recommendation == "PUT":
                analysis_summary = f"{symbol} muestra tendencia bajista con precio actual de ${current_price:.2f}, un {abs(price_change):.2f}% por debajo del cierre anterior. RSI en {rsi:.1f} indica {' sobreventa' if rsi < 30 else ' debilidad'}."

                # Añadir información de resistencias si están disponibles
                if resistance_levels and len(resistance_levels) > 0:
                    analysis_summary += (
                        f" Resistencia clave en ${resistance_levels[0]:.2f}."
                    )

            else:
                analysis_summary = f"{symbol} se encuentra en rango lateral con precio actual de ${current_price:.2f}. Los indicadores técnicos no muestran una dirección clara."

            # Añadir información de patrones de velas si están disponibles
            if candle_patterns and len(candle_patterns) > 0:
                analysis_summary += f" Patrón de velas detectado: {candle_patterns[0]}."

            # Crear objeto de análisis
            analysis = {
                "symbol": symbol,
                "recommendation": recommendation,
                "confidence_level": confidence,
                "timeframe": timeframe,
                "strategy": strategy,
                "analysis_summary": analysis_summary,
                "price": current_price,
                "price_change": price_change,
                "rsi": rsi,
                "macd": float(macd),
                "macd_signal": float(signal),
                "sma20": float(sma20),
                "sma50": float(sma50),
                "sma200": float(sma200),
                "trend": trend,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "candle_patterns": candle_patterns,
            }

            return analysis
        except Exception as e:
            logger.error(f"Error creando análisis básico para {symbol}: {str(e)}")
            return None


# Clase para gestionar la conexión a la base de datos
class DatabaseManager:
    """Gestiona la conexión y operaciones con la base de datos MariaDB"""

    def __init__(self):
        """Inicializa el gestor de base de datos con credenciales desde secrets"""
        try:
            # Obtener credenciales desde secrets.toml
            self.db_config = {
                "host": st.secrets.get("db_host", "localhost"),
                "user": st.secrets.get("db_user", ""),
                "password": st.secrets.get("db_password", ""),
                "database": st.secrets.get("db_name", "inversoria"),
                "port": st.secrets.get("db_port", 3306),
            }
            self.connection = None
            logger.info("Configuración de base de datos inicializada")
        except Exception as e:
            logger.error(
                f"Error inicializando configuración de base de datos: {str(e)}"
            )
            self.db_config = None

    def connect(self):
        """Establece conexión con la base de datos"""
        if not self.db_config:
            return False

        try:
            # En modo desarrollo, simular conexión exitosa si no hay credenciales
            if not self.db_config.get("user") or not self.db_config.get("password"):
                logger.warning(
                    "Usando modo simulación para base de datos (no hay credenciales)"
                )
                return True

            self.connection = mysql.connector.connect(**self.db_config)
            return True
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {str(e)}")
            return False

    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexión a base de datos cerrada")

    def execute_query(self, query, params=None, fetch=True):
        """Ejecuta una consulta SQL y opcionalmente devuelve resultados"""
        # Validar que hay una consulta
        if not query:
            logger.error("No se especificó una consulta SQL")
            return None

        # Intentar conectar a la base de datos
        if not self.connect():
            logger.error("No se pudo conectar a la base de datos")
            return None

        try:
            # Verificar si estamos en modo sin conexión
            if not hasattr(self, "connection") or self.connection is None:
                logger.error("No hay conexión a la base de datos disponible")
                # Devolver lista vacía o error en lugar de datos simulados
                if "SELECT" in query.upper() and fetch:
                    logger.warning(
                        "Devolviendo lista vacía para consulta SELECT sin conexión"
                    )
                    return []
                else:
                    logger.warning(
                        "Devolviendo error para operación de escritura sin conexión"
                    )
                    return None

            # Ejecutar consulta real
            cursor = self.connection.cursor(dictionary=True)
            logger.info(f"Ejecutando consulta: {query}")
            logger.info(f"Parámetros: {params}")

            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
                logger.info(f"Consulta devuelve {len(result)} resultados")
            else:
                self.connection.commit()
                result = cursor.rowcount
                logger.info(f"Consulta afectó {result} filas")

            cursor.close()
            return result
        except mysql.connector.Error as e:
            logger.error(f"Error de MySQL: {str(e)}\nQuery: {query}")
            return None
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {str(e)}\nQuery: {query}")
            return None
        finally:
            self.disconnect()

    def _generate_sample_signals(self):
        """Genera datos de ejemplo para señales de trading (para desarrollo)"""
        return [
            {
                "id": 1,
                "symbol": "AAPL",
                "price": 175.23,
                "direction": "CALL",
                "confidence_level": "Alta",
                "timeframe": "Medio Plazo",
                "strategy": "Tendencia + Soporte",
                "category": "Tecnología",
                "analysis": "Apple muestra una fuerte tendencia alcista tras superar resistencia clave en $170.",
                "created_at": datetime.now() - timedelta(hours=4),
            },
            {
                "id": 2,
                "symbol": "MSFT",
                "price": 340.50,
                "direction": "CALL",
                "confidence_level": "Media",
                "timeframe": "Corto Plazo",
                "strategy": "Rebote en Soporte",
                "category": "Tecnología",
                "analysis": "Microsoft ha rebotado en soporte clave con aumento de volumen.",
                "created_at": datetime.now() - timedelta(hours=8),
            },
        ]

    def _generate_sample_email_logs(self):
        """Genera datos de ejemplo para logs de correo (para desarrollo)"""
        return [
            {
                "id": 1,
                "recipients": "usuario1@example.com, usuario2@example.com",
                "subject": "InversorIA Pro - Boletín de Trading 20/05/2025",
                "content_summary": "Boletín con 3 señales",
                "signals_included": "1, 2, 4",
                "sent_at": datetime.now() - timedelta(days=1),
            }
        ]

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
        """Guarda una nueva señal de trading en la base de datos"""
        query = """INSERT INTO trading_signals
                  (symbol, price, direction, confidence_level, timeframe,
                   strategy, category, analysis, created_at)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())"""

        params = (
            signal_data.get("symbol"),
            signal_data.get("price"),
            signal_data.get("direction"),
            signal_data.get("confidence_level"),
            signal_data.get("timeframe"),
            signal_data.get("strategy"),
            signal_data.get("category"),
            signal_data.get("analysis"),
        )

        return self.execute_query(query, params, fetch=False)

    def log_email_sent(self, email_data):
        """Registra el envío de un correo electrónico"""
        query = """INSERT INTO email_logs
                  (recipients, subject, content_summary, signals_included, sent_at)
                  VALUES (%s, %s, %s, %s, NOW())"""

        params = (
            email_data.get("recipients"),
            email_data.get("subject"),
            email_data.get("content_summary"),
            email_data.get("signals_included"),
        )

        return self.execute_query(query, params, fetch=False)

    def save_market_sentiment(self, sentiment_data):
        """Guarda el sentimiento del mercado en la base de datos"""
        # Primero verificar si ya existe un registro para la fecha actual
        check_query = """SELECT id FROM market_sentiment WHERE date = CURDATE()"""
        result = self.execute_query(check_query)

        if result and len(result) > 0:
            # Si existe, actualizar el registro existente
            query = """UPDATE market_sentiment
                      SET overall = %s, vix = %s, sp500_trend = %s,
                          technical_indicators = %s, volume = %s, notes = %s
                      WHERE date = CURDATE()"""
            logger.info("Actualizando sentimiento del mercado existente para hoy")
        else:
            # Si no existe, insertar un nuevo registro
            query = """INSERT INTO market_sentiment
                      (date, overall, vix, sp500_trend, technical_indicators, volume, notes, created_at)
                      VALUES (CURDATE(), %s, %s, %s, %s, %s, %s, NOW())"""
            logger.info("Insertando nuevo sentimiento del mercado para hoy")

        params = (
            sentiment_data.get("overall"),
            sentiment_data.get("vix"),
            sentiment_data.get("sp500_trend"),
            sentiment_data.get("technical_indicators"),
            sentiment_data.get("volume"),
            sentiment_data.get("notes", "Generado automáticamente al enviar boletín"),
        )

        return self.execute_query(query, params, fetch=False)

    def save_market_news(self, news_data):
        """Guarda una noticia del mercado en la base de datos"""
        # Verificar si la noticia ya existe (por título)
        check_query = """SELECT id FROM market_news WHERE title = %s AND DATE(news_date) = CURDATE()"""
        result = self.execute_query(check_query, (news_data.get("title"),))

        if result and len(result) > 0:
            # Si existe, no hacer nada para evitar duplicados
            logger.info(
                f"La noticia '{news_data.get('title')}' ya existe en la base de datos"
            )
            return True

        # Si no existe, insertar la noticia
        query = """INSERT INTO market_news
                  (title, summary, source, url, news_date, impact, created_at)
                  VALUES (%s, %s, %s, %s, NOW(), %s, NOW())"""

        params = (
            news_data.get("title"),
            news_data.get("summary"),
            news_data.get("source"),
            news_data.get("url", ""),
            news_data.get("impact", "Medio"),
        )

        return self.execute_query(query, params, fetch=False)


# Clase para gestionar el envío de correos electrónicos
class EmailManager:
    """Gestiona el envío de correos electrónicos con boletines de trading"""

    def __init__(self):
        """Inicializa el gestor de correos con credenciales desde secrets"""
        try:
            # Obtener credenciales desde secrets.toml
            self.email_config = {
                "smtp_server": st.secrets.get("smtp_server", "smtp.gmail.com"),
                "smtp_port": st.secrets.get("smtp_port", 587),
                "email_user": st.secrets.get("email_user", ""),
                "email_password": st.secrets.get("email_password", ""),
                "email_from": st.secrets.get("email_from", ""),
            }
            logger.info("Configuración de correo electrónico inicializada")
        except Exception as e:
            logger.error(f"Error inicializando configuración de correo: {str(e)}")
            self.email_config = None

    def send_email(self, recipients, subject, html_content, images=None):
        """Envía un correo electrónico con contenido HTML y opcionalmente imágenes"""
        # Validar que hay destinatarios
        if not recipients:
            logger.error("No se especificaron destinatarios para el correo")
            return False

        # Convertir a lista si es un string
        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.split(",") if r.strip()]

        # Validar configuración de correo
        if not self.email_config or not self.email_config.get("email_user"):
            logger.warning(
                "Configuración de correo no disponible, verificando secrets.toml"
            )
            # Intentar obtener credenciales nuevamente
            try:
                self.email_config = {
                    "smtp_server": st.secrets.get("smtp_server", "smtp.gmail.com"),
                    "smtp_port": st.secrets.get("smtp_port", 587),
                    "email_user": st.secrets.get("email_user", ""),
                    "email_password": st.secrets.get("email_password", ""),
                    "email_from": st.secrets.get("email_from", ""),
                }
                logger.info(
                    f"Credenciales de correo actualizadas: {self.email_config['email_user']}"
                )
            except Exception as e:
                logger.error(f"Error obteniendo credenciales de correo: {str(e)}")
                return False

        # Validar que hay credenciales
        if not self.email_config.get("email_user") or not self.email_config.get(
            "email_password"
        ):
            logger.error("Faltan credenciales de correo en secrets.toml")
            return False

        try:
            # Crear mensaje
            msg = MIMEMultipart("related")
            msg["Subject"] = subject
            msg["From"] = self.email_config.get("email_from") or self.email_config.get(
                "email_user"
            )
            msg["To"] = ", ".join(recipients)

            logger.info(f"Preparando correo para: {msg['To']}")

            # Adjuntar contenido HTML
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Adjuntar imágenes si existen
            if images and isinstance(images, dict):
                for img_id, img_data in images.items():
                    image = MIMEImage(img_data)
                    image.add_header("Content-ID", f"<{img_id}>")
                    msg.attach(image)

            # Conectar al servidor SMTP con timeout
            logger.info(
                f"Conectando a servidor SMTP: {self.email_config.get('smtp_server')}:{self.email_config.get('smtp_port')}"
            )

            # Verificar si el puerto es 465 (SSL) o 587 (TLS)
            port = self.email_config.get("smtp_port")
            use_ssl = port == 465

            try:
                if use_ssl:
                    # Conexión SSL directa
                    logger.info("Usando conexión SSL")
                    server = smtplib.SMTP_SSL(
                        self.email_config.get("smtp_server"),
                        port,
                        timeout=10,  # Timeout de 10 segundos
                    )
                else:
                    # Conexión normal con STARTTLS
                    logger.info("Usando conexión con STARTTLS")
                    server = smtplib.SMTP(
                        self.email_config.get("smtp_server"),
                        port,
                        timeout=10,  # Timeout de 10 segundos
                    )
                    server.starttls()

                server.set_debuglevel(
                    1
                )  # Activar debug para ver la comunicación con el servidor
            except socket.timeout:
                logger.error(
                    f"Timeout al conectar con el servidor SMTP: {self.email_config.get('smtp_server')}:{port}"
                )
                return False
            except ConnectionRefusedError:
                logger.error(
                    f"Conexión rechazada por el servidor SMTP: {self.email_config.get('smtp_server')}:{port}"
                )
                return False

            # Intentar login
            logger.info(
                f"Iniciando sesión con usuario: {self.email_config.get('email_user')}"
            )
            server.login(
                self.email_config.get("email_user"),
                self.email_config.get("email_password"),
            )

            # Enviar correo con timeout
            logger.info("Enviando mensaje...")
            try:
                server.send_message(msg)
                server.quit()
                logger.info(f"Correo enviado exitosamente a {msg['To']}")
                return True
            except smtplib.SMTPServerDisconnected:
                logger.error("El servidor SMTP se desconectó durante el envío")
                return False
            except socket.timeout:
                logger.error("Timeout durante el envío del correo")
                return False
            except Exception as e:
                logger.error(f"Error durante el envío del correo: {str(e)}")
                return False

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {str(e)}")
            logger.error(
                "Verifica tu usuario y contraseña. Si usas Gmail, asegúrate de usar una 'Clave de aplicación'."
            )
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error enviando correo: {str(e)}")
            return False

    def create_newsletter_html(self, signals, market_sentiment, news_summary):
        """Crea el contenido HTML para el boletín de trading"""
        # Fecha actual formateada
        current_date = datetime.now().strftime("%d de %B de %Y")

        # Encabezado del boletín
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .signal-high {{ background-color: #d4edda; }}
                .signal-medium {{ background-color: #fff3cd; }}
                .signal-low {{ background-color: #f8f9fa; }}
                .buy {{ color: #28a745; }}
                .sell {{ color: #dc3545; }}
                .neutral {{ color: #6c757d; }}
                .sentiment {{ padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .sentiment-bullish {{ background-color: rgba(40, 167, 69, 0.1); border-left: 4px solid #28a745; }}
                .sentiment-bearish {{ background-color: rgba(220, 53, 69, 0.1); border-left: 4px solid #dc3545; }}
                .sentiment-neutral {{ background-color: rgba(108, 117, 125, 0.1); border-left: 4px solid #6c757d; }}
                .news {{ background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .detailed-analysis {{ background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
                .detailed-analysis h3 {{ color: #007bff; margin-top: 0; }}
                .levels {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .levels div {{ flex: 1; margin-right: 10px; }}
                .levels div:last-child {{ margin-right: 0; }}
                .level-item {{ background-color: white; padding: 8px; border-radius: 4px; margin-bottom: 5px; border: 1px solid #ddd; }}
                .support {{ border-left: 3px solid #28a745; }}
                .resistance {{ border-left: 3px solid #dc3545; }}
                .pattern {{ background-color: rgba(0, 123, 255, 0.1); padding: 5px 10px; border-radius: 15px; display: inline-block; margin: 2px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>InversorIA Pro - Boletín de Trading</h1>
                <p>{current_date}</p>
            </div>
            <div class="content">
                <h2>Señales de Trading Recientes</h2>
        """

        # Tabla de señales
        if signals and len(signals) > 0:
            html += """
                <table>
                    <tr>
                        <th>Símbolo</th>
                        <th>Dirección</th>
                        <th>Precio</th>
                        <th>Confianza</th>
                        <th>Estrategia</th>
                        <th>Timeframe</th>
                    </tr>
            """

            for signal in signals:
                confidence_class = (
                    "signal-high"
                    if signal.get("confidence_level") == "Alta"
                    else (
                        "signal-medium"
                        if signal.get("confidence_level") == "Media"
                        else "signal-low"
                    )
                )
                direction_class = (
                    "buy"
                    if signal.get("direction") == "CALL"
                    else "sell" if signal.get("direction") == "PUT" else "neutral"
                )
                direction_text = (
                    "Compra"
                    if signal.get("direction") == "CALL"
                    else "Venta" if signal.get("direction") == "PUT" else "Neutral"
                )

                html += f"""
                    <tr class="{confidence_class}">
                        <td><strong>{signal.get('symbol', '')}</strong></td>
                        <td class="{direction_class}">{direction_text}</td>
                        <td>${signal.get('price', '0.00')}</td>
                        <td>{signal.get('confidence_level', 'Baja')}</td>
                        <td>{signal.get('strategy', 'N/A')}</td>
                        <td>{signal.get('timeframe', 'Corto')}</td>
                    </tr>
                """

            html += "</table>"

            # Añadir análisis detallado para señales de alta confianza
            high_confidence_signals = [
                s for s in signals if s.get("confidence_level") == "Alta"
            ]
            if high_confidence_signals:
                html += "<h2>Análisis Detallado de Señales de Alta Confianza</h2>"

                for signal in high_confidence_signals:
                    symbol = signal.get("symbol", "")
                    direction = signal.get("direction", "NEUTRAL")
                    direction_text = (
                        "Compra"
                        if direction == "CALL"
                        else "Venta" if direction == "PUT" else "Neutral"
                    )
                    direction_class = (
                        "buy"
                        if direction == "CALL"
                        else "sell" if direction == "PUT" else "neutral"
                    )

                    # Obtener detalles adicionales si están disponibles
                    detailed_analysis = signal.get("detailed_analysis", {})
                    support_levels = detailed_analysis.get("support_levels", [])
                    resistance_levels = detailed_analysis.get("resistance_levels", [])
                    candle_patterns = detailed_analysis.get("candle_patterns", [])
                    company_info = detailed_analysis.get("company_info", {})

                    # Obtener indicadores técnicos si están disponibles
                    rsi = detailed_analysis.get(
                        "rsi", detailed_analysis.get("indicators", {}).get("rsi", "N/A")
                    )
                    macd = detailed_analysis.get(
                        "macd",
                        detailed_analysis.get("indicators", {}).get("macd", "N/A"),
                    )
                    sma20 = detailed_analysis.get(
                        "sma20",
                        detailed_analysis.get("indicators", {}).get("sma20", "N/A"),
                    )
                    sma50 = detailed_analysis.get(
                        "sma50",
                        detailed_analysis.get("indicators", {}).get("sma50", "N/A"),
                    )

                    # Obtener datos adicionales si están disponibles (no se usan directamente pero podrían ser útiles en el futuro)
                    _ = detailed_analysis.get("trend", "")
                    _ = detailed_analysis.get("trend_lines", {})
                    _ = detailed_analysis.get("market_context", {})
                    _ = detailed_analysis.get("multi_timeframe", {})
                    _ = detailed_analysis.get("web_insights", {})

                    # Obtener precio y cambio porcentual
                    price = signal.get("price", "0.00")
                    change_percent = detailed_analysis.get(
                        "change_percent", detailed_analysis.get("price_change", 0)
                    )
                    change_sign = "+" if change_percent >= 0 else ""

                    html += f"""
                    <div class="detailed-analysis">
                        <h3>{symbol} - <span class="{direction_class}">{direction_text}</span></h3>
                        <p><strong>Precio Actual:</strong> ${price} <span style="color: {'#28a745' if change_percent >= 0 else '#dc3545'};">({change_sign}{change_percent:.2f}%)</span></p>
                        <p><strong>Estrategia:</strong> {signal.get('strategy', 'N/A')}</p>
                        <p><strong>Timeframe:</strong> {signal.get('timeframe', 'Corto Plazo')}</p>
                        <p><strong>Análisis:</strong> {signal.get('analysis', 'No hay análisis disponible')}</p>

                        <div style="background-color: white; padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #ddd;">
                            <h4>Indicadores Técnicos</h4>
                            <div style="display: flex; flex-wrap: wrap;">
                                <div style="flex: 1; min-width: 120px; margin: 5px;">
                                    <strong>RSI:</strong> {rsi if isinstance(rsi, str) else f"{rsi:.1f}"}
                                </div>
                                <div style="flex: 1; min-width: 120px; margin: 5px;">
                                    <strong>MACD:</strong> {macd if isinstance(macd, str) else f"{macd:.2f}"}
                                </div>
                                <div style="flex: 1; min-width: 120px; margin: 5px;">
                                    <strong>SMA20:</strong> {sma20 if isinstance(sma20, str) else f"${sma20:.2f}"}
                                </div>
                                <div style="flex: 1; min-width: 120px; margin: 5px;">
                                    <strong>SMA50:</strong> {sma50 if isinstance(sma50, str) else f"${sma50:.2f}"}
                                </div>
                            </div>
                        </div>
                    """

                    # Añadir niveles de soporte y resistencia si están disponibles
                    if support_levels or resistance_levels:
                        html += """
                        <div class="levels">
                        """

                        if support_levels:
                            html += """
                            <div>
                                <h4>Niveles de Soporte</h4>
                            """
                            for level in support_levels[
                                :3
                            ]:  # Mostrar solo los 3 primeros niveles
                                html += f"""
                                <div class="level-item support">${level:.2f}</div>
                                """
                            html += "</div>"

                        if resistance_levels:
                            html += """
                            <div>
                                <h4>Niveles de Resistencia</h4>
                            """
                            for level in resistance_levels[
                                :3
                            ]:  # Mostrar solo los 3 primeros niveles
                                html += f"""
                                <div class="level-item resistance">${level:.2f}</div>
                                """
                            html += "</div>"

                        html += "</div>"

                    # Añadir patrones de velas si están disponibles
                    if candle_patterns:
                        html += """
                        <div>
                            <h4>Patrones de Velas Detectados</h4>
                        """
                        for pattern in candle_patterns:
                            html += f"""
                            <span class="pattern">{pattern}</span>
                            """
                        html += "</div>"

                    # Añadir información de la empresa si está disponible
                    if company_info:
                        html += f"""
                        <div>
                            <h4>Información de la Empresa</h4>
                            <p><strong>Nombre:</strong> {company_info.get('name', symbol)}</p>
                            <p><strong>Sector:</strong> {company_info.get('sector', 'N/A')}</p>
                            <p><strong>Descripción:</strong> {company_info.get('description', 'No hay descripción disponible')}</p>
                        </div>
                        """

                    # Añadir análisis detallados si están disponibles (para señales de alta confianza)
                    if signal.get("confidence_level") == "Alta":
                        # 1. Añadir análisis experto si está disponible
                        expert_analysis = detailed_analysis.get("expert_analysis", {})
                        if expert_analysis:
                            # Extraer mensaje del análisis experto
                            expert_message = expert_analysis.get("message", "")
                            expert_summary = expert_analysis.get("summary", "")

                            if expert_message or expert_summary:
                                html += f"""
                                <div style="background-color: rgba(0, 123, 255, 0.1); padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 4px solid #007bff;">
                                    <h4 style="color: #007bff;">Análisis Experto</h4>
                                """

                                if expert_summary:
                                    html += f"<p><strong>Resumen:</strong> {expert_summary}</p>"

                                if expert_message:
                                    html += f"<p>{expert_message}</p>"

                                html += "</div>"

                        # 2. Añadir análisis del Trading Specialist si está disponible
                        trading_specialist = detailed_analysis.get(
                            "trading_specialist", {}
                        )
                        if trading_specialist:
                            # Extraer datos del Trading Specialist
                            specialist_recommendation = trading_specialist.get(
                                "recommendation", ""
                            )
                            specialist_analysis = trading_specialist.get("analysis", "")
                            specialist_key_points = trading_specialist.get(
                                "key_points", []
                            )

                            if (
                                specialist_recommendation
                                or specialist_analysis
                                or specialist_key_points
                            ):
                                html += f"""
                                <div style="background-color: rgba(40, 167, 69, 0.1); padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 4px solid #28a745;">
                                    <h4 style="color: #28a745;">Trading Specialist</h4>
                                """

                                if specialist_recommendation:
                                    html += f"<p><strong>Recomendación:</strong> {specialist_recommendation}</p>"

                                if specialist_analysis:
                                    html += f"<p>{specialist_analysis}</p>"

                                if (
                                    specialist_key_points
                                    and len(specialist_key_points) > 0
                                ):
                                    html += "<p><strong>Puntos clave:</strong></p><ul>"
                                    for point in specialist_key_points:
                                        html += f"<li>{point}</li>"
                                    html += "</ul>"

                                html += "</div>"

                        # 3. Añadir resumen técnico si está disponible
                        technical_summary = detailed_analysis.get(
                            "technical_summary", {}
                        )
                        if technical_summary:
                            # Extraer datos del resumen técnico
                            summary_text = technical_summary.get("summary", "")
                            indicators = technical_summary.get("indicators", {})
                            patterns = technical_summary.get("patterns", [])

                            if summary_text or indicators or patterns:
                                html += f"""
                                <div style="background-color: rgba(108, 117, 125, 0.1); padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 4px solid #6c757d;">
                                    <h4 style="color: #6c757d;">Resumen Técnico</h4>
                                """

                                if summary_text:
                                    html += f"<p>{summary_text}</p>"

                                if indicators and len(indicators) > 0:
                                    html += "<p><strong>Indicadores:</strong></p>"
                                    html += (
                                        "<div style='display: flex; flex-wrap: wrap;'>"
                                    )
                                    for name, value in indicators.items():
                                        html += f"<div style='flex: 1; min-width: 150px; margin: 5px;'><strong>{name}:</strong> {value}</div>"
                                    html += "</div>"

                                if patterns and len(patterns) > 0:
                                    html += (
                                        "<p><strong>Patrones detectados:</strong></p>"
                                    )
                                    for pattern in patterns:
                                        html += (
                                            f"<span class='pattern'>{pattern}</span> "
                                        )

                                html += "</div>"

                    html += "</div>"
        else:
            html += "<p>No hay señales de trading disponibles en este momento.</p>"

        # Sección de sentimiento de mercado
        sentiment_class = (
            "sentiment-bullish"
            if market_sentiment.get("overall") == "Alcista"
            else (
                "sentiment-bearish"
                if market_sentiment.get("overall") == "Bajista"
                else "sentiment-neutral"
            )
        )

        html += f"""
                <h2>Sentimiento de Mercado</h2>
                <div class="sentiment {sentiment_class}">
                    <h3>Sentimiento General: {market_sentiment.get('overall', 'Neutral')}</h3>
                    <p><strong>VIX:</strong> {market_sentiment.get('vix', 'N/A')}</p>
                    <p><strong>Tendencia S&P 500:</strong> {market_sentiment.get('sp500_trend', 'N/A')}</p>
                    <p><strong>Indicadores Técnicos:</strong> {market_sentiment.get('technical_indicators', 'N/A')}</p>
                    <p><strong>Volumen:</strong> {market_sentiment.get('volume', 'N/A')}</p>
                </div>
        """

        # Sección de noticias
        html += """
                <h2>Noticias Relevantes</h2>
                <div class="news">
        """

        if news_summary and len(news_summary) > 0:
            for news in news_summary:
                # Añadir indicador de impacto si está disponible
                impact = news.get("impact", "")
                impact_html = ""
                if impact:
                    impact_color = (
                        "#28a745"
                        if impact == "Alto"
                        else "#ffc107" if impact == "Medio" else "#6c757d"
                    )
                    impact_html = f'<span style="color: {impact_color}; font-weight: bold;">Impacto: {impact}</span> | '

                html += f"""
                    <h4>{news.get('title', '')}</h4>
                    <p>{news.get('summary', '')}</p>
                    <p><small>{impact_html}Fuente: {news.get('source', '')}</small></p>
                    <hr>
                """
        else:
            html += "<p>No hay noticias relevantes disponibles en este momento.</p>"

        html += """
                </div>
            </div>
            <div class="footer">
                <p>Este boletín es generado automáticamente por InversorIA Pro. La información proporcionada es solo para fines educativos y no constituye asesoramiento financiero.</p>
                <p>Los datos presentados son calculados en tiempo real utilizando análisis técnico avanzado y algoritmos de inteligencia artificial.</p>
                <p>&copy; 2025 InversorIA Pro. Todos los derechos reservados.</p>
            </div>
        </body>
        </html>
        """

        return html


# Clase para gestionar las señales de trading
class SignalManager:
    """Gestiona las señales de trading y su procesamiento"""

    def __init__(self):
        """Inicializa el gestor de señales"""
        self.db_manager = DatabaseManager()
        self.email_manager = EmailManager()
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

        # Determinar sector a escanear
        sector = "Todas" if not categories or "Todas" in categories else categories[0]

        # Determinar nivel de confianza
        confidence = (
            confidence_levels[0]
            if confidence_levels and len(confidence_levels) > 0
            else "Media"
        )

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
        """Obtiene noticias relevantes del mercado en tiempo real"""
        return self.real_time_analyzer.get_real_time_market_news()

    def get_detailed_analysis(self, symbol):
        """Obtiene análisis detallado para un símbolo específico"""
        return self.real_time_analyzer.get_detailed_analysis(symbol)

    def save_signal(self, signal_data):
        """Guarda una nueva señal en la base de datos"""
        return self.db_manager.save_signal(signal_data)

    def send_newsletter(self, recipients, signals, market_sentiment, news_summary):
        """Envía un boletín con las señales y análisis"""
        # Guardar las señales en la base de datos
        signal_ids = []
        if signals and len(signals) > 0:
            for signal in signals:
                # Preparar datos para guardar (siempre guardar todas las señales seleccionadas)
                signal_data = {
                    "symbol": signal.get("symbol"),
                    "price": signal.get("price"),
                    "direction": signal.get("direction"),
                    "confidence_level": signal.get("confidence_level"),
                    "timeframe": signal.get("timeframe"),
                    "strategy": signal.get("strategy"),
                    "category": signal.get("category"),
                    "analysis": signal.get("analysis"),
                }

                # Guardar la señal en la base de datos
                logger.info(
                    f"Guardando señal en la base de datos: {signal.get('symbol')}"
                )

                # Ejecutar la consulta directamente para asegurar que se guarde
                query = """INSERT INTO trading_signals
                          (symbol, price, direction, confidence_level, timeframe,
                           strategy, category, analysis, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())"""

                params = (
                    signal_data.get("symbol"),
                    signal_data.get("price"),
                    signal_data.get("direction"),
                    signal_data.get("confidence_level"),
                    signal_data.get("timeframe"),
                    signal_data.get("strategy"),
                    signal_data.get("category"),
                    signal_data.get("analysis"),
                )

                # Intentar guardar directamente
                try:
                    # Conectar a la base de datos
                    if self.db_manager.connect():
                        cursor = self.db_manager.connection.cursor(dictionary=True)
                        cursor.execute(query, params)
                        self.db_manager.connection.commit()
                        new_id = cursor.lastrowid
                        cursor.close()
                        self.db_manager.disconnect()

                        # Añadir ID a la lista de señales incluidas
                        if new_id:
                            signal_ids.append(str(new_id))
                            logger.info(f"Señal guardada con ID: {new_id}")
                        else:
                            # Si no se pudo obtener el ID, usar un ID temporal
                            signal_ids.append(str(len(signal_ids) + 1))
                            logger.warning(
                                f"No se pudo obtener el ID de la señal guardada, usando ID temporal"
                            )
                    else:
                        # Si no se pudo conectar, usar un ID temporal
                        signal_ids.append(str(len(signal_ids) + 1))
                        logger.warning(
                            f"No se pudo conectar a la base de datos, usando ID temporal"
                        )
                except Exception as e:
                    # En caso de error, usar un ID temporal
                    signal_ids.append(str(len(signal_ids) + 1))
                    logger.error(
                        f"Error al guardar la señal {signal.get('symbol')}: {str(e)}"
                    )

        # Guardar el sentimiento del mercado en la base de datos
        if market_sentiment:
            try:
                logger.info("Guardando sentimiento del mercado en la base de datos")

                # Extraer solo el valor numérico del VIX (por ejemplo, de "16.5 - Volatilidad Baja" a "16.5")
                vix_value = market_sentiment.get("vix", "0")
                if isinstance(vix_value, str) and "-" in vix_value:
                    vix_value = vix_value.split("-")[0].strip()

                # Crear una copia del sentimiento con el VIX corregido
                sentiment_data = market_sentiment.copy()
                sentiment_data["vix"] = vix_value

                self.db_manager.save_market_sentiment(sentiment_data)
            except Exception as e:
                logger.error(f"Error al guardar sentimiento del mercado: {str(e)}")

        # Guardar las noticias en la base de datos
        if news_summary and len(news_summary) > 0:
            try:
                logger.info(
                    f"Guardando {len(news_summary)} noticias en la base de datos"
                )
                for news in news_summary:
                    self.db_manager.save_market_news(news)
            except Exception as e:
                logger.error(f"Error al guardar noticias: {str(e)}")

        # Crear contenido HTML del boletín
        html_content = self.email_manager.create_newsletter_html(
            signals, market_sentiment, news_summary
        )

        # Enviar correo
        subject = (
            f"InversorIA Pro - Boletín de Trading {datetime.now().strftime('%d/%m/%Y')}"
        )
        success = self.email_manager.send_email(recipients, subject, html_content)

        # Registrar envío en la base de datos si fue exitoso
        if success:
            # Usar los IDs de las señales guardadas o existentes
            signal_ids_str = ", ".join(signal_ids) if signal_ids else "Ninguna"

            email_data = {
                "recipients": (
                    recipients if isinstance(recipients, str) else ", ".join(recipients)
                ),
                "subject": subject,
                "content_summary": f"Boletín con {len(signals) if signals else 0} señales",
                "signals_included": signal_ids_str,
            }
            self.db_manager.log_email_sent(email_data)

        return success


# Crear pestañas para organizar la interfaz
tab1, tab2, tab3 = st.tabs(
    ["📋 Señales Activas", "📬 Envío de Boletines", "📊 Historial de Señales"]
)

# Inicializar estado de sesión para señales
if "cached_signals" not in st.session_state:
    st.session_state.cached_signals = []

# Verificar si hay señales en otras páginas
if "market_signals" in st.session_state and st.session_state.market_signals:
    # Combinar señales sin duplicados
    existing_symbols = {
        signal.get("symbol") for signal in st.session_state.cached_signals
    }
    for signal in st.session_state.market_signals:
        if signal.get("symbol") not in existing_symbols:
            st.session_state.cached_signals.append(signal)
            existing_symbols.add(signal.get("symbol"))

    logger.info(
        f"Se importaron {len(st.session_state.market_signals)} señales desde otras páginas"
    )

# Inicializar el gestor de señales
signal_manager = SignalManager()

# Contenido de la pestaña "Señales Activas"
with tab1:
    st.header("📋 Señales de Trading Activas")

    # Añadir botón de actualización
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(
            "Utilice los filtros de la barra lateral para personalizar los resultados."
        )
    with col2:
        refresh = st.button(
            "🔄 Actualizar Datos",
            help="Fuerza un nuevo escaneo del mercado en tiempo real",
        )

    # Obtener señales filtradas (forzar tiempo real si se presiona el botón de actualización)
    categoria_filtro = "Todas" if categoria == "Todas" else [categoria]
    signals = signal_manager.get_active_signals(
        days_back=dias_atras,
        categories=categoria_filtro,
        confidence_levels=confianza,
        force_realtime=refresh,  # Forzar escaneo en tiempo real si se presiona el botón
    )

    # Mostrar mensaje de actualización si se presionó el botón
    if refresh:
        st.success("Datos actualizados con éxito mediante escaneo en tiempo real.")

    # Mostrar señales en tarjetas
    if signals and len(signals) > 0:
        # Dividir en columnas para mostrar las tarjetas
        cols = st.columns(2)

        for i, signal in enumerate(signals):
            # Alternar entre columnas
            with cols[i % 2]:
                # Determinar color de fondo según dirección (compatible con modo oscuro)
                if signal.get("direction") == "CALL":
                    card_bg = "rgba(40, 167, 69, 0.2)"  # Verde semi-transparente
                    text_color = "#28a745"  # Verde
                    direction_text = "📈 COMPRA"
                elif signal.get("direction") == "PUT":
                    card_bg = "rgba(220, 53, 69, 0.2)"  # Rojo semi-transparente
                    text_color = "#dc3545"  # Rojo
                    direction_text = "📉 VENTA"
                else:
                    card_bg = "rgba(108, 117, 125, 0.2)"  # Gris semi-transparente
                    text_color = "#6c757d"  # Gris
                    direction_text = "↔️ NEUTRAL"

                # Formatear fecha (asegurarse de que no sea futura)
                created_at = signal.get("created_at")
                if isinstance(created_at, datetime):
                    # Corregir fechas futuras
                    if created_at > datetime.now():
                        created_at = datetime.now()
                        signal["created_at"] = (
                            created_at  # Actualizar la fecha en el objeto original
                        )
                    fecha = created_at.strftime("%d/%m/%Y %H:%M")
                else:
                    # Si no es un objeto datetime, usar la fecha actual
                    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                    signal["created_at"] = (
                        datetime.now()
                    )  # Actualizar la fecha en el objeto original

                # Crear tarjeta con CSS personalizado (compatible con modo oscuro)
                st.markdown(
                    f"""
                <div style="background-color: {card_bg}; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; color: {text_color};">{signal.get('symbol', '')} - {direction_text}</h3>
                    <p><strong>Precio:</strong> ${signal.get('price', '0.00')}</p>
                    <p><strong>Confianza:</strong> {signal.get('confidence_level', 'Baja')}</p>
                    <p><strong>Estrategia:</strong> {signal.get('strategy', 'N/A')}</p>
                    <p><strong>Timeframe:</strong> {signal.get('timeframe', 'Corto')}</p>
                    <p><strong>Categoría:</strong> {signal.get('category', 'N/A')}</p>
                    <p><strong>Fecha:</strong> {fecha}</p>
                    <details>
                        <summary style="color: {text_color};">Ver análisis detallado</summary>
                        <p>{signal.get('analysis', 'No hay análisis disponible.')}</p>
                    </details>
                </div>
                """,
                    unsafe_allow_html=True,
                )
    else:
        # Mostrar mensaje más detallado cuando no hay señales
        st.warning("No se encontraron señales activas con los filtros seleccionados.")

        # Sugerir acciones al usuario
        st.markdown(
            """
        ### Sugerencias:
        1. **Prueba a cambiar los filtros** - Selecciona "Todas" en la categoría o "Baja" en el nivel de confianza para ver más resultados.
        2. **Actualiza los datos** - Usa el botón "Actualizar Datos" para forzar un nuevo escaneo del mercado.
        3. **Verifica la conexión** - Asegúrate de tener una conexión a Internet estable para obtener datos en tiempo real.
        4. **Horario de mercado** - Recuerda que algunas señales solo están disponibles durante el horario de mercado.
        """
        )

    # Mostrar sentimiento de mercado
    st.subheader("📈 Sentimiento de Mercado")

    # Crear un contenedor para mostrar un mensaje de carga
    sentiment_container = st.container()
    with sentiment_container:
        with st.spinner("Analizando sentimiento de mercado..."):
            sentiment = signal_manager.get_market_sentiment()

    # Verificar si hay datos de sentimiento válidos
    has_valid_sentiment = (
        sentiment
        and sentiment.get("overall", "Neutral") != "Neutral"
        or sentiment.get("vix", "N/A") != "N/A"
        or sentiment.get("sp500_trend", "N/A") != "No disponible"
        or sentiment.get("volume", "N/A") != "No disponible"
    )

    if has_valid_sentiment:
        # Determinar color según sentimiento
        if sentiment.get("overall") == "Alcista":
            sentiment_color = "#28a745"  # Verde
        elif sentiment.get("overall") == "Bajista":
            sentiment_color = "#dc3545"  # Rojo
        else:
            sentiment_color = "#6c757d"  # Gris

        # Mostrar indicadores de sentimiento
        cols = st.columns(4)
        with cols[0]:
            st.metric("Sentimiento", sentiment.get("overall", "Neutral"))
        with cols[1]:
            st.metric("VIX", sentiment.get("vix", "N/A"))
        with cols[2]:
            st.metric("S&P 500", sentiment.get("sp500_trend", "N/A"))
        with cols[3]:
            st.metric("Volumen", sentiment.get("volume", "N/A"))

        # Mostrar notas adicionales si están disponibles
        if sentiment.get("notes"):
            st.caption(sentiment.get("notes"))
    else:
        # Mostrar mensaje cuando no hay datos válidos
        st.warning(
            "No se pudieron obtener datos de sentimiento de mercado en tiempo real."
        )

        # Sugerir acciones al usuario
        st.markdown(
            """
        **Sugerencias:**
        - Verifica tu conexión a Internet
        - Intenta actualizar la página
        - Los datos de sentimiento pueden no estar disponibles fuera del horario de mercado
        """
        )

    # Mostrar noticias relevantes
    st.subheader("📰 Noticias Relevantes")

    # Crear un contenedor para mostrar un mensaje de carga
    news_container = st.container()
    with news_container:
        with st.spinner("Buscando noticias relevantes..."):
            news = signal_manager.get_market_news()

    if news and len(news) > 0:
        # Mostrar contador de noticias
        st.write(f"Se encontraron {len(news)} noticias relevantes.")

        for item in news:
            # Formatear fecha (asegurarse de que no sea futura)
            news_date = item.get("date")
            if isinstance(news_date, datetime):
                # Corregir fechas futuras
                if news_date > datetime.now():
                    news_date = datetime.now()
                    item["date"] = (
                        news_date  # Actualizar la fecha en el objeto original
                    )
                fecha = news_date.strftime("%d/%m/%Y")
            else:
                # Si no es un objeto datetime, usar la fecha actual
                fecha = datetime.now().strftime("%d/%m/%Y")
                item["date"] = (
                    datetime.now()
                )  # Actualizar la fecha en el objeto original

            # Mostrar noticia (compatible con modo oscuro)
            st.markdown(
                f"""
            <div style="background-color: rgba(108, 117, 125, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid rgba(0,0,0,0.1);">
                <h4 style="margin-top: 0; color: #0275d8;">{item.get('title', '')}</h4>
                <p>{item.get('summary', '')}</p>
                <p><small>Fuente: <span style="color: #6c757d;">{item.get('source', '')}</span> - {fecha}</small></p>
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        # Mostrar mensaje cuando no hay noticias disponibles
        st.warning("No se pudieron obtener noticias relevantes en tiempo real.")

        # Sugerir acciones al usuario
        st.markdown(
            """
        **Sugerencias:**
        - Verifica tu conexión a Internet
        - Intenta actualizar la página
        - Las noticias pueden no estar disponibles temporalmente
        - Prueba a cambiar los filtros o actualizar los datos
        """
        )

# Contenido de la pestaña "Envío de Boletines"
with tab2:
    st.header("📬 Envío de Boletines de Trading")

    # Selección de señales para incluir en el boletín
    st.subheader("Paso 1: Seleccionar Señales para el Boletín")

    # Añadir botón de actualización
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write("Seleccione las señales que desea incluir en el boletín.")
    with col2:
        refresh_bulletin = st.button(
            "🔄 Actualizar Señales",
            help="Fuerza un nuevo escaneo del mercado en tiempo real",
            key="refresh_bulletin",
        )

    # Obtener todas las señales disponibles (forzar tiempo real si se presiona el botón)
    # Primero verificar si hay señales en caché
    if (
        "cached_signals" in st.session_state
        and st.session_state.cached_signals
        and not refresh_bulletin
    ):
        all_signals = st.session_state.cached_signals
        logger.info(f"Usando {len(all_signals)} señales desde la caché para el boletín")
    else:
        all_signals = signal_manager.get_active_signals(
            days_back=dias_atras,
            force_realtime=refresh_bulletin,  # Forzar escaneo en tiempo real si se presiona el botón
        )

    # Mostrar mensaje de actualización si se presionó el botón
    if refresh_bulletin:
        st.success("Señales actualizadas con éxito mediante escaneo en tiempo real.")

    if all_signals and len(all_signals) > 0:
        # Crear opciones para multiselect
        signal_options = {}
        for signal in all_signals:
            # Crear texto descriptivo para cada señal
            direction = (
                "COMPRA"
                if signal.get("direction") == "CALL"
                else "VENTA" if signal.get("direction") == "PUT" else "NEUTRAL"
            )
            key = f"{signal.get('symbol')} - {direction} - {signal.get('confidence_level')}"
            signal_options[key] = signal

        # Permitir al usuario seleccionar señales
        selected_signals = st.multiselect(
            "Seleccionar señales para incluir:",
            options=list(signal_options.keys()),
            default=list(signal_options.keys())[: min(3, len(signal_options))],
        )

        # Obtener las señales seleccionadas
        signals_to_include = [signal_options[key] for key in selected_signals]
    else:
        st.warning("No hay señales disponibles para incluir en el boletín.")
        signals_to_include = []

    # Configuración del boletín
    st.subheader("Paso 2: Configurar Boletín")

    # Obtener sentimiento de mercado y noticias
    market_sentiment = signal_manager.get_market_sentiment()
    market_news = signal_manager.get_market_news()

    # Permitir personalizar el boletín
    include_sentiment = st.checkbox("Incluir Sentimiento de Mercado", value=True)
    include_news = st.checkbox("Incluir Noticias Relevantes", value=True)

    # Validar destinatarios
    if not destinatarios:
        st.warning("Por favor, ingrese al menos un destinatario en la barra lateral.")

    # Vista previa del boletín
    st.subheader("Paso 3: Vista Previa del Boletín")

    # Crear contenido HTML del boletín
    preview_sentiment = market_sentiment if include_sentiment else {}
    preview_news = market_news if include_news else []

    html_content = signal_manager.email_manager.create_newsletter_html(
        signals_to_include, preview_sentiment, preview_news
    )

    # Mostrar vista previa
    with st.expander("Ver Vista Previa del Boletín", expanded=True):
        st.components.v1.html(html_content, height=500, scrolling=True)

    # Botón para enviar boletín
    st.subheader("Paso 4: Enviar Boletín")

    col1, col2 = st.columns([3, 1])
    with col1:
        if destinatarios:
            recipient_list = [
                email.strip() for email in destinatarios.split(",") if email.strip()
            ]
            st.write(f"Se enviará a: {', '.join(recipient_list)}")
        else:
            st.write("No hay destinatarios configurados.")

    with col2:
        send_button = st.button(
            "📩 Enviar Boletín",
            disabled=not destinatarios or len(signals_to_include) == 0,
        )

    # Opción para modo simulación (solo para desarrollo)
    simulation_mode = st.checkbox(
        "Modo simulación (sin enviar correo real)", value=False
    )

    if send_button:
        with st.spinner("Enviando boletín..."):
            if simulation_mode:
                # Simular envío exitoso
                logger.info(
                    f"[SIMULACIÓN] Simulando envío de boletín a: {', '.join(recipient_list)}"
                )
                time.sleep(2)  # Simular tiempo de envío
                success = True

                # Mostrar el contenido del correo en la consola para depuración
                logger.info(
                    "[SIMULACIÓN] Contenido del boletín (primeros 500 caracteres):"
                )
                logger.info(html_content[:500] + "...")
            else:
                # Usar la función real de envío de correos
                success = signal_manager.send_newsletter(
                    recipient_list, signals_to_include, preview_sentiment, preview_news
                )

            # Registrar el resultado en el log
            if success:
                msg = "Boletín enviado correctamente" + (
                    " (SIMULACIÓN)" if simulation_mode else ""
                )
                logger.info(f"{msg} a: {', '.join(recipient_list)}")
                st.success(f"{msg} a los destinatarios.")
            else:
                logger.error(f"Error al enviar boletín a: {', '.join(recipient_list)}")
                st.error(
                    "Error al enviar el boletín. Por favor, verifica la configuración de correo."
                )

# Contenido de la pestaña "Historial de Señales"
with tab3:
    st.header("📊 Historial de Señales y Envíos")

    # Crear pestañas para separar historial de señales y envíos
    hist_tab1, hist_tab2 = st.tabs(["Historial de Señales", "Registro de Envíos"])

    # Historial de señales
    with hist_tab1:
        st.subheader("Señales Registradas")

        # Filtros adicionales para el historial
        col1, col2, col3 = st.columns(3)
        with col1:
            hist_days = st.slider("Período (días)", 1, 90, 30)
        with col2:
            hist_direction = st.selectbox(
                "Dirección", ["Todas", "CALL (Compra)", "PUT (Venta)", "NEUTRAL"]
            )
        with col3:
            hist_confidence = st.selectbox(
                "Confianza", ["Todas", "Alta", "Media", "Baja"]
            )

        # Obtener señales históricas de la base de datos
        try:
            # Construir la consulta base
            query = """SELECT * FROM trading_signals
                      WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"""
            params = [hist_days]

            # Añadir filtros adicionales si es necesario
            if hist_direction != "Todas":
                direction_filter = hist_direction.split(" ")[
                    0
                ]  # Extraer CALL, PUT o NEUTRAL
                query += " AND direction = %s"
                params.append(direction_filter)

            if hist_confidence != "Todas":
                query += " AND confidence_level = %s"
                params.append(hist_confidence)

            query += " ORDER BY created_at DESC"

            # Conectar a la base de datos y ejecutar la consulta
            if signal_manager.db_manager.connect():
                cursor = signal_manager.db_manager.connection.cursor(dictionary=True)
                cursor.execute(query, params)
                historic_signals = cursor.fetchall()
                cursor.close()
                signal_manager.db_manager.disconnect()

                logger.info(
                    f"Se obtuvieron {len(historic_signals)} señales históricas de la base de datos"
                )

                # Si no hay resultados, simplemente mostrar un mensaje
                if not historic_signals:
                    logger.info(
                        "No se encontraron señales en la base de datos con los filtros seleccionados"
                    )
                    # No usar datos de ejemplo para evitar confusiones con los filtros
                    # historic_signals = []  # Lista vacía
            else:
                # Si no se puede conectar, mostrar un mensaje de error
                logger.warning("No se pudo conectar a la base de datos")
                st.error(
                    "No se pudo conectar a la base de datos. Por favor, verifica la configuración."
                )
                historic_signals = []  # Lista vacía
        except Exception as e:
            logger.error(f"Error al obtener señales históricas: {str(e)}")
            # En caso de error, mostrar mensaje y no usar datos de ejemplo
            st.error(f"Error al obtener datos de la base de datos: {str(e)}")
            historic_signals = []  # Lista vacía

        # Los filtros ya se aplicaron en la consulta SQL
        # No es necesario filtrar de nuevo los resultados

        # Mostrar tabla de señales
        if historic_signals and len(historic_signals) > 0:
            # Convertir a DataFrame para mejor visualización
            df_signals = pd.DataFrame(historic_signals)

            # Formatear columnas para visualización
            if "created_at" in df_signals.columns:
                df_signals["Fecha"] = df_signals["created_at"].apply(
                    lambda x: (
                        x.strftime("%d/%m/%Y %H:%M")
                        if isinstance(x, datetime)
                        else str(x)
                    )
                )

            # Seleccionar y renombrar columnas para la tabla
            display_cols = {
                "symbol": "Símbolo",
                "direction": "Dirección",
                "price": "Precio",
                "confidence_level": "Confianza",
                "strategy": "Estrategia",
                "category": "Categoría",
                "Fecha": "Fecha",
            }

            # Crear DataFrame para mostrar
            df_display = df_signals[
                [c for c in display_cols.keys() if c in df_signals.columns]
            ].copy()
            df_display.columns = [display_cols[c] for c in df_display.columns]

            # Mostrar tabla con estilo
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Opción para exportar datos
            if st.button("📥 Exportar a CSV"):
                # Generar CSV para descarga
                csv = df_display.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"senales_trading_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
        else:
            st.info("No se encontraron señales con los filtros seleccionados.")

    # Registro de envíos
    with hist_tab2:
        st.subheader("Registro de Boletines Enviados")

        # Obtener datos de envíos de la base de datos
        try:
            # Consultar los últimos 30 días de envíos
            query = """SELECT id, recipients, subject, content_summary, signals_included, sent_at, status, error_message
                      FROM email_logs
                      WHERE sent_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                      ORDER BY sent_at DESC"""

            # Conectar a la base de datos y ejecutar la consulta
            if signal_manager.db_manager.connect():
                cursor = signal_manager.db_manager.connection.cursor(dictionary=True)
                cursor.execute(query)
                email_logs = cursor.fetchall()
                cursor.close()
                signal_manager.db_manager.disconnect()

                logger.info(
                    f"Se obtuvieron {len(email_logs)} registros de envíos de la base de datos"
                )
            else:
                # Si no se puede conectar, usar datos de ejemplo
                logger.warning(
                    "No se pudo conectar a la base de datos, usando datos de ejemplo"
                )
                email_logs = [
                    {
                        "id": 1,
                        "recipients": "usuario1@example.com, usuario2@example.com",
                        "subject": "InversorIA Pro - Boletín de Trading 20/05/2025",
                        "content_summary": "Boletín con 3 señales",
                        "signals_included": "1, 2, 4",
                        "sent_at": datetime.now() - timedelta(days=1),
                        "status": "success",
                        "error_message": None,
                    },
                    {
                        "id": 2,
                        "recipients": "usuario1@example.com",
                        "subject": "InversorIA Pro - Boletín de Trading 18/05/2025",
                        "content_summary": "Boletín con 2 señales",
                        "signals_included": "3, 5",
                        "sent_at": datetime.now() - timedelta(days=3),
                        "status": "success",
                        "error_message": None,
                    },
                ]
        except Exception as e:
            logger.error(f"Error al obtener registros de envíos: {str(e)}")
            # En caso de error, usar datos de ejemplo
            email_logs = [
                {
                    "id": 1,
                    "recipients": "usuario1@example.com, usuario2@example.com",
                    "subject": "InversorIA Pro - Boletín de Trading 20/05/2025",
                    "content_summary": "Boletín con 3 señales",
                    "signals_included": "1, 2, 4",
                    "sent_at": datetime.now() - timedelta(days=1),
                    "status": "success",
                    "error_message": None,
                }
            ]
            st.warning(
                "Error al obtener datos de la base de datos. Mostrando datos de ejemplo."
            )

        # Mostrar tabla de envíos
        if email_logs and len(email_logs) > 0:
            # Convertir a DataFrame
            df_emails = pd.DataFrame(email_logs)

            # Formatear fecha
            if "sent_at" in df_emails.columns:
                df_emails["Fecha de Envío"] = df_emails["sent_at"].apply(
                    lambda x: (
                        x.strftime("%d/%m/%Y %H:%M")
                        if isinstance(x, datetime)
                        else str(x)
                    )
                )

            # Seleccionar columnas para mostrar
            display_cols = {
                "subject": "Asunto",
                "recipients": "Destinatarios",
                "content_summary": "Contenido",
                "signals_included": "Señales Incluidas",
                "Fecha de Envío": "Fecha de Envío",
            }

            # Crear DataFrame para mostrar
            df_display = df_emails[
                [c for c in display_cols.keys() if c in df_emails.columns]
            ].copy()
            df_display.columns = [display_cols[c] for c in df_display.columns]

            # Mostrar tabla
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Añadir explicación detallada del significado de "Señales Incluidas"
            st.info(
                """
            **Nota sobre "Señales Incluidas"**:
            Los números que aparecen en esta columna son los IDs de las señales de trading que fueron incluidas en el boletín.
            Estos IDs corresponden a los registros en la base de datos de señales de trading (tabla `trading_signals`).

            **Proceso completo cuando se envía un boletín:**
            1. **Guardado de señales:** Cada señal seleccionada se guarda en la base de datos, generando un ID único.
            2. **Guardado de sentimiento:** El sentimiento de mercado incluido en el boletín se guarda en la tabla `market_sentiment`.
            3. **Guardado de noticias:** Las noticias relevantes incluidas se guardan en la tabla `market_news`.
            4. **Registro del envío:** Se crea un registro en la tabla `email_logs` que incluye los IDs de las señales enviadas.

            **Beneficios de este sistema:**
            - **Trazabilidad completa:** Permite rastrear qué señales específicas se enviaron en cada boletín.
            - **Análisis de rendimiento:** Facilita el análisis posterior del rendimiento de las señales enviadas.
            - **Histórico de datos:** Mantiene un registro histórico completo del sentimiento de mercado y noticias relevantes.

            Los datos se calculan en tiempo real al momento de generar el boletín, utilizando las mismas funciones de análisis que se usan en la aplicación principal.
            """
            )
        else:
            st.info("No hay registros de envíos de boletines.")
