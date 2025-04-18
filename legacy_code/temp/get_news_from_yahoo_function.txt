def get_news_from_yahoo(symbol: str, max_news: int = 5) -> List[Dict[str, Any]]:
    """
    Obtiene noticias de Yahoo Finance
    
    Args:
        symbol (str): Símbolo del activo
        max_news (int): Número máximo de noticias a obtener
        
    Returns:
        List[Dict[str, Any]]: Lista de noticias
    """
    if not YAHOO_SCRAPER_AVAILABLE:
        logger.warning("YahooFinanceScraper no está disponible. No se pueden obtener noticias de Yahoo Finance.")
        return []
    
    try:
        # Inicializar scraper
        scraper = YahooFinanceScraper()
        
        # Obtener noticias
        news = scraper.get_news(symbol, max_news)
        
        return news
    except Exception as e:
        logger.error(f"Error obteniendo noticias de Yahoo Finance para {symbol}: {str(e)}")
        return []
