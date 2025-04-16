import mysql.connector
from datetime import datetime
import json
import toml
import pandas as pd

# Cargar configuración
secrets = toml.load('.streamlit/secrets.toml')

# Crear una señal de prueba
test_row = {
    "Symbol": "AAPL",
    "Precio": 175.50,
    "Estrategia": "CALL",
    "Confianza": "Alta",
    "Sector": "Tecnología",
    "RSI": 65.2,
    "Tendencia": "ALCISTA",
    "Fuerza": "moderada",
    "Setup": "Ruptura de resistencia",
    "R/R": 2.5,
}

# Simular el código de generación de señales
# Generar análisis técnico
technical_analysis = f"El activo {test_row['Symbol']} muestra una tendencia {test_row.get('Tendencia', 'NEUTRAL').lower()} "
technical_analysis += f"con fuerza {test_row.get('Fuerza', 'moderada')}. "
technical_analysis += f"RSI en {test_row.get('RSI', 50):.2f} indica "

# Interpretar RSI
rsi_value = test_row.get('RSI', 50)
if rsi_value < 30:
    technical_analysis += "condiciones de sobreventa. "
elif rsi_value > 70:
    technical_analysis += "condiciones de sobrecompra. "
else:
    technical_analysis += "condiciones neutras. "

# Añadir información de setup
technical_analysis += f"El setup identificado es {test_row.get('Setup', 'Análisis Técnico')} "
technical_analysis += f"con una relación riesgo/recompensa de {test_row.get('R/R', 0.0):.2f}."

# Generar niveles de soporte y resistencia
price = test_row.get('Precio', 0.0)
if price > 0:
    # Calcular soporte y resistencia basados en el precio actual y la tendencia
    trend = test_row.get('Tendencia', 'NEUTRAL')
    if trend == 'ALCISTA':
        support_level = price * 0.95  # 5% por debajo del precio actual
        resistance_level = price * 1.10  # 10% por encima del precio actual
    elif trend == 'BAJISTA':
        support_level = price * 0.90  # 10% por debajo del precio actual
        resistance_level = price * 1.05  # 5% por encima del precio actual
    else:  # NEUTRAL
        support_level = price * 0.97  # 3% por debajo del precio actual
        resistance_level = price * 1.03  # 3% por encima del precio actual
        
    technical_analysis += f" Niveles clave: Soporte en ${support_level:.2f} y resistencia en ${resistance_level:.2f}."

# Generar volatilidad
sector = test_row.get("Sector", "")
trend = test_row.get("Tendencia", "NEUTRAL")

# Valores base de volatilidad por sector
sector_volatility = {
    "Tecnología": 35.0,
    "Finanzas": 25.0,
    "Salud": 30.0,
    "Energía": 40.0,
    "Consumo": 20.0,
    "Volatilidad": 60.0,
    "Materias Primas": 35.0,
    "Comunicaciones": 28.0,
    "Industrial": 27.0,
    "Servicios": 22.0,
    "Utilidades": 18.0,
    "Inmobiliario": 23.0,
    "Índices": 20.0,
}

# Obtener volatilidad base del sector o valor predeterminado
base_volatility = sector_volatility.get(sector, 30.0)

# Ajustar por tendencia
if trend == "ALCISTA" and test_row.get("Fuerza", "") == "fuerte":
    volatility = base_volatility * 0.8  # Menos volatilidad en tendencia alcista fuerte
elif trend == "BAJISTA" and test_row.get("Fuerza", "") == "fuerte":
    volatility = base_volatility * 1.3  # Más volatilidad en tendencia bajista fuerte
elif trend == "NEUTRAL":
    volatility = base_volatility * 1.1  # Ligeramente más volatilidad en mercado neutral
else:
    volatility = base_volatility

# Ajustar por RSI
if rsi_value < 30 or rsi_value > 70:
    volatility *= 1.2  # Mayor volatilidad en condiciones extremas

# Generar señal de opciones
direction = "CALL" if test_row.get("Estrategia", "") == "CALL" else "PUT"
if direction == "CALL":
    if volatility > 40:
        options_signal = "CALL SPREAD"  # Menos riesgo en alta volatilidad
    else:
        options_signal = "CALL DIRECTO"
elif direction == "PUT":
    if volatility > 40:
        options_signal = "PUT SPREAD"  # Menos riesgo en alta volatilidad
    else:
        options_signal = "PUT DIRECTO"
else:
    if volatility > 35:
        options_signal = "IRON CONDOR"  # Estrategia neutral para alta volatilidad
    else:
        options_signal = "BUTTERFLY"

# Generar análisis de opciones
options_analysis = f"La volatilidad implícita de {test_row['Symbol']} es del {volatility:.2f}%, "
if volatility > 50:
    options_analysis += "lo que indica alta incertidumbre en el mercado. "
elif volatility > 30:
    options_analysis += "lo que indica volatilidad moderada. "
else:
    options_analysis += "lo que indica baja volatilidad. "

options_analysis += f"El análisis de opciones sugiere una estrategia {options_signal}. "

# Añadir recomendaciones específicas basadas en la estrategia
if options_signal == "CALL DIRECTO":
    options_analysis += f"Considerar compra de calls con strike cercano a ${test_row.get('Precio', 0.0):.2f} "
    options_analysis += "con vencimiento de 30-45 días."
elif options_signal == "PUT DIRECTO":
    options_analysis += f"Considerar compra de puts con strike cercano a ${test_row.get('Precio', 0.0):.2f} "
    options_analysis += "con vencimiento de 30-45 días."
elif "SPREAD" in options_signal:
    options_analysis += "Esta estrategia limita el riesgo y la recompensa, "
    options_analysis += "ideal para entornos de alta volatilidad."
elif options_signal in ["IRON CONDOR", "BUTTERFLY"]:
    options_analysis += "Estrategia neutral que se beneficia de baja volatilidad "
    options_analysis += "o movimiento lateral del precio."

# Generar análisis multi-timeframe
mtf_analysis = f"Análisis de {test_row['Symbol']} en múltiples marcos temporales: "

# Tendencias por timeframe
daily_trend = "NEUTRAL"
weekly_trend = "NEUTRAL"
monthly_trend = "NEUTRAL"

# Determinar tendencias basadas en la tendencia principal y la fuerza
main_trend = test_row.get("Tendencia", "NEUTRAL")
strength = test_row.get("Fuerza", "moderada")

if main_trend == "ALCISTA":
    if strength == "fuerte":
        daily_trend = "ALCISTA"
        weekly_trend = "ALCISTA"
        monthly_trend = "NEUTRAL"
    elif strength == "moderada":
        daily_trend = "ALCISTA"
        weekly_trend = "NEUTRAL"
        monthly_trend = "NEUTRAL"
    else:
        daily_trend = "ALCISTA"
        weekly_trend = "NEUTRAL"
        monthly_trend = "BAJISTA"
elif main_trend == "BAJISTA":
    if strength == "fuerte":
        daily_trend = "BAJISTA"
        weekly_trend = "BAJISTA"
        monthly_trend = "NEUTRAL"
    elif strength == "moderada":
        daily_trend = "BAJISTA"
        weekly_trend = "NEUTRAL"
        monthly_trend = "NEUTRAL"
    else:
        daily_trend = "BAJISTA"
        weekly_trend = "NEUTRAL"
        monthly_trend = "ALCISTA"

mtf_analysis += f"Diario: {daily_trend}, Semanal: {weekly_trend}, Mensual: {monthly_trend}. "

# Añadir recomendación basada en tendencias
if daily_trend == weekly_trend and daily_trend != "NEUTRAL":
    mtf_analysis += f"Confirmación de tendencia {daily_trend.lower()} en múltiples timeframes."
elif daily_trend != weekly_trend and daily_trend != "NEUTRAL" and weekly_trend != "NEUTRAL":
    mtf_analysis += "Divergencia entre timeframes, se recomienda cautela."
else:
    mtf_analysis += "Sin tendencia clara en múltiples timeframes."

# Generar análisis experto
expert_analysis = f"Análisis experto para {test_row['Symbol']}: "

# Determinar recomendación basada en la dirección y confianza
confidence = test_row.get("Confianza", "Media")
if direction == "CALL" and confidence == "Alta":
    recommendation = "COMPRAR"
    expert_analysis += "Se recomienda COMPRAR basado en fuerte señal alcista. "
elif direction == "PUT" and confidence == "Alta":
    recommendation = "VENDER"
    expert_analysis += "Se recomienda VENDER basado en fuerte señal bajista. "
elif direction == "CALL":
    recommendation = "MANTENER/COMPRAR"
    expert_analysis += "Se recomienda MANTENER/COMPRAR con cautela. "
elif direction == "PUT":
    recommendation = "MANTENER/VENDER"
    expert_analysis += "Se recomienda MANTENER/VENDER con cautela. "
else:
    recommendation = "MANTENER"
    expert_analysis += "Se recomienda MANTENER y esperar mejor configuración. "

# Añadir información de riesgo/recompensa
rr = test_row.get("R/R", 0.0)
if rr > 3:
    expert_analysis += f"Excelente relación riesgo/recompensa de {rr:.2f}."
elif rr > 2:
    expert_analysis += f"Buena relación riesgo/recompensa de {rr:.2f}."
elif rr > 1:
    expert_analysis += f"Aceptable relación riesgo/recompensa de {rr:.2f}."
else:
    expert_analysis += f"Baja relación riesgo/recompensa de {rr:.2f}, se recomienda cautela."

# Generar indicadores alcistas/bajistas
bullish_indicators = []
if test_row.get("RSI", 50) < 30:
    bullish_indicators.append("RSI en sobreventa")
if test_row.get("Tendencia", "NEUTRAL") == "ALCISTA":
    bullish_indicators.append("Tendencia alcista")
if test_row.get("Precio", 0) > support_level and support_level > 0:
    bullish_indicators.append("Precio por encima del soporte")

bullish_indicators_str = (
    ", ".join(bullish_indicators)
    if bullish_indicators
    else "No se detectaron indicadores alcistas significativos"
)

bearish_indicators = []
if test_row.get("RSI", 50) > 70:
    bearish_indicators.append("RSI en sobrecompra")
if test_row.get("Tendencia", "NEUTRAL") == "BAJISTA":
    bearish_indicators.append("Tendencia bajista")
if test_row.get("Precio", 0) < resistance_level and resistance_level > 0:
    bearish_indicators.append("Precio por debajo de la resistencia")

bearish_indicators_str = (
    ", ".join(bearish_indicators)
    if bearish_indicators
    else "No se detectaron indicadores bajistas significativos"
)

# Generar noticias
latest_news = f"Análisis técnico muestra {test_row.get('Tendencia', 'NEUTRAL').lower()} para {test_row['Symbol']} con RSI en {test_row.get('RSI', 50):.2f}"
news_source = "InversorIA Analytics"
additional_news = (
    f"El activo {test_row['Symbol']} del sector {test_row['Sector']} muestra una tendencia {test_row.get('Tendencia', 'NEUTRAL').lower()} "
    + f"con una relación riesgo/recompensa de {test_row.get('R/R', 1.0):.2f}. "
    + (
        "Se recomienda cautela debido a la volatilidad del mercado."
        if volatility > 35
        else "Las condiciones de mercado son favorables para esta operación."
    )
)

# Calcular stop loss y target price
entry_price = test_row.get("Precio", 0.0)
if direction == "CALL":
    stop_loss = entry_price * 0.98  # 2% abajo para CALL
    target_price = entry_price * 1.05  # 5% arriba para CALL
else:  # PUT
    stop_loss = entry_price * 1.02  # 2% arriba para PUT
    target_price = entry_price * 0.95  # 5% abajo para PUT

# Crear señal completa
signal = {
    # Campos básicos
    "symbol": test_row["Symbol"],
    "price": test_row["Precio"],
    "direction": direction,
    "confidence_level": confidence,
    "timeframe": "Medio Plazo",
    "strategy": test_row.get("Estrategia", "NEUTRAL"),
    "category": test_row["Sector"],
    "analysis": f"Señal {direction} con confianza {confidence}. RSI: {test_row.get('RSI', 'N/A')}. R/R: {test_row.get('R/R', 'N/A')}",
    "created_at": datetime.now(),
    
    # Campos adicionales para niveles de trading
    "entry_price": entry_price,
    "stop_loss": stop_loss,
    "target_price": target_price,
    "risk_reward": test_row.get("R/R", 0.0),
    "setup_type": test_row.get("Setup", f"Estrategia {direction} genérica"),
    
    # Campos para análisis técnico
    "technical_analysis": technical_analysis,
    "support_level": support_level,
    "resistance_level": resistance_level,
    "rsi": test_row.get("RSI", 0.0),
    "trend": test_row.get("Tendencia", "NEUTRAL"),
    "trend_strength": test_row.get("Fuerza", "moderada"),
    
    # Campos para opciones
    "volatility": volatility,
    "options_signal": options_signal,
    "options_analysis": options_analysis,
    
    # Campos para Trading Specialist
    "trading_specialist_signal": "NEUTRAL",
    "trading_specialist_confidence": "MEDIA",
    
    # Campos para sentimiento y noticias
    "sentiment": "neutral",
    "sentiment_score": 0.5,
    "latest_news": latest_news,
    "news_source": news_source,
    "additional_news": additional_news,
    
    # Campos para análisis experto y multi-timeframe
    "expert_analysis": expert_analysis,
    "recommendation": recommendation,
    "mtf_analysis": mtf_analysis,
    "daily_trend": daily_trend,
    "weekly_trend": weekly_trend,
    "monthly_trend": monthly_trend,
    "bullish_indicators": bullish_indicators_str,
    "bearish_indicators": bearish_indicators_str,
    
    # Indicador de alta confianza
    "is_high_confidence": confidence == "Alta",
}

# Conectar a la base de datos
try:
    conn = mysql.connector.connect(
        host=secrets['db_host'],
        user=secrets['db_user'],
        password=secrets['db_password'],
        database=secrets['db_name'],
        port=int(secrets['db_port'])
    )
    
    cursor = conn.cursor()
    
    # Preparar consulta con todos los campos
    query = """INSERT INTO trading_signals
              (symbol, price, direction, confidence_level, timeframe,
               strategy, category, analysis, created_at,
               entry_price, stop_loss, target_price, risk_reward, setup_type,
               technical_analysis, support_level, resistance_level, rsi, trend, trend_strength,
               volatility, options_signal, options_analysis, trading_specialist_signal,
               trading_specialist_confidence, sentiment, sentiment_score, latest_news,
               news_source, additional_news, expert_analysis, recommendation, mtf_analysis,
               daily_trend, weekly_trend, monthly_trend, bullish_indicators, bearish_indicators,
               is_high_confidence)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    
    # Preparar datos
    params = (
        signal["symbol"],
        signal["price"],
        signal["direction"],
        signal["confidence_level"],
        signal["timeframe"],
        signal["strategy"],
        signal["category"],
        signal["analysis"],
        signal["created_at"],
        signal["entry_price"],
        signal["stop_loss"],
        signal["target_price"],
        signal["risk_reward"],
        signal["setup_type"],
        signal["technical_analysis"],
        signal["support_level"],
        signal["resistance_level"],
        signal["rsi"],
        signal["trend"],
        signal["trend_strength"],
        signal["volatility"],
        signal["options_signal"],
        signal["options_analysis"],
        signal["trading_specialist_signal"],
        signal["trading_specialist_confidence"],
        signal["sentiment"],
        signal["sentiment_score"],
        signal["latest_news"],
        signal["news_source"],
        signal["additional_news"],
        signal["expert_analysis"],
        signal["recommendation"],
        signal["mtf_analysis"],
        signal["daily_trend"],
        signal["weekly_trend"],
        signal["monthly_trend"],
        signal["bullish_indicators"],
        signal["bearish_indicators"],
        signal["is_high_confidence"],
    )
    
    # Ejecutar consulta
    cursor.execute(query, params)
    conn.commit()
    
    # Obtener ID insertado
    signal_id = cursor.lastrowid
    print(f"Señal guardada con ID: {signal_id}")
    
    # Verificar la señal guardada
    cursor.execute(f"SELECT * FROM trading_signals WHERE id = {signal_id}")
    result = cursor.fetchone()
    
    # Convertir a diccionario
    columns = [col[0] for col in cursor.description]
    saved_signal = dict(zip(columns, result))
    
    # Imprimir resultado
    print(json.dumps(saved_signal, default=str, indent=2))
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}")
