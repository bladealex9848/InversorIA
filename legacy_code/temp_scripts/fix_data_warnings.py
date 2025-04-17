"""
Script para corregir las advertencias de datos insuficientes
"""

import logging
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def fix_market_utils_warnings():
    """Corrige las advertencias en market_utils.py"""
    try:
        with open("market_utils.py", "r") as file:
            content = file.read()
        
        # Buscar la advertencia específica en TechnicalAnalyzer.calculate_indicators
        warning_pattern = r'logger\.warning\(\s*f"⚠️ Datos insuficientes para calcular indicadores: solo {len\(df\)} filas disponibles\. Se necesitan al menos 20 filas\."\s*\)'
        
        if re.search(warning_pattern, content):
            logger.info("Encontrada advertencia de datos insuficientes en TechnicalAnalyzer.calculate_indicators")
            
            # Modificar para mostrar la advertencia solo una vez
            modified_content = re.sub(
                warning_pattern,
                'if not hasattr(self, "_warning_shown"):\n                    logger.warning(f"⚠️ Datos insuficientes para calcular indicadores: solo {len(df)} filas disponibles. Se necesitan al menos 20 filas.")\n                    self._warning_shown = True',
                content
            )
            
            # Buscar otras advertencias similares
            other_warning_pattern = r'logger\.warning\(\s*f"⚠️ Datos insuficientes para (\w+) en timeframe (\w+)\. Usando datos sintéticos\."\s*\)'
            
            if re.search(other_warning_pattern, content):
                logger.info("Encontradas otras advertencias de datos insuficientes")
                
                # Modificar para mostrar estas advertencias solo una vez por símbolo y timeframe
                modified_content = re.sub(
                    other_warning_pattern,
                    r'if not hasattr(fetch_market_data, "_warnings"):\n            fetch_market_data._warnings = set()\n        warning_key = f"{symbol}_{timeframe}"\n        if warning_key not in fetch_market_data._warnings:\n            logger.warning(f"⚠️ Datos insuficientes para \1 en timeframe \2. Usando datos sintéticos.")\n            fetch_market_data._warnings.add(warning_key)',
                    modified_content
                )
            
            # Guardar el archivo modificado
            with open("market_utils.py", "w") as file:
                file.write(modified_content)
            
            logger.info("Archivo market_utils.py modificado correctamente")
            return True
        else:
            logger.warning("No se encontró el patrón de advertencia en market_utils.py")
            return False
    
    except Exception as e:
        logger.error(f"Error modificando market_utils.py: {str(e)}")
        return False

def fix_fetch_market_data_warnings():
    """Corrige las advertencias en la función fetch_market_data"""
    try:
        with open("market_utils.py", "r") as file:
            content = file.read()
        
        # Buscar la función fetch_market_data
        if "def fetch_market_data" in content:
            logger.info("Encontrada función fetch_market_data")
            
            # Buscar advertencias específicas
            warning_pattern = r'logger\.warning\(\s*f"⚠️ Datos insuficientes para {symbol} en timeframe {timeframe}\. Usando datos sintéticos\."\s*\)'
            
            if re.search(warning_pattern, content):
                logger.info("Encontrada advertencia de datos insuficientes en fetch_market_data")
                
                # Modificar para mostrar la advertencia solo una vez por símbolo y timeframe
                modified_content = re.sub(
                    warning_pattern,
                    r'if not hasattr(fetch_market_data, "_symbol_warnings"):\n                fetch_market_data._symbol_warnings = set()\n            warning_key = f"{symbol}_{timeframe}"\n            if warning_key not in fetch_market_data._symbol_warnings:\n                logger.warning(f"⚠️ Datos insuficientes para {symbol} en timeframe {timeframe}. Usando datos sintéticos.")\n                fetch_market_data._symbol_warnings.add(warning_key)',
                    content
                )
                
                # Guardar el archivo modificado
                with open("market_utils.py", "w") as file:
                    file.write(modified_content)
                
                logger.info("Advertencias en fetch_market_data modificadas correctamente")
                return True
            else:
                logger.warning("No se encontró el patrón de advertencia en fetch_market_data")
                return False
        else:
            logger.warning("No se encontró la función fetch_market_data")
            return False
    
    except Exception as e:
        logger.error(f"Error modificando advertencias en fetch_market_data: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("Iniciando corrección de advertencias de datos insuficientes")
    
    # Corregir advertencias en TechnicalAnalyzer.calculate_indicators
    fixed_technical_analyzer = fix_market_utils_warnings()
    
    # Corregir advertencias en fetch_market_data
    fixed_fetch_market_data = fix_fetch_market_data_warnings()
    
    if fixed_technical_analyzer or fixed_fetch_market_data:
        logger.info("Se han corregido las advertencias de datos insuficientes")
    else:
        logger.warning("No se han podido corregir las advertencias de datos insuficientes")
    
    logger.info("Corrección completada")

if __name__ == "__main__":
    main()
