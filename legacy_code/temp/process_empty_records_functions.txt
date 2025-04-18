def process_empty_news_summaries(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> int:
    """
    Procesa noticias con resumen vacío
    
    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a procesar
        
    Returns:
        int: Número de registros procesados
    """
    # Obtener noticias con resumen vacío
    empty_news = get_empty_news_summaries(connection, limit)
    
    if not empty_news:
        logger.info("No hay noticias con resumen vacío para procesar")
        return 0
    
    logger.info(f"Se encontraron {len(empty_news)} noticias con resumen vacío")
    
    # Procesar cada noticia
    processed_count = 0
    for news in empty_news:
        news_id = news.get("id")
        title = news.get("title", "")
        symbol = news.get("symbol", "SPY")
        url = news.get("url", "")
        
        logger.info(f"Procesando noticia ID {news_id}: {title[:50]}...")
        
        # Traducir título si está en inglés
        original_title = title
        translated_title = translate_title_to_spanish(title)
        if translated_title != original_title:
            logger.info(f"Título traducido: {translated_title}")
            
            # Actualizar título en la base de datos
            try:
                cursor = connection.cursor()
                query = "UPDATE market_news SET title = %s, updated_at = NOW() WHERE id = %s"
                cursor.execute(query, (translated_title, news_id))
                connection.commit()
                cursor.close()
                logger.info(f"Título actualizado para noticia ID {news_id}")
                
                # Usar el título traducido para generar el resumen
                title = translated_title
            except Exception as e:
                logger.error(
                    f"Error actualizando título para noticia ID {news_id}: {str(e)}"
                )
        
        # Intentar obtener noticias de Yahoo Finance si no hay URL
        if not url and YAHOO_SCRAPER_AVAILABLE:
            yahoo_news = get_news_from_yahoo(symbol, 1)
            if yahoo_news:
                # Usar la primera noticia como referencia
                url = yahoo_news[0].get("url", "")
                logger.info(f"URL obtenida de Yahoo Finance: {url}")
                
                # Actualizar URL en la base de datos
                try:
                    cursor = connection.cursor()
                    query = "UPDATE market_news SET url = %s, updated_at = NOW() WHERE id = %s"
                    cursor.execute(query, (url, news_id))
                    connection.commit()
                    cursor.close()
                    logger.info(f"URL actualizada para noticia ID {news_id}")
                except Exception as e:
                    logger.error(
                        f"Error actualizando URL para noticia ID {news_id}: {str(e)}"
                    )
        
        # Generar resumen con IA
        summary = generate_summary_with_ai(title, symbol, url)
        
        # Actualizar resumen en la base de datos solo si se generó un resumen válido
        if summary is not None:
            if update_news_summary(connection, news_id, summary):
                logger.info(f"Resumen actualizado para noticia ID {news_id}")
                processed_count += 1
            else:
                logger.error(f"Error actualizando resumen para noticia ID {news_id}")
        else:
            logger.warning(f"No se pudo generar un resumen válido para la noticia ID {news_id}")
        
        # Esperar un poco para no sobrecargar la API
        time.sleep(1)
    
    return processed_count


def process_empty_sentiment_analysis(
    connection: mysql.connector.MySQLConnection, limit: int = 10
) -> int:
    """
    Procesa registros de sentimiento con análisis vacío
    
    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        limit (int): Número máximo de registros a procesar
        
    Returns:
        int: Número de registros procesados
    """
    # Obtener registros de sentimiento con análisis vacío
    empty_sentiment = get_empty_sentiment_analysis(connection, limit)
    
    if not empty_sentiment:
        logger.info("No hay registros de sentimiento con análisis vacío para procesar")
        return 0
    
    logger.info(
        f"Se encontraron {len(empty_sentiment)} registros de sentimiento con análisis vacío"
    )
    
    # Procesar cada registro
    processed_count = 0
    for sentiment in empty_sentiment:
        sentiment_id = sentiment.get("id")
        
        logger.info(f"Procesando sentimiento ID {sentiment_id}...")
        
        # Generar análisis con IA
        analysis = generate_sentiment_analysis_with_ai(sentiment)
        
        # Actualizar análisis en la base de datos solo si se generó un análisis válido
        if analysis is not None:
            if update_sentiment_analysis(connection, sentiment_id, analysis):
                logger.info(f"Análisis actualizado para sentimiento ID {sentiment_id}")
                processed_count += 1
            else:
                logger.error(
                    f"Error actualizando análisis para sentimiento ID {sentiment_id}"
                )
        else:
            logger.warning(f"No se pudo generar un análisis válido para el sentimiento ID {sentiment_id}")
        
        # Esperar un poco para no sobrecargar la API
        time.sleep(1)
    
    return processed_count
