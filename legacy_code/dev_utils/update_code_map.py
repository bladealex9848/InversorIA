#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar el mapa de código (code_map.json)
"""

import os
import re
import json
import ast
from typing import Dict, List, Any, Optional, Tuple

def extract_classes_and_functions(file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extrae clases y funciones de un archivo Python
    
    Args:
        file_path (str): Ruta al archivo Python
        
    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: Clases y funciones extraídas
    """
    classes = []
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Intentar parsear el archivo con ast
        try:
            tree = ast.parse(content)
            
            # Extraer clases
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "description": extract_docstring(node),
                        "start_line": node.lineno,
                        "end_line": find_end_line(content, node.lineno)
                    }
                    
                    # Extraer métodos de la clase
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "description": extract_docstring(item),
                                "start_line": item.lineno,
                                "end_line": find_end_line(content, item.lineno, item)
                            }
                            methods.append(method_info)
                    
                    if methods:
                        class_info["methods"] = methods
                        
                    classes.append(class_info)
                
                # Extraer funciones (solo las de nivel superior)
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    function_info = {
                        "name": node.name,
                        "description": extract_docstring(node),
                        "start_line": node.lineno,
                        "end_line": find_end_line(content, node.lineno, node)
                    }
                    functions.append(function_info)
                    
        except SyntaxError:
            # Si hay un error de sintaxis, usar expresiones regulares como fallback
            classes = extract_classes_with_regex(content)
            functions = extract_functions_with_regex(content)
            
    except Exception as e:
        print(f"Error procesando {file_path}: {str(e)}")
        
    return classes, functions

def extract_docstring(node: ast.AST) -> str:
    """
    Extrae el docstring de un nodo AST
    
    Args:
        node (ast.AST): Nodo AST
        
    Returns:
        str: Docstring extraído o descripción por defecto
    """
    if not node.body:
        return "Sin descripción disponible"
    
    first_node = node.body[0]
    if isinstance(first_node, ast.Expr) and isinstance(first_node.value, ast.Str):
        # Extraer la primera línea del docstring
        docstring = first_node.value.s.strip().split('\n')[0]
        return docstring
    
    return "Sin descripción disponible"

def find_end_line(content: str, start_line: int, node: Optional[ast.AST] = None) -> int:
    """
    Encuentra la línea final de una definición
    
    Args:
        content (str): Contenido del archivo
        start_line (int): Línea de inicio
        node (Optional[ast.AST]): Nodo AST
        
    Returns:
        int: Línea final
    """
    if node and hasattr(node, 'end_lineno') and node.end_lineno:
        return node.end_lineno
    
    lines = content.split('\n')
    
    # Buscar la siguiente definición de clase o función
    for i in range(start_line, len(lines)):
        if re.match(r'^(class|def)\s+', lines[i]):
            if i > start_line:
                return i - 1
    
    # Si no se encuentra, estimar basado en indentación
    indent_level = None
    for i in range(start_line, len(lines)):
        line = lines[i].rstrip()
        if not line:
            continue
            
        # Obtener nivel de indentación de la primera línea
        if indent_level is None:
            indent_level = len(line) - len(line.lstrip())
            continue
            
        # Si encontramos una línea con menor o igual indentación, es el final
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= indent_level and re.match(r'^(class|def)\s+', line.lstrip()):
            return i - 1
    
    # Si no se encuentra, devolver una estimación
    return start_line + 50

def extract_classes_with_regex(content: str) -> List[Dict[str, Any]]:
    """
    Extrae clases usando expresiones regulares
    
    Args:
        content (str): Contenido del archivo
        
    Returns:
        List[Dict[str, Any]]: Clases extraídas
    """
    classes = []
    class_pattern = r'class\s+(\w+)(?:\(.*?\))?:'
    
    for match in re.finditer(class_pattern, content):
        class_name = match.group(1)
        start_line = content[:match.start()].count('\n') + 1
        
        # Estimar la línea final
        end_line = start_line + 50  # Estimación aproximada
        
        classes.append({
            "name": class_name,
            "description": "Clase extraída con regex",
            "start_line": start_line,
            "end_line": end_line
        })
    
    return classes

def extract_functions_with_regex(content: str) -> List[Dict[str, Any]]:
    """
    Extrae funciones usando expresiones regulares
    
    Args:
        content (str): Contenido del archivo
        
    Returns:
        List[Dict[str, Any]]: Funciones extraídas
    """
    functions = []
    function_pattern = r'^def\s+(\w+)\s*\('
    
    for match in re.finditer(function_pattern, content, re.MULTILINE):
        function_name = match.group(1)
        start_line = content[:match.start()].count('\n') + 1
        
        # Estimar la línea final
        end_line = start_line + 20  # Estimación aproximada
        
        functions.append({
            "name": function_name,
            "description": "Función extraída con regex",
            "start_line": start_line,
            "end_line": end_line
        })
    
    return functions

def update_code_map(output_file: str = 'code_map.json'):
    """
    Actualiza el mapa de código
    
    Args:
        output_file (str): Archivo de salida
    """
    code_map = {
        "main_files": {},
        "auxiliary_files": {},
        "pages": {},
        "components": {},
        "utils": {}
    }
    
    # Procesar archivo principal
    main_file = '📊_InversorIA_Pro.py'
    if os.path.exists(main_file):
        classes, functions = extract_classes_and_functions(main_file)
        code_map["main_files"][main_file] = {
            "classes": classes,
            "functions": functions
        }
        print(f"Procesado archivo principal: {main_file}")
    
    # Procesar archivos auxiliares
    auxiliary_files = [
        'market_utils.py', 'technical_analysis.py', 'market_scanner.py', 
        'ai_utils.py', 'database_utils.py', 'trading_analyzer.py',
        'yahoo_finance_scraper.py', 'news_processor.py', 'news_sentiment_analyzer.py',
        'signal_analyzer.py', 'signal_manager.py', 'market_data_engine.py',
        'market_data_manager.py', 'market_data_processor.py', 'market_data_throttling.py',
        'enhanced_market_data.py', 'enhanced_market_scanner.py', 'enhanced_market_scanner_fixed.py',
        'trading_dashboard.py', 'company_data.py', 'authenticator.py'
    ]
    
    for file in auxiliary_files:
        if os.path.exists(file):
            classes, functions = extract_classes_and_functions(file)
            code_map["auxiliary_files"][file] = {
                "classes": classes,
                "functions": functions
            }
            print(f"Procesado archivo auxiliar: {file}")
    
    # Procesar páginas
    pages_dir = 'pages'
    if os.path.exists(pages_dir) and os.path.isdir(pages_dir):
        for file in os.listdir(pages_dir):
            if file.endswith('.py'):
                file_path = os.path.join(pages_dir, file)
                classes, functions = extract_classes_and_functions(file_path)
                code_map["pages"][file] = {
                    "classes": classes,
                    "functions": functions
                }
                print(f"Procesada página: {file}")
    
    # Procesar componentes
    components_dir = 'components'
    if os.path.exists(components_dir) and os.path.isdir(components_dir):
        for file in os.listdir(components_dir):
            if file.endswith('.py'):
                file_path = os.path.join(components_dir, file)
                classes, functions = extract_classes_and_functions(file_path)
                code_map["components"][file] = {
                    "classes": classes,
                    "functions": functions
                }
                print(f"Procesado componente: {file}")
    
    # Procesar utilidades
    utils_dir = 'utils'
    if os.path.exists(utils_dir) and os.path.isdir(utils_dir):
        for file in os.listdir(utils_dir):
            if file.endswith('.py'):
                file_path = os.path.join(utils_dir, file)
                classes, functions = extract_classes_and_functions(file_path)
                code_map["utils"][file] = {
                    "classes": classes,
                    "functions": functions
                }
                print(f"Procesada utilidad: {file}")
    
    # Eliminar secciones vacías
    for section in list(code_map.keys()):
        if not code_map[section]:
            del code_map[section]
    
    # Guardar el mapa de código
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(code_map, f, ensure_ascii=False, indent=2)
    
    print(f"Mapa de código actualizado y guardado en {output_file}")

if __name__ == "__main__":
    update_code_map()
