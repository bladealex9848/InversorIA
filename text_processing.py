#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para procesamiento y análisis de texto.
Incluye funciones para detectar idiomas y traducir texto.
"""

import re
import logging
from typing import Dict, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Intentar importar el experto en IA
AI_EXPERT_AVAILABLE = False
try:
    from ai_utils import AIExpert
    AI_EXPERT_AVAILABLE = True
    logger.info("AIExpert disponible para uso en text_processing.py")
except ImportError:
    logger.warning("AIExpert no está disponible en text_processing.py. Se usarán métodos alternativos.")


def is_english_text(text: str) -> bool:
    """
    Detecta si un texto está en inglés
    
    Args:
        text (str): Texto a analizar
        
    Returns:
        bool: True si el texto parece estar en inglés, False en caso contrario
    """
    if not text or len(text) < 10:
        return False
    
    # Palabras comunes en inglés que no suelen usarse en español
    english_words = [
        r'\bthe\b', r'\band\b', r'\bof\b', r'\bto\b', r'\ba\b', r'\bin\b', 
        r'\bthat\b', r'\bhave\b', r'\bI\b', r'\bit\b', r'\bfor\b', r'\bnot\b', 
        r'\bon\b', r'\bwith\b', r'\bhe\b', r'\bas\b', r'\byou\b', r'\bdo\b', 
        r'\bat\b', r'\bthis\b', r'\bbut\b', r'\bhis\b', r'\bby\b', r'\bfrom\b',
        r'\bthey\b', r'\bwe\b', r'\bsay\b', r'\bher\b', r'\bshe\b', r'\bor\b',
        r'\ban\b', r'\bwill\b', r'\bmy\b', r'\bone\b', r'\ball\b', r'\bwould\b',
        r'\bthere\b', r'\btheir\b', r'\bwhat\b', r'\bso\b', r'\bup\b', r'\bout\b',
        r'\bif\b', r'\babout\b', r'\bwho\b', r'\bget\b', r'\bwhich\b', r'\bgo\b',
        r'\bme\b', r'\bwhen\b', r'\bmake\b', r'\bcan\b', r'\blike\b', r'\btime\b',
        r'\bno\b', r'\bjust\b', r'\bhim\b', r'\bknow\b', r'\btake\b', r'\bpeople\b'
    ]
    
    # Contar palabras en inglés
    english_count = 0
    for word in english_words:
        if re.search(word, text.lower()):
            english_count += 1
    
    # Si hay más de 3 palabras en inglés, consideramos que el texto está en inglés
    return english_count > 3


def translate_title_to_spanish_without_ai(title: str) -> str:
    """
    Traduce un título al español sin usar IA (traducción básica)
    
    Args:
        title (str): Título a traducir
        
    Returns:
        str: Título traducido de forma básica
    """
    # Diccionario básico de traducción para palabras comunes en títulos financieros
    translation_dict = {
        "stock": "acción",
        "stocks": "acciones",
        "market": "mercado",
        "markets": "mercados",
        "price": "precio",
        "prices": "precios",
        "rise": "sube",
        "rises": "sube",
        "fall": "cae",
        "falls": "cae",
        "drop": "cae",
        "drops": "cae",
        "gain": "gana",
        "gains": "gana",
        "lose": "pierde",
        "loses": "pierde",
        "bull": "alcista",
        "bear": "bajista",
        "bullish": "alcista",
        "bearish": "bajista",
        "up": "arriba",
        "down": "abajo",
        "high": "alto",
        "low": "bajo",
        "report": "informe",
        "reports": "informes",
        "earnings": "ganancias",
        "revenue": "ingresos",
        "profit": "beneficio",
        "profits": "beneficios",
        "loss": "pérdida",
        "losses": "pérdidas",
        "investor": "inversor",
        "investors": "inversores",
        "trading": "operaciones",
        "trader": "operador",
        "traders": "operadores",
        "buy": "compra",
        "sell": "venta",
        "buys": "compra",
        "sells": "vende",
        "bought": "compró",
        "sold": "vendió",
        "crypto": "cripto",
        "cryptocurrency": "criptomoneda",
        "cryptocurrencies": "criptomonedas",
        "bitcoin": "Bitcoin",
        "ethereum": "Ethereum",
        "ripple": "Ripple",
        "the": "",
        "a": "",
        "an": "",
        "and": "y",
        "or": "o",
        "in": "en",
        "on": "en",
        "at": "en",
        "to": "a",
        "for": "para",
        "with": "con",
        "without": "sin",
        "by": "por",
        "from": "de",
        "of": "de",
        "as": "como",
        "is": "es",
        "are": "son",
        "was": "fue",
        "were": "fueron",
        "will": "será",
        "would": "sería",
        "could": "podría",
        "should": "debería",
        "can": "puede",
        "cannot": "no puede",
        "not": "no",
        "no": "no",
        "yes": "sí"
    }
    
    # Dividir el título en palabras
    words = title.split()
    
    # Traducir cada palabra
    translated_words = []
    for word in words:
        # Eliminar puntuación al final de la palabra para buscarla en el diccionario
        clean_word = word.lower().rstrip('.,;:!?')
        punctuation = word[len(clean_word):] if len(clean_word) < len(word) else ''
        
        # Buscar en el diccionario
        if clean_word in translation_dict:
            translated_word = translation_dict[clean_word]
            # Si la palabra original empieza con mayúscula, mantener la mayúscula
            if word[0].isupper() and translated_word:
                translated_word = translated_word[0].upper() + translated_word[1:]
            translated_words.append(translated_word + punctuation)
        else:
            translated_words.append(word)
    
    # Unir las palabras traducidas
    translated_title = ' '.join(word for word in translated_words if word)
    
    return translated_title


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


def clean_text(text: str) -> str:
    """
    Limpia un texto eliminando caracteres especiales y espacios innecesarios
    
    Args:
        text (str): Texto a limpiar
        
    Returns:
        str: Texto limpio
    """
    if not text:
        return ""
    
    # Eliminar comillas al inicio y final
    text = re.sub(r'^["\']|["\']$', "", text)
    
    # Reemplazar múltiples saltos de línea por uno solo
    text = re.sub(r"\n+", " ", text)
    
    # Reemplazar múltiples espacios por uno solo
    text = re.sub(r"\s+", " ", text)
    
    # Eliminar espacios al inicio y final
    text = text.strip()
    
    return text


def contains_prompt_text(text: str, prompt_fragments: list) -> bool:
    """
    Verifica si un texto contiene fragmentos del prompt
    
    Args:
        text (str): Texto a verificar
        prompt_fragments (list): Lista de fragmentos de prompt a buscar
        
    Returns:
        bool: True si el texto contiene algún fragmento del prompt, False en caso contrario
    """
    if not text:
        return True
    
    for fragment in prompt_fragments:
        if fragment in text:
            return True
    
    return False


if __name__ == "__main__":
    # Pruebas básicas
    test_texts = [
        "The stock market is rising today due to positive economic data",
        "El mercado de valores está subiendo hoy debido a datos económicos positivos",
        "Apple announces new iPhone with improved features",
        "Tesla reports record earnings in Q3",
        "Microsoft acquires AI startup for $1 billion"
    ]
    
    print("Pruebas de detección de idioma:")
    for text in test_texts:
        is_english = is_english_text(text)
        print(f"'{text[:30]}...' -> {'Inglés' if is_english else 'Español'}")
    
    print("\nPruebas de traducción básica:")
    for text in test_texts:
        if is_english_text(text):
            translated = translate_title_to_spanish_without_ai(text)
            print(f"Original: '{text[:30]}...'")
            print(f"Traducido: '{translated[:30]}...'")
    
    if AI_EXPERT_AVAILABLE:
        print("\nPruebas de traducción con IA:")
        for text in test_texts:
            if is_english_text(text):
                translated = translate_title_to_spanish(text)
                print(f"Original: '{text[:30]}...'")
                print(f"Traducido: '{translated[:30]}...'")
