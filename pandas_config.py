"""
Configuración de pandas para mejorar el rendimiento y evitar advertencias.
Este archivo debe importarse al inicio de la aplicación.
"""

import pandas as pd

# Activar Copy-on-Write para mejorar el rendimiento y evitar SettingWithCopyWarning
try:
    pd.options.mode.copy_on_write = True
except Exception as e:
    print(f"Error configurando copy_on_write: {str(e)}")

# Configurar opciones de visualización
try:
    pd.set_option("display.max_columns", None)
    pd.set_option("display.expand_frame_repr", False)
    pd.set_option("display.precision", 2)
except Exception as e:
    print(f"Error configurando opciones de visualización: {str(e)}")
