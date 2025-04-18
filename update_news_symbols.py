"""
Script para actualizar los símbolos en la tabla market_news basado en los títulos de las noticias.
"""

import logging
import sys
from database_utils import DatabaseManager, extract_symbol_from_title

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("update_news_symbols")
logger.setLevel(logging.DEBUG)

# Asegurar que los mensajes se muestren en la consola
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def update_news_symbols():
    """
    Actualiza los símbolos en la tabla market_news basado en los títulos de las noticias.
    """
    try:
        print("Conectando a la base de datos...")
        db = DatabaseManager()
        print("Conexión establecida")

        # Obtener todas las noticias
        print("Obteniendo noticias...")
        news = db.execute_query("SELECT id, title, symbol FROM market_news")
        print(f"Se obtuvieron {len(news)} noticias")

        updated_count = 0
        skipped_count = 0

        for item in news:
            news_id = item["id"]
            title = item["title"]
            current_symbol = item["symbol"]

            # Extraer símbolo del título
            extracted_symbol = extract_symbol_from_title(title)

            # Si se extrajo un símbolo y es diferente al actual
            if extracted_symbol and extracted_symbol != current_symbol:
                # Actualizar el símbolo en la base de datos
                update_query = "UPDATE market_news SET symbol = %s WHERE id = %s"
                db.execute_query(update_query, [extracted_symbol, news_id], fetch=False)

                logger.info(
                    f"ID {news_id}: Símbolo actualizado de '{current_symbol}' a '{extracted_symbol}' - Título: {title[:50]}..."
                )
                updated_count += 1
            else:
                skipped_count += 1

        logger.info(
            f"Actualización completada: {updated_count} registros actualizados, {skipped_count} registros sin cambios"
        )
        return updated_count, skipped_count
    except Exception as e:
        logger.error(f"Error en update_news_symbols: {str(e)}")
        logger.error("Traza completa:", exc_info=True)
        return 0, 0


if __name__ == "__main__":
    print("Iniciando actualización de símbolos en noticias...")
    try:
        print("Conectando a la base de datos...")
        from database_utils import DatabaseManager

        db = DatabaseManager()
        print("Conexión establecida")

        print("Ejecutando update_news_symbols()...")
        updated, skipped = update_news_symbols()
        print(
            f"Proceso finalizado: {updated} registros actualizados, {skipped} registros sin cambios"
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()
