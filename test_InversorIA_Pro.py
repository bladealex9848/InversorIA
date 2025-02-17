import pytest
import pandas as pd
from datetime import datetime

from InversorIA_Pro import fetch_market_data, TechnicalAnalyzer, get_market_context

def test_fetch_market_data():
    # Prueba con un símbolo válido
    data = fetch_market_data("AAPL", period="1mo", interval="1d")
    assert data is not None
    assert len(data) > 0
    assert all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])

    # Prueba con un símbolo inválido
    data = fetch_market_data("INVALID", period="1mo", interval="1d")
    assert data is None

def test_technical_analyzer():
    # Crear datos de prueba
    data = pd.DataFrame({
        'Open': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        'High': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
        'Low': [1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        'Close': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
        'Volume': [1000] * 20
    })

    # Prueba con datos válidos
    analyzer = TechnicalAnalyzer(data)
    analyzer.calculate_indicators()
    signals = analyzer.get_current_signals()
    assert signals is not None
    assert isinstance(signals, dict)

def test_get_market_context():
    context = get_market_context("AAPL")
    assert context is not None
    assert isinstance(context, dict)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error en aplicación principal: {str(e)}")
        st.error(
            "Error en la aplicación. Por favor, revise los logs para más detalles."
        )