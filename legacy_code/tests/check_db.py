#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para examinar los últimos registros de la tabla trading_signals
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

def get_last_signals(limit=4):
    """Obtiene los últimos registros de la tabla trading_signals"""
    connection = connect_to_db()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Consulta para obtener los últimos registros
        query = """
        SELECT id, symbol, direction, confidence_level, created_at, 
               analysis, technical_analysis, expert_analysis, mtf_analysis,
               options_analysis, latest_news, additional_news,
               bullish_indicators, bearish_indicators
        FROM trading_signals 
        ORDER BY id DESC 
        LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        # Convertir datetime a string para poder serializar a JSON
        for row in results:
            if 'created_at' in row and isinstance(row['created_at'], datetime):
                row['created_at'] = row['created_at'].isoformat()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"Error al obtener los registros: {str(e)}")
        if connection:
            connection.close()
        return []

def analyze_text_fields(signals):
    """Analiza los campos de texto de las señales"""
    text_fields = [
        'analysis', 'technical_analysis', 'expert_analysis', 'mtf_analysis',
        'options_analysis', 'latest_news', 'additional_news',
        'bullish_indicators', 'bearish_indicators'
    ]
    
    analysis = {}
    
    for field in text_fields:
        field_stats = {
            'total_length': 0,
            'avg_length': 0,
            'min_length': float('inf'),
            'max_length': 0,
            'empty_count': 0,
            'has_intro_phrases': 0,
            'has_closing_phrases': 0
        }
        
        for signal in signals:
            content = signal.get(field, '')
            if not content:
                field_stats['empty_count'] += 1
                continue
                
            length = len(content)
            field_stats['total_length'] += length
            field_stats['min_length'] = min(field_stats['min_length'], length)
            field_stats['max_length'] = max(field_stats['max_length'], length)
            
            # Verificar frases introductorias y de cierre
            if "Claro, aquí tienes" in content or "A continuación" in content:
                field_stats['has_intro_phrases'] += 1
                
            if "¿Deseas" in content or "¿Necesitas" in content or "¿Quieres" in content:
                field_stats['has_closing_phrases'] += 1
        
        if len(signals) - field_stats['empty_count'] > 0:
            field_stats['avg_length'] = field_stats['total_length'] / (len(signals) - field_stats['empty_count'])
        
        # Si min_length sigue siendo infinito, establecerlo a 0
        if field_stats['min_length'] == float('inf'):
            field_stats['min_length'] = 0
            
        analysis[field] = field_stats
    
    return analysis

def print_signal_examples(signals):
    """Imprime ejemplos de los campos de texto de las señales"""
    if not signals:
        print("No hay señales para analizar")
        return
    
    # Imprimir información básica de las señales
    print("\n=== INFORMACIÓN BÁSICA DE LAS SEÑALES ===")
    for signal in signals:
        print(f"ID: {signal['id']}, Símbolo: {signal['symbol']}, Dirección: {signal['direction']}, Confianza: {signal['confidence_level']}, Fecha: {signal['created_at']}")
    
    # Imprimir ejemplos de campos de texto
    text_fields = [
        'expert_analysis', 'technical_analysis', 'analysis', 'latest_news'
    ]
    
    for field in text_fields:
        print(f"\n=== EJEMPLOS DE {field.upper()} ===")
        for i, signal in enumerate(signals):
            content = signal.get(field, '')
            if content:
                print(f"\nSeñal {i+1} ({signal['symbol']}):")
                # Imprimir solo los primeros 500 caracteres para no saturar la salida
                print(f"{content[:500]}..." if len(content) > 500 else content)

def main():
    """Función principal"""
    print("Obteniendo los últimos registros de trading_signals...")
    signals = get_last_signals(4)
    
    if not signals:
        print("No se pudieron obtener registros")
        return
    
    print(f"Se obtuvieron {len(signals)} registros")
    
    # Analizar campos de texto
    analysis = analyze_text_fields(signals)
    
    # Imprimir análisis
    print("\n=== ANÁLISIS DE CAMPOS DE TEXTO ===")
    for field, stats in analysis.items():
        print(f"\nCampo: {field}")
        print(f"  Registros vacíos: {stats['empty_count']} de {len(signals)}")
        if stats['empty_count'] < len(signals):
            print(f"  Longitud promedio: {stats['avg_length']:.2f} caracteres")
            print(f"  Longitud mínima: {stats['min_length']} caracteres")
            print(f"  Longitud máxima: {stats['max_length']} caracteres")
            print(f"  Contiene frases introductorias: {stats['has_intro_phrases']} de {len(signals) - stats['empty_count']}")
            print(f"  Contiene frases de cierre: {stats['has_closing_phrases']} de {len(signals) - stats['empty_count']}")
    
    # Imprimir ejemplos
    print_signal_examples(signals)
    
    # Guardar resultados en un archivo JSON
    with open('signal_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(signals, f, ensure_ascii=False, indent=2)
    
    print("\nLos resultados completos se han guardado en 'signal_analysis.json'")

if __name__ == "__main__":
    main()
