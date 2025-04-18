#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para consultar los últimos 10 registros de las tablas 'market_news',
'market_sentiment' y 'trading_signals' en la base de datos.

Este script lee las credenciales de la base de datos desde el archivo secrets.toml
para garantizar la seguridad de las credenciales.
"""

import mysql.connector
import os
import sys
import toml
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def load_db_config() -> Dict[str, Any]:
    """
    Carga la configuración de la base de datos desde secrets.toml

    Returns:
        Dict[str, Any]: Configuración de la base de datos
    """
    try:
        # Ruta al archivo secrets.toml
        secrets_path = os.path.join(".streamlit", "secrets.toml")

        # Verificar si el archivo existe
        if not os.path.exists(secrets_path):
            logger.error(f"El archivo {secrets_path} no existe")
            # Buscar en otras ubicaciones comunes
            alt_paths = [
                "secrets.toml",
                os.path.join("..", ".streamlit", "secrets.toml"),
                os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml"),
            ]

            for path in alt_paths:
                if os.path.exists(path):
                    secrets_path = path
                    logger.info(f"Usando archivo de secretos alternativo: {path}")
                    break
            else:
                raise FileNotFoundError(f"No se encontró el archivo secrets.toml")

        # Leer el archivo secrets.toml
        secrets = toml.load(secrets_path)

        # Intentar obtener configuración con diferentes nombres de variables
        if "mysql" in secrets:
            logger.info(
                "Usando configuración de base de datos desde secrets.toml (formato mysql)"
            )
            return {
                "host": secrets["mysql"].get("host", "localhost"),
                "port": int(secrets["mysql"].get("port", 3306)),
                "user": secrets["mysql"].get("user", "root"),
                "password": secrets["mysql"].get("password", ""),
                "database": secrets["mysql"].get("database", "inversoria"),
            }
        elif "db_host" in secrets:
            logger.info(
                "Usando configuración de base de datos desde secrets.toml (formato db_)"
            )
            return {
                "host": secrets.get("db_host", "localhost"),
                "port": int(secrets.get("db_port", 3306)),
                "user": secrets.get("db_user", "root"),
                "password": secrets.get("db_password", ""),
                "database": secrets.get("db_name", "inversoria"),
            }
        else:
            # No se encontró configuración válida
            logger.error("No se encontró configuración válida en secrets.toml")
            logger.error(
                "Por favor, asegúrate de que el archivo secrets.toml contiene las credenciales de la base de datos"
            )
            logger.error(
                "El archivo debe estar en la carpeta .streamlit o en la raíz del proyecto"
            )
            raise ValueError(
                "Configuración de base de datos no encontrada en secrets.toml"
            )
    except Exception as e:
        logger.error(f"Error cargando configuración: {str(e)}")
        logger.error("No se pudo cargar la configuración de la base de datos")
        logger.error(
            "Por favor, verifica que el archivo secrets.toml existe y contiene las credenciales correctas"
        )
        raise ValueError("Error al cargar la configuración de la base de datos")


def connect_to_db(config: Dict[str, Any]) -> Optional[mysql.connector.MySQLConnection]:
    """
    Conecta a la base de datos usando la configuración proporcionada

    Args:
        config (Dict[str, Any]): Configuración de la base de datos

    Returns:
        Optional[mysql.connector.MySQLConnection]: Conexión a la base de datos o None si hay error
    """
    try:
        connection = mysql.connector.connect(**config)
        logger.info(f"Conexión establecida con la base de datos {config['database']}")
        return connection
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        return None


def get_table_structure(
    connection: mysql.connector.MySQLConnection, table: str
) -> List[Dict[str, Any]]:
    """
    Obtiene la estructura de una tabla

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        table (str): Nombre de la tabla

    Returns:
        List[Dict[str, Any]]: Lista de columnas con sus propiedades
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Ejecutar consulta para obtener la estructura de la tabla
        query = f"DESCRIBE {table}"
        cursor.execute(query)

        # Obtener resultados
        results = cursor.fetchall()

        # Cerrar cursor
        cursor.close()

        return results
    except Exception as e:
        logger.error(f"Error obteniendo estructura de la tabla {table}: {str(e)}")
        return []


def get_latest_records(
    connection: mysql.connector.MySQLConnection, table: str, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Obtiene los últimos registros de una tabla

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        table (str): Nombre de la tabla
        limit (int, optional): Número de registros a obtener. Defaults to 10.

    Returns:
        List[Dict[str, Any]]: Lista de registros
    """
    try:
        cursor = connection.cursor(dictionary=True)

        # Determinar la columna de ordenamiento según la tabla
        order_column = "created_at"

        # Ejecutar consulta
        query = f"SELECT * FROM {table} ORDER BY {order_column} DESC LIMIT {limit}"
        cursor.execute(query)

        # Obtener resultados
        results = cursor.fetchall()

        # Cerrar cursor
        cursor.close()

        return results
    except Exception as e:
        logger.error(f"Error obteniendo registros de {table}: {str(e)}")
        return []


def format_record(record: Dict[str, Any], table: str) -> str:
    """
    Formatea un registro para mostrarlo en la consola

    Args:
        record (Dict[str, Any]): Registro a formatear
        table (str): Nombre de la tabla

    Returns:
        str: Registro formateado
    """
    if table == "market_news":
        # Formatear registro de noticias
        summary = record.get("summary", "")
        if summary and len(summary) > 150:
            summary = summary[:147] + "..."

        return (
            f"ID: {record.get('id')}\n"
            f"Símbolo: {record.get('symbol', 'N/A')}\n"
            f"Título: {record.get('title', 'N/A')}\n"
            f"Resumen: {summary or '[VACÍO]'}\n"
            f"Fuente: {record.get('source', 'N/A')}\n"
            f"Impacto: {record.get('impact', 'N/A')}\n"
            f"URL: {record.get('url', 'N/A')}\n"
            f"Fecha: {record.get('news_date')}\n"
            f"Creado: {record.get('created_at')}"
        )
    elif table == "market_sentiment":
        # Formatear registro de sentimiento
        analysis = record.get("analysis", "")
        if analysis and len(analysis) > 150:
            analysis = analysis[:147] + "..."

        tech_indicators = record.get("technical_indicators", "")
        if tech_indicators and len(tech_indicators) > 150:
            tech_indicators = tech_indicators[:147] + "..."

        notes = record.get("notes", "")
        if notes and len(notes) > 100:
            notes = notes[:97] + "..."

        return (
            f"ID: {record.get('id')}\n"
            f"Fecha: {record.get('date')}\n"
            f"Sentimiento: {record.get('overall', 'N/A')}\n"
            f"VIX: {record.get('vix', 'N/A')}\n"
            f"Tendencia S&P500: {record.get('sp500_trend', 'N/A')}\n"
            f"Análisis: {analysis or '[VACÍO]'}\n"
            f"Indicadores técnicos: {tech_indicators or '[VACÍO]'}\n"
            f"Volumen: {record.get('volume', 'N/A')}\n"
            f"Notas: {notes or '[VACÍO]'}\n"
            f"Creado: {record.get('created_at')}"
        )
    elif table == "trading_signals":
        # Formatear registro de señales
        analysis = record.get("analysis", "")
        if analysis and len(analysis) > 150:
            analysis = analysis[:147] + "..."

        tech_analysis = record.get("technical_analysis", "")
        if tech_analysis and len(tech_analysis) > 150:
            tech_analysis = tech_analysis[:147] + "..."

        expert_analysis = record.get("expert_analysis", "")
        if expert_analysis and len(expert_analysis) > 150:
            expert_analysis = expert_analysis[:147] + "..."

        # Formatear precio y niveles con 2 decimales
        price = record.get("price")
        if price is not None:
            try:
                price = f"${float(price):.2f}"
            except (ValueError, TypeError):
                price = str(price)

        support = record.get("support_level")
        if support is not None:
            try:
                support = f"${float(support):.2f}"
            except (ValueError, TypeError):
                support = str(support)

        resistance = record.get("resistance_level")
        if resistance is not None:
            try:
                resistance = f"${float(resistance):.2f}"
            except (ValueError, TypeError):
                resistance = str(resistance)

        return (
            f"ID: {record.get('id')}\n"
            f"Símbolo: {record.get('symbol', 'N/A')}\n"
            f"Precio: {price}\n"
            f"Dirección: {record.get('direction', 'N/A')}\n"
            f"Confianza: {record.get('confidence_level', 'N/A')}\n"
            f"Estrategia: {record.get('strategy', 'N/A')}\n"
            f"Categoría: {record.get('category', 'N/A')}\n"
            f"Timeframe: {record.get('timeframe', 'N/A')}\n"
            f"Soporte: {support or 'N/A'}\n"
            f"Resistencia: {resistance or 'N/A'}\n"
            f"RSI: {record.get('rsi', 'N/A')}\n"
            f"Tendencia: {record.get('trend', 'N/A')}\n"
            f"Análisis: {analysis or '[VACÍO]'}\n"
            f"Análisis técnico: {tech_analysis or '[VACÍO]'}\n"
            f"Análisis experto: {expert_analysis or '[VACÍO]'}\n"
            f"Creado: {record.get('created_at')}"
        )
    else:
        # Formatear registro genérico
        return str(record)


def analyze_table_data_quality(
    connection: mysql.connector.MySQLConnection, table: str
) -> Dict[str, Any]:
    """
    Analiza la calidad de los datos en una tabla

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos
        table (str): Nombre de la tabla

    Returns:
        Dict[str, Any]: Estadísticas de calidad de datos
    """
    try:
        # Obtener la estructura de la tabla
        structure = get_table_structure(connection, table)

        # Inicializar estadísticas
        stats = {
            "total_records": 0,
            "recent_records": 0,
            "empty_fields": {},
            "null_fields": {},
            "field_stats": {},
        }

        # Contar registros totales
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        stats["total_records"] = cursor.fetchone()[0]
        cursor.close()

        # Contar registros recientes (últimos 7 días)
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT COUNT(*) FROM {table} WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
        )
        stats["recent_records"] = cursor.fetchone()[0]
        cursor.close()

        # Analizar cada campo
        for field in structure:
            field_name = field.get("Field")
            field_type = field.get("Type")

            # Contar valores nulos
            cursor = connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {field_name} IS NULL")
            null_count = cursor.fetchone()[0]
            cursor.close()

            if null_count > 0:
                stats["null_fields"][field_name] = null_count

            # Contar valores vacíos (para campos de texto)
            if "char" in field_type.lower() or "text" in field_type.lower():
                cursor = connection.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {field_name} = ''")
                empty_count = cursor.fetchone()[0]
                cursor.close()

                if empty_count > 0:
                    stats["empty_fields"][field_name] = empty_count

            # Estadísticas específicas según el tipo de campo
            if "enum" in field_type.lower():
                # Obtener distribución de valores para campos enum
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    f"SELECT {field_name}, COUNT(*) as count FROM {table} GROUP BY {field_name}"
                )
                value_distribution = cursor.fetchall()
                cursor.close()

                stats["field_stats"][field_name] = {
                    "type": "enum",
                    "distribution": value_distribution,
                }
            elif "date" in field_type.lower() or "time" in field_type.lower():
                # Obtener rango de fechas
                cursor = connection.cursor()
                cursor.execute(
                    f"SELECT MIN({field_name}), MAX({field_name}) FROM {table} WHERE {field_name} IS NOT NULL"
                )
                date_range = cursor.fetchone()
                cursor.close()

                stats["field_stats"][field_name] = {
                    "type": "date",
                    "min": date_range[0],
                    "max": date_range[1],
                }
            elif (
                "int" in field_type.lower()
                or "decimal" in field_type.lower()
                or "float" in field_type.lower()
            ):
                # Obtener estadísticas numéricas
                cursor = connection.cursor()
                cursor.execute(
                    f"SELECT MIN({field_name}), MAX({field_name}), AVG({field_name}) FROM {table} WHERE {field_name} IS NOT NULL"
                )
                num_stats = cursor.fetchone()
                cursor.close()

                stats["field_stats"][field_name] = {
                    "type": "numeric",
                    "min": num_stats[0],
                    "max": num_stats[1],
                    "avg": num_stats[2],
                }

        return stats
    except Exception as e:
        logger.error(f"Error analizando calidad de datos en {table}: {str(e)}")
        return {"error": str(e)}


def get_empty_critical_fields(
    connection: mysql.connector.MySQLConnection,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Obtiene registros con campos críticos vacíos

    Args:
        connection (mysql.connector.MySQLConnection): Conexión a la base de datos

    Returns:
        Dict[str, List[Dict[str, Any]]]: Registros con campos críticos vacíos por tabla
    """
    try:
        results = {}

        # Campos críticos por tabla
        critical_fields = {
            "market_news": [
                {
                    "field": "summary",
                    "query": "SELECT id, symbol, title, source, created_at FROM market_news WHERE summary IS NULL OR summary = '' LIMIT 10",
                },
                {
                    "field": "title",
                    "query": "SELECT id, symbol, summary, source, created_at FROM market_news WHERE title IS NULL OR title = '' LIMIT 10",
                },
                {
                    "field": "symbol",
                    "query": "SELECT id, title, summary, source, created_at FROM market_news WHERE symbol IS NULL OR symbol = '' LIMIT 10",
                },
            ],
            "market_sentiment": [
                {
                    "field": "analysis",
                    "query": "SELECT id, date, overall, vix, sp500_trend, created_at FROM market_sentiment WHERE analysis IS NULL OR analysis = '' LIMIT 10",
                },
                {
                    "field": "overall",
                    "query": "SELECT id, date, analysis, vix, sp500_trend, created_at FROM market_sentiment WHERE overall IS NULL LIMIT 10",
                },
                {
                    "field": "technical_indicators",
                    "query": "SELECT id, date, overall, analysis, created_at FROM market_sentiment WHERE technical_indicators IS NULL OR technical_indicators = '' LIMIT 10",
                },
            ],
            "trading_signals": [
                {
                    "field": "analysis",
                    "query": "SELECT id, symbol, direction, confidence_level, price, created_at FROM trading_signals WHERE analysis IS NULL OR analysis = '' LIMIT 10",
                },
                {
                    "field": "symbol",
                    "query": "SELECT id, direction, confidence_level, price, created_at FROM trading_signals WHERE symbol IS NULL OR symbol = '' LIMIT 10",
                },
                {
                    "field": "direction",
                    "query": "SELECT id, symbol, confidence_level, price, created_at FROM trading_signals WHERE direction IS NULL LIMIT 10",
                },
                {
                    "field": "price",
                    "query": "SELECT id, symbol, direction, confidence_level, created_at FROM trading_signals WHERE price IS NULL LIMIT 10",
                },
            ],
        }

        # Ejecutar consultas para cada campo crítico
        for table, fields in critical_fields.items():
            results[table] = []

            for field_info in fields:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(field_info["query"])
                records = cursor.fetchall()
                cursor.close()

                if records:
                    results[table].append(
                        {
                            "field": field_info["field"],
                            "count": len(records),
                            "records": records,
                        }
                    )

        return results
    except Exception as e:
        logger.error(f"Error obteniendo campos críticos vacíos: {str(e)}")
        return {}


def main():
    """Función principal"""
    try:
        # Cargar configuración
        db_config = load_db_config()

        # Conectar a la base de datos
        connection = connect_to_db(db_config)
        if not connection:
            logger.error("No se pudo conectar a la base de datos")
            return

        # Tablas a consultar
        tables = ["market_news", "market_sentiment", "trading_signals"]

        # Mostrar estructura de las tablas
        print("\n" + "=" * 80)
        print("ESTRUCTURA DE LAS TABLAS")
        print("=" * 80)

        for table in tables:
            structure = get_table_structure(connection, table)
            print(f"\nTabla: {table}")
            print("-" * 40)
            for field in structure:
                print(
                    f"Campo: {field.get('Field', 'N/A'):<20} Tipo: {field.get('Type', 'N/A'):<30} Nulo: {field.get('Null', 'N/A'):<5} Clave: {field.get('Key', 'N/A'):<5} Default: {field.get('Default', 'N/A')}"
                )

        # Resumen de registros y análisis de calidad
        print("\n" + "=" * 80)
        print("RESUMEN DE REGISTROS Y CALIDAD DE DATOS")
        print("=" * 80)

        for table in tables:
            stats = analyze_table_data_quality(connection, table)

            print(f"\nTabla {table}:")
            print(f"  - Registros totales: {stats['total_records']}")
            print(f"  - Registros recientes (7 días): {stats['recent_records']}")

            if stats["null_fields"]:
                print("  - Campos con valores NULL:")
                for field, count in stats["null_fields"].items():
                    print(
                        f"    * {field}: {count} registros ({(count/stats['total_records'])*100:.1f}%)"
                    )

            if stats["empty_fields"]:
                print("  - Campos con valores vacíos:")
                for field, count in stats["empty_fields"].items():
                    print(
                        f"    * {field}: {count} registros ({(count/stats['total_records'])*100:.1f}%)"
                    )

        # Consultar cada tabla
        for table in tables:
            print(f"\n{'=' * 30} ÚLTIMOS 10 REGISTROS DE {table.upper()} {'=' * 30}")
            records = get_latest_records(connection, table)

            if not records:
                print(f"No se encontraron registros en la tabla {table}")
                continue

            for i, record in enumerate(records, 1):
                print(f"\n--- Registro {i} ---")
                print(format_record(record, table))
                print("-" * 80)

        # Verificar registros con campos críticos vacíos
        print("\n" + "=" * 80)
        print("REGISTROS CON CAMPOS CRÍTICOS VACÍOS")
        print("=" * 80)

        empty_critical = get_empty_critical_fields(connection)

        for table, field_results in empty_critical.items():
            if not field_results:
                print(f"\nTabla {table}: No se encontraron campos críticos vacíos")
                continue

            print(f"\nTabla {table}:")
            for field_info in field_results:
                print(
                    f"  - Campo '{field_info['field']}': {field_info['count']} registros con valores vacíos"
                )

                # Mostrar algunos ejemplos
                for i, record in enumerate(field_info["records"][:5], 1):
                    id_value = record.get("id", "N/A")
                    created_at = record.get("created_at", "N/A")

                    # Mostrar campos relevantes según la tabla
                    if table == "market_news":
                        print(
                            f"    * Registro {i}: ID={id_value}, Símbolo={record.get('symbol', 'N/A')}, Título={record.get('title', 'N/A')[:30]}..., Creado={created_at}"
                        )
                    elif table == "market_sentiment":
                        print(
                            f"    * Registro {i}: ID={id_value}, Fecha={record.get('date', 'N/A')}, Sentimiento={record.get('overall', 'N/A')}, Creado={created_at}"
                        )
                    elif table == "trading_signals":
                        print(
                            f"    * Registro {i}: ID={id_value}, Símbolo={record.get('symbol', 'N/A')}, Dirección={record.get('direction', 'N/A')}, Confianza={record.get('confidence_level', 'N/A')}, Creado={created_at}"
                        )

        print("=" * 80)

        # Cerrar conexión
        connection.close()
        logger.info("Conexión cerrada")

    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")


if __name__ == "__main__":
    main()
