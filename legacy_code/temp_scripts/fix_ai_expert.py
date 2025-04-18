#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para modificar la clase AIExpert en ai_utils.py para que pueda inicializar
el cliente OpenAI directamente desde las credenciales en secrets.toml.
"""

import os
import sys
import re
import logging
from typing import Dict, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_file(file_path: str) -> Optional[str]:
    """
    Carga un archivo de texto

    Args:
        file_path (str): Ruta al archivo

    Returns:
        Optional[str]: Contenido del archivo o None si hay error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error cargando archivo {file_path}: {str(e)}")
        return None

def save_file(file_path: str, content: str) -> bool:
    """
    Guarda un archivo de texto

    Args:
        file_path (str): Ruta al archivo
        content (str): Contenido a guardar

    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error guardando archivo {file_path}: {str(e)}")
        return False

def fix_ai_expert_class(content: str) -> str:
    """
    Modifica la clase AIExpert para que pueda inicializar el cliente OpenAI
    directamente desde las credenciales en secrets.toml

    Args:
        content (str): Contenido del archivo ai_utils.py

    Returns:
        str: Contenido modificado
    """
    # Buscar la definición de la clase AIExpert
    ai_expert_pattern = r"class AIExpert:.*?def __init__\(self\):.*?self\.client = None.*?try:.*?if \"openai_client\" in st\.session_state:.*?self\.client = st\.session_state\.openai_client.*?except:.*?pass"

    # Reemplazar con la nueva implementación
    new_init = """class AIExpert:
    """
    Clase para procesar texto con IA utilizando OpenAI
    """

    def __init__(self):"""
        """
        Inicializa el experto en IA
        """
        self.client = None
        try:
            # Intentar obtener el cliente desde session_state si estamos en Streamlit
            import streamlit as st
            if hasattr(st, "session_state") and "openai_client" in st.session_state:
                self.client = st.session_state.openai_client
                logger.info("Cliente OpenAI obtenido desde st.session_state")
            else:
                # Si no estamos en Streamlit, inicializar el cliente directamente
                import openai
                import toml
                import os

                # Cargar secretos
                secrets_path = os.path.join(".streamlit", "secrets.toml")
                if not os.path.exists(secrets_path):
                    alt_paths = [
                        "secrets.toml",
                        os.path.join("..", ".streamlit", "secrets.toml"),
                        os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml"),
                    ]

                    for path in alt_paths:
                        if os.path.exists(path):
                            secrets_path = path
                            break

                if os.path.exists(secrets_path):
                    secrets = toml.load(secrets_path)

                    # Configurar cliente OpenAI
                    if "openai" in secrets and "api_key" in secrets["openai"]:
                        openai.api_key = secrets["openai"]["api_key"]
                        self.client = openai.client.OpenAI(api_key=secrets["openai"]["api_key"])
                        logger.info("Cliente OpenAI inicializado con 'openai.api_key'")
                    elif "OPENAI_API_KEY" in secrets:
                        openai.api_key = secrets["OPENAI_API_KEY"]
                        self.client = openai.client.OpenAI(api_key=secrets["OPENAI_API_KEY"])
                        logger.info("Cliente OpenAI inicializado con 'OPENAI_API_KEY'")
        except Exception as e:
            logger.error(f"Error inicializando cliente OpenAI: {str(e)}")
            pass"""

    # Usar expresión regular para reemplazar
    modified_content = re.sub(ai_expert_pattern, new_init, content, flags=re.DOTALL)

    return modified_content

def main():
    """Función principal"""
    # Ruta al archivo ai_utils.py
    ai_utils_path = "ai_utils.py"

    # Cargar archivo
    content = load_file(ai_utils_path)
    if not content:
        logger.error("No se pudo cargar el archivo ai_utils.py")
        return

    # Hacer una copia de seguridad
    backup_path = "ai_utils.py.bak"
    if save_file(backup_path, content):
        logger.info(f"Copia de seguridad guardada en {backup_path}")

    # Modificar la clase AIExpert
    modified_content = fix_ai_expert_class(content)

    # Guardar archivo modificado
    if save_file(ai_utils_path, modified_content):
        logger.info(f"Archivo {ai_utils_path} modificado correctamente")
    else:
        logger.error(f"No se pudo guardar el archivo modificado {ai_utils_path}")

if __name__ == "__main__":
    main()
