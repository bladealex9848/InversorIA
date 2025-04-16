"""
InversorIA Pro - Analizador de Señales en Tiempo Real
----------------------------------------------------
Este archivo contiene clases y funciones para analizar el mercado en tiempo real
y generar señales de trading.
"""

import logging
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Importar componentes personalizados
try:
    from market_utils import (
        fetch_market_data,
        get_market_context,
        get_vix_level,
    )
except Exception as e:
    logging.error(f"Error importando market_utils: {str(e)}")

# Importar datos de empresas
try:
    from company_data import COMPANY_INFO
except Exception as e:
    logging.error(f"Error importando company_data: {str(e)}")
    COMPANY_INFO = {}

logger = logging.getLogger(__name__)

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
        self.company_info = COMPANY_INFO
        self.import_success = True

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
            if "scanner" in st.session_state and st.session_state.scanner is not None:
                market_scanner = st.session_state.scanner
                logger.info("Usando market_scanner existente desde session_state")

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
                            # Intentar usar el método scan_market del market_scanner
                            try:
                                scan_result = market_scanner.scan_market(
                                    [current_sector]
                                )
                                if not scan_result.empty:
                                    # Filtrar por símbolo
                                    symbol_result = scan_result[
                                        scan_result["Symbol"] == symbol
                                    ]
                                    if not symbol_result.empty:
                                        # Mapear el formato del market_scanner al formato de señal
                                        row = symbol_result.iloc[0]
                                        direction = (
                                            "CALL"
                                            if row["Estrategia"] == "CALL"
                                            else (
                                                "PUT"
                                                if row["Estrategia"] == "PUT"
                                                else "NEUTRAL"
                                            )
                                        )
                                        confidence = row["Confianza"]
                                        price = row["Precio"]
                                        strategy = row["Setup"]
                                        timeframe = "Medio Plazo"
                                        analysis = f"Señal {direction} con confianza {confidence}. {strategy}."

                                        # Crear señal
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
                                        }

                                        # Añadir a la lista de señales
                                        all_signals.append(signal)
                                        continue
                            except Exception as scanner_error:
                                logger.warning(
                                    f"Error usando market_scanner.scan_market: {str(scanner_error)}"
                                )

                        # Si no se pudo usar el market_scanner, usar get_market_context
                        try:
                            # Obtener contexto de mercado
                            context = get_market_context(symbol)
                            if not context or "error" in context:
                                continue

                            # Extraer datos clave
                            price = context.get("last_price", 0)
                            change = context.get("change_percent", 0)
                            signals = context.get("signals", {})

                            # Obtener señal general
                            overall_signal = "NEUTRAL"
                            confidence = "Media"
                            if "overall" in signals:
                                signal = signals["overall"]["signal"]
                                confidence = signals["overall"]["confidence"]
                                if signal in ["compra", "compra_fuerte"]:
                                    overall_signal = "CALL"
                                elif signal in ["venta", "venta_fuerte"]:
                                    overall_signal = "PUT"

                            # Filtrar por nivel de confianza
                            if confidence_threshold == "Alta" and confidence != "Alta":
                                continue

                            # Filtrar señales neutras
                            if overall_signal == "NEUTRAL":
                                continue

                            # Crear señal
                            signal = {
                                "symbol": symbol,
                                "price": price,
                                "direction": overall_signal,
                                "confidence_level": confidence,
                                "timeframe": "Medio Plazo",
                                "strategy": "Análisis Técnico",
                                "category": current_sector,
                                "analysis": f"Señal {overall_signal} con confianza {confidence}. RSI: {signals.get('momentum', {}).get('rsi', 'N/A')}.",
                                "created_at": datetime.now(),
                            }

                            # Añadir a la lista de señales
                            all_signals.append(signal)
                        except Exception as context_error:
                            logger.warning(
                                f"Error obteniendo contexto para {symbol}: {str(context_error)}"
                            )
                    except Exception as e:
                        logger.error(f"Error escaneando {symbol}: {str(e)}")
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
        """Genera análisis detallado para un símbolo específico"""
        try:
            # Mostrar mensaje de estado
            status_placeholder = st.empty()
            status_placeholder.info(f"Analizando {symbol} en detalle...")

            # Verificar si hay análisis en caché
            if symbol in self.analysis_cache:
                cached_analysis = self.analysis_cache[symbol]
                # Verificar si el análisis es reciente (menos de 1 hora)
                if (
                    datetime.now() - cached_analysis.get("timestamp", datetime.min)
                ).total_seconds() < 3600:
                    status_placeholder.empty()
                    return cached_analysis

            # Obtener contexto de mercado
            context = get_market_context(symbol)
            if not context or "error" in context:
                status_placeholder.empty()
                return self._create_basic_analysis(symbol)

            # Extraer datos clave
            price = context.get("last_price", 0)
            change = context.get("change_percent", 0)
            signals = context.get("signals", {})

            # Obtener señal general
            overall_signal = "NEUTRAL"
            confidence = "Media"
            if "overall" in signals:
                signal = signals["overall"]["signal"]
                confidence = signals["overall"]["confidence"]
                if signal in ["compra", "compra_fuerte"]:
                    overall_signal = "CALL"
                elif signal in ["venta", "venta_fuerte"]:
                    overall_signal = "PUT"

            # Obtener información de la empresa
            company_info = self.company_info.get(
                symbol,
                {
                    "name": symbol,
                    "sector": "No especificado",
                    "description": f"Activo financiero negociado bajo el símbolo {symbol}",
                },
            )

            # Obtener datos técnicos
            technical_data = {}
            if "momentum" in signals:
                technical_data["rsi"] = signals["momentum"].get("rsi", "N/A")
                technical_data["macd"] = signals["momentum"].get("macd", "N/A")

            if "trend" in signals:
                technical_data["sma20"] = signals["trend"].get("sma20", "N/A")
                technical_data["sma50"] = signals["trend"].get("sma50", "N/A")
                technical_data["sma200"] = signals["trend"].get("sma200", "N/A")

            # Obtener niveles de soporte y resistencia
            support_levels = []
            resistance_levels = []
            if "levels" in signals:
                support_levels = signals["levels"].get("support", [])
                resistance_levels = signals["levels"].get("resistance", [])

            # Obtener patrones de velas
            candle_patterns = []
            if "patterns" in signals:
                candle_patterns = signals["patterns"].get("candles", [])

            # Crear análisis detallado
            detailed_analysis = {
                "symbol": symbol,
                "price": price,
                "change": change,
                "direction": overall_signal,
                "confidence_level": confidence,
                "timeframe": "Medio Plazo",
                "strategy": "Análisis Técnico Avanzado",
                "category": company_info.get("sector", "No especificado"),
                "analysis": f"Señal {overall_signal} con confianza {confidence}. RSI: {technical_data.get('rsi', 'N/A')}.",
                "created_at": datetime.now(),
                "company_info": company_info,
                "indicators": technical_data,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "candle_patterns": candle_patterns,
                "timestamp": datetime.now(),
            }

            # Guardar en caché
            self.analysis_cache[symbol] = detailed_analysis

            # Limpiar mensaje de estado
            status_placeholder.empty()

            return detailed_analysis
        except Exception as e:
            logger.error(f"Error generando análisis detallado para {symbol}: {str(e)}")
            return self._create_basic_analysis(symbol)

    def get_real_time_market_sentiment(self):
        """Obtiene el sentimiento actual del mercado en tiempo real"""
        try:
            # Mostrar mensaje de estado
            status_placeholder = st.empty()
            status_placeholder.info("Analizando sentimiento de mercado...")

            # Inicializar variables
            overall = "Neutral"
            bullish_count = 0
            bearish_count = 0
            volume_status = "Normal"
            sp500_trend = "Neutral"

            # Obtener datos del VIX
            vix_value = "N/A"
            vix_status = "N/A"
            try:
                # Intentar importar get_vix_level desde market_utils
                vix_value = get_vix_level()
                if vix_value:
                    vix_status = vix_value.get("status", "N/A")
            except Exception as vix_error:
                logger.warning(f"Error obteniendo datos del VIX: {str(vix_error)}")

            # Analizar índices principales
            indices = ["SPY", "QQQ", "DIA", "IWM"]
            for index in indices:
                try:
                    context = get_market_context(index)
                    if context and "error" not in context:
                        signals = context.get("signals", {})
                        if "overall" in signals:
                            signal = signals["overall"]["signal"]
                            if signal in ["compra", "compra_fuerte"]:
                                bullish_count += 1
                            elif signal in ["venta", "venta_fuerte"]:
                                bearish_count += 1

                        # Obtener tendencia del S&P 500
                        if index == "SPY":
                            change = context.get("change_percent", 0)
                            if change > 0.5:
                                sp500_trend = "Alcista"
                            elif change < -0.5:
                                sp500_trend = "Bajista"
                            else:
                                sp500_trend = "Neutral"

                            # Obtener volumen
                            volume = context.get("volume", 0)
                            avg_volume = context.get("avg_volume", 0)
                            if avg_volume > 0:
                                volume_ratio = volume / avg_volume
                                if volume_ratio > 1.5:
                                    volume_status = "Alto"
                                elif volume_ratio < 0.5:
                                    volume_status = "Bajo"
                                else:
                                    volume_status = "Normal"
                except Exception as index_error:
                    logger.warning(
                        f"Error analizando índice {index}: {str(index_error)}"
                    )

            # Determinar sentimiento general
            if bullish_count > bearish_count + 1:
                overall = "Alcista"
            elif bearish_count > bullish_count + 1:
                overall = "Bajista"
            else:
                overall = "Neutral"

            # Crear objeto de sentimiento
            sentiment = {
                "date": datetime.now().date(),
                "overall": overall,
                "vix": vix_status,
                "sp500_trend": sp500_trend,
                "technical_indicators": f"Alcistas: {bullish_count}, Bajistas: {bearish_count}",
                "volume": volume_status,
                "notes": f"Análisis generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "created_at": datetime.now(),
            }

            # Limpiar mensaje de estado
            status_placeholder.empty()

            return sentiment
        except Exception as e:
            logger.error(f"Error obteniendo sentimiento de mercado: {str(e)}")
            return {
                "overall": "Neutral",
                "vix": "N/A",
                "sp500_trend": "No disponible",
                "technical_indicators": "No disponible",
                "volume": "No disponible",
                "notes": f"Error generando análisis - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            }

    def get_market_news(self):
        """Obtiene noticias relevantes del mercado en tiempo real"""
        try:
            # Mostrar mensaje de estado
            status_placeholder = st.empty()
            status_placeholder.info("Buscando noticias relevantes...")

            # Intentar obtener noticias desde el market_scanner
            if "scanner" in st.session_state and st.session_state.scanner is not None:
                market_scanner = st.session_state.scanner
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

            # Si no se pudieron obtener noticias desde el scanner, generar noticias básicas
            news_summary = []

            # Analizar índices principales para generar noticias
            indices = ["SPY", "QQQ", "DIA", "IWM"]
            try:
                for index in indices:
                    context = get_market_context(index)
                    if context and "error" not in context:
                        change = context.get("change_percent", 0)
                        price = context.get("last_price", 0)
                        name = self.company_info.get(index, {}).get("name", index)

                        if abs(change) > 1.0:
                            direction = "sube" if change > 0 else "cae"
                            news_summary.append(
                                {
                                    "title": f"{name} {direction} un {abs(change):.2f}%",
                                    "summary": f"El {name} {direction} un {abs(change):.2f}% hasta los ${price:.2f}, impulsado por {'el optimismo de los inversores' if change > 0 else 'las preocupaciones sobre la economía'}.",
                                    "source": "InversorIA Pro",
                                    "date": datetime.now(),
                                }
                            )

                # Si no hay noticias significativas, añadir una noticia genérica
                if not news_summary:
                    # Obtener datos del S&P 500
                    spy_context = get_market_context("SPY")
                    if spy_context and "error" not in spy_context:
                        spy_change = spy_context.get("change_percent", 0)
                        spy_price = spy_context.get("last_price", 0)

                        if abs(spy_change) < 0.3:
                            news_summary.append(
                                {
                                    "title": "Mercados en consolidación",
                                    "summary": f"El S&P 500 se mantiene estable en ${spy_price:.2f} ({spy_change:+.2f}%) mientras los inversores evalúan las condiciones actuales del mercado.",
                                    "source": "InversorIA Pro",
                                    "date": datetime.now(),
                                }
                            )
                        elif spy_change > 0:
                            news_summary.append(
                                {
                                    "title": "Mercados al alza",
                                    "summary": f"El S&P 500 avanza un {spy_change:.2f}% hasta los ${spy_price:.2f}, impulsado por datos económicos positivos y resultados empresariales sólidos.",
                                    "source": "InversorIA Pro",
                                    "date": datetime.now(),
                                }
                            )
                        else:
                            news_summary.append(
                                {
                                    "title": "Mercados a la baja",
                                    "summary": f"El S&P 500 retrocede un {abs(spy_change):.2f}% hasta los ${spy_price:.2f}, presionado por preocupaciones sobre la inflación y posibles subidas de tipos de interés.",
                                    "source": "InversorIA Pro",
                                    "date": datetime.now(),
                                }
                            )
                    else:
                        news_summary.append(
                            {
                                "title": "Mercados en consolidación",
                                "summary": "Los principales índices se mantienen en un rango estrecho mientras los inversores evalúan las condiciones actuales del mercado.",
                                "source": "InversorIA Pro",
                                "date": datetime.now(),
                            }
                        )
            except Exception as news_error:
                logger.warning(f"Error generando noticias básicas: {str(news_error)}")

            # Limpiar mensaje de estado
            status_placeholder.empty()

            return news_summary
        except Exception as e:
            logger.error(f"Error obteniendo noticias: {str(e)}")
            return []

    def _create_basic_analysis(self, symbol):
        """Crea un análisis básico para un símbolo cuando no hay datos disponibles"""
        company_info = self.company_info.get(
            symbol,
            {
                "name": symbol,
                "sector": "No especificado",
                "description": f"Activo financiero negociado bajo el símbolo {symbol}",
            },
        )

        return {
            "symbol": symbol,
            "price": 0,
            "change": 0,
            "direction": "NEUTRAL",
            "confidence_level": "Baja",
            "timeframe": "Medio Plazo",
            "strategy": "Análisis Técnico",
            "category": company_info.get("sector", "No especificado"),
            "analysis": "No hay datos suficientes para generar un análisis detallado.",
            "created_at": datetime.now(),
            "company_info": company_info,
            "indicators": {},
            "support_levels": [],
            "resistance_levels": [],
            "candle_patterns": [],
            "timestamp": datetime.now(),
        }
