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
            # 2. Trading_Specialist contiene "COMPRA" o "VENTA" con confianza "ALTA"
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

            # Agregar un indicador visual para señales de alta confianza
            if not high_confidence.empty:
                st.markdown(
                    """
                <div style="background-color: #f8d7da; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                    <h4 style="color: #721c24; margin: 0;">🚨 Señales de Alta Confianza Detectadas</h4>
                    <p style="margin: 5px 0 0 0;">Se han detectado señales de alta confianza que requieren atención inmediata.</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

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

                    # Crear pestañas para diferentes tipos de análisis con diseño mejorado
                    st.markdown(
                        """
                    <style>
                    .stTabs [data-baseweb="tab-list"] {
                        gap: 8px;
                    }
                    .stTabs [data-baseweb="tab"] {
                        background-color: #f0f2f6;
                        border-radius: 4px 4px 0px 0px;
                        padding: 10px 16px;
                        font-weight: 600;
                    }
                    .stTabs [aria-selected="true"] {
                        background-color: #e6f3ff;
                        color: #0366d6;
                        border-bottom: 2px solid #0366d6;
                    }
                    </style>
                    """,
                        unsafe_allow_html=True,
                    )

                    analysis_tabs = st.tabs(
                        [
                            "📊 Resumen",
                            "📈 Análisis Técnico",
                            "🎯 Opciones",
                            "⚙️ Multi-Timeframe",
                            "🧠 Análisis Experto",
                            "📰 Noticias y Sentimiento",
                        ]
                    )

                    # Pestaña de Resumen con diseño mejorado
                    with analysis_tabs[0]:
                        # Encabezado con estilo
                        symbol_color = (
                            "green"
                            if row["Estrategia"] == "CALL"
                            else "red" if row["Estrategia"] == "PUT" else "gray"
                        )
                        st.markdown(
                            f"""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid {symbol_color};">
                            <h2 style="margin:0; color: {symbol_color};">{row['Symbol']} - {row['Sector']}</h2>
                            <p style="margin:5px 0 0 0; font-size: 1.1em;">Precio: <b>${row['Precio']:.2f}</b> | Estrategia: <b style="color: {symbol_color};">{row['Estrategia']}</b> | Confianza: <b>{row['Confianza']}</b></p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Dividir en columnas
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            # Tarjeta de niveles de trading
                            st.markdown(
                                f"""
                            <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                                <h4 style="margin-top:0;">📏 Niveles de Trading</h4>
                                <table style="width:100%">
                                    <tr>
                                        <td style="padding: 5px; width: 40%;"><b>Entrada:</b></td>
                                        <td style="padding: 5px;">${row['Entry']:.2f}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 5px; width: 40%;"><b>Stop Loss:</b></td>
                                        <td style="padding: 5px; color: red;">${row['Stop']:.2f}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 5px; width: 40%;"><b>Target:</b></td>
                                        <td style="padding: 5px; color: green;">${row['Target']:.2f}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 5px; width: 40%;"><b>Ratio R/R:</b></td>
                                        <td style="padding: 5px; font-weight: bold;">{row['R/R']:.2f}</td>
                                    </tr>
                                </table>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Trading Specialist con estilo
                            if (
                                "Trading_Specialist" in row
                                and pd.notna(row["Trading_Specialist"])
                                and row["Trading_Specialist"] != "NEUTRAL"
                            ):
                                signal_color = (
                                    "green"
                                    if row["Trading_Specialist"] == "COMPRA"
                                    else "red"
                                )
                                st.markdown(
                                    f"""
                                <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 15px; border-left: 5px solid {signal_color};">
                                    <h4 style="margin-top:0;">💬 Trading Specialist</h4>
                                    <p style="font-size: 1.1em; margin: 5px 0;">Señal: <span style="color:{signal_color}; font-weight:bold;">{row['Trading_Specialist']} {row.get('TS_Confianza', '')}</span></p>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                        with col2:
                            # Métricas clave con estilo
                            st.markdown(
                                "<h4 style='margin-bottom:15px;'>📊 Métricas Clave</h4>",
                                unsafe_allow_html=True,
                            )

                            # RSI con color basado en valor
                            rsi_value = row["RSI"]
                            rsi_color = (
                                "red"
                                if rsi_value > 70
                                else "green" if rsi_value < 30 else "gray"
                            )
                            st.markdown(
                                f"""
                            <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span><b>RSI</b></span>
                                    <span style="color: {rsi_color}; font-weight: bold;">{rsi_value:.1f}</span>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Tendencia con color
                            trend = row["Tendencia"]
                            trend_color = (
                                "green"
                                if trend == "ALCISTA"
                                else "red" if trend == "BAJISTA" else "gray"
                            )
                            st.markdown(
                                f"""
                            <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span><b>Tendencia</b></span>
                                    <span style="color: {trend_color}; font-weight: bold;">{trend}</span>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Fuerza con color
                            strength = row["Fuerza"]
                            strength_color = (
                                "green"
                                if strength == "fuerte"
                                else "orange" if strength == "moderada" else "gray"
                            )
                            st.markdown(
                                f"""
                            <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span><b>Fuerza</b></span>
                                    <span style="color: {strength_color}; font-weight: bold;">{strength}</span>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Setup
                            st.markdown(
                                f"""
                            <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span><b>Setup</b></span>
                                    <span style="font-weight: bold;">{row['Setup']}</span>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                    # Pestaña de Análisis Técnico
                    with analysis_tabs[1]:
                        # Análisis Técnico
                        if "Análisis_Técnico" in row and pd.notna(
                            row["Análisis_Técnico"]
                        ):
                            # Crear una tarjeta moderna para el análisis técnico
                            st.markdown(
                                f"""
                            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #0366d6;">
                                <h3 style="margin-top:0; color: #0366d6;">📊 Análisis Técnico Detallado</h3>
                                <p style="margin-bottom: 10px;">{row["Análisis_Técnico"]}</p>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Indicadores en tarjetas modernas
                            if (
                                "Indicadores_Alcistas" in row
                                and "Indicadores_Bajistas" in row
                            ):
                                st.markdown("#### Indicadores")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(
                                        f"""
                                    <div style="background-color: #e6f4ea; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 3px solid #34a853;">
                                        <h5 style="margin-top:0; color: #34a853;">Indicadores Alcistas</h5>
                                        <p style="margin:0;">{row["Indicadores_Alcistas"]}</p>
                                    </div>
                                    """,
                                        unsafe_allow_html=True,
                                    )
                                with col2:
                                    st.markdown(
                                        f"""
                                    <div style="background-color: #fce8e6; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 3px solid #ea4335;">
                                        <h5 style="margin-top:0; color: #ea4335;">Indicadores Bajistas</h5>
                                        <p style="margin:0;">{row["Indicadores_Bajistas"]}</p>
                                    </div>
                                    """,
                                        unsafe_allow_html=True,
                                    )

                            # Soportes y Resistencias en tarjetas modernas
                            if "Soporte" in row or "Resistencia" in row:
                                st.markdown(
                                    "<h4 style='margin-top:20px;'>📏 Soportes y Resistencias</h4>",
                                    unsafe_allow_html=True,
                                )
                                col1, col2 = st.columns(2)
                                with col1:
                                    if "Soporte" in row and pd.notna(row["Soporte"]):
                                        st.markdown(
                                            f"""
                                        <div style="background-color: #e6f4ea; padding: 15px; border-radius: 5px; text-align: center;">
                                            <h5 style="margin-top:0; color: #34a853;">Soporte</h5>
                                            <p style="font-size: 1.5em; font-weight: bold; margin:0;">${row['Soporte']:.2f}</p>
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                                with col2:
                                    if "Resistencia" in row and pd.notna(
                                        row["Resistencia"]
                                    ):
                                        st.markdown(
                                            f"""
                                        <div style="background-color: #fce8e6; padding: 15px; border-radius: 5px; text-align: center;">
                                            <h5 style="margin-top:0; color: #ea4335;">Resistencia</h5>
                                            <p style="font-size: 1.5em; font-weight: bold; margin:0;">${row['Resistencia']:.2f}</p>
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                        else:
                            st.info(
                                "No hay análisis técnico detallado disponible para este activo."
                            )

                    # Pestaña de Opciones con diseño mejorado
                    with analysis_tabs[2]:
                        # Encabezado con estilo
                        st.markdown(
                            "<h3 style='color: #5c6bc0; margin-bottom: 15px;'>🎯 Análisis de Opciones</h3>",
                            unsafe_allow_html=True,
                        )

                        if "Volatilidad" in row and pd.notna(row["Volatilidad"]):
                            # Determinar nivel de volatilidad para color
                            volatility = row["Volatilidad"]
                            if volatility > 50:
                                vol_color = "#d32f2f"  # Rojo para alta volatilidad
                                vol_level = "ALTA"
                                vol_bg = "#ffebee"
                            elif volatility > 30:
                                vol_color = "#f57c00"  # Naranja para volatilidad media
                                vol_level = "MEDIA"
                                vol_bg = "#fff3e0"
                            else:
                                vol_color = "#388e3c"  # Verde para baja volatilidad
                                vol_level = "BAJA"
                                vol_bg = "#e8f5e9"

                            # Tarjeta de volatilidad
                            st.markdown(
                                f"""
                            <div style="background-color: {vol_bg}; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid {vol_color};">
                                <h4 style="margin-top:0; color: {vol_color};">Volatilidad Implícita: {volatility:.2f}%</h4>
                                <p style="margin:0;">Nivel de volatilidad: <strong>{vol_level}</strong></p>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Señal de opciones en tarjeta
                            if "Options_Signal" in row and pd.notna(
                                row["Options_Signal"]
                            ):
                                options_signal = row["Options_Signal"]
                                if "CALL" in options_signal:
                                    signal_color = "#388e3c"  # Verde para CALL
                                    signal_bg = "#e8f5e9"
                                elif "PUT" in options_signal:
                                    signal_color = "#d32f2f"  # Rojo para PUT
                                    signal_bg = "#ffebee"
                                else:
                                    signal_color = "#5c6bc0"  # Azul para neutral
                                    signal_bg = "#e8eaf6"

                                st.markdown(
                                    f"""
                                <div style="background-color: {signal_bg}; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid {signal_color};">
                                    <h4 style="margin-top:0; color: {signal_color};">Estrategia Recomendada: {options_signal}</h4>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                            # Análisis de opciones en tarjeta
                            if "Options_Analysis" in row and pd.notna(
                                row["Options_Analysis"]
                            ):
                                st.markdown(
                                    f"""
                                <div style="background-color: #e8eaf6; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #3f51b5;">
                                    <h4 style="margin-top:0; color: #3f51b5;">Análisis Detallado</h4>
                                    <p style="margin:0;">{row["Options_Analysis"]}</p>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.info(
                                "No hay datos de opciones disponibles para este activo."
                            )

                    # Pestaña de Multi-Timeframe con diseño mejorado
                    with analysis_tabs[3]:
                        # Encabezado con estilo
                        st.markdown(
                            "<h3 style='color: #7b1fa2; margin-bottom: 15px;'>⚙️ Análisis Multi-Timeframe</h3>",
                            unsafe_allow_html=True,
                        )

                        if "MTF_Analysis" in row and pd.notna(row["MTF_Analysis"]):
                            # Tarjeta para el análisis MTF
                            st.markdown(
                                f"""
                            <div style="background-color: #f3e5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #7b1fa2;">
                                <h4 style="margin-top:0; color: #7b1fa2;">Resumen Multi-Timeframe</h4>
                                <p style="margin:0;">{row["MTF_Analysis"]}</p>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Tendencias por timeframe en tarjetas modernas
                            st.markdown(
                                "<h4 style='margin-top:20px;'>Tendencias por Timeframe</h4>",
                                unsafe_allow_html=True,
                            )

                            timeframes = ["Diario", "Semanal", "Mensual"]
                            cols = st.columns(len(timeframes))

                            for i, tf in enumerate(timeframes):
                                tf_key = f"Tendencia_{tf}"
                                if tf_key in row and pd.notna(row[tf_key]):
                                    trend = row[tf_key]
                                    if trend == "ALCISTA":
                                        color = "#388e3c"  # Verde para alcista
                                        bg_color = "#e8f5e9"
                                        icon = "↗️"  # Flecha hacia arriba
                                    elif trend == "BAJISTA":
                                        color = "#d32f2f"  # Rojo para bajista
                                        bg_color = "#ffebee"
                                        icon = "↘️"  # Flecha hacia abajo
                                    else:  # NEUTRAL
                                        color = "#757575"  # Gris para neutral
                                        bg_color = "#f5f5f5"
                                        icon = "↔️"  # Flecha horizontal

                                    with cols[i]:
                                        st.markdown(
                                            f"""
                                        <div style="background-color: {bg_color}; padding: 15px; border-radius: 5px; text-align: center; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                                            <h5 style="margin-top:0; color: {color};">{tf}</h5>
                                            <p style="font-size: 1.2em; font-weight: bold; margin:5px 0; color: {color};">{icon} {trend}</p>
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                                else:
                                    with cols[i]:
                                        st.markdown(
                                            f"""
                                        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                                            <h5 style="margin-top:0; color: #757575;">{tf}</h5>
                                            <p style="font-size: 1.2em; font-weight: bold; margin:5px 0; color: #757575;">N/A</p>
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                        else:
                            st.info(
                                "No hay análisis multi-timeframe disponible para este activo."
                            )

                    # Pestaña de Análisis Experto con diseño mejorado
                    with analysis_tabs[4]:
                        # Encabezado con estilo
                        st.markdown(
                            "<h3 style='color: #00796b; margin-bottom: 15px;'>🧠 Análisis Experto</h3>",
                            unsafe_allow_html=True,
                        )

                        if "Análisis_Experto" in row and pd.notna(
                            row["Análisis_Experto"]
                        ):
                            # Recomendación en tarjeta destacada
                            if "Recomendación" in row and pd.notna(
                                row["Recomendación"]
                            ):
                                recommendation = row["Recomendación"]

                                # Determinar colores y estilos basados en la recomendación
                                if recommendation in ["COMPRAR", "FUERTE COMPRA"]:
                                    rec_color = "#388e3c"  # Verde para compra
                                    rec_bg = "#e8f5e9"
                                    rec_icon = "📈"  # Gráfico subiendo
                                elif recommendation in ["VENDER", "FUERTE VENTA"]:
                                    rec_color = "#d32f2f"  # Rojo para venta
                                    rec_bg = "#ffebee"
                                    rec_icon = "📉"  # Gráfico bajando
                                else:  # MANTENER o similar
                                    rec_color = "#0288d1"  # Azul para mantener
                                    rec_bg = "#e1f5fe"
                                    rec_icon = "📊"  # Gráfico plano

                                # Tarjeta de recomendación destacada
                                st.markdown(
                                    f"""
                                <div style="background-color: {rec_bg}; padding: 20px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid {rec_color}; text-align: center;">
                                    <h3 style="margin-top:0; color: {rec_color};">{rec_icon} Recomendación</h3>
                                    <p style="font-size: 1.8em; font-weight: bold; margin:10px 0; color: {rec_color};">{recommendation}</p>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                            # Análisis experto en tarjeta
                            st.markdown(
                                f"""
                            <div style="background-color: #e0f2f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #00796b;">
                                <h4 style="margin-top:0; color: #00796b;">Análisis Detallado</h4>
                                <p style="margin:0;">{row["Análisis_Experto"]}</p>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Indicadores adicionales si están disponibles
                            if (
                                "Indicadores_Alcistas" in row
                                and "Indicadores_Bajistas" in row
                            ):
                                # Contar indicadores
                                bullish_count = (
                                    len(row["Indicadores_Alcistas"].split(","))
                                    if "No se detectaron"
                                    not in row["Indicadores_Alcistas"]
                                    else 0
                                )
                                bearish_count = (
                                    len(row["Indicadores_Bajistas"].split(","))
                                    if "No se detectaron"
                                    not in row["Indicadores_Bajistas"]
                                    else 0
                                )

                                # Calcular balance de indicadores
                                if bullish_count > bearish_count:
                                    balance = "ALCISTA"
                                    balance_color = "#388e3c"
                                    balance_bg = "#e8f5e9"
                                elif bearish_count > bullish_count:
                                    balance = "BAJISTA"
                                    balance_color = "#d32f2f"
                                    balance_bg = "#ffebee"
                                else:
                                    balance = "NEUTRAL"
                                    balance_color = "#757575"
                                    balance_bg = "#f5f5f5"

                                # Mostrar balance de indicadores
                                st.markdown(
                                    f"""
                                <div style="background-color: {balance_bg}; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid {balance_color}; text-align: center;">
                                    <h4 style="margin-top:0; color: {balance_color};">Balance de Indicadores</h4>
                                    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                                        <div style="text-align: center; width: 30%;">
                                            <p style="font-size: 1.2em; font-weight: bold; color: #388e3c;">{bullish_count}</p>
                                            <p style="margin:0;">Alcistas</p>
                                        </div>
                                        <div style="text-align: center; width: 30%;">
                                            <p style="font-size: 1.2em; font-weight: bold; color: {balance_color};">{balance}</p>
                                            <p style="margin:0;">Balance</p>
                                        </div>
                                        <div style="text-align: center; width: 30%;">
                                            <p style="font-size: 1.2em; font-weight: bold; color: #d32f2f;">{bearish_count}</p>
                                            <p style="margin:0;">Bajistas</p>
                                        </div>
                                    </div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.info(
                                "No hay análisis experto disponible para este activo."
                            )

                    # Pestaña de Noticias y Sentimiento con diseño mejorado
                    with analysis_tabs[5]:
                        # Encabezado con estilo
                        st.markdown(
                            "<h3 style='color: #e65100; margin-bottom: 15px;'>📰 Noticias y Sentimiento</h3>",
                            unsafe_allow_html=True,
                        )

                        # Sentimiento en tarjeta moderna
                        if "Sentimiento" in row and pd.notna(row["Sentimiento"]):
                            sentiment = row["Sentimiento"]
                            sentiment_score = row.get("Sentimiento_Score", 0.5) * 100

                            # Determinar colores y estilos basados en el sentimiento
                            if sentiment == "positivo":
                                sentiment_color = "#388e3c"  # Verde para positivo
                                sentiment_bg = "#e8f5e9"
                                sentiment_icon = "😀"  # Cara sonriente
                                sentiment_text = "POSITIVO"
                            elif sentiment == "negativo":
                                sentiment_color = "#d32f2f"  # Rojo para negativo
                                sentiment_bg = "#ffebee"
                                sentiment_icon = "🙁"  # Cara triste
                                sentiment_text = "NEGATIVO"
                            else:  # neutral
                                sentiment_color = "#757575"  # Gris para neutral
                                sentiment_bg = "#f5f5f5"
                                sentiment_icon = "😐"  # Cara neutral
                                sentiment_text = "NEUTRAL"

                            # Tarjeta de sentimiento
                            st.markdown(
                                f"""
                            <div style="background-color: {sentiment_bg}; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid {sentiment_color}; display: flex; align-items: center; justify-content: space-between;">
                                <div>
                                    <h4 style="margin-top:0; color: {sentiment_color};">🧠 Sentimiento de Mercado</h4>
                                    <p style="margin:0; font-size: 1.1em;">Sentimiento: <strong style="color: {sentiment_color};">{sentiment_text}</strong></p>
                                </div>
                                <div style="text-align: center; min-width: 80px;">
                                    <div style="font-size: 2em;">{sentiment_icon}</div>
                                    <div style="font-weight: bold; color: {sentiment_color};">{sentiment_score:.1f}%</div>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                        # Última noticia en tarjeta destacada
                        if "Última_Noticia" in row and pd.notna(row["Última_Noticia"]):
                            st.markdown(
                                f"""
                            <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #e65100;">
                                <h4 style="margin-top:0; color: #e65100;">📰 Última Noticia</h4>
                                <p style="margin:0; font-weight: bold;">{row["Última_Noticia"]}</p>
                                <p style="margin:5px 0 0 0; font-size: 0.8em; color: #757575;">Fuente: {row.get('Fuente_Noticia', 'No especificada')}</p>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Noticias adicionales en tarjeta
                            if "Noticias_Adicionales" in row and pd.notna(
                                row["Noticias_Adicionales"]
                            ):
                                st.markdown(
                                    f"""
                                <div style="background-color: #fff8e1; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #ffa000;">
                                    <h4 style="margin-top:0; color: #ffa000;">Más Noticias</h4>
                                    <p style="margin:0;">{row["Noticias_Adicionales"]}</p>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                            # Añadir botón para buscar más noticias
                            st.markdown(
                                f"""
                            <div style="text-align: center; margin-top: 20px;">
                                <a href="https://www.google.com/search?q={row['Symbol']}+stock+news" target="_blank" style="text-decoration: none;">
                                    <button style="background-color: #e65100; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">
                                        🔍 Buscar Más Noticias
                                    </button>
                                </a>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.info("No hay noticias disponibles para este activo.")

                            # Añadir botón para buscar noticias
                            st.markdown(
                                f"""
                            <div style="text-align: center; margin-top: 20px;">
                                <a href="https://www.google.com/search?q={row['Symbol']}+stock+news" target="_blank" style="text-decoration: none;">
                                    <button style="background-color: #e65100; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">
                                        🔍 Buscar Noticias
                                    </button>
                                </a>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

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
                # Contar señales de alta confianza con diferentes capitalizaciones
                high_conf = len([c for c in row["Confianza"] if c.upper() == "ALTA"])

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

                # Identificar activos de alta confianza en este sector con diferentes capitalizaciones
                sector_high_conf = sector_opportunities[
                    sector_opportunities["Confianza"].str.upper() == "ALTA"
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
                        & (sector_opportunities["TS_Confianza"].str.upper() == "ALTA")
                    ].copy()

                    # Combinar con los de alta confianza, evitando duplicados
                    if not sector_strong_signals.empty:
                        sector_high_conf = pd.concat(
                            [sector_high_conf, sector_strong_signals]
                        ).drop_duplicates(subset=["Symbol"])

                # Verificar si realmente hay señales de alta confianza
                # Comparar con el contador de alta confianza para asegurar consistencia
                if high_conf > 0 and sector_high_conf.empty:
                    # Buscar de nuevo con criterios más amplios y verificar si hay valores nulos
                    try:
                        # Intentar con str.contains para mayor flexibilidad
                        sector_high_conf = sector_opportunities[
                            sector_opportunities["Confianza"].str.contains(
                                "alta", case=False, na=False
                            )
                        ].copy()
                    except:
                        # Si falla, usar el enfoque anterior
                        sector_high_conf = sector_opportunities[
                            (sector_opportunities["Confianza"] == "Alta")
                            | (sector_opportunities["Confianza"] == "ALTA")
                            | (sector_opportunities["Confianza"] == "alta")
                        ].copy()

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

                        # Crear pestañas para diferentes tipos de análisis
                        analysis_tabs = st.tabs(
                            [
                                "📊 Resumen",
                                "📈 Análisis Técnico",
                                "🎯 Opciones",
                                "⚙️ Multi-Timeframe",
                                "🧠 Análisis Experto",
                                "📰 Noticias y Sentimiento",
                            ]
                        )

                        # Pestaña de Resumen con diseño mejorado
                        with analysis_tabs[0]:
                            # Encabezado con estilo
                            symbol_color = (
                                "#388e3c"
                                if asset_row["Estrategia"] == "CALL"
                                else (
                                    "#d32f2f"
                                    if asset_row["Estrategia"] == "PUT"
                                    else "#757575"
                                )
                            )
                            st.markdown(
                                f"""
                            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid {symbol_color};">
                                <h2 style="margin:0; color: {symbol_color};">{asset_row['Symbol']} - {asset_row['Sector']}</h2>
                                <p style="margin:5px 0 0 0; font-size: 1.1em;">Precio: <b>${asset_row['Precio']:.2f}</b> | Estrategia: <b style="color: {symbol_color};">{asset_row['Estrategia']}</b> | Confianza: <b>{asset_row['Confianza']}</b></p>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Dividir en columnas
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                # Tarjeta de niveles de trading
                                st.markdown(
                                    f"""
                                <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                                    <h4 style="margin-top:0;">📏 Niveles de Trading</h4>
                                    <table style="width:100%">
                                        <tr>
                                            <td style="padding: 5px; width: 40%;"><b>Entrada:</b></td>
                                            <td style="padding: 5px;">${asset_row['Entry']:.2f}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 5px; width: 40%;"><b>Stop Loss:</b></td>
                                            <td style="padding: 5px; color: red;">${asset_row['Stop']:.2f}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 5px; width: 40%;"><b>Target:</b></td>
                                            <td style="padding: 5px; color: green;">${asset_row['Target']:.2f}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 5px; width: 40%;"><b>Ratio R/R:</b></td>
                                            <td style="padding: 5px; font-weight: bold;">{asset_row['R/R']:.2f}</td>
                                        </tr>
                                    </table>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                                # Trading Specialist con estilo
                                if (
                                    "Trading_Specialist" in asset_row
                                    and pd.notna(asset_row["Trading_Specialist"])
                                    and asset_row["Trading_Specialist"] != "NEUTRAL"
                                ):
                                    signal_color = (
                                        "#388e3c"
                                        if asset_row["Trading_Specialist"] == "COMPRA"
                                        else "#d32f2f"
                                    )
                                    st.markdown(
                                        f"""
                                    <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 15px; border-left: 5px solid {signal_color};">
                                        <h4 style="margin-top:0;">💬 Trading Specialist</h4>
                                        <p style="font-size: 1.1em; margin: 5px 0;">Señal: <span style="color:{signal_color}; font-weight:bold;">{asset_row['Trading_Specialist']} {asset_row.get('TS_Confianza', '')}</span></p>
                                    </div>
                                    """,
                                        unsafe_allow_html=True,
                                    )

                            with col2:
                                # Métricas clave con estilo
                                st.markdown(
                                    "<h4 style='margin-bottom:15px;'>📊 Métricas Clave</h4>",
                                    unsafe_allow_html=True,
                                )

                                # RSI con color basado en valor
                                rsi_value = asset_row["RSI"]
                                rsi_color = (
                                    "#d32f2f"
                                    if rsi_value > 70
                                    else "#388e3c" if rsi_value < 30 else "#757575"
                                )
                                st.markdown(
                                    f"""
                                <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span><b>RSI</b></span>
                                        <span style="color: {rsi_color}; font-weight: bold;">{rsi_value:.1f}</span>
                                    </div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                                # Tendencia con color
                                trend = asset_row["Tendencia"]
                                trend_color = (
                                    "#388e3c"
                                    if trend == "ALCISTA"
                                    else "#d32f2f" if trend == "BAJISTA" else "#757575"
                                )
                                st.markdown(
                                    f"""
                                <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span><b>Tendencia</b></span>
                                        <span style="color: {trend_color}; font-weight: bold;">{trend}</span>
                                    </div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                                # Fuerza con color
                                strength = asset_row["Fuerza"]
                                strength_color = (
                                    "#388e3c"
                                    if strength == "fuerte"
                                    else (
                                        "#f57c00"
                                        if strength == "moderada"
                                        else "#757575"
                                    )
                                )
                                st.markdown(
                                    f"""
                                <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span><b>Fuerza</b></span>
                                        <span style="color: {strength_color}; font-weight: bold;">{strength}</span>
                                    </div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                                # Setup
                                st.markdown(
                                    f"""
                                <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span><b>Setup</b></span>
                                        <span style="font-weight: bold;">{asset_row['Setup']}</span>
                                    </div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                        # Pestaña de Análisis Técnico
                        with analysis_tabs[1]:
                            # Análisis Técnico
                            if "Análisis_Técnico" in asset_row and pd.notna(
                                asset_row["Análisis_Técnico"]
                            ):
                                st.markdown("### 📊 Análisis Técnico Detallado")
                                st.markdown(asset_row["Análisis_Técnico"])

                                # Indicadores
                                if (
                                    "Indicadores_Alcistas" in asset_row
                                    and "Indicadores_Bajistas" in asset_row
                                ):
                                    st.markdown("#### Indicadores")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown(f"**Indicadores Alcistas:**")
                                        st.markdown(asset_row["Indicadores_Alcistas"])
                                    with col2:
                                        st.markdown(f"**Indicadores Bajistas:**")
                                        st.markdown(asset_row["Indicadores_Bajistas"])

                                # Soportes y Resistencias
                                if "Soporte" in asset_row or "Resistencia" in asset_row:
                                    st.markdown("#### 📏 Soportes y Resistencias")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if "Soporte" in asset_row and pd.notna(
                                            asset_row["Soporte"]
                                        ):
                                            st.metric(
                                                "Soporte",
                                                f"${asset_row['Soporte']:.2f}",
                                            )
                                    with col2:
                                        if "Resistencia" in asset_row and pd.notna(
                                            asset_row["Resistencia"]
                                        ):
                                            st.metric(
                                                "Resistencia",
                                                f"${asset_row['Resistencia']:.2f}",
                                            )
                            else:
                                st.info(
                                    "No hay análisis técnico detallado disponible para este activo."
                                )

                        # Pestaña de Opciones
                        with analysis_tabs[2]:
                            st.markdown("### 🎯 Análisis de Opciones")
                            if "Volatilidad" in asset_row and pd.notna(
                                asset_row["Volatilidad"]
                            ):
                                st.markdown("#### Datos de Volatilidad")
                                st.metric(
                                    "Volatilidad Implícita",
                                    f"{asset_row['Volatilidad']:.2f}%",
                                )

                                if "Options_Signal" in asset_row and pd.notna(
                                    asset_row["Options_Signal"]
                                ):
                                    signal_color = (
                                        "green"
                                        if asset_row["Options_Signal"] == "CALL"
                                        else "red"
                                    )
                                    st.markdown(
                                        f"**Señal de Opciones:** <span style='color:{signal_color};'>{asset_row['Options_Signal']}</span>",
                                        unsafe_allow_html=True,
                                    )

                                # Información adicional de opciones si está disponible
                                if "Options_Analysis" in asset_row and pd.notna(
                                    asset_row["Options_Analysis"]
                                ):
                                    st.markdown("#### Análisis de Opciones")
                                    st.markdown(asset_row["Options_Analysis"])
                            else:
                                st.info(
                                    "No hay datos de opciones disponibles para este activo."
                                )

                        # Pestaña de Multi-Timeframe
                        with analysis_tabs[3]:
                            st.markdown("### ⚙️ Análisis Multi-Timeframe")
                            if "MTF_Analysis" in asset_row and pd.notna(
                                asset_row["MTF_Analysis"]
                            ):
                                st.markdown(asset_row["MTF_Analysis"])

                                # Tendencias por timeframe si están disponibles
                                timeframes = ["Diario", "Semanal", "Mensual"]
                                cols = st.columns(len(timeframes))
                                for i, tf in enumerate(timeframes):
                                    tf_key = f"Tendencia_{tf}"
                                    if tf_key in asset_row and pd.notna(
                                        asset_row[tf_key]
                                    ):
                                        color = (
                                            "green"
                                            if asset_row[tf_key] == "ALCISTA"
                                            else (
                                                "red"
                                                if asset_row[tf_key] == "BAJISTA"
                                                else "gray"
                                            )
                                        )
                                        with cols[i]:
                                            st.markdown(
                                                f"**{tf}:** <span style='color:{color};'>{asset_row[tf_key]}</span>",
                                                unsafe_allow_html=True,
                                            )
                            else:
                                st.info(
                                    "No hay análisis multi-timeframe disponible para este activo."
                                )

                        # Pestaña de Análisis Experto
                        with analysis_tabs[4]:
                            st.markdown("### 🧠 Análisis Experto")
                            if "Análisis_Experto" in asset_row and pd.notna(
                                asset_row["Análisis_Experto"]
                            ):
                                st.markdown(asset_row["Análisis_Experto"])

                                # Recomendaciones si están disponibles
                                if "Recomendación" in asset_row and pd.notna(
                                    asset_row["Recomendación"]
                                ):
                                    rec_color = (
                                        "green"
                                        if asset_row["Recomendación"]
                                        in ["COMPRAR", "FUERTE COMPRA"]
                                        else (
                                            "red"
                                            if asset_row["Recomendación"]
                                            in ["VENDER", "FUERTE VENTA"]
                                            else "gray"
                                        )
                                    )
                                    st.markdown(
                                        f"**Recomendación:** <span style='color:{rec_color};'>{asset_row['Recomendación']}</span>",
                                        unsafe_allow_html=True,
                                    )
                            else:
                                st.info(
                                    "No hay análisis experto disponible para este activo."
                                )

                        # Pestaña de Noticias y Sentimiento
                        with analysis_tabs[5]:
                            st.markdown("### 📰 Noticias y Sentimiento")

                            # Sentimiento
                            if (
                                "Sentimiento" in asset_row
                                and pd.notna(asset_row["Sentimiento"])
                                and asset_row["Sentimiento"] != "neutral"
                            ):
                                st.markdown("#### 🧠 Sentimiento de Mercado")
                                sentiment_color = (
                                    "green"
                                    if asset_row["Sentimiento"] == "positivo"
                                    else "red"
                                )
                                sentiment_score = (
                                    asset_row.get("Sentimiento_Score", 0.5) * 100
                                )
                                st.markdown(
                                    f"**Sentimiento:** <span style='color:{sentiment_color};'>{asset_row['Sentimiento'].upper()}</span> ({sentiment_score:.1f}%)",
                                    unsafe_allow_html=True,
                                )

                            # Noticias
                            if "Última_Noticia" in asset_row and pd.notna(
                                asset_row["Última_Noticia"]
                            ):
                                st.markdown("#### 📰 Últimas Noticias")
                                st.markdown(f"**{asset_row['Última_Noticia']}**")
                                if "Fuente_Noticia" in asset_row:
                                    st.caption(f"Fuente: {asset_row['Fuente_Noticia']}")

                                # Más noticias si están disponibles
                                if "Noticias_Adicionales" in asset_row and pd.notna(
                                    asset_row["Noticias_Adicionales"]
                                ):
                                    st.markdown("#### Más Noticias")
                                    st.markdown(asset_row["Noticias_Adicionales"])
                            else:
                                st.info(
                                    "No hay noticias o datos de sentimiento disponibles para este activo."
                                )
                else:
                    # Mensaje mejorado cuando no hay oportunidades de alta confianza
                    st.markdown(
                        f"""
                    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #2196f3; text-align: center;">
                        <h4 style="margin-top:0; color: #2196f3;">ℹ️ Información</h4>
                        <p style="margin:0;">No se encontraron oportunidades de alta confianza en el sector <b>{selected_sector}</b>.</p>
                        <p style="margin-top:10px;">Puedes revisar la tabla condensada para ver todas las oportunidades disponibles en este sector.</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # Actualización
        st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
