"""
Script para actualizar los símbolos en la tabla market_news basado en los títulos de las noticias.
"""

import logging
from database_utils import DatabaseManager, extract_symbol_from_title

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("update_news_symbols")

def update_news_symbols():
    """
    Actualiza los símbolos en la tabla market_news basado en los títulos de las noticias.
    """
    db = DatabaseManager()
    
    # Obtener todas las noticias
    news = db.execute_query("SELECT id, title, symbol FROM market_news")
    
    updated_count = 0
    skipped_count = 0
    
    for item in news:
        news_id = item['id']
        title = item['title']
        current_symbol = item['symbol']
        
        # Extraer símbolo del título
        extracted_symbol = extract_symbol_from_title(title)
        
        # Si se extrajo un símbolo y es diferente al actual (que probablemente es SPY)
        if extracted_symbol and (not current_symbol or current_symbol == 'SPY'):
            # Actualizar el símbolo en la base de datos
            update_query = "UPDATE market_news SET symbol = %s WHERE id = %s"
            db.execute_query(update_query, [extracted_symbol, news_id], fetch=False)
            
            logger.info(f"ID {news_id}: Símbolo actualizado de '{current_symbol}' a '{extracted_symbol}' - Título: {title[:50]}...")
            updated_count += 1
        else:
            skipped_count += 1
    
    logger.info(f"Actualización completada: {updated_count} registros actualizados, {skipped_count} registros sin cambios")
    return updated_count, skipped_count

if __name__ == "__main__":
    logger.info("Iniciando actualización de símbolos en noticias...")
    updated, skipped = update_news_symbols()
    logger.info(f"Proceso finalizado: {updated} registros actualizados, {skipped} registros sin cambios")
