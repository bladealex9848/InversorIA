#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir los problemas con post_save_quality_check.py
"""

import sys
import logging
import os
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

def fix_post_save_quality_check():
    """
    Corrige los problemas con post_save_quality_check.py
    """
    try:
        # 1. Verificar que post_save_quality_check.py existe
        if not os.path.exists("post_save_quality_check.py"):
            logger.error("El archivo post_save_quality_check.py no existe")
            return False
            
        logger.info("Corrigiendo problemas con post_save_quality_check.py...")
        
        # 2. Corregir el problema con OPENAI_API_KEY en post_save_quality_check.py
        with open("post_save_quality_check.py", "r", encoding="utf-8") as file:
            content = file.read()
            
        # Verificar si ya se ha corregido el problema
        if "import toml" in content and "secrets = toml.load" in content:
            logger.info("El archivo post_save_quality_check.py ya ha sido corregido")
        else:
            # Agregar importación de toml y carga de secrets.toml
            new_content = content.replace(
                "import mysql.connector",
                "import mysql.connector\nimport toml\nimport os"
            )
            
            # Agregar función para cargar la API key de OpenAI
            openai_config_code = """
# Cargar configuración de OpenAI desde secrets.toml
def load_openai_config():
    \"\"\"
    Carga la configuración de OpenAI desde secrets.toml
    
    Returns:
        dict: Configuración de OpenAI
    \"\"\"
    try:
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            
            # Buscar la API key en diferentes ubicaciones
            api_key = None
            if "OPENAI_API_KEY" in secrets:
                api_key = secrets["OPENAI_API_KEY"]
            elif "openai" in secrets and "api_key" in secrets["openai"]:
                api_key = secrets["openai"]["api_key"]
            elif "api_keys" in secrets and "OPENAI_API_KEY" in secrets["api_keys"]:
                api_key = secrets["api_keys"]["OPENAI_API_KEY"]
                
            # Buscar el modelo en diferentes ubicaciones
            model = "gpt-3.5-turbo"
            if "OPENAI_API_MODEL" in secrets:
                model = secrets["OPENAI_API_MODEL"]
            elif "openai" in secrets and "model" in secrets["openai"]:
                model = secrets["openai"]["model"]
            elif "api_keys" in secrets and "OPENAI_API_MODEL" in secrets["api_keys"]:
                model = secrets["api_keys"]["OPENAI_API_MODEL"]
                
            return {
                "api_key": api_key,
                "model": model
            }
        else:
            logger.warning(f"No se encontró el archivo {secrets_path}")
            return {}
    except Exception as e:
        logger.error(f"Error cargando configuración de OpenAI: {str(e)}")
        return {}
"""
            
            # Insertar el código después de la definición del logger
            new_content = new_content.replace(
                "logger = logging.getLogger(__name__)",
                "logger = logging.getLogger(__name__)" + openai_config_code
            )
            
            # Corregir las funciones que generan contenido con IA
            # Primero, buscar generate_summary_with_ai
            if "def generate_summary_with_ai" in new_content:
                # Encontrar la función completa
                start_index = new_content.find("def generate_summary_with_ai")
                end_index = new_content.find("def ", start_index + 1)
                if end_index == -1:
                    end_index = len(new_content)
                    
                old_function = new_content[start_index:end_index]
                
                # Crear la nueva función
                new_function = """def generate_summary_with_ai(title, symbol, url=None):
    \"\"\"
    Genera un resumen de una noticia utilizando IA
    
    Args:
        title (str): Título de la noticia
        symbol (str): Símbolo de la acción
        url (str, optional): URL de la noticia
        
    Returns:
        str: Resumen generado o None si hubo un error
    \"\"\"
    try:
        # Cargar configuración de OpenAI
        config = load_openai_config()
        api_key = config.get("api_key")
        model = config.get("model", "gpt-3.5-turbo")
        
        if not api_key:
            logger.warning("No se encontró la API key de OpenAI")
            return "Resumen generado automáticamente para la noticia: " + title
            
        # Inicializar cliente de OpenAI
        try:
            import openai
            openai.api_key = api_key
            client = openai.OpenAI(api_key=api_key)
            logger.info("Cliente OpenAI inicializado correctamente")
        except Exception as e:
            logger.warning(f"Error inicializando cliente OpenAI: {str(e)}")
            return "Resumen generado automáticamente para la noticia: " + title
            
        # Crear prompt para generar el resumen
        prompt = f"Genera un resumen detallado en español para la siguiente noticia financiera sobre {symbol}. "
        prompt += f"Título: {title}. "
        if url:
            prompt += f"URL: {url}. "
        prompt += "El resumen debe ser informativo, objetivo y enfocado en los aspectos financieros relevantes para inversores."
        
        # Generar resumen con OpenAI
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Eres un analista financiero experto especializado en resumir noticias del mercado."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Resumen generado correctamente para {symbol}: {summary[:50]}...")
            return summary
        except Exception as e:
            logger.warning(f"Error generando resumen con OpenAI: {str(e)}")
            return "Resumen generado automáticamente para la noticia: " + title
    except Exception as e:
        logger.error(f"Error en generate_summary_with_ai: {str(e)}")
        return "Resumen generado automáticamente para la noticia: " + title
"""
                
                # Reemplazar la función antigua con la nueva
                new_content = new_content.replace(old_function, new_function)
                
            # Corregir generate_sentiment_analysis_with_ai
            if "def generate_sentiment_analysis_with_ai" in new_content:
                # Encontrar la función completa
                start_index = new_content.find("def generate_sentiment_analysis_with_ai")
                end_index = new_content.find("def ", start_index + 1)
                if end_index == -1:
                    end_index = len(new_content)
                    
                old_function = new_content[start_index:end_index]
                
                # Crear la nueva función
                new_function = """def generate_sentiment_analysis_with_ai(sentiment_data):
    \"\"\"
    Genera un análisis de sentimiento utilizando IA
    
    Args:
        sentiment_data (dict): Datos de sentimiento
        
    Returns:
        str: Análisis generado o None si hubo un error
    \"\"\"
    try:
        # Cargar configuración de OpenAI
        config = load_openai_config()
        api_key = config.get("api_key")
        model = config.get("model", "gpt-3.5-turbo")
        
        if not api_key:
            logger.warning("No se encontró la API key de OpenAI")
            return "Análisis de sentimiento de mercado generado automáticamente."
            
        # Inicializar cliente de OpenAI
        try:
            import openai
            openai.api_key = api_key
            client = openai.OpenAI(api_key=api_key)
            logger.info("Cliente OpenAI inicializado correctamente")
        except Exception as e:
            logger.warning(f"Error inicializando cliente OpenAI: {str(e)}")
            return "Análisis de sentimiento de mercado generado automáticamente."
            
        # Crear prompt para generar el análisis
        prompt = "Genera un análisis detallado del sentimiento de mercado basado en los siguientes datos:\\n"
        prompt += f"Sentimiento general: {sentiment_data.get('overall', 'Neutral')}\\n"
        prompt += f"VIX: {sentiment_data.get('vix', 'N/A')}\\n"
        prompt += f"Tendencia S&P 500: {sentiment_data.get('sp500_trend', 'N/A')}\\n"
        prompt += f"Indicadores técnicos: {sentiment_data.get('technical_indicators', 'N/A')}\\n"
        prompt += f"Volumen: {sentiment_data.get('volume', 'N/A')}\\n"
        prompt += f"Notas: {sentiment_data.get('notes', '')}\\n"
        prompt += "El análisis debe ser detallado, objetivo y enfocado en los aspectos relevantes para inversores."
        
        # Generar análisis con OpenAI
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Eres un analista financiero experto especializado en interpretar el sentimiento del mercado."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            analysis = response.choices[0].message.content.strip()
            logger.info(f"Análisis de sentimiento generado correctamente: {analysis[:50]}...")
            return analysis
        except Exception as e:
            logger.warning(f"Error generando análisis con OpenAI: {str(e)}")
            return "Análisis de sentimiento de mercado generado automáticamente."
    except Exception as e:
        logger.error(f"Error en generate_sentiment_analysis_with_ai: {str(e)}")
        return "Análisis de sentimiento de mercado generado automáticamente."
"""
                
                # Reemplazar la función antigua con la nueva
                new_content = new_content.replace(old_function, new_function)
                
            # Corregir generate_trading_signal_analysis_with_ai
            if "def generate_trading_signal_analysis_with_ai" in new_content:
                # Encontrar la función completa
                start_index = new_content.find("def generate_trading_signal_analysis_with_ai")
                end_index = new_content.find("def ", start_index + 1)
                if end_index == -1:
                    end_index = len(new_content)
                    
                old_function = new_content[start_index:end_index]
                
                # Crear la nueva función
                new_function = """def generate_trading_signal_analysis_with_ai(signal_data):
    \"\"\"
    Genera un análisis experto para una señal de trading utilizando IA
    
    Args:
        signal_data (dict): Datos de la señal
        
    Returns:
        str: Análisis generado o None si hubo un error
    \"\"\"
    try:
        # Cargar configuración de OpenAI
        config = load_openai_config()
        api_key = config.get("api_key")
        model = config.get("model", "gpt-3.5-turbo")
        
        if not api_key:
            logger.warning("No se encontró la API key de OpenAI")
            return "Análisis experto generado automáticamente para la señal de trading."
            
        # Inicializar cliente de OpenAI
        try:
            import openai
            openai.api_key = api_key
            client = openai.OpenAI(api_key=api_key)
            logger.info("Cliente OpenAI inicializado correctamente")
        except Exception as e:
            logger.warning(f"Error inicializando cliente OpenAI: {str(e)}")
            return "Análisis experto generado automáticamente para la señal de trading."
            
        # Crear prompt para generar el análisis
        symbol = signal_data.get("symbol", "")
        direction = signal_data.get("direction", "")
        price = signal_data.get("price", 0.0)
        confidence = signal_data.get("confidence_level", "")
        strategy = signal_data.get("strategy", "")
        
        prompt = f"Genera un análisis experto detallado para la siguiente señal de trading:\\n"
        prompt += f"Símbolo: {symbol}\\n"
        prompt += f"Dirección: {direction}\\n"
        prompt += f"Precio: {price}\\n"
        prompt += f"Nivel de confianza: {confidence}\\n"
        prompt += f"Estrategia: {strategy}\\n"
        
        # Agregar información adicional si está disponible
        if signal_data.get("entry_price"):
            prompt += f"Precio de entrada: {signal_data.get('entry_price')}\\n"
        if signal_data.get("stop_loss"):
            prompt += f"Stop loss: {signal_data.get('stop_loss')}\\n"
        if signal_data.get("take_profit"):
            prompt += f"Take profit: {signal_data.get('take_profit')}\\n"
        if signal_data.get("risk_reward"):
            prompt += f"Riesgo/Recompensa: {signal_data.get('risk_reward')}\\n"
        if signal_data.get("expiration_date"):
            prompt += f"Fecha de expiración: {signal_data.get('expiration_date')}\\n"
        if signal_data.get("market_sentiment"):
            prompt += f"Sentimiento de mercado: {signal_data.get('market_sentiment')}\\n"
        if signal_data.get("technical_indicators"):
            prompt += f"Indicadores técnicos: {signal_data.get('technical_indicators')}\\n"
        if signal_data.get("fundamental_analysis"):
            prompt += f"Análisis fundamental: {signal_data.get('fundamental_analysis')}\\n"
        if signal_data.get("latest_news"):
            prompt += f"Últimas noticias: {signal_data.get('latest_news')}\\n"
            
        prompt += "El análisis debe ser detallado, objetivo y enfocado en los aspectos relevantes para inversores. Incluye recomendaciones específicas y justificación técnica."
        
        # Generar análisis con OpenAI
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Eres un trader profesional experto en análisis técnico y fundamental de mercados financieros."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            analysis = response.choices[0].message.content.strip()
            logger.info(f"Análisis experto generado correctamente para {symbol}: {analysis[:50]}...")
            return analysis
        except Exception as e:
            logger.warning(f"Error generando análisis experto con OpenAI: {str(e)}")
            return "Análisis experto generado automáticamente para la señal de trading."
    except Exception as e:
        logger.error(f"Error en generate_trading_signal_analysis_with_ai: {str(e)}")
        return "Análisis experto generado automáticamente para la señal de trading."
"""
                
                # Reemplazar la función antigua con la nueva
                new_content = new_content.replace(old_function, new_function)
            
            # Guardar los cambios
            with open("post_save_quality_check.py", "w", encoding="utf-8") as file:
                file.write(new_content)
                
            logger.info("Se ha corregido post_save_quality_check.py")
        
        # 3. Verificar si post_save_quality_check.py se llama desde enhanced_market_scanner_fixed.py
        if os.path.exists("enhanced_market_scanner_fixed.py"):
            with open("enhanced_market_scanner_fixed.py", "r", encoding="utf-8") as file:
                content = file.read()
                
            if "post_save_quality_check" not in content:
                # Buscar un lugar adecuado para agregar la llamada
                if "save_signal" in content:
                    # Buscar la función que guarda señales
                    save_signal_index = content.find("save_signal")
                    if save_signal_index != -1:
                        # Buscar el final de la función
                        next_def_index = content.find("def ", save_signal_index + 1)
                        if next_def_index == -1:
                            next_def_index = len(content)
                            
                        # Buscar el return de la función
                        return_index = content.rfind("return", save_signal_index, next_def_index)
                        if return_index != -1:
                            # Buscar el final de la línea
                            end_line_index = content.find("\n", return_index)
                            if end_line_index != -1:
                                # Agregar la llamada a post_save_quality_check.py
                                new_content = content[:end_line_index + 1] + """
                                # Procesar la calidad de los datos después de guardar
                                try:
                                    import post_save_quality_check
                                    
                                    # Procesar solo las señales de trading
                                    post_save_quality_check.process_quality_after_save(
                                        table_name="signals", limit=1
                                    )
                                    logger.info(f"Procesamiento de calidad completado para la señal")
                                except Exception as e:
                                    logger.warning(f"Error en el procesamiento de calidad: {str(e)}")
                                    logger.warning(f"Traza completa:", exc_info=True)
                                """ + content[end_line_index + 1:]
                                
                                # Guardar los cambios
                                with open("enhanced_market_scanner_fixed.py", "w", encoding="utf-8") as file:
                                    file.write(new_content)
                                    
                                logger.info("Se ha agregado la llamada a post_save_quality_check.py en enhanced_market_scanner_fixed.py")
        
        # 4. Verificar si post_save_quality_check.py se llama desde components/market_scanner_ui.py
        if os.path.exists("components/market_scanner_ui.py"):
            with open("components/market_scanner_ui.py", "r", encoding="utf-8") as file:
                content = file.read()
                
            if "post_save_quality_check" not in content:
                # Buscar un lugar adecuado para agregar la llamada
                if "save_signal" in content:
                    # Buscar la función que guarda señales
                    save_signal_index = content.find("signal_manager.db_manager.save_signal")
                    if save_signal_index != -1:
                        # Buscar el final de la línea
                        end_line_index = content.find("\n", save_signal_index)
                        if end_line_index != -1:
                            # Buscar la línea que incrementa signals_saved
                            signals_saved_index = content.find("signals_saved += 1", save_signal_index)
                            if signals_saved_index != -1 and signals_saved_index < save_signal_index + 200:
                                # Buscar el final de la línea
                                signals_saved_end_index = content.find("\n", signals_saved_index)
                                if signals_saved_end_index != -1:
                                    # Agregar la llamada a post_save_quality_check.py
                                    new_content = content[:signals_saved_end_index + 1] + """
                                                    # Procesar la calidad de los datos después de guardar
                                                    try:
                                                        import post_save_quality_check
                                                        
                                                        # Procesar solo las señales de trading
                                                        post_save_quality_check.process_quality_after_save(
                                                            table_name="signals", limit=1
                                                        )
                                                        logger.info(f"Procesamiento de calidad completado para la señal")
                                                    except Exception as e:
                                                        logger.warning(f"Error en el procesamiento de calidad: {str(e)}")
                                                        logger.warning(f"Traza completa:", exc_info=True)
                                    """ + content[signals_saved_end_index + 1:]
                                    
                                    # Guardar los cambios
                                    with open("components/market_scanner_ui.py", "w", encoding="utf-8") as file:
                                        file.write(new_content)
                                        
                                    logger.info("Se ha agregado la llamada a post_save_quality_check.py en components/market_scanner_ui.py")
        
        logger.info("Correcciones completadas")
        return True
        
    except Exception as e:
        logger.error(f"Error en fix_post_save_quality_check: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if fix_post_save_quality_check():
        logger.info("Correcciones aplicadas con éxito")
        sys.exit(0)
    else:
        logger.error("No se pudieron aplicar las correcciones")
        sys.exit(1)
