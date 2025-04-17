#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar los últimos registros de la tabla market_sentiment
"""

import mysql.connector
import json
from datetime import datetime

# Credenciales de la base de datos
DB_CONFIG = {
    "host": "190.8.178.74",
    "port": 3306,
    "user": "liceopan_root",
    "password": "@Soporte2020@",
    "database": "liceopan_enki_sincelejo"
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

def get_last_market_sentiment(limit=5):
    """Obtiene los últimos registros de la tabla market_sentiment"""
    connection = connect_to_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Consulta para obtener los últimos registros
        query = """
        SELECT id, date, overall, vix, sp500_trend, technical_indicators, volume, notes, created_at
        FROM market_sentiment 
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
    print("Obteniendo los últimos registros de market_sentiment...")
    sentiment_records = get_last_market_sentiment(5)
    
    if not sentiment_records:
        print("No se pudieron obtener registros")
        return
    
    print(f"Se obtuvieron {len(sentiment_records)} registros")
    
    # Análisis de registros
    print("\n=== ANÁLISIS DE MARKET_SENTIMENT ===")
    
    # Estadísticas generales
    total_records = len(sentiment_records)
    records_with_technical = sum(1 for record in sentiment_records if record.get('technical_indicators') and record['technical_indicators'] != 'N/A')
    records_with_vix = sum(1 for record in sentiment_records if record.get('vix') and record['vix'] != 'N/A')
    
    print(f"Total de registros: {total_records}")
    print(f"Registros con indicadores técnicos: {records_with_technical} ({records_with_technical/total_records*100:.1f}% si hay registros)")
    print(f"Registros con VIX: {records_with_vix} ({records_with_vix/total_records*100:.1f}% si hay registros)")
    
    # Mostrar registros
    for i, record in enumerate(sentiment_records):
        print(f"\nRegistro {i+1} (ID: {record['id']}):")
        print(f"Fecha: {record.get('date', 'N/A')}")
        print(f"Sentimiento general: {record.get('overall', 'N/A')}")
        print(f"VIX: {record.get('vix', 'N/A')}")
        print(f"Tendencia S&P500: {record.get('sp500_trend', 'N/A')}")
        
        # Mostrar indicadores técnicos (limitados a 100 caracteres para la salida)
        tech_indicators = record.get('technical_indicators', 'N/A')
        if len(tech_indicators) > 100:
            print(f"Indicadores técnicos: {tech_indicators[:100]}...")
        else:
            print(f"Indicadores técnicos: {tech_indicators}")
        
        print(f"Volumen: {record.get('volume', 'N/A')}")
        
        # Mostrar notas (limitadas a 100 caracteres para la salida)
        notes = record.get('notes', 'N/A')
        if len(notes) > 100:
            print(f"Notas: {notes[:100]}...")
        else:
            print(f"Notas: {notes}")
        
        # Detectar problemas
        problems = []
        if not record.get('technical_indicators') or record['technical_indicators'] == 'N/A':
            problems.append("Indicadores técnicos ausentes")
        if not record.get('vix') or record['vix'] == 'N/A':
            problems.append("VIX ausente")
        if not record.get('sp500_trend') or record['sp500_trend'] == 'N/A':
            problems.append("Tendencia S&P500 ausente")
        
        if problems:
            print("Problemas detectados:")
            for problem in problems:
                print(f"- {problem}")
    
    # Guardar resultados en un archivo JSON
    with open('market_sentiment_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(sentiment_records, f, ensure_ascii=False, indent=2)
    
    print("\nLos resultados completos se han guardado en 'market_sentiment_analysis.json'")

if __name__ == "__main__":
    main()
