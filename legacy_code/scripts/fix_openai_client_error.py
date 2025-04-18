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
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def fix_client_variable_issue():
    """
    Corrige el problema con la variable 'client' en los archivos de la aplicación
    """
    try:
        # Lista de archivos a revisar
        files_to_check = [
            "pages/2_🤖_Inversor_Bot.py",
            "pages/4_📈_MarketIntel_Options_Analyzer.py",
            "pages/5_📈_Technical_Expert_Analyzer.py",
            "ai_utils.py"
        ]
        
        fixed_files = []
        
        for file_path in files_to_check:
            if not os.path.exists(file_path):
                logger.warning(f"El archivo {file_path} no existe")
                continue
                
            logger.info(f"Revisando archivo: {file_path}")
            
            # Leer el contenido del archivo
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Buscar patrones problemáticos
            if "client = openai" in content:
                logger.info(f"Encontrado patrón problemático 'client = openai' en {file_path}")
                
                # Reemplazar el patrón problemático
                new_content = content.replace(
                    "client = openai",
                    "client = openai.OpenAI(api_key=OPENAI_API_KEY)"
                )
                
                # Guardar el archivo modificado
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                logger.info(f"Archivo {file_path} corregido")
                fixed_files.append(file_path)
            
            # Buscar otros patrones problemáticos
            if "client.api_key = " in content:
                logger.info(f"Encontrado patrón problemático 'client.api_key = ' en {file_path}")
                
                # Reemplazar el patrón problemático
                new_content = content.replace(
                    "client.api_key = OPENAI_API_KEY",
                    "client = openai.OpenAI(api_key=OPENAI_API_KEY)"
                )
                
                # Guardar el archivo modificado
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                logger.info(f"Archivo {file_path} corregido")
                if file_path not in fixed_files:
                    fixed_files.append(file_path)
        
        # Verificar si se corrigieron archivos
        if fixed_files:
            logger.info(f"Se corrigieron {len(fixed_files)} archivos: {', '.join(fixed_files)}")
            return True
        else:
            logger.warning("No se encontraron patrones problemáticos en los archivos revisados")
            return False
            
    except Exception as e:
        logger.error(f"Error en fix_client_variable_issue: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if fix_client_variable_issue():
        logger.info("Corrección aplicada con éxito")
        sys.exit(0)
    else:
        logger.error("No se pudo aplicar la corrección")
        sys.exit(1)
