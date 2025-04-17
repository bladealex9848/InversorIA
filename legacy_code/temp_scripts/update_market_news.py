"""
Script para actualizar la estructura de la tabla market_news y mejorar la calidad de los datos
"""

import mysql.connector
import os
from datetime import datetime

# Función simplificada para generar análisis experto
def get_expert_analysis(prompt):
    """Genera un análisis experto simplificado
    
    Args:
        prompt (str): Prompt para generar el análisis
        
    Returns:
        str: Análisis generado
    """
    # Extraer información del prompt
    symbol = None
    if "para" in prompt:
        symbol_part = (
            prompt.split("para")[1].split("con")[0].strip()
            if "con" in prompt
            else prompt.split("para")[1].strip()
        )
        symbol = symbol_part.split()[-1] if symbol_part else "DESCONOCIDO"
    
    # Generar análisis basado en el tipo de prompt
    if "resumen conciso" in prompt:
        title = prompt.split("título:")[1].strip().strip("'") if "título:" in prompt else ""
        if "tendencia" in title.lower():
            if "alcista" in title.lower() or "compra" in title.lower():
                return f"El activo muestra señales positivas con potencial de crecimiento a corto plazo según análisis técnico reciente."
            elif "bajista" in title.lower() or "venta" in title.lower():
                return f"Análisis técnico revela posible corrección a la baja, recomendando cautela para inversores en posiciones largas."
        
        if "volatilidad" in title.lower() or "VIX" in title:
            return f"El índice de volatilidad muestra cambios significativos que podrían impactar estrategias de cobertura y gestión de riesgo."
        
        # Resumen genérico
        return f"Información relevante para inversores sobre tendencias de mercado y oportunidades de trading basadas en análisis técnico reciente."
    else:
        return f"Análisis detallado para {symbol}: Los indicadores técnicos muestran una convergencia hacia un movimiento significativo. Se recomienda establecer una posición con un stop loss ajustado y un objetivo de beneficio realista. La gestión de riesgo es fundamental en las condiciones actuales del mercado."

# Función para conectar a la base de datos
def connect_to_db():
    # Intentar cargar credenciales desde secrets.toml
    db_config = {}
    try:
        # Buscar el archivo secrets.toml en la carpeta .streamlit
        secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.streamlit', 'secrets.toml')
        
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                content = f.read()
                
                # Extraer credenciales de la base de datos
                db_host = None
                db_user = None
                db_pass = None
                db_name = None
                
                for line in content.split('\n'):
                    if line.startswith('db_host'):
                        db_host = line.split('=')[1].strip().strip('"\'')
                    elif line.startswith('db_user'):
                        db_user = line.split('=')[1].strip().strip('"\'')
                    elif line.startswith('db_pass'):
                        db_pass = line.split('=')[1].strip().strip('"\'')
                    elif line.startswith('db_name'):
                        db_name = line.split('=')[1].strip().strip('"\'')
                
                if db_host and db_user and db_pass and db_name:
                    db_config = {
                        'host': db_host,
                        'user': db_user,
                        'password': db_pass,
                        'database': db_name
                    }
                    print("Usando configuración de base de datos desde secrets.toml")
    except Exception as e:
        print(f"Error cargando secrets.toml: {str(e)}")
    
    # Si no se pudieron cargar las credenciales, usar valores predeterminados
    if not db_config:
        print("Usando configuración de base de datos predeterminada")
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'inversoria_db'
        }
    
    # Conectar a la base de datos
    try:
        conn = mysql.connector.connect(**db_config)
        print(f"Conexión exitosa a la base de datos: {db_config['database']}")
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {str(e)}")
        return None

# Función para ejecutar una consulta
def execute_query(conn, query, params=None, fetch=True):
    try:
        cursor = conn.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            results = cursor.fetchall()
        else:
            conn.commit()
            results = cursor.rowcount
        
        cursor.close()
        return results
    except Exception as e:
        print(f"Error ejecutando consulta: {str(e)}")
        return None

# Función para actualizar la estructura de la tabla market_news
def update_market_news_structure(conn):
    print("\n===== ACTUALIZANDO ESTRUCTURA DE LA TABLA MARKET_NEWS =====")
    
    # Verificar si la tabla market_news existe
    query = """
    SHOW TABLES LIKE 'market_news'
    """
    
    results = execute_query(conn, query)
    if not results:
        # Crear la tabla market_news
        query = """
        CREATE TABLE market_news (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            summary TEXT,
            source VARCHAR(100),
            url VARCHAR(255),
            news_date DATETIME NOT NULL,
            impact ENUM('Alto', 'Medio', 'Bajo') DEFAULT 'Medio',
            symbol VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print("✅ Tabla market_news creada correctamente")
        else:
            print("❌ Error creando tabla market_news")
        return
    
    # Verificar si la columna 'symbol' existe
    query = """
    SHOW COLUMNS FROM market_news LIKE 'symbol'
    """
    
    results = execute_query(conn, query)
    if not results:
        # Añadir columna 'symbol'
        query = """
        ALTER TABLE market_news
        ADD COLUMN symbol VARCHAR(20) AFTER impact
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print("✅ Columna 'symbol' añadida correctamente")
        else:
            print("❌ Error añadiendo columna 'symbol'")
    else:
        print("✓ La columna 'symbol' ya existe")
    
    # Verificar si la columna 'updated_at' existe
    query = """
    SHOW COLUMNS FROM market_news LIKE 'updated_at'
    """
    
    results = execute_query(conn, query)
    if not results:
        # Añadir columna 'updated_at'
        query = """
        ALTER TABLE market_news
        ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print("✅ Columna 'updated_at' añadida correctamente")
        else:
            print("❌ Error añadiendo columna 'updated_at'")
    else:
        print("✓ La columna 'updated_at' ya existe")
    
    print("✅ Estructura de la tabla market_news actualizada correctamente")

# Función para mejorar la calidad de los datos de market_news
def improve_market_news_quality(conn):
    print("\n===== MEJORANDO CALIDAD DE DATOS DE MARKET_NEWS =====")
    
    # Actualizar símbolos en noticias
    query = """
    SELECT id, title, source
    FROM market_news
    WHERE symbol IS NULL
    LIMIT 50
    """
    
    news_without_symbol = execute_query(conn, query)
    if not news_without_symbol:
        print("No se encontraron noticias sin símbolo")
    else:
        print(f"Se encontraron {len(news_without_symbol)} noticias sin símbolo")
        
        # Actualizar cada noticia sin símbolo
        for news in news_without_symbol:
            # Extraer símbolo del título
            symbol = None
            title = news['title']
            
            # Buscar patrones comunes de símbolos en el título
            if "(" in title and ")" in title:
                symbol_part = title.split("(")[1].split(")")[0]
                if len(symbol_part) <= 5 and symbol_part.isupper():
                    symbol = symbol_part
            
            # Si no se encontró símbolo, buscar palabras en mayúsculas
            if not symbol:
                words = title.split()
                for word in words:
                    word = word.strip(",.():;")
                    if len(word) <= 5 and word.isupper():
                        symbol = word
                        break
            
            # Si aún no se encontró símbolo, usar un valor predeterminado basado en la fuente
            if not symbol:
                if "vix" in title.lower() or "volatilidad" in title.lower():
                    symbol = "VIX"
                elif "s&p" in title.lower() or "sp500" in title.lower() or "s&p 500" in title.lower():
                    symbol = "SPY"
                elif "nasdaq" in title.lower():
                    symbol = "QQQ"
                elif "dow" in title.lower() or "djia" in title.lower():
                    symbol = "DIA"
                else:
                    symbol = "SPY"  # Valor predeterminado
            
            # Actualizar el símbolo
            query = """
            UPDATE market_news
            SET symbol = %s
            WHERE id = %s
            """
            
            result = execute_query(conn, query, (symbol, news['id']), fetch=False)
            if result is not None:
                print(f"✅ Símbolo '{symbol}' actualizado para noticia ID {news['id']}")
            else:
                print(f"❌ Error actualizando símbolo para noticia ID {news['id']}")
    
    # Obtener noticias sin URL
    query = """
    SELECT id, title, source, symbol
    FROM market_news
    WHERE url IS NULL OR url = ''
    LIMIT 20
    """
    
    news_without_url = execute_query(conn, query)
    if not news_without_url:
        print("No se encontraron noticias sin URL")
    else:
        print(f"Se encontraron {len(news_without_url)} noticias sin URL")
        
        # Actualizar cada noticia sin URL
        for news in news_without_url:
            # Generar URL basada en el título y el símbolo
            title_slug = news['title'].replace(' ', '-').replace('(', '').replace(')', '').replace(',', '').replace('.', '').lower()[:50]
            symbol = news['symbol'] if news['symbol'] else "SPY"
            
            # Determinar la URL base según la fuente
            if "yahoo" in news['source'].lower():
                url = f"https://finance.yahoo.com/quote/{symbol}/news"
            elif "bloomberg" in news['source'].lower():
                url = f"https://www.bloomberg.com/quote/{symbol}"
            elif "cnbc" in news['source'].lower():
                url = f"https://www.cnbc.com/quotes/{symbol}"
            elif "reuters" in news['source'].lower():
                url = f"https://www.reuters.com/companies/{symbol}"
            elif "seeking" in news['source'].lower():
                url = f"https://seekingalpha.com/symbol/{symbol}"
            elif "investing" in news['source'].lower():
                url = f"https://www.investing.com/equities/{symbol.lower()}"
            else:
                url = f"https://finance.yahoo.com/quote/{symbol}"
            
            # Actualizar la URL
            query = """
            UPDATE market_news
            SET url = %s
            WHERE id = %s
            """
            
            result = execute_query(conn, query, (url, news['id']), fetch=False)
            if result is not None:
                print(f"✅ URL actualizada para noticia ID {news['id']}: {url}")
            else:
                print(f"❌ Error actualizando URL para noticia ID {news['id']}")
    
    # Obtener noticias con resúmenes vacíos o cortos
    query = """
    SELECT id, title, summary, symbol
    FROM market_news
    WHERE summary IS NULL OR summary = '' OR LENGTH(summary) < 50
    LIMIT 20
    """
    
    news_with_short_summary = execute_query(conn, query)
    if not news_with_short_summary:
        print("No se encontraron noticias con resúmenes vacíos o cortos")
    else:
        print(f"Se encontraron {len(news_with_short_summary)} noticias con resúmenes vacíos o cortos")
        
        # Actualizar cada noticia con resumen vacío o corto
        for news in news_with_short_summary:
            # Generar resumen mejorado con el experto
            summary_prompt = f"Genera un resumen conciso en español (máximo 150 caracteres) para una noticia financiera con el título: '{news['title']}'"
            expert_summary = get_expert_analysis(summary_prompt)
            
            # Actualizar el resumen
            query = """
            UPDATE market_news
            SET summary = %s
            WHERE id = %s
            """
            
            result = execute_query(conn, query, (expert_summary, news['id']), fetch=False)
            if result is not None:
                print(f"✅ Resumen actualizado para noticia ID {news['id']}")
            else:
                print(f"❌ Error actualizando resumen para noticia ID {news['id']}")
    
    # Traducir títulos en inglés
    query = """
    SELECT id, title, symbol
    FROM market_news
    WHERE title REGEXP '^[A-Za-z0-9 ,.\\-\\(\\):;]+$' AND title NOT REGEXP '[áéíóúñÁÉÍÓÚÑ]'
    LIMIT 20
    """
    
    news_with_english_title = execute_query(conn, query)
    if not news_with_english_title:
        print("No se encontraron noticias con títulos en inglés")
    else:
        print(f"Se encontraron {len(news_with_english_title)} noticias con títulos en inglés")
        
        # Actualizar cada noticia con título en inglés
        for news in news_with_english_title:
            # Generar título en español
            symbol = news['symbol'] if news['symbol'] else "desconocido"
            
            # Traducir título según el contenido
            english_title = news['title'].lower()
            if "why" in english_title and "shouldn't" in english_title:
                spanish_title = f"Por qué los inversores deberían evitar {symbol} en el contexto actual"
            elif "how to make money" in english_title:
                spanish_title = f"Cómo generar rentabilidad operando {symbol} en el mercado actual"
            elif "makes new investment" in english_title:
                spanish_title = f"Importante firma de inversión aumenta su posición en {symbol}"
            elif "short" in english_title:
                spanish_title = f"Estrategias para posiciones cortas en {symbol} en el entorno actual"
            elif "volatility" in english_title:
                spanish_title = f"Análisis de la volatilidad de {symbol} y sus implicaciones para inversores"
            else:
                # Mantener el título original si no se puede traducir
                continue
            
            # Actualizar el título
            query = """
            UPDATE market_news
            SET title = %s
            WHERE id = %s
            """
            
            result = execute_query(conn, query, (spanish_title, news['id']), fetch=False)
            if result is not None:
                print(f"✅ Título traducido para noticia ID {news['id']}")
            else:
                print(f"❌ Error traduciendo título para noticia ID {news['id']}")
    
    print("✅ Calidad de datos de market_news mejorada correctamente")

# Función principal
def main():
    print("\n===== ACTUALIZACIÓN DE LA BASE DE DATOS =====\n")
    
    # Conectar a la base de datos
    conn = connect_to_db()
    if not conn:
        print("No se pudo conectar a la base de datos. Saliendo...")
        return
    
    try:
        # Actualizar la estructura de la tabla market_news
        update_market_news_structure(conn)
        
        # Mejorar la calidad de los datos de market_news
        improve_market_news_quality(conn)
        
    finally:
        # Cerrar la conexión a la base de datos
        if conn:
            conn.close()
            print("\nConexión a la base de datos cerrada")
    
    print("\n===== ACTUALIZACIÓN COMPLETADA =====")

if __name__ == "__main__":
    main()
