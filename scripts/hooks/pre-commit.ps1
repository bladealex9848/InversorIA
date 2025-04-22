# Hook pre-commit para proteger el repositorio en Windows
# Este hook verifica que no se cometan credenciales, archivos grandes o código de depuración

# Función para mostrar mensajes en color
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

Write-Yellow "Ejecutando verificaciones pre-commit..."

# Obtener la lista de archivos que se van a confirmar
$files = git diff --cached --name-only --diff-filter=ACM

# Patrones de credenciales sensibles a buscar
$patterns = @(
    # Direcciones IP (patrón general)
    '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'

    # Patrones de direcciones IP sensibles (solo fragmentos parciales)
    '190\.8\.[0-9]{1,3}\.[0-9]{1,3}'
    '192\.168\.[0-9]{1,3}\.[0-9]{1,3}'

    # Contraseñas comunes en código
    'password\s*=\s*["''][^\s][^'']*["'']'
    'passwd\s*=\s*["''][^\s][^'']*["'']'
    'pwd\s*=\s*["''][^\s][^'']*["'']'
    'pass\s*=\s*["''][^\s][^'']*["'']'
    'secret\s*=\s*["''][^\s][^'']*["'']'
    'key\s*=\s*["''][^\s][^'']*["'']'

    # Nombres de usuario comunes en código
    'username\s*=\s*["''][^\s][^'']*["'']'
    'user\s*=\s*["''][^\s][^'']*["'']'

    # Tokens y claves API
    'api[_-]?key\s*=\s*["''][^\s][^'']*["'']'
    'auth[_-]?token\s*=\s*["''][^\s][^'']*["'']'
    'oauth\s*=\s*["''][^\s][^'']*["'']'
    'access[_-]?token\s*=\s*["''][^\s][^'']*["'']'
    'secret[_-]?key\s*=\s*["''][^\s][^'']*["'']'

    # Cadenas de conexión
    'jdbc:[a-z]+://[a-zA-Z0-9\.\-_:]+/[a-zA-Z0-9\.\-_]+'
    'mongodb://[a-zA-Z0-9\.\-_:]+/[a-zA-Z0-9\.\-_]+'
    'mysql://[a-zA-Z0-9\.\-_:]+/[a-zA-Z0-9\.\-_]+'
    'postgresql://[a-zA-Z0-9\.\-_:]+/[a-zA-Z0-9\.\-_]+'
    'redis://[a-zA-Z0-9\.\-_:]+/[a-zA-Z0-9\.\-_]+'

    # Código de depuración
    'console\.log\('
    'print\(.*\)'
    'debugger'
    'TODO:'
    'FIXME:'
    'XXX:'
)

# Archivos a ignorar (expresiones regulares)
$ignoredFiles = @(
    '\.git/'
    '\.gitignore'
    '\.env\.example'
    'secrets\.toml\.example'
    '\.git/hooks/pre-commit'
    'scripts/hooks/'
    'scripts/hooks/pre-commit'
    'legacy_code/'
    'requirements\.txt'
)

# Función para verificar si un archivo debe ser ignorado
function Should-IgnoreFile {
    param (
        [string]$file
    )

    foreach ($pattern in $ignoredFiles) {
        if ($file -match $pattern) {
            return $true
        }
    }

    return $false
}

# Función para verificar si una línea debe ser ignorada
function Should-IgnoreLine {
    param (
        [string]$line
    )

    # Ignorar líneas de comentarios
    if ($line -match '^\s*[#//]') {
        return $true
    }

    # Ignorar líneas que contienen "example" o "placeholder"
    if ($line -match 'example|placeholder|dummy|localhost|127\.0\.0\.1|0\.0\.0\.0') {
        return $true
    }

    return $false
}

# Función para verificar archivos grandes (>5MB)
function Check-LargeFiles {
    $maxSize = 5MB
    $largeFiles = @()

    foreach ($file in $files) {
        if ((Test-Path $file) -and -not (Should-IgnoreFile $file)) {
            $fileInfo = Get-Item $file
            if ($fileInfo.Length -gt $maxSize) {
                $readableSize = "{0:N2} MB" -f ($fileInfo.Length / 1MB)
                $largeFiles += "$file ($readableSize)"
            }
        }
    }

    if ($largeFiles.Count -gt 0) {
        Write-Red "Advertencia: Se detectaron archivos demasiado grandes (>5MB):"
        foreach ($file in $largeFiles) {
            Write-Yellow "  - $file"
        }
        return $false
    }

    return $true
}

# Banderas para rastrear si se encontraron problemas
$credentialsFound = $false
$largeFilesFound = $false

# Verificar cada archivo para credenciales
foreach ($file in $files) {
    # Ignorar archivos que no existen o están en la lista de ignorados
    if (-not (Test-Path $file) -or (Should-IgnoreFile $file)) {
        continue
    }

    # Obtener el contenido del archivo
    $content = Get-Content $file

    # Verificar cada patrón en el archivo
    foreach ($pattern in $patterns) {
        $lineNumber = 0

        foreach ($line in $content) {
            $lineNumber++

            # Verificar si la línea coincide con el patrón
            if ($line -match $pattern) {
                # Ignorar líneas que deben ser ignoradas
                if (Should-IgnoreLine $line) {
                    continue
                }

                # Mostrar la advertencia
                Write-Red "Advertencia: Posible credencial sensible encontrada en $file (línea $lineNumber)"
                Write-Yellow $line
                Write-Output ""

                $credentialsFound = $true
            }
        }
    }
}

# Verificar archivos grandes
if (-not (Check-LargeFiles)) {
    $largeFilesFound = $true
}

# Verificar si hay problemas y abortar el commit si es necesario
$errors = 0

# Si se encontraron credenciales, incrementar contador de errores
if ($credentialsFound) {
    Write-Red "Error: Se encontraron posibles credenciales sensibles en los archivos a confirmar."
    Write-Output "Por favor, elimina las credenciales sensibles antes de confirmar."
    $errors++
}

# Si se encontraron archivos grandes, incrementar contador de errores
if ($largeFilesFound) {
    Write-Red "Error: Se encontraron archivos demasiado grandes en los archivos a confirmar."
    Write-Output "Por favor, reduce el tamaño de los archivos o añádelos a .gitignore."
    $errors++
}

# Si hay errores, abortar el commit
if ($errors -gt 0) {
    Write-Red "Commit abortado debido a $errors error(es)."
    Write-Output "Si estás seguro de que quieres ignorar estas advertencias, puedes forzar el commit con --no-verify."
    exit 1
}

Write-Green "Verificación completada. No se encontraron problemas."
exit 0
