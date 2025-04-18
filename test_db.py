from database_utils import DatabaseManager

print("Conectando a la base de datos...")
db = DatabaseManager()
print("Conexión establecida")

# Obtener todas las noticias
print("Obteniendo noticias...")
news = db.execute_query("SELECT id, title, symbol FROM market_news LIMIT 5")
print(f"Se obtuvieron {len(news)} noticias")

# Mostrar las noticias
for item in news:
    print(f"ID: {item['id']}, Título: {item['title'][:50]}..., Símbolo: {item['symbol']}")
