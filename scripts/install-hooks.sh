#!/bin/bash

# Script para instalar los hooks de Git
# Este script copia los hooks de Git del directorio hooks/ al directorio .git/hooks/

# Crear el directorio scripts si no existe
mkdir -p scripts/hooks

# Copiar el hook pre-commit del directorio .git/hooks/ al directorio scripts/hooks/
cp .git/hooks/pre-commit scripts/hooks/

# Mostrar mensaje de éxito
echo "Hooks copiados al directorio scripts/hooks/"
echo "Para instalar los hooks en un nuevo clon del repositorio, ejecuta este script."
