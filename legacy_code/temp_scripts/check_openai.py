#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar si el cliente OpenAI está disponible y configurado correctamente.
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
    handlers=[logging.StreamHandler(sys.stdout)],
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


def check_openai_config(secrets: Dict[str, Any]) -> bool:
    """
    Verifica si la configuración de OpenAI está presente en los secretos

    Args:
        secrets (Dict[str, Any]): Secretos cargados

    Returns:
        bool: True si la configuración está presente, False en caso contrario
    """
    # Verificar si hay una clave de API de OpenAI
    if "openai" in secrets and "api_key" in secrets["openai"]:
        logger.info("Configuración de OpenAI encontrada en formato 'openai.api_key'")
        return True
    elif "OPENAI_API_KEY" in secrets:
        logger.info("Configuración de OpenAI encontrada en formato 'OPENAI_API_KEY'")
        return True
    else:
        logger.error("No se encontró configuración de OpenAI en secrets.toml")
        return False


def check_openai_client() -> bool:
    """
    Verifica si el cliente OpenAI está disponible y configurado correctamente

    Returns:
        bool: True si el cliente está disponible, False en caso contrario
    """
    try:
        # Intentar importar OpenAI
        import openai

        logger.info("Biblioteca OpenAI importada correctamente")

        # Cargar secretos
        secrets = load_secrets()

        # Verificar configuración
        if not check_openai_config(secrets):
            return False

        # Configurar cliente OpenAI
        if "openai" in secrets and "api_key" in secrets["openai"]:
            openai.api_key = secrets["openai"]["api_key"]
        elif "OPENAI_API_KEY" in secrets:
            openai.api_key = secrets["OPENAI_API_KEY"]

        # Verificar si el cliente funciona
        try:
            # Intentar hacer una llamada simple a la API
            response = openai.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, are you working?"},
                ],
                max_tokens=10,
            )

            # Si llegamos aquí, el cliente funciona
            logger.info("Cliente OpenAI configurado correctamente y funcionando")
            logger.info(f"Respuesta de prueba: {response.choices[0].message.content}")
            return True

        except Exception as api_error:
            logger.error(
                f"Error al hacer una llamada de prueba a la API de OpenAI: {str(api_error)}"
            )
            return False

    except ImportError:
        logger.error("No se pudo importar la biblioteca OpenAI")
        return False
    except Exception as e:
        logger.error(f"Error verificando cliente OpenAI: {str(e)}")
        return False


def main():
    """Función principal"""
    logger.info("Verificando disponibilidad del cliente OpenAI...")

    # Verificar cliente OpenAI
    if check_openai_client():
        logger.info("✅ El cliente OpenAI está disponible y configurado correctamente")
    else:
        logger.error(
            "❌ El cliente OpenAI no está disponible o no está configurado correctamente"
        )

    # Verificar AIExpert
    try:
        from ai_utils import AIExpert

        # Crear instancia de AIExpert
        ai_expert = AIExpert()

        # Verificar si el cliente está disponible
        if ai_expert.client:
            logger.info("✅ AIExpert inicializado correctamente con cliente OpenAI")

            # Probar procesamiento de texto
            result = ai_expert.process_text("Prueba de procesamiento de texto")
            logger.info(f"Resultado de prueba: {result}")
        else:
            logger.warning("⚠️ AIExpert inicializado pero sin cliente OpenAI")

    except ImportError:
        logger.error("❌ No se pudo importar AIExpert desde ai_utils")
    except Exception as e:
        logger.error(f"❌ Error verificando AIExpert: {str(e)}")


if __name__ == "__main__":
    main()
