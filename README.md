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

### 4. Instalar Dependencias
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

## 🔍 Cómo Sacarle el Máximo Provecho

InversorIA Pro está diseñado para un flujo de trabajo analítico. Aquí tienes una guía paso a paso:

### 1. Configuración Inicial Optimizada
- Asegúrate de tener todas las API keys necesarias en `secrets.toml`.
- Utiliza un entorno virtual de Python para evitar conflictos de dependencias.

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

## ⚠️ Limitaciones (Potenciales)

- La precisión del análisis depende de la calidad y puntualidad de los datos de las APIs configuradas.
- Funcionalidades avanzadas pueden requerir suscripciones a servicios de datos adicionales.
- El rendimiento puede variar según la potencia de tu máquina, especialmente al procesar grandes cantidades de datos.

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