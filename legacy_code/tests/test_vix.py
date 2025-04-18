import market_utils
import pandas as pd

# Limpiar caché
market_utils._data_cache.clear()

# Forzar la generación de datos sintéticos
data = market_utils._generate_vix_synthetic_data("1mo")
print(f"Datos sintéticos del VIX generados: {len(data)} filas")
print(data.tail(3))
