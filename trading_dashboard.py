import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import traceback

# Constantes
TIMEFRAMES = {
    "Intradía": ["1m", "5m", "15m", "30m", "1h"],
    "Swing": ["1d", "1wk"],
    "Posicional": ["1mo", "3mo"],
}


def create_advanced_chart(data, timeframe="diario"):
    """Crea gráfico técnico avanzado con análisis institucional"""
    try:
        if data is None or len(data) < 2:
            st.warning(
                f"Datos insuficientes para crear gráfico: {len(data) if data is not None else 0} registros"
            )
            return None

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=(f"Análisis Técnico ({timeframe})", "MACD & RSI", "Volumen"),
        )

        # Panel Principal: OHLC y Bandas de Bollinger
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data["Open"],
                high=data["High"],
                low=data["Low"],
                close=data["Close"],
                name="OHLC",
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350",
            ),
            row=1,
            col=1,
        )

        # Bollinger Bands
        for band, name, color in [
            ("BB_High", "BB Superior", "rgba(173, 204, 255, 0.3)"),
            ("BB_Mid", "BB Media", "rgba(173, 204, 255, 0.6)"),
            ("BB_Low", "BB Inferior", "rgba(173, 204, 255, 0.3)"),
        ]:
            if band in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[band],
                        name=name,
                        line=dict(color=color, width=1),
                        fill="tonexty" if band == "BB_Low" else None,
                    ),
                    row=1,
                    col=1,
                )

        # Medias Móviles
        for ma, color, width in [
            ("SMA_20", "#2196f3", 1.5),  # Azul
            ("SMA_50", "#ff9800", 1.5),  # Naranja
            ("SMA_200", "#f44336", 1.5),  # Rojo
        ]:
            if ma in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data[ma],
                        name=f"{ma}",
                        line=dict(color=color, width=width),
                    ),
                    row=1,
                    col=1,
                )

        # Panel MACD y RSI
        if all(x in data.columns for x in ["MACD", "MACD_Signal"]):
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["MACD"],
                    name="MACD",
                    line=dict(color="#2196f3", width=1.5),
                ),
                row=2,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["MACD_Signal"],
                    name="Señal",
                    line=dict(color="#ff9800", width=1.5),
                ),
                row=2,
                col=1,
            )

        # Añadir RSI
        if "RSI" in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["RSI"],
                    name="RSI",
                    line=dict(color="#9c27b0", width=1.5),
                ),
                row=2,
                col=1,
            )

            # Líneas de referencia RSI
            for level in [30, 70]:
                fig.add_shape(
                    type="line",
                    x0=data.index[0],
                    x1=data.index[-1],
                    y0=level,
                    y1=level,
                    line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dash"),
                    row=2,
                    col=1,
                )

        # Panel de Volumen
        if "Volume" in data.columns:
            volume_colors = np.where(
                data["Close"] >= data["Open"],
                "rgba(38, 166, 154, 0.5)",  # Verde para velas alcistas
                "rgba(239, 83, 80, 0.5)",  # Rojo para velas bajistas
            )
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data["Volume"],
                    name="Volumen",
                    marker_color=volume_colors,
                ),
                row=3,
                col=1,
            )

        # Layout profesional
        fig.update_layout(
            height=600,
            template="plotly_dark",
            showlegend=True,
            xaxis_rangeslider_visible=False,
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        return fig

    except Exception as e:
        st.error(f"Error en visualización: {str(e)}")
        return None


def render_technical_metrics(df_technical):
    """Renderiza métricas técnicas resumidas"""
    try:
        if df_technical is None or len(df_technical) < 2:
            st.warning("Datos insuficientes para calcular métricas técnicas")
            return

        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            price_change = (
                (df_technical["Close"].iloc[-1] / df_technical["Close"].iloc[-2]) - 1
            ) * 100
            st.metric(
                "Precio",
                f"${df_technical['Close'].iloc[-1]:.2f}",
                f"{price_change:.2f}%",
                delta_color="normal" if price_change >= 0 else "inverse",
            )

        with col2:
            if "RSI" in df_technical.columns:
                rsi_value = df_technical["RSI"].iloc[-1]
                rsi_status = (
                    "Sobrecomprado"
                    if rsi_value > 70
                    else "Sobrevendido" if rsi_value < 30 else "Neutral"
                )
                st.metric("RSI", f"{rsi_value:.1f}", rsi_status)
            else:
                st.metric("RSI", "N/A", "No disponible")

        with col3:
            if "Volume" in df_technical.columns and df_technical["Volume"].mean() > 0:
                vol_ratio = (
                    df_technical["Volume"].iloc[-1] / df_technical["Volume"].mean()
                )
                st.metric(
                    "Vol Ratio",
                    f"{vol_ratio:.2f}x",
                    f"{(vol_ratio-1)*100:.1f}% vs Media",
                )
            else:
                st.metric("Vol Ratio", "N/A", "No disponible")

        with col4:
            if (
                "BB_Width" in df_technical.columns
                and df_technical["BB_Width"].mean() > 0
            ):
                bb_width = df_technical["BB_Width"].iloc[-1]
                bb_avg = df_technical["BB_Width"].mean()
                st.metric(
                    "Volatilidad",
                    f"{bb_width:.3f}",
                    f"{(bb_width/bb_avg-1)*100:.1f}% vs Media",
                )
            else:
                st.metric("Volatilidad", "N/A", "No disponible")

    except Exception as e:
        st.warning(f"Error calculando métricas: {str(e)}")


def render_signal_summary(signals, vix_level=None):
    """Renderiza resumen de señales de trading"""
    try:
        if not signals:
            st.warning("No hay señales disponibles")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Señal general
            if "overall" in signals:
                overall = signals["overall"]
                signal = overall["signal"]
                confidence = overall["confidence"]

                # Determinar color y emoji
                if signal in ["compra", "compra_fuerte"]:
                    signal_color = "green"
                    emoji = "🟢"
                elif signal in ["venta", "venta_fuerte"]:
                    signal_color = "red"
                    emoji = "🔴"
                else:
                    signal_color = "gray"
                    emoji = "⚪"

                st.markdown(
                    f"### Señal General: <span style='color:{signal_color}'>{signal.upper()} {emoji}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Confianza:** {confidence.capitalize()}")

                if "score" in overall:
                    st.markdown(f"**Score:** {overall['score']}")

        with col2:
            # Opciones
            if "options" in signals:
                options = signals["options"]
                direction = options["direction"]
                strategy = options["strategy"]

                # Determinar color para opciones
                if direction == "CALL":
                    option_color = "green"
                    option_emoji = "📈"
                elif direction == "PUT":
                    option_color = "red"
                    option_emoji = "📉"
                else:
                    option_color = "gray"
                    option_emoji = "⚖️"

                st.markdown(
                    f"### Opciones: <span style='color:{option_color}'>{direction} {option_emoji}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Estrategia:** {strategy}")
                st.markdown(f"**Timeframe:** {options.get('timeframe', 'N/A')}")

        # Añadir contexto de VIX si está disponible
        if vix_level:
            vix_status = (
                "ALTA" if vix_level > 25 else "BAJA" if vix_level < 15 else "NORMAL"
            )
            vix_color = (
                "red" if vix_level > 25 else "green" if vix_level < 15 else "gray"
            )
            st.markdown(
                f"**VIX:** <span style='color:{vix_color}'>{vix_level:.2f} ({vix_status})</span>",
                unsafe_allow_html=True,
            )

    except Exception as e:
        st.warning(f"Error mostrando señales: {str(e)}")


def render_timeframe_analysis(multi_tf_analysis):
    """Renderiza análisis por timeframe"""
    try:
        if not multi_tf_analysis or "error" in multi_tf_analysis:
            st.warning("No hay análisis multi-timeframe disponible")
            return

        st.markdown("### Análisis Multi-Timeframe")

        # Crear tabla para mostrar análisis por timeframe
        data = []

        # Primero procesar el análisis consolidado
        if "consolidated" in multi_tf_analysis:
            cons = multi_tf_analysis["consolidated"]
            data.append(
                {
                    "Timeframe": "CONSOLIDADO",
                    "Señal": cons["signal"].upper(),
                    "Confianza": cons["confidence"].upper(),
                    "Opciones": cons.get("options_recommendation", "N/A"),
                }
            )

        # Luego procesar cada timeframe individual
        for tf, analysis in multi_tf_analysis.items():
            if (
                tf != "consolidated"
                and isinstance(analysis, dict)
                and "overall" in analysis
            ):
                data.append(
                    {
                        "Timeframe": tf,
                        "Señal": analysis["overall"]["signal"].upper(),
                        "Confianza": analysis["overall"]["confidence"].upper(),
                        "Opciones": (
                            analysis["options"]["direction"]
                            if "options" in analysis
                            else "N/A"
                        ),
                    }
                )

        # Crear dataframe
        if data:
            df = pd.DataFrame(data)

            # Aplicar estilo condicional
            def highlight_signal(val):
                if "COMPRA" in val:
                    return "background-color: rgba(38, 166, 154, 0.2)"
                elif "VENTA" in val:
                    return "background-color: rgba(239, 83, 80, 0.2)"
                return ""

            st.dataframe(
                df.style.applymap(highlight_signal, subset=["Señal", "Opciones"])
            )

            # Mostrar recomendación derivada del análisis multi-timeframe
            if "consolidated" in multi_tf_analysis:
                cons = multi_tf_analysis["consolidated"]
                direction = cons.get("options_recommendation", "NEUTRAL")

                if direction == "CALL":
                    st.success(
                        "✅ RECOMENDACIÓN: Considerar estrategia CALL basada en alineación de timeframes"
                    )
                elif direction == "PUT":
                    st.error(
                        "⛔ RECOMENDACIÓN: Considerar estrategia PUT basada en alineación de timeframes"
                    )
                else:
                    st.info(
                        "ℹ️ RECOMENDACIÓN: Mantener posición neutral, señales mixtas entre timeframes"
                    )
        else:
            st.info("No hay datos suficientes para análisis multi-timeframe")

    except Exception as e:
        st.warning(f"Error mostrando análisis multi-timeframe: {str(e)}")


def render_support_resistance(levels, current_price=None):
    """Renderiza niveles clave de soporte y resistencia"""
    try:
        if not levels or (not levels.get("supports") and not levels.get("resistances")):
            st.info("No hay niveles de soporte/resistencia disponibles")
            return

        st.markdown("### Niveles Clave")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Resistencias")
            if levels.get("resistances"):
                for i, level in enumerate(sorted(levels["resistances"])):
                    distance = (
                        ((level / current_price) - 1) * 100 if current_price else 0
                    )
                    st.markdown(f"R{i+1}: ${level:.2f} ({distance:+.2f}%)")
            else:
                st.info("No hay resistencias identificadas")

        with col2:
            st.markdown("#### Soportes")
            if levels.get("supports"):
                for i, level in enumerate(sorted(levels["supports"], reverse=True)):
                    distance = (
                        ((level / current_price) - 1) * 100 if current_price else 0
                    )
                    st.markdown(f"S{i+1}: ${level:.2f} ({distance:+.2f}%)")
            else:
                st.info("No hay soportes identificados")

        # Añadir niveles Fibonacci si están disponibles
        if levels.get("fibonacci"):
            st.markdown("#### Niveles Fibonacci")
            fib_levels = []
            for fib, level in levels["fibonacci"].items():
                distance = ((level / current_price) - 1) * 100 if current_price else 0
                fib_levels.append(
                    (
                        float(fib) if fib.replace(".", "").isdigit() else 0,
                        fib,
                        level,
                        distance,
                    )
                )

            # Ordenar y mostrar
            for _, fib, level, distance in sorted(fib_levels):
                st.markdown(f"Fib {fib}: ${level:.2f} ({distance:+.2f}%)")

    except Exception as e:
        st.warning(f"Error mostrando niveles: {str(e)}")


def render_option_recommendations(signals, symbol, options_params, vix_level=None):
    """Renderiza recomendaciones concretas para opciones"""
    try:
        if not signals or "options" not in signals:
            st.warning("No hay señales de opciones disponibles")
            return

        options = signals["options"]
        direction = options["direction"]

        # Solo mostrar recomendaciones si hay una dirección clara
        if direction == "NEUTRAL":
            st.info(
                "⚠️ No se recomienda operar opciones en este momento debido a señales mixtas"
            )
            return

        st.markdown(f"### Recomendación de Opciones {direction}")

        # Mostrar detalles de la estrategia
        strategy = options["strategy"]
        confidence = options["confidence"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Estrategia:** {strategy}")
            st.markdown(f"**Confianza:** {confidence}")
            st.markdown(f"**Dirección:** {direction}")

        with col2:
            # Mostrar parámetros específicos
            if options_params:
                st.markdown("#### Parámetros")
                for param, value in options_params.items():
                    st.markdown(f"**{param}:** {value}")

        # Ajustes por volatilidad
        if vix_level:
            st.markdown("#### Ajustes por Volatilidad")
            if vix_level > 25:
                st.markdown("🔴 **Alta volatilidad** - Considerar:")
                st.markdown("- Reducir tamaño de posición")
                st.markdown("- Usar spreads en lugar de opciones directas")
                st.markdown("- Strike más alejado del precio actual")
            elif vix_level < 15:
                st.markdown("🟢 **Baja volatilidad** - Considerar:")
                st.markdown("- Strike más cercano al precio actual")
                st.markdown("- Opciones directas preferibles a spreads")
                st.markdown("- Mayor duración en la estrategia")
            else:
                st.markdown("⚪ **Volatilidad normal** - Parámetros estándar")

        # Ejemplo concreto de trading
        st.markdown("#### Ejemplo de Trade")
        st.markdown(f"- **Activo:** {symbol}")
        st.markdown(f"- **Tipo:** {direction}")
        st.markdown(f"- **Estrategia:** {strategy}")
        st.markdown(
            f"- **Distancia Strike:** {options_params.get('distance_spot_strike', 'N/A')}"
        )
        st.markdown(f"- **Volumen Mínimo:** {options_params.get('volumen_min', 'N/A')}")

    except Exception as e:
        st.warning(f"Error mostrando recomendaciones: {str(e)}")


def render_dashboard(symbol, timeframe, data=None, context=None):
    """Renderiza dashboard completo con análisis técnico"""
    try:
        from market_utils import (
            fetch_market_data,
            TechnicalAnalyzer,
            get_market_context,
        )

        # Si no se proporcionan datos o contexto, obtenerlos
        if data is None:
            data = fetch_market_data(symbol, "6mo", timeframe)

        if context is None:
            context = get_market_context(symbol)

        # Mostrar gráfico principal
        with st.container():
            st.subheader(f"Análisis Técnico: {symbol}")

            if data is not None and not data.empty:
                # Crear el analizador
                analyzer = TechnicalAnalyzer(data)
                df_technical = analyzer.calculate_indicators()

                # Mostrar gráfico si hay datos suficientes
                if df_technical is not None and len(df_technical) >= 20:
                    fig = create_advanced_chart(df_technical, timeframe)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                    # Mostrar métricas clave
                    render_technical_metrics(df_technical)
                else:
                    st.warning(f"Datos insuficientes para análisis técnico de {symbol}")
            else:
                st.error(f"No se pudieron obtener datos para {symbol}")

        # Mostrar señales y recomendaciones si hay contexto
        if context and "error" not in context:
            with st.container():
                st.markdown("---")

                # Resumen de señales
                st.subheader("📊 Resumen de Señales")
                if "signals" in context:
                    render_signal_summary(context["signals"], context.get("vix_level"))

                # Análisis multi-timeframe
                st.markdown("---")
                st.subheader("⏱️ Análisis por Timeframe")
                if "multi_timeframe" in context:
                    render_timeframe_analysis(context["multi_timeframe"])

                # Niveles clave
                st.markdown("---")
                st.subheader("🎯 Niveles y Zonas Clave")
                if "support_resistance" in context:
                    render_support_resistance(
                        context["support_resistance"], context.get("last_price")
                    )

                # Recomendación de opciones
                st.markdown("---")
                st.subheader("💰 Trading de Opciones")
                if "signals" in context and "options_params" in context:
                    render_option_recommendations(
                        context["signals"],
                        symbol,
                        context["options_params"],
                        context.get("vix_level"),
                    )
        else:
            error_msg = (
                context.get("error", "Error desconocido")
                if context
                else "No hay contexto disponible"
            )
            st.error(f"Error obteniendo análisis: {error_msg}")

    except Exception as e:
        st.error(f"Error renderizando dashboard: {str(e)}")


def render_technical_tab(symbol, timeframe):
    """Renderiza pestaña de análisis técnico"""
    render_dashboard(symbol, timeframe)


def render_options_tab(symbol):
    """Renderiza pestaña de análisis de opciones"""
    from market_utils import get_market_context

    context = get_market_context(symbol)
    if context and "error" not in context:
        render_option_recommendations(
            context["signals"],
            symbol,
            context["options_params"],
            context.get("vix_level"),
        )
    else:
        st.error("No se pudo obtener información de opciones")


def render_multiframe_tab(symbol):
    """Renderiza pestaña de análisis multi-timeframe"""
    from market_utils import get_market_context

    context = get_market_context(symbol)
    if context and "error" not in context and "multi_timeframe" in context:
        render_timeframe_analysis(context["multi_timeframe"])
    else:
        st.error("No se pudo obtener análisis multi-timeframe")


def render_fundamental_tab():
    """Renderiza pestaña de análisis fundamental"""
    st.info("Análisis fundamental no disponible en esta versión")


def render_report_tab():
    """Renderiza pestaña de reporte ejecutivo"""
    st.info("Reportes ejecutivos no disponibles en esta versión")


def render_risk_tab():
    """Renderiza pestaña de gestión de riesgo"""
    st.info("Análisis de riesgo no disponible en esta versión")
