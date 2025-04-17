#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar los últimos registros de las tablas market_news, market_sentiment y trading_signals
"""

import mysql.connector
import json
from datetime import datetime
import pandas as pd
import re

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

def get_last_records(table_name, limit=5):
    """Obtiene los últimos registros de una tabla"""
    connection = connect_to_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Consulta para obtener los últimos registros
        query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT %s"
        
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
        print(f"Error al obtener los registros de {table_name}: {str(e)}")
        if connection:
            connection.close()
        return []

def analyze_market_news(records):
    """Analiza los registros de la tabla market_news"""
    if not records:
        print("No hay registros de market_news para analizar")
        return
    
    print("\n=== ANÁLISIS DE MARKET_NEWS ===")
    
    # Estadísticas generales
    total_records = len(records)
    records_with_url = sum(1 for record in records if record.get('url') and record['url'].startswith('http'))
    records_with_source = sum(1 for record in records if record.get('source') and record['source'] != 'InversorIA Analytics')
    
    print(f"Total de registros: {total_records}")
    print(f"Registros con URL válida: {records_with_url} ({records_with_url/total_records*100:.1f}%)")
    print(f"Registros con fuente específica: {records_with_source} ({records_with_source/total_records*100:.1f}%)")
    
    # Análisis de contenido
    for i, record in enumerate(records):
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

def analyze_market_sentiment(records):
    """Analiza los registros de la tabla market_sentiment"""
    if not records:
        print("No hay registros de market_sentiment para analizar")
        return
    
    print("\n=== ANÁLISIS DE MARKET_SENTIMENT ===")
    
    # Estadísticas generales
    total_records = len(records)
    records_with_technical = sum(1 for record in records if record.get('technical_indicators') and record['technical_indicators'] != 'N/A')
    records_with_vix = sum(1 for record in records if record.get('vix') and record['vix'] != 'N/A')
    
    print(f"Total de registros: {total_records}")
    print(f"Registros con indicadores técnicos: {records_with_technical} ({records_with_technical/total_records*100:.1f}%)")
    print(f"Registros con VIX: {records_with_vix} ({records_with_vix/total_records*100:.1f}%)")
    
    # Análisis de contenido
    for i, record in enumerate(records):
        print(f"\nRegistro {i+1} (ID: {record['id']}):")
        print(f"Fecha: {record.get('date', 'N/A')}")
        print(f"Sentimiento general: {record.get('overall', 'N/A')}")
        print(f"VIX: {record.get('vix', 'N/A')}")
        print(f"Tendencia S&P500: {record.get('sp500_trend', 'N/A')}")
        print(f"Indicadores técnicos: {record.get('technical_indicators', 'N/A')[:100]}..." if len(record.get('technical_indicators', '')) > 100 else f"Indicadores técnicos: {record.get('technical_indicators', 'N/A')}")
        print(f"Volumen: {record.get('volume', 'N/A')}")
        print(f"Notas: {record.get('notes', 'N/A')[:100]}..." if len(record.get('notes', '')) > 100 else f"Notas: {record.get('notes', 'N/A')}")
        
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

def analyze_trading_signals(records):
    """Analiza los registros de la tabla trading_signals"""
    if not records:
        print("No hay registros de trading_signals para analizar")
        return
    
    print("\n=== ANÁLISIS DE TRADING_SIGNALS ===")
    
    # Estadísticas generales
    total_records = len(records)
    high_confidence = sum(1 for record in records if record.get('is_high_confidence') == 1)
    
    print(f"Total de registros: {total_records}")
    print(f"Señales de alta confianza: {high_confidence} ({high_confidence/total_records*100:.1f}%)")
    
    # Análisis de campos de texto
    text_fields = [
        'analysis', 'technical_analysis', 'expert_analysis', 'mtf_analysis',
        'options_analysis', 'latest_news', 'additional_news'
    ]
    
    field_stats = {field: {'has_intro': 0, 'has_closing': 0} for field in text_fields}
    
    for record in records:
        for field in text_fields:
            content = record.get(field, '')
            if not content:
                continue
                
            # Verificar frases introductorias
            intro_patterns = [
                r"^(Aquí tienes|Claro|Por supuesto|A continuación)",
                r"^(Como|En este|El siguiente)",
                r"^(Te presento|Basado en)"
            ]
            
            for pattern in intro_patterns:
                if re.search(pattern, content):
                    field_stats[field]['has_intro'] += 1
                    break
            
            # Verificar frases de cierre
            closing_patterns = [
                r"(¿Deseas|¿Quieres|¿Necesitas).*\?$",
                r"(Espero que|Esto te ayudará).*$",
                r"(¿Hay algo más|Si tienes).*\?$"
            ]
            
            for pattern in closing_patterns:
                if re.search(pattern, content):
                    field_stats[field]['has_closing'] += 1
                    break
    
    # Mostrar estadísticas de frases introductorias y de cierre
    print("\nEstadísticas de frases introductorias y de cierre:")
    for field, stats in field_stats.items():
        print(f"{field}:")
        print(f"  - Con frases introductorias: {stats['has_intro']} de {total_records} ({stats['has_intro']/total_records*100:.1f}%)")
        print(f"  - Con frases de cierre: {stats['has_closing']} de {total_records} ({stats['has_closing']/total_records*100:.1f}%)")
    
    # Análisis de ejemplos
    print("\nEjemplos de campos de texto:")
    for field in ['expert_analysis', 'technical_analysis']:
        print(f"\n{field.upper()}:")
        for i, record in enumerate(records[:2]):  # Mostrar solo 2 ejemplos
            content = record.get(field, '')
            if content:
                print(f"\nRegistro {i+1} (ID: {record['id']}, Símbolo: {record.get('symbol', 'N/A')}):")
                # Mostrar primeras 10 líneas
                lines = content.split('\n')[:10]
                print('\n'.join(lines))
                if len(lines) < len(content.split('\n')):
                    print("...")

def main():
    """Función principal"""
    # Obtener los últimos registros de cada tabla
    market_news_records = get_last_records('market_news')
    market_sentiment_records = get_last_records('market_sentiment')
    trading_signals_records = get_last_records('trading_signals')
    
    # Analizar cada tabla
    analyze_market_news(market_news_records)
    analyze_market_sentiment(market_sentiment_records)
    analyze_trading_signals(trading_signals_records)
    
    # Guardar resultados en archivos JSON para análisis posterior
    with open('market_news_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(market_news_records, f, ensure_ascii=False, indent=2)
    
    with open('market_sentiment_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(market_sentiment_records, f, ensure_ascii=False, indent=2)
    
    with open('trading_signals_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(trading_signals_records, f, ensure_ascii=False, indent=2)
    
    print("\nLos resultados completos se han guardado en archivos JSON para análisis posterior.")

if __name__ == "__main__":
    main()
