"""
Script para solucionar el problema de "cannot access local variable 'client' where it is not associated with a value"
Este script modifica el código para asegurar que la variable 'client' esté siempre definida antes de ser utilizada.
"""

import logging
import sys
import re
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def fix_client_variable_in_file(file_path):
    """
    Busca y corrige problemas con la variable 'client' en un archivo.

    Args:
        file_path (str): Ruta al archivo a corregir

    Returns:
        bool: True si se realizaron correcciones, False en caso contrario
    """
    try:
        # Verificar si el archivo existe
        if not os.path.exists(file_path):
            logger.error(f"❌ El archivo {file_path} no existe")
            return False

        logger.info(f"Analizando archivo: {file_path}")

        # Leer el contenido del archivo
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            lines = content.split("\n")

        # Buscar líneas con problemas potenciales
        modified = False
        modified_lines = []

        # Variables para rastrear el contexto
        in_function = False
        client_defined = False
        needs_client_definition = False

        for i, line in enumerate(lines):
            # Detectar inicio de función
            if re.search(r"\bdef\b", line):
                in_function = True
                client_defined = False

            # Detectar definición de client
            if re.search(r"\bclient\s*=", line):
                client_defined = True

            # Detectar uso de client sin definición previa
            if (
                in_function
                and not client_defined
                and re.search(r"\bclient\b", line)
                and not re.search(r"\bclient\s*=", line)
            ):
                needs_client_definition = True

            # Detectar bloques de código que usan client y podrían causar el error
            if re.search(r"if\s+\(.*\bclient\b.*\):", line) and not client_defined:
                logger.info(
                    f"Encontrada línea problemática en {file_path}:{i+1}: {line.strip()}"
                )
                # Insertar definición de client antes de este bloque
                modified_lines.append(
                    "        # Definir client como None para evitar errores"
                )
                modified_lines.append("        client = None")
                modified_lines.append("")
                modified_lines.append(line)
                modified = True
                continue

            # Detectar uso de client en condiciones
            if re.search(
                r'if\s+\(.*signal\.get\(["\']sentiment["\']\)\s+and\s+client.*\):', line
            ):
                logger.info(
                    f"Encontrada condición problemática en {file_path}:{i+1}: {line.strip()}"
                )
                # Reemplazar con una verificación explícita
                new_line = line.replace("client", "client is not None")
                modified_lines.append(new_line)
                modified = True
                continue

            # Agregar línea sin cambios
            modified_lines.append(line)

        # Si se necesita definir client al inicio de una función
        if needs_client_definition and not modified:
            logger.info(f"Se necesita definir client en {file_path}")
            # Buscar el inicio de la función y agregar la definición
            for i, line in enumerate(modified_lines):
                if re.search(r"\bdef\b", line):
                    # Encontrar la primera línea después de la definición de la función
                    j = i + 1
                    while j < len(modified_lines) and (
                        modified_lines[j].strip() == ""
                        or modified_lines[j].strip().startswith('"""')
                    ):
                        j += 1

                    # Insertar la definición de client
                    modified_lines.insert(
                        j, "    # Definir client como None para evitar errores"
                    )
                    modified_lines.insert(j + 1, "    client = None")
                    modified_lines.insert(j + 2, "")
                    modified = True
                    break

        # Guardar el archivo modificado si se realizaron cambios
        if modified:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(modified_lines))

            logger.info(
                f"✅ Se corrigieron problemas con la variable 'client' en {file_path}"
            )
            return True
        else:
            logger.info(
                f"ℹ️ No se encontraron problemas con la variable 'client' en {file_path}"
            )
            return False

    except Exception as e:
        logger.error(f"❌ Error al corregir {file_path}: {str(e)}")
        return False


def fix_client_variable():
    """
    Busca y corrige problemas con la variable 'client' en archivos clave del proyecto.

    Returns:
        int: Número de archivos corregidos
    """
    # Lista de archivos a revisar
    files_to_check = [
        "📊_InversorIA_Pro.py",
        "enhanced_market_scanner.py",
        "market_scanner.py",
        "ai_utils.py",
    ]

    corrected_files = 0

    for file_path in files_to_check:
        if fix_client_variable_in_file(file_path):
            corrected_files += 1

    return corrected_files


if __name__ == "__main__":
    logger.info("Iniciando corrección para el problema de la variable 'client'...")

    # Aplicar correcciones
    corrected_count = fix_client_variable()

    if corrected_count > 0:
        logger.info(f"✅ Corrección aplicada en {corrected_count} archivos.")
    else:
        logger.warning(
            "⚠️ No se encontraron problemas para corregir o no se pudieron aplicar las correcciones."
        )
