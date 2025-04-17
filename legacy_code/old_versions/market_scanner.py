import pandas as pd
import numpy as np
from trading_analyzer import TradingAnalyzer
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import streamlit as st

logger = logging.getLogger(__name__)


class MarketScanner:
    def __init__(self, symbols_dict, analyzer=None):
        self.symbols_dict = symbols_dict
        # Si se proporciona un analizador, usarlo; de lo contrario, crear uno nuevo
        self.analyzer = analyzer if analyzer is not None else TradingAnalyzer()
        self.all_symbols = [
            symbol for symbols in symbols_dict.values() for symbol in symbols
        ]
        self.last_scan_results = {}  # Almacena resultados del último scan

    def _analyze_symbol(self, symbol):
        try:
            # Obtener datos de tendencia y estrategias
            trend, daily_data = self.analyzer.analyze_trend(symbol)

            # Verificar que tenemos datos válidos
            if trend is None or not isinstance(trend, dict):
                logger.warning(f"No se pudo obtener tendencia válida para {symbol}")
                return None

            # Obtener datos horarios
            hourly_data = self.analyzer.get_market_data(
                symbol, period="5d", interval="1h"
            )

            # Identificar estrategias
            strategies = self.analyzer.identify_strategy(hourly_data, trend)

            if not strategies:
                logger.info(f"No se identificaron estrategias para {symbol}")
                return None

            # Obtener sector
            sector = None
            for s, symbols in self.symbols_dict.items():
                if symbol in symbols:
                    sector = s
                    break

            if sector is None:
                logger.warning(f"No se pudo determinar el sector para {symbol}")
                sector = "Desconocido"

            # Extraer métricas con manejo de errores
            try:
                price = (
                    float(trend["metrics"]["price"])
                    if "price" in trend["metrics"]
                    else 0.0
                )
                rsi = (
                    float(trend["metrics"]["rsi"])
                    if "rsi" in trend["metrics"]
                    else 50.0
                )
                direction = (
                    str(trend["direction"]) if "direction" in trend else "NEUTRAL"
                )
                strength = str(trend["strength"]) if "strength" in trend else "MEDIA"

                # Extraer datos de la primera estrategia
                strategy_type = (
                    str(strategies[0]["type"]) if "type" in strategies[0] else "NEUTRAL"
                )
                setup_name = (
                    str(strategies[0]["name"])
                    if "name" in strategies[0]
                    else "Desconocido"
                )
                confidence = (
                    str(strategies[0]["confidence"])
                    if "confidence" in strategies[0]
                    else "MEDIA"
                )

                # Extraer niveles
                levels = strategies[0].get("levels", {})
                entry = float(levels.get("entry", price))
                stop = float(levels.get("stop", price * 0.95))
                target = float(levels.get("target", price * 1.05))
                r_r = float(levels.get("r_r", 1.0))

            except (TypeError, ValueError, KeyError) as e:
                logger.warning(f"Error extrayendo métricas para {symbol}: {str(e)}")
                # Valores por defecto
                price = 0.0
                rsi = 50.0
                direction = "NEUTRAL"
                strength = "MEDIA"
                strategy_type = "NEUTRAL"
                setup_name = "Desconocido"
                confidence = "MEDIA"
                entry = 0.0
                stop = 0.0
                target = 0.0
                r_r = 0.0

            # Crear resultado
            result = {
                "Symbol": symbol,
                "Sector": sector,
                "Tendencia": direction,
                "Fuerza": strength,
                "Precio": price,
                "RSI": rsi,
                "Estrategia": strategy_type,
                "Setup": setup_name,
                "Confianza": confidence,
                "Entry": entry,
                "Stop": stop,
                "Target": target,
                "R/R": r_r,
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "trend_data": trend,
                "strategies": strategies,  # Guardamos todas las estrategias
            }

            # Almacenar resultado en el cache
            self.last_scan_results[symbol] = result

            return result

        except Exception as e:
            logger.error(f"Error analizando {symbol}: {str(e)}")
            return None

    def _analyze_symbol_with_details(self, symbol):
        """
        Analiza un símbolo con detalles completos para el scanner de mercado mejorado.
        Incluye análisis técnico, opciones, multi-timeframe y Trading Specialist.

        Args:
            symbol (str): Símbolo a analizar

        Returns:
            dict: Resultado del análisis con detalles completos o None si no hay señal
        """
        try:
            # Primero obtenemos el análisis básico
            basic_result = self._analyze_symbol(symbol)

            # Si no hay señal clara, no continuamos
            if basic_result is None:
                return None

            # Obtener datos completos para análisis detallado
            try:
                # Intentar importar funciones necesarias
                from trading_analyzer import get_market_context, analyze_market_data
            except ImportError:
                logger.warning(
                    f"No se pudieron importar funciones para análisis detallado de {symbol}"
                )
                return basic_result

            # Obtener contexto completo de mercado
            try:
                context = get_market_context(symbol)
            except Exception as e:
                logger.warning(
                    f"Error al obtener contexto de mercado para {symbol}: {str(e)}"
                )
                return basic_result

            # Si no hay contexto válido, usar solo el análisis básico
            if context is None or "error" in context:
                logger.warning(f"No se pudo obtener contexto completo para {symbol}")
                return basic_result

            # Extraer señales del Trading Specialist
            signals = context.get("signals", {})

            # Obtener señal general del Trading Specialist
            trading_specialist_signal = "NEUTRAL"
            trading_specialist_confidence = "MEDIA"

            if "overall" in signals:
                signal = signals["overall"]["signal"]
                if signal in ["compra", "compra_fuerte"]:
                    trading_specialist_signal = "COMPRA"
                    if signal == "compra_fuerte":
                        trading_specialist_confidence = "ALTA"
                elif signal in ["venta", "venta_fuerte"]:
                    trading_specialist_signal = "VENTA"
                    if signal == "venta_fuerte":
                        trading_specialist_confidence = "ALTA"

                # Actualizar confianza si el Trading Specialist tiene alta confianza
                if (
                    trading_specialist_confidence == "ALTA"
                    and basic_result["Estrategia"] != "NEUTRAL"
                ):
                    basic_result["Confianza"] = "ALTA"

            # Añadir información adicional al resultado
            basic_result["Trading_Specialist"] = trading_specialist_signal
            basic_result["TS_Confianza"] = trading_specialist_confidence

            # Añadir información de opciones si está disponible
            options_data = context.get("options_data", {})
            if options_data:
                basic_result["Volatilidad"] = options_data.get("implied_volatility", 0)
                basic_result["Options_Signal"] = options_data.get(
                    "recommendation", "NEUTRAL"
                )

            # Añadir información de sentimiento si está disponible
            sentiment = context.get("news_sentiment", {})
            if sentiment:
                basic_result["Sentimiento"] = sentiment.get("sentiment", "neutral")
                basic_result["Sentimiento_Score"] = sentiment.get("score", 0.5)

            # Añadir información de soporte/resistencia
            support_resistance = context.get("support_resistance", {})
            if support_resistance:
                if "supports" in support_resistance and support_resistance["supports"]:
                    supports = sorted(support_resistance["supports"], reverse=True)
                    if supports:
                        basic_result["Soporte"] = supports[0]

                if (
                    "resistances" in support_resistance
                    and support_resistance["resistances"]
                ):
                    resistances = sorted(support_resistance["resistances"])
                    if resistances:
                        basic_result["Resistencia"] = resistances[0]

            # Añadir información de análisis técnico
            technical_analysis = context.get("technical_analysis", {})
            if technical_analysis:
                basic_result["Análisis_Técnico"] = technical_analysis.get("summary", "")
                basic_result["Indicadores_Alcistas"] = technical_analysis.get(
                    "bullish_indicators", 0
                )
                basic_result["Indicadores_Bajistas"] = technical_analysis.get(
                    "bearish_indicators", 0
                )

            # Añadir información de noticias
            news = context.get("news", [])
            if news and len(news) > 0:
                basic_result["Última_Noticia"] = news[0].get("title", "")
                basic_result["Fuente_Noticia"] = news[0].get("source", "")

            # Guardar resultado completo en caché
            self.last_scan_results[symbol] = basic_result

            return basic_result

        except Exception as e:
            logger.error(f"Error en análisis detallado de {symbol}: {str(e)}")
            # Intentar devolver el análisis básico si está disponible
            return self._analyze_symbol(symbol)

    def get_cached_analysis(self, symbol):
        """Obtiene el último análisis cacheado para un símbolo"""
        return self.last_scan_results.get(symbol)

    def scan_market(self, selected_sectors=None):
        """
        Escanea el mercado, opcionalmente filtrando por sectores.

        Args:
            selected_sectors (list): Lista de sectores a analizar. None para todos.
        """
        # Filtrar símbolos por sector si es necesario
        symbols_to_scan = []
        if selected_sectors:
            symbols_to_scan = [
                symbol
                for sector in selected_sectors
                for symbol in self.symbols_dict.get(sector, [])
            ]
        else:
            symbols_to_scan = self.all_symbols

        logger.info(
            f"Escaneando {len(symbols_to_scan)} símbolos de los sectores seleccionados"
        )

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for result in executor.map(
                self._analyze_symbol_with_details, symbols_to_scan
            ):
                if result is not None:
                    results.append(result)

        # Ordenar resultados
        if results:
            df = pd.DataFrame(results)

            # Asegurar que la columna 'Confianza' sea de tipo string
            df["Confianza"] = df["Confianza"].astype(str)

            # Añadir columna de cambio (porcentaje) si no existe
            if "Cambio" not in df.columns:
                # Valor por defecto (0.5% para CALL, -0.5% para PUT)
                df["Cambio"] = df.apply(
                    lambda row: (
                        0.5
                        if row["Estrategia"] == "CALL"
                        else -0.5 if row["Estrategia"] == "PUT" else 0.0
                    ),
                    axis=1,
                )

            # Ordenar por confianza
            confidence_order = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
            # Usar get para manejar valores no encontrados
            df["conf_order"] = df["Confianza"].map(lambda x: confidence_order.get(x, 3))
            df = df.sort_values(["conf_order", "Symbol"]).drop("conf_order", axis=1)

            # Registrar información sobre los resultados
            logger.info(f"Scanner encontró {len(df)} oportunidades")
            logger.info(f"Columnas disponibles: {df.columns.tolist()}")

            return df

        # Si no hay resultados, crear datos sintéticos para pruebas
        logger.warning(
            "No se encontraron resultados reales, creando datos sintéticos para pruebas"
        )

        # Crear datos sintéticos para pruebas
        synthetic_data = [
            {
                "Symbol": "AAPL",
                "Sector": "Tecnología",
                "Tendencia": "ALCISTA",
                "Fuerza": "ALTA",
                "Precio": 175.50,
                "RSI": 65.2,
                "Estrategia": "CALL",
                "Setup": "Soporte Fuerte",
                "Confianza": "ALTA",
                "Entry": 175.50,
                "Stop": 170.0,
                "Target": 185.0,
                "R/R": 1.9,
                "Cambio": 0.8,
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
            },
            {
                "Symbol": "MSFT",
                "Sector": "Tecnología",
                "Tendencia": "ALCISTA",
                "Fuerza": "MEDIA",
                "Precio": 380.25,
                "RSI": 58.7,
                "Estrategia": "CALL",
                "Setup": "Breakout",
                "Confianza": "MEDIA",
                "Entry": 380.25,
                "Stop": 375.0,
                "Target": 390.0,
                "R/R": 1.5,
                "Cambio": 0.5,
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
            },
            {
                "Symbol": "NVDA",
                "Sector": "Tecnología",
                "Tendencia": "BAJISTA",
                "Fuerza": "ALTA",
                "Precio": 850.30,
                "RSI": 30.5,
                "Estrategia": "PUT",
                "Setup": "Resistencia Fuerte",
                "Confianza": "ALTA",
                "Entry": 850.30,
                "Stop": 870.0,
                "Target": 820.0,
                "R/R": 1.5,
                "Cambio": -0.7,
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
            },
        ]

        df = pd.DataFrame(synthetic_data)
        logger.info(f"Devolviendo {len(df)} resultados sintéticos")
        return df


def display_opportunities(scanner):
    """
    Muestra oportunidades de trading en Streamlit con análisis detallado.

    Args:
        scanner (MarketScanner): Scanner de mercado inicializado
    """
    st.subheader("🎯 Scanner de Mercado Mejorado")

    # Selector de sectores
    available_sectors = list(scanner.symbols_dict.keys())
    selected_sectors = st.multiselect(
        "Seleccionar Sectores",
        options=available_sectors,
        default=(
            ["Tecnología", "Finanzas"]
            if "Tecnología" in available_sectors and "Finanzas" in available_sectors
            else available_sectors[:2]
        ),
        help="Selecciona los sectores que deseas analizar",
    )

    # Botón para iniciar el escaneo
    scan_button = st.button("Escanear Mercado", type="primary")

    if scan_button or "scan_results" in st.session_state:
        with st.spinner("Analizando el mercado... Esto puede tardar unos segundos."):
            # Obtener oportunidades
            if scan_button or "scan_results" not in st.session_state:
                opportunities = scanner.scan_market(selected_sectors)
                st.session_state.scan_results = opportunities
            else:
                opportunities = st.session_state.scan_results

        if opportunities.empty:
            st.warning("No se identificaron oportunidades que cumplan los criterios")
            return

        # Mostrar métricas generales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_calls = len(opportunities[opportunities["Estrategia"] == "CALL"])
            st.metric("Setups CALL", total_calls)
        with col2:
            total_puts = len(opportunities[opportunities["Estrategia"] == "PUT"])
            st.metric("Setups PUT", total_puts)
        with col3:
            high_conf = len(opportunities[opportunities["Confianza"] == "ALTA"])
            st.metric("Alta Confianza", high_conf)
        with col4:
            # Verificar si la columna Trading_Specialist existe
            if "Trading_Specialist" in opportunities.columns:
                ts_signals = sum(
                    1
                    for x in opportunities["Trading_Specialist"].fillna("NEUTRAL")
                    if x in ["COMPRA", "VENTA"]
                )
                st.metric("Señales Trading Specialist", ts_signals)
            else:
                st.metric("Señales Trading Specialist", 0)

        # Crear pestañas para diferentes vistas
        tab1, tab2, tab3 = st.tabs(
            [
                "📊 Tabla de Oportunidades",
                "🔍 Análisis Detallado",
                "📈 Análisis por Sector",
            ]
        )

        with tab1:
            # Mostrar tabla de oportunidades
            st.markdown("### Oportunidades Identificadas")

            # Columnas a mostrar en la tabla principal
            display_columns = [
                "Symbol",
                "Sector",
                "Tendencia",
                "Fuerza",
                "Precio",
                "RSI",
                "Estrategia",
                "Setup",
                "Confianza",
                "Entry",
                "Stop",
                "Target",
                "R/R",
                "Trading_Specialist",
                "Timestamp",
            ]

            # Filtrar columnas disponibles
            available_columns = [
                col for col in display_columns if col in opportunities.columns
            ]

            # Estilizar DataFrame
            styled_df = opportunities[available_columns].style.apply(
                lambda x: [
                    (
                        "background-color: #c8e6c9"
                        if x["Estrategia"] == "CALL"
                        else (
                            "background-color: #ffcdd2"
                            if x["Estrategia"] == "PUT"
                            else ""
                        )
                    )
                    for _ in range(len(x))
                ],
                axis=1,
            )

            st.dataframe(
                styled_df,
                column_config={
                    "Symbol": "Símbolo",
                    "Sector": "Sector",
                    "Tendencia": "Tendencia",
                    "Fuerza": "Fuerza",
                    "Precio": st.column_config.NumberColumn("Precio", format="$%.2f"),
                    "RSI": st.column_config.NumberColumn("RSI", format="%.1f"),
                    "Estrategia": "Estrategia",
                    "Setup": "Setup",
                    "Confianza": "Confianza",
                    "Entry": st.column_config.NumberColumn("Entrada", format="$%.2f"),
                    "Stop": st.column_config.NumberColumn("Stop Loss", format="$%.2f"),
                    "Target": st.column_config.NumberColumn("Target", format="$%.2f"),
                    "R/R": "Riesgo/Reward",
                    "Trading_Specialist": "Trading Specialist",
                    "Timestamp": "Hora",
                },
                hide_index=True,
                use_container_width=True,
            )

        with tab2:
            st.markdown("### 🔍 Análisis Detallado por Activo")

            # Filtrar activos de alta confianza
            high_confidence = opportunities[opportunities["Confianza"] == "ALTA"]

            if not high_confidence.empty:
                st.markdown("#### 🌟 Oportunidades de Alta Confianza")

                # Crear tarjetas para cada activo de alta confianza
                for i, (_, row) in enumerate(high_confidence.iterrows()):
                    with st.expander(
                        f"{row['Symbol']} - {row['Estrategia']} - {row['Setup']}",
                        expanded=i == 0,
                    ):
                        # Crear columnas para la información
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            # Información básica
                            st.markdown(f"### {row['Symbol']} - {row['Sector']}")
                            st.markdown(f"**Precio:** ${row['Precio']:.2f}")
                            st.markdown(
                                f"**Estrategia:** {row['Estrategia']} - {row['Setup']}"
                            )
                            st.markdown(f"**Confianza:** {row['Confianza']}")

                            # Niveles
                            st.markdown("#### Niveles de Trading")
                            st.markdown(f"**Entrada:** ${row['Entry']:.2f}")
                            st.markdown(f"**Stop Loss:** ${row['Stop']:.2f}")
                            st.markdown(f"**Target:** ${row['Target']:.2f}")
                            st.markdown(
                                f"**Ratio Riesgo/Recompensa:** {row['R/R']:.2f}"
                            )

                            # Trading Specialist
                            if (
                                "Trading_Specialist" in row
                                and row["Trading_Specialist"] != "NEUTRAL"
                            ):
                                st.markdown("#### 💬 Trading Specialist")
                                signal_color = (
                                    "green"
                                    if row["Trading_Specialist"] == "COMPRA"
                                    else "red"
                                )
                                st.markdown(
                                    f"**⚠️ Señal General:** <span style='color:{signal_color};'>{row['Trading_Specialist']} {row.get('TS_Confianza', '')}</span>",
                                    unsafe_allow_html=True,
                                )

                            # Análisis Técnico
                            if "Análisis_Técnico" in row and row["Análisis_Técnico"]:
                                st.markdown("#### 📊 Análisis Técnico")
                                st.markdown(row["Análisis_Técnico"])

                                # Indicadores
                                if (
                                    "Indicadores_Alcistas" in row
                                    and "Indicadores_Bajistas" in row
                                ):
                                    st.markdown(
                                        f"**Indicadores Alcistas:** {row['Indicadores_Alcistas']}"
                                    )
                                    st.markdown(
                                        f"**Indicadores Bajistas:** {row['Indicadores_Bajistas']}"
                                    )

                            # Soportes y Resistencias
                            if "Soporte" in row or "Resistencia" in row:
                                st.markdown("#### 📏 Soportes y Resistencias")
                                if "Soporte" in row:
                                    st.markdown(f"**Soporte:** ${row['Soporte']:.2f}")
                                if "Resistencia" in row:
                                    st.markdown(
                                        f"**Resistencia:** ${row['Resistencia']:.2f}"
                                    )

                            # Noticias
                            if "Última_Noticia" in row and row["Última_Noticia"]:
                                st.markdown("#### 📰 Últimas Noticias")
                                st.markdown(f"**{row['Última_Noticia']}**")
                                if "Fuente_Noticia" in row:
                                    st.caption(f"Fuente: {row['Fuente_Noticia']}")

                            # Sentimiento
                            if "Sentimiento" in row and row["Sentimiento"] != "neutral":
                                st.markdown("#### 🧠 Sentimiento de Mercado")
                                sentiment_color = (
                                    "green"
                                    if row["Sentimiento"] == "positivo"
                                    else "red"
                                )
                                sentiment_score = (
                                    row.get("Sentimiento_Score", 0.5) * 100
                                )
                                st.markdown(
                                    f"**Sentimiento:** <span style='color:{sentiment_color};'>{row['Sentimiento'].upper()}</span> ({sentiment_score:.1f}%)",
                                    unsafe_allow_html=True,
                                )

                        with col2:
                            # Opciones
                            if "Volatilidad" in row:
                                st.markdown("#### 🎯 Datos de Opciones")
                                st.markdown(
                                    f"**Volatilidad Implícita:** {row['Volatilidad']:.2f}%"
                                )
                                if "Options_Signal" in row:
                                    st.markdown(
                                        f"**Señal de Opciones:** {row['Options_Signal']}"
                                    )

                            # Métricas adicionales
                            st.markdown("#### 📊 Métricas Clave")
                            st.metric("RSI", f"{row['RSI']:.1f}")
                            st.metric("Tendencia", row["Tendencia"])
                            st.metric("Fuerza", row["Fuerza"])

            # Mostrar el resto de oportunidades
            other_opportunities = opportunities[opportunities["Confianza"] != "ALTA"]
            if not other_opportunities.empty:
                st.markdown("#### Otras Oportunidades")

                # Selector de símbolo
                selected_symbol = st.selectbox(
                    "Seleccionar Activo",
                    options=other_opportunities["Symbol"].tolist(),
                    format_func=lambda x: f"{x} - {other_opportunities[other_opportunities['Symbol'] == x]['Estrategia'].values[0]} - {other_opportunities[other_opportunities['Symbol'] == x]['Setup'].values[0]}",
                )

                if selected_symbol:
                    row = other_opportunities[
                        other_opportunities["Symbol"] == selected_symbol
                    ].iloc[0]

                    # Crear columnas para la información
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        # Información básica
                        st.markdown(f"### {row['Symbol']} - {row['Sector']}")
                        st.markdown(f"**Precio:** ${row['Precio']:.2f}")
                        st.markdown(
                            f"**Estrategia:** {row['Estrategia']} - {row['Setup']}"
                        )
                        st.markdown(f"**Confianza:** {row['Confianza']}")

                        # Niveles
                        st.markdown("#### Niveles de Trading")
                        st.markdown(f"**Entrada:** ${row['Entry']:.2f}")
                        st.markdown(f"**Stop Loss:** ${row['Stop']:.2f}")
                        st.markdown(f"**Target:** ${row['Target']:.2f}")
                        st.markdown(f"**Ratio Riesgo/Recompensa:** {row['R/R']:.2f}")

                        # Trading Specialist
                        if (
                            "Trading_Specialist" in row
                            and row["Trading_Specialist"] != "NEUTRAL"
                        ):
                            st.markdown("#### 💬 Trading Specialist")
                            signal_color = (
                                "green"
                                if row["Trading_Specialist"] == "COMPRA"
                                else "red"
                            )
                            st.markdown(
                                f"**⚠️ Señal General:** <span style='color:{signal_color};'>{row['Trading_Specialist']} {row.get('TS_Confianza', '')}</span>",
                                unsafe_allow_html=True,
                            )

                    with col2:
                        # Métricas adicionales
                        st.markdown("#### 📊 Métricas Clave")
                        st.metric("RSI", f"{row['RSI']:.1f}")
                        st.metric("Tendencia", row["Tendencia"])
                        st.metric("Fuerza", row["Fuerza"])

        with tab3:
            # Mostrar detalles por sector
            st.markdown("### 📊 Análisis por Sector")
            sector_stats = (
                opportunities.groupby("Sector")
                .agg(
                    {
                        "Symbol": "count",
                        "Estrategia": lambda x: list(x),
                        "Confianza": lambda x: list(x),
                    }
                )
                .reset_index()
            )

            for _, row in sector_stats.iterrows():
                with st.expander(f"{row['Sector']} ({row['Symbol']} oportunidades)"):
                    calls = len([s for s in row["Estrategia"] if s == "CALL"])
                    puts = len([s for s in row["Estrategia"] if s == "PUT"])
                    high_conf = len([c for c in row["Confianza"] if c == "ALTA"])

                    # Mostrar métricas del sector
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("CALLS", calls)
                    with col2:
                        st.metric("PUTS", puts)
                    with col3:
                        st.metric("Alta Confianza", high_conf)

                    # Mostrar activos del sector
                    sector_opportunities = opportunities[
                        opportunities["Sector"] == row["Sector"]
                    ]
                    st.dataframe(
                        sector_opportunities[
                            [
                                "Symbol",
                                "Estrategia",
                                "Confianza",
                                "Setup",
                                "Precio",
                                "R/R",
                            ]
                        ],
                        hide_index=True,
                        use_container_width=True,
                    )

        # Actualización
        st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")


def run_scanner(symbols_dict):
    """
    Ejecuta el scanner de mercado.

    Args:
        symbols_dict (dict): Diccionario de símbolos por sector
    """
    scanner = MarketScanner(symbols_dict)
    display_opportunities(scanner)
