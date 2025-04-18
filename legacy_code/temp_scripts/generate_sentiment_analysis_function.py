def generate_sentiment_analysis_with_ai(sentiment_data: Dict[str, Any]) -> Optional[str]:
    """
    Genera un análisis de sentimiento utilizando IA
    
    Args:
        sentiment_data (Dict[str, Any]): Datos de sentimiento
        
    Returns:
        Optional[str]: Análisis generado o None si no se pudo generar un análisis válido
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning(
            "AIExpert no está disponible. No se puede generar análisis con IA."
        )
        return None

    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()
        
        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, 'client') or not ai_expert.client:
            logger.warning("Cliente OpenAI no disponible. No se puede generar análisis.")
            return None

        # Recopilar datos disponibles para generar un análisis completo
        overall = sentiment_data.get("overall", "Neutral")
        vix = sentiment_data.get("vix", "N/A")
        sp500_trend = sentiment_data.get("sp500_trend", "N/A")
        tech_indicators = sentiment_data.get("technical_indicators", "N/A")

        # Crear prompt para generar análisis (sin espacios al inicio de cada línea)
        prompt = f"""Genera un análisis detallado del sentimiento de mercado 
basado en los siguientes datos:

- Sentimiento general: {overall}
- VIX (índice de volatilidad): {vix}
- Tendencia S&P500: {sp500_trend}
- Indicadores técnicos: {tech_indicators}

El análisis debe:
1. Explicar las implicaciones de estos datos para inversores
2. Incluir una evaluación de riesgos y oportunidades
3. Proporcionar contexto sobre la situación actual del mercado
4. Estar escrito en español profesional y objetivo
5. Tener entre 150-300 palabras
6. NO incluir frases genéricas de introducción o cierre"""

        # Generar análisis
        analysis = ai_expert.process_text(prompt, max_tokens=500)
        
        # Verificar si el análisis contiene parte del prompt (caso de fallback)
        if not analysis or "Genera un análisis detallado" in analysis:
            logger.warning("El análisis generado contiene parte del prompt o está vacío.")
            return None

        # Limpiar análisis
        # Eliminar comillas al inicio y final
        analysis = re.sub(r'^["\']|["\']$', "", analysis)

        # Reemplazar múltiples saltos de línea por uno solo
        analysis = re.sub(r"\n+", " ", analysis)

        # Reemplazar múltiples espacios por uno solo
        analysis = re.sub(r"\s+", " ", analysis)

        # Eliminar espacios al inicio y final
        analysis = analysis.strip()
        
        # Verificar que el análisis tenga una longitud mínima
        if len(analysis) < 50:
            logger.warning(f"Análisis demasiado corto: {analysis}")
            return None

        return analysis
    except Exception as e:
        logger.error(f"Error generando análisis con IA: {str(e)}")
        return None
