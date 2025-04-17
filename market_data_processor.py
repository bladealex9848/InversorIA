#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Data Processor - Módulo para procesar datos de mercado con IA
"""

import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketDataProcessor:
    """Clase para procesar datos de mercado con IA"""
    
    def __init__(self, ai_processor=None):
        """
        Inicializa el procesador de datos de mercado
        
        Args:
            ai_processor: Procesador de IA para mejorar los datos
        """
        self.ai_processor = ai_processor
        logger.info("MarketDataProcessor inicializado correctamente")
    
    def process_news(self, news_data: List[Dict[str, Any]], symbol: str, company_name: str = None) -> List[Dict[str, Any]]:
        """
        Procesa noticias para mejorar su calidad y relevancia
        
        Args:
            news_data (List[Dict[str, Any]]): Lista de noticias a procesar
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa
            
        Returns:
            List[Dict[str, Any]]: Noticias procesadas
        """
        if not news_data:
            return []
        
        processed_news = []
        
        for news in news_data:
            # Verificar si la noticia tiene título
            if not news.get("title"):
                continue
            
            # Verificar si la noticia es relevante para el símbolo
            if not self._is_news_relevant(news, symbol, company_name):
                continue
            
            # Procesar con IA si está disponible
            if self.ai_processor:
                try:
                    # Contexto para el procesamiento
                    context = {
                        "symbol": symbol,
                        "company_name": company_name or symbol,
                        "date": news.get("date", datetime.now().strftime("%Y-%m-%d"))
                    }
                    
                    # Procesar título
                    if news.get("title"):
                        processed_title = self.ai_processor.process_content_with_ai(
                            symbol, news["title"], "news_title", context
                        )
                        if processed_title:
                            news["title"] = processed_title
                    
                    # Procesar resumen
                    if news.get("summary"):
                        processed_summary = self.ai_processor.process_content_with_ai(
                            symbol, news["summary"], "news_summary", context
                        )
                        if processed_summary:
                            news["summary"] = processed_summary
                except Exception as e:
                    logger.error(f"Error procesando noticia con IA: {str(e)}")
            
            # Asegurar que la noticia tenga todos los campos necesarios
            if not news.get("url"):
                news["url"] = self._generate_fallback_url(symbol, news.get("source", ""))
            
            if not news.get("date"):
                news["date"] = datetime.now().strftime("%Y-%m-%d")
            
            if not news.get("source"):
                news["source"] = "Fuente financiera"
            
            # Añadir a la lista de noticias procesadas
            processed_news.append(news)
        
        # Si no hay noticias después del procesamiento, generar una noticia genérica
        if not processed_news:
            generic_news = {
                "title": f"Información de mercado para {company_name or symbol}",
                "summary": f"No hay noticias específicas disponibles para {company_name or symbol} en este momento. Consulte fuentes financieras para obtener la información más reciente.",
                "url": self._generate_fallback_url(symbol),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Sistema InversorIA"
            }
            processed_news.append(generic_news)
        
        return processed_news
    
    def process_analysis(self, analysis_data: Dict[str, Any], symbol: str, company_name: str = None) -> Dict[str, Any]:
        """
        Procesa datos de análisis para mejorar su calidad y relevancia
        
        Args:
            analysis_data (Dict[str, Any]): Datos de análisis a procesar
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa
            
        Returns:
            Dict[str, Any]: Análisis procesado
        """
        if not analysis_data:
            return {}
        
        # Procesar con IA si está disponible
        if self.ai_processor:
            try:
                # Contexto para el procesamiento
                context = {
                    "symbol": symbol,
                    "company_name": company_name or symbol,
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
                
                # Procesar recomendaciones
                if "recommendations" in analysis_data and analysis_data["recommendations"].get("average"):
                    recommendation = analysis_data["recommendations"]["average"]
                    processed_recommendation = self.ai_processor.process_content_with_ai(
                        symbol, recommendation, "recommendation", context
                    )
                    if processed_recommendation:
                        analysis_data["recommendations"]["average"] = processed_recommendation
            except Exception as e:
                logger.error(f"Error procesando análisis con IA: {str(e)}")
        
        return analysis_data
    
    def generate_expert_analysis(self, data: Dict[str, Any], symbol: str, company_name: str = None) -> str:
        """
        Genera un análisis experto basado en los datos disponibles
        
        Args:
            data (Dict[str, Any]): Datos del activo
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa
            
        Returns:
            str: Análisis experto
        """
        if not data:
            return ""
        
        # Extraer información relevante
        price = data.get("quote", {}).get("price", {}).get("current")
        change = data.get("quote", {}).get("price", {}).get("change")
        change_percent = data.get("quote", {}).get("price", {}).get("change_percent")
        
        # Determinar dirección del mercado
        direction = "alcista" if change and change > 0 else "bajista" if change and change < 0 else "neutral"
        
        # Extraer recomendaciones
        recommendation = data.get("analysis", {}).get("recommendations", {}).get("average", "neutral")
        
        # Extraer objetivos de precio
        price_target = data.get("analysis", {}).get("price_targets", {}).get("average")
        price_target_low = data.get("analysis", {}).get("price_targets", {}).get("low")
        price_target_high = data.get("analysis", {}).get("price_targets", {}).get("high")
        
        # Generar análisis básico
        company = company_name or symbol
        analysis = f"Análisis de {company} ({symbol}): "
        
        if price:
            analysis += f"Cotiza a ${price:.2f} "
            if change and change_percent:
                analysis += f"con un cambio de {change:+.2f} ({change_percent:+.2f}%). "
            analysis += f"El mercado muestra una tendencia {direction}. "
        
        if recommendation:
            analysis += f"La recomendación promedio de los analistas es {recommendation}. "
        
        if price_target:
            analysis += f"El objetivo de precio promedio es ${price_target:.2f} "
            if price_target_low and price_target_high:
                analysis += f"(rango: ${price_target_low:.2f} - ${price_target_high:.2f}). "
        
        # Añadir información de noticias si está disponible
        if data.get("news") and len(data["news"]) > 0:
            analysis += "Noticias recientes: "
            for i, news in enumerate(data["news"][:3], 1):
                if news.get("title"):
                    analysis += f"{i}. {news['title']}. "
        
        # Procesar con IA si está disponible
        if self.ai_processor:
            try:
                # Contexto para el procesamiento
                context = {
                    "symbol": symbol,
                    "company_name": company,
                    "price": price,
                    "change": change,
                    "change_percent": change_percent,
                    "direction": direction,
                    "recommendation": recommendation,
                    "price_target": price_target,
                    "price_target_low": price_target_low,
                    "price_target_high": price_target_high
                }
                
                processed_analysis = self.ai_processor.process_content_with_ai(
                    symbol, analysis, "expert_analysis", context
                )
                if processed_analysis:
                    return processed_analysis
            except Exception as e:
                logger.error(f"Error generando análisis experto con IA: {str(e)}")
        
        return analysis
    
    def _is_news_relevant(self, news: Dict[str, Any], symbol: str, company_name: str = None) -> bool:
        """
        Determina si una noticia es relevante para un símbolo
        
        Args:
            news (Dict[str, Any]): Noticia a evaluar
            symbol (str): Símbolo del activo
            company_name (str, optional): Nombre de la empresa
            
        Returns:
            bool: True si la noticia es relevante, False en caso contrario
        """
        # Obtener título y resumen
        title = news.get("title", "").lower()
        summary = news.get("summary", "").lower()
        
        # Verificar si el símbolo aparece en el título o resumen
        if symbol.lower() in title or symbol.lower() in summary:
            return True
        
        # Verificar si el nombre de la empresa aparece en el título o resumen
        if company_name and (company_name.lower() in title or company_name.lower() in summary):
            return True
        
        # Verificar palabras clave financieras
        financial_keywords = ["stock", "shares", "market", "investor", "earnings", "revenue", "profit", "loss"]
        for keyword in financial_keywords:
            if keyword in title or keyword in summary:
                return True
        
        # Por defecto, considerar relevante
        return True
    
    def _generate_fallback_url(self, symbol: str, source: str = "") -> str:
        """
        Genera una URL de respaldo basada en la fuente y el símbolo
        
        Args:
            symbol (str): Símbolo del activo
            source (str): Fuente de la noticia
            
        Returns:
            str: URL de respaldo
        """
        source_lower = source.lower()
        
        if "yahoo" in source_lower:
            return f"https://finance.yahoo.com/quote/{symbol}"
        elif "bloomberg" in source_lower:
            return f"https://www.bloomberg.com/quote/{symbol}"
        elif "cnbc" in source_lower:
            return f"https://www.cnbc.com/quotes/{symbol}"
        elif "reuters" in source_lower:
            return f"https://www.reuters.com/companies/{symbol}"
        elif "marketwatch" in source_lower:
            return f"https://www.marketwatch.com/investing/stock/{symbol}"
        elif "investing.com" in source_lower:
            return f"https://www.investing.com/search/?q={symbol}"
        else:
            return f"https://www.google.com/finance/quote/{symbol}"

# Crear instancia global para uso en otros módulos
market_processor = MarketDataProcessor()
