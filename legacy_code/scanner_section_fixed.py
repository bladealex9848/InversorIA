# Pestaña de Scanner de Mercado
with main_tab2:
    st.markdown("## 🔍 Scanner de Mercado")
    
    # Usar la función mejorada de display_opportunities
    from market_scanner import display_opportunities
    
    # Verificar si el scanner está disponible
    if st.session_state.scanner is not None:
        # Mostrar el scanner mejorado
        display_opportunities(st.session_state.scanner)
        
        # Guardar señales en la base de datos cuando hay resultados
        if "scan_results" in st.session_state and not st.session_state.scan_results.empty:
            # Botón para guardar señales en la base de datos
            if st.button("Guardar Señales en Base de Datos", type="primary"):
                # Inicializar gestor de señales si no existe
                if "signal_manager" not in locals():
                    signal_manager = SignalManager()
                    
                with st.spinner("Guardando señales en la base de datos..."):
                    signals_saved = 0
                    for _, row in st.session_state.scan_results.iterrows():
                        try:
                            # Mapear dirección
                            direction = (
                                "CALL"
                                if row["Estrategia"] == "CALL"
                                else (
                                    "PUT"
                                    if row["Estrategia"] == "PUT"
                                    else "NEUTRAL"
                                )
                            )

                            # Mapear confianza
                            confidence = (
                                row["Confianza"].capitalize()
                                if isinstance(row["Confianza"], str)
                                else "Media"
                            )
                            if confidence == "Alta" or confidence == "ALTA":
                                confidence = "Alta"
                            elif (
                                confidence == "Media"
                                or confidence == "MEDIA"
                            ):
                                confidence = "Media"
                            else:
                                confidence = "Baja"

                            # Crear señal
                            signal = {
                                "symbol": row["Symbol"],
                                "price": (
                                    row["Precio"]
                                    if isinstance(
                                        row["Precio"], (int, float)
                                    )
                                    else 0.0
                                ),
                                "direction": direction,
                                "confidence_level": confidence,
                                "timeframe": "Medio Plazo",
                                "strategy": (
                                    row["Setup"]
                                    if "Setup" in row
                                    else "Análisis Técnico"
                                ),
                                "category": row["Sector"],
                                "analysis": f"Señal {direction} con confianza {confidence}. RSI: {row.get('RSI', 'N/A')}. R/R: {row.get('R/R', 'N/A')}",
                                "created_at": datetime.now(),
                            }
                            
                            # Añadir información adicional si está disponible
                            if "Trading_Specialist" in row and row["Trading_Specialist"] != "NEUTRAL":
                                signal["analysis"] += f" Trading Specialist: {row['Trading_Specialist']}"
                            
                            if "Sentimiento" in row and row["Sentimiento"] != "neutral":
                                signal["analysis"] += f" Sentimiento: {row['Sentimiento']}"

                            # Verificar si la señal ya existe en la base de datos
                            existing_signals = signal_manager.db_manager.execute_query(
                                "SELECT id FROM trading_signals WHERE symbol = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)",
                                [signal["symbol"]],
                            )

                            if not existing_signals:
                                # Guardar señal en la base de datos
                                signal_manager.db_manager.save_signal(
                                    signal
                                )
                                signals_saved += 1
                        except Exception as e:
                            logger.error(
                                f"Error guardando señal en la base de datos: {str(e)}"
                            )

                    if signals_saved > 0:
                        st.success(
                            f"Se guardaron {signals_saved} señales en la base de datos"
                        )
                    else:
                        st.info("No se guardaron nuevas señales en la base de datos")
    else:
        st.error(
            "El scanner de mercado no está disponible. Verifique la importación desde market_scanner.py"
        )
        st.session_state.scan_results = pd.DataFrame()
    
    # Sección de información
    with st.expander("ℹ️ Acerca del Scanner"):
        st.markdown(
            """
            ### Algoritmo de Scanner

            El scanner de mercado de InversorIA Pro utiliza un enfoque multifactorial que evalúa:

            - **Análisis técnico**: Medias móviles, RSI, MACD, patrones de velas y tendencias
            - **Opciones**: Flujo de opciones, volatilidad implícita y superficie de volatilidad
            - **Niveles clave**: Soportes, resistencias y zonas de interés

            Cada oportunidad es calificada con un nivel de confianza basado en la alineación de factores y la calidad de la configuración.

            ### Interpretación de las Señales

            - **Alta Confianza**: Fuerte alineación de múltiples factores
            - **Media Confianza**: Buena configuración con algunos factores contradictorios
            - **Baja Confianza**: Configuración básica que requiere más análisis

            El ratio R/R (Riesgo/Recompensa) se calcula automáticamente basado en niveles técnicos y volatilidad del activo.
            """
        )
