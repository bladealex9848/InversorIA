"""
InversorIA Pro - Gestor de Señales de Trading
--------------------------------------------
Este archivo contiene clases y funciones para gestionar las señales de trading.
"""

import logging
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Importar componentes personalizados
try:
    from database_utils import DatabaseManager
    from signal_analyzer import RealTimeSignalAnalyzer
except Exception as e:
    logging.error(f"Error importando componentes: {str(e)}")

logger = logging.getLogger(__name__)

class SignalManager:
    """Gestiona las señales de trading y su procesamiento"""

    def __init__(self):
        """Inicializa el gestor de señales"""
        self.db_manager = DatabaseManager()
        self.real_time_analyzer = RealTimeSignalAnalyzer()

    def get_active_signals(
        self, days_back=7, categories=None, confidence_levels=None, force_realtime=False, refresh=False
    ):
        """Obtiene las señales activas filtradas"""
        # Verificar si hay señales en caché de sesión y no se fuerza actualización
        if (
            "cached_signals" in st.session_state
            and st.session_state.cached_signals
            and not force_realtime
            and not refresh
        ):
            logger.info(
                f"Usando {len(st.session_state.cached_signals)} señales desde la caché de sesión"
            )
            
            # Filtrar señales por categoría y nivel de confianza
            filtered_signals = st.session_state.cached_signals
            
            if categories and "Todas" not in categories:
                if isinstance(categories, str):
                    categories = [categories]
                filtered_signals = [
                    signal for signal in filtered_signals
                    if signal.get("category") in categories
                ]
            
            if confidence_levels and len(confidence_levels) > 0:
                filtered_signals = [
                    signal for signal in filtered_signals
                    if signal.get("confidence_level") in confidence_levels
                ]
            
            # Filtrar por fecha
            if days_back > 0:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                filtered_signals = [
                    signal for signal in filtered_signals
                    if isinstance(signal.get("created_at"), datetime) and signal.get("created_at") >= cutoff_date
                ]
            
            logger.info(f"Se filtraron {len(filtered_signals)} señales de la caché")
            return filtered_signals

        # Si no hay señales en caché o se fuerza actualización, intentar obtener de la base de datos
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
        
        # Determinar sector para escanear
        sector = "Todas"
        if categories and "Todas" not in categories:
            if isinstance(categories, str):
                sector = categories
            elif len(categories) == 1:
                sector = categories[0]
        
        # Determinar nivel de confianza
        confidence = "Media"
        if confidence_levels and len(confidence_levels) == 1:
            confidence = confidence_levels[0]
        
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
        """Obtiene noticias relevantes del mercado"""
        return self.real_time_analyzer.get_market_news()
    
    def get_detailed_analysis(self, symbol):
        """Obtiene análisis detallado para un símbolo específico"""
        # Primero intentar obtener desde la base de datos
        analysis_data = self.db_manager.get_detailed_analysis(symbol)

        if analysis_data and len(analysis_data) > 0:
            logger.info(
                f"Se obtuvo análisis detallado para {symbol} desde la base de datos"
            )
            return analysis_data[0]

        # Si no hay datos en la base de datos, generar análisis en tiempo real
        logger.info(f"Generando análisis detallado para {symbol} en tiempo real")
        return self.real_time_analyzer.get_detailed_analysis(symbol)
    
    def save_signal(self, signal_data):
        """Guarda una nueva señal en la base de datos"""
        return self.db_manager.save_signal(signal_data)
    
    def save_market_sentiment(self, sentiment_data):
        """Guarda datos de sentimiento de mercado en la base de datos"""
        return self.db_manager.save_market_sentiment(sentiment_data)
    
    def save_market_news(self, news_data):
        """Guarda noticias de mercado en la base de datos"""
        return self.db_manager.save_market_news(news_data)
    
    def process_scanner_signals(self, scanner_results):
        """Procesa señales del scanner y las guarda en la base de datos"""
        if scanner_results is None or scanner_results.empty:
            logger.warning("No hay resultados del scanner para procesar")
            return 0
        
        signals_saved = 0
        
        for _, row in scanner_results.iterrows():
            try:
                # Determinar dirección
                direction = "NEUTRAL"
                if row["Estrategia"] == "CALL":
                    direction = "CALL"
                elif row["Estrategia"] == "PUT":
                    direction = "PUT"
                
                # Determinar nivel de confianza
                confidence = "Media"
                if isinstance(row["Confianza"], str):
                    confidence = row["Confianza"]
                
                # Crear señal
                signal = {
                    "symbol": row["Symbol"],
                    "price": (
                        row["Precio"]
                        if isinstance(row["Precio"], (int, float))
                        else 0.0
                    ),
                    "direction": direction,
                    "confidence_level": confidence,
                    "timeframe": "Medio Plazo",
                    "strategy": (
                        row["Setup"] if "Setup" in row else "Análisis Técnico"
                    ),
                    "category": row["Sector"],
                    "analysis": f"Señal {direction} con confianza {confidence}. RSI: {row.get('RSI', 'N/A')}. R/R: {row.get('R/R', 'N/A')}",
                    "created_at": datetime.now(),
                }
                
                # Verificar si la señal ya existe en la base de datos
                existing_signals = self.db_manager.execute_query(
                    "SELECT id FROM trading_signals WHERE symbol = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)",
                    [signal["symbol"]],
                )
                
                if not existing_signals:
                    # Guardar señal en la base de datos
                    self.db_manager.save_signal(signal)
                    signals_saved += 1
            except Exception as e:
                logger.error(f"Error procesando señal del scanner: {str(e)}")
                continue
        
        return signals_saved
