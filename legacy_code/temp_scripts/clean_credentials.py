#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar credenciales expuestas en archivos de legacy_code
"""

import os
import re
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Credenciales a reemplazar
CREDENTIALS = {
    "localhost": "localhost",
    "db_user": "db_user",
    "db_password": "db_password",
    "inversoria_db": "inversoria_db",
    "smtp.example.com": "smtp.example.com",
    "info@example.com": "info@example.com",
    "InversorIA Pro <info@example.com>": "InversorIA Pro <info@example.com>"
}

def clean_file(file_path):
    """Limpia las credenciales de un archivo"""
    try:
        # Leer el contenido del archivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si hay credenciales
        has_credentials = False
        for credential in CREDENTIALS:
            if credential in content:
                has_credentials = True
                break
        
        if not has_credentials:
            logger.info(f"No se encontraron credenciales en {file_path}")
            return False
        
        # Reemplazar credenciales
        new_content = content
        for credential, replacement in CREDENTIALS.items():
            new_content = new_content.replace(credential, replacement)
        
        # Guardar el archivo modificado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Se limpiaron credenciales en {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error limpiando credenciales en {file_path}: {str(e)}")
        return False

def scan_directory(directory):
    """Escanea un directorio en busca de archivos Python y limpia credenciales"""
    cleaned_files = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if clean_file(file_path):
                    cleaned_files += 1
    
    return cleaned_files

def main():
    """Función principal"""
    logger.info("Iniciando limpieza de credenciales")
    
    # Limpiar archivos en legacy_code
    legacy_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cleaned = scan_directory(legacy_dir)
    
    logger.info(f"Se limpiaron credenciales en {cleaned} archivos")
    logger.info("Limpieza completada")

if __name__ == "__main__":
    main()
