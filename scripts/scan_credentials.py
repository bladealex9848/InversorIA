#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para escanear el repositorio en busca de credenciales sensibles
"""

import os
import re
import sys
from pathlib import Path
import argparse
import json


# Colores para la salida
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# Patrones de credenciales sensibles
PATTERNS = {
    # Direcciones IP
    "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    # Credenciales de base de datos
    "DB_HOST": r'(?:host|HOST|Host)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    "DB_USER": r'(?:user|USER|User|username|USERNAME|Username)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    "DB_PASSWORD": r'(?:password|PASSWORD|Password|passwd|PASSWD|Passwd)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    "DB_NAME": r'(?:database|DATABASE|Database|db_name|DB_NAME|DbName)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    # Credenciales específicas (parcialmente ocultas por seguridad)
    "SPECIFIC_DB": r"liceopan_enki_[a-z]+",
    "SPECIFIC_USER": r"liceopan_[a-z]+",
    "SPECIFIC_PASSWORD": r"@[A-Z][a-z]+[0-9]{4}@",
    # Credenciales de correo electrónico
    "EMAIL_SERVER": r'(?:smtp_server|SMTP_SERVER|SmtpServer)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    "EMAIL_USER": r'(?:email_user|EMAIL_USER|EmailUser)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    "EMAIL_PASSWORD": r'(?:email_password|EMAIL_PASSWORD|EmailPassword)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    # Claves API y tokens
    "API_KEY": r'(?:api_key|API_KEY|ApiKey|api[_-]?key)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    "AUTH_TOKEN": r'(?:auth_token|AUTH_TOKEN|AuthToken|token|TOKEN|Token)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    "SECRET_KEY": r'(?:secret_key|SECRET_KEY|SecretKey|secret|SECRET|Secret)\s*(?:=|:)\s*["\']([^"\']+)["\']',
    # Cadenas de conexión
    "CONNECTION_STRING": r'(?:jdbc|mongodb|mysql|postgresql|redis)://[^\s"\']+',
}

# Archivos y directorios a ignorar
IGNORED_PATHS = [
    ".git",
    "venv",
    "node_modules",
    "__pycache__",
    ".streamlit/secrets.toml",
    "secrets.toml",
    ".env",
    ".venv",
    "scripts/scan_credentials.py",
    "scripts/hooks/pre-commit",
    ".git/hooks/pre-commit",
]

# Extensiones de archivo a escanear
FILE_EXTENSIONS = [
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".json",
    ".yml",
    ".yaml",
    ".xml",
    ".html",
    ".css",
    ".scss",
    ".md",
    ".txt",
    ".sh",
    ".bash",
    ".sql",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".config",
    ".env.example",
    ".sample",
    ".template",
]


def is_ignored(path):
    """Verifica si una ruta debe ser ignorada"""
    for ignored in IGNORED_PATHS:
        if ignored in str(path):
            return True
    return False


def scan_file(file_path):
    """Escanea un archivo en busca de credenciales sensibles"""
    results = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        for pattern_name, pattern in PATTERNS.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                # Extraer el contexto (línea completa)
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()

                # Encontrar el número de línea
                line_number = content[: match.start()].count("\n") + 1

                # Extraer el valor de la credencial
                credential_value = match.group(0)

                # Si es un patrón que captura grupos, usar el primer grupo capturado
                if "(" in pattern and match.groups():
                    credential_value = match.group(1)

                # Añadir el resultado
                results.append(
                    {
                        "file": str(file_path),
                        "line": line_number,
                        "pattern": pattern_name,
                        "value": credential_value,
                        "context": context,
                    }
                )
    except Exception as e:
        print(f"{Colors.WARNING}Error al escanear {file_path}: {str(e)}{Colors.ENDC}")

    return results


def scan_directory(directory, exclude_legacy=False):
    """Escanea un directorio en busca de credenciales sensibles"""
    results = []

    for root, dirs, files in os.walk(directory):
        # Ignorar directorios en la lista de ignorados
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d))]

        # Ignorar legacy_code si se especifica
        if exclude_legacy and "legacy_code" in dirs:
            dirs.remove("legacy_code")

        for file in files:
            file_path = os.path.join(root, file)

            # Ignorar archivos en la lista de ignorados
            if is_ignored(file_path):
                continue

            # Verificar la extensión del archivo
            if not any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                continue

            # Escanear el archivo
            file_results = scan_file(file_path)
            results.extend(file_results)

    return results


def scan_git_history(directory, exclude_legacy=False):
    """Escanea el historial de Git en busca de credenciales sensibles"""
    results = []

    try:
        # Obtener todos los commits
        import subprocess

        # Obtener la lista de commits
        cmd = ["git", "log", "--pretty=format:%H"]
        commits = (
            subprocess.check_output(cmd, cwd=directory).decode("utf-8").splitlines()
        )

        total_commits = len(commits)
        print(
            f"{Colors.BLUE}Escaneando {total_commits} commits en el historial de Git...{Colors.ENDC}"
        )

        for i, commit in enumerate(commits):
            # Mostrar progreso
            if i % 10 == 0:
                print(
                    f"{Colors.BLUE}Progreso: {i}/{total_commits} commits ({i/total_commits*100:.1f}%){Colors.ENDC}"
                )

            # Obtener los archivos modificados en este commit
            cmd = ["git", "show", "--name-only", "--pretty=format:", commit]
            files = (
                subprocess.check_output(cmd, cwd=directory).decode("utf-8").splitlines()
            )

            # Ignorar legacy_code si se especifica
            if exclude_legacy:
                files = [f for f in files if "legacy_code" not in f]

            # Ignorar archivos en la lista de ignorados
            files = [f for f in files if not is_ignored(f)]

            # Verificar la extensión de los archivos
            files = [
                f for f in files if any(f.endswith(ext) for ext in FILE_EXTENSIONS)
            ]

            for file in files:
                # Obtener el contenido del archivo en este commit
                try:
                    cmd = ["git", "show", f"{commit}:{file}"]
                    content = subprocess.check_output(cmd, cwd=directory).decode(
                        "utf-8", errors="ignore"
                    )

                    # Escanear el contenido
                    for pattern_name, pattern in PATTERNS.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            # Extraer el contexto (línea completa)
                            start = max(0, match.start() - 50)
                            end = min(len(content), match.end() + 50)
                            context = content[start:end].strip()

                            # Encontrar el número de línea
                            line_number = content[: match.start()].count("\n") + 1

                            # Extraer el valor de la credencial
                            credential_value = match.group(0)

                            # Si es un patrón que captura grupos, usar el primer grupo capturado
                            if "(" in pattern and match.groups():
                                credential_value = match.group(1)

                            # Añadir el resultado
                            results.append(
                                {
                                    "commit": commit[:8],
                                    "file": file,
                                    "line": line_number,
                                    "pattern": pattern_name,
                                    "value": credential_value,
                                    "context": context,
                                }
                            )
                except subprocess.CalledProcessError:
                    # El archivo no existe en este commit
                    pass
                except Exception as e:
                    print(
                        f"{Colors.WARNING}Error al escanear {file} en commit {commit[:8]}: {str(e)}{Colors.ENDC}"
                    )

    except Exception as e:
        print(
            f"{Colors.FAIL}Error al escanear el historial de Git: {str(e)}{Colors.ENDC}"
        )

    return results


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Escanea el repositorio en busca de credenciales sensibles"
    )
    parser.add_argument("--directory", "-d", default=".", help="Directorio a escanear")
    parser.add_argument("--output", "-o", help="Archivo de salida (JSON)")
    parser.add_argument(
        "--history", "-g", action="store_true", help="Escanear el historial de Git"
    )
    parser.add_argument(
        "--exclude-legacy",
        "-e",
        action="store_true",
        help="Excluir el directorio legacy_code",
    )

    args = parser.parse_args()

    print(
        f"{Colors.HEADER}Escaneando el repositorio en busca de credenciales sensibles...{Colors.ENDC}"
    )

    # Escanear el código actual
    print(f"{Colors.BLUE}Escaneando el código actual...{Colors.ENDC}")
    current_results = scan_directory(args.directory, args.exclude_legacy)

    # Escanear el historial de Git si se especifica
    history_results = []
    if args.history:
        history_results = scan_git_history(args.directory, args.exclude_legacy)

    # Combinar resultados
    all_results = {"current_code": current_results, "git_history": history_results}

    # Mostrar resultados
    print(f"\n{Colors.HEADER}Resultados del escaneo:{Colors.ENDC}")

    # Resultados del código actual
    print(f"\n{Colors.BOLD}Código actual:{Colors.ENDC}")
    if current_results:
        print(
            f"{Colors.FAIL}Se encontraron {len(current_results)} posibles credenciales sensibles:{Colors.ENDC}"
        )
        for result in current_results:
            print(
                f"{Colors.FAIL}[{result['pattern']}] {result['file']}:{result['line']} - {result['value']}{Colors.ENDC}"
            )
            print(f"{Colors.WARNING}Contexto: {result['context']}{Colors.ENDC}\n")
    else:
        print(
            f"{Colors.GREEN}No se encontraron credenciales sensibles en el código actual.{Colors.ENDC}"
        )

    # Resultados del historial de Git
    if args.history:
        print(f"\n{Colors.BOLD}Historial de Git:{Colors.ENDC}")
        if history_results:
            print(
                f"{Colors.FAIL}Se encontraron {len(history_results)} posibles credenciales sensibles:{Colors.ENDC}"
            )
            for result in history_results:
                print(
                    f"{Colors.FAIL}[{result['pattern']}] {result['commit']} - {result['file']}:{result['line']} - {result['value']}{Colors.ENDC}"
                )
                print(f"{Colors.WARNING}Contexto: {result['context']}{Colors.ENDC}\n")
        else:
            print(
                f"{Colors.GREEN}No se encontraron credenciales sensibles en el historial de Git.{Colors.ENDC}"
            )

    # Guardar resultados en un archivo si se especifica
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)
        print(f"\n{Colors.GREEN}Resultados guardados en {args.output}{Colors.ENDC}")

    # Retornar código de salida
    if current_results or history_results:
        print(
            f"\n{Colors.FAIL}¡Atención! Se encontraron credenciales sensibles. Revisa los resultados y toma medidas para eliminarlas.{Colors.ENDC}"
        )
        return 1
    else:
        print(
            f"\n{Colors.GREEN}¡Felicidades! No se encontraron credenciales sensibles.{Colors.ENDC}"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
