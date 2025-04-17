#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar los últimos registros de la tabla trading_signals
"""

import mysql.connector
import json
from datetime import datetime
import re

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

def get_last_trading_signals(limit=3):
    """Obtiene los últimos registros de la tabla trading_signals"""
    connection = connect_to_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Consulta para obtener los últimos registros
        query = """
        SELECT id, symbol, direction, confidence_level, created_at, 
               technical_analysis, expert_analysis, latest_news, additional_news,
               is_high_confidence
        FROM trading_signals 
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

def check_intro_closing_phrases(text):
    """Verifica si el texto contiene frases introductorias o de cierre"""
    if not text:
        return False, False
    
    # Patrones para frases introductorias
    intro_patterns = [
        r"^(Aquí tienes|Claro|Por supuesto|A continuación)",
        r"^(Como|En este|El siguiente)",
        r"^(Te presento|Basado en)"
    ]
    
    # Patrones para frases de cierre
    closing_patterns = [
        r"(¿Deseas|¿Quieres|¿Necesitas).*\?$",
        r"(Espero que|Esto te ayudará).*$",
        r"(¿Hay algo más|Si tienes).*\?$"
    ]
    
    has_intro = any(re.search(pattern, text) for pattern in intro_patterns)
    has_closing = any(re.search(pattern, text) for pattern in closing_patterns)
    
    return has_intro, has_closing

def main():
    """Función principal"""
    print("Obteniendo los últimos registros de trading_signals...")
    signals = get_last_trading_signals(3)
    
    if not signals:
        print("No se pudieron obtener registros")
        return
    
    print(f"Se obtuvieron {len(signals)} registros")
    
    # Análisis de registros
    print("\n=== ANÁLISIS DE TRADING_SIGNALS ===")
    
    # Estadísticas generales
    total_records = len(signals)
    high_confidence = sum(1 for record in signals if record.get('is_high_confidence') == 1)
    
    print(f"Total de registros: {total_records}")
    print(f"Señales de alta confianza: {high_confidence} ({high_confidence/total_records*100:.1f}% si hay registros)")
    
    # Análisis de frases introductorias y de cierre
    fields_to_check = ['technical_analysis', 'expert_analysis', 'latest_news', 'additional_news']
    field_stats = {field: {'has_intro': 0, 'has_closing': 0} for field in fields_to_check}
    
    for record in signals:
        for field in fields_to_check:
            content = record.get(field, '')
            has_intro, has_closing = check_intro_closing_phrases(content)
            
            if has_intro:
                field_stats[field]['has_intro'] += 1
            
            if has_closing:
                field_stats[field]['has_closing'] += 1
    
    # Mostrar estadísticas de frases introductorias y de cierre
    print("\nEstadísticas de frases introductorias y de cierre:")
    for field, stats in field_stats.items():
        print(f"{field}:")
        print(f"  - Con frases introductorias: {stats['has_intro']} de {total_records} ({stats['has_intro']/total_records*100:.1f}% si hay registros)")
        print(f"  - Con frases de cierre: {stats['has_closing']} de {total_records} ({stats['has_closing']/total_records*100:.1f}% si hay registros)")
    
    # Mostrar ejemplos de los primeros registros
    for i, record in enumerate(signals):
        print(f"\nRegistro {i+1} (ID: {record['id']}):")
        print(f"Símbolo: {record.get('symbol', 'N/A')}")
        print(f"Dirección: {record.get('direction', 'N/A')}")
        print(f"Nivel de confianza: {record.get('confidence_level', 'N/A')}")
        print(f"Alta confianza: {'Sí' if record.get('is_high_confidence') == 1 else 'No'}")
        print(f"Fecha de creación: {record.get('created_at', 'N/A')}")
        
        # Mostrar primeras líneas de technical_analysis
        tech_analysis = record.get('technical_analysis', '')
        if tech_analysis:
            lines = tech_analysis.split('\n')[:3]
            print(f"Technical Analysis (primeras líneas):")
            for line in lines:
                print(f"  {line}")
            
            has_intro, has_closing = check_intro_closing_phrases(tech_analysis)
            if has_intro or has_closing:
                print("  Problemas detectados:")
                if has_intro:
                    print("  - Contiene frases introductorias")
                if has_closing:
                    print("  - Contiene frases de cierre")
        
        # Mostrar primeras líneas de expert_analysis
        expert_analysis = record.get('expert_analysis', '')
        if expert_analysis:
            lines = expert_analysis.split('\n')[:3]
            print(f"Expert Analysis (primeras líneas):")
            for line in lines:
                print(f"  {line}")
            
            has_intro, has_closing = check_intro_closing_phrases(expert_analysis)
            if has_intro or has_closing:
                print("  Problemas detectados:")
                if has_intro:
                    print("  - Contiene frases introductorias")
                if has_closing:
                    print("  - Contiene frases de cierre")
        
        # Mostrar latest_news y additional_news
        print(f"Latest News: {record.get('latest_news', 'N/A')}")
        print(f"Additional News: {record.get('additional_news', 'N/A')}")
    
    # Guardar resultados en un archivo JSON
    try:
        with open('trading_signals_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(signals, f, ensure_ascii=False, indent=2)
        
        print("\nLos resultados completos se han guardado en 'trading_signals_analysis.json'")
    except Exception as e:
        print(f"Error al guardar el archivo JSON: {str(e)}")

if __name__ == "__main__":
    main()
