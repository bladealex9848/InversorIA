#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar los resultados del escaneo de credenciales
"""

import json
import sys

def main():
    """Función principal"""
    try:
        # Cargar los resultados del escaneo
        with open('scan_results_history.json', 'r') as f:
            data = json.load(f)
        
        # Contar las credenciales
        current_code_count = len(data["current_code"])
        git_history_count = len(data["git_history"])
        
        print(f'Credenciales en el código actual: {current_code_count}')
        print(f'Credenciales en el historial de Git: {git_history_count}')
        
        # Filtrar las credenciales reales (no ejemplos)
        real_creds = [
            item for item in data['git_history'] 
            if item['pattern'] in ['SPECIFIC_DB', 'SPECIFIC_USER', 'SPECIFIC_PASSWORD', 'IP_ADDRESS'] 
            and not item['file'].startswith('scripts/hooks/')
        ]
        
        print(f'\nCredenciales reales encontradas en el historial:')
        print(f'Total: {len(real_creds)}')
        
        # Agrupar por tipo de credencial
        for pattern in ['SPECIFIC_DB', 'SPECIFIC_USER', 'SPECIFIC_PASSWORD', 'IP_ADDRESS']:
            pattern_items = [item for item in real_creds if item['pattern'] == pattern]
            if pattern_items:
                print(f'\n{pattern}: {len(pattern_items)} ocurrencias')
                for item in pattern_items[:3]:
                    print(f'  - {item["commit"]} - {item["file"]} - {item["value"]}')
                if len(pattern_items) > 3:
                    print(f'  - ... y {len(pattern_items) - 3} más')
        
        # Agrupar por archivo
        print('\nArchivos con más credenciales:')
        file_counts = {}
        for item in real_creds:
            file_counts[item['file']] = file_counts.get(item['file'], 0) + 1
        
        sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
        for file, count in sorted_files[:10]:
            print(f'  - {file}: {count} credenciales')
        
        # Agrupar por commit
        print('\nCommits con más credenciales:')
        commit_counts = {}
        for item in real_creds:
            commit_counts[item['commit']] = commit_counts.get(item['commit'], 0) + 1
        
        sorted_commits = sorted(commit_counts.items(), key=lambda x: x[1], reverse=True)
        for commit, count in sorted_commits[:5]:
            print(f'  - {commit}: {count} credenciales')
        
        return 0
    except Exception as e:
        print(f'Error: {str(e)}')
        return 1

if __name__ == "__main__":
    sys.exit(main())
