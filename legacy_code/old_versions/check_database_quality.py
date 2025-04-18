"""
Script para verificar la calidad de los datos en las tablas de la base de datos
"""

import logging
import pandas as pd
from database_utils import DatabaseManager
from ai_utils import get_expert_analysis

# import streamlit as st
from datetime import datetime, timedelta
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_table_quality(db_manager, table_name, limit=5):
    """Consulta los últimos registros de una tabla y evalúa su calidad"""
    try:
        query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}"
        results = db_manager.execute_query(query)

        if not results:
            logger.warning(f"No se encontraron registros en la tabla {table_name}")
            return None, "No hay registros"

        # Convertir a DataFrame para análisis más fácil
        df = pd.DataFrame(results)

        # Calcular estadísticas básicas
        total_rows = len(df)
        null_counts = df.isnull().sum()
        empty_string_counts = df.apply(
            lambda x: (x == "").sum() if x.dtype == "object" else 0
        )

        # Evaluar calidad
        quality_issues = []

        # Verificar campos vacíos o nulos
        for col in df.columns:
            null_pct = null_counts[col] / total_rows * 100
            if null_pct > 20:  # Si más del 20% son nulos
                quality_issues.append(f"Campo '{col}': {null_pct:.1f}% valores nulos")

            if col in empty_string_counts and empty_string_counts[col] > 0:
                empty_pct = empty_string_counts[col] / total_rows * 100
                if empty_pct > 20:  # Si más del 20% son cadenas vacías
                    quality_issues.append(
                        f"Campo '{col}': {empty_pct:.1f}% valores vacíos"
                    )

        # Verificar calidad de texto en campos específicos según la tabla
        if table_name == "trading_signals":
            text_fields = [
                "analysis",
                "technical_analysis",
                "expert_analysis",
                "recommendation",
            ]
            for field in text_fields:
                if field in df.columns:
                    for idx, value in df[field].items():
                        if isinstance(value, str) and len(value) < 50 and value:
                            quality_issues.append(
                                f"Registro {df.iloc[idx]['id']}, campo '{field}': texto demasiado corto ({len(value)} caracteres)"
                            )

        elif table_name == "market_news":
            for idx, row in df.iterrows():
                if (
                    "summary" in df.columns
                    and isinstance(row.get("summary"), str)
                    and len(row.get("summary", "")) < 50
                ):
                    quality_issues.append(
                        f"Noticia {row['id']}: resumen demasiado corto ({len(row.get('summary', ''))} caracteres)"
                    )
                if "url" in df.columns and not row.get("url"):
                    quality_issues.append(f"Noticia {row['id']}: sin URL de fuente")

        elif table_name == "market_sentiment":
            for idx, row in df.iterrows():
                if (
                    "notes" in df.columns
                    and isinstance(row.get("notes"), str)
                    and len(row.get("notes", "")) < 30
                ):
                    quality_issues.append(
                        f"Sentimiento {row['id']}: notas demasiado cortas ({len(row.get('notes', ''))} caracteres)"
                    )

        elif table_name == "email_logs":
            for idx, row in df.iterrows():
                if (
                    "content_summary" in df.columns
                    and isinstance(row.get("content_summary"), str)
                    and len(row.get("content_summary", "")) < 50
                ):
                    quality_issues.append(
                        f"Email {row['id']}: resumen de contenido demasiado corto ({len(row.get('content_summary', ''))} caracteres)"
                    )

        # Evaluar calidad general
        quality_score = 100 - min(
            len(quality_issues) * 10, 100
        )  # Reducir 10 puntos por cada problema, mínimo 0
        quality_level = (
            "Excelente"
            if quality_score >= 90
            else (
                "Buena"
                if quality_score >= 70
                else "Regular" if quality_score >= 50 else "Deficiente"
            )
        )

        quality_summary = {
            "tabla": table_name,
            "registros_analizados": total_rows,
            "calidad": quality_level,
            "puntuacion": quality_score,
            "problemas": quality_issues,
        }

        return df, quality_summary

    except Exception as e:
        logger.error(f"Error consultando tabla {table_name}: {str(e)}")
        return None, f"Error: {str(e)}"


def improve_data_quality(db_manager, table_name, data_df, quality_summary):
    """Mejora la calidad de los datos utilizando el experto"""
    if data_df is not None and not data_df.empty:
        logger.info(f"Mejorando calidad de datos para tabla {table_name}")

        # Diferentes estrategias según la tabla
        if table_name == "trading_signals":
            for idx, row in data_df.iterrows():
                signal_id = row["id"]

                # Campos a mejorar
                fields_to_improve = {}

                # Verificar campos de texto que necesitan mejora
                text_fields = {
                    "analysis": "análisis general",
                    "technical_analysis": "análisis técnico",
                    "expert_analysis": "análisis experto",
                    "recommendation": "recomendación",
                }

                for field, description in text_fields.items():
                    if field in row and (
                        row[field] is None
                        or (
                            isinstance(row[field], str)
                            and (
                                len(row[field]) < 100
                                or "lorem ipsum" in row[field].lower()
                            )
                        )
                    ):
                        fields_to_improve[field] = row.get(field, "")

                if fields_to_improve:
                    # Preparar contexto para el experto
                    symbol = row.get("symbol", "Desconocido")
                    direction = row.get("direction", "NEUTRAL")
                    price = row.get("price", 0)

                    # Mejorar cada campo con el experto
                    for field, current_text in fields_to_improve.items():
                        prompt = f"""
                        Eres un experto en análisis financiero. Necesito que mejores el siguiente {text_fields[field]} para una señal de trading:

                        Símbolo: {symbol}
                        Dirección: {direction}
                        Precio: {price}

                        Texto actual: "{current_text}"

                        Por favor, proporciona un {text_fields[field]} más detallado, profesional y útil para inversores.
                        Incluye análisis específicos, datos relevantes y conclusiones claras.
                        El texto debe ser conciso pero informativo, aproximadamente 200-300 palabras.
                        """

                        try:
                            improved_text = get_expert_analysis(prompt)

                            if improved_text and len(improved_text) > len(current_text):
                                # Actualizar en la base de datos
                                update_query = f"UPDATE trading_signals SET {field} = %s WHERE id = %s"
                                db_manager.execute_query(
                                    update_query,
                                    [improved_text, signal_id],
                                    fetch=False,
                                )
                                logger.info(
                                    f"Mejorado campo {field} para señal ID {signal_id}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error mejorando campo {field} para señal ID {signal_id}: {str(e)}"
                            )

        elif table_name == "market_news":
            for idx, row in data_df.iterrows():
                news_id = row["id"]

                # Verificar si el resumen necesita mejora
                if "summary" in row and (
                    row["summary"] is None
                    or (isinstance(row["summary"], str) and len(row["summary"]) < 100)
                ):
                    title = row.get("title", "Noticia sin título")

                    prompt = f"""
                    Eres un experto en noticias financieras. Necesito que mejores el siguiente resumen de noticia:

                    Título: {title}
                    Resumen actual: "{row.get('summary', '')}"

                    Por favor, proporciona un resumen más detallado, informativo y profesional.
                    Incluye los puntos clave, el impacto potencial en los mercados y cualquier dato relevante.
                    El resumen debe ser conciso pero completo, aproximadamente 150-200 palabras.
                    """

                    try:
                        improved_summary = get_expert_analysis(prompt)

                        if improved_summary and len(improved_summary) > len(
                            row.get("summary", "")
                        ):
                            # Actualizar en la base de datos
                            update_query = (
                                "UPDATE market_news SET summary = %s WHERE id = %s"
                            )
                            db_manager.execute_query(
                                update_query, [improved_summary, news_id], fetch=False
                            )
                            logger.info(f"Mejorado resumen para noticia ID {news_id}")
                    except Exception as e:
                        logger.error(
                            f"Error mejorando resumen para noticia ID {news_id}: {str(e)}"
                        )

        elif table_name == "market_sentiment":
            for idx, row in data_df.iterrows():
                sentiment_id = row["id"]

                # Verificar si las notas necesitan mejora
                if "notes" in row and (
                    row["notes"] is None
                    or (isinstance(row["notes"], str) and len(row["notes"]) < 100)
                ):
                    overall = row.get("overall", "Neutral")

                    prompt = f"""
                    Eres un experto en análisis de sentimiento de mercado. Necesito que mejores las siguientes notas:

                    Sentimiento general: {overall}
                    VIX: {row.get('vix', 'N/A')}
                    Tendencia S&P500: {row.get('sp500_trend', 'N/A')}

                    Notas actuales: "{row.get('notes', '')}"

                    Por favor, proporciona notas más detalladas y analíticas sobre el sentimiento del mercado.
                    Incluye análisis de factores clave, tendencias actuales y posibles implicaciones para inversores.
                    Las notas deben ser profesionales y útiles, aproximadamente 200-250 palabras.
                    """

                    try:
                        improved_notes = get_expert_analysis(prompt)

                        if improved_notes and len(improved_notes) > len(
                            row.get("notes", "")
                        ):
                            # Actualizar en la base de datos
                            update_query = (
                                "UPDATE market_sentiment SET notes = %s WHERE id = %s"
                            )
                            db_manager.execute_query(
                                update_query,
                                [improved_notes, sentiment_id],
                                fetch=False,
                            )
                            logger.info(
                                f"Mejoradas notas para sentimiento ID {sentiment_id}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error mejorando notas para sentimiento ID {sentiment_id}: {str(e)}"
                        )

    return "Proceso de mejora completado"


def main():
    """Función principal"""
    print("\n===== VERIFICACIÓN DE CALIDAD DE DATOS EN LA BASE DE DATOS =====\n")

    # Crear instancia del gestor de base de datos
    db_manager = DatabaseManager()

    # Tablas a verificar
    tables = ["trading_signals", "market_news", "market_sentiment", "email_logs"]

    all_quality_summaries = {}
    all_data = {}

    # Verificar cada tabla
    for table in tables:
        print(f"\n----- Verificando tabla: {table} -----")
        data_df, quality_summary = check_table_quality(db_manager, table)

        all_quality_summaries[table] = quality_summary
        all_data[table] = data_df

        # Mostrar resultados
        if isinstance(quality_summary, dict):
            print(
                f"Calidad: {quality_summary['calidad']} ({quality_summary['puntuacion']}/100)"
            )
            print(f"Registros analizados: {quality_summary['registros_analizados']}")

            if quality_summary["problemas"]:
                print("\nProblemas detectados:")
                for issue in quality_summary["problemas"]:
                    print(f"- {issue}")
            else:
                print("\nNo se detectaron problemas de calidad.")
        else:
            print(f"No se pudo analizar la tabla: {quality_summary}")

    # Preguntar si se desea mejorar la calidad de los datos
    improve = input("\n¿Desea mejorar la calidad de los datos? (s/n): ")

    if improve.lower() == "s":
        for table in tables:
            if (
                table in all_data
                and all_data[table] is not None
                and not all_data[table].empty
            ):
                if (
                    isinstance(all_quality_summaries[table], dict)
                    and all_quality_summaries[table]["problemas"]
                ):
                    print(f"\nMejorando calidad de datos para tabla {table}...")
                    result = improve_data_quality(
                        db_manager, table, all_data[table], all_quality_summaries[table]
                    )
                    print(result)

    print("\n===== VERIFICACIÓN COMPLETADA =====")


if __name__ == "__main__":
    main()
