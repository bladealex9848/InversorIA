# Inventario de Funciones y Clases

Este documento contiene un inventario de todas las funciones y clases del proyecto InversorIA. Sirve como referencia para desarrolladores y agentes de IA que trabajan en el proyecto.

**Última actualización:** `17/04/2025` (Actualizado por agente de IA)

> **Nota**: Este inventario se debe actualizar cada vez que se añadan, modifiquen o eliminen funciones o clases del proyecto.

## Estructura del Proyecto

El proyecto sigue la estructura definida en `PROJECT_STRUCTURE_GUIDE.md` y `STRUCTURE_GUIDE.md`. Todos los archivos temporales deben almacenarse en la carpeta `temp/` y el código antiguo o no utilizado debe moverse a `legacy_code/`.

### Archivos Principales

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `📊_InversorIA_Pro.py` | Aplicación principal | Activo |
| `market_utils.py` | Utilidades para datos de mercado | Activo |
| `technical_analysis.py` | Funciones de análisis técnico | Activo |
| `ai_utils.py` | Utilidades para procesamiento con IA | Activo |
| `database_utils.py` | Utilidades para base de datos | Activo |
| `signal_analyzer.py` | Analizador de señales | Activo |
| `signal_manager.py` | Gestor de señales | Activo |
| `news_processor.py` | Procesador de noticias | Activo |
| `news_sentiment_analyzer.py` | Analizador de sentimiento | Activo |
| `yahoo_finance_scraper.py` | Scraper para Yahoo Finance | Activo |
| `visualization_utils.py` | Utilidades de visualización | Activo |
| `company_data.py` | Datos de compañías | Activo |
| `enhanced_market_scanner_fixed.py` | Scanner de mercado mejorado | Activo |
| `pandas_config.py` | Configuración de pandas | Activo |
| `openai_utils.py` | Utilidades para OpenAI | Activo |
| `authenticator.py` | Sistema de autenticación | Activo |

### Carpetas Principales

| Carpeta | Descripción | Contenido |
|---------|-------------|----------|
| `pages/` | Páginas adicionales | 7 páginas de la aplicación |
| `components/` | Componentes UI | Componentes reutilizables de la interfaz |
| `utils/` | Utilidades | Funciones y clases de utilidad general |
| `styles/` | Estilos | Archivos CSS para la apariencia |
| `temp/` | Temporales | Archivos temporales generados en ejecución |
| `legacy_code/` | Código antiguo | Código no utilizado pero conservado como referencia |
| `legacy_code/tests/` | Pruebas antiguas | Scripts de prueba antiguos |
| `legacy_code/dev_utils/` | Utilidades de desarrollo | Scripts para desarrollo y mantenimiento |
| `legacy_code/old_versions/` | Versiones antiguas | Versiones anteriores de archivos actuales |
| `legacy_code/docs/` | Documentación antigua | Documentación reemplazada o antigua |
| `legacy_code/sql/` | SQL antiguo | Scripts SQL antiguos o de referencia |

## Inventario Detallado

### 📊_InversorIA_Pro.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `NumpyEncoder` | Encoder personalizado para manejar diversos tipos de datos NumPy y Pandas | 117-605 |
| `DataCache` | Sistema de caché con invalidación por tiempo | 607-663 |
| `MarketScanner` | Escáner de mercado con detección de estrategias | 665-813 |
| `DatabaseManager` | Gestiona la conexión y operaciones con la base de datos | 815-1269 |
| `RealTimeSignalAnalyzer` | Analiza el mercado en tiempo real para generar señales de trading | 1271-1844 |
| `SignalManager` | Gestiona las señales de trading y su procesamiento | 1846-2076 |

##### Métodos de NumpyEncoder

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `default` | Sin descripción disponible | 120-139 |

##### Métodos de DataCache

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 610-615 |
| `get` | Obtiene dato del caché si es válido | 617-625 |
| `set` | Almacena dato en caché con timestamp | 627-629 |
| `clear` | Limpia caché completo | 631-636 |
| `can_request` | Controla frecuencia de solicitudes por símbolo | 638-648 |
| `get_stats` | Retorna estadísticas del caché | 650-662 |

##### Métodos de MarketScanner

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 668-672 |
| `get_cached_analysis` | Obtiene análisis cacheado si existe | 674-678 |
| `scan_market` | Ejecuta escaneo de mercado enfocado en sectores seleccionados | 680-807 |

##### Métodos de DatabaseManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de base de datos | 818-821 |
| `_get_db_config` | Obtiene la configuración de la base de datos desde secrets.toml | 823-867 |
| `connect` | Establece conexión con la base de datos | 869-988 |
| `disconnect` | Cierra la conexión con la base de datos | 990-993 |
| `execute_query` | Ejecuta una consulta SQL y devuelve los resultados | 995-1029 |
| `get_signals` | Obtiene señales de trading filtradas | 1031-1050 |
| `save_signal` | Guarda una señal de trading en la base de datos con información detallada | 1052-1142 |
| `log_email_sent` | Registra el envío de un correo electrónico | 1144-1183 |
| `save_market_sentiment` | Guarda datos de sentimiento de mercado | 1185-1224 |
| `save_market_news` | Guarda noticias de mercado | 1226-1264 |

##### Métodos de RealTimeSignalAnalyzer

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el analizador de señales en tiempo real | 1274-1288 |
| `scan_market_by_sector` | Escanea el mercado por sector para encontrar señales de trading en tiempo real | 1290-1601 |
| `get_real_time_market_sentiment` | Obtiene el sentimiento actual del mercado en tiempo real | 1603-1739 |
| `get_market_news` | Obtiene noticias relevantes del mercado en tiempo real | 1741-1843 |

##### Métodos de SignalManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de señales | 1849-1852 |
| `get_active_signals` | Obtiene las señales activas filtradas | 1854-2059 |
| `get_market_sentiment` | Obtiene el sentimiento actual del mercado en tiempo real | 2061-2063 |
| `get_market_news` | Obtiene noticias relevantes del mercado | 2065-2067 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `create_technical_chart` | Crea gráfico técnico avanzado con indicadores y patrones técnicos | 2078-2556 |
| `format_patterns_for_prompt` | Formatea los patrones técnicos para incluirlos en el prompt del asistente IA | 2559-2621 |
| `process_message_with_citations` | Extrae y devuelve el texto del mensaje del asistente con manejo mejorado de errores | 2624-2640 |
| `process_expert_analysis` | Procesa análisis experto con OpenAI asegurando una sección de análisis fundamental | 2643-2912 |
| `display_expert_opinion` | Muestra la opinión del experto IA con formato mejorado y opción de exportar a MD | 2915-3157 |
| `display_sentiment_analysis` | Muestra análisis de sentimiento integrado desde MarketIntel | 3165-3292 |
| `display_news_feed` | Muestra feed de noticias integrado desde MarketIntel | 3295-3326 |
| `display_web_insights` | Muestra insights de búsqueda web integrado desde MarketIntel | 3329-3354 |
| `display_technical_summary` | Muestra resumen técnico en un formato mejorado | 3364-3443 |
| `display_options_analysis` | Muestra análisis de opciones en formato mejorado | 3446-3548 |
| `display_asset_info` | Muestra información básica del activo compatible con modo claro y oscuro | 3551-3601 |
| `process_chat_input_with_openai` | Procesa la entrada del chat utilizando OpenAI para respuestas más naturales y variadas. | 3609-3650 |
| `process_with_assistant` | Procesa el mensaje utilizando la API de Asistentes de OpenAI con manejo mejorado | 3653-3796 |
| `process_with_chat_completion` | Procesa el mensaje utilizando la API de Chat Completion de OpenAI | 3799-3900 |
| `fallback_analyze_symbol` | Función de respaldo para analizar símbolos cuando OpenAI no está disponible | 3903-4267 |
| `initialize_session_state` | Inicializa el estado de la sesión | 4275-4339 |
| `render_sidebar` | Renderiza el panel lateral con información profesional y estado del mercado | 4342-4629 |
| `analyze_market_data` | Analiza datos de mercado con indicadores técnicos avanzados | 4637-4734 |
| `render_enhanced_dashboard` | Renderiza un dashboard mejorado con análisis técnico avanzado y manejo de fallos | 4737-5863 |
| `setup_openai` | Configura credenciales de OpenAI con manejo mejorado de errores | 5871-5972 |
| `check_api_keys` | Verifica las API keys disponibles en secret.toml o env vars | 5980-6055 |
| `check_libraries` | Verifica la disponibilidad de las bibliotecas necesarias | 6058-6110 |
| `display_system_status` | Muestra el estado del sistema, APIs y librerías con diseño mejorado | 6113-6290 |
| `check_authentication` | Verifica autenticación del usuario con interfaz mejorada | 6298-6376 |
| `main` | Función principal de la aplicación | 6384-7983 |

## Archivos Auxiliares y Utilidades

### market_utils.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `MarketDataError` | Excepción personalizada para errores de datos de mercado | 33-42 |
| `DataCache` | Sistema avanzado de caché con invalidación por tiempo | 44-108 |
| `OptionsParameterManager` | Gestiona parámetros para trading de opciones basados en categoría de activo | 607-1408 |
| `TechnicalAnalyzer` | Analizador técnico avanzado con manejo profesional de indicadores | 1410-2528 |
| `TechnicalAnalyzer_Legacy` | Versión legada de TechnicalAnalyzer para compatibilidad | 3624-3625 |

##### Métodos de DataCache

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 47-52 |
| `get` | Obtiene dato del caché si es válido | 54-62 |
| `set` | Almacena dato en caché con timestamp | 64-66 |
| `clear` | Limpia caché completo | 68-73 |
| `can_request` | Controla frecuencia de solicitudes por símbolo | 75-85 |
| `get_stats` | Retorna estadísticas del caché | 87-99 |

##### Métodos de OptionsParameterManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 610-1352 |
| `get_symbol_params` | Obtiene parámetros específicos para un símbolo | 1354-1356 |
| `get_strategy_recommendations` | Obtiene estrategias recomendadas según tendencia | 1358-1369 |
| `get_volatility_adjustments` | Obtiene ajustes recomendados según nivel de VIX | 1371-1402 |

##### Métodos de TechnicalAnalyzer

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el analizador con validación de datos | 1413-1418 |
| `calculate_indicators` | Calcula indicadores técnicos con validación avanzada | 1420-1624 |
| `get_current_signals` | Obtiene señales actuales con validación robusta | 1626-1864 |
| `_analyze_options_strategy` | Recomienda estrategia de opciones basada en señales | 1866-1977 |
| `_get_rsi_condition` | Determina la condición del RSI | 1979-1986 |
| `_get_price_position` | Determina la posición del precio respecto a las bandas | 1988-2002 |
| `_get_volatility_state` | Evalúa el estado de la volatilidad | 2004-2026 |
| `_calculate_overall_signal` | Calcula la señal general basada en todos los indicadores | 2028-2113 |
| `analyze_multi_timeframe` | Analiza múltiples timeframes para un símbolo | 2115-2238 |
| `get_candle_patterns` | Identifica patrones de velas comunes en los datos | 2240-2428 |
| `get_support_resistance` | Calcula niveles de soporte y resistencia relevantes | 2430-2522 |

##### Métodos de TechnicalAnalyzer_Legacy

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 3627-3630 |
| `calculate_indicators` | Versión legada compatible con TechnicalAnalyzer original | 3632-3636 |
| `get_current_signals` | Versión legada compatible con TechnicalAnalyzer original | 3638-3645 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `validate_market_data` | Valida la integridad de los datos de mercado | 110-148 |
| `validate_and_fix_data` | Valida y corrige problemas en datos de mercado | 151-198 |
| `_get_api_key` | Obtiene clave de API desde secrets o variables de entorno | 206-217 |
| `_generate_synthetic_data` | Genera datos sintéticos robustos para fallback de interfaz | 220-323 |
| `_get_alpha_vantage_data` | Obtiene datos desde Alpha Vantage como respaldo | 326-390 |
| `_get_finnhub_data` | Obtiene datos desde Finnhub como respaldo adicional | 393-448 |
| `_get_marketstack_data` | Obtiene datos desde MarketStack como otra fuente alternativa | 451-502 |
| `fetch_market_data` | Obtiene datos de mercado con múltiples fallbacks y validación. | 505-599 |
| `get_vix_level` | Obtiene el nivel actual del VIX con manejo de errores | 2530-2539 |
| `get_api_keys_from_secrets` | Obtiene claves API de secrets.toml con manejo mejorado | 2542-2635 |
| `get_market_context` | Obtiene contexto completo de mercado para un símbolo | 2638-2719 |
| `fetch_news_data` | Obtiene noticias recientes para un símbolo usando múltiples fuentes con respaldo de Yahoo Finance | 2722-3003 |
| `analyze_sentiment` | Analiza el sentimiento para un símbolo basado en noticias | 3006-3060 |
| `get_web_insights` | Obtiene análisis de fuentes web sobre un símbolo mediante consultas a múltiples APIs con respaldo de Yahoo Finance | 3063-3601 |
| `clear_cache` | Limpia el caché global | 3604-3606 |
| `validate_market_data_legacy` | Versión legada de validate_market_data para compatibilidad | 3614-3616 |
| `fetch_market_data_legacy` | Versión legada de fetch_market_data para compatibilidad | 3619-3621 |

### technical_analysis.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `detect_support_resistance` | Detecta niveles de soporte y resistencia en un DataFrame de precios | 15-111 |
| `detect_trend_lines` | Detecta líneas de tendencia alcistas y bajistas en un DataFrame de precios | 114-235 |
| `detect_channels` | Detecta canales de precio basados en líneas de tendencia | 238-323 |
| `improve_technical_analysis` | Mejora los indicadores técnicos y corrige valores N/A | 326-447 |
| `improve_sentiment_analysis` | Mejora el análisis de sentimiento y muestra fuentes | 450-606 |
| `detect_improved_patterns` | Detección mejorada de patrones técnicos (tendencias, canales, soportes, resistencias) | 609-707 |
| `detect_classic_chart_patterns` | Detecta patrones clásicos de chartismo como cabeza y hombros, doble techo/suelo, etc. | 710-816 |
| `detect_candle_patterns` | Detecta patrones de velas japonesas en los datos de precios | 819-1035 |
| `calculate_volume_profile` | Calcula el perfil de volumen para identificar zonas de soporte/resistencia basadas en volumen | 1038-1137 |

### market_scanner.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `MarketScanner` | Sin descripción disponible | 12-395 |

##### Métodos de MarketScanner

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 13-20 |
| `_analyze_symbol` | Sin descripción disponible | 22-136 |
| `_analyze_symbol_with_details` | Analiza un símbolo con detalles completos para el scanner de mercado mejorado. | 138-265 |
| `get_cached_analysis` | Obtiene el último análisis cacheado para un símbolo | 267-269 |
| `scan_market` | Escanea el mercado, opcionalmente filtrando por sectores. | 271-394 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `display_opportunities` | Muestra oportunidades de trading en Streamlit con análisis detallado. | 397-764 |
| `run_scanner` | Ejecuta el scanner de mercado. | 767-775 |

### ai_utils.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `AIExpert` | Clase para procesar texto con IA utilizando OpenAI | 991-1058 |

##### Métodos de AIExpert

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el experto en IA | 996-1005 |
| `process_text` | Procesa texto con IA | 1007-1042 |
| `_fallback_process` | Método de respaldo para procesar texto | 1044-1057 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `format_patterns_for_prompt` | Formatea los patrones técnicos para incluirlos en el prompt del asistente IA | 62-119 |
| `process_message_with_citations` | Extrae y devuelve el texto del mensaje del asistente con manejo mejorado de errores | 122-138 |
| `process_expert_analysis` | Procesa análisis experto con OpenAI asegurando una sección de análisis fundamental | 141-457 |
| `process_chat_input_with_openai` | Procesa la entrada del chat utilizando OpenAI para respuestas más naturales y variadas. | 460-494 |
| `process_with_assistant` | Procesa el mensaje utilizando la API de Asistentes de OpenAI con manejo mejorado | 497-616 |
| `process_with_chat_completion` | Procesa el mensaje utilizando la API de Chat Completion de OpenAI | 619-707 |
| `process_content_with_ai` | Procesa cualquier tipo de contenido con IA para mejorar su calidad y coherencia | 710-929 |
| `get_real_news` | Obtiene noticias reales para un símbolo utilizando el procesador de noticias | 932-988 |
| `fallback_analyze_symbol` | Función de respaldo para analizar símbolos cuando OpenAI no está disponible | 1060-1158 |

### database_utils.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `DatabaseManager` | Gestiona la conexión y operaciones con la base de datos | 16-17 |

##### Métodos de DatabaseManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de base de datos | 19-22 |
| `_get_db_config` | Obtiene la configuración de la base de datos desde secrets.toml | 24-68 |
| `connect` | Establece conexión con la base de datos | 70-187 |
| `disconnect` | Cierra la conexión con la base de datos | 189-192 |
| `execute_query` | Ejecuta una consulta SQL y devuelve los resultados | 194-233 |
| `get_signals` | Obtiene señales de trading filtradas | 235-254 |
| `get_detailed_analysis` | Obtiene análisis detallado para un símbolo específico | 256-264 |
| `save_signal` | Guarda una señal de trading en la base de datos con todos los campos disponibles | 266-349 |
| `log_email_sent` | Registra el envío de un correo electrónico | 351-366 |
| `save_market_sentiment` | Guarda datos de sentimiento de mercado | 368-407 |
| `get_market_sentiment` | Obtiene datos de sentimiento de mercado | 409-416 |
| `save_market_news` | Guarda noticias de mercado | 418-456 |
| `get_market_news` | Obtiene noticias de mercado | 458-465 |

### trading_analyzer.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `TradingAnalyzer` | Analizador de trading que proporciona análisis técnico y detección de estrategias | 11-12 |

##### Métodos de TradingAnalyzer

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el analizador de trading | 14-16 |
| `get_market_data` | Obtiene datos de mercado para un símbolo | 18-78 |
| `_create_synthetic_data` | Crea datos sintéticos para pruebas cuando no se pueden obtener datos reales | 80-115 |
| `_calculate_indicators` | Calcula indicadores técnicos para un DataFrame | 117-213 |
| `analyze_trend` | Analiza la tendencia de un símbolo | 215-341 |
| `_find_support_resistance` | Encuentra niveles de soporte y resistencia | 343-424 |
| `identify_strategy` | Identifica estrategias de trading basadas en el análisis técnico | 426-570 |

### yahoo_finance_scraper.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `YahooFinanceScraper` | Clase para obtener datos y noticias de Yahoo Finance con múltiples fuentes | 46-47 |

##### Métodos de YahooFinanceScraper

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el scraper con headers para simular un navegador | 49-70 |
| `_get_cached_data` | Obtiene datos de la caché si están disponibles y no han expirado | 72-77 |
| `_cache_data` | Almacena datos en la caché con tiempo de expiración | 79-82 |
| `get_quote_data` | Obtiene datos básicos de cotización para un símbolo | 84-165 |
| `get_news` | Obtiene noticias para un símbolo desde múltiples fuentes | 167-418 |
| `get_analysis` | Obtiene análisis y recomendaciones para un símbolo | 420-551 |
| `get_options_data` | Obtiene datos de opciones para un símbolo | 553-686 |
| `get_all_data` | Obtiene todos los datos disponibles para un símbolo | 688-726 |
| `process_news_with_expert` | Procesa noticias con el experto en IA para mejorar su calidad | 728-777 |
| `_is_news_relevant` | Determina si una noticia es relevante para un símbolo | 779-826 |
| `_generate_fallback_url` | Genera una URL de respaldo basada en la fuente y el símbolo | 828-856 |
| `_parse_float` | Convierte un string a float, manejando errores | 858-867 |
| `_parse_int` | Convierte un string a int, manejando errores | 869-878 |
| `_get_news_from_google_finance` | Obtiene noticias de un símbolo utilizando Google Finance | 880-977 |
| `_get_news_from_marketwatch` | Obtiene noticias de un símbolo utilizando MarketWatch | 979-1070 |
| `_get_company_name` | Obtiene el nombre de la empresa a partir del símbolo | 1072-1107 |

### news_processor.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `NewsProcessor` | Clase para procesar noticias financieras con IA | 21-22 |
| `MockAIExpert` | Sin descripción disponible | 317-367 |

##### Métodos de NewsProcessor

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el procesador de noticias | 24-43 |
| `get_news_for_symbol` | Obtiene noticias para un símbolo | 45-177 |
| `process_with_ai` | Procesa noticias con el experto en IA | 179-275 |
| `_is_english_text` | Determina si un texto está en inglés | 277-311 |

##### Métodos de MockAIExpert

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `process_text` | Sin descripción disponible | 318-320 |

### news_sentiment_analyzer.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `NewsSentimentAnalyzer` | Clase para obtener y analizar noticias y sentimiento de mercado de fuentes fiables | 22-23 |

##### Métodos de NewsSentimentAnalyzer

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el analizador de noticias y sentimiento | 25-41 |
| `get_news_from_finnhub` | Obtiene noticias de Finnhub | 43-102 |
| `get_news_from_alpha_vantage` | Obtiene noticias de Alpha Vantage | 104-182 |
| `get_news_from_web_search` | Obtiene noticias mediante búsqueda web | 184-239 |
| `analyze_sentiment_with_ai` | Analiza el sentimiento de las noticias usando IA | 241-321 |
| `_analyze_sentiment_basic` | Analiza el sentimiento de las noticias usando un método básico | 323-396 |
| `get_consolidated_news_and_sentiment` | Obtiene noticias consolidadas y análisis de sentimiento de múltiples fuentes | 398-456 |

### signal_analyzer.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `RealTimeSignalAnalyzer` | Analiza el mercado en tiempo real para generar señales de trading | 34-35 |

##### Métodos de RealTimeSignalAnalyzer

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el analizador de señales en tiempo real | 37-51 |
| `scan_market_by_sector` | Escanea el mercado por sector para encontrar señales de trading en tiempo real | 53-254 |
| `get_detailed_analysis` | Genera análisis detallado para un símbolo específico | 256-357 |
| `get_real_time_market_sentiment` | Obtiene el sentimiento actual del mercado en tiempo real | 359-457 |
| `get_market_news` | Obtiene noticias relevantes del mercado en tiempo real | 459-558 |
| `_create_basic_analysis` | Crea un análisis básico para un símbolo cuando no hay datos disponibles | 560-588 |

### signal_manager.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `SignalManager` | Gestiona las señales de trading y su procesamiento | 22-23 |

##### Métodos de SignalManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de señales | 25-28 |
| `get_active_signals` | Obtiene las señales activas filtradas | 30-152 |
| `get_market_sentiment` | Obtiene el sentimiento actual del mercado en tiempo real | 154-156 |
| `get_market_news` | Obtiene noticias relevantes del mercado | 158-160 |
| `get_detailed_analysis` | Obtiene análisis detallado para un símbolo específico | 162-175 |
| `save_signal` | Guarda una nueva señal en la base de datos | 177-179 |
| `save_market_sentiment` | Guarda datos de sentimiento de mercado en la base de datos | 181-183 |
| `save_market_news` | Guarda noticias de mercado en la base de datos | 185-187 |
| `process_scanner_signals` | Procesa señales del scanner y las guarda en la base de datos | 189-244 |

### market_data_engine.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `ThrottlingController` | Controlador avanzado de tasas de solicitud para proveedores de datos de mercado | 30-198 |
| `MarketDataCache` | Caché para datos de mercado y resultados de búsqueda web | 200-249 |
| `WebSearchEngine` | Motor de búsqueda web con múltiples proveedores | 347-628 |
| `WebScraper` | Scraper para datos fundamentales y técnicos de acciones | 630-938 |
| `StockDataAnalyzer` | Analizador de datos de acciones para trading de opciones | 1471-1886 |

##### Métodos de ThrottlingController

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 33-59 |
| `can_request` | Determina si se puede realizar una solicitud al proveedor especificado | 61-105 |
| `get_backoff_time` | Calcula tiempo de espera adaptativo basado en la congestión del proveedor | 107-121 |
| `report_error` | Reporta un error con un proveedor para activar cooldown | 123-140 |
| `get_stats` | Obtiene estadísticas de throttling | 142-160 |
| `suggest_alternative_provider` | Sugiere un proveedor alternativo cuando uno está limitado | 162-193 |

##### Métodos de MarketDataCache

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 203-208 |
| `get` | Obtener datos de caché si son válidos | 210-219 |
| `set` | Almacenar datos en caché con timestamp | 221-224 |
| `clear` | Limpiar caché completo y retornar número de entradas eliminadas | 226-230 |
| `get_stats` | Retornar estadísticas del caché | 232-244 |

##### Métodos de WebSearchEngine

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 350-356 |
| `_get_api_key` | Obtener clave API con estrategia de fallback robusta | 358-381 |
| `search_you_api` | Buscar usando API de YOU | 383-422 |
| `search_tavily` | Buscar usando API de Tavily | 424-474 |
| `search_duckduckgo` | Buscar usando DuckDuckGo | 476-512 |
| `search_alpha_vantage_news` | Buscar noticias usando Alpha Vantage News API | 514-551 |
| `perform_web_search` | Realizar búsqueda web utilizando múltiples proveedores con throttling inteligente | 553-627 |

##### Métodos de WebScraper

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 633-638 |
| `_clean_html` | Limpia texto HTML | 640-642 |
| `scrape_yahoo_finance` | Scrape datos de Yahoo Finance | 644-758 |
| `_get_alpha_vantage_overview` | Obtener resumen de company de Alpha Vantage | 760-781 |
| `scrape_financial_news` | Scrape noticias financieras relevantes | 783-846 |
| `_get_alpha_vantage_news` | Obtener noticias desde Alpha Vantage | 848-889 |
| `get_finnhub_sentiment` | Obtener análisis de sentimiento de noticias de Finnhub | 891-937 |

##### Métodos de StockDataAnalyzer

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 1474-1482 |
| `get_stock_technical_data` | Obtiene datos técnicos históricos de una acción | 1484-1548 |
| `get_news_sentiment` | Analiza sentimiento de noticias para una acción | 1550-1662 |
| `get_options_recommendation` | Genera recomendación para operaciones de opciones | 1664-1884 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `get_api_keys_from_secrets` | Obtiene claves API de secrets.toml con manejo mejorado | 251-344 |
| `validate_market_data` | Valida la integridad de los datos de mercado | 940-978 |
| `validate_and_fix_data` | Valida y corrige problemas en datos de mercado | 981-1028 |
| `_generate_synthetic_data` | Genera datos sintéticos para fallback de interfaz | 1031-1093 |
| `_get_alpha_vantage_data` | Obtiene datos desde Alpha Vantage como respaldo | 1096-1166 |
| `_get_finnhub_data` | Obtiene datos desde Finnhub como respaldo adicional | 1169-1230 |
| `_get_marketstack_data` | Obtiene datos desde MarketStack como otra fuente alternativa | 1233-1285 |
| `fetch_market_data` | Obtiene datos de mercado con throttling inteligente, multiple fallbacks y validación. | 1288-1468 |
| `analyze_stock_options` | Función principal para análisis completo de opciones de un símbolo. | 1888-1937 |

### market_data_manager.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `MarketDataManager` | Clase para gestionar datos de mercado (noticias y sentimiento) | 55-56 |

##### Métodos de MarketDataManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de datos de mercado | 58-60 |
| `save_news_from_signal` | Guarda noticias relevantes de una señal en la tabla market_news | 62-448 |
| `save_sentiment_from_signal` | Guarda datos de sentimiento de mercado basados en una señal | 450-616 |
| `_determine_news_impact` | Determina el impacto de una noticia basado en los datos de la señal | 618-637 |
| `_extract_technical_info` | Extrae información técnica del análisis | 639-682 |
| `_extract_vix` | Extrae información del VIX del análisis | 684-718 |
| `_extract_sp500_trend` | Extrae información de la tendencia del S&P 500 | 720-753 |
| `_extract_volume_info` | Extrae información sobre el volumen | 755-766 |

### market_data_processor.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `MarketDataProcessor` | Clase para procesar datos de mercado con IA | 17-18 |

##### Métodos de MarketDataProcessor

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el procesador de datos de mercado | 20-27 |
| `process_news` | Procesa noticias para mejorar su calidad y relevancia | 29-98 |
| `process_analysis` | Procesa datos de análisis para mejorar su calidad y relevancia | 100-136 |
| `generate_expert_analysis` | Genera un análisis experto basado en los datos disponibles | 138-220 |
| `_is_news_relevant` | Determina si una noticia es relevante para un símbolo | 222-256 |
| `_generate_fallback_url` | Genera una URL de respaldo basada en la fuente y el símbolo | 258-284 |

### market_data_throttling.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `ThrottlingController` | Controlador avanzado de tasas de solicitud para proveedores de datos de mercado | 16-17 |

##### Métodos de ThrottlingController

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 19-66 |
| `normalize_provider_name` | Normaliza el nombre del proveedor para manejar diferentes variantes | 68-84 |
| `can_request` | Determina si se puede realizar una solicitud al proveedor especificado | 86-139 |
| `get_backoff_time` | Calcula tiempo de espera adaptativo basado en la congestión del proveedor | 141-157 |
| `report_error` | Reporta un error con un proveedor para activar cooldown | 159-179 |
| `get_stats` | Obtiene estadísticas de throttling | 181-199 |
| `suggest_alternative_provider` | Sugiere un proveedor alternativo cuando uno está limitado | 201-236 |

### enhanced_market_data.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `EnhancedMarketData` | Clase para obtener datos de mercado de múltiples fuentes con fallbacks | 24-25 |

##### Métodos de EnhancedMarketData

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el recolector de datos de mercado | 27-57 |
| `_get_cached_data` | Obtiene datos de la caché si están disponibles y no han expirado | 59-64 |
| `_cache_data` | Almacena datos en la caché con tiempo de expiración | 66-69 |
| `get_stock_data` | Obtiene datos completos de un símbolo utilizando múltiples fuentes | 71-147 |
| `_get_data_from_yfinance` | Obtiene datos de un símbolo utilizando yfinance | 149-251 |
| `_get_data_from_scraping` | Obtiene datos de un símbolo mediante web scraping | 253-371 |
| `_get_news_from_duckduckgo` | Obtiene noticias de un símbolo utilizando DuckDuckGo | 373-408 |
| `_get_news_from_google_finance` | Obtiene noticias de un símbolo utilizando Google Finance | 410-482 |
| `_get_company_name` | Obtiene el nombre de la empresa a partir del símbolo | 484-517 |
| `_merge_dict` | Combina dos diccionarios de forma recursiva, actualizando solo los valores vacíos | 519-537 |
| `process_with_expert` | Procesa los datos con el agente experto para mejorar la calidad | 539-551 |

### enhanced_market_scanner.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `render_enhanced_market_scanner` | Función extraída con regex | 23-43 |

### enhanced_market_scanner_fixed.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `render_enhanced_market_scanner` | Renderiza la versión mejorada del scanner de mercado. | 20-2490 |

### trading_dashboard.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `create_advanced_chart` | Crea gráfico técnico avanzado con análisis institucional | 18-171 |
| `render_technical_metrics` | Renderiza métricas técnicas resumidas | 174-236 |
| `render_signal_summary` | Renderiza resumen de señales de trading | 239-314 |
| `render_timeframe_analysis` | Renderiza análisis por timeframe | 317-398 |
| `render_support_resistance` | Renderiza niveles clave de soporte y resistencia | 401-454 |
| `render_option_recommendations` | Renderiza recomendaciones concretas para opciones | 457-521 |
| `render_dashboard` | Renderiza dashboard completo con análisis técnico | 524-605 |
| `render_technical_tab` | Renderiza pestaña de análisis técnico | 608-610 |
| `render_options_tab` | Renderiza pestaña de análisis de opciones | 613-626 |
| `render_multiframe_tab` | Renderiza pestaña de análisis multi-timeframe | 629-637 |
| `render_fundamental_tab` | Renderiza pestaña de análisis fundamental | 640-642 |
| `render_report_tab` | Renderiza pestaña de reporte ejecutivo | 645-647 |
| `render_risk_tab` | Renderiza pestaña de gestión de riesgo | 650-652 |

### company_data.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `get_company_info` | Obtiene información completa de la empresa o activo | 468-490 |

### authenticator.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `InvalidAccessError` | Exception raised for invalid authentication attempts. | 12-14 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `_get_valid_passwords` | Retrieve valid password hashes from Streamlit secrets. | 16-30 |
| `_hash_password` | Hash a password using SHA-256. | 32-42 |
| `check_password` | Validate password and manage authentication attempts. | 44-86 |
| `validate_session` | Validate current session is authentic and not expired. | 88-103 |
| `get_session_info` | Get current session information. | 105-116 |
| `clear_session` | Clear all authentication session data. | 118-127 |

## Páginas

### 4_📈_MarketIntel_Options_Analyzer.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `NumpyEncoder` | Encoder personalizado para manejar diversos tipos de datos NumPy y Pandas | 63-320 |

##### Métodos de NumpyEncoder

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `default` | Sin descripción disponible | 66-85 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `init_openai_client` | Inicializa el cliente de OpenAI con manejo mejorado de credenciales | 322-425 |
| `create_technical_chart` | Crea gráfico técnico con indicadores y patrones técnicos | 428-748 |
| `format_patterns_for_prompt` | Formatea los patrones técnicos para incluirlos en el prompt del asistente IA | 751-790 |
| `process_message_with_citations` | Extrae y devuelve el texto del mensaje del asistente con manejo mejorado de errores | 793-809 |
| `consult_expert_ia` | Consulta al experto de IA con análisis detallado y solicitud de contraste entre noticias y fundamentos | 812-943 |
| `display_expert_opinion` | Muestra la opinión del experto IA con manejo mejorado de salida | 946-1064 |
| `display_recommendation_summary` | Muestra resumen de recomendación | 1067-1163 |
| `display_fundamental_factors` | Muestra factores fundamentales | 1166-1221 |
| `display_technical_factors` | Muestra factores técnicos | 1224-1384 |
| `display_sentiment_analysis` | Muestra análisis de sentimiento | 1387-1517 |
| `display_news_feed` | Muestra feed de noticias | 1520-1542 |
| `display_web_insights` | Muestra insights de búsqueda web | 1545-1570 |
| `display_trading_strategies` | Muestra estrategias de trading recomendadas | 1573-1690 |
| `display_cache_stats` | Muestra estadísticas de caché | 1693-1706 |
| `display_disclaimer` | Muestra disclaimer | 1709-1720 |
| `main` | Función principal | 1723-1978 |

### 5_📈_Technical_Expert_Analyzer.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `NumpyEncoder` | Encoder personalizado para manejar diversos tipos de datos NumPy y Pandas | 56-80 |

##### Métodos de NumpyEncoder

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `default` | Sin descripción disponible | 59-78 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `init_openai_client` | Inicializa el cliente de OpenAI con manejo mejorado de credenciales | 82-185 |
| `create_technical_chart` | Crea gráfico técnico con indicadores y patrones técnicos | 188-508 |
| `process_message_with_citations` | Extrae y devuelve el texto del mensaje del asistente con manejo mejorado de errores | 511-527 |
| `format_patterns_for_prompt` | Formatea los patrones técnicos para incluirlos en el prompt del asistente IA | 530-569 |
| `consult_expert_ia` | Consulta al experto de IA con análisis detallado | 572-703 |
| `display_expert_opinion` | Muestra la opinión del experto IA con manejo mejorado de salida | 706-824 |
| `display_login_form` | Muestra formulario de login con validación mejorada | 827-853 |
| `display_session_info` | Muestra información de sesión en la barra lateral con formato mejorado | 857-902 |
| `display_disclaimer` | Muestra disclaimer legal | 905-916 |
| `main` | Función principal para el Analizador Técnico y Experto | 919-1201 |

### 2_🤖_Inversor_Bot.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `secrets_file_exists` | Sin descripción disponible | 30-32 |
| `process_message_with_citations` | Extraiga y devuelva solo el texto del mensaje del asistente. | 102-110 |

### 1_📈_Analizador_de_Acciones_Pro.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `get_popular_symbols` | Retorna una lista de símbolos populares por categoría | 25-38 |
| `fetch_stock_price` | Obtiene el precio actual de una acción | 41-56 |
| `fetch_stock_info` | Obtiene información general sobre una acción | 59-76 |
| `fetch_stock_data` | Descarga datos históricos de una acción | 79-86 |
| `calculate_technical_indicators` | Calcula indicadores técnicos optimizados | 88-109 |
| `create_price_chart` | Crea gráfico de precios interactivo | 111-123 |
| `create_technical_charts` | Genera gráficos técnicos profesionales | 125-160 |
| `fetch_options_data` | Descarga datos de opciones con manejo de errores | 163-179 |
| `main` | Sin descripción disponible | 181-301 |

### 7_🔔_Notificaciones.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `DatabaseManager` | Gestiona la conexión y operaciones con la base de datos MariaDB | 122-400 |
| `EmailManager` | Gestiona el envío de correos electrónicos con boletines de trading | 402-1062 |
| `SignalManager` | Gestiona las señales de trading y su procesamiento | 1064-1065 |

##### Métodos de DatabaseManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de base de datos con credenciales desde secrets | 125-142 |
| `connect` | Establece conexión con la base de datos | 144-161 |
| `disconnect` | Cierra la conexión con la base de datos | 163-167 |
| `execute_query` | Ejecuta una consulta SQL y opcionalmente devuelve resultados | 169-221 |
| `get_signals` | Obtiene señales de trading filtradas con todos los campos detallados | 223-256 |
| `get_market_sentiment` | Obtiene sentimiento de mercado reciente | 258-273 |
| `get_market_news` | Obtiene noticias de mercado recientes | 275-283 |
| `get_detailed_analysis` | Obtiene análisis detallado para un símbolo específico | 285-301 |
| `save_signal` | Guarda una nueva señal de trading en la base de datos | 303-322 |
| `log_email_sent` | Registra el envío de un correo electrónico | 324-339 |
| `save_market_sentiment` | Guarda el sentimiento del mercado en la base de datos | 341-370 |
| `save_market_news` | Guarda una noticia del mercado en la base de datos | 372-398 |

##### Métodos de EmailManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de correos con credenciales desde secrets | 405-419 |
| `send_email` | Envía un correo electrónico con contenido HTML, PDF y opcionalmente imágenes | 421-583 |
| `create_newsletter_html` | Crea el contenido HTML para el boletín de trading con diseño mejorado optimizado para clientes de correo | 585-1031 |
| `generate_pdf` | Genera un PDF a partir del contenido HTML | 1033-1060 |

##### Métodos de SignalManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de señales | 1067-1070 |
| `get_active_signals` | Obtiene las señales activas filtradas desde la base de datos | 1072-1188 |
| `get_market_sentiment` | Obtiene el sentimiento actual del mercado desde la base de datos | 1190-1214 |
| `get_market_news` | Obtiene noticias relevantes del mercado desde la base de datos | 1216-1234 |
| `get_detailed_analysis` | Obtiene análisis detallado para un símbolo específico desde la base de datos | 1236-1256 |
| `save_signal` | Guarda una nueva señal en la base de datos | 1258-1260 |
| `send_newsletter` | Envía un boletín con las señales y análisis | 1262-1409 |

### 6_📊_InversorIA.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `setup_openai` | Configura credenciales de OpenAI | 114-137 |
| `check_api_keys` | Verifica las API keys disponibles en secret.toml o env vars | 145-203 |
| `check_libraries` | Verifica la disponibilidad de las bibliotecas necesarias | 206-247 |
| `display_system_status` | Muestra el estado del sistema, APIs y librerías | 250-324 |
| `check_authentication` | Verifica autenticación del usuario | 332-376 |
| `process_chat_input_with_openai` | Procesa la entrada del chat utilizando OpenAI para respuestas más naturales y variadas. | 384-432 |
| `process_with_assistant` | Procesa el mensaje utilizando la API de Asistentes de OpenAI | 435-533 |
| `process_with_chat_completion` | Procesa el mensaje utilizando la API de Chat Completion de OpenAI | 536-600 |
| `fallback_analyze_symbol` | Función de respaldo para analizar símbolos cuando OpenAI no está disponible | 603-891 |
| `initialize_session_state` | Inicializa el estado de la sesión | 899-936 |
| `render_sidebar` | Renderiza el panel lateral con información profesional | 939-1111 |
| `main` | Función principal de la aplicación | 1119-1305 |

### 3_📊_InversorIA_Mini.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `MarketDataError` | Excepción para errores en datos de mercado | 43-46 |
| `DataCache` | Sistema de caché con invalidación por tiempo | 48-102 |
| `OptionsParameterManager` | Gestiona parámetros para trading de opciones basados en categoría de activo | 104-300 |
| `MarketDataProvider` | Proveedor de datos de mercado con manejo de errores y limitación de tasa | 302-553 |
| `TechnicalAnalyzer` | Analizador técnico con cálculo de indicadores robustos | 555-892 |
| `MarketScanner` | Escáner de mercado con detección de estrategias | 894-981 |

##### Métodos de DataCache

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 51-56 |
| `get` | Obtiene dato del caché si es válido | 58-66 |
| `set` | Almacena dato en caché con timestamp | 68-70 |
| `clear` | Limpia caché completo | 72-77 |
| `can_request` | Controla frecuencia de solicitudes por símbolo | 79-89 |
| `get_stats` | Retorna estadísticas del caché | 91-101 |

##### Métodos de OptionsParameterManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 107-252 |
| `get_symbol_params` | Obtiene parámetros específicos para un símbolo | 254-256 |
| `get_strategy_recommendations` | Obtiene estrategias recomendadas según tendencia | 258-266 |
| `get_volatility_adjustments` | Obtiene ajustes recomendados según nivel de VIX | 268-299 |

##### Métodos de MarketDataProvider

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 305-310 |
| `_get_api_key` | Obtiene clave de API desde secrets o variables de entorno | 312-317 |
| `_rate_limit` | Controla la tasa de solicitudes | 319-342 |
| `get_market_data` | Obtiene datos de mercado con manejo de errores | 344-402 |
| `_validate_and_fix_data` | Valida y corrige problemas en datos de mercado | 404-434 |
| `_get_alpha_vantage_data` | Obtiene datos desde Alpha Vantage como respaldo | 436-494 |
| `_generate_synthetic_data` | Genera datos sintéticos para fallback de interfaz | 496-552 |

##### Métodos de TechnicalAnalyzer

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 558-560 |
| `get_market_data` | Obtiene datos de mercado a través del proveedor | 562-564 |
| `analyze_trend` | Analiza tendencia de un símbolo con manejo de errores | 566-617 |
| `_calculate_indicators` | Calcula indicadores técnicos con seguridad en asignaciones | 619-678 |
| `_determine_trend` | Determina tendencia basada en indicadores con manejo seguro | 680-788 |
| `identify_strategy` | Identifica estrategias basadas en el análisis técnico | 790-862 |
| `_check_strategy_conditions` | Verifica si las condiciones de una estrategia se cumplen | 864-891 |

##### Métodos de MarketScanner

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Sin descripción disponible | 897-901 |
| `get_cached_analysis` | Obtiene análisis cacheado si existe | 903-907 |
| `scan_market` | Ejecuta escaneo de mercado enfocado en sectores seleccionados | 909-980 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `get_market_status` | Obtiene el estado actual del mercado con manejo seguro de errores | 983-1023 |
| `initialize_session_state` | Inicializa el estado de la sesión con manejo de errores | 1026-1056 |
| `main` | Sin descripción disponible | 1059-1334 |

## Componentes

### market_scanner_ui.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `render_market_scanner` | Renderiza la pestaña del scanner de mercado | 14-148 |

### sidebar.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `render_sidebar` | Renderiza la barra lateral de la aplicación | 12-77 |

### ai_chat.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `render_ai_chat` | Renderiza la pestaña de chat con IA | 18-127 |

### __init__.py

### dashboard.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `render_dashboard` | Renderiza el dashboard principal | 18-184 |

### individual_analysis_fixed.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `render_individual_analysis` | Renderiza la pestaña de análisis individual | 30-126 |

### individual_analysis.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `render_individual_analysis` | Renderiza la pestaña de análisis individual | 31-117 |

## Utilidades

### config.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `NumpyEncoder` | Encoder personalizado para manejar diversos tipos de datos NumPy y Pandas | 21-43 |

##### Métodos de NumpyEncoder

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `default` | Sin descripción disponible | 24-43 |

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `setup_page_config` | Configura la página de Streamlit | 45-54 |
| `initialize_session_state` | Inicializa el estado de la sesión con valores por defecto | 56-80 |

### session_state.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `initialize_session_state` | Inicializa el estado de la sesión con valores por defecto | 12-39 |
| `get_current_symbol` | Obtiene el símbolo actual seleccionado | 41-45 |
| `set_current_symbol` | Establece el símbolo actual | 47-52 |
| `update_scan_results` | Actualiza los resultados del scanner | 54-60 |
| `add_chat_message` | Añade un mensaje al historial de chat | 62-69 |
| `clear_chat_history` | Limpia el historial de chat | 71-75 |

### summary_manager.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `SummaryManager` | Clase para gestionar resúmenes de procesamiento y resultados | 16-20 |

##### Métodos de SummaryManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de resúmenes | 22-26 |
| `create_summary_container` | Crea un nuevo contenedor para resúmenes | 28-39 |
| `show_summary` | Muestra un resumen de procesamiento | 41-81 |
| `show_database_summary` | Muestra un resumen de operaciones de base de datos | 83-125 |
| `show_signal_summary` | Muestra un resumen de señales procesadas | 127-170 |
| `clear_summary` | Limpia un contenedor de resumen | 172-188 |
| `clear_all_summaries` | Limpia todos los contenedores de resumen | 190-197 |

### __init__.py

### ui_utils.py

#### Funciones

| Función | Descripción | Líneas |
|---------|-------------|--------|
| `display_header` | Muestra un encabezado con estilo consistente | 13-19 |
| `display_info_message` | Muestra un mensaje informativo con estilo | 21-32 |
| `display_error_message` | Muestra un mensaje de error con estilo | 34-45 |
| `display_asset_card` | Muestra una tarjeta de activo con información básica | 47-71 |
| `create_candlestick_chart` | Crea un gráfico de velas con Plotly | 73-101 |
| `format_timestamp` | Formatea una marca de tiempo para mostrarla | 103-116 |
| `display_data_table` | Muestra una tabla de datos con formato mejorado | 118-136 |

### progress_manager.py

#### Clases

| Clase | Descripción | Líneas |
|-------|-------------|--------|
| `ProgressManager` | Clase para gestionar barras de progreso y mensajes de estado | 16-20 |

##### Métodos de ProgressManager

| Método | Descripción | Líneas |
|--------|-------------|--------|
| `__init__` | Inicializa el gestor de progreso | 22-32 |
| `create_progress_bar` | Crea una nueva barra de progreso | 34-48 |
| `update_progress` | Actualiza una barra de progreso existente | 50-70 |
| `complete_progress` | Marca una barra de progreso como completada | 72-98 |
| `error_progress` | Marca una barra de progreso con error | 100-122 |
| `clear_progress` | Limpia una barra de progreso y sus mensajes asociados | 124-153 |
| `clear_all_progress` | Limpia todas las barras de progreso y mensajes | 155-162 |
| `run_with_progress` | Ejecuta una función mostrando una barra de progreso | 164-219 |

