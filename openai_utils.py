import json
import logging
from market_utils import get_market_context, fetch_market_data, TechnicalAnalyzer

logger = logging.getLogger(__name__)

def process_tool_calls(tool_calls, current_symbol=None):
    """Procesa llamadas a funciones con mejor manejo de errores"""
    responses = []
    for tool_call in tool_calls:
        try:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Usar símbolo actual si no se especifica
            symbol = function_args.get("symbol", current_symbol)
            if not symbol:
                raise ValueError("No se especificó símbolo")
            
            if function_name == "analyze_technical":
                context = get_market_context(symbol)
                if context:
                    response = {
                        "status": "success",
                        "data": context
                    }
                else:
                    response = {
                        "status": "error",
                        "message": f"No se pudieron obtener datos para {symbol}"
                    }
                    
            elif function_name == "get_multi_timeframe_analysis":
                timeframes = ["1d", "1wk", "1mo"]
                analysis = {}
                
                for tf in timeframes:
                    data = fetch_market_data(symbol, "1y", tf)
                    if data is not None:
                        analyzer = TechnicalAnalyzer(data)
                        df = analyzer.calculate_indicators()
                        if df is not None:
                            signals = analyzer.get_current_signals()
                            if signals:
                                analysis[tf] = signals
                
                if analysis:
                    response = {
                        "status": "success",
                        "data": analysis
                    }
                else:
                    response = {
                        "status": "error",
                        "message": "No se pudo completar el análisis multitemporal"
                    }
                    
            else:
                response = {
                    "status": "error",
                    "message": f"Función {function_name} no implementada"
                }
            
            responses.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(response)
            })
            
        except Exception as e:
            logger.error(f"Error en process_tool_calls: {str(e)}")
            responses.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps({
                    "status": "error",
                    "message": str(e)
                })
            })
            
    return responses

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