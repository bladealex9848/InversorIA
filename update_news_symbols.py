"""
Script para actualizar los símbolos en la tabla market_news basado en los títulos y contenido de las noticias.
Utiliza la función mejorada extract_symbol_from_content para obtener símbolos más precisos.
"""

import logging
import sys
from database_utils import DatabaseManager, extract_symbol_from_content
from company_data import COMPANY_INFO

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
    Actualiza los símbolos en la tabla market_news basado en los títulos y contenido de las noticias.
    Utiliza la función mejorada extract_symbol_from_content para obtener símbolos más precisos.

    Returns:
        tuple: (número de registros actualizados, número de registros sin cambios)
    """
    try:
        print("Conectando a la base de datos...")
        db = DatabaseManager()
        print("Conexión establecida")

        # Obtener todas las noticias con resumen
        print("Obteniendo noticias...")
        news = db.execute_query("SELECT id, title, summary, symbol FROM market_news")
        print(f"Se obtuvieron {len(news)} noticias")

        updated_count = 0
        skipped_count = 0

        for item in news:
            news_id = item["id"]
            title = item["title"]
            current_symbol = item["symbol"]

            # Extraer símbolo del título y resumen
            summary = item.get("summary", "")
            extracted_symbol = extract_symbol_from_content(title, summary)

            # Si se extrajo un símbolo y es diferente al actual
            if extracted_symbol and extracted_symbol != current_symbol:
                # Validar que el símbolo exista en COMPANY_INFO o sea un índice común
                common_indices = ["SPY", "QQQ", "DIA", "IWM", "VIX"]
                if (
                    extracted_symbol not in COMPANY_INFO
                    and extracted_symbol not in common_indices
                ):
                    logger.warning(
                        f"ID {news_id}: Símbolo extraído '{extracted_symbol}' no válido - Título: {title[:50]}..."
                    )
                    # Marcar para revisión manual
                    extracted_symbol = "REVIEW"
                # Actualizar el símbolo en la base de datos
                update_query = "UPDATE market_news SET symbol = %s WHERE id = %s"
                db.execute_query(update_query, [extracted_symbol, news_id], fetch=False)

                logger.info(
                    f"ID {news_id}: Símbolo actualizado de '{current_symbol}' a '{extracted_symbol}' - Título: {title[:50]}..."
                )
                updated_count += 1
            else:
                # Si el símbolo actual es SPY y no se pudo extraer uno mejor, marcar para revisión manual
                if current_symbol == "SPY" or not current_symbol:
                    update_query = "UPDATE market_news SET symbol = %s WHERE id = %s"
                    db.execute_query(update_query, ["REVIEW", news_id], fetch=False)
                    logger.info(
                        f"ID {news_id}: Marcado para revisión manual - Título: {title[:50]}..."
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
