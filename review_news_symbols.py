#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InversorIA Pro - Revisor de Símbolos de Noticias
------------------------------------------------
Este script permite revisar y corregir manualmente los símbolos de noticias
que han sido marcadas para revisión (symbol = 'REVIEW').
"""

import logging
import sys
import os
import pandas as pd
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/review_news_symbols_{datetime.now().strftime('%Y%m%d')}.log"),
    ],
)
logger = logging.getLogger(__name__)

# Asegurar que el directorio de logs exista
os.makedirs("logs", exist_ok=True)

# Importar utilidades de base de datos
try:
    from database_utils import DatabaseManager
    from company_data import COMPANY_INFO
except ImportError as e:
    logger.error(f"Error importando módulos necesarios: {str(e)}")
    sys.exit(1)


def get_news_for_review():
    """
    Obtiene las noticias marcadas para revisión manual (symbol = 'REVIEW')
    
    Returns:
        list: Lista de noticias que necesitan revisión
    """
    try:
        db = DatabaseManager()
        query = """
        SELECT id, title, summary, source, url, news_date
        FROM market_news
        WHERE symbol = 'REVIEW'
        ORDER BY news_date DESC
        """
        
        news = db.execute_query(query)
        logger.info(f"Se encontraron {len(news)} noticias para revisar")
        return news
    except Exception as e:
        logger.error(f"Error obteniendo noticias para revisar: {str(e)}")
        return []


def update_news_symbol(news_id, symbol):
    """
    Actualiza el símbolo de una noticia
    
    Args:
        news_id (int): ID de la noticia
        symbol (str): Nuevo símbolo a asignar
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        # Validar que el símbolo exista en COMPANY_INFO
        if symbol not in COMPANY_INFO and symbol not in ["SPY", "QQQ", "DIA", "IWM", "VIX"]:
            logger.warning(f"El símbolo {symbol} no existe en COMPANY_INFO")
            return False
            
        db = DatabaseManager()
        query = """
        UPDATE market_news
        SET symbol = %s
        WHERE id = %s
        """
        
        db.execute_query(query, [symbol, news_id], fetch=False)
        logger.info(f"Símbolo actualizado para noticia ID {news_id}: {symbol}")
        return True
    except Exception as e:
        logger.error(f"Error actualizando símbolo: {str(e)}")
        return False


def display_news_for_review(news):
    """
    Muestra las noticias para revisión en un formato legible
    
    Args:
        news (list): Lista de noticias para revisar
    """
    if not news:
        print("No hay noticias para revisar")
        return
        
    print("\n=== NOTICIAS PARA REVISIÓN ===\n")
    
    for i, item in enumerate(news, 1):
        print(f"{i}. ID: {item['id']}")
        print(f"   Título: {item['title']}")
        if item.get('summary'):
            print(f"   Resumen: {item['summary'][:150]}...")
        print(f"   Fuente: {item.get('source', 'N/A')}")
        if item.get('url'):
            print(f"   URL: {item['url']}")
        print(f"   Fecha: {item.get('news_date', 'N/A')}")
        print()


def get_available_symbols():
    """
    Obtiene una lista de símbolos disponibles para asignar
    
    Returns:
        list: Lista de símbolos disponibles
    """
    # Obtener símbolos de índices comunes
    common_indices = ["SPY", "QQQ", "DIA", "IWM", "VIX"]
    
    # Obtener símbolos de COMPANY_INFO
    company_symbols = list(COMPANY_INFO.keys())
    
    # Combinar y ordenar
    all_symbols = sorted(common_indices + company_symbols)
    
    return all_symbols


def interactive_review():
    """
    Inicia el proceso interactivo de revisión de símbolos
    """
    news = get_news_for_review()
    if not news:
        return
        
    display_news_for_review(news)
    
    # Obtener símbolos disponibles
    available_symbols = get_available_symbols()
    
    print("\nSímbolos comunes:")
    print(", ".join(["SPY", "QQQ", "DIA", "IWM", "VIX"]))
    
    while True:
        try:
            news_index = int(input("\nIngrese el número de la noticia a revisar (0 para salir): ")) - 1
            
            if news_index == -1:
                break
                
            if news_index < 0 or news_index >= len(news):
                print("Número de noticia inválido")
                continue
                
            news_item = news[news_index]
            print(f"\nRevisando noticia: {news_item['title']}")
            
            # Permitir búsqueda de símbolos
            search_term = input("Buscar símbolo (Enter para omitir): ").upper()
            if search_term:
                matching_symbols = [s for s in available_symbols if search_term in s]
                if matching_symbols:
                    print("Símbolos coincidentes:")
                    for i, symbol in enumerate(matching_symbols[:10], 1):
                        company_name = COMPANY_INFO.get(symbol, {}).get("name", "")
                        print(f"{i}. {symbol} - {company_name}")
                        
                    symbol_choice = input("Seleccione un número o ingrese un símbolo directamente: ")
                    try:
                        choice_index = int(symbol_choice) - 1
                        if 0 <= choice_index < len(matching_symbols):
                            symbol = matching_symbols[choice_index]
                        else:
                            symbol = symbol_choice.upper()
                    except ValueError:
                        symbol = symbol_choice.upper()
                else:
                    print("No se encontraron símbolos coincidentes")
                    symbol = input("Ingrese el símbolo a asignar: ").upper()
            else:
                symbol = input("Ingrese el símbolo a asignar: ").upper()
                
            if not symbol:
                print("No se ingresó un símbolo")
                continue
                
            # Confirmar la asignación
            company_name = COMPANY_INFO.get(symbol, {}).get("name", "")
            if company_name:
                confirm = input(f"¿Confirma asignar el símbolo {symbol} ({company_name}) a esta noticia? (s/n): ")
            else:
                confirm = input(f"¿Confirma asignar el símbolo {symbol} a esta noticia? (s/n): ")
                
            if confirm.lower() == "s":
                success = update_news_symbol(news_item["id"], symbol)
                if success:
                    print(f"Símbolo actualizado correctamente a {symbol}")
                    # Actualizar la lista de noticias
                    news = get_news_for_review()
                    if not news:
                        print("No hay más noticias para revisar")
                        break
                    display_news_for_review(news)
                else:
                    print("Error actualizando el símbolo")
            else:
                print("Operación cancelada")
                
        except ValueError:
            print("Por favor ingrese un número válido")
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario")
            break
        except Exception as e:
            logger.error(f"Error en el proceso de revisión: {str(e)}")
            print(f"Error: {str(e)}")


def batch_review():
    """
    Realiza una revisión por lotes de las noticias marcadas para revisión
    """
    news = get_news_for_review()
    if not news:
        return
        
    # Convertir a DataFrame para facilitar la manipulación
    df = pd.DataFrame(news)
    
    # Mostrar un resumen
    print(f"\nSe encontraron {len(df)} noticias para revisar")
    
    # Intentar asignar símbolos automáticamente basados en patrones comunes
    from database_utils import extract_symbol_from_content
    
    updated_count = 0
    for index, row in df.iterrows():
        title = row["title"]
        summary = row.get("summary", "")
        
        # Intentar extraer símbolo del contenido
        extracted_symbol = extract_symbol_from_content(title, summary)
        
        if extracted_symbol:
            # Actualizar en la base de datos
            success = update_news_symbol(row["id"], extracted_symbol)
            if success:
                updated_count += 1
                print(f"ID {row['id']}: Asignado símbolo {extracted_symbol} - {title[:50]}...")
    
    print(f"\nSe actualizaron automáticamente {updated_count} de {len(df)} noticias")
    
    # Si quedan noticias sin asignar, sugerir revisión manual
    remaining = len(df) - updated_count
    if remaining > 0:
        print(f"Quedan {remaining} noticias que requieren revisión manual")
        choice = input("¿Desea iniciar la revisión manual ahora? (s/n): ")
        if choice.lower() == "s":
            interactive_review()


def main():
    """Función principal"""
    print("\nInversorIA Pro - Revisor de Símbolos de Noticias")
    print("=" * 50)
    
    while True:
        print("\nOpciones:")
        print("1. Revisión interactiva")
        print("2. Revisión automática por lotes")
        print("0. Salir")
        
        choice = input("\nSeleccione una opción: ")
        
        if choice == "1":
            interactive_review()
        elif choice == "2":
            batch_review()
        elif choice == "0":
            break
        else:
            print("Opción inválida")


if __name__ == "__main__":
    main()
