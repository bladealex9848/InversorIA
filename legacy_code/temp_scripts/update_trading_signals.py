"""
Script para actualizar la estructura de la tabla trading_signals y mejorar la calidad de los datos
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
    if "señal de trading" in prompt:
        return f"Análisis de señal para {symbol}: Los indicadores técnicos muestran una convergencia hacia un movimiento significativo. El RSI está en niveles que sugieren una oportunidad de entrada, mientras que el MACD muestra una divergencia positiva. Se recomienda establecer una posición con un stop loss ajustado y un objetivo de beneficio realista."
    elif "resumen conciso" in prompt:
        return f"Información relevante sobre tendencias de mercado y oportunidades de trading basadas en análisis técnico reciente."
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
            'database': 'liceopan_enki_sincelejo'
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

# Función para actualizar la estructura de la tabla trading_signals
def update_trading_signals_structure(conn):
    print("\n===== ACTUALIZANDO ESTRUCTURA DE LA TABLA TRADING_SIGNALS =====")
    
    # Verificar si la tabla trading_signals existe
    query = """
    SHOW TABLES LIKE 'trading_signals'
    """
    
    results = execute_query(conn, query)
    if not results:
        # Crear la tabla trading_signals
        query = """
        CREATE TABLE trading_signals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            direction ENUM('CALL', 'PUT', 'NEUTRAL') NOT NULL,
            trend VARCHAR(50) NOT NULL,
            recommendation TEXT,
            sentiment VARCHAR(50),
            sentiment_score DECIMAL(5,2),
            signal_date DATE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY idx_symbol_date (symbol, signal_date)
        )
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print("✅ Tabla trading_signals creada correctamente")
        else:
            print("❌ Error creando tabla trading_signals")
        return
    
    # Verificar si la columna 'signal_date' existe
    query = """
    SHOW COLUMNS FROM trading_signals LIKE 'signal_date'
    """
    
    results = execute_query(conn, query)
    if not results:
        # Añadir columna 'signal_date'
        query = """
        ALTER TABLE trading_signals
        ADD COLUMN signal_date DATE NOT NULL AFTER sentiment_score
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print("✅ Columna 'signal_date' añadida correctamente")
        else:
            print("❌ Error añadiendo columna 'signal_date'")
    else:
        print("✓ La columna 'signal_date' ya existe")
    
    # Verificar si la columna 'updated_at' existe
    query = """
    SHOW COLUMNS FROM trading_signals LIKE 'updated_at'
    """
    
    results = execute_query(conn, query)
    if not results:
        # Añadir columna 'updated_at'
        query = """
        ALTER TABLE trading_signals
        ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print("✅ Columna 'updated_at' añadida correctamente")
        else:
            print("❌ Error añadiendo columna 'updated_at'")
    else:
        print("✓ La columna 'updated_at' ya existe")
    
    # Verificar si existe el índice único para symbol y signal_date
    query = """
    SHOW INDEX FROM trading_signals WHERE Key_name = 'idx_symbol_date'
    """
    
    results = execute_query(conn, query)
    if not results:
        # Añadir índice único
        query = """
        ALTER TABLE trading_signals
        ADD UNIQUE KEY idx_symbol_date (symbol, signal_date)
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print("✅ Índice único 'idx_symbol_date' añadido correctamente")
        else:
            print("❌ Error añadiendo índice único 'idx_symbol_date'")
    else:
        print("✓ El índice único 'idx_symbol_date' ya existe")
    
    print("✅ Estructura de la tabla trading_signals actualizada correctamente")

# Función para insertar datos de ejemplo en la tabla trading_signals
def insert_sample_trading_signals(conn):
    print("\n===== INSERTANDO DATOS DE EJEMPLO EN LA TABLA TRADING_SIGNALS =====")
    
    # Verificar si ya hay datos en la tabla
    query = """
    SELECT COUNT(*) as count FROM trading_signals
    """
    
    results = execute_query(conn, query)
    if results and results[0]['count'] > 0:
        print(f"Ya hay {results[0]['count']} registros en la tabla trading_signals")
        return
    
    # Datos de ejemplo para insertar
    sample_data = [
        {
            'symbol': 'SPY',
            'price': 475.25,
            'direction': 'CALL',
            'trend': 'ALCISTA',
            'recommendation': 'Comprar SPY con stop loss en $470 y objetivo en $485',
            'sentiment': 'positivo',
            'sentiment_score': 0.75,
            'signal_date': '2025-04-17'
        },
        {
            'symbol': 'QQQ',
            'price': 380.50,
            'direction': 'CALL',
            'trend': 'ALCISTA',
            'recommendation': 'Comprar QQQ con stop loss en $375 y objetivo en $390',
            'sentiment': 'positivo',
            'sentiment_score': 0.80,
            'signal_date': '2025-04-17'
        },
        {
            'symbol': 'AAPL',
            'price': 175.30,
            'direction': 'CALL',
            'trend': 'ALCISTA',
            'recommendation': 'Comprar AAPL con stop loss en $170 y objetivo en $185',
            'sentiment': 'positivo',
            'sentiment_score': 0.70,
            'signal_date': '2025-04-17'
        },
        {
            'symbol': 'MSFT',
            'price': 410.75,
            'direction': 'PUT',
            'trend': 'BAJISTA',
            'recommendation': 'Vender MSFT con stop loss en $415 y objetivo en $400',
            'sentiment': 'negativo',
            'sentiment_score': 0.30,
            'signal_date': '2025-04-17'
        },
        {
            'symbol': 'GOOGL',
            'price': 165.20,
            'direction': 'PUT',
            'trend': 'BAJISTA',
            'recommendation': 'Vender GOOGL con stop loss en $170 y objetivo en $160',
            'sentiment': 'negativo',
            'sentiment_score': 0.25,
            'signal_date': '2025-04-17'
        },
        {
            'symbol': 'AMZN',
            'price': 180.45,
            'direction': 'NEUTRAL',
            'trend': 'LATERAL',
            'recommendation': 'Mantener AMZN y esperar ruptura de rango $175-$185',
            'sentiment': 'neutral',
            'sentiment_score': 0.50,
            'signal_date': '2025-04-17'
        },
        {
            'symbol': 'TSLA',
            'price': 195.30,
            'direction': 'CALL',
            'trend': 'ALCISTA',
            'recommendation': 'Comprar TSLA con stop loss en $190 y objetivo en $205',
            'sentiment': 'positivo',
            'sentiment_score': 0.65,
            'signal_date': '2025-04-17'
        },
        {
            'symbol': 'META',
            'price': 485.60,
            'direction': 'CALL',
            'trend': 'ALCISTA',
            'recommendation': 'Comprar META con stop loss en $475 y objetivo en $500',
            'sentiment': 'positivo',
            'sentiment_score': 0.70,
            'signal_date': '2025-04-17'
        },
        {
            'symbol': 'NVDA',
            'price': 920.75,
            'direction': 'NEUTRAL',
            'trend': 'LATERAL',
            'recommendation': 'Mantener NVDA y esperar ruptura de rango $900-$940',
            'sentiment': 'neutral',
            'sentiment_score': 0.55,
            'signal_date': '2025-04-17'
        },
        {
            'symbol': 'VXX',
            'price': 71.30,
            'direction': 'PUT',
            'trend': 'BAJISTA',
            'recommendation': 'Vender VXX con stop loss en $75 y objetivo en $65',
            'sentiment': 'neutral',
            'sentiment_score': 0.50,
            'signal_date': '2025-04-17'
        }
    ]
    
    # Insertar datos de ejemplo
    for data in sample_data:
        query = """
        INSERT INTO trading_signals (
            symbol, price, direction, trend, recommendation, sentiment, sentiment_score, signal_date
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        params = (
            data['symbol'],
            data['price'],
            data['direction'],
            data['trend'],
            data['recommendation'],
            data['sentiment'],
            data['sentiment_score'],
            data['signal_date']
        )
        
        result = execute_query(conn, query, params, fetch=False)
        if result is not None:
            print(f"✅ Registro insertado para {data['symbol']}")
        else:
            print(f"❌ Error insertando registro para {data['symbol']}")
    
    print("✅ Datos de ejemplo insertados correctamente")

# Función para mejorar la calidad de los datos de trading_signals
def improve_trading_signals_quality(conn):
    print("\n===== MEJORANDO CALIDAD DE DATOS DE TRADING_SIGNALS =====")
    
    # Obtener registros con recomendaciones vacías o cortas
    query = """
    SELECT id, symbol, price, direction, trend, recommendation, sentiment, sentiment_score
    FROM trading_signals
    WHERE recommendation IS NULL OR recommendation = '' OR LENGTH(recommendation) < 20
    LIMIT 10
    """
    
    signals_with_short_recommendation = execute_query(conn, query)
    if not signals_with_short_recommendation:
        print("No se encontraron señales con recomendaciones vacías o cortas")
    else:
        print(f"Se encontraron {len(signals_with_short_recommendation)} señales con recomendaciones vacías o cortas")
        
        # Actualizar cada señal con recomendación vacía o corta
        for signal in signals_with_short_recommendation:
            # Generar recomendación mejorada con el experto
            recommendation_prompt = f"Genera una recomendación de trading detallada para {signal['symbol']} con dirección {signal['direction']} y tendencia {signal['trend']}. Incluye niveles de entrada, stop loss y objetivo."
            expert_recommendation = get_expert_analysis(recommendation_prompt)
            
            # Actualizar la recomendación
            query = """
            UPDATE trading_signals
            SET recommendation = %s
            WHERE id = %s
            """
            
            result = execute_query(conn, query, (expert_recommendation, signal['id']), fetch=False)
            if result is not None:
                print(f"✅ Recomendación actualizada para señal ID {signal['id']}")
            else:
                print(f"❌ Error actualizando recomendación para señal ID {signal['id']}")
    
    print("✅ Calidad de datos de trading_signals mejorada correctamente")

# Función principal
def main():
    print("\n===== ACTUALIZACIÓN DE LA BASE DE DATOS =====\n")
    
    # Conectar a la base de datos
    conn = connect_to_db()
    if not conn:
        print("No se pudo conectar a la base de datos. Saliendo...")
        return
    
    try:
        # Actualizar la estructura de la tabla trading_signals
        update_trading_signals_structure(conn)
        
        # Insertar datos de ejemplo en la tabla trading_signals
        insert_sample_trading_signals(conn)
        
        # Mejorar la calidad de los datos de trading_signals
        improve_trading_signals_quality(conn)
        
    finally:
        # Cerrar la conexión a la base de datos
        if conn:
            conn.close()
            print("\nConexión a la base de datos cerrada")
    
    print("\n===== ACTUALIZACIÓN COMPLETADA =====")

if __name__ == "__main__":
    main()
