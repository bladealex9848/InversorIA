"""
Script para corregir el error de procesamiento de JSON de sentimiento
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

def fix_json_processing():
    """Corrige el error de procesamiento de JSON de sentimiento"""
    # Buscar archivos que procesan JSON de sentimiento
    files_to_check = [
        "market_data_manager.py",
        "database_utils.py",
        "📊_InversorIA_Pro.py",
        "pages/7_🔔_Notificaciones.py"
    ]
    
    fixed_files = 0
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            logger.warning(f"Archivo {file_path} no encontrado")
            continue
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Buscar patrones de procesamiento de JSON
            json_processing_patterns = [
                (r'json\.loads\(([^)]+)\)', r'try:\n    json.loads(\1)\nexcept json.JSONDecodeError as e:\n    logger.warning(f"Error decodificando JSON: {str(e)}")\n    {}'),
                (r'(\w+)\s*=\s*json\.loads\(([^)]+)\)', r'try:\n    \1 = json.loads(\2)\nexcept json.JSONDecodeError as e:\n    logger.warning(f"Error decodificando JSON: {str(e)}")\n    \1 = {}'),
                (r'logger\.warning\(f"Error procesando JSON de sentimiento: {str\(e\)}"\)', r'logger.warning(f"Error procesando JSON de sentimiento: {str(e)}")\n            sentiment_data = {}')
            ]
            
            modified = False
            for pattern, replacement in json_processing_patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    modified = True
            
            if modified:
                # Guardar el archivo modificado
                with open(file_path, 'w') as f:
                    f.write(content)
                
                logger.info(f"Archivo {file_path} modificado correctamente")
                fixed_files += 1
            else:
                logger.info(f"No se encontraron patrones para modificar en {file_path}")
        
        except Exception as e:
            logger.error(f"Error modificando {file_path}: {str(e)}")
    
    return fixed_files

def add_json_validation_function():
    """Añade una función de validación de JSON a un archivo de utilidades"""
    utils_file = "utils/data_utils.py"
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(utils_file), exist_ok=True)
    
    # Verificar si el archivo existe
    if not os.path.exists(utils_file):
        # Crear el archivo si no existe
        with open(utils_file, 'w') as f:
            f.write("""\"\"\"
Utilidades para procesamiento de datos
\"\"\"

import json
import logging

logger = logging.getLogger(__name__)

def safe_json_loads(json_str, default=None):
    \"\"\"
    Carga un string JSON de forma segura
    
    Args:
        json_str (str): String JSON a cargar
        default (any, optional): Valor por defecto si hay error. Por defecto es None.
        
    Returns:
        any: Objeto JSON cargado o valor por defecto
    \"\"\"
    if default is None:
        default = {}
    
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Error decodificando JSON: {str(e)}")
        return default
    except Exception as e:
        logger.warning(f"Error procesando JSON: {str(e)}")
        return default
""")
        logger.info(f"Archivo {utils_file} creado correctamente")
    else:
        # Verificar si la función ya existe
        with open(utils_file, 'r') as f:
            content = f.read()
        
        if 'def safe_json_loads' not in content:
            # Añadir la función al final del archivo
            with open(utils_file, 'a') as f:
                f.write("""

def safe_json_loads(json_str, default=None):
    \"\"\"
    Carga un string JSON de forma segura
    
    Args:
        json_str (str): String JSON a cargar
        default (any, optional): Valor por defecto si hay error. Por defecto es None.
        
    Returns:
        any: Objeto JSON cargado o valor por defecto
    \"\"\"
    if default is None:
        default = {}
    
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Error decodificando JSON: {str(e)}")
        return default
    except Exception as e:
        logger.warning(f"Error procesando JSON: {str(e)}")
        return default
""")
            logger.info(f"Función safe_json_loads añadida a {utils_file}")
        else:
            logger.info(f"La función safe_json_loads ya existe en {utils_file}")
    
    return True

def main():
    """Función principal"""
    logger.info("Iniciando corrección de error de procesamiento de JSON de sentimiento")
    
    # Corregir el procesamiento de JSON
    fixed_files = fix_json_processing()
    
    # Añadir función de validación de JSON
    add_json_validation_function()
    
    logger.info(f"Se han corregido {fixed_files} archivos")
    logger.info("Corrección completada")

if __name__ == "__main__":
    main()
