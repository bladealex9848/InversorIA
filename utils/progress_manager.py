#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de barras de progreso para InversorIA Pro
"""

import streamlit as st
import time
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional, Union, Callable

# Configurar logging
logger = logging.getLogger(__name__)

class ProgressManager:
    """
    Clase para gestionar barras de progreso y mensajes de estado
    Evita la acumulación de barras de progreso en la interfaz
    """
    
    def __init__(self):
        """Inicializa el gestor de progreso"""
        # Inicializar contenedores para barras de progreso y mensajes
        if "progress_bars" not in st.session_state:
            st.session_state.progress_bars = {}
        
        if "status_messages" not in st.session_state:
            st.session_state.status_messages = {}
        
        if "progress_details" not in st.session_state:
            st.session_state.progress_details = {}
    
    def create_progress_bar(self, key: str, initial_text: str = "Procesando...") -> None:
        """
        Crea una nueva barra de progreso
        
        Args:
            key (str): Identificador único para la barra de progreso
            initial_text (str): Texto inicial para mostrar
        """
        # Limpiar barras anteriores con la misma clave
        self.clear_progress(key)
        
        # Crear nuevos contenedores
        st.session_state.progress_bars[key] = st.progress(0, text=initial_text)
        st.session_state.status_messages[key] = st.empty()
        st.session_state.progress_details[key] = st.empty()
    
    def update_progress(self, key: str, progress: float, status_text: str = None, detail_text: str = None) -> None:
        """
        Actualiza una barra de progreso existente
        
        Args:
            key (str): Identificador de la barra de progreso
            progress (float): Valor de progreso (0-1)
            status_text (str, optional): Texto de estado principal
            detail_text (str, optional): Texto de detalle secundario
        """
        if key in st.session_state.progress_bars:
            # Actualizar barra de progreso
            progress_text = status_text if status_text else st.session_state.progress_bars[key].text
            st.session_state.progress_bars[key].progress(progress, text=progress_text)
            
            # Actualizar mensajes si se proporcionan
            if status_text and key in st.session_state.status_messages:
                st.session_state.status_messages[key].text(status_text)
            
            if detail_text and key in st.session_state.progress_details:
                st.session_state.progress_details[key].text(detail_text)
    
    def complete_progress(self, key: str, success_text: str = "¡Completado!", show_success: bool = True, 
                         clear_after: float = 1.0) -> None:
        """
        Marca una barra de progreso como completada
        
        Args:
            key (str): Identificador de la barra de progreso
            success_text (str): Texto a mostrar al completar
            show_success (bool): Si se debe mostrar el mensaje de éxito
            clear_after (float): Segundos a esperar antes de limpiar (0 para no limpiar)
        """
        if key in st.session_state.progress_bars:
            # Completar la barra
            st.session_state.progress_bars[key].progress(1.0)
            
            # Mostrar mensaje de éxito si se solicita
            if show_success and key in st.session_state.status_messages:
                st.session_state.status_messages[key].success(success_text)
            
            # Limpiar detalles
            if key in st.session_state.progress_details:
                st.session_state.progress_details[key].empty()
            
            # Esperar y limpiar si se solicita
            if clear_after > 0:
                time.sleep(clear_after)
                self.clear_progress(key)
    
    def error_progress(self, key: str, error_text: str = "Error en el proceso", 
                      clear_after: float = 3.0) -> None:
        """
        Marca una barra de progreso con error
        
        Args:
            key (str): Identificador de la barra de progreso
            error_text (str): Texto de error a mostrar
            clear_after (float): Segundos a esperar antes de limpiar (0 para no limpiar)
        """
        if key in st.session_state.progress_bars:
            # Mostrar mensaje de error
            if key in st.session_state.status_messages:
                st.session_state.status_messages[key].error(error_text)
            
            # Limpiar detalles
            if key in st.session_state.progress_details:
                st.session_state.progress_details[key].empty()
            
            # Esperar y limpiar si se solicita
            if clear_after > 0:
                time.sleep(clear_after)
                self.clear_progress(key)
    
    def clear_progress(self, key: str) -> None:
        """
        Limpia una barra de progreso y sus mensajes asociados
        
        Args:
            key (str): Identificador de la barra de progreso
        """
        # Limpiar barra de progreso
        if key in st.session_state.progress_bars:
            try:
                st.session_state.progress_bars[key].empty()
            except:
                pass
            st.session_state.progress_bars.pop(key, None)
        
        # Limpiar mensaje de estado
        if key in st.session_state.status_messages:
            try:
                st.session_state.status_messages[key].empty()
            except:
                pass
            st.session_state.status_messages.pop(key, None)
        
        # Limpiar detalles
        if key in st.session_state.progress_details:
            try:
                st.session_state.progress_details[key].empty()
            except:
                pass
            st.session_state.progress_details.pop(key, None)
    
    def clear_all_progress(self) -> None:
        """Limpia todas las barras de progreso y mensajes"""
        # Obtener todas las claves
        keys = list(st.session_state.progress_bars.keys())
        
        # Limpiar cada barra
        for key in keys:
            self.clear_progress(key)
    
    def run_with_progress(self, key: str, function: Callable, args: tuple = None, 
                         kwargs: dict = None, initial_text: str = "Procesando...",
                         success_text: str = "¡Completado!", error_text: str = "Error en el proceso",
                         phases: List[str] = None) -> Any:
        """
        Ejecuta una función mostrando una barra de progreso
        
        Args:
            key (str): Identificador para la barra de progreso
            function (Callable): Función a ejecutar
            args (tuple): Argumentos posicionales para la función
            kwargs (dict): Argumentos con nombre para la función
            initial_text (str): Texto inicial para la barra
            success_text (str): Texto a mostrar al completar con éxito
            error_text (str): Texto a mostrar en caso de error
            phases (List[str]): Lista de fases a mostrar durante la ejecución
            
        Returns:
            Any: Resultado de la función ejecutada
        """
        # Preparar argumentos
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        
        # Crear barra de progreso
        self.create_progress_bar(key, initial_text)
        
        # Configurar fases si se proporcionan
        phase_duration = 0
        if phases:
            phase_duration = 1.0 / len(phases)
            self.update_progress(key, 0.05, initial_text, phases[0])
        else:
            self.update_progress(key, 0.05, initial_text)
        
        try:
            # Iniciar tiempo
            start_time = time.time()
            
            # Ejecutar función en un hilo separado para poder actualizar la UI
            result = function(*args, **kwargs)
            
            # Calcular tiempo transcurrido
            elapsed = time.time() - start_time
            
            # Mostrar mensaje de éxito
            self.complete_progress(key, f"{success_text} ({elapsed:.1f}s)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en run_with_progress para {key}: {str(e)}")
            self.error_progress(key, f"{error_text}: {str(e)}")
            raise e

# Crear instancia global
progress_manager = ProgressManager()

# Ejemplo de uso
if __name__ == "__main__":
    st.title("Demo de ProgressManager")
    
    if st.button("Ejecutar proceso con fases"):
        # Lista de fases
        phases = [
            "Inicializando proceso...",
            "Cargando datos...",
            "Procesando información...",
            "Analizando resultados...",
            "Generando informe...",
            "Finalizando..."
        ]
        
        # Crear barra de progreso
        progress_manager.create_progress_bar("demo", "Iniciando proceso")
        
        # Simular proceso con fases
        for i, phase in enumerate(phases):
            # Actualizar progreso
            progress = (i / len(phases)) * 0.9  # Máximo 90% hasta completar
            progress_manager.update_progress("demo", progress, f"Proceso en curso ({int(progress*100)}%)", phase)
            
            # Simular trabajo
            time.sleep(1)
        
        # Completar proceso
        progress_manager.complete_progress("demo", "¡Proceso completado con éxito!")
