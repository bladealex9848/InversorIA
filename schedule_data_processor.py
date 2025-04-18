#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para programar la ejecución periódica del procesador de calidad de datos.
Este script ejecuta database_quality_processor.py cada cierto tiempo.
"""

import logging
import sys
import os
import time
import subprocess
import argparse
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_data_processor():
    """
    Ejecuta el script database_quality_processor.py

    Returns:
        bool: True si se ejecutó correctamente, False en caso contrario
    """
    try:
        logger.info("Ejecutando database_quality_processor.py...")

        # Obtener la ruta del script
        script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "database_quality_processor.py"
        )

        # Verificar que el script existe
        if not os.path.exists(script_path):
            logger.error(f"El script {script_path} no existe")
            return False

        # Ejecutar el script
        result = subprocess.run(
            [sys.executable, script_path], capture_output=True, text=True
        )

        # Verificar resultado
        if result.returncode == 0:
            logger.info("Script ejecutado correctamente")
            logger.info(f"Salida: {result.stdout}")
            return True
        else:
            logger.error(f"Error ejecutando script: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error ejecutando database_quality_processor.py: {str(e)}")
        return False


def main():
    """Función principal"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description="Programador para database_quality_processor.py"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="Intervalo de ejecución en segundos (por defecto: 3600 = 1 hora)",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=0,
        help="Número máximo de ejecuciones (0 = infinito)",
    )
    parser.add_argument(
        "--run-once", action="store_true", help="Ejecutar una sola vez y salir"
    )

    # Parsear argumentos
    args = parser.parse_args()

    # Mostrar configuración
    if args.run_once:
        logger.info("Modo de ejecución única")
    else:
        logger.info(f"Intervalo de ejecución: {args.interval} segundos")
        if args.max_runs > 0:
            logger.info(f"Número máximo de ejecuciones: {args.max_runs}")
        else:
            logger.info("Ejecución continua (sin límite)")

    # Ejecutar una vez si se especifica
    if args.run_once:
        run_data_processor()
        return

    # Ejecutar periódicamente
    run_count = 0
    try:
        while True:
            # Ejecutar el procesador
            success = run_data_processor()
            run_count += 1

            # Verificar si se alcanzó el número máximo de ejecuciones
            if args.max_runs > 0 and run_count >= args.max_runs:
                logger.info(
                    f"Se alcanzó el número máximo de ejecuciones ({args.max_runs})"
                )
                break

            # Calcular próxima ejecución
            next_run = datetime.now() + timedelta(seconds=args.interval)
            logger.info(f"Próxima ejecución: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

            # Esperar hasta la próxima ejecución
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Ejecución interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")


if __name__ == "__main__":
    main()
