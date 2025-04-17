#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar los últimos registros de la tabla market_news
"""

import mysql.connector
import json
from datetime import datetime

# Credenciales de la base de datos
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "db_user",
    "password": "db_password",
    "database": "inversoria_db"
}

def connect_to_db():
    """Conecta a la base de datos"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("Conexión establecida con éxito")
        return connection
    except Exception as e:
        print(f"Error al conectar a la base de datos: {str(e)}")
        return None

def get_last_market_news(limit=5):
    """Obtiene los últimos registros de la tabla market_news"""
    connection = connect_to_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Consulta para obtener los últimos registros
        query = """
        SELECT id, title, summary, source, url, news_date, impact, created_at
        FROM market_news 
        ORDER BY id DESC 
        LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        # Convertir datetime a string para poder serializar a JSON
        for row in results:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"Error al obtener los registros: {str(e)}")
        if connection:
            connection.close()
        return []

def main():
    """Función principal"""
    print("Obteniendo los últimos registros de market_news...")
    news_records = get_last_market_news(5)
    
    if not news_records:
        print("No se pudieron obtener registros")
        return
    
    print(f"Se obtuvieron {len(news_records)} registros")
    
    # Análisis de registros
    print("\n=== ANÁLISIS DE MARKET_NEWS ===")
    
    # Estadísticas generales
    total_records = len(news_records)
    records_with_url = sum(1 for record in news_records if record.get('url') and record['url'].startswith('http'))
    records_with_source = sum(1 for record in news_records if record.get('source') and record['source'] != 'InversorIA Analytics')
    
    print(f"Total de registros: {total_records}")
    print(f"Registros con URL válida: {records_with_url} ({records_with_url/total_records*100:.1f}% si hay registros)")
    print(f"Registros con fuente específica: {records_with_source} ({records_with_source/total_records*100:.1f}% si hay registros)")
    
    # Mostrar registros
    for i, record in enumerate(news_records):
        print(f"\nRegistro {i+1} (ID: {record['id']}):")
        print(f"Título: {record.get('title', 'N/A')}")
        print(f"Resumen: {record.get('summary', 'N/A')[:100]}..." if len(record.get('summary', '')) > 100 else f"Resumen: {record.get('summary', 'N/A')}")
        print(f"Fuente: {record.get('source', 'N/A')}")
        print(f"URL: {record.get('url', 'N/A')}")
        print(f"Fecha: {record.get('news_date', 'N/A')}")
        print(f"Impacto: {record.get('impact', 'N/A')}")
        
        # Detectar problemas
        problems = []
        if not record.get('url') or not record['url'].startswith('http'):
            problems.append("URL no válida o ausente")
        if not record.get('source') or record['source'] == 'InversorIA Analytics':
            problems.append("Fuente genérica o ausente")
        if record.get('title') and record.get('title').startswith(("Análisis técnico", "El activo")):
            problems.append("Título parece generado automáticamente, no una noticia real")
        
        if problems:
            print("Problemas detectados:")
            for problem in problems:
                print(f"- {problem}")
    
    # Guardar resultados en un archivo JSON
    with open('market_news_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(news_records, f, ensure_ascii=False, indent=2)
    
    print("\nLos resultados completos se han guardado en 'market_news_analysis.json'")

if __name__ == "__main__":
    main()
