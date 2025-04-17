"""
Utilidades para procesamiento de datos
"""

import json
import logging

logger = logging.getLogger(__name__)

def safe_json_loads(json_str, default=None):
    """
    Carga un string JSON de forma segura
    
    Args:
        json_str (str): String JSON a cargar
        default (any, optional): Valor por defecto si hay error. Por defecto es None.
        
    Returns:
        any: Objeto JSON cargado o valor por defecto
    """
    if default is None:
        default = {}
    
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Error decodificando JSON: {str(e)}")
        return default
    except Exception as e:
        logger.warning(f"Error procesando JSON: {str(e)}")
        return default
