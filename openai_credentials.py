#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para gestionar las credenciales de OpenAI.
Este archivo proporciona funciones para cargar y acceder a las credenciales de OpenAI
desde diferentes fuentes (secrets.toml, variables de entorno, etc.).
"""

import os
import logging
import toml
from typing import Dict, Optional, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def load_openai_credentials() -> Dict[str, Any]:
    """
    Carga las credenciales de OpenAI desde diferentes fuentes.
    
    Returns:
        Dict[str, Any]: Diccionario con las credenciales de OpenAI
    """
    credentials = {}
    
    try:
        # 1. Intentar cargar desde secrets.toml
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            
            # Buscar API key en diferentes ubicaciones
            if "openai" in secrets and "api_key" in secrets["openai"]:
                credentials["api_key"] = secrets["openai"]["api_key"]
                logger.info("API key de OpenAI cargada desde secrets.toml (openai.api_key)")
            elif "OPENAI_API_KEY" in secrets:
                credentials["api_key"] = secrets["OPENAI_API_KEY"]
                logger.info("API key de OpenAI cargada desde secrets.toml (OPENAI_API_KEY)")
            elif "api_keys" in secrets and "OPENAI_API_KEY" in secrets["api_keys"]:
                credentials["api_key"] = secrets["api_keys"]["OPENAI_API_KEY"]
                logger.info("API key de OpenAI cargada desde secrets.toml (api_keys.OPENAI_API_KEY)")
            
            # Buscar modelo en diferentes ubicaciones
            if "openai" in secrets and "model" in secrets["openai"]:
                credentials["model"] = secrets["openai"]["model"]
            elif "OPENAI_API_MODEL" in secrets:
                credentials["model"] = secrets["OPENAI_API_MODEL"]
            elif "api_keys" in secrets and "OPENAI_API_MODEL" in secrets["api_keys"]:
                credentials["model"] = secrets["api_keys"]["OPENAI_API_MODEL"]
            else:
                credentials["model"] = "gpt-4.1-nano"  # Modelo por defecto
        
        # 2. Si no se encontró en secrets.toml, intentar cargar desde variables de entorno
        if "api_key" not in credentials:
            if "OPENAI_API_KEY" in os.environ:
                credentials["api_key"] = os.environ["OPENAI_API_KEY"]
                logger.info("API key de OpenAI cargada desde variables de entorno")
            
            if "OPENAI_API_MODEL" in os.environ:
                credentials["model"] = os.environ["OPENAI_API_MODEL"]
            else:
                credentials["model"] = "gpt-4.1-nano"  # Modelo por defecto
        
        # Verificar si se encontraron credenciales
        if "api_key" not in credentials:
            logger.warning("No se encontraron credenciales de OpenAI")
        
        return credentials
    
    except Exception as e:
        logger.error(f"Error cargando credenciales de OpenAI: {str(e)}")
        return {}

def initialize_openai_client():
    """
    Inicializa el cliente de OpenAI con las credenciales cargadas.
    
    Returns:
        Optional[Any]: Cliente de OpenAI o None si no se pudo inicializar
    """
    try:
        import openai
        
        # Cargar credenciales
        credentials = load_openai_credentials()
        
        if "api_key" not in credentials:
            logger.warning("No se encontró API key de OpenAI. No se puede inicializar el cliente.")
            return None
        
        # Inicializar cliente
        openai.api_key = credentials["api_key"]
        client = openai.OpenAI(api_key=credentials["api_key"])
        
        logger.info("Cliente OpenAI inicializado correctamente")
        return client
    
    except ImportError:
        logger.warning("No se pudo importar el módulo openai. Instálalo con: pip install openai")
        return None
    except Exception as e:
        logger.error(f"Error inicializando cliente OpenAI: {str(e)}")
        return None

# Variables globales para acceso fácil
OPENAI_CREDENTIALS = load_openai_credentials()
OPENAI_API_KEY = OPENAI_CREDENTIALS.get("api_key")
OPENAI_API_MODEL = OPENAI_CREDENTIALS.get("model", "gpt-4.1-nano")

if __name__ == "__main__":
    # Prueba de funcionamiento
    credentials = load_openai_credentials()
    print(f"Credenciales encontradas: {credentials}")
    
    client = initialize_openai_client()
    if client:
        print("Cliente OpenAI inicializado correctamente")
    else:
        print("No se pudo inicializar el cliente OpenAI")
