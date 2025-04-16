"""
Versión corregida de la función display_opportunities en market_scanner.py
"""

def display_opportunities(scanner):
    """
    Muestra las oportunidades detectadas por el scanner de mercado.
    
    Args:
        scanner (MarketScanner): Instancia del scanner de mercado
    """
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    
    # Ejecutar el scanner si no se ha ejecutado antes
    if not hasattr(scanner, "results") or scanner.results is None:
        st.info("Ejecutando scanner de mercado...")
        scanner.scan_market()
    
    # Obtener resultados
    opportunities = scanner.results
    
    # Guardar resultados en session_state para uso posterior
    st.session_state.scan_results = opportunities
    
    # Verificar si hay resultados
    if opportunities is None or opportunities.empty:
        st.warning("No se encontraron oportunidades en el mercado")
        return
    
    # Mostrar resumen
    st.markdown("## Oportunidades Detectadas")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Oportunidades", len(opportunities))
    with col2:
        total_calls = len(opportunities[opportunities["Estrategia"] == "CALL"])
        st.metric("Setups CALL", total_calls)
    with col3:
        total_puts = len(opportunities[opportunities["Estrategia"] == "PUT"])
        st.metric("Setups PUT", total_puts)
    with col4:
        high_conf = len(opportunities[opportunities["Confianza"] == "ALTA"])
        st.metric("Alta Confianza", high_conf)
    
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
                        if "Análisis_Técnico" in row and pd.notna(row["Análisis_Técnico"]):
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
                        if "Sentimiento" in row and pd.notna(row["Sentimiento"]) and row["Sentimiento"] != "neutral":
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
