"""
Enhanced Market Scanner - Implementación mejorada del Scanner de Mercado
------------------------------------------------------------------------
Este módulo proporciona una versión mejorada del scanner de mercado que incluye:
1. Tabla condensada con todos los activos del sector
2. Información detallada para activos de alta confianza
3. Tarjetas informativas completas con análisis técnico, opciones, etc.
4. Identificación de señales de alta confianza (COMPRA/VENTA FUERTE)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

# Configurar logging
logger = logging.getLogger(__name__)


def render_enhanced_market_scanner(
    scanner, analyzer, get_market_context, symbols_dict=None
):
    """
    Renderiza la versión mejorada del scanner de mercado.

    Args:
        scanner: Instancia del scanner de mercado
        analyzer: Instancia del analizador de trading
        get_market_context: Función para obtener el contexto de mercado
        symbols_dict: Diccionario de símbolos por sector (opcional)
    """
    st.markdown("## 🔍 Scanner de Mercado Mejorado")

    # Definir sectores predeterminados
    default_sectors = [
        "Tecnología",
        "Finanzas",
        "Energía",
        "Salud",
        "Consumo",
        "Industrial",
        "ETF",
        "Índices",
        "Cripto ETFs",
        "Materias Primas",
        "Bonos",
        "Inmobiliario",
        "Volatilidad",
        "Forex",
    ]

    # Obtener los sectores disponibles
    try:
        # Primero verificamos si se pasó el parámetro symbols_dict
        if symbols_dict is not None:
            available_sectors = list(symbols_dict.keys())
        # Luego intentamos acceder al atributo symbols_dict del scanner
        elif hasattr(scanner, "symbols_dict"):
            available_sectors = list(scanner.symbols_dict.keys())
        # Luego intentamos acceder al atributo SYMBOLS del scanner
        elif hasattr(scanner, "SYMBOLS"):
            available_sectors = list(scanner.SYMBOLS.keys())
        # Si no encontramos ninguno, usamos los sectores predeterminados
        else:
            available_sectors = default_sectors
            logger.warning("No se encontraron sectores, usando predeterminados")
    except Exception as e:
        logger.warning(f"Error al obtener sectores: {str(e)}")
        available_sectors = default_sectors

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
                "Timestamp",
            ]

            # Añadir Trading_Specialist si existe
            if "Trading_Specialist" in opportunities.columns:
                display_columns.insert(-1, "Trading_Specialist")

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

            # Configuración de columnas
            column_config = {
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
                "Timestamp": "Hora",
            }

            # Añadir Trading_Specialist a la configuración si existe
            if "Trading_Specialist" in opportunities.columns:
                column_config["Trading_Specialist"] = "Trading Specialist"

            st.dataframe(
                styled_df,
                column_config=column_config,
                hide_index=True,
                use_container_width=True,
            )

        with tab2:
            st.markdown("### 🔍 Análisis Detallado por Activo")

            # Identificar activos de alta confianza
            # Consideramos alta confianza si:
            # 1. La columna Confianza es "ALTA" o
            # 2. Trading_Specialist contiene "FUERTE"
            high_confidence = opportunities[opportunities["Confianza"] == "ALTA"].copy()

            # Si existe la columna Trading_Specialist, añadir los que tienen señal FUERTE
            if (
                "Trading_Specialist" in opportunities.columns
                and "TS_Confianza" in opportunities.columns
            ):
                strong_signals = opportunities[
                    (opportunities["Trading_Specialist"].isin(["COMPRA", "VENTA"]))
                    & (opportunities["TS_Confianza"] == "ALTA")
                ].copy()

                # Combinar con los de alta confianza, evitando duplicados
                if not strong_signals.empty:
                    high_confidence = pd.concat(
                        [high_confidence, strong_signals]
                    ).drop_duplicates(subset=["Symbol"])

            # Crear pestañas para alta confianza y otras oportunidades
            if not high_confidence.empty:
                st.markdown("#### 🌟 Oportunidades de Alta Confianza")

                # Selector para activos de alta confianza
                selected_high_conf = st.selectbox(
                    "Seleccionar Activo de Alta Confianza",
                    options=high_confidence["Symbol"].tolist(),
                    format_func=lambda x: f"{x} - {high_confidence[high_confidence['Symbol'] == x]['Estrategia'].values[0]} - {high_confidence[high_confidence['Symbol'] == x]['Setup'].values[0]}",
                )

                if selected_high_conf:
                    # Obtener datos del activo seleccionado
                    row = high_confidence[
                        high_confidence["Symbol"] == selected_high_conf
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
                            and pd.notna(row["Trading_Specialist"])
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
                        if "Análisis_Técnico" in row and pd.notna(
                            row["Análisis_Técnico"]
                        ):
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
                            if "Soporte" in row and pd.notna(row["Soporte"]):
                                st.markdown(f"**Soporte:** ${row['Soporte']:.2f}")
                            if "Resistencia" in row and pd.notna(row["Resistencia"]):
                                st.markdown(
                                    f"**Resistencia:** ${row['Resistencia']:.2f}"
                                )

                        # Noticias
                        if "Última_Noticia" in row and pd.notna(row["Última_Noticia"]):
                            st.markdown("#### 📰 Últimas Noticias")
                            st.markdown(f"**{row['Última_Noticia']}**")
                            if "Fuente_Noticia" in row:
                                st.caption(f"Fuente: {row['Fuente_Noticia']}")

                        # Sentimiento
                        if (
                            "Sentimiento" in row
                            and pd.notna(row["Sentimiento"])
                            and row["Sentimiento"] != "neutral"
                        ):
                            st.markdown("#### 🧠 Sentimiento de Mercado")
                            sentiment_color = (
                                "green" if row["Sentimiento"] == "positivo" else "red"
                            )
                            sentiment_score = row.get("Sentimiento_Score", 0.5) * 100
                            st.markdown(
                                f"**Sentimiento:** <span style='color:{sentiment_color};'>{row['Sentimiento'].upper()}</span> ({sentiment_score:.1f}%)",
                                unsafe_allow_html=True,
                            )

                    with col2:
                        # Opciones
                        if "Volatilidad" in row and pd.notna(row["Volatilidad"]):
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
            other_opportunities = opportunities[
                ~opportunities["Symbol"].isin(high_confidence["Symbol"])
            ]
            if not other_opportunities.empty:
                st.markdown("#### Otras Oportunidades")

                # Selector de símbolo
                selected_symbol = st.selectbox(
                    "Seleccionar Activo",
                    options=other_opportunities["Symbol"].tolist(),
                    format_func=lambda x: f"{x} - {other_opportunities[other_opportunities['Symbol'] == x]['Estrategia'].values[0]} - {other_opportunities[other_opportunities['Symbol'] == x]['Setup'].values[0]}",
                    key="other_opportunities_selectbox",  # Clave única para evitar conflictos
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
                            and pd.notna(row["Trading_Specialist"])
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

            # Crear selectbox para elegir sector
            selected_sector = st.selectbox(
                "Seleccionar Sector",
                options=sector_stats["Sector"].tolist(),
                format_func=lambda x: f"{x} ({sector_stats[sector_stats['Sector'] == x]['Symbol'].values[0]} oportunidades)",
            )

            if selected_sector:
                # Obtener datos del sector seleccionado
                row = sector_stats[sector_stats["Sector"] == selected_sector].iloc[0]

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
                    opportunities["Sector"] == selected_sector
                ]

                # Mostrar tabla condensada
                st.markdown("#### Tabla Condensada")
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

                # Identificar activos de alta confianza en este sector
                sector_high_conf = sector_opportunities[
                    sector_opportunities["Confianza"] == "ALTA"
                ].copy()

                # Si existe la columna Trading_Specialist, añadir los que tienen señal FUERTE
                if (
                    "Trading_Specialist" in sector_opportunities.columns
                    and "TS_Confianza" in sector_opportunities.columns
                ):
                    sector_strong_signals = sector_opportunities[
                        (
                            sector_opportunities["Trading_Specialist"].isin(
                                ["COMPRA", "VENTA"]
                            )
                        )
                        & (sector_opportunities["TS_Confianza"] == "ALTA")
                    ].copy()

                    # Combinar con los de alta confianza, evitando duplicados
                    if not sector_strong_signals.empty:
                        sector_high_conf = pd.concat(
                            [sector_high_conf, sector_strong_signals]
                        ).drop_duplicates(subset=["Symbol"])

                # Mostrar activos de alta confianza para este sector
                if not sector_high_conf.empty:
                    st.markdown(
                        "#### 🌟 Oportunidades de Alta Confianza en este Sector"
                    )

                    # Crear selectbox para elegir activo de alta confianza
                    selected_high_conf_asset = st.selectbox(
                        "Seleccionar Activo de Alta Confianza",
                        options=sector_high_conf["Symbol"].tolist(),
                        format_func=lambda x: f"{x} - {sector_high_conf[sector_high_conf['Symbol'] == x]['Estrategia'].values[0]} - {sector_high_conf[sector_high_conf['Symbol'] == x]['Setup'].values[0]}",
                        key="sector_high_conf_selectbox",  # Clave única para evitar conflictos
                    )

                    if selected_high_conf_asset:
                        # Obtener datos del activo seleccionado
                        asset_row = sector_high_conf[
                            sector_high_conf["Symbol"] == selected_high_conf_asset
                        ].iloc[0]

                        # Crear columnas para la información
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            # Información básica
                            st.markdown(
                                f"### {asset_row['Symbol']} - {asset_row['Sector']}"
                            )
                            st.markdown(f"**Precio:** ${asset_row['Precio']:.2f}")
                            st.markdown(
                                f"**Estrategia:** {asset_row['Estrategia']} - {asset_row['Setup']}"
                            )
                            st.markdown(f"**Confianza:** {asset_row['Confianza']}")

                            # Niveles
                            st.markdown("#### Niveles de Trading")
                            st.markdown(f"**Entrada:** ${asset_row['Entry']:.2f}")
                            st.markdown(f"**Stop Loss:** ${asset_row['Stop']:.2f}")
                            st.markdown(f"**Target:** ${asset_row['Target']:.2f}")
                            st.markdown(
                                f"**Ratio Riesgo/Recompensa:** {asset_row['R/R']:.2f}"
                            )

                            # Trading Specialist
                            if (
                                "Trading_Specialist" in asset_row
                                and pd.notna(asset_row["Trading_Specialist"])
                                and asset_row["Trading_Specialist"] != "NEUTRAL"
                            ):
                                st.markdown("#### 💬 Trading Specialist")
                                signal_color = (
                                    "green"
                                    if asset_row["Trading_Specialist"] == "COMPRA"
                                    else "red"
                                )
                                st.markdown(
                                    f"**⚠️ Señal General:** <span style='color:{signal_color};'>{asset_row['Trading_Specialist']} {asset_row.get('TS_Confianza', '')}</span>",
                                    unsafe_allow_html=True,
                                )

                            # Análisis Técnico
                            if "Análisis_Técnico" in asset_row and pd.notna(
                                asset_row["Análisis_Técnico"]
                            ):
                                st.markdown("#### 📊 Análisis Técnico")
                                st.markdown(asset_row["Análisis_Técnico"])

                        with col2:
                            # Métricas adicionales
                            st.markdown("#### 📊 Métricas Clave")
                            st.metric("RSI", f"{asset_row['RSI']:.1f}")
                            st.metric("Tendencia", asset_row["Tendencia"])
                            st.metric("Fuerza", asset_row["Fuerza"])
                else:
                    st.info("No hay oportunidades de alta confianza en este sector.")

        # Actualización
        st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
