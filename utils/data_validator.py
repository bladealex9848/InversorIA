import logging
import re
from datetime import datetime

# Configurar logging
logger = logging.getLogger(__name__)


class DataValidator:
    """
    Clase para validar y mejorar datos antes de guardarlos en la base de datos.
    Asegura que los campos críticos estén completos y bien formateados.
    """

    def __init__(self, ai_expert=None):
        """
        Inicializa el validador de datos

        Args:
            ai_expert: Instancia del experto en IA para procesar contenido
        """
        self.ai_expert = ai_expert

    def validate_market_news(self, news_data):
        """
        Valida y mejora los datos de noticias antes de guardarlos

        Args:
            news_data (dict): Datos de la noticia a validar

        Returns:
            dict: Datos de la noticia validados y mejorados
        """
        validated_data = news_data.copy()

        # Asegurar que los campos obligatorios existan
        if not validated_data.get("title"):
            validated_data["title"] = (
                f"Noticia financiera - {datetime.now().strftime('%Y-%m-%d')}"
            )
            logger.warning("Se generó un título genérico para una noticia sin título")

        # Asegurar que el símbolo esté presente
        if not validated_data.get("symbol"):
            # Intentar extraer el símbolo del título y contenido
            try:
                from database_utils import extract_symbol_from_content

                title = validated_data.get("title", "")
                summary = validated_data.get("summary", "")

                # Buscar el símbolo actual en el contexto
                import inspect

                current_frame = inspect.currentframe()
                context_symbol = None

                # Buscar en los frames anteriores si hay un símbolo en el contexto
                while current_frame:
                    if (
                        "symbol" in current_frame.f_locals
                        and current_frame.f_locals["symbol"]
                    ):
                        context_symbol = current_frame.f_locals["symbol"]
                        break
                    current_frame = current_frame.f_back

                # Extraer símbolo usando la función mejorada que analiza título y contenido
                extracted_symbol = extract_symbol_from_content(
                    title, summary, context_symbol
                )

                if extracted_symbol:
                    validated_data["symbol"] = extracted_symbol
                    logger.info(
                        f"Símbolo extraído del contenido: {extracted_symbol} para noticia: {title[:30]}..."
                    )
                else:
                    # Intentar usar IA para identificar el símbolo si está disponible
                    if self.ai_expert:
                        try:
                            # Usar tanto el título como el resumen para la identificación
                            content_for_ai = title
                            if summary:
                                content_for_ai += "\n" + summary

                            prompt = f"Identifica el símbolo bursátil (ticker) principal mencionado en esta noticia financiera. Responde solo con el símbolo, sin explicaciones:\n'{content_for_ai}'"
                            ai_symbol = (
                                self.ai_expert.process_text(prompt, max_tokens=50)
                                .strip()
                                .upper()
                            )

                            if (
                                ai_symbol
                                and len(ai_symbol) <= 5
                                and ai_symbol.isalpha()
                            ):
                                validated_data["symbol"] = ai_symbol
                                logger.info(
                                    f"Símbolo identificado por IA: {ai_symbol} para noticia: {title[:30]}..."
                                )
                            else:
                                # Usar el símbolo del contexto si está disponible
                                if context_symbol:
                                    validated_data["symbol"] = context_symbol
                                    logger.info(
                                        f"Usando símbolo del contexto: {context_symbol} para noticia: {title[:30]}..."
                                    )
                                else:
                                    # Intentar identificar índices o sectores mencionados
                                    indices = {
                                        "S&P 500": "SPY",
                                        "S&P500": "SPY",
                                        "SP500": "SPY",
                                        "Dow Jones": "DIA",
                                        "DJIA": "DIA",
                                        "Nasdaq": "QQQ",
                                        "Nasdaq 100": "QQQ",
                                        "Russell 2000": "IWM",
                                        "VIX": "VIX",
                                        "Volatilidad": "VIX",
                                    }

                                    for index_name, index_symbol in indices.items():
                                        if index_name.lower() in content_for_ai.lower():
                                            validated_data["symbol"] = index_symbol
                                            logger.info(
                                                f"Índice identificado: {index_name}, usando símbolo: {index_symbol} para noticia: {title[:30]}..."
                                            )
                                            break
                                    else:  # Este else pertenece al for, se ejecuta si no se hace break
                                        # Como último recurso, marcar para revisión manual
                                        validated_data["symbol"] = (
                                            "REVIEW"  # Marcar para revisión
                                        )
                                        logger.warning(
                                            f"No se pudo identificar un símbolo para: {title[:30]}... - Marcado para revisión manual"
                                        )
                        except Exception as e:
                            logger.error(
                                f"Error al usar IA para identificar símbolo: {str(e)}"
                            )
                            # Usar el símbolo del contexto si está disponible
                            if context_symbol:
                                validated_data["symbol"] = context_symbol
                                logger.info(
                                    f"Usando símbolo del contexto después de error: {context_symbol} para noticia: {title[:30]}..."
                                )
                            else:
                                validated_data["symbol"] = (
                                    "REVIEW"  # Marcar para revisión
                                )
                                logger.warning(
                                    "Error al identificar símbolo - Noticia marcada para revisión manual"
                                )
                    else:
                        # Usar el símbolo del contexto si está disponible
                        if context_symbol:
                            validated_data["symbol"] = context_symbol
                            logger.info(
                                f"Usando símbolo del contexto (sin IA): {context_symbol} para noticia: {title[:30]}..."
                            )
                        else:
                            validated_data["symbol"] = "REVIEW"  # Marcar para revisión
                            logger.warning(
                                "No se pudo identificar símbolo (sin IA disponible) - Noticia marcada para revisión manual"
                            )
            except Exception as e:
                logger.error(f"Error al extraer símbolo del contenido: {str(e)}")
                # Usar el símbolo del contexto si está disponible como último recurso
                if context_symbol:
                    validated_data["symbol"] = context_symbol
                    logger.info(
                        f"Usando símbolo del contexto después de excepción: {context_symbol} para noticia: {title[:30]}..."
                    )
                else:
                    validated_data["symbol"] = "REVIEW"  # Marcar para revisión
                    logger.warning(
                        "Error en extracción de símbolo - Noticia marcada para revisión manual"
                    )

        # Asegurar que la fecha de noticia esté presente
        if not validated_data.get("news_date"):
            validated_data["news_date"] = datetime.now()
            logger.warning("Se asignó la fecha actual a una noticia sin fecha")

        # Asegurar que el impacto esté presente y sea válido
        if not validated_data.get("impact") or validated_data.get("impact") not in [
            "Alto",
            "Medio",
            "Bajo",
        ]:
            validated_data["impact"] = "Medio"  # Valor por defecto
            logger.warning(
                "Se asignó impacto Medio por defecto a una noticia sin impacto válido"
            )

        # Asegurar que la fuente esté presente
        if not validated_data.get("source"):
            validated_data["source"] = "Fuente financiera"
            logger.warning("Se asignó una fuente genérica a una noticia sin fuente")

        # Procesar el resumen con IA si está disponible y el resumen está vacío o es muy corto
        if self.ai_expert and (
            not validated_data.get("summary")
            or len(validated_data.get("summary", "")) < 20
        ):
            try:
                # Intentar generar un resumen basado en el título
                title = validated_data.get("title", "")
                symbol = validated_data.get("symbol", "SPY")

                prompt = f"""
                Como experto financiero, genera un resumen informativo y detallado en español (150-200 caracteres)
                para una noticia sobre {symbol} con este título: '{title}'.

                El resumen debe:
                1. Ser específico y relevante para inversores
                2. Incluir posibles implicaciones para el precio de la acción
                3. Estar escrito en un tono profesional y objetivo
                4. NO incluir frases genéricas de introducción o cierre
                5. Ir directo al punto principal de la noticia
                """

                generated_summary = self.ai_expert.process_text(prompt, max_tokens=250)

                if generated_summary and len(generated_summary) > 30:
                    # Limpiar el resumen generado (eliminar comillas, saltos de línea, etc.)
                    generated_summary = self._clean_text(generated_summary)
                    validated_data["summary"] = generated_summary
                    logger.info(
                        f"Resumen generado con IA para noticia: {title[:30]}..."
                    )
                else:
                    # Si no se pudo generar un resumen, crear uno genérico pero informativo
                    validated_data["summary"] = (
                        f"Noticia sobre {validated_data.get('symbol')} relacionada con {title[:50]}..."
                    )
                    logger.warning(
                        f"No se pudo generar resumen con IA, usando genérico para: {title[:30]}..."
                    )
            except Exception as e:
                logger.error(f"Error generando resumen con IA: {str(e)}")
                # Asignar un resumen genérico en caso de error
                validated_data["summary"] = (
                    f"Información financiera sobre {validated_data.get('symbol')}"
                )

        # Si el resumen existe pero está en inglés, traducirlo
        elif (
            self.ai_expert
            and validated_data.get("summary")
            and self._is_english_text(validated_data.get("summary", ""))
        ):
            try:
                prompt = f"""
                Traduce este resumen de noticia financiera al español de forma profesional y concisa:
                '{validated_data.get('summary')}'

                La traducción debe:
                1. Mantener toda la información relevante
                2. Usar terminología financiera correcta en español
                3. Ser clara y directa
                4. NO exceder 200 caracteres
                """

                translated_summary = self.ai_expert.process_text(prompt, max_tokens=250)

                if translated_summary and len(translated_summary) > 30:
                    # Limpiar el resumen traducido
                    translated_summary = self._clean_text(translated_summary)
                    validated_data["summary"] = translated_summary
                    logger.info(
                        f"Resumen traducido con IA para noticia: {validated_data.get('title')[:30]}..."
                    )
            except Exception as e:
                logger.error(f"Error traduciendo resumen con IA: {str(e)}")

        return validated_data

    def validate_market_sentiment(self, sentiment_data):
        """
        Valida y mejora los datos de sentimiento de mercado antes de guardarlos

        Args:
            sentiment_data (dict): Datos de sentimiento a validar

        Returns:
            dict: Datos de sentimiento validados y mejorados
        """
        validated_data = sentiment_data.copy()

        # Asegurar que la fecha esté presente
        if not validated_data.get("date"):
            validated_data["date"] = datetime.now().date()
            logger.warning("Se asignó la fecha actual a un sentimiento sin fecha")

        # Asegurar que el sentimiento general esté presente y sea válido
        if not validated_data.get("overall") or validated_data.get("overall") not in [
            "Alcista",
            "Bajista",
            "Neutral",
        ]:
            validated_data["overall"] = "Neutral"  # Valor por defecto
            logger.warning(
                "Se asignó sentimiento Neutral por defecto a un registro sin sentimiento válido"
            )

        # Asegurar que el campo de análisis esté presente y sea informativo
        if self.ai_expert and (
            not validated_data.get("analysis")
            or len(validated_data.get("analysis", "")) < 50
        ):
            try:
                # Recopilar datos disponibles para generar un análisis completo
                overall = validated_data.get("overall", "Neutral")
                vix = validated_data.get("vix", "N/A")
                sp500_trend = validated_data.get("sp500_trend", "N/A")
                tech_indicators = validated_data.get("technical_indicators", "N/A")

                prompt = f"""
                Como analista financiero experto, genera un análisis detallado del sentimiento de mercado
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
                6. NO incluir frases genéricas de introducción o cierre
                """

                generated_analysis = self.ai_expert.process_text(prompt, max_tokens=500)

                if generated_analysis and len(generated_analysis) > 100:
                    # Limpiar el análisis generado
                    generated_analysis = self._clean_text(generated_analysis)
                    validated_data["analysis"] = generated_analysis
                    logger.info("Análisis de sentimiento de mercado generado con IA")
                else:
                    # Si no se pudo generar un análisis, crear uno genérico pero informativo
                    validated_data["analysis"] = (
                        f"El mercado muestra un sentimiento {overall.lower()} con VIX en {vix} y tendencia {sp500_trend.lower()} en el S&P500."
                    )
                    logger.warning(
                        "No se pudo generar análisis con IA, usando genérico"
                    )
            except Exception as e:
                logger.error(f"Error generando análisis con IA: {str(e)}")
                # Asignar un análisis genérico en caso de error
                validated_data["analysis"] = (
                    f"Sentimiento de mercado: {validated_data.get('overall', 'Neutral')}"
                )

        # Asegurar que los indicadores técnicos estén presentes
        if not validated_data.get("technical_indicators"):
            validated_data["technical_indicators"] = (
                "No hay datos de indicadores técnicos disponibles"
            )

        # Asegurar que el volumen esté presente
        if not validated_data.get("volume"):
            validated_data["volume"] = "N/A"

        return validated_data

    def _is_english_text(self, text):
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
            r"\bthe\b",
            r"\band\b",
            r"\bof\b",
            r"\bto\b",
            r"\ba\b",
            r"\bin\b",
            r"\bthat\b",
            r"\bhave\b",
            r"\bI\b",
            r"\bit\b",
            r"\bfor\b",
            r"\bnot\b",
            r"\bon\b",
            r"\bwith\b",
            r"\bhe\b",
            r"\bas\b",
            r"\byou\b",
            r"\bdo\b",
            r"\bat\b",
            r"\bthis\b",
            r"\bbut\b",
            r"\bhis\b",
            r"\bby\b",
            r"\bfrom\b",
            r"\bthey\b",
            r"\bwe\b",
            r"\bsay\b",
            r"\bher\b",
            r"\bshe\b",
            r"\bor\b",
            r"\ban\b",
            r"\bwill\b",
            r"\bmy\b",
            r"\bone\b",
            r"\ball\b",
            r"\bwould\b",
            r"\bthere\b",
            r"\btheir\b",
            r"\bwhat\b",
            r"\bso\b",
            r"\bup\b",
            r"\bout\b",
            r"\bif\b",
            r"\babout\b",
            r"\bwho\b",
            r"\bget\b",
            r"\bwhich\b",
            r"\bgo\b",
            r"\bme\b",
            r"\bwhen\b",
            r"\bmake\b",
            r"\bcan\b",
            r"\blike\b",
            r"\btime\b",
            r"\bno\b",
            r"\bjust\b",
            r"\bhim\b",
            r"\bknow\b",
            r"\btake\b",
            r"\bpeople\b",
        ]

        # Contar palabras en inglés
        english_count = 0
        for word in english_words:
            if re.search(word, text.lower()):
                english_count += 1

        # Si hay más de 3 palabras en inglés, consideramos que el texto está en inglés
        return english_count > 3

    def _clean_text(self, text):
        """
        Limpia un texto eliminando comillas, saltos de línea y espacios extra

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
