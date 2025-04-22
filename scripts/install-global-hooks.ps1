# Script para instalar hooks de Git de forma global en Windows
# Este script configura los hooks de Git para que se apliquen a todos los repositorios

# Colores para los mensajes
function Write-ColorOutput($ForegroundColor) {
    # Guardar el color actual
    $fc = $host.UI.RawUI.ForegroundColor

    # Cambiar al color especificado
    $host.UI.RawUI.ForegroundColor = $ForegroundColor

    # Obtener los argumentos que no son el color
    if ($args) {
        Write-Output $args
    }

    # Restaurar el color original
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Green($message) {
    Write-ColorOutput Green $message
}

function Write-Yellow($message) {
    Write-ColorOutput Yellow $message
}

function Write-Red($message) {
    Write-ColorOutput Red $message
}

# Verificar si Git está instalado
try {
    $gitVersion = git --version
    Write-Green "Git encontrado: $gitVersion"
} catch {
    Write-Red "Error: Git no está instalado o no está en el PATH."
    exit 1
}

# Obtener la ruta del directorio de configuración global de Git
$gitConfigDir = git config --global --get core.hooksPath
if (-not $gitConfigDir) {
    # Si no está configurado, crear un directorio para los hooks globales
    $gitConfigDir = "$env:USERPROFILE\.git-hooks"

    # Crear el directorio si no existe
    if (-not (Test-Path $gitConfigDir)) {
        Write-Yellow "Creando directorio para hooks globales: $gitConfigDir"
        New-Item -ItemType Directory -Path $gitConfigDir -Force | Out-Null
    }

    # Configurar Git para usar este directorio para hooks
    Write-Yellow "Configurando Git para usar hooks globales..."
    git config --global core.hooksPath $gitConfigDir
    Write-Green "Git configurado para usar hooks globales en: $gitConfigDir"
} else {
    Write-Yellow "Git ya está configurado para usar hooks globales en: $gitConfigDir"
}

# Copiar el hook pre-commit al directorio de hooks globales
$sourceHook = "$PSScriptRoot\hooks\pre-commit.ps1"
$destHook = "$gitConfigDir\pre-commit"

if (Test-Path $sourceHook) {
    Write-Yellow "Copiando hook pre-commit al directorio de hooks globales..."

    # Crear un archivo wrapper que ejecute el script de PowerShell
    $wrapperContent = @"
#!/bin/sh
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "$gitConfigDir\pre-commit.ps1"
exit `$?
"@

    # Guardar el wrapper
    $wrapperContent | Out-File -FilePath $destHook -Encoding ascii -Force

    # Copiar el script de PowerShell
    Copy-Item -Path $sourceHook -Destination "$gitConfigDir\pre-commit.ps1" -Force

    Write-Green "Hook pre-commit instalado globalmente."
} else {
    Write-Red "Error: No se encontró el archivo de hook pre-commit en $sourceHook"
    exit 1
}

Write-Green "Instalación completada. El hook pre-commit se aplicará a todos los repositorios Git."
Write-Yellow "NOTA: Este hook se aplicará a todos los repositorios Git que uses en este equipo."
Write-Yellow "Si deseas desactivar esta configuración, ejecuta: git config --global --unset core.hooksPath"
