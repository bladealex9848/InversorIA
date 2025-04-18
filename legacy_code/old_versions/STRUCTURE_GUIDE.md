# Guía de Estructura del Proyecto InversorIA

Este archivo sirve como guía para los agentes de IA que trabajan en este proyecto, para mantener una estructura consistente y organizada.

## Estructura General del Proyecto

```
InversorIA/
├── 📊_InversorIA_Pro.py       # Archivo principal de la aplicación
├── pages/                     # Páginas adicionales de la aplicación
│   ├── 1_📈_Analizador_de_Acciones_Pro.py
│   ├── 2_🤖_Inversor_Bot.py
│   ├── 3_📊_InversorIA_Mini.py
│   ├── 4_📈_MarketIntel_Options_Analyzer.py
│   ├── 5_📈_Technical_Expert_Analyzer.py
│   ├── 6_📊_InversorIA.py
│   └── 7_🔔_Notificaciones.py
├── assets/                    # Recursos estáticos (imágenes, logos, etc.)
├── components/                # Componentes reutilizables
├── styles/                    # Estilos CSS
├── utils/                     # Utilidades generales
├── sql/                       # Scripts SQL activos
├── temp/                      # Carpeta para archivos temporales
├── legacy_code/               # Código antiguo o no utilizado
│   ├── tests/                 # Scripts de prueba
│   ├── old_versions/          # Versiones antiguas de archivos
│   ├── temp_json/             # Archivos JSON temporales
│   ├── dev_utils/             # Utilidades de desarrollo
│   ├── docs/                  # Documentación antigua
│   └── sql/                   # Scripts SQL antiguos
├── .streamlit/                # Configuración de Streamlit
├── requirements.txt           # Dependencias del proyecto
├── README.md                  # Documentación principal
├── PROJECT_STRUCTURE_GUIDE.md # Guía para mantener la estructura del proyecto
└── secrets.toml.example       # Ejemplo de configuración de secretos
```

## Directrices para Mantener la Estructura

### 1. Archivos Principales

- **Archivo Principal**: `📊_InversorIA_Pro.py` contiene la aplicación principal.
- **Páginas Adicionales**: Coloca nuevas páginas en la carpeta `pages/` con un prefijo numérico para mantener el orden.
- **Módulos Auxiliares**: Coloca los módulos auxiliares en la raíz del proyecto si son utilizados por múltiples componentes.

### 2. Organización de Carpetas

- **assets/**: Almacena recursos estáticos como imágenes, logos, etc.
- **components/**: Contiene componentes reutilizables de la interfaz de usuario.
- **styles/**: Almacena archivos CSS para personalizar la apariencia.
- **utils/**: Contiene funciones y clases de utilidad general.
- **sql/**: Almacena scripts SQL activos utilizados por la aplicación.
- **temp/**: Utiliza esta carpeta para archivos temporales generados durante la ejecución.

### 3. Gestión de Archivos Temporales

- **Ubicación**: Todos los archivos temporales deben guardarse en la carpeta `temp/`.
- **Limpieza**: Implementa mecanismos para limpiar archivos temporales antiguos.
- **Extensiones**: Usa extensiones apropiadas (.tmp, .cache, etc.) para archivos temporales.

### 4. Código Antiguo o No Utilizado

- **legacy_code/**: Mueve aquí el código que ya no se utiliza pero que quieres conservar como referencia.
  - **tests/**: Scripts de prueba antiguos.
  - **old_versions/**: Versiones anteriores de archivos actuales.
  - **temp_json/**: Archivos JSON temporales antiguos.
  - **dev_utils/**: Utilidades de desarrollo que no son parte del flujo principal.
  - **docs/**: Documentación antigua o reemplazada.
  - **sql/**: Scripts SQL antiguos o de referencia.

### 5. Documentación

- **README.md**: Mantén actualizada la documentación principal.
- **Comentarios**: Documenta adecuadamente el código con docstrings y comentarios.
- **Inventario de Funciones**: Actualiza `inventario_funciones.md` cuando añadas nuevas funciones.
- **Mapa de Código**: Actualiza `code_map.json` cuando modifiques la estructura del proyecto.

### 6. Convenciones de Nomenclatura

- **Archivos Python**: Usa snake_case para nombres de archivos (ej. `market_utils.py`).
- **Clases**: Usa PascalCase para nombres de clases (ej. `MarketScanner`).
- **Funciones y Variables**: Usa snake_case para funciones y variables (ej. `get_market_data()`).
- **Constantes**: Usa UPPER_CASE para constantes (ej. `MAX_RETRIES`).

### 7. Gestión de Dependencias

- **requirements.txt**: Mantén actualizado este archivo con todas las dependencias.
- **Versiones**: Especifica versiones exactas para evitar problemas de compatibilidad.
- **Entorno Virtual**: Utiliza siempre un entorno virtual para el desarrollo.

## Notas para Agentes de IA

1. **Antes de Añadir Nuevos Archivos**: Verifica si ya existe un módulo que proporcione la funcionalidad deseada.
2. **Refactorización**: Si encuentras código duplicado, considera refactorizarlo en un módulo común.
3. **Pruebas**: Escribe pruebas para nuevas funcionalidades y colócalas en una carpeta `tests/` apropiada.
4. **Documentación**: Actualiza la documentación cuando añadas nuevas características o modifiques las existentes.
5. **Limpieza**: Mueve el código obsoleto a `legacy_code/` en lugar de eliminarlo, para mantener la referencia.
6. **Archivos Temporales**: Nunca guardes archivos temporales en la raíz del proyecto, usa la carpeta `temp/`.
7. **Actualización de Mapas**: Después de modificar la estructura del proyecto, actualiza `code_map.json` e `inventario_funciones.md`.

Siguiendo estas directrices, mantendremos el proyecto organizado, facilitando su mantenimiento y evolución a largo plazo.
