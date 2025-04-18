def translate_title_to_spanish(title: str) -> str:
    """
    Traduce un título al español utilizando IA
    
    Args:
        title (str): Título a traducir
        
    Returns:
        str: Título traducido
    """
    if not AI_EXPERT_AVAILABLE:
        logger.warning("AIExpert no está disponible. No se puede traducir título.")
        return translate_title_to_spanish_without_ai(title)
    
    # Verificar si el título ya está en español
    if not is_english_text(title):
        return title
    
    try:
        # Inicializar experto en IA
        ai_expert = AIExpert()
        
        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, 'client') or not ai_expert.client:
            logger.warning("Cliente OpenAI no disponible. Usando traducción básica.")
            return translate_title_to_spanish_without_ai(title)
        
        # Crear prompt para traducir título
        prompt = f"""Traduce este título de noticia financiera al español de forma profesional y concisa:
'{title}'

La traducción debe:
1. Mantener el significado original
2. Usar terminología financiera correcta en español
3. Ser clara y directa
4. NO exceder la longitud original significativamente"""
        
        # Traducir título
        translated_title = ai_expert.process_text(prompt, max_tokens=150)
        
        # Verificar si la traducción contiene parte del prompt (caso de fallback)
        if not translated_title or "Traduce este título" in translated_title:
            logger.warning("La traducción generada contiene parte del prompt o está vacía. Usando traducción básica.")
            return translate_title_to_spanish_without_ai(title)
        
        # Limpiar título traducido
        # Eliminar comillas al inicio y final
        translated_title = re.sub(r'^["\']|["\']$', "", translated_title)
        
        # Reemplazar múltiples saltos de línea por uno solo
        translated_title = re.sub(r"\n+", " ", translated_title)
        
        # Reemplazar múltiples espacios por uno solo
        translated_title = re.sub(r"\s+", " ", translated_title)
        
        # Eliminar espacios al inicio y final
        translated_title = translated_title.strip()
        
        # Verificar que la traducción tenga una longitud mínima
        if len(translated_title) < 10:
            logger.warning(f"Traducción demasiado corta: {translated_title}. Usando traducción básica.")
            return translate_title_to_spanish_without_ai(title)
        
        return translated_title
    except Exception as e:
        logger.error(f"Error traduciendo título con IA: {str(e)}")
        return translate_title_to_spanish_without_ai(title)
