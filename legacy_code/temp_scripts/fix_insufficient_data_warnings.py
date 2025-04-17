"""
Script para reducir las advertencias de datos insuficientes para calcular indicadores
"""

import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def modify_market_utils():
    """Modifica el archivo market_utils.py para reducir las advertencias de datos insuficientes"""
    try:
        with open("market_utils.py", "r") as file:
            content = file.read()
            
            # Buscar la función que genera las advertencias
            if "def validate_market_data" in content:
                logger.info("Función validate_market_data encontrada en market_utils.py")
                
                # Buscar el código que genera las advertencias
                warning_code = "logger.warning(f\"⚠️ Datos insuficientes para calcular indicadores: solo {len(data)} filas disponibles. Se necesitan al menos {min_rows} filas.\")"
                
                if warning_code in content:
                    logger.info("Código de advertencia encontrado en validate_market_data")
                    
                    # Modificar el código para reducir las advertencias
                    modified_content = content.replace(
                        warning_code,
                        "if not hasattr(validate_market_data, 'warning_shown'):\n        logger.warning(f\"⚠️ Datos insuficientes para calcular indicadores: solo {len(data)} filas disponibles. Se necesitan al menos {min_rows} filas.\")\n        validate_market_data.warning_shown = True"
                    )
                    
                    # Guardar el archivo modificado
                    with open("market_utils.py", "w") as file:
                        file.write(modified_content)
                    
                    logger.info("Archivo market_utils.py modificado correctamente para reducir advertencias")
                    return True
                else:
                    logger.warning("Código de advertencia no encontrado en validate_market_data")
            else:
                logger.warning("Función validate_market_data no encontrada en market_utils.py")
            
            # Buscar otras funciones que generan advertencias similares
            warning_patterns = [
                "logger.warning(f\"⚠️ Datos insuficientes para {symbol} en timeframe {timeframe}. Usando datos sintéticos.\")",
                "logger.warning(f\"⚠️ Datos insuficientes para calcular"
            ]
            
            modified = False
            for pattern in warning_patterns:
                if pattern in content:
                    logger.info(f"Patrón de advertencia encontrado: {pattern[:50]}...")
                    
                    # Modificar el patrón para reducir las advertencias
                    modified_content = content.replace(
                        pattern,
                        f"if not hasattr(fetch_market_data, 'warning_shown_{pattern[:10].replace(' ', '_')}_count'):\n        fetch_market_data.warning_shown_{pattern[:10].replace(' ', '_')}_count = 0\n    fetch_market_data.warning_shown_{pattern[:10].replace(' ', '_')}_count += 1\n    if fetch_market_data.warning_shown_{pattern[:10].replace(' ', '_')}_count <= 1:\n        {pattern}"
                    )
                    
                    # Guardar el archivo modificado
                    with open("market_utils.py", "w") as file:
                        file.write(modified_content)
                    
                    content = modified_content
                    modified = True
            
            if modified:
                logger.info("Archivo market_utils.py modificado correctamente para reducir advertencias adicionales")
                return True
            
            return False
    except Exception as e:
        logger.error(f"Error modificando market_utils.py: {str(e)}")
        return False

def modify_technical_analysis():
    """Modifica el archivo technical_analysis.py para reducir las advertencias de datos insuficientes"""
    try:
        if not os.path.exists("technical_analysis.py"):
            logger.warning("Archivo technical_analysis.py no encontrado")
            return False
            
        with open("technical_analysis.py", "r") as file:
            content = file.read()
            
            # Buscar patrones de advertencia
            warning_patterns = [
                "logger.warning(f\"⚠️ Datos insuficientes para calcular",
                "logger.warning(\"⚠️ Datos insuficientes para"
            ]
            
            modified = False
            for pattern in warning_patterns:
                if pattern in content:
                    logger.info(f"Patrón de advertencia encontrado en technical_analysis.py: {pattern[:50]}...")
                    
                    # Modificar el patrón para reducir las advertencias
                    modified_content = content.replace(
                        pattern,
                        f"if not hasattr(detect_support_resistance, 'warning_shown_{pattern[:10].replace(' ', '_')}_count'):\n        detect_support_resistance.warning_shown_{pattern[:10].replace(' ', '_')}_count = 0\n    detect_support_resistance.warning_shown_{pattern[:10].replace(' ', '_')}_count += 1\n    if detect_support_resistance.warning_shown_{pattern[:10].replace(' ', '_')}_count <= 1:\n        {pattern}"
                    )
                    
                    # Guardar el archivo modificado
                    with open("technical_analysis.py", "w") as file:
                        file.write(modified_content)
                    
                    content = modified_content
                    modified = True
            
            if modified:
                logger.info("Archivo technical_analysis.py modificado correctamente para reducir advertencias")
                return True
            else:
                logger.warning("No se encontraron patrones de advertencia en technical_analysis.py")
                return False
    except Exception as e:
        logger.error(f"Error modificando technical_analysis.py: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("Iniciando corrección de advertencias de datos insuficientes")
    
    # Modificar market_utils.py
    modified_market_utils = modify_market_utils()
    
    # Modificar technical_analysis.py
    modified_technical_analysis = modify_technical_analysis()
    
    if modified_market_utils or modified_technical_analysis:
        logger.info("Se han reducido las advertencias de datos insuficientes")
    else:
        logger.warning("No se han podido reducir las advertencias de datos insuficientes")
    
    logger.info("Corrección completada")

if __name__ == "__main__":
    main()
