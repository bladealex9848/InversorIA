# Sistema de Notificaciones para InversorIA Pro

Este módulo implementa un sistema de notificaciones y seguimiento para InversorIA Pro, permitiendo:

1. Visualizar señales de trading activas
2. Enviar boletines por correo electrónico
3. Almacenar señales en una base de datos MariaDB
4. Consultar el historial de señales y envíos

## Configuración

### Base de Datos

1. Crear una base de datos MariaDB:

```sql
CREATE DATABASE inversoria CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Crear un usuario con permisos:

```sql
CREATE USER 'usuario_db'@'localhost' IDENTIFIED BY 'contraseña_db';
GRANT ALL PRIVILEGES ON inversoria.* TO 'usuario_db'@'localhost';
FLUSH PRIVILEGES;
```

3. Importar el esquema de la base de datos:

```bash
mysql -u usuario_db -p inversoria < db_schema.sql
```

### Configuración de Credenciales

1. Crear el directorio `.streamlit` en la raíz del proyecto (si no existe):

```bash
mkdir -p .streamlit
```

2. Copiar el archivo de ejemplo de credenciales:

```bash
cp secrets.toml.example .streamlit/secrets.toml
```

3. Editar el archivo `.streamlit/secrets.toml` con las credenciales reales:
   - Credenciales de la base de datos
   - Configuración del servidor SMTP para envío de correos
   - Claves de API necesarias

### Dependencias

Asegúrate de tener instaladas las dependencias necesarias:

```bash
pip install mysql-connector-python
```

## Uso

### Visualización de Señales

La pestaña "Señales Activas" muestra:
- Señales de trading recientes filtradas por categoría y nivel de confianza
- Sentimiento actual del mercado
- Noticias relevantes

### Envío de Boletines

La pestaña "Envío de Boletines" permite:
1. Seleccionar señales para incluir en el boletín
2. Configurar el contenido del boletín
3. Ver una vista previa del boletín
4. Enviar el boletín a los destinatarios configurados

### Historial

La pestaña "Historial de Señales" permite:
- Consultar el historial de señales generadas
- Ver el registro de boletines enviados
- Exportar datos a CSV

## Estructura de la Base de Datos

El sistema utiliza las siguientes tablas:

1. `trading_signals`: Almacena las señales de trading
2. `email_logs`: Registra los envíos de boletines
3. `market_sentiment`: Almacena el sentimiento diario del mercado
4. `market_news`: Guarda noticias relevantes del mercado

Para más detalles sobre la estructura, consulta el archivo `db_schema.sql`.

## Notas Importantes

- Para Gmail, es recomendable usar una "Clave de aplicación" en lugar de la contraseña normal
- Las credenciales nunca deben ser compartidas o subidas a repositorios públicos
- El archivo `.streamlit/secrets.toml` está incluido en `.gitignore` para evitar su exposición
