# Validación y Mejora de Datos para InversorIA

Este conjunto de scripts permite validar y mejorar la calidad de los datos almacenados en la base de datos de InversorIA, asegurando que los campos críticos como 'summary' en la tabla 'market_news' y 'analysis' en la tabla 'market_sentiment' estén siempre completos y procesados por el experto en IA.

## Archivos Incluidos

1. **utils/data_validator.py**: Clase para validar y mejorar datos antes de guardarlos en la base de datos.
2. **check_db.py**: Script para consultar y analizar la estructura y calidad de los datos en las tablas.
3. **data_processor_improvement.py**: Script para procesar registros con campos críticos vacíos.
4. **schedule_data_processor.py**: Script para programar la ejecución periódica del procesador de datos.

## Requisitos

- Python 3.7 o superior
- Bibliotecas: mysql-connector-python, toml, openai (para el experto en IA)
- Archivo de configuración secrets.toml con las credenciales de la base de datos

## Configuración

1. Asegúrate de tener un archivo `secrets.toml` en la carpeta `.streamlit` o en la raíz del proyecto con las credenciales de la base de datos:

```toml
# Formato 1
[mysql]
host = "tu_host"
port = 3306
user = "tu_usuario"
password = "tu_contraseña"
database = "tu_base_de_datos"

# O formato 2
db_host = "tu_host"
db_port = 3306
db_user = "tu_usuario"
db_password = "tu_contraseña"
db_name = "tu_base_de_datos"
```

2. Asegúrate de tener instaladas las bibliotecas necesarias:

```bash
pip install mysql-connector-python toml openai
```

## Uso

### Verificar la estructura y calidad de los datos

```bash
python check_db.py
```

Este script mostrará:
- La estructura de las tablas
- Un resumen de registros y calidad de datos
- Los últimos 10 registros de cada tabla
- Registros con campos críticos vacíos

### Procesar registros con campos críticos vacíos

```bash
python data_processor_improvement.py
```

Este script:
- Busca noticias con resumen vacío y genera resúmenes con IA
- Busca registros de sentimiento con análisis vacío y genera análisis con IA
- Traduce títulos en inglés al español
- Intenta obtener URLs de noticias desde Yahoo Finance cuando faltan

### Programar la ejecución periódica del procesador de datos

```bash
# Ejecutar cada hora (por defecto)
python schedule_data_processor.py

# Ejecutar cada 30 minutos
python schedule_data_processor.py --interval 1800

# Ejecutar 5 veces y salir
python schedule_data_processor.py --max-runs 5

# Ejecutar una sola vez y salir
python schedule_data_processor.py --run-once
```

## Integración con el flujo de trabajo existente

El validador de datos (`utils/data_validator.py`) ya está integrado en el flujo de trabajo existente a través de `market_data_manager.py`. Esto asegura que los nuevos datos que se guardan en la base de datos sean validados y mejorados automáticamente.

Los scripts `data_processor_improvement.py` y `schedule_data_processor.py` complementan esta integración, procesando los registros existentes que tienen campos críticos vacíos.

## Recomendaciones

1. **Ejecución periódica**: Configura el script `schedule_data_processor.py` para que se ejecute periódicamente (por ejemplo, cada día) para mantener la calidad de los datos.

2. **Monitoreo**: Ejecuta regularmente el script `check_db.py` para monitorear la calidad de los datos y detectar problemas.

3. **Actualización de datos**: Si se añaden nuevos campos críticos a las tablas, actualiza el script `data_processor_improvement.py` para incluirlos en el procesamiento.

4. **Mejora continua**: Revisa y mejora los prompts utilizados para generar resúmenes y análisis con IA para obtener resultados de mayor calidad.

## Solución de problemas

- **Error de conexión a la base de datos**: Verifica que el archivo `secrets.toml` existe y contiene las credenciales correctas.
- **Error de importación de módulos**: Asegúrate de que todas las bibliotecas necesarias están instaladas.
- **Error en el experto en IA**: Verifica que la API de OpenAI está configurada correctamente y que tienes acceso a ella.
- **Errores de Streamlit**: Algunos componentes requieren que se ejecuten dentro de una aplicación Streamlit. Si ves errores relacionados con `st.session_state`, considera ejecutar los scripts dentro de una aplicación Streamlit o modificarlos para que no dependan de Streamlit.
