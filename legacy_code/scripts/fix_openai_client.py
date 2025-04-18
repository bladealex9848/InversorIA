"""
Script para corregir el error 'cannot access local variable 'client' where it is not associated with a value'
"""

import logging
import os
import sys
import traceback

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def fix_openai_client_issue():
    """
    Corrige el problema con la inicialización del cliente de OpenAI
    """
    try:
        # Importar las bibliotecas necesarias
        import openai
        import toml

        logger.info("Verificando configuración de OpenAI...")

        # Buscar secrets.toml
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if not os.path.exists(secrets_path):
            logger.warning(f"No se encontró el archivo {secrets_path}")
            return False

        # Cargar secrets.toml
        secrets = toml.load(secrets_path)

        # Verificar si existe la clave OPENAI_API_KEY
        api_key = None
        if "OPENAI_API_KEY" in secrets:
            api_key = secrets["OPENAI_API_KEY"]
            logger.info("Se encontró OPENAI_API_KEY en secrets.toml")
        elif "openai" in secrets and "api_key" in secrets["openai"]:
            api_key = secrets["openai"]["api_key"]
            logger.info("Se encontró openai.api_key en secrets.toml")
        elif "api_keys" in secrets and "OPENAI_API_KEY" in secrets["api_keys"]:
            api_key = secrets["api_keys"]["OPENAI_API_KEY"]
            logger.info("Se encontró api_keys.OPENAI_API_KEY en secrets.toml")

        if not api_key:
            logger.error(
                "No se encontró ninguna clave de API de OpenAI en secrets.toml"
            )
            return False

        # Configurar cliente OpenAI
        openai.api_key = api_key

        # Verificar si el cliente funciona
        try:
            # Intentar hacer una llamada simple a la API
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
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
            logger.error(f"Error al probar el cliente OpenAI: {str(api_error)}")
            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"Error en fix_openai_client_issue: {str(e)}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if fix_openai_client_issue():
        logger.info("Corrección aplicada con éxito")
        sys.exit(0)
    else:
        logger.error("No se pudo aplicar la corrección")
        sys.exit(1)
