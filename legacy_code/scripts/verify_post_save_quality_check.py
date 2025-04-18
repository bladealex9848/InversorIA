#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar si post_save_quality_check.py se está aplicando correctamente
después de guardar registros en las tablas 'market_news', 'market_sentiment' y 'trading_signals'.
"""

import sys
import logging
import traceback
import time
from datetime import datetime, timedelta
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

def verify_post_save_quality_check():
    """
    Verifica si post_save_quality_check.py se está aplicando correctamente
    """
    try:
        # Importar módulos necesarios
        from database_utils import DatabaseManager
        import post_save_quality_check
        
        # Verificar que post_save_quality_check.py existe y es accesible
        if not os.path.exists("post_save_quality_check.py"):
            logger.error("El archivo post_save_quality_check.py no existe")
            return False
            
        logger.info("Verificando la aplicación de post_save_quality_check.py...")
        
        # Conectar a la base de datos
        db_manager = DatabaseManager()
        
        # 1. Verificar si hay registros con campos vacíos en las tablas
        logger.info("Verificando registros con campos vacíos en las tablas...")
        
        # Verificar market_news
        news_query = """
        SELECT COUNT(*) as count FROM market_news 
        WHERE summary IS NULL OR summary = '' OR symbol = 'SPY'
        """
        news_result = db_manager.execute_query(news_query)
        empty_news_count = news_result[0]['count'] if news_result else 0
        
        # Verificar market_sentiment
        sentiment_query = """
        SELECT COUNT(*) as count FROM market_sentiment 
        WHERE analysis IS NULL OR analysis = '' OR vix = 0.0
        """
        sentiment_result = db_manager.execute_query(sentiment_query)
        empty_sentiment_count = sentiment_result[0]['count'] if sentiment_result else 0
        
        # Verificar trading_signals
        signals_query = """
        SELECT COUNT(*) as count FROM trading_signals 
        WHERE analysis IS NULL OR analysis = ''
        """
        signals_result = db_manager.execute_query(signals_query)
        empty_signals_count = signals_result[0]['count'] if signals_result else 0
        
        logger.info(f"Noticias con campos vacíos: {empty_news_count}")
        logger.info(f"Registros de sentimiento con campos vacíos: {empty_sentiment_count}")
        logger.info(f"Señales de trading con campos vacíos: {empty_signals_count}")
        
        # 2. Verificar si post_save_quality_check.py se está llamando desde database_utils.py
        logger.info("Verificando llamadas a post_save_quality_check.py desde database_utils.py...")
        
        # Crear registros de prueba para cada tabla
        test_news = {
            "title": f"Test News {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "summary": "",  # Campo vacío para que post_save_quality_check.py lo procese
            "source": "Test",
            "url": "https://example.com",
            "news_date": datetime.now(),
            "impact": "Bajo",
            "symbol": "SPY"  # Usar SPY para que post_save_quality_check.py actualice el símbolo
        }
        
        test_sentiment = {
            "overall": "Neutral",
            "vix": 0.0,  # Campo vacío para que post_save_quality_check.py lo procese
            "sp500_trend": "Lateral",
            "technical_indicators": "Mixtos",
            "volume": "Normal",
            "notes": "Test",
            "symbol": "SPY",
            "sentiment": "Neutral",
            "score": 0.5,
            "source": "Test",
            "analysis": "",  # Campo vacío para que post_save_quality_check.py lo procese
            "sentiment_date": datetime.now()
        }
        
        test_signal = {
            "symbol": "AAPL",
            "price": 150.0,
            "direction": "CALL",
            "confidence_level": "ALTA",
            "timeframe": "DIARIO",
            "strategy": "TENDENCIA",
            "category": "ACCIONES",
            "analysis": "",  # Campo vacío para que post_save_quality_check.py lo procese
            "entry_price": 150.0,
            "stop_loss": 145.0,
            "take_profit": 160.0,
            "risk_reward": 2.0,
            "expiration_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "strike_price": 155.0,
            "option_type": "CALL",
            "option_expiration": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "market_sentiment": "ALCISTA",
            "technical_indicators": "RSI, MACD, MA",
            "fundamental_analysis": "Buenos resultados trimestrales",
            "news_impact": "POSITIVO",
            "latest_news": "Apple anuncia nuevos productos",
            "news_source": "https://example.com",
            "expert_opinion": "",  # Campo vacío para que post_save_quality_check.py lo procese
            "probability_of_success": 75.0,
            "recommended_position_size": 5.0,
            "max_loss_percentage": 3.0,
            "notes": "Test signal"
        }
        
        # Guardar registros de prueba
        from database_utils import save_market_news, save_market_sentiment, save_trading_signal
        
        # Guardar noticia de prueba
        logger.info("Guardando noticia de prueba...")
        news_id = save_market_news(test_news)
        if news_id:
            logger.info(f"Noticia de prueba guardada con ID: {news_id}")
            
            # Verificar si el resumen se actualizó
            time.sleep(2)  # Esperar a que post_save_quality_check.py procese el registro
            news_query = f"SELECT summary, symbol FROM market_news WHERE id = {news_id}"
            news_result = db_manager.execute_query(news_query)
            
            if news_result and news_result[0]['summary']:
                logger.info(f"✅ El resumen de la noticia se actualizó correctamente: {news_result[0]['summary'][:50]}...")
                logger.info(f"✅ El símbolo de la noticia es: {news_result[0]['symbol']}")
                
                # Verificar si se llamó a post_save_quality_check.py
                if news_result[0]['symbol'] != 'SPY' or len(news_result[0]['summary']) > 10:
                    logger.info("✅ post_save_quality_check.py se aplicó correctamente para market_news")
                else:
                    logger.warning("❌ post_save_quality_check.py NO se aplicó correctamente para market_news")
            else:
                logger.warning("❌ El resumen de la noticia NO se actualizó")
        else:
            logger.error("❌ No se pudo guardar la noticia de prueba")
        
        # Guardar sentimiento de prueba (solo si no hay un registro para hoy)
        logger.info("Verificando si ya existe un registro de sentimiento para hoy...")
        today = datetime.now().strftime("%Y-%m-%d")
        check_today_query = "SELECT id FROM market_sentiment WHERE DATE(created_at) = %s"
        existing_today = db_manager.execute_query(check_today_query, params=[today])
        
        if existing_today and len(existing_today) > 0:
            logger.info(f"Ya existe un registro de sentimiento para hoy con ID: {existing_today[0]['id']}")
            sentiment_id = existing_today[0]['id']
            
            # Actualizar el registro existente para forzar el procesamiento
            update_query = "UPDATE market_sentiment SET analysis = '', vix = 0.0 WHERE id = %s"
            db_manager.execute_query(update_query, params=[sentiment_id], fetch=False)
            logger.info(f"Registro de sentimiento actualizado con campos vacíos para forzar el procesamiento")
            
            # Llamar directamente a post_save_quality_check.py
            logger.info("Llamando directamente a post_save_quality_check.py para procesar el sentimiento...")
            result = post_save_quality_check.process_quality_after_save(table_name="sentiment", limit=1)
            logger.info(f"Resultado del procesamiento: {result}")
            
            # Verificar si el análisis y el VIX se actualizaron
            time.sleep(2)  # Esperar a que post_save_quality_check.py procese el registro
            sentiment_query = f"SELECT analysis, vix FROM market_sentiment WHERE id = {sentiment_id}"
            sentiment_result = db_manager.execute_query(sentiment_query)
            
            if sentiment_result:
                if sentiment_result[0]['analysis']:
                    logger.info(f"✅ El análisis del sentimiento se actualizó correctamente: {sentiment_result[0]['analysis'][:50]}...")
                else:
                    logger.warning("❌ El análisis del sentimiento NO se actualizó")
                    
                if sentiment_result[0]['vix'] > 0.0:
                    logger.info(f"✅ El VIX se actualizó correctamente: {sentiment_result[0]['vix']}")
                else:
                    logger.warning("❌ El VIX NO se actualizó")
            else:
                logger.warning("❌ No se pudo verificar el registro de sentimiento")
        else:
            logger.info("No hay registro de sentimiento para hoy, guardando uno nuevo...")
            sentiment_id = save_market_sentiment(test_sentiment)
            if sentiment_id:
                logger.info(f"Sentimiento de prueba guardado con ID: {sentiment_id}")
                
                # Verificar si el análisis y el VIX se actualizaron
                time.sleep(2)  # Esperar a que post_save_quality_check.py procese el registro
                sentiment_query = f"SELECT analysis, vix FROM market_sentiment WHERE id = {sentiment_id}"
                sentiment_result = db_manager.execute_query(sentiment_query)
                
                if sentiment_result:
                    if sentiment_result[0]['analysis']:
                        logger.info(f"✅ El análisis del sentimiento se actualizó correctamente: {sentiment_result[0]['analysis'][:50]}...")
                        logger.info("✅ post_save_quality_check.py se aplicó correctamente para market_sentiment")
                    else:
                        logger.warning("❌ El análisis del sentimiento NO se actualizó")
                        logger.warning("❌ post_save_quality_check.py NO se aplicó correctamente para market_sentiment")
                        
                    if sentiment_result[0]['vix'] > 0.0:
                        logger.info(f"✅ El VIX se actualizó correctamente: {sentiment_result[0]['vix']}")
                    else:
                        logger.warning("❌ El VIX NO se actualizó")
                else:
                    logger.warning("❌ No se pudo verificar el registro de sentimiento")
            else:
                logger.error("❌ No se pudo guardar el sentimiento de prueba")
        
        # Guardar señal de trading de prueba
        logger.info("Guardando señal de trading de prueba...")
        signal_id = save_trading_signal(test_signal)
        if signal_id:
            logger.info(f"Señal de trading de prueba guardada con ID: {signal_id}")
            
            # Verificar si el análisis se actualizó
            time.sleep(2)  # Esperar a que post_save_quality_check.py procese el registro
            signal_query = f"SELECT analysis FROM trading_signals WHERE id = {signal_id}"
            signal_result = db_manager.execute_query(signal_query)
            
            if signal_result and signal_result[0]['analysis']:
                logger.info(f"✅ El análisis de la señal se actualizó correctamente: {signal_result[0]['analysis'][:50]}...")
                logger.info("✅ post_save_quality_check.py se aplicó correctamente para trading_signals")
            else:
                logger.warning("❌ El análisis de la señal NO se actualizó")
                logger.warning("❌ post_save_quality_check.py NO se aplicó correctamente para trading_signals")
        else:
            logger.error("❌ No se pudo guardar la señal de trading de prueba")
        
        # 3. Verificar si post_save_quality_check.py se está llamando desde el proceso de escaneo de mercado
        logger.info("Verificando llamadas a post_save_quality_check.py desde el proceso de escaneo de mercado...")
        
        # Buscar en el código fuente
        scanner_files = [
            "market_scanner.py",
            "enhanced_market_scanner.py",
            "enhanced_market_scanner_fixed.py",
            "components/market_scanner_ui.py",
            "📊_InversorIA_Pro.py"
        ]
        
        for file_path in scanner_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if "post_save_quality_check" in content:
                        logger.info(f"✅ Se encontró referencia a post_save_quality_check.py en {file_path}")
                        
                        # Buscar patrones específicos
                        if "process_quality_after_save" in content:
                            logger.info(f"✅ Se encontró llamada a process_quality_after_save en {file_path}")
                        else:
                            logger.warning(f"❌ No se encontró llamada a process_quality_after_save en {file_path}")
                    else:
                        logger.warning(f"❌ No se encontró referencia a post_save_quality_check.py en {file_path}")
            else:
                logger.warning(f"El archivo {file_path} no existe")
        
        # 4. Verificar si se está ejecutando update_news_symbols.py después de guardar noticias
        logger.info("Verificando si se está ejecutando update_news_symbols.py después de guardar noticias...")
        
        if os.path.exists("update_news_symbols.py"):
            logger.info("✅ El archivo update_news_symbols.py existe")
            
            # Verificar si se llama desde database_utils.py
            with open("database_utils.py", 'r', encoding='utf-8') as file:
                content = file.read()
                if "update_news_symbols" in content:
                    logger.info("✅ Se encontró referencia a update_news_symbols.py en database_utils.py")
                    
                    # Buscar patrones específicos
                    if "update_news_symbols.update_news_symbols()" in content:
                        logger.info("✅ Se encontró llamada a update_news_symbols.update_news_symbols() en database_utils.py")
                    else:
                        logger.warning("❌ No se encontró llamada a update_news_symbols.update_news_symbols() en database_utils.py")
                else:
                    logger.warning("❌ No se encontró referencia a update_news_symbols.py en database_utils.py")
        else:
            logger.warning("❌ El archivo update_news_symbols.py no existe")
        
        # 5. Verificar si se muestra el mensaje de confirmación después de guardar registros
        logger.info("Verificando si se muestra el mensaje de confirmación después de guardar registros...")
        
        confirmation_message = "Los datos han sido almacenados correctamente en la base de datos y estarán disponibles para consultas futuras"
        
        with open("database_utils.py", 'r', encoding='utf-8') as file:
            content = file.read()
            if confirmation_message in content:
                logger.info(f"✅ Se encontró el mensaje de confirmación en database_utils.py")
            else:
                logger.warning(f"❌ No se encontró el mensaje de confirmación en database_utils.py")
        
        logger.info("Verificación completada")
        return True
        
    except Exception as e:
        logger.error(f"Error en verify_post_save_quality_check: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if verify_post_save_quality_check():
        logger.info("Verificación completada con éxito")
        sys.exit(0)
    else:
        logger.error("Error en la verificación")
        sys.exit(1)
