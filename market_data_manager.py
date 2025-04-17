#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para gestionar datos de mercado (noticias y sentimiento)
"""

import logging
from datetime import datetime
import re
import json
from database_utils import DatabaseManager

logger = logging.getLogger(__name__)

class MarketDataManager:
    """Clase para gestionar datos de mercado (noticias y sentimiento)"""
    
    def __init__(self, db_manager=None):
        """Inicializa el gestor de datos de mercado"""
        self.db_manager = db_manager if db_manager else DatabaseManager()
    
    def save_news_from_signal(self, signal_data):
        """
        Guarda noticias relevantes de una señal en la tabla market_news
        
        Args:
            signal_data (dict): Datos de la señal
            
        Returns:
            list: IDs de las noticias guardadas
        """
        try:
            news_ids = []
            
            # Verificar si hay noticias en la señal
            if not signal_data.get("latest_news") and not signal_data.get("additional_news"):
                logger.warning(f"No hay noticias para guardar en la señal de {signal_data.get('symbol', '')}")
                return news_ids
            
            # Guardar la noticia principal
            if signal_data.get("latest_news"):
                main_news = {
                    "title": signal_data.get("latest_news", ""),
                    "summary": signal_data.get("analysis", ""),
                    "source": signal_data.get("news_source", ""),
                    "url": "",  # No tenemos URL en la señal
                    "news_date": datetime.now(),
                    "impact": self._determine_news_impact(signal_data)
                }
                
                # Verificar si la noticia ya existe
                existing_news = self.db_manager.execute_query(
                    "SELECT id FROM market_news WHERE title = %s AND DATE(news_date) = CURDATE()",
                    [main_news["title"]]
                )
                
                if not existing_news:
                    news_id = self.db_manager.save_market_news(main_news)
                    if news_id:
                        news_ids.append(news_id)
                        logger.info(f"Noticia principal guardada con ID: {news_id}")
                else:
                    logger.info(f"La noticia principal ya existe con ID: {existing_news[0]['id']}")
            
            # Guardar noticias adicionales
            if signal_data.get("additional_news"):
                # Dividir las noticias adicionales (pueden estar separadas por saltos de línea)
                additional_news_list = signal_data.get("additional_news", "").split("\\n")
                
                for i, news_title in enumerate(additional_news_list):
                    if news_title.strip():
                        add_news = {
                            "title": news_title.strip(),
                            "summary": f"Noticia adicional relacionada con {signal_data.get('symbol', '')}",
                            "source": signal_data.get("news_source", ""),
                            "url": "",
                            "news_date": datetime.now(),
                            "impact": "Medio"  # Impacto medio por defecto para noticias adicionales
                        }
                        
                        # Verificar si la noticia ya existe
                        existing_news = self.db_manager.execute_query(
                            "SELECT id FROM market_news WHERE title = %s AND DATE(news_date) = CURDATE()",
                            [add_news["title"]]
                        )
                        
                        if not existing_news:
                            news_id = self.db_manager.save_market_news(add_news)
                            if news_id:
                                news_ids.append(news_id)
                                logger.info(f"Noticia adicional {i+1} guardada con ID: {news_id}")
                        else:
                            logger.info(f"La noticia adicional {i+1} ya existe con ID: {existing_news[0]['id']}")
            
            return news_ids
        
        except Exception as e:
            logger.error(f"Error guardando noticias: {str(e)}")
            return []
    
    def save_sentiment_from_signal(self, signal_data):
        """
        Guarda datos de sentimiento de mercado basados en una señal
        
        Args:
            signal_data (dict): Datos de la señal
            
        Returns:
            int: ID del sentimiento guardado o None si hay error
        """
        try:
            # Verificar si hay datos de sentimiento en la señal
            if not signal_data.get("sentiment"):
                logger.warning(f"No hay datos de sentimiento para guardar en la señal de {signal_data.get('symbol', '')}")
                return None
            
            # Verificar si ya existe un registro de sentimiento para hoy
            existing_sentiment = self.db_manager.execute_query(
                "SELECT id FROM market_sentiment WHERE DATE(date) = CURDATE()",
                []
            )
            
            if existing_sentiment:
                logger.info(f"Ya existe un registro de sentimiento para hoy con ID: {existing_sentiment[0]['id']}")
                return existing_sentiment[0]['id']
            
            # Mapear el sentimiento de la señal al formato de la tabla
            sentiment_mapping = {
                "positivo": "Alcista",
                "negativo": "Bajista",
                "neutral": "Neutral",
                "muy positivo": "Alcista",
                "muy negativo": "Bajista",
                "ligeramente positivo": "Alcista",
                "ligeramente negativo": "Bajista"
            }
            
            overall_sentiment = sentiment_mapping.get(
                signal_data.get("sentiment", "").lower(), 
                "Neutral"
            )
            
            # Extraer información técnica del análisis
            technical_indicators = self._extract_technical_info(signal_data)
            
            # Crear datos de sentimiento
            sentiment_data = {
                "date": datetime.now().date(),
                "overall": overall_sentiment,
                "vix": self._extract_vix(signal_data),
                "sp500_trend": self._extract_sp500_trend(signal_data),
                "technical_indicators": technical_indicators,
                "volume": self._extract_volume_info(signal_data),
                "notes": f"Basado en análisis de {signal_data.get('symbol', '')}. " +
                         f"Sentimiento: {signal_data.get('sentiment', 'Neutral')} " +
                         f"(Score: {signal_data.get('sentiment_score', 0.5)})"
            }
            
            # Guardar datos de sentimiento
            sentiment_id = self.db_manager.save_market_sentiment(sentiment_data)
            
            if sentiment_id:
                logger.info(f"Datos de sentimiento guardados con ID: {sentiment_id}")
            
            return sentiment_id
        
        except Exception as e:
            logger.error(f"Error guardando datos de sentimiento: {str(e)}")
            return None
    
    def _determine_news_impact(self, signal_data):
        """Determina el impacto de una noticia basado en los datos de la señal"""
        # Si es una señal de alta confianza, el impacto es alto
        if signal_data.get("is_high_confidence") or signal_data.get("confidence_level") == "Alta":
            return "Alto"
        
        # Si el sentimiento es muy positivo o muy negativo, el impacto es alto
        sentiment = signal_data.get("sentiment", "").lower()
        if "muy positivo" in sentiment or "muy negativo" in sentiment:
            return "Alto"
        
        # Si el sentimiento es ligeramente positivo o negativo, el impacto es medio
        if "ligeramente" in sentiment:
            return "Medio"
        
        # Por defecto, impacto medio
        return "Medio"
    
    def _extract_technical_info(self, signal_data):
        """Extrae información técnica del análisis"""
        technical_info = []
        
        # Añadir indicadores alcistas y bajistas
        if signal_data.get("bullish_indicators"):
            technical_info.append(f"Indicadores alcistas: {signal_data.get('bullish_indicators')}")
        
        if signal_data.get("bearish_indicators"):
            technical_info.append(f"Indicadores bajistas: {signal_data.get('bearish_indicators')}")
        
        # Añadir RSI si está disponible
        if signal_data.get("rsi"):
            technical_info.append(f"RSI: {signal_data.get('rsi')}")
        
        # Añadir tendencia
        if signal_data.get("trend"):
            technical_info.append(f"Tendencia: {signal_data.get('trend')}")
        
        return " | ".join(technical_info) if technical_info else "N/A"
    
    def _extract_vix(self, signal_data):
        """Extrae información del VIX del análisis"""
        # Intentar extraer el valor del VIX del análisis
        if signal_data.get("analysis"):
            vix_match = re.search(r"VIX.*?(\d+\.?\d*)", signal_data.get("analysis", ""))
            if vix_match:
                return vix_match.group(1)
        
        return "N/A"
    
    def _extract_sp500_trend(self, signal_data):
        """Extrae información de la tendencia del S&P 500"""
        # Intentar extraer información sobre el S&P 500
        if signal_data.get("analysis"):
            if "S&P 500" in signal_data.get("analysis", ""):
                if "alcista" in signal_data.get("analysis", "").lower():
                    return "Alcista"
                elif "bajista" in signal_data.get("analysis", "").lower():
                    return "Bajista"
                elif "lateral" in signal_data.get("analysis", "").lower():
                    return "Lateral"
        
        return "N/A"
    
    def _extract_volume_info(self, signal_data):
        """Extrae información sobre el volumen"""
        # Intentar extraer información sobre el volumen
        if signal_data.get("analysis"):
            volume_match = re.search(r"volumen.*?(alto|bajo|normal|fuerte|débil)", 
                                    signal_data.get("analysis", "").lower())
            if volume_match:
                return volume_match.group(1).capitalize()
        
        return "N/A"
