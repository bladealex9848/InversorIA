#!/bin/bash

# Script para instalar hooks de Git de forma global en Linux/macOS
# Este script configura los hooks de Git para que se apliquen a todos los repositorios

# Colores para los mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar si Git está instalado
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git no está instalado o no está en el PATH.${NC}"
    exit 1
fi

echo -e "${GREEN}Git encontrado: $(git --version)${NC}"

# Obtener la ruta del directorio de configuración global de Git
GIT_CONFIG_DIR=$(git config --global --get core.hooksPath)
if [ -z "$GIT_CONFIG_DIR" ]; then
    # Si no está configurado, crear un directorio para los hooks globales
    GIT_CONFIG_DIR="$HOME/.git-hooks"
    
    # Crear el directorio si no existe
    if [ ! -d "$GIT_CONFIG_DIR" ]; then
        echo -e "${YELLOW}Creando directorio para hooks globales: $GIT_CONFIG_DIR${NC}"
        mkdir -p "$GIT_CONFIG_DIR"
    fi
    
    # Configurar Git para usar este directorio para hooks
    echo -e "${YELLOW}Configurando Git para usar hooks globales...${NC}"
    git config --global core.hooksPath "$GIT_CONFIG_DIR"
    echo -e "${GREEN}Git configurado para usar hooks globales en: $GIT_CONFIG_DIR${NC}"
else
    echo -e "${YELLOW}Git ya está configurado para usar hooks globales en: $GIT_CONFIG_DIR${NC}"
fi

# Copiar el hook pre-commit al directorio de hooks globales
SOURCE_HOOK="$(dirname "$0")/hooks/pre-commit"
DEST_HOOK="$GIT_CONFIG_DIR/pre-commit"

if [ -f "$SOURCE_HOOK" ]; then
    echo -e "${YELLOW}Copiando hook pre-commit al directorio de hooks globales...${NC}"
    cp "$SOURCE_HOOK" "$DEST_HOOK"
    
    # Hacer el archivo ejecutable
    chmod +x "$DEST_HOOK"
    echo -e "${GREEN}Hook pre-commit instalado globalmente.${NC}"
else
    echo -e "${RED}Error: No se encontró el archivo de hook pre-commit en $SOURCE_HOOK${NC}"
    exit 1
fi

echo -e "${GREEN}Instalación completada. El hook pre-commit se aplicará a todos los repositorios Git.${NC}"
echo -e "${YELLOW}NOTA: Este hook se aplicará a todos los repositorios Git que uses en este equipo.${NC}"
echo -e "${YELLOW}Si deseas desactivar esta configuración, ejecuta: git config --global --unset core.hooksPath${NC}"
