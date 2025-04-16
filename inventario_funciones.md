# Inventario de Funciones - InversorIA

Este documento contiene un inventario detallado de las funciones y clases presentes en el proyecto InversorIA, incluyendo su ubicación, propósito y líneas de código.

## Archivo Principal: 📊_InversorIA_Pro.py

### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| NumpyEncoder | Codificador JSON personalizado para manejar tipos de NumPy | 110-132 |
| DataCache | Gestiona el caché de datos de mercado con invalidación por tiempo | 1176-1232 |
| MarketScanner | Escanea el mercado en busca de oportunidades de trading | 1234-1376 |

### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| create_technical_chart | Crea gráficos técnicos avanzados con indicadores y patrones | 1384-1864 |
| format_patterns_for_prompt | Formatea patrones técnicos para incluirlos en prompts de IA | 1865-1928 |
| process_message_with_citations | Extrae y devuelve el texto del mensaje del asistente | 1930-1947 |
| process_expert_analysis | Procesa análisis experto con OpenAI y contexto de mercado | 1949-2219 |
| display_expert_opinion | Muestra la opinión del experto IA con formato mejorado | 2221-2364 |
| display_sentiment_analysis | Muestra análisis de sentimiento en la interfaz | 2471-2600 |
| display_news_feed | Muestra noticias relevantes en la interfaz | 2601-2634 |
| display_web_insights | Muestra insights web en la interfaz | 2635-2667 |
| get_company_info | Obtiene información detallada de la empresa | 2668-2692 |
| display_technical_summary | Muestra resumen técnico en la interfaz | 2693-2750 |

## Archivos Auxiliares

### market_utils.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| MarketDataError | Excepción personalizada para errores de datos de mercado | 33-36 |
| DataCache | Gestiona el caché de datos de mercado con invalidación por tiempo | 44-99 |
| OptionsParameterManager | Gestiona parámetros para análisis de opciones | 607-1409 |
| TechnicalAnalyzer | Realiza análisis técnico avanzado de datos de mercado | 1410-3617 |
| TechnicalAnalyzer_Legacy | Versión anterior del analizador técnico (mantenida por compatibilidad) | 3618-3640 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| validate_market_data | Valida la integridad de los datos de mercado | 110-149 |
| validate_and_fix_data | Valida y corrige problemas en datos de mercado | 151-199 |
| _get_api_key | Obtiene claves API desde secrets o variables de entorno | 206-217 |
| _generate_synthetic_data | Genera datos sintéticos robustos para fallback de interfaz | 220-324 |
| _get_alpha_vantage_data | Obtiene datos desde Alpha Vantage como respaldo | 326-391 |
| _get_finnhub_data | Obtiene datos desde Finnhub como respaldo adicional | 393-449 |
| _get_marketstack_data | Obtiene datos desde MarketStack como otra fuente alternativa | 451-499 |
| fetch_market_data | Función principal para obtener datos de mercado de múltiples fuentes | 505-606 |
| get_market_context | Obtiene contexto completo de mercado para un símbolo | 2000-2529 |
| get_vix_level | Obtiene el nivel actual del VIX y su interpretación | 2530-2541 |
| get_api_keys_from_secrets | Obtiene claves API desde secrets.toml | 2542-2560 |

### technical_analysis.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| detect_support_resistance | Detecta niveles de soporte y resistencia con análisis multi-timeframe | 15-112 |
| detect_trend_lines | Detecta líneas de tendencia alcistas y bajistas con algoritmo adaptativo | 114-236 |
| detect_channels | Detecta canales de precio basados en líneas de tendencia | 238-324 |
| improve_technical_analysis | Mejora indicadores técnicos y corrige valores N/A | 326-448 |
| improve_sentiment_analysis | Mejora el análisis de sentimiento y muestra fuentes | 450-608 |
| detect_improved_patterns | Detecta patrones mejorados en los datos con algoritmos avanzados | 609-709 |
| detect_classic_chart_patterns | Detecta patrones clásicos de gráficos (cabeza y hombros, triángulos, etc.) | 710-818 |
| detect_candle_patterns | Detecta patrones de velas japonesas con clasificación de fuerza | 819-1037 |
| calculate_volume_profile | Calcula el perfil de volumen para análisis de liquidez | 1038-1138 |

### market_scanner.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| MarketScanner | Escanea el mercado en busca de oportunidades de trading | 11-92 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| display_opportunities | Muestra oportunidades de trading en Streamlit | 93-175 |
| run_scanner | Ejecuta el escáner de mercado con interfaz visual | 176-184 |

## Archivos en el directorio 'pages'

### 1_📈_Analizador_de_Acciones_Pro.py
Interfaz simplificada para análisis de acciones individuales.

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| get_popular_symbols | Obtiene una lista de símbolos populares por categoría | 15-30 |
| fetch_data | Obtiene datos de mercado para un símbolo específico | 32-50 |
| create_chart | Crea un gráfico técnico básico | 52-120 |
| analyze_data | Realiza análisis básico de datos de mercado | 122-180 |
| display_summary | Muestra un resumen del análisis | 182-220 |
| main | Función principal que controla la interfaz | 222-280 |

### 2_🤖_Inversor_Bot.py
Asistente conversacional para consultas sobre inversiones.

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| InvestmentAdvisor | Proporciona recomendaciones de inversión | 20-150 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| process_query | Procesa consultas del usuario | 152-200 |
| generate_response | Genera respuestas basadas en el contexto | 202-250 |
| display_chat_interface | Muestra la interfaz de chat | 252-300 |
| main | Función principal de la aplicación | 302-350 |

### 3_📊_InversorIA_Mini.py
Versión reducida de la plataforma principal con funcionalidades básicas.

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| MarketDataProvider | Proveedor de datos de mercado simplificado | 25-120 |
| SimpleAnalyzer | Analizador técnico simplificado | 122-250 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| create_simple_chart | Crea gráficos técnicos simplificados | 252-350 |
| display_mini_dashboard | Muestra un dashboard simplificado | 352-420 |
| main | Función principal de la aplicación | 422-500 |

### 4_📈_MarketIntel_Options_Analyzer.py
Analizador especializado en opciones financieras.

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| OptionsAnalyzer | Analiza estrategias de opciones | 30-200 |
| VolatilityCalculator | Calcula y analiza la volatilidad | 202-300 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| calculate_greeks | Calcula los griegos de las opciones | 302-350 |
| display_options_chain | Muestra la cadena de opciones | 352-400 |
| plot_volatility_surface | Grafica la superficie de volatilidad | 402-450 |
| consult_expert_ia | Consulta al experto IA sobre opciones | 452-500 |
| main | Función principal de la aplicación | 502-550 |

### 5_📈_Technical_Expert_Analyzer.py
Analizador técnico avanzado con enfoque en patrones y niveles.

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| PatternDetector | Detecta patrones técnicos avanzados | 40-150 |
| LevelAnalyzer | Analiza niveles clave de soporte/resistencia | 152-250 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| detect_advanced_patterns | Detecta patrones técnicos avanzados | 252-350 |
| analyze_market_structure | Analiza la estructura del mercado | 352-450 |
| display_technical_dashboard | Muestra dashboard técnico avanzado | 452-550 |
| display_session_info | Muestra información de la sesión | 552-600 |
| main | Función principal de la aplicación | 602-700 |

### 6_📊_InversorIA.py
Versión anterior de la plataforma principal, mantenida por compatibilidad.

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| LegacyDataProvider | Proveedor de datos de la versión anterior | 30-120 |
| LegacyAnalyzer | Analizador de la versión anterior | 122-250 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| render_technical_tab | Renderiza pestaña de análisis técnico | 252-350 |
| render_options_tab | Renderiza pestaña de opciones | 352-450 |
| render_multiframe_tab | Renderiza pestaña multi-timeframe | 452-550 |
| main | Función principal de la aplicación | 552-650 |

### 7_🔔_Notificaciones.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| RealTimeSignalAnalyzer | Analiza señales de trading en tiempo real usando datos del mercado | 90-934 |
| DatabaseManager | Gestiona la conexión y operaciones con la base de datos MariaDB | 1132-1393 |
| EmailManager | Gestiona el envío de correos electrónicos con boletines de trading | 1394-1867 |
| SignalManager | Gestiona las señales de trading y su procesamiento | 1868-1975 |

#### Métodos Principales de RealTimeSignalAnalyzer

| Método | Descripción | Líneas |
|--------|-------------|--------|
| scan_market_by_sector | Escanea el mercado por sector para encontrar señales de trading | 170-357 |
| get_detailed_analysis | Genera análisis detallado para un símbolo específico | 359-556 |
| get_real_time_market_sentiment | Obtiene el sentimiento actual del mercado en tiempo real | 557-711 |
| get_real_time_market_news | Obtiene noticias relevantes del mercado en tiempo real | 712-834 |
| _create_basic_analysis | Crea un análisis básico para un símbolo usando datos técnicos | 835-934 |

#### Métodos Principales de DatabaseManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| connect | Establece conexión con la base de datos | 1150-1170 |
| disconnect | Cierra la conexión con la base de datos | 1172-1180 |
| execute_query | Ejecuta una consulta SQL en la base de datos | 1182-1210 |
| save_signal | Guarda una señal de trading en la base de datos | 1299-1316 |
| log_email_sent | Registra el envío de un correo electrónico | 1318-1331 |
| save_market_sentiment | Guarda el sentimiento del mercado en la base de datos | 1333-1362 |
| save_market_news | Guarda una noticia del mercado en la base de datos | 1364-1390 |

#### Métodos Principales de EmailManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| send_email | Envía un correo electrónico con contenido HTML y opcionalmente imágenes | 1413-1553 |
| create_newsletter_html | Crea el contenido HTML para el boletín de trading | 1555-1866 |

#### Métodos Principales de SignalManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| generate_signals | Genera señales de trading en tiempo real | 1880-1903 |
| send_newsletter | Envía un boletín con señales de trading | 1905-1975 |

## Conclusiones

El proyecto InversorIA es una plataforma compleja y bien estructurada para análisis de mercados financieros, con las siguientes características principales:

1. **Arquitectura modular**: El código está organizado en módulos especializados que se encargan de diferentes aspectos del análisis financiero.

2. **Componentes principales**:
   - Análisis técnico avanzado (patrones, soportes/resistencias, indicadores)
   - Análisis de opciones financieras
   - Escaner de mercado para identificar oportunidades
   - Sistema de notificaciones y boletines
   - Integración con IA para análisis experto

3. **Estructura de archivos**:
   - Archivo principal (`📊_InversorIA_Pro.py`): Contiene la interfaz principal y la lógica central
   - Archivos auxiliares: Contienen funcionalidades específicas (análisis técnico, obtención de datos, etc.)
   - Directorio 'pages': Contiene módulos complementarios accesibles desde la interfaz principal

4. **Patrones de diseño**:
   - Uso de clases para encapsular funcionalidades relacionadas
   - Sistema de caché para optimizar el rendimiento
   - Manejo de errores y fallbacks para garantizar la robustez
   - Separación de la lógica de negocio y la presentación

Este inventario proporciona una visión general de las funciones y clases disponibles en el proyecto, facilitando la navegación y comprensión del código para futuros desarrollos y mantenimiento.

