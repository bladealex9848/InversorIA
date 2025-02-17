import openai
import logging
import json
from typing import List, Dict

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def process_tool_calls(tool_calls: List[Dict], symbol: str) -> List[Dict]:
    """Procesa llamadas a herramientas"""
    try:
        responses = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if function_name == "analyze_technical":
                response = analyze_technical(arguments["symbol"])
            elif function_name == "get_multi_timeframe_analysis":
                response = get_multi_timeframe_analysis(arguments["symbol"])
            else:
                response = {"status": "error", "message": f"Función {function_name} no implementada"}

            responses.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(response)
            })

        return responses

    except Exception as e:
        logger.error(f"Error en process_tool_calls: {str(e)}")
        return []

def analyze_technical(symbol: str) -> Dict:
    """Obtiene análisis técnico actualizado"""
    try:
        from market_utils import get_market_context
        context = get_market_context(symbol)
        if context:
            return {
                "status": "success",
                "data": {
                    "last_price": context["last_price"],
                    "change": context["change"],
                    "signals": context["signals"]
                }
            }
        return {"status": "error", "message": "Error obteniendo contexto del mercado"}
    except Exception as e:
        logger.error(f"Error en analyze_technical: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_multi_timeframe_analysis(symbol: str) -> Dict:
    """Análisis en múltiples timeframes"""
    try:
        from market_utils import fetch_market_data, TechnicalAnalyzer
        timeframes = ["1d", "1wk", "1mo"]
        analysis_multi = {}

        for tf in timeframes:
            data = fetch_market_data(symbol, "1y", tf)
            if data is not None:
                if len(data) < 20:
                    return {"status": "error", "message": f"Se requieren al menos 20 períodos para análisis en el timeframe {tf}"}
                analyzer = TechnicalAnalyzer(data)
                analyzer.calculate_indicators()  # Actualiza los datos con indicadores
                analysis_multi[tf] = analyzer.get_current_signals()

        return {"status": "success", "data": analysis_multi}
    except Exception as e:
        logger.error(f"Error en get_multi_timeframe_analysis: {str(e)}")
        return {"status": "error", "message": str(e)}

# Definición de herramientas
tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_technical",
            "description": "Obtiene análisis técnico actualizado",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Símbolo a analizar"
                    }
                },
                "required": ["symbol"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_multi_timeframe_analysis",
            "description": "Análisis en múltiples timeframes",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Símbolo a analizar"
                    }
                },
                "required": ["symbol"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]