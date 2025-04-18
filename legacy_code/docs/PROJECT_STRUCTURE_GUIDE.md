# Guía de Estructura del Proyecto InversorIA

Este documento sirve como guía para mantener la estructura del proyecto InversorIA organizada y consistente. Sigue estas directrices al añadir nuevos archivos o modificar la estructura existente.

## Estructura General

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
├── sql/                       # Scripts SQL
├── temp/                      # Carpeta para archivos temporales
├── ai_utils.py                # Utilidades de IA y procesamiento con modelos
├── database_utils.py          # Utilidades para interacción con base de datos
├── market_utils.py            # Utilidades para análisis de mercado
├── market_data_processor.py   # Procesador de datos de mercado con IA
├── database_quality_processor.py # Procesador de calidad de datos en la base de datos
├── database_quality_utils.py  # Utilidades para verificar y mejorar la calidad de los datos
├── text_processing.py         # Funciones para análisis y traducción de texto
├── ai_content_generator.py    # Funciones para generar contenido con IA
├── data_enrichment.py         # Funciones para enriquecer datos (URLs, noticias, etc.)
├── yahoo_finance_scraper.py   # Scraper para obtener datos de Yahoo Finance
├── company_data.py            # Datos de compañías y símbolos
├── check_db.py                # Herramienta para verificar calidad de datos
├── update_database_schema.py  # Herramienta para actualizar esquema de base de datos
├── legacy_code/               # Código antiguo o no utilizado
│   ├── tests/                 # Scripts de prueba
│   ├── old_versions/          # Versiones antiguas de archivos
│   ├── temp_json/             # Archivos JSON temporales
│   ├── temp_scripts/          # Scripts temporales de mantenimiento
│   ├── dev_utils/             # Utilidades de desarrollo
│   ├── docs/                  # Documentación antigua
│   └── sql/                   # Scripts SQL antiguos
├── .streamlit/                # Configuración de Streamlit
├── requirements.txt           # Dependencias del proyecto
├── README.md                  # Documentación principal
├── PROJECT_STRUCTURE_GUIDE.md # Guía de estructura del proyecto
├── inventario_funciones.md    # Inventario de funciones del proyecto
├── code_map.json              # Mapa de código del proyecto
└── secrets.toml.example       # Ejemplo de configuración de secretos
```

## Directrices para Mantener la Estructura

### 1. Archivos Principales

- **Archivo Principal**: `📊_InversorIA_Pro.py` contiene la aplicación principal.
- **Páginas Adicionales**: Coloca nuevas páginas en la carpeta `pages/` con un prefijo numérico para mantener el orden.
- **Módulos Auxiliares**: Coloca los módulos auxiliares en la raíz del proyecto si son utilizados por múltiples componentes.
- **Herramientas de Mantenimiento**: Archivos como `database_quality_processor.py`, `check_db.py` y `update_database_schema.py` son herramientas para mantener la calidad y estructura de los datos.

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
  - **temp_scripts/**: Scripts temporales de mantenimiento y correcciones.
  - **dev_utils/**: Utilidades de desarrollo que no son parte del flujo principal.
  - **docs/**: Documentación antigua o reemplazada.
  - **sql/**: Scripts SQL antiguos o de referencia.

### 5. Documentación

- **README.md**: Mantén actualizada la documentación principal.
- **Comentarios**: Documenta adecuadamente el código con docstrings y comentarios.
- **Inventario de Funciones**: Actualiza `inventario_funciones.md` cuando añadas nuevas funciones.
- **Mapa de Código**: Actualiza `code_map.json` cuando modifiques la estructura del proyecto.
- **Guía de Estructura**: Actualiza `PROJECT_STRUCTURE_GUIDE.md` cuando realices cambios en la estructura del proyecto.
- **Calidad de Datos**: Utiliza `check_db.py` para verificar la calidad de los datos y `database_quality_processor.py` para procesar y mejorar los datos con campos vacíos.

### 6. Convenciones de Nomenclatura

- **Archivos Python**: Usa snake_case para nombres de archivos (ej. `market_utils.py`).
- **Clases**: Usa PascalCase para nombres de clases (ej. `MarketScanner`).
- **Funciones y Variables**: Usa snake_case para funciones y variables (ej. `get_market_data()`).
- **Constantes**: Usa UPPER_CASE para constantes (ej. `MAX_RETRIES`).

### 7. Gestión de Dependencias

- **requirements.txt**: Mantén actualizado este archivo con todas las dependencias.
- **Versiones**: Especifica versiones exactas para evitar problemas de compatibilidad.
- **Entorno Virtual**: Utiliza siempre un entorno virtual para el desarrollo.

## Notas para Colaboradores

1. **Antes de Añadir Nuevos Archivos**: Verifica si ya existe un módulo que proporcione la funcionalidad deseada.
2. **Refactorización**: Si encuentras código duplicado, considera refactorizarlo en un módulo común.
3. **Pruebas**: Escribe pruebas para nuevas funcionalidades y colócalas en una carpeta `tests/` apropiada.
4. **Documentación**: Actualiza la documentación cuando añadas nuevas características o modifiques las existentes.
5. **Limpieza**: Mueve el código obsoleto a `legacy_code/` en lugar de eliminarlo, para mantener la referencia.
6. **Calidad de Datos**: Ejecuta regularmente `check_db.py` para verificar la calidad de los datos, `database_quality_processor.py` para procesar y mejorar los datos con campos vacíos, y `update_database_schema.py` cuando necesites modificar el esquema de la base de datos.
7. **Scraping de Datos**: Asegúrate de que el scraper de Yahoo Finance (`yahoo_finance_scraper.py`) obtenga URLs válidas para las noticias y datos completos.

Siguiendo estas directrices, mantendremos el proyecto organizado, facilitando su mantenimiento y evolución a largo plazo.
