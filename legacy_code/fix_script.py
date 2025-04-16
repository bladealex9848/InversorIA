#!/usr/bin/env python3

# Script para reemplazar la sección del scanner de mercado en el archivo principal

import re

# Leer el archivo principal
with open('📊_InversorIA_Pro.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Leer la sección corregida
with open('scanner_section_fixed.py', 'r', encoding='utf-8') as f:
    new_section = f.read()

# Patrón para encontrar la sección del scanner de mercado
pattern = r'# Pestaña de Scanner de Mercado\s+with main_tab2:.*?(?=\s{8}# Pestaña de|$)'

# Reemplazar la sección
new_content = re.sub(pattern, new_section, content, flags=re.DOTALL)

# Guardar el archivo corregido
with open('📊_InversorIA_Pro_fixed.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Archivo corregido guardado como 📊_InversorIA_Pro_fixed.py")
