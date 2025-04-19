#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear una versión modificada de AIExpert que funcione fuera de Streamlit.
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


class StandaloneAIExpert:
    """
    Clase para procesar texto con IA utilizando OpenAI, diseñada para funcionar
    fuera del entorno de Streamlit.
    """

    def __init__(self):
        """
        Inicializa el experto en IA
        """
        self.client = None
        self.assistant_id = None
        self.model = "gpt-4.1-nano"  # Modelo por defecto

        try:
            # Importar OpenAI
            import openai

            # Cargar secretos
            secrets = load_secrets()

            # Obtener el modelo preferido de los secretos
            if "OPENAI_API_MODEL" in secrets:
                self.model = secrets["OPENAI_API_MODEL"]
                logger.info(f"Usando modelo: {self.model}")

            # Obtener el ID del asistente si está disponible
            if "ASSISTANT_ID" in secrets:
                self.assistant_id = secrets["ASSISTANT_ID"]
                logger.info(f"Usando asistente con ID: {self.assistant_id}")

            # Configurar cliente OpenAI
            if "openai" in secrets and "api_key" in secrets["openai"]:
                openai.api_key = secrets["openai"]["api_key"]
                self.client = openai.OpenAI(api_key=secrets["openai"]["api_key"])
                logger.info("Cliente OpenAI inicializado con 'openai.api_key'")
            elif "OPENAI_API_KEY" in secrets:
                openai.api_key = secrets["OPENAI_API_KEY"]
                self.client = openai.OpenAI(api_key=secrets["OPENAI_API_KEY"])
                logger.info("Cliente OpenAI inicializado con 'OPENAI_API_KEY'")
            else:
                logger.error("No se encontró configuración de OpenAI en secrets.toml")
        except ImportError:
            logger.error("No se pudo importar la biblioteca OpenAI")
        except Exception as e:
            logger.error(f"Error inicializando cliente OpenAI: {str(e)}")

    def process_text(self, prompt: str, max_tokens: int = 250) -> str:
        """
        Procesa texto con IA

        Args:
            prompt (str): Texto a procesar
            max_tokens (int): Número máximo de tokens en la respuesta

        Returns:
            str: Texto procesado
        """
        try:
            # Si no tenemos cliente, devolver un fallback
            if not self.client:
                return self._fallback_process(prompt)

            # Si tenemos un asistente configurado, usarlo
            if self.assistant_id:
                return self._process_with_assistant(prompt)

            # Si no hay asistente, usar chat completions
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis financiero y trading.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=max_tokens,
            )

            # Extraer respuesta
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error en process_text: {str(e)}")
            return self._fallback_process(prompt)

    def _process_with_assistant(self, prompt: str) -> str:
        """
        Procesa texto utilizando un asistente de OpenAI

        Args:
            prompt (str): Texto a procesar

        Returns:
            str: Texto procesado
        """
        try:
            import time

            # Crear un hilo
            thread = self.client.beta.threads.create()

            # Añadir mensaje al hilo
            self.client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=prompt
            )

            # Ejecutar el asistente
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=self.assistant_id
            )

            # Esperar a que termine la ejecución
            while run.status != "completed":
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )

                # Si hay un error, salir del bucle
                if run.status in ["failed", "cancelled", "expired"]:
                    logger.error(f"Error en la ejecución del asistente: {run.status}")
                    return self._fallback_process(prompt)

            # Obtener los mensajes
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)

            # Extraer la respuesta del asistente
            for message in messages.data:
                if message.role == "assistant":
                    # Extraer el contenido del mensaje
                    if hasattr(message, "content") and len(message.content) > 0:
                        message_content = message.content[0]
                        if hasattr(message_content, "text"):
                            nested_text = message_content.text
                            if hasattr(nested_text, "value"):
                                return nested_text.value

            # Si no se pudo extraer la respuesta
            return "No se pudo procesar el mensaje del asistente"

        except Exception as e:
            logger.error(f"Error procesando con asistente: {str(e)}")
            return self._fallback_process(prompt)

    def _fallback_process(self, prompt: str) -> str:
        """
        Método de respaldo para procesar texto

        Args:
            prompt (str): Texto a procesar

        Returns:
            str: Texto procesado
        """
        # Simplemente devolver un resumen del prompt
        if len(prompt) > 100:
            return f"{prompt[:97]}..."
        return prompt


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
    try:
        # Inicializar experto en IA
        ai_expert = StandaloneAIExpert()

        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, "client") or not ai_expert.client:
            logger.warning("Cliente OpenAI no disponible. No se puede generar resumen.")
            return None

        # Crear prompt para generar resumen
        url_info = f"URL: {url}" if url else ""
        prompt = f"""Genera un resumen informativo y detallado en español (150-200 caracteres)
para una noticia financiera sobre {symbol} con este título: '{title}'.
{url_info}

El resumen debe:
1. Ser específico y relevante para inversores
2. Incluir posibles implicaciones para el precio de la acción
3. Estar escrito en un tono profesional y objetivo
4. NO incluir frases genéricas de introducción o cierre
5. Ir directo al punto principal de la noticia"""

        # Generar resumen
        summary = ai_expert.process_text(prompt, max_tokens=250)

        # Verificar que el resumen tenga una longitud mínima
        if not summary or len(summary) < 30:
            logger.warning(f"Resumen demasiado corto o vacío: {summary}")
            return None

        return summary
    except Exception as e:
        logger.error(f"Error generando resumen con IA: {str(e)}")
        return None


def generate_sentiment_analysis_with_ai(
    sentiment_data: Dict[str, Any],
) -> Optional[str]:
    """
    Genera un análisis de sentimiento utilizando IA

    Args:
        sentiment_data (Dict[str, Any]): Datos de sentimiento

    Returns:
        Optional[str]: Análisis generado o None si no se pudo generar un análisis válido
    """
    try:
        # Inicializar experto en IA
        ai_expert = StandaloneAIExpert()

        # Verificar si el cliente OpenAI está disponible
        if not hasattr(ai_expert, "client") or not ai_expert.client:
            logger.warning(
                "Cliente OpenAI no disponible. No se puede generar análisis."
            )
            return None

        # Recopilar datos disponibles para generar un análisis completo
        overall = sentiment_data.get("overall", "Neutral")
        vix = sentiment_data.get("vix", "N/A")
        sp500_trend = sentiment_data.get("sp500_trend", "N/A")
        tech_indicators = sentiment_data.get("technical_indicators", "N/A")

        # Crear prompt para generar análisis
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

        # Verificar que el análisis tenga una longitud mínima
        if not analysis or len(analysis) < 50:
            logger.warning(f"Análisis demasiado corto o vacío: {analysis}")
            return None

        return analysis
    except Exception as e:
        logger.error(f"Error generando análisis con IA: {str(e)}")
        return None


def main():
    """Función principal"""
    logger.info("Probando StandaloneAIExpert...")

    # Probar generación de resumen
    title = "Bitcoin Surges Past $60,000 as Institutional Adoption Grows"
    symbol = "BTC"

    logger.info(f"Generando resumen para: {title}")
    summary = generate_summary_with_ai(title, symbol)

    if summary:
        logger.info(f"✅ Resumen generado correctamente: {summary}")
    else:
        logger.error("❌ No se pudo generar el resumen")

    # Probar generación de análisis de sentimiento
    sentiment_data = {
        "overall": "Neutral",
        "vix": 25.5,
        "sp500_trend": "Bajista",
        "technical_indicators": "RSI: 45, MACD: Negativo",
    }

    logger.info("Generando análisis de sentimiento")
    analysis = generate_sentiment_analysis_with_ai(sentiment_data)

    if analysis:
        logger.info(
            f"✅ Análisis de sentimiento generado correctamente: {analysis[:100]}..."
        )
    else:
        logger.error("❌ No se pudo generar el análisis de sentimiento")


if __name__ == "__main__":
    main()
