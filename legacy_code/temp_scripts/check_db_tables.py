"""
Script para verificar las tablas de la base de datos y detectar columnas vacías o nulas
"""

import logging
import mysql.connector
import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_db_config():
    """Obtiene la configuración de la base de datos desde secrets.toml"""
    try:
        # Intentar obtener configuración desde secrets.toml
        if hasattr(st, "secrets") and "db_host" in st.secrets:
            logger.info("Usando configuración de base de datos desde secrets.toml")
            return {
                "host": st.secrets.get("db_host", "localhost"),
                "port": st.secrets.get("db_port", 3306),
                "user": st.secrets.get("db_user", "root"),
                "password": st.secrets.get("db_password", ""),
                "database": st.secrets.get("db_name", "inversoria"),
            }
        else:
            logger.warning(
                "No se encontró configuración de base de datos en secrets.toml, usando valores por defecto"
            )
            return {
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "",
                "database": "inversoria_db",
            }
    except Exception as e:
        logger.error(f"Error obteniendo configuración de BD: {str(e)}")
        return {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "inversoria_db",
        }


def execute_query(connection, query, params=None, fetch=True):
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        cursor = connection.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if fetch:
            results = cursor.fetchall()
            cursor.close()
            return results
        else:
            connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
    except Exception as e:
        logger.error(f"Error ejecutando consulta: {str(e)}")
        logger.error(f"Query: {query}")
        if params:
            logger.error(f"Params: {params}")
        return None


def get_table_structure(connection, table_name):
    """Obtiene la estructura de una tabla"""
    query = f"DESCRIBE {table_name}"
    results = execute_query(connection, query)

    if results:
        logger.info(f"Estructura de la tabla {table_name}:")
        for column in results:
            logger.info(
                f"  {column['Field']} - {column['Type']} - {column['Null']} - {column['Default']}"
            )
    else:
        logger.error(f"No se pudo obtener la estructura de la tabla {table_name}")

    return results


def check_null_values(connection, table_name):
    """Verifica campos NULL en una tabla"""
    # Obtener columnas de la tabla
    query = f"DESCRIBE {table_name}"
    columns = execute_query(connection, query)

    if not columns:
        logger.error(f"No se pudieron obtener las columnas de la tabla {table_name}")
        return None

    # Verificar valores NULL en cada columna
    logger.info(f"Verificando valores NULL en la tabla {table_name}:")
    null_counts = {}

    for column in columns:
        column_name = column["Field"]
        query = (
            f"SELECT COUNT(*) as count FROM {table_name} WHERE {column_name} IS NULL"
        )
        result = execute_query(connection, query)

        if result and result[0]["count"] > 0:
            null_counts[column_name] = result[0]["count"]
            logger.warning(
                f"  La columna {column_name} tiene {result[0]['count']} valores NULL"
            )

    # Verificar valores vacíos en columnas de texto
    logger.info(f"Verificando valores vacíos en la tabla {table_name}:")
    empty_counts = {}

    for column in columns:
        column_name = column["Field"]
        column_type = column["Type"].lower()

        if "char" in column_type or "text" in column_type:
            query = (
                f"SELECT COUNT(*) as count FROM {table_name} WHERE {column_name} = ''"
            )
            result = execute_query(connection, query)

            if result and result[0]["count"] > 0:
                empty_counts[column_name] = result[0]["count"]
                logger.warning(
                    f"  La columna {column_name} tiene {result[0]['count']} valores vacíos"
                )

    return {"null_counts": null_counts, "empty_counts": empty_counts}


def get_latest_records(connection, table_name, limit=5):
    """Obtiene los últimos registros de una tabla"""
    query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}"
    results = execute_query(connection, query)

    if results:
        logger.info(f"Últimos {len(results)} registros de la tabla {table_name}:")
        for i, record in enumerate(results, 1):
            # Convertir a formato legible
            record_dict = {}
            for k, v in record.items():
                if isinstance(v, (datetime, bytes)):
                    record_dict[k] = str(v)
                elif hasattr(v, "__str__"):
                    # Para manejar tipos como Decimal
                    record_dict[k] = str(v)
                else:
                    record_dict[k] = v

            record_str = json.dumps(record_dict, indent=2, ensure_ascii=False)
            logger.info(f"  Registro {i}: {record_str}")
    else:
        logger.error(
            f"No se pudieron obtener los últimos registros de la tabla {table_name}"
        )

    return results


def analyze_table_data(connection, table_name):
    """Analiza los datos de una tabla"""
    # Obtener estructura de la tabla
    structure = get_table_structure(connection, table_name)

    # Verificar valores NULL y vacíos
    null_empty_counts = check_null_values(connection, table_name)

    # Obtener últimos registros
    latest_records = get_latest_records(connection, table_name)

    # Obtener conteo total de registros
    query = f"SELECT COUNT(*) as count FROM {table_name}"
    count_result = execute_query(connection, query)
    total_records = count_result[0]["count"] if count_result else 0

    logger.info(f"Total de registros en la tabla {table_name}: {total_records}")

    # Verificar si hay registros duplicados
    if structure:
        # Buscar columnas que podrían ser únicas
        unique_candidates = []
        for column in structure:
            column_name = column["Field"]
            if column_name not in ["id", "created_at", "updated_at"]:
                unique_candidates.append(column_name)

        if unique_candidates:
            # Verificar duplicados en columnas candidatas
            for column_name in unique_candidates:
                query = f"""
                SELECT {column_name}, COUNT(*) as count
                FROM {table_name}
                GROUP BY {column_name}
                HAVING COUNT(*) > 1
                LIMIT 5
                """
                duplicates = execute_query(connection, query)

                if duplicates:
                    logger.warning(
                        f"Encontrados valores duplicados en la columna {column_name}:"
                    )
                    for dup in duplicates:
                        logger.warning(
                            f"  Valor: {dup[column_name]}, Repeticiones: {dup['count']}"
                        )

    return {
        "structure": structure,
        "null_empty_counts": null_empty_counts,
        "latest_records": latest_records,
        "total_records": total_records,
    }


def main():
    """Función principal"""
    logger.info("Iniciando verificación de tablas de la base de datos")

    # Obtener configuración de la base de datos
    config = get_db_config()

    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**config)
        logger.info(f"Conexión establecida con la base de datos {config['database']}")

        # Tablas a verificar
        tables = ["trading_signals", "market_sentiment", "market_news", "email_logs"]

        # Analizar cada tabla
        analysis_results = {}
        for table in tables:
            logger.info(f"\n{'='*50}\nAnalizando tabla {table}\n{'='*50}")
            analysis_results[table] = analyze_table_data(connection, table)

        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")

        # Mostrar resumen de problemas encontrados
        logger.info("\n\n===== RESUMEN DE PROBLEMAS ENCONTRADOS =====")
        for table, analysis in analysis_results.items():
            null_empty = analysis.get("null_empty_counts", {})
            null_counts = null_empty.get("null_counts", {})
            empty_counts = null_empty.get("empty_counts", {})

            if null_counts or empty_counts:
                logger.warning(f"\nProblemas en la tabla {table}:")

                if null_counts:
                    logger.warning(f"  Columnas con valores NULL:")
                    for column, count in null_counts.items():
                        logger.warning(f"    - {column}: {count} valores NULL")

                if empty_counts:
                    logger.warning(f"  Columnas con valores vacíos:")
                    for column, count in empty_counts.items():
                        logger.warning(f"    - {column}: {count} valores vacíos")
            else:
                logger.info(f"\nNo se encontraron problemas en la tabla {table}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")

    logger.info("Verificación completada")


if __name__ == "__main__":
    main()
