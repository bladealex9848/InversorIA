import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger().setLevel(logging.DEBUG)

try:
    from database_utils import DatabaseManager, extract_symbol_from_title

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

        # Si se extrajo un símbolo y es diferente al actual (que probablemente es SPY)
        if extracted_symbol and (not current_symbol or current_symbol == "SPY"):
            # Actualizar el símbolo en la base de datos
            update_query = "UPDATE market_news SET symbol = %s WHERE id = %s"
            db.execute_query(update_query, [extracted_symbol, news_id], fetch=False)

            print(
                f"ID {news_id}: Símbolo actualizado de '{current_symbol}' a '{extracted_symbol}' - Título: {title[:50]}..."
            )
            updated_count += 1
        else:
            skipped_count += 1

    print(
        f"Actualización completada: {updated_count} registros actualizados, {skipped_count} registros sin cambios"
    )

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback

    traceback.print_exc()
