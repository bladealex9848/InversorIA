![Logo de InversorIA](https://github.com/bladealex9848/InversorIA/blob/main/assets/logo.jpg)

# InversorIA Pro 💹 Terminal Institucional de Trading

[![Version](https://img.shields.io/badge/versión-2.0.3-darkgreen.svg)](https://github.com/bladealex9848/InversorIA-Pro)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30.0-ff4b4b.svg)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI_API-v2-00C244.svg)](https://platform.openai.com/)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-yellow.svg)](LICENSE)

## 📊 Descripción Detallada

**InversorIA Pro** es una **Terminal de Trading Integral** diseñada específicamente para las exigencias de **traders institucionales y profesionales**. Su objetivo es centralizar y potenciar el proceso de toma de decisiones combinando análisis cuantitativo avanzado, visualización de datos interactiva y la potencia de la inteligencia artificial contextualizada.

Esta plataforma integra de forma fluida:
* **Análisis Técnico Profundo:** Desde patrones clásicos hasta indicadores avanzados y detección automática de niveles.
* **Estrategias de Opciones Sofisticadas:** Incluyendo análisis de la superficie de volatilidad y recomendaciones estratégicas.
* **Perspectiva Multitemporal:** Para confirmar la robustez de las señales a través de diferentes horizontes de inversión.
* **Inteligencia de Mercado en Tiempo Real:** Incorporando análisis de sentimiento, noticias relevantes y datos fundamentales.
* **Descubrimiento de Oportunidades:** Mediante un scanner de mercado configurable y eficiente.
* **Sistema de Notificaciones:** Envío de boletines por correo y seguimiento de señales en base de datos.
* **Asistencia IA Contextual:** Un copiloto inteligente que entiende el estado actual del mercado y del activo analizado.

InversorIA Pro busca capacitar a los traders para que operen con mayor confianza, eficiencia y una perspectiva basada en datos, todo dentro de un entorno unificado.

## 🎬 Demostración

Mira este video para ver InversorIA Pro en acción, mostrando un flujo de trabajo completo desde el escaneo de mercado hasta la validación y toma de decisiones:

[![InversorIA Pro Demo](https://img.youtube.com/vi/UmGnJHiLDEA/0.jpg)](https://www.youtube.com/watch?v=UmGnJHiLDEA)

[Ver demostración en YouTube](https://www.youtube.com/watch?v=UmGnJHiLDEA)

## ✨ Funcionalidades Clave

### 🔐 Autenticación Segura
Protege el acceso a la terminal, garantizando la privacidad de tu análisis y configuración.

### 📊 Dashboard Interactivo
Visualiza toda la información relevante de un activo en un solo lugar, con pestañas dedicadas para cada tipo de análisis (Técnico, Opciones, Multiframe, Experto IA, Noticias/Sentimiento).

### 📈 Análisis Técnico Avanzado
- **Tendencias:** Identifica la dirección predominante del mercado usando múltiples indicadores (Medias Móviles, MACD).
- **Patrones y Niveles:** Detecta automáticamente formaciones de velas significativas, soportes, resistencias, líneas de tendencia y canales.
- **Indicadores Clave:** RSI, MACD, Bandas de Bollinger y ATR para análisis completo.

### 🎯 Análisis de Opciones
- **Superficie de Volatilidad:** Visualiza en 3D cómo varía la volatilidad implícita según el strike y el vencimiento.
- **Estrategias Sugeridas:** Recomendaciones basadas en el análisis técnico y de volatilidad.
- **IV vs HV:** Comparación entre volatilidad implícita y histórica para evaluar primas.

### ⏳ Análisis Multiframe
Compara señales en gráficos diarios, semanales y mensuales para identificar alineación o divergencias que impactan la confianza en la señal.

### 📰 Análisis Fundamental y de Mercado
- **Datos Fundamentales:** Métricas clave de la empresa para complementar el análisis técnico.
- **Sentimiento y Noticias:** Medición del "mood" del mercado y feed de noticias contextual.
- **Insights Web:** Resumen de análisis o menciones relevantes de fuentes externas.

### 🔍 Scanner de Mercado
- **Exploración Eficiente:** Filtra rápidamente el universo de activos por sector.
- **Detección de Oportunidades:** Encuentra activos que cumplen criterios técnicos o de opciones predefinidos.
- **Priorización:** Ordenamiento por confianza de la señal o ratio Riesgo/Recompensa (R/R).

### 🧠 Asistente IA Especializado
- **Análisis Integrado:** Resúmenes expertos que combinan todos los análisis disponibles.
- **Consultas Específicas:** Respuestas a preguntas concretas sobre el mercado y activos.
- **Contexto Persistente:** Recuerda el activo que estás analizando y el estado general del mercado.

### 🔔 Sistema de Notificaciones
- **Señales Activas:** Visualización de señales de trading recientes filtradas por categoría y confianza.
- **Envío de Boletines:** Generación y envío de boletines por correo electrónico con señales seleccionadas.
- **Historial de Señales:** Consulta del historial de señales generadas y boletines enviados.
- **Almacenamiento en Base de Datos:** Registro persistente de señales, noticias y sentimiento de mercado.

## 📁 Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

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
├── scripts/                   # Scripts de utilidad y configuración
│   ├── setup-repo.sh           # Script para configurar el repositorio
│   ├── install-hooks.sh        # Script para instalar hooks de Git
│   └── hooks/                  # Hooks de Git pre-commit
├── styles/                    # Estilos CSS
├── utils/                     # Utilidades generales
├── sql/                       # Scripts SQL
├── temp/                      # Carpeta para archivos temporales
├── legacy_code/               # Código antiguo o no utilizado
│   ├── tests/                 # Scripts de prueba
│   ├── old_versions/          # Versiones antiguas de archivos
│   ├── temp_json/             # Archivos JSON temporales
│   └── dev_utils/             # Utilidades de desarrollo
├── .streamlit/                # Configuración de Streamlit
├── requirements.txt           # Dependencias del proyecto
├── README.md                  # Documentación principal
└── secrets.toml.example       # Ejemplo de configuración de secretos
```

## 🚀 Instalación

### 1. Prerrequisitos
- Python 3.8 o superior y `pip`
- Acceso a API de OpenAI

### 2. Entorno Virtual (Recomendado)
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Clonar Repositorio
```bash
git clone https://github.com/bladealex9848/InversorIA-Pro
cd InversorIA-Pro
```

### 4. Configurar el Repositorio
Ejecuta el script de configuración para instalar los hooks de Git y configurar el entorno:
```bash
./scripts/setup-repo.sh
```

Este script realizará las siguientes acciones:
- Instalar los hooks de Git para prevenir la exposición de credenciales sensibles
- Crear el archivo `.streamlit/secrets.toml` a partir de `secrets.toml.example`
- Ofrecer instalar las dependencias del proyecto

### 5. Instalar Dependencias (Si no lo hiciste en el paso anterior)
```bash
pip install -r requirements.txt
```

### 5. Configurar Credenciales
Crea la carpeta `.streamlit` y dentro el archivo `secrets.toml`:

```toml
# --- Obligatorias ---
OPENAI_API_KEY = "sk-..."
ASSISTANT_ID = "asst_..." # Si usas la API de Asistentes OpenAI

# Contraseña para acceder a la aplicación
PASSWORD = "tu-contraseña-muy-segura"

# --- Opcionales (Habilitan más funcionalidades) ---
# ALPHA_VANTAGE_API_KEY = "tu-alpha-vantage-key"
# YOU_API_KEY = "tu-you-com-key"
# TAVILY_API_KEY = "tu-tavily-key"
# FINNHUB_API_KEY = "tu-finnhub-key"

# --- Configuración de Base de Datos (Para Sistema de Notificaciones) ---
# [connections.mysql]
# host = "localhost"
# port = 3306
# database = "inversoria"
# user = "usuario_db"
# password = "contraseña_db"

# --- Configuración de Correo Electrónico (Para Envío de Boletines) ---
# [email]
# sender = "tu-correo@gmail.com"
# password = "tu-clave-de-aplicacion"
# smtp_server = "smtp.gmail.com"
# smtp_port = 587
```

## 💻 Uso

1. **Iniciar la Aplicación:**
   ```bash
   streamlit run 📊_InversorIA_Pro.py
   ```

2. **Acceder:**
   Abre tu navegador en `http://localhost:8501` e ingresa la contraseña configurada.

3. **Navegación:**
   - Usa las pestañas principales para cambiar entre modos.
   - En "Análisis Individual", selecciona Sector, Activo y Timeframe.
   - Explora las sub-pestañas para diferentes tipos de análisis.

4. **Interactuar con IA:**
   Escribe tus preguntas o solicitudes en el panel de chat.

5. **Sistema de Notificaciones:**
   - Accede a la pestaña "Notificaciones" para gestionar señales y boletines.
   - Configura la base de datos y el servidor de correo en `secrets.toml`.
   - Visualiza señales activas, envía boletines y consulta el historial.

## 🔍 Cómo Sacarle el Máximo Provecho

InversorIA Pro está diseñado para un flujo de trabajo analítico. Aquí tienes una guía paso a paso:

### 1. Configuración Inicial Optimizada
- Asegúrate de tener todas las API keys necesarias en `secrets.toml`.
- Utiliza un entorno virtual de Python para evitar conflictos de dependencias.
- Los archivos temporales se guardarán en la carpeta `temp/` para mantener organizado el directorio principal.

### 2. Vista Panorámica con el Scanner
- **Inicia aquí:** Selecciona los sectores que te interesan y ejecuta el scanner.
- **Filtra Inteligentemente:** Reduce el ruido filtrando por señal, estrategia o confianza.
- **Prioriza por R/R:** Identifica setups con potencial de recompensa favorable.

### 3. Análisis Profundo del Candidato
- **Pestaña Técnica:** Estudia la acción del precio, patrones y niveles técnicos.
- **Pestaña Opciones:** Analiza la volatilidad y evalúa estrategias sugeridas.
- **Pestaña Multiframe:** Confirma la tendencia en diferentes timeframes.
- **Pestaña Noticias/Sentimiento:** Entiende el contexto narrativo del mercado.
- **Pestaña Análisis Experto:** Consulta la visión integrada del asistente IA.

### 4. Dialoga con el Experto IA
- **Resuelve Dudas:** Pregunta sobre aspectos específicos del análisis.
- **Simula Escenarios:** Explora situaciones hipotéticas de mercado.
- **Personaliza Estrategias:** Solicita ajustes a las recomendaciones.

### 5. Define tu Plan de Trading
- Establece puntos concretos de entrada, stop-loss y objetivos basados en el análisis.

### 6. Monitoreo y Ajuste
- Revisa periódicamente nuevas oportunidades y el estado de posiciones abiertas.
- Utiliza "Limpiar Caché" para actualizar datos cuando sea necesario.

### 7. Configuración del Sistema de Notificaciones
- **Base de Datos:** Crea una base de datos MariaDB con el siguiente comando:
  ```sql
  CREATE DATABASE inversoria CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```
- **Usuario de Base de Datos:** Crea un usuario con permisos:
  ```sql
  CREATE USER 'usuario_db'@'localhost' IDENTIFIED BY 'contraseña_db';
  GRANT ALL PRIVILEGES ON inversoria.* TO 'usuario_db'@'localhost';
  FLUSH PRIVILEGES;
  ```
- **Correo Electrónico:** Para Gmail, usa una "Clave de aplicación" en lugar de la contraseña normal.
- **Seguridad:** Las credenciales nunca deben ser compartidas o subidas a repositorios públicos.

## ⚠️ Limitaciones (Potenciales)

- La precisión del análisis depende de la calidad y puntualidad de los datos de las APIs configuradas.
- Funcionalidades avanzadas pueden requerir suscripciones a servicios de datos adicionales.
- El rendimiento puede variar según la potencia de tu máquina, especialmente al procesar grandes cantidades de datos.
- El código antiguo o no utilizado se almacena en la carpeta `legacy_code/` para referencia, pero no se utiliza en la aplicación principal.

## 🔒 Seguridad

### Protección de Credenciales

El proyecto incluye medidas para proteger las credenciales sensibles:

1. **Hooks de Git Pre-commit**: Previenen automáticamente la exposición de credenciales sensibles en los commits.
   - Detecta patrones comunes de credenciales (contraseñas, API keys, tokens, etc.)
   - Bloquea commits que contengan información sensible
   - Se instala automáticamente con el script `setup-repo.sh`

2. **Archivo `secrets.toml`**: Todas las credenciales deben almacenarse en este archivo, que está incluido en `.gitignore`.

3. **Ejemplo de Configuración**: El archivo `secrets.toml.example` muestra la estructura correcta sin exponer credenciales reales.

### Mejores Prácticas de Seguridad

- **Nunca** incluyas credenciales directamente en el código fuente
- **Nunca** subas el archivo `secrets.toml` al repositorio
- Utiliza siempre el hook pre-commit para verificar tus cambios antes de confirmarlos
- Cambia regularmente tus contraseñas y tokens de API
- Utiliza claves de API con permisos limitados cuando sea posible

## 💾 Estructura de la Base de Datos

El sistema de notificaciones utiliza las siguientes tablas en la base de datos:

1. `trading_signals`: Almacena las señales de trading generadas
   - Incluye información detallada sobre cada señal: símbolo, dirección, confianza, fecha, etc.

2. `email_logs`: Registra los envíos de boletines
   - Guarda información sobre cada boletín enviado: destinatarios, asunto, fecha, señales incluidas, etc.

3. `market_sentiment`: Almacena el sentimiento diario del mercado
   - Registra indicadores de sentimiento para diferentes sectores y el mercado general

4. `market_news`: Guarda noticias relevantes del mercado
   - Almacena noticias importantes relacionadas con activos específicos o el mercado en general

## 🤝 Contribuciones

¡Tus contribuciones son bienvenidas! Si deseas mejorar InversorIA Pro:

1. Haz un fork del repositorio.
2. Crea una nueva rama para tus cambios (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus modificaciones y haz commit (`git commit -am 'Añade nueva funcionalidad X'`).
4. Empuja tus cambios a tu fork (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request en el repositorio original.

## 📝 Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para más información.

## 👤 Autor

Creado por Alexander Oviedo Fadul

[GitHub](https://github.com/bladealex9848) | [Website](https://alexanderoviedofadul.dev) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)

---

### 📊 Mensaje Final

InversorIA Pro es el resultado de combinar tecnologías avanzadas de análisis técnico, cuantitativo y de inteligencia artificial para crear una terminal de trading verdaderamente integral. Esta herramienta busca democratizar el acceso a capacidades analíticas profesionales, permitiendo a traders de todos los niveles tomar decisiones más informadas y sistemáticas.

*"El éxito en el trading no proviene de la suerte, sino de un proceso sistemático de análisis, gestión de riesgo y disciplina. La tecnología debe potenciar ese proceso, no reemplazarlo."*