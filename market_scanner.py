import pandas as pd
import numpy as np
from trading_analyzer import TradingAnalyzer
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import streamlit as st

logger = logging.getLogger(__name__)


class MarketScanner:
    def __init__(self, symbols_dict, analyzer=None):
        self.symbols_dict = symbols_dict
        # Si se proporciona un analizador, usarlo; de lo contrario, crear uno nuevo
        self.analyzer = analyzer if analyzer is not None else TradingAnalyzer()
        self.all_symbols = [
            symbol for symbols in symbols_dict.values() for symbol in symbols
        ]
        self.last_scan_results = {}  # Almacena resultados del último scan

    def _analyze_symbol(self, symbol):
        try:
            trend, daily_data = self.analyzer.analyze_trend(symbol)
            hourly_data = self.analyzer.get_market_data(
                symbol, period="5d", interval="1h"
            )
            strategies = self.analyzer.identify_strategy(hourly_data, trend)

            if not strategies:
                return None

            result = {
                "Symbol": symbol,
                "Sector": next(
                    sector
                    for sector, symbols in self.symbols_dict.items()
                    if symbol in symbols
                ),
                "Tendencia": trend["direction"],
                "Fuerza": trend["strength"],
                "Precio": trend["metrics"]["price"],
                "RSI": trend["metrics"]["rsi"],
                "Estrategia": strategies[0]["type"],
                "Setup": strategies[0]["name"],
                "Confianza": strategies[0]["confidence"],
                "Entry": strategies[0]["levels"]["entry"],
                "Stop": strategies[0]["levels"]["stop"],
                "Target": strategies[0]["levels"]["target"],
                "R/R": strategies[0]["levels"]["r_r"],
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "trend_data": trend,
                "strategies": strategies,  # Guardamos todas las estrategias
            }

            # Almacenar resultado en el cache
            self.last_scan_results[symbol] = result

            return result

        except Exception as e:
            logger.error(f"Error analizando {symbol}: {str(e)}")
            return None

    def get_cached_analysis(self, symbol):
        """Obtiene el último análisis cacheado para un símbolo"""
        return self.last_scan_results.get(symbol)

    def scan_market(self, selected_sectors=None):
        """
        Escanea el mercado, opcionalmente filtrando por sectores.

        Args:
            selected_sectors (list): Lista de sectores a analizar. None para todos.
        """
        # Filtrar símbolos por sector si es necesario
        symbols_to_scan = []
        if selected_sectors:
            symbols_to_scan = [
                symbol
                for sector in selected_sectors
                for symbol in self.symbols_dict.get(sector, [])
            ]
        else:
            symbols_to_scan = self.all_symbols

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for result in executor.map(self._analyze_symbol, symbols_to_scan):
                if result is not None:
                    results.append(result)

        # Ordenar resultados
        if results:
            df = pd.DataFrame(results)
            confidence_order = {"ALTA": 0, "MEDIA": 1}
            df["conf_order"] = df["Confianza"].map(confidence_order)
            df = df.sort_values(["conf_order", "Symbol"]).drop("conf_order", axis=1)
            return df

        return pd.DataFrame()


def display_opportunities(scanner):
    """
    Muestra oportunidades de trading en Streamlit.

    Args:
        scanner (MarketScanner): Scanner de mercado inicializado
    """
    st.subheader("🎯 Scanner de Oportunidades")

    # Obtener oportunidades
    opportunities = scanner.scan_market()

    if opportunities.empty:
        st.warning("No se identificaron oportunidades que cumplan los criterios")
        return

    # Mostrar métricas generales
    col1, col2, col3 = st.columns(3)
    with col1:
        total_calls = len(opportunities[opportunities["Estrategia"] == "CALL"])
        st.metric("Setups CALL", total_calls)
    with col2:
        total_puts = len(opportunities[opportunities["Estrategia"] == "PUT"])
        st.metric("Setups PUT", total_puts)
    with col3:
        high_conf = len(opportunities[opportunities["Confianza"] == "ALTA"])
        st.metric("Alta Confianza", high_conf)

    # Mostrar tabla de oportunidades
    st.markdown("### Oportunidades Identificadas")

    # Estilizar DataFrame
    styled_df = opportunities.style.apply(
        lambda x: [
            (
                "background-color: #c8e6c9"
                if x["Estrategia"] == "CALL"
                else "background-color: #ffcdd2" if x["Estrategia"] == "PUT" else ""
            )
            for i in range(len(x))
        ],
        axis=1,
    )

    st.dataframe(
        styled_df,
        column_config={
            "Symbol": "Símbolo",
            "Sector": "Sector",
            "Tendencia": "Tendencia",
            "Fuerza": "Fuerza",
            "Precio": st.column_config.NumberColumn("Precio", format="$%.2f"),
            "RSI": st.column_config.NumberColumn("RSI", format="%.1f"),
            "Estrategia": "Estrategia",
            "Setup": "Setup",
            "Confianza": "Confianza",
            "Entry": st.column_config.NumberColumn("Entrada", format="$%.2f"),
            "Stop": st.column_config.NumberColumn("Stop Loss", format="$%.2f"),
            "Target": st.column_config.NumberColumn("Target", format="$%.2f"),
            "R/R": "Riesgo/Reward",
            "Timestamp": "Hora",
        },
        hide_index=True,
        use_container_width=True,
    )

    # Mostrar detalles por sector
    st.markdown("### 📊 Análisis por Sector")
    sector_stats = (
        opportunities.groupby("Sector")
        .agg(
            {
                "Symbol": "count",
                "Estrategia": lambda x: list(x),
                "Confianza": lambda x: list(x),
            }
        )
        .reset_index()
    )

    for _, row in sector_stats.iterrows():
        with st.expander(f"{row['Sector']} ({row['Symbol']} oportunidades)"):
            calls = len([s for s in row["Estrategia"] if s == "CALL"])
            puts = len([s for s in row["Estrategia"] if s == "PUT"])
            high_conf = len([c for c in row["Confianza"] if c == "ALTA"])

            st.write(
                f"""
            - CALLS: {calls}
            - PUTS: {puts}
            - Alta Confianza: {high_conf}
            """
            )

    # Actualización
    st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")


def run_scanner(symbols_dict):
    """
    Ejecuta el scanner de mercado.

    Args:
        symbols_dict (dict): Diccionario de símbolos por sector
    """
    scanner = MarketScanner(symbols_dict)
    display_opportunities(scanner)
