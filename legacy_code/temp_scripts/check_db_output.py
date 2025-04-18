#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar check_db.py y guardar la salida en un archivo
"""

import subprocess
import os

# Directorio del proyecto
project_dir = "/Users/alexander/Library/CloudStorage/OneDrive-ConsejoSuperiordelaJudicatura/Backup Personal/HP 14-cm0046la/Desktop/Proyectos_Python/InversorIA"

# Ruta del archivo de salida
output_file = os.path.join(project_dir, "db_check_output.txt")

# Ejecutar check_db.py y guardar la salida
with open(output_file, "w") as f:
    subprocess.run(
        ["python", "check_db.py"],
        cwd=project_dir,
        stdout=f,
        stderr=subprocess.STDOUT,
        text=True
    )

print(f"Salida guardada en {output_file}")
