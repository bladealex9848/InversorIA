"""
Script para actualizar la estructura de la tabla trading_signals
"""

import mysql.connector
import os
from datetime import datetime

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
    
    # Verificar si la columna 'signal_date' existe
    query = """
    SHOW COLUMNS FROM trading_signals LIKE 'signal_date'
    """
    
    results = execute_query(conn, query)
    if not results:
        # Añadir columna 'signal_date' con valor por defecto
        query = """
        ALTER TABLE trading_signals
        ADD COLUMN signal_date DATE DEFAULT CURRENT_DATE AFTER sentiment_score
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print("✅ Columna 'signal_date' añadida correctamente con valor por defecto")
        else:
            print("❌ Error añadiendo columna 'signal_date'")
    else:
        # Modificar la columna 'signal_date' para añadir valor por defecto
        query = """
        ALTER TABLE trading_signals
        MODIFY COLUMN signal_date DATE DEFAULT CURRENT_DATE
        """
        
        result = execute_query(conn, query, fetch=False)
        if result is not None:
            print("✅ Columna 'signal_date' modificada para añadir valor por defecto")
        else:
            print("❌ Error modificando columna 'signal_date'")
    
    print("✅ Estructura de la tabla trading_signals actualizada correctamente")

# Función principal
def main():
    print("\n===== ACTUALIZACIÓN DE LA TABLA TRADING_SIGNALS =====\n")
    
    # Conectar a la base de datos
    conn = connect_to_db()
    if not conn:
        print("No se pudo conectar a la base de datos. Saliendo...")
        return
    
    try:
        # Actualizar la estructura de la tabla trading_signals
        update_trading_signals_structure(conn)
        
    finally:
        # Cerrar la conexión a la base de datos
        if conn:
            conn.close()
            print("\nConexión a la base de datos cerrada")
    
    print("\n===== ACTUALIZACIÓN COMPLETADA =====")

if __name__ == "__main__":
    main()
