def generate_summary_with_ai(title: str, symbol: str, url: str = None) -> Optional[str]:
    """
    Genera un resumen de noticia utilizando IA
    
    Args:
        title (str): Título de la noticia
        symbol (str): Símbolo del activo
        url (str, optional): URL de la noticia
        
    Returns:
        Optional[str]: Resumen generado o None si no se pudo generar un resumen válido
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning(
            "AIExpert no está disponible. No se puede generar resumen con IA."
        )
        return None

    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()
        
        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, 'client') or not ai_expert.client:
            logger.warning("Cliente OpenAI no disponible. No se puede generar resumen.")
            return None

        # Crear prompt para generar resumen (sin espacios al inicio de cada línea)
        prompt = f"""Genera un resumen informativo y detallado en español (150-200 caracteres) 
para una noticia financiera sobre {symbol} con este título: '{title}'.

El resumen debe:
1. Ser específico y relevante para inversores
2. Incluir posibles implicaciones para el precio de la acción
3. Estar escrito en un tono profesional y objetivo
4. NO incluir frases genéricas de introducción o cierre
5. Ir directo al punto principal de la noticia"""

        # Generar resumen
        summary = ai_expert.process_text(prompt, max_tokens=250)
        
        # Verificar si el resumen contiene parte del prompt (caso de fallback)
        if not summary or "Genera un resumen informativo" in summary or "Como experto financiero" in summary:
            logger.warning("El resumen generado contiene parte del prompt o está vacío.")
            return None

        # Limpiar resumen
        # Eliminar comillas al inicio y final
        summary = re.sub(r'^["\']|["\']$', "", summary)

        # Reemplazar múltiples saltos de línea por uno solo
        summary = re.sub(r"\n+", " ", summary)

        # Reemplazar múltiples espacios por uno solo
        summary = re.sub(r"\s+", " ", summary)

        # Eliminar espacios al inicio y final
        summary = summary.strip()
        
        # Verificar que el resumen tenga una longitud mínima
        if len(summary) < 30:
            logger.warning(f"Resumen demasiado corto: {summary}")
            return None

        return summary
    except Exception as e:
        logger.error(f"Error generando resumen con IA: {str(e)}")
        return None
