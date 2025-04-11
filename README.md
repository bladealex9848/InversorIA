![Logo de InversorIA](https://github.com/bladealex9848/InversorIA/blob/main/assets/logo.jpg)

# InversorIA Pro 💹 Terminal Institucional de Trading

## Descripción Detallada
**InversorIA Pro** es más que un simple asistente; es una **Terminal de Trading Integral** diseñada específicamente para las exigencias de **traders institucionales y profesionales**. Su objetivo es centralizar y potenciar el proceso de toma de decisiones combinando análisis cuantitativo avanzado, visualización de datos interactiva y la potencia de la inteligencia artificial contextualizada.

Esta plataforma integra de forma fluida:
* **Análisis Técnico Profundo:** Desde patrones clásicos hasta indicadores avanzados y detección automática de niveles.
* **Estrategias de Opciones Sofisticadas:** Incluyendo análisis de la superficie de volatilidad y recomendaciones estratégicas.
* **Perspectiva Multitemporal:** Para confirmar la robustez de las señales a través de diferentes horizontes de inversión.
* **Inteligencia de Mercado en Tiempo Real:** Incorporando análisis de sentimiento, noticias relevantes y datos fundamentales.
* **Descubrimiento de Oportunidades:** Mediante un scanner de mercado configurable y eficiente.
* **Asistencia IA Contextual:** Un copiloto inteligente que entiende el estado actual del mercado y del activo analizado.

InversorIA Pro busca capacitar a los traders para que operen con mayor confianza, eficiencia y una perspectiva basada en datos, todo dentro de un entorno unificado.

## 🎬 Video Demostrativo

Mira este video para ver InversorIA Pro en acción, mostrando un flujo de trabajo completo desde el escaneo de mercado hasta la validación y toma de decisiones usando uCharts:

<iframe width="560" height="315" src="https://www.youtube.com/embed/UmGnJHiLDEA?si=7r4XPdHUmJQrf8Ng" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

*(Nota: Si el video no se carga, asegúrate de que la URL en el `src` sea correcta y accesible).*

## Funcionalidades Clave Explicadas
* **🔐 Autenticación Segura:** Protege el acceso a la terminal, garantizando la privacidad de tu análisis y configuración.
* **📊 Dashboard Interactivo:** Visualiza toda la información relevante de un activo en un solo lugar, con pestañas dedicadas para cada tipo de análisis (Técnico, Opciones, Multiframe, Experto IA, Noticias/Sentimiento).
* **📈 Análisis Técnico Avanzado:**
    * **Tendencias:** Identifica la dirección predominante del mercado usando múltiples indicadores (Medias Móviles, MACD).
    * **Patrones y Niveles:** Detecta automáticamente formaciones de velas significativas, soportes, resistencias, líneas de tendencia y canales, dibujándolos directamente en el gráfico para una fácil interpretación.
    * **Indicadores Clave:** Calcula y muestra RSI (con niveles de sobrecompra/venta), MACD (con histograma y línea de señal), Bandas de Bollinger (para volatilidad y posibles reversiones) y ATR (para medir la volatilidad y ayudar en la colocación de stops).
* **🎯 Análisis de Opciones:**
    * **Superficie de Volatilidad:** Visualiza en 3D cómo varía la volatilidad implícita según el strike y el vencimiento, crucial para identificar opciones baratas o caras.
    * **Estrategias Sugeridas:** Basado en el análisis técnico y de volatilidad, propone estrategias adecuadas (Spreads, Condors, etc.) para diferentes escenarios (alcista, bajista, neutral).
    * **IV vs HV:** Compara la volatilidad implícita (expectativa del mercado) con la histórica (realizada) para evaluar primas.
* **⏳ Análisis Multiframe:** Compara señales (tendencia, momentum) en gráficos diarios, semanales y mensuales. Una fuerte alineación aumenta la confianza en la señal; las divergencias pueden indicar posibles giros o debilidad.
* **📰 Análisis Fundamental y de Mercado:**
    * **Datos Fundamentales:** Accede a métricas clave de la empresa (si aplica) para complementar el análisis técnico.
    * **Sentimiento y Noticias:** Mide el "mood" del mercado hacia un activo analizando noticias recientes y proporciona un feed para entender el contexto narrativo.
    * **Insights Web:** Resume análisis o menciones relevantes de fuentes externas.
* **🔍 Scanner de Mercado:**
    * **Exploración Eficiente:** Filtra rápidamente el universo de activos por sector.
    * **Detección de Oportunidades:** Encuentra activos que cumplen criterios técnicos o de opciones predefinidos (ej. RSI en sobreventa, cruce de medias, alta probabilidad en spreads).
    * **Priorización:** Ordena los resultados por confianza de la señal o ratio Riesgo/Recompensa (R/R).
* **🧠 Asistente IA Especializado:**
    * **Análisis Integrado:** Pide al IA un resumen experto que combine todos los análisis disponibles (técnico, opciones, sentimiento).
    * **Consultas Específicas:** Pregunta dudas concretas ("¿Cuál es el soporte más cercano?", "¿Qué estrategia usar si espero baja volatilidad?").
    * **Contexto Persistente:** El IA recuerda el activo que estás analizando y el estado general del mercado.
* **🛡️ Gestión de Riesgo:** Pestaña dedicada para visualizar métricas de riesgo (detalles a implementar según `trading_dashboard`).
* **📄 Reportes:** Capacidad de generar informes consolidados del análisis (detalles a implementar según `trading_dashboard`).

## Cómo Sacarle el Máximo Provecho a InversorIA Pro

InversorIA Pro está diseñado para un flujo de trabajo analítico. Aquí tienes una guía paso a paso:

1.  **Configuración Inicial Optimizada:**
    * Asegúrate de tener todas las API keys necesarias en `secrets.toml`. Claves como `ALPHA_VANTAGE_API_KEY`, `YOU_API_KEY` o `TAVILY_API_KEY` habilitarán análisis de noticias, sentimiento e insights web más ricos.
    * Utiliza un entorno virtual de Python (`venv` o `conda`) para evitar conflictos de dependencias.

2.  **Vista Panorámica con el Scanner (Pestaña "Scanner de Mercado"):**
    * **Inicia aquí:** Selecciona los sectores que te interesan y ejecuta el scanner. Es tu radar para encontrar posibles operaciones.
    * **Filtra Inteligentemente:** Usa los filtros para reducir el ruido. Filtra por señal (Alcista/Bajista), estrategia (CALL/PUT) o "Alta Confianza" para ver las configuraciones más prometedoras.
    * **Prioriza por R/R:** Observa la columna "R/R" para identificar setups con potencial de recompensa favorable frente al riesgo asumido.

3.  **Análisis Profundo del Candidato (Pestaña "Análisis Individual"):**
    * **Selecciona el Activo:** Elige un símbolo interesante del scanner o introduce uno directamente.
    * **Pestaña Técnica:**
        * Estudia el gráfico: Observa la acción del precio, los patrones de velas y los niveles técnicos dibujados.
        * Valida Indicadores: Comprueba el RSI, MACD y la posición respecto a las Medias Móviles. ¿Confirman la señal del scanner?
    * **Pestaña Opciones:**
        * Analiza la Volatilidad: ¿La IV es alta o baja comparada con la HV y su propio histórico? ¿Hay skew? Esto informa qué tipo de estrategia es más adecuada (comprar o vender prima).
        * Evalúa Estrategias: Revisa las sugerencias y la superficie de volatilidad.
    * **Pestaña Multiframe:**
        * Confirma la Tendencia: ¿Las señales diaria, semanal y mensual están alineadas? Una fuerte alineación da más confianza. Una divergencia (ej. diario alcista pero semanal bajista) sugiere cautela o un posible giro.
    * **Pestaña Noticias/Sentimiento:**
        * Entiende el Contexto: ¿Hay noticias recientes importantes? ¿Cómo está el sentimiento general? Esto puede afectar la fuerza o duración de un movimiento técnico.
    * **Pestaña Análisis Experto:**
        * Consolida la Información: Solicita un análisis al IA para obtener una visión integrada y una recomendación final basada en todos los datos procesados.

4.  **Dialoga con el Experto IA (Panel de Chat):**
    * **Resuelve Dudas:** Si algo no está claro en el análisis, pregunta directamente ("Explícame el cruce de medias", "¿Por qué recomiendas esa estrategia de opciones?").
    * **Simula Escenarios:** Pregunta sobre situaciones hipotéticas ("¿Qué pasa si el VIX sube a 30?", "¿Cómo ajustarías el stop si rompe la resistencia R1?").
    * **Personaliza Estrategias:** Pide ajustes a las estrategias sugeridas ("¿Puedes darme los strikes para un Iron Condor más conservador?").

5.  **Define tu Plan de Trading:**
    * Basado en todo el análisis, define puntos claros de entrada, stop-loss (quizás usando el ATR mostrado en el análisis técnico) y objetivos de beneficio (basados en niveles técnicos o R/R).

6.  **Monitoreo y Ajuste:**
    * Usa el scanner periódicamente para nuevas oportunidades.
    * Revisa tus posiciones abiertas usando el dashboard individual para ver si las condiciones han cambiado.
    * Utiliza la acción "Limpiar Caché" en la barra lateral si sospechas que los datos no están actualizados.

## Limitaciones (Potenciales)
* La precisión del análisis depende de la calidad y puntualidad de los datos de las APIs configuradas. Verifica el estado de las APIs si encuentras problemas.
* Funcionalidades como análisis de sentimiento profundo, noticias en tiempo real o datos fundamentales extensivos pueden requerir suscripciones o API keys adicionales de proveedores específicos.
* El rendimiento puede variar según la potencia de tu máquina, especialmente al procesar grandes cantidades de datos o múltiples timeframes simultáneamente.

## Instalación

1.  **Prerrequisitos:** Asegúrate de tener Python 3.8 o superior y `pip` instalados.
2.  **Entorno Virtual (Recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```
3.  **Clonar Repositorio:**
    ```bash
    git clone <URL-DEL-REPOSITORIO-PRO> # Reemplaza con la URL correcta
    cd InversorIA-Pro # Ajusta el nombre si es diferente
    ```
4.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
    * *Nota: El archivo `requirements.txt` debe listar todas las librerías necesarias: `streamlit`, `pandas`, `numpy`, `plotly`, `pytz`, `requests`, `openai`, `yfinance`, `ta`, `scikit-learn`, `scipy`, `statsmodels`, `beautifulsoup4`, `tavily-python`, etc., y cualquier dependencia de los módulos custom.*
5.  **Configurar Credenciales:**
    * Crea la carpeta `.streamlit` si no existe en el directorio raíz del proyecto.
    * Dentro de `.streamlit`, crea el archivo `secrets.toml`.
    * Añade tus credenciales (ver ejemplo abajo). **¡Nunca compartas este archivo!**
    ```toml
    # --- Obligatorias ---
    OPENAI_API_KEY = "sk-..."
    ASSISTANT_ID = "asst_..." # Si usas la API de Asistentes OpenAI

    # Contraseña para acceder a la aplicación
    PASSWORD = "tu-contraseña-muy-segura"

    # --- Opcionales (Habilitan más funcionalidades) ---
    # ALPHA_VANTAGE_API_KEY = "tu-alpha-vantage-key" # Para noticias y fundamentales
    # YOU_API_KEY = "tu-you-com-key" # Para búsqueda web IA / análisis de sentimiento
    # TAVILY_API_KEY = "tu-tavily-key" # Alternativa para búsqueda web IA
    # FINNHUB_API_KEY = "tu-finnhub-key" # Fuente alternativa de datos de mercado/opciones
    # ... otras claves que tus módulos puedan necesitar ...
    ```
6.  **Variables de Entorno (Alternativa):** Puedes configurar las claves API como variables de entorno (ej. `export OPENAI_API_KEY="sk-..."`) en lugar de usar `secrets.toml`.

## Uso

1.  **Iniciar la Aplicación:** Abre tu terminal, activa tu entorno virtual (si usaste uno), navega al directorio del proyecto y ejecuta:
    ```bash
    streamlit run app.py
    ```
2.  **Acceder:** Abre tu navegador web y ve a la dirección URL local que proporciona Streamlit (normalmente `http://localhost:8501`).
3.  **Autenticación:** Ingresa la contraseña que configuraste en el archivo `secrets.toml`.
4.  **Navegación:**
    * Usa las pestañas principales ("Análisis Individual", "Scanner de Mercado") para cambiar entre modos.
    * En "Análisis Individual", utiliza los menús desplegables para seleccionar el Sector, Activo y Timeframe.
    * Explora las sub-pestañas dentro de "Análisis Individual" para ver los diferentes tipos de análisis.
5.  **Interactuar con IA:** Escribe tus preguntas o solicitudes en el cuadro de chat del panel derecho.
6.  **Acciones Rápidas (Sidebar):** Usa los botones en la barra lateral para limpiar el caché de datos, ver el estado del sistema o limpiar el historial del chat.

## Contribuciones

¡Tus contribuciones son bienvenidas! Si deseas mejorar InversorIA Pro:
1.  Haz un fork del repositorio.
2.  Crea una nueva rama para tus cambios (`git checkout -b feature/nueva-funcionalidad`).
3.  Realiza tus modificaciones y haz commit (`git commit -am 'Añade nueva funcionalidad X'`).
4.  Empuja tus cambios a tu fork (`git push origin feature/nueva-funcionalidad`).
5.  Abre un Pull Request en el repositorio original, explicando claramente tus cambios y por qué son beneficiosos.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para obtener más información.

## Autor

Creado por Alexander Oviedo Fadul

[GitHub](https://github.com/bladealex9848) | [Website](https://alexanderoviedofadul.dev) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)