#!/bin/bash

# Script para configurar el repositorio después de clonarlo
# Este script instala los hooks de Git y realiza otras configuraciones necesarias

# Colores para los mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Configurando el repositorio InversorIA...${NC}"

# Verificar si el directorio .git existe
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: No se encontró el directorio .git. Asegúrate de ejecutar este script desde la raíz del repositorio.${NC}"
    exit 1
fi

# Crear el directorio para los hooks si no existe
mkdir -p .git/hooks

# Copiar los hooks
echo -e "${YELLOW}Instalando hooks de Git...${NC}"
if [ -d "scripts/hooks" ]; then
    cp scripts/hooks/* .git/hooks/
    chmod +x .git/hooks/*
    echo -e "${GREEN}Hooks instalados correctamente.${NC}"
else
    echo -e "${RED}Error: No se encontró el directorio scripts/hooks.${NC}"
    exit 1
fi

# Verificar si existe el archivo secrets.toml.example
if [ -f "secrets.toml.example" ]; then
    # Verificar si ya existe el directorio .streamlit
    if [ ! -d ".streamlit" ]; then
        echo -e "${YELLOW}Creando directorio .streamlit...${NC}"
        mkdir -p .streamlit
    fi
    
    # Verificar si ya existe el archivo secrets.toml
    if [ ! -f ".streamlit/secrets.toml" ]; then
        echo -e "${YELLOW}Creando archivo .streamlit/secrets.toml a partir de secrets.toml.example...${NC}"
        cp secrets.toml.example .streamlit/secrets.toml
        echo -e "${GREEN}Archivo .streamlit/secrets.toml creado. Por favor, edita este archivo con tus credenciales.${NC}"
    else
        echo -e "${YELLOW}El archivo .streamlit/secrets.toml ya existe. No se sobrescribirá.${NC}"
    fi
else
    echo -e "${RED}Advertencia: No se encontró el archivo secrets.toml.example.${NC}"
fi

# Verificar si existe el archivo requirements.txt
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}¿Deseas instalar las dependencias del proyecto? (s/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([sS][iI]|[sS])$ ]]; then
        echo -e "${YELLOW}Instalando dependencias...${NC}"
        pip install -r requirements.txt
        echo -e "${GREEN}Dependencias instaladas correctamente.${NC}"
    else
        echo -e "${YELLOW}No se instalarán las dependencias.${NC}"
    fi
else
    echo -e "${RED}Advertencia: No se encontró el archivo requirements.txt.${NC}"
fi

echo -e "${GREEN}Configuración completada.${NC}"
echo -e "${YELLOW}Recuerda editar el archivo .streamlit/secrets.toml con tus credenciales antes de ejecutar la aplicación.${NC}"
exit 0
