#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la generación de contenido con IA.
"""

import os
import sys
import logging
import toml
from typing import Dict, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_secrets() -> Dict[str, Any]:
    """
    Carga los secretos desde el archivo secrets.toml
    
    Returns:
        Dict[str, Any]: Secretos cargados
    """
    try:
        # Ruta al archivo secrets.toml
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        
        # Verificar si el archivo existe
        if not os.path.exists(secrets_path):
            logger.error(f"El archivo {secrets_path} no existe")
            # Buscar en otras ubicaciones comunes
            alt_paths = [
                "secrets.toml",
                os.path.join("..", ".streamlit", "secrets.toml"),
                os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml"),
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    secrets_path = path
                    logger.info(f"Usando archivo de secretos alternativo: {path}")
                    break
            else:
                raise FileNotFoundError(f"No se encontró el archivo secrets.toml")
        
        # Leer el archivo secrets.toml
        secrets = toml.load(secrets_path)
        return secrets
    
    except Exception as e:
        logger.error(f"Error cargando secretos: {str(e)}")
        return {}

def configure_openai():
    """
    Configura el cliente OpenAI con la clave de API
    """
    try:
        import openai
        
        # Cargar secretos
        secrets = load_secrets()
        
        # Configurar cliente OpenAI
        if "openai" in secrets and "api_key" in secrets["openai"]:
            openai.api_key = secrets["openai"]["api_key"]
            logger.info("Cliente OpenAI configurado con 'openai.api_key'")
        elif "OPENAI_API_KEY" in secrets:
            openai.api_key = secrets["OPENAI_API_KEY"]
            logger.info("Cliente OpenAI configurado con 'OPENAI_API_KEY'")
        else:
            logger.error("No se encontró configuración de OpenAI en secrets.toml")
            return False
        
        return True
    
    except ImportError:
        logger.error("No se pudo importar la biblioteca OpenAI")
        return False
    except Exception as e:
        logger.error(f"Error configurando OpenAI: {str(e)}")
        return False

def test_generate_summary():
    """
    Prueba la función generate_summary_with_ai
    """
    try:
        from ai_content_generator import generate_summary_with_ai
        
        # Configurar OpenAI
        if not configure_openai():
            return
        
        # Probar generación de resumen
        title = "Bitcoin Surges Past $60,000 as Institutional Adoption Grows"
        symbol = "BTC"
        url = "https://example.com/bitcoin-news"
        
        logger.info(f"Generando resumen para: {title}")
        summary = generate_summary_with_ai(title, symbol, url)
        
        if summary:
            logger.info(f"✅ Resumen generado correctamente: {summary}")
        else:
            logger.error("❌ No se pudo generar el resumen")
    
    except ImportError:
        logger.error("❌ No se pudo importar generate_summary_with_ai desde ai_content_generator")
    except Exception as e:
        logger.error(f"❌ Error en test_generate_summary: {str(e)}")

def test_generate_sentiment_analysis():
    """
    Prueba la función generate_sentiment_analysis_with_ai
    """
    try:
        from ai_content_generator import generate_sentiment_analysis_with_ai
        
        # Configurar OpenAI
        if not configure_openai():
            return
        
        # Crear datos de sentimiento de prueba
        sentiment_data = {
            "id": 1,
            "date": "2025-04-18",
            "overall": "Neutral",
            "vix": 25.5,
            "sp500_trend": "Bajista",
            "technical_indicators": "RSI: 45, MACD: Negativo",
            "volume": "Por debajo del promedio",
            "notes": "Mercado en espera de datos económicos"
        }
        
        logger.info("Generando análisis de sentimiento")
        analysis = generate_sentiment_analysis_with_ai(sentiment_data)
        
        if analysis:
            logger.info(f"✅ Análisis de sentimiento generado correctamente: {analysis}")
        else:
            logger.error("❌ No se pudo generar el análisis de sentimiento")
    
    except ImportError:
        logger.error("❌ No se pudo importar generate_sentiment_analysis_with_ai desde ai_content_generator")
    except Exception as e:
        logger.error(f"❌ Error en test_generate_sentiment_analysis: {str(e)}")

def main():
    """Función principal"""
    logger.info("Probando generación de contenido con IA...")
    
    # Probar generación de resumen
    test_generate_summary()
    
    # Probar generación de análisis de sentimiento
    test_generate_sentiment_analysis()

if __name__ == "__main__":
    main()
