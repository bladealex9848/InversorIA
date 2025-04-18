from database_utils import DatabaseManager, extract_symbol_from_title

print("Conectando a la base de datos...")
db = DatabaseManager()
print("Conexión establecida")

# Obtener todas las noticias
print("Obteniendo noticias...")
news = db.execute_query("SELECT id, title, symbol FROM market_news LIMIT 20")
print(f"Se obtuvieron {len(news)} noticias")

# Mostrar las noticias
for item in news:
    title = item["title"]
    extracted_symbol = extract_symbol_from_title(title)
    print(
        f"ID: {item['id']}, Título: {title[:50]}..., Símbolo actual: {item['symbol']}, Símbolo extraído: {extracted_symbol}"
    )

# Actualizar los símbolos
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

        print(
            f"ID {news_id}: Símbolo actualizado de '{current_symbol}' a '{extracted_symbol}' - Título: {title[:50]}..."
        )
        updated_count += 1
    else:
        skipped_count += 1

print(
    f"Actualización completada: {updated_count} registros actualizados, {skipped_count} registros sin cambios"
)
