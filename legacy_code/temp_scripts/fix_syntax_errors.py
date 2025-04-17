"""
Script para corregir errores de sintaxis en el archivo principal
"""

import logging
import re
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def fix_syntax_errors():
    """Corrige errores de sintaxis en el archivo principal"""
    file_path = "📊_InversorIA_Pro.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Corregir error de sintaxis en la línea 7938-7944
        pattern = r'improved_data = try:\s*json\.loads\(\s*improved_sentiment\s*\)\s*except json\.JSONDecodeError as e:\s*logger\.warning\(f"Error decodificando JSON: {str\(e\)}"\)\s*{}'
        replacement = """try:
    improved_data = json.loads(improved_sentiment)
except json.JSONDecodeError as e:
    logger.warning(f"Error decodificando JSON: {str(e)}")
    improved_data = {}"""
        
        # Usar expresión regular para encontrar y reemplazar el patrón
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            logger.info("Corregido error de sintaxis en la línea 7938-7944")
        
        # Corregir error de sintaxis en la línea 6265
        pattern = r'st\.dataframe\(test_data\.tail\(3\.astype\(str\)\), use_container_width=True\)'
        replacement = 'st.dataframe(test_data.tail(3).astype(str), use_container_width=True)'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            logger.info("Corregido error de sintaxis en la línea 6265")
        
        # Guardar el archivo corregido
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Archivo {file_path} corregido correctamente")
        return True
    
    except Exception as e:
        logger.error(f"Error corrigiendo errores de sintaxis: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("Iniciando corrección de errores de sintaxis")
    
    # Corregir errores de sintaxis
    fixed = fix_syntax_errors()
    
    if fixed:
        logger.info("Se han corregido los errores de sintaxis")
    else:
        logger.warning("No se han podido corregir los errores de sintaxis")
    
    logger.info("Corrección completada")

if __name__ == "__main__":
    main()
