"""
InversorIA Pro - Datos de Empresas y Símbolos
---------------------------------------------
Este archivo contiene información sobre empresas y símbolos utilizados en la plataforma.
"""

import logging

logger = logging.getLogger(__name__)

# Información de símbolos y nombres completos
COMPANY_INFO = {
    # Tecnología
    "AAPL": {
        "name": "Apple Inc.",
        "sector": "Tecnología",
        "description": "Fabricante de dispositivos electrónicos y software",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "sector": "Tecnología",
        "description": "Empresa de software y servicios en la nube",
    },
    "GOOGL": {
        "name": "Alphabet Inc. (Google)",
        "sector": "Tecnología",
        "description": "Conglomerado especializado en productos y servicios de Internet",
    },
    "AMZN": {
        "name": "Amazon.com Inc.",
        "sector": "Consumo Discrecional",
        "description": "Comercio electrónico y servicios en la nube",
    },
    "TSLA": {
        "name": "Tesla Inc.",
        "sector": "Automóviles",
        "description": "Fabricante de vehículos eléctricos y tecnología de energía limpia",
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "sector": "Tecnología",
        "description": "Fabricante de unidades de procesamiento gráfico",
    },
    "META": {
        "name": "Meta Platforms Inc.",
        "sector": "Tecnología",
        "description": "Empresa de redes sociales y tecnología",
    },
    "NFLX": {
        "name": "Netflix Inc.",
        "sector": "Comunicación",
        "description": "Servicio de streaming y producción de contenido",
    },
    "PYPL": {
        "name": "PayPal Holdings Inc.",
        "sector": "Servicios Financieros",
        "description": "Plataforma de pagos en línea",
    },
    "CRM": {
        "name": "Salesforce Inc.",
        "sector": "Tecnología",
        "description": "Software de gestión de relaciones con clientes",
    },
    # Finanzas
    "JPM": {
        "name": "JPMorgan Chase & Co.",
        "sector": "Finanzas",
        "description": "Banco multinacional y servicios financieros",
    },
    "BAC": {
        "name": "Bank of America Corp.",
        "sector": "Finanzas",
        "description": "Institución bancaria multinacional",
    },
    "WFC": {
        "name": "Wells Fargo & Co.",
        "sector": "Finanzas",
        "description": "Servicios bancarios y financieros",
    },
    "C": {
        "name": "Citigroup Inc.",
        "sector": "Finanzas",
        "description": "Banca de inversión y servicios financieros",
    },
    "GS": {
        "name": "Goldman Sachs Group Inc.",
        "sector": "Finanzas",
        "description": "Banca de inversión y gestión de activos",
    },
    "MS": {
        "name": "Morgan Stanley",
        "sector": "Finanzas",
        "description": "Servicios financieros y banca de inversión",
    },
    "V": {
        "name": "Visa Inc.",
        "sector": "Finanzas",
        "description": "Servicios de pagos electrónicos",
    },
    "MA": {
        "name": "Mastercard Inc.",
        "sector": "Finanzas",
        "description": "Tecnología de pagos globales",
    },
    "AXP": {
        "name": "American Express Co.",
        "sector": "Finanzas",
        "description": "Servicios financieros y tarjetas de crédito",
    },
    "BLK": {
        "name": "BlackRock Inc.",
        "sector": "Finanzas",
        "description": "Gestión de inversiones y servicios financieros",
    },
    # ETFs e Índices
    "SPY": {
        "name": "SPDR S&P 500 ETF Trust",
        "sector": "ETF",
        "description": "ETF que sigue el índice S&P 500",
    },
    "QQQ": {
        "name": "Invesco QQQ Trust",
        "sector": "ETF",
        "description": "ETF que sigue el índice Nasdaq-100",
    },
    "DIA": {
        "name": "SPDR Dow Jones Industrial Average ETF",
        "sector": "ETF",
        "description": "ETF que sigue el índice Dow Jones Industrial Average",
    },
    "IWM": {
        "name": "iShares Russell 2000 ETF",
        "sector": "ETF",
        "description": "ETF que sigue el índice Russell 2000 de small caps",
    },
    "EFA": {
        "name": "iShares MSCI EAFE ETF",
        "sector": "ETF",
        "description": "ETF que sigue acciones internacionales desarrolladas",
    },
    "VWO": {
        "name": "Vanguard FTSE Emerging Markets ETF",
        "sector": "ETF",
        "description": "ETF que sigue mercados emergentes",
    },
    "XLE": {
        "name": "Energy Select Sector SPDR Fund",
        "sector": "ETF",
        "description": "ETF del sector energético",
    },
    "XLF": {
        "name": "Financial Select Sector SPDR Fund",
        "sector": "ETF",
        "description": "ETF del sector financiero",
    },
    "XLV": {
        "name": "Health Care Select Sector SPDR Fund",
        "sector": "ETF",
        "description": "ETF del sector sanitario",
    },
    # Energía
    "XOM": {
        "name": "Exxon Mobil Corp.",
        "sector": "Energía",
        "description": "Compañía integrada de petróleo y gas",
    },
    "CVX": {
        "name": "Chevron Corporation",
        "sector": "Energía",
        "description": "Producción y refinación de petróleo",
    },
    "SHEL": {
        "name": "Shell PLC",
        "sector": "Energía",
        "description": "Multinacional energética integrada",
    },
    "TTE": {
        "name": "TotalEnergies SE",
        "sector": "Energía",
        "description": "Compañía energética multinacional",
    },
    "COP": {
        "name": "ConocoPhillips",
        "sector": "Energía",
        "description": "Exploración y producción de petróleo y gas",
    },
    "EOG": {
        "name": "EOG Resources Inc.",
        "sector": "Energía",
        "description": "Exploración y producción de petróleo",
    },
    "PXD": {
        "name": "Pioneer Natural Resources Co.",
        "sector": "Energía",
        "description": "Compañía de exploración y producción de petróleo",
    },
    "DVN": {
        "name": "Devon Energy Corp.",
        "sector": "Energía",
        "description": "Compañía independiente de petróleo y gas",
    },
    "MPC": {
        "name": "Marathon Petroleum Corp.",
        "sector": "Energía",
        "description": "Refinación y comercialización de petróleo",
    },
    "PSX": {
        "name": "Phillips 66",
        "sector": "Energía",
        "description": "Refinación de petróleo y productos químicos",
    },
    # Salud
    "JNJ": {
        "name": "Johnson & Johnson",
        "sector": "Salud",
        "description": "Productos farmacéuticos y dispositivos médicos",
    },
    "UNH": {
        "name": "UnitedHealth Group Inc.",
        "sector": "Salud",
        "description": "Seguros médicos y servicios de salud",
    },
    "PFE": {
        "name": "Pfizer Inc.",
        "sector": "Salud",
        "description": "Farmacéutica multinacional",
    },
    "MRK": {
        "name": "Merck & Co Inc.",
        "sector": "Salud",
        "description": "Compañía farmacéutica global",
    },
    "ABBV": {
        "name": "AbbVie Inc.",
        "sector": "Salud",
        "description": "Biotecnología y productos farmacéuticos",
    },
    "LLY": {
        "name": "Eli Lilly and Co.",
        "sector": "Salud",
        "description": "Farmacéutica especializada en medicamentos innovadores",
    },
    "AMGN": {
        "name": "Amgen Inc.",
        "sector": "Salud",
        "description": "Biotecnología y terapias médicas",
    },
    "BMY": {
        "name": "Bristol-Myers Squibb Co.",
        "sector": "Salud",
        "description": "Compañía biofarmacéutica global",
    },
    "GILD": {
        "name": "Gilead Sciences Inc.",
        "sector": "Salud",
        "description": "Biotecnología especializada en antivirales",
    },
    "TMO": {
        "name": "Thermo Fisher Scientific Inc.",
        "sector": "Salud",
        "description": "Equipamiento científico y servicios de laboratorio",
    },
    # Consumo Discrecional
    "MCD": {
        "name": "McDonald's Corp.",
        "sector": "Consumo Discrecional",
        "description": "Cadena mundial de restaurantes de comida rápida",
    },
    "SBUX": {
        "name": "Starbucks Corp.",
        "sector": "Consumo Discrecional",
        "description": "Cadena internacional de cafeterías",
    },
    "NKE": {
        "name": "Nike Inc.",
        "sector": "Consumo Discrecional",
        "description": "Fabricante de calzado y ropa deportiva",
    },
    "TGT": {
        "name": "Target Corporation",
        "sector": "Consumo Discrecional",
        "description": "Cadena minorista de grandes almacenes",
    },
    "HD": {
        "name": "Home Depot Inc.",
        "sector": "Consumo Discrecional",
        "description": "Minorista de mejoras para el hogar",
    },
    "LOW": {
        "name": "Lowe's Companies Inc.",
        "sector": "Consumo Discrecional",
        "description": "Minorista de artículos para el hogar",
    },
    "TJX": {
        "name": "TJX Companies Inc.",
        "sector": "Consumo Discrecional",
        "description": "Minorista de ropa y artículos para el hogar",
    },
    "ROST": {
        "name": "Ross Stores Inc.",
        "sector": "Consumo Discrecional",
        "description": "Minorista de descuento de ropa y hogar",
    },
    "CMG": {
        "name": "Chipotle Mexican Grill Inc.",
        "sector": "Consumo Discrecional",
        "description": "Cadena de restaurantes de comida rápida mexicana",
    },
    "DHI": {
        "name": "D.R. Horton Inc.",
        "sector": "Consumo Discrecional",
        "description": "Constructora residencial",
    },
    # Cripto ETFs
    "BITO": {
        "name": "ProShares Bitcoin Strategy ETF",
        "sector": "Cripto ETF",
        "description": "ETF vinculado a futuros de Bitcoin",
    },
    "GBTC": {
        "name": "Grayscale Bitcoin Trust",
        "sector": "Cripto ETF",
        "description": "Fideicomiso de inversión en Bitcoin",
    },
    "ETHE": {
        "name": "Grayscale Ethereum Trust",
        "sector": "Cripto ETF",
        "description": "Fideicomiso de inversión en Ethereum",
    },
    "ARKW": {
        "name": "ARK Next Generation Internet ETF",
        "sector": "Cripto ETF",
        "description": "ETF con exposición a blockchain y cripto",
    },
    "BLOK": {
        "name": "Amplify Transformational Data Sharing ETF",
        "sector": "Cripto ETF",
        "description": "ETF enfocado en tecnologías blockchain",
    },
    # Materias Primas
    "GLD": {
        "name": "SPDR Gold Shares",
        "sector": "Materias Primas",
        "description": "ETF respaldado por oro físico",
    },
    "SLV": {
        "name": "iShares Silver Trust",
        "sector": "Materias Primas",
        "description": "ETF respaldado por plata física",
    },
    "USO": {
        "name": "United States Oil Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado al precio del petróleo",
    },
    "UNG": {
        "name": "United States Natural Gas Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado al precio del gas natural",
    },
    "CORN": {
        "name": "Teucrium Corn Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado a futuros de maíz",
    },
    "SOYB": {
        "name": "Teucrium Soybean Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado a futuros de soja",
    },
    "WEAT": {
        "name": "Teucrium Wheat Fund",
        "sector": "Materias Primas",
        "description": "ETF vinculado a futuros de trigo",
    },
    # Volatilidad
    "VXX": {
        "name": "iPath Series B S&P 500 VIX Short-Term Futures ETN",
        "sector": "Volatilidad",
        "description": "Vinculado a futuros de VIX a corto plazo",
    },
    "UVXY": {
        "name": "ProShares Ultra VIX Short-Term Futures ETF",
        "sector": "Volatilidad",
        "description": "ETF apalancado vinculado al VIX",
    },
    "SVXY": {
        "name": "ProShares Short VIX Short-Term Futures ETF",
        "sector": "Volatilidad",
        "description": "ETF inverso vinculado al VIX",
    },
    "VIXY": {
        "name": "ProShares VIX Short-Term Futures ETF",
        "sector": "Volatilidad",
        "description": "Exposición directa a futuros del VIX",
    },
    # Forex (Principales pares por volumen)
    "EURUSD": {
        "name": "Euro/Dólar Estadounidense",
        "sector": "Forex",
        "description": "Par más negociado del mundo",
    },
}

# Universo de Trading
SYMBOLS = {
    "Índices": ["SPY", "QQQ", "DIA", "IWM", "EFA", "VWO", "IYR", "XLE", "XLF", "XLV"],
    "Tecnología": [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "TSLA",
        "NVDA",
        "META",
        "NFLX",
        "PYPL",
        "CRM",
    ],
    "Finanzas": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK"],
    "Energía": ["XOM", "CVX", "SHEL", "TTE", "COP", "EOG", "PXD", "DVN", "MPC", "PSX"],
    "Salud": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "AMGN", "BMY", "GILD", "TMO"],
    "Consumo Discrecional": [
        "MCD",
        "SBUX",
        "NKE",
        "TGT",
        "HD",
        "LOW",
        "TJX",
        "ROST",
        "CMG",
        "DHI",
    ],
    "Cripto ETFs": ["BITO", "GBTC", "ETHE", "ARKW", "BLOK"],
    "Materias Primas": ["GLD", "SLV", "USO", "UNG", "CORN", "SOYB", "WEAT"],
    "Bonos": ["AGG", "BND", "IEF", "TLT", "LQD", "HYG", "JNK", "TIP", "MUB", "SHY"],
    "Inmobiliario": [
        "VNQ",
        "XLRE",
        "IYR",
        "REIT",
        "HST",
        "EQR",
        "AVB",
        "PLD",
        "SPG",
        "AMT",
    ],
    "Volatilidad": ["VXX", "UVXY", "SVXY", "VIXY"],
    "Forex": [
        "EURUSD",
        "USDJPY",
        "GBPUSD",
        "USDCHF",
        "AUDUSD",
        "USDCAD",
        "NZDUSD",
        "EURGBP",
        "EURJPY",
        "GBPJPY",
        "USDCNH",
        "USDINR",
        "USDTRY",
    ],
}

def get_company_info(symbol):
    """Obtiene información completa de la empresa o activo"""
    # Si el símbolo está en nuestra base de datos de información de compañías
    if symbol in COMPANY_INFO:
        return COMPANY_INFO[symbol]

    # Información para símbolos no conocidos explícitamente
    # Determinar a qué categoría pertenece
    category = None
    for cat, symbols in SYMBOLS.items():
        if symbol in symbols:
            category = cat
            break

    if not category:
        category = "No categorizado"

    # Crear información básica
    return {
        "name": f"{symbol}",
        "sector": category,
        "description": f"Activo financiero negociado bajo el símbolo {symbol}",
    }
