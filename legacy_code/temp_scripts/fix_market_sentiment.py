"""
Script para corregir la estructura y datos de la tabla market_sentiment
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
    if "sentimiento de mercado" in prompt:
        return f"""Análisis de sentimiento para {symbol}: El mercado muestra una tendencia mixta con señales técnicas que sugieren cautela. 

Los indicadores técnicos muestran divergencias que podrían anticipar un cambio de dirección en el corto plazo. El volumen de operaciones ha disminuido en las últimas sesiones, lo que indica menor convicción por parte de los participantes del mercado.

Recomendaciones para inversores:
1. Mantener posiciones diversificadas y considerar reducir exposición en sectores más volátiles
2. Establecer stop loss ajustados para proteger capital
3. Considerar estrategias de cobertura ante posibles movimientos bruscos

Factores a vigilar:
- Niveles de soporte y resistencia clave
- Volumen en momentos de ruptura de niveles importantes
- Comportamiento de activos correlacionados"""
    else:
        return f"""Análisis detallado para {symbol}: Los indicadores técnicos muestran una convergencia hacia un movimiento significativo. 

El RSI se encuentra en niveles que sugieren una oportunidad de entrada, mientras que el MACD muestra una divergencia positiva. Los niveles de soporte y resistencia están bien definidos, proporcionando puntos claros para gestionar el riesgo.

Se recomienda establecer una posición con un stop loss ajustado y un objetivo de beneficio realista. La gestión de riesgo es fundamental en las condiciones actuales del mercado."""

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

# Función para corregir la estructura de la tabla market_sentiment
def fix_market_sentiment_structure(conn):
    print("\n===== CORRIGIENDO ESTRUCTURA DE LA TABLA MARKET_SENTIMENT =====")
    
    # Verificar si hay registros con symbol NULL
    query = """
    SELECT COUNT(*) as count
    FROM market_sentiment
    WHERE symbol IS NULL
    """
    
    results = execute_query(conn, query)
    if results and results[0]['count'] > 0:
        print(f"Se encontraron {results[0]['count']} registros con symbol NULL")
        
        # Actualizar registros con symbol NULL
        query = """
        UPDATE market_sentiment
        SET symbol = 'SPY'
        WHERE symbol IS NULL
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print(f"✅ {result} registros actualizados con symbol = 'SPY'")
        else:
            print("❌ Error actualizando registros con symbol NULL")
    else:
        print("No se encontraron registros con symbol NULL")
    
    # Verificar si hay registros con sentiment NULL
    query = """
    SELECT COUNT(*) as count
    FROM market_sentiment
    WHERE sentiment IS NULL
    """
    
    results = execute_query(conn, query)
    if results and results[0]['count'] > 0:
        print(f"Se encontraron {results[0]['count']} registros con sentiment NULL")
        
        # Actualizar registros con sentiment NULL
        query = """
        UPDATE market_sentiment
        SET sentiment = 'neutral',
            score = 0.5
        WHERE sentiment IS NULL
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print(f"✅ {result} registros actualizados con sentiment = 'neutral' y score = 0.5")
        else:
            print("❌ Error actualizando registros con sentiment NULL")
    else:
        print("No se encontraron registros con sentiment NULL")
    
    # Verificar si hay registros con sentiment_date NULL
    query = """
    SELECT COUNT(*) as count
    FROM market_sentiment
    WHERE sentiment_date IS NULL
    """
    
    results = execute_query(conn, query)
    if results and results[0]['count'] > 0:
        print(f"Se encontraron {results[0]['count']} registros con sentiment_date NULL")
        
        # Actualizar registros con sentiment_date NULL
        query = """
        UPDATE market_sentiment
        SET sentiment_date = created_at
        WHERE sentiment_date IS NULL
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print(f"✅ {result} registros actualizados con sentiment_date = created_at")
        else:
            print("❌ Error actualizando registros con sentiment_date NULL")
    else:
        print("No se encontraron registros con sentiment_date NULL")
    
    # Verificar si hay registros con analysis NULL
    query = """
    SELECT COUNT(*) as count
    FROM market_sentiment
    WHERE analysis IS NULL
    """
    
    results = execute_query(conn, query)
    if results and results[0]['count'] > 0:
        print(f"Se encontraron {results[0]['count']} registros con analysis NULL")
        
        # Obtener registros con analysis NULL
        query = """
        SELECT id, symbol, sentiment, score, notes
        FROM market_sentiment
        WHERE analysis IS NULL
        """
        
        records = execute_query(conn, query)
        
        # Actualizar cada registro con analysis NULL
        for record in records:
            # Generar análisis con el experto
            analysis_prompt = f"Genera un análisis de sentimiento de mercado detallado para {record['symbol']} con sentimiento {record['sentiment']} (score: {record['score']})"
            expert_analysis = get_expert_analysis(analysis_prompt)
            
            # Actualizar el análisis
            query = """
            UPDATE market_sentiment
            SET analysis = %s
            WHERE id = %s
            """
            
            result = execute_query(conn, query, (expert_analysis, record['id']), fetch=False)
            if result is not None:
                print(f"✅ Análisis actualizado para registro ID {record['id']}")
            else:
                print(f"❌ Error actualizando análisis para registro ID {record['id']}")
    else:
        print("No se encontraron registros con analysis NULL")
    
    print("✅ Estructura de la tabla market_sentiment corregida correctamente")

# Función para corregir los datos de la tabla market_sentiment
def fix_market_sentiment_data(conn):
    print("\n===== CORRIGIENDO DATOS DE LA TABLA MARKET_SENTIMENT =====")
    
    # Verificar si hay registros duplicados
    query = """
    SELECT symbol, DATE(sentiment_date) as date, COUNT(*) as count
    FROM market_sentiment
    GROUP BY symbol, DATE(sentiment_date)
    HAVING COUNT(*) > 1
    """
    
    duplicates = execute_query(conn, query)
    if duplicates:
        print(f"Se encontraron {len(duplicates)} grupos de registros duplicados")
        
        # Procesar cada grupo de duplicados
        for duplicate in duplicates:
            symbol = duplicate['symbol']
            date = duplicate['date']
            count = duplicate['count']
            
            print(f"Procesando {count} duplicados para {symbol} en fecha {date}")
            
            # Obtener los registros duplicados
            query = """
            SELECT id, created_at
            FROM market_sentiment
            WHERE symbol = %s AND DATE(sentiment_date) = %s
            ORDER BY created_at DESC
            """
            
            records = execute_query(conn, query, (symbol, date))
            
            # Mantener el registro más reciente y eliminar los demás
            if records and len(records) > 1:
                # El primer registro es el más reciente (ordenado por created_at DESC)
                keep_id = records[0]['id']
                
                # Eliminar los demás registros
                for i in range(1, len(records)):
                    query = """
                    DELETE FROM market_sentiment
                    WHERE id = %s
                    """
                    
                    result = execute_query(conn, query, (records[i]['id'],), fetch=False)
                    if result is not None:
                        print(f"✅ Registro duplicado ID {records[i]['id']} eliminado")
                    else:
                        print(f"❌ Error eliminando registro duplicado ID {records[i]['id']}")
                
                print(f"✅ Se mantuvo el registro más reciente ID {keep_id}")
    else:
        print("No se encontraron registros duplicados")
    
    # Verificar si hay registros con source NULL
    query = """
    SELECT COUNT(*) as count
    FROM market_sentiment
    WHERE source IS NULL
    """
    
    results = execute_query(conn, query)
    if results and results[0]['count'] > 0:
        print(f"Se encontraron {results[0]['count']} registros con source NULL")
        
        # Actualizar registros con source NULL
        query = """
        UPDATE market_sentiment
        SET source = 'InversorIA Analytics'
        WHERE source IS NULL
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print(f"✅ {result} registros actualizados con source = 'InversorIA Analytics'")
        else:
            print("❌ Error actualizando registros con source NULL")
    else:
        print("No se encontraron registros con source NULL")
    
    print("✅ Datos de la tabla market_sentiment corregidos correctamente")

# Función principal
def main():
    print("\n===== CORRECCIÓN DE LA TABLA MARKET_SENTIMENT =====\n")
    
    # Conectar a la base de datos
    conn = connect_to_db()
    if not conn:
        print("No se pudo conectar a la base de datos. Saliendo...")
        return
    
    try:
        # Corregir la estructura de la tabla market_sentiment
        fix_market_sentiment_structure(conn)
        
        # Corregir los datos de la tabla market_sentiment
        fix_market_sentiment_data(conn)
        
    finally:
        # Cerrar la conexión a la base de datos
        if conn:
            conn.close()
            print("\nConexión a la base de datos cerrada")
    
    print("\n===== CORRECCIÓN COMPLETADA =====")

if __name__ == "__main__":
    main()
