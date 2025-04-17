"""
Script para corregir el error de serialización de DataFrame a Arrow
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

def find_dataframe_displays():
    """Busca archivos que muestran DataFrames en Streamlit"""
    dataframe_files = []
    
    # Patrones para buscar
    patterns = [
        r'st\.dataframe\(',
        r'st\.table\(',
        r'st\.write\(\s*.*?df',
        r'st\.write\(\s*pd\.DataFrame'
    ]
    
    # Buscar en archivos .py
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                        # Verificar si algún patrón coincide
                        for pattern in patterns:
                            if re.search(pattern, content):
                                dataframe_files.append(file_path)
                                break
                except Exception as e:
                    logger.error(f"Error leyendo {file_path}: {str(e)}")
    
    return dataframe_files

def fix_dataframe_serialization(file_path):
    """Corrige la serialización de DataFrames en un archivo"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Buscar patrones de visualización de DataFrames
        df_display_patterns = [
            (r'(st\.dataframe\()([^,\)]+)(\))', r'\1\2.astype(str)\3'),
            (r'(st\.dataframe\()([^,\)]+)(,.*?\))', r'\1\2.astype(str)\3'),
            (r'(st\.table\()([^,\)]+)(\))', r'\1\2.astype(str)\3'),
            (r'(st\.table\()([^,\)]+)(,.*?\))', r'\1\2.astype(str)\3'),
            (r'(st\.write\()([^,\)]+df[^,\)]*?)(\))', r'\1\2.astype(str)\3'),
            (r'(st\.write\()([^,\)]*?pd\.DataFrame[^,\)]*?)(\))', r'\1\2.astype(str)\3')
        ]
        
        modified = False
        for pattern, replacement in df_display_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True
        
        if modified:
            # Guardar el archivo modificado
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Archivo {file_path} modificado correctamente")
            return True
        else:
            logger.info(f"No se encontraron patrones para modificar en {file_path}")
            return False
    
    except Exception as e:
        logger.error(f"Error modificando {file_path}: {str(e)}")
        return False

def add_dataframe_conversion_function():
    """Añade una función de conversión de DataFrames a un archivo de utilidades"""
    utils_file = "visualization_utils.py"
    
    # Verificar si el archivo existe
    if not os.path.exists(utils_file):
        # Crear el archivo si no existe
        with open(utils_file, 'w') as f:
            f.write("""\"\"\"
Utilidades para visualización de datos
\"\"\"

import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

def safe_dataframe(df):
    \"\"\"
    Convierte un DataFrame a un formato seguro para Streamlit
    
    Args:
        df (pd.DataFrame): DataFrame a convertir
        
    Returns:
        pd.DataFrame: DataFrame convertido
    \"\"\"
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    
    # Hacer una copia para evitar modificar el original
    safe_df = df.copy()
    
    # Convertir columnas problemáticas a string
    for col in safe_df.columns:
        # Verificar si la columna contiene tipos mixtos
        if safe_df[col].dtype == 'object':
            safe_df[col] = safe_df[col].astype(str)
        
        # Convertir fechas a string
        elif pd.api.types.is_datetime64_any_dtype(safe_df[col]):
            safe_df[col] = safe_df[col].astype(str)
    
    return safe_df
""")
        logger.info(f"Archivo {utils_file} creado correctamente")
    else:
        # Verificar si la función ya existe
        with open(utils_file, 'r') as f:
            content = f.read()
        
        if 'def safe_dataframe' not in content:
            # Añadir la función al final del archivo
            with open(utils_file, 'a') as f:
                f.write("""

def safe_dataframe(df):
    \"\"\"
    Convierte un DataFrame a un formato seguro para Streamlit
    
    Args:
        df (pd.DataFrame): DataFrame a convertir
        
    Returns:
        pd.DataFrame: DataFrame convertido
    \"\"\"
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    
    # Hacer una copia para evitar modificar el original
    safe_df = df.copy()
    
    # Convertir columnas problemáticas a string
    for col in safe_df.columns:
        # Verificar si la columna contiene tipos mixtos
        if safe_df[col].dtype == 'object':
            safe_df[col] = safe_df[col].astype(str)
        
        # Convertir fechas a string
        elif pd.api.types.is_datetime64_any_dtype(safe_df[col]):
            safe_df[col] = safe_df[col].astype(str)
    
    return safe_df
""")
            logger.info(f"Función safe_dataframe añadida a {utils_file}")
        else:
            logger.info(f"La función safe_dataframe ya existe en {utils_file}")
    
    return True

def main():
    """Función principal"""
    logger.info("Iniciando corrección de error de serialización de DataFrame a Arrow")
    
    # Buscar archivos que muestran DataFrames
    dataframe_files = find_dataframe_displays()
    logger.info(f"Se encontraron {len(dataframe_files)} archivos que muestran DataFrames")
    
    # Corregir la serialización de DataFrames en cada archivo
    fixed_files = 0
    for file_path in dataframe_files:
        if fix_dataframe_serialization(file_path):
            fixed_files += 1
    
    # Añadir función de conversión de DataFrames
    add_dataframe_conversion_function()
    
    logger.info(f"Se han corregido {fixed_files} archivos")
    logger.info("Corrección completada")

if __name__ == "__main__":
    main()
