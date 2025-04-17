#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar un inventario de funciones en formato Markdown
"""

import json
import os
from typing import Dict, List, Any

def generate_function_inventory(code_map_file: str = 'code_map.json', output_file: str = 'inventario_funciones.md'):
    """
    Genera un inventario de funciones en formato Markdown
    
    Args:
        code_map_file (str): Archivo con el mapa de código
        output_file (str): Archivo de salida
    """
    # Cargar el mapa de código
    with open(code_map_file, 'r', encoding='utf-8') as f:
        code_map = json.load(f)
    
    # Iniciar el contenido del archivo Markdown
    content = "# Inventario de Funciones y Clases\n\n"
    content += "Este documento contiene un inventario de todas las funciones y clases del proyecto.\n\n"
    
    # Procesar archivos principales
    if "main_files" in code_map:
        content += "## Archivos Principales\n\n"
        for file, data in code_map["main_files"].items():
            content += f"### {file}\n\n"
            
            # Clases
            if "classes" in data and data["classes"]:
                content += "#### Clases\n\n"
                content += "| Clase | Descripción | Líneas |\n"
                content += "|-------|-------------|--------|\n"
                
                for cls in data["classes"]:
                    content += f"| `{cls['name']}` | {cls['description']} | {cls['start_line']}-{cls['end_line']} |\n"
                
                content += "\n"
                
                # Métodos de clases
                for cls in data["classes"]:
                    if "methods" in cls and cls["methods"]:
                        content += f"##### Métodos de {cls['name']}\n\n"
                        content += "| Método | Descripción | Líneas |\n"
                        content += "|--------|-------------|--------|\n"
                        
                        for method in cls["methods"]:
                            content += f"| `{method['name']}` | {method['description']} | {method['start_line']}-{method['end_line']} |\n"
                        
                        content += "\n"
            
            # Funciones
            if "functions" in data and data["functions"]:
                content += "#### Funciones\n\n"
                content += "| Función | Descripción | Líneas |\n"
                content += "|---------|-------------|--------|\n"
                
                for func in data["functions"]:
                    content += f"| `{func['name']}` | {func['description']} | {func['start_line']}-{func['end_line']} |\n"
                
                content += "\n"
    
    # Procesar archivos auxiliares
    if "auxiliary_files" in code_map:
        content += "## Archivos Auxiliares\n\n"
        for file, data in code_map["auxiliary_files"].items():
            content += f"### {file}\n\n"
            
            # Clases
            if "classes" in data and data["classes"]:
                content += "#### Clases\n\n"
                content += "| Clase | Descripción | Líneas |\n"
                content += "|-------|-------------|--------|\n"
                
                for cls in data["classes"]:
                    content += f"| `{cls['name']}` | {cls['description']} | {cls['start_line']}-{cls['end_line']} |\n"
                
                content += "\n"
                
                # Métodos de clases
                for cls in data["classes"]:
                    if "methods" in cls and cls["methods"]:
                        content += f"##### Métodos de {cls['name']}\n\n"
                        content += "| Método | Descripción | Líneas |\n"
                        content += "|--------|-------------|--------|\n"
                        
                        for method in cls["methods"]:
                            content += f"| `{method['name']}` | {method['description']} | {method['start_line']}-{method['end_line']} |\n"
                        
                        content += "\n"
            
            # Funciones
            if "functions" in data and data["functions"]:
                content += "#### Funciones\n\n"
                content += "| Función | Descripción | Líneas |\n"
                content += "|---------|-------------|--------|\n"
                
                for func in data["functions"]:
                    content += f"| `{func['name']}` | {func['description']} | {func['start_line']}-{func['end_line']} |\n"
                
                content += "\n"
    
    # Procesar páginas
    if "pages" in code_map:
        content += "## Páginas\n\n"
        for file, data in code_map["pages"].items():
            content += f"### {file}\n\n"
            
            # Clases
            if "classes" in data and data["classes"]:
                content += "#### Clases\n\n"
                content += "| Clase | Descripción | Líneas |\n"
                content += "|-------|-------------|--------|\n"
                
                for cls in data["classes"]:
                    content += f"| `{cls['name']}` | {cls['description']} | {cls['start_line']}-{cls['end_line']} |\n"
                
                content += "\n"
                
                # Métodos de clases
                for cls in data["classes"]:
                    if "methods" in cls and cls["methods"]:
                        content += f"##### Métodos de {cls['name']}\n\n"
                        content += "| Método | Descripción | Líneas |\n"
                        content += "|--------|-------------|--------|\n"
                        
                        for method in cls["methods"]:
                            content += f"| `{method['name']}` | {method['description']} | {method['start_line']}-{method['end_line']} |\n"
                        
                        content += "\n"
            
            # Funciones
            if "functions" in data and data["functions"]:
                content += "#### Funciones\n\n"
                content += "| Función | Descripción | Líneas |\n"
                content += "|---------|-------------|--------|\n"
                
                for func in data["functions"]:
                    content += f"| `{func['name']}` | {func['description']} | {func['start_line']}-{func['end_line']} |\n"
                
                content += "\n"
    
    # Procesar componentes
    if "components" in code_map:
        content += "## Componentes\n\n"
        for file, data in code_map["components"].items():
            content += f"### {file}\n\n"
            
            # Clases
            if "classes" in data and data["classes"]:
                content += "#### Clases\n\n"
                content += "| Clase | Descripción | Líneas |\n"
                content += "|-------|-------------|--------|\n"
                
                for cls in data["classes"]:
                    content += f"| `{cls['name']}` | {cls['description']} | {cls['start_line']}-{cls['end_line']} |\n"
                
                content += "\n"
                
                # Métodos de clases
                for cls in data["classes"]:
                    if "methods" in cls and cls["methods"]:
                        content += f"##### Métodos de {cls['name']}\n\n"
                        content += "| Método | Descripción | Líneas |\n"
                        content += "|--------|-------------|--------|\n"
                        
                        for method in cls["methods"]:
                            content += f"| `{method['name']}` | {method['description']} | {method['start_line']}-{method['end_line']} |\n"
                        
                        content += "\n"
            
            # Funciones
            if "functions" in data and data["functions"]:
                content += "#### Funciones\n\n"
                content += "| Función | Descripción | Líneas |\n"
                content += "|---------|-------------|--------|\n"
                
                for func in data["functions"]:
                    content += f"| `{func['name']}` | {func['description']} | {func['start_line']}-{func['end_line']} |\n"
                
                content += "\n"
    
    # Procesar utilidades
    if "utils" in code_map:
        content += "## Utilidades\n\n"
        for file, data in code_map["utils"].items():
            content += f"### {file}\n\n"
            
            # Clases
            if "classes" in data and data["classes"]:
                content += "#### Clases\n\n"
                content += "| Clase | Descripción | Líneas |\n"
                content += "|-------|-------------|--------|\n"
                
                for cls in data["classes"]:
                    content += f"| `{cls['name']}` | {cls['description']} | {cls['start_line']}-{cls['end_line']} |\n"
                
                content += "\n"
                
                # Métodos de clases
                for cls in data["classes"]:
                    if "methods" in cls and cls["methods"]:
                        content += f"##### Métodos de {cls['name']}\n\n"
                        content += "| Método | Descripción | Líneas |\n"
                        content += "|--------|-------------|--------|\n"
                        
                        for method in cls["methods"]:
                            content += f"| `{method['name']}` | {method['description']} | {method['start_line']}-{method['end_line']} |\n"
                        
                        content += "\n"
            
            # Funciones
            if "functions" in data and data["functions"]:
                content += "#### Funciones\n\n"
                content += "| Función | Descripción | Líneas |\n"
                content += "|---------|-------------|--------|\n"
                
                for func in data["functions"]:
                    content += f"| `{func['name']}` | {func['description']} | {func['start_line']}-{func['end_line']} |\n"
                
                content += "\n"
    
    # Guardar el inventario
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Inventario de funciones generado en {output_file}")

if __name__ == "__main__":
    generate_function_inventory()
