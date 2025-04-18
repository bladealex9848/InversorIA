#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from datetime import datetime
from signal_analyzer import RealTimeSignalAnalyzer
from database_utils import save_market_sentiment, DatabaseManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def test_market_sentiment_generation():
    """Prueba la generación y guardado del sentimiento de mercado diario"""
    try:
        logger.info("Iniciando prueba de generación de sentimiento de mercado")

        # Paso 1: Generar sentimiento de mercado usando RealTimeSignalAnalyzer
        analyzer = RealTimeSignalAnalyzer()
        sentiment_data = analyzer.get_real_time_market_sentiment()

        # Corregir el campo vix si es 'N/A'
        if sentiment_data.get("vix") == "N/A":
            sentiment_data["vix"] = 0.0  # Usar 0.0 como valor por defecto

        logger.info(f"Sentimiento generado: {sentiment_data}")

        # Paso 2: Guardar el sentimiento en la base de datos
        sentiment_id = save_market_sentiment(sentiment_data)

        if sentiment_id:
            logger.info(f"Sentimiento guardado correctamente con ID: {sentiment_id}")

            # Paso 3: Verificar que se guardó correctamente
            db = DatabaseManager()
            result = db.execute_query(
                f"SELECT * FROM market_sentiment WHERE id = {sentiment_id}"
            )

            if result and len(result) > 0:
                logger.info(f"Registro verificado en la base de datos: {result[0]}")

                # Paso 4: Intentar guardar otro registro para el mismo día
                logger.info("Intentando guardar otro registro para el mismo día...")
                second_id = save_market_sentiment(sentiment_data)

                if second_id == sentiment_id:
                    logger.info(
                        f"Correcto: No se guardó un segundo registro, se devolvió el ID existente: {second_id}"
                    )
                else:
                    logger.error(
                        f"Error: Se guardó un segundo registro con ID: {second_id}"
                    )
            else:
                logger.error(f"Error: No se encontró el registro con ID {sentiment_id}")
        else:
            logger.error("Error: No se pudo guardar el sentimiento")

    except Exception as e:
        logger.error(f"Error en la prueba: {str(e)}")


if __name__ == "__main__":
    test_market_sentiment_generation()
