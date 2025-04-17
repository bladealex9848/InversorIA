#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de resúmenes para InversorIA Pro
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional, Union

# Configurar logging
logger = logging.getLogger(__name__)

class SummaryManager:
    """
    Clase para gestionar resúmenes de procesamiento y resultados
    Proporciona una forma consistente de mostrar información de resultados
    """
    
    def __init__(self):
        """Inicializa el gestor de resúmenes"""
        # Inicializar contenedores para resúmenes
        if "summary_containers" not in st.session_state:
            st.session_state.summary_containers = {}
    
    def create_summary_container(self, key: str) -> None:
        """
        Crea un nuevo contenedor para resúmenes
        
        Args:
            key (str): Identificador único para el contenedor
        """
        # Limpiar contenedor anterior con la misma clave
        self.clear_summary(key)
        
        # Crear nuevo contenedor
        st.session_state.summary_containers[key] = st.container()
    
    def show_summary(self, key: str, title: str, data: Dict[str, Any], 
                    show_timestamp: bool = True, icon: str = "📊") -> None:
        """
        Muestra un resumen de procesamiento
        
        Args:
            key (str): Identificador del contenedor
            title (str): Título del resumen
            data (Dict[str, Any]): Datos a mostrar en el resumen
            show_timestamp (bool): Si se debe mostrar la marca de tiempo
            icon (str): Icono a mostrar junto al título
        """
        if key not in st.session_state.summary_containers:
            self.create_summary_container(key)
        
        with st.session_state.summary_containers[key]:
            # Limpiar contenido anterior
            st.empty()
            
            # Mostrar título con icono
            st.markdown(f"### {icon} {title}")
            
            # Mostrar marca de tiempo si se solicita
            if show_timestamp:
                st.caption(f"Generado: {datetime.now().strftime('%H:%M:%S')}")
            
            # Mostrar datos en formato de tabla
            if isinstance(data, dict):
                # Convertir a DataFrame para mejor visualización
                df = pd.DataFrame(list(data.items()), columns=["Parámetro", "Valor"])
                st.dataframe(df, hide_index=True, use_container_width=True)
            elif isinstance(data, pd.DataFrame):
                # Mostrar DataFrame directamente
                st.dataframe(data, hide_index=True, use_container_width=True)
            elif isinstance(data, list):
                # Mostrar lista como texto
                for item in data:
                    st.text(f"• {item}")
            else:
                # Mostrar como texto
                st.text(str(data))
    
    def show_database_summary(self, key: str, operation: str, results: Dict[str, Any]) -> None:
        """
        Muestra un resumen de operaciones de base de datos
        
        Args:
            key (str): Identificador del contenedor
            operation (str): Tipo de operación (INSERT, UPDATE, etc.)
            results (Dict[str, Any]): Resultados de la operación
        """
        if key not in st.session_state.summary_containers:
            self.create_summary_container(key)
        
        with st.session_state.summary_containers[key]:
            # Determinar icono y color según el resultado
            success = results.get("success", False)
            icon = "✅" if success else "❌"
            
            # Mostrar título con icono
            st.markdown(f"### {icon} Operación de Base de Datos: {operation}")
            
            # Mostrar marca de tiempo
            st.caption(f"Ejecutado: {datetime.now().strftime('%H:%M:%S')}")
            
            # Mostrar detalles de la operación
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Tabla", results.get("table", "N/A"))
                st.metric("Registros procesados", results.get("count", 0))
            
            with col2:
                st.metric("Estado", "Éxito" if success else "Error")
                if "elapsed" in results:
                    st.metric("Tiempo (s)", f"{results['elapsed']:.2f}")
            
            # Mostrar mensaje de éxito o error
            if success:
                st.success(results.get("message", "Operación completada con éxito"))
            else:
                st.error(results.get("error", "Error en la operación"))
                if "details" in results:
                    with st.expander("Detalles del error"):
                        st.code(results["details"])
    
    def show_signal_summary(self, key: str, signals: Dict[str, Any]) -> None:
        """
        Muestra un resumen de señales procesadas
        
        Args:
            key (str): Identificador del contenedor
            signals (Dict[str, Any]): Información de señales procesadas
        """
        if key not in st.session_state.summary_containers:
            self.create_summary_container(key)
        
        with st.session_state.summary_containers[key]:
            # Mostrar título
            st.markdown("### 📈 Resumen de Señales Procesadas")
            
            # Mostrar marca de tiempo
            st.caption(f"Generado: {datetime.now().strftime('%H:%M:%S')}")
            
            # Mostrar métricas principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de señales", signals.get("total", 0))
            
            with col2:
                st.metric("Señales guardadas", signals.get("saved", 0))
            
            with col3:
                st.metric("Alta confianza", signals.get("high_confidence", 0))
            
            # Mostrar detalles por tipo
            if "by_type" in signals and signals["by_type"]:
                st.subheader("Señales por tipo")
                
                type_data = []
                for signal_type, count in signals["by_type"].items():
                    type_data.append({"Tipo": signal_type, "Cantidad": count})
                
                st.dataframe(pd.DataFrame(type_data), hide_index=True)
            
            # Mostrar símbolos procesados
            if "symbols" in signals and signals["symbols"]:
                with st.expander("Símbolos procesados"):
                    st.write(", ".join(signals["symbols"]))
    
    def clear_summary(self, key: str) -> None:
        """
        Limpia un contenedor de resumen
        
        Args:
            key (str): Identificador del contenedor
        """
        if key in st.session_state.summary_containers:
            try:
                # Intentar limpiar el contenedor
                with st.session_state.summary_containers[key]:
                    st.empty()
            except:
                pass
            
            # Eliminar referencia
            st.session_state.summary_containers.pop(key, None)
    
    def clear_all_summaries(self) -> None:
        """Limpia todos los contenedores de resumen"""
        # Obtener todas las claves
        keys = list(st.session_state.summary_containers.keys())
        
        # Limpiar cada contenedor
        for key in keys:
            self.clear_summary(key)

# Crear instancia global
summary_manager = SummaryManager()

# Ejemplo de uso
if __name__ == "__main__":
    st.title("Demo de SummaryManager")
    
    if st.button("Mostrar resumen de ejemplo"):
        # Datos de ejemplo
        data = {
            "Total de símbolos": 25,
            "Símbolos procesados": 20,
            "Señales generadas": 15,
            "Señales de alta confianza": 5,
            "Tiempo de procesamiento": "45.2 segundos"
        }
        
        # Mostrar resumen
        summary_manager.show_summary("demo", "Resumen de Procesamiento", data)
    
    if st.button("Mostrar resumen de base de datos"):
        # Datos de ejemplo
        results = {
            "success": True,
            "table": "trading_signals",
            "count": 15,
            "elapsed": 2.34,
            "message": "Se guardaron 15 señales en la base de datos"
        }
        
        # Mostrar resumen
        summary_manager.show_database_summary("db_demo", "INSERT", results)
    
    if st.button("Mostrar resumen de señales"):
        # Datos de ejemplo
        signals = {
            "total": 25,
            "saved": 20,
            "high_confidence": 8,
            "by_type": {
                "CALL": 15,
                "PUT": 8,
                "NEUTRAL": 2
            },
            "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        }
        
        # Mostrar resumen
        summary_manager.show_signal_summary("signals_demo", signals)
