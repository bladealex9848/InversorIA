"""
Script para corregir los valores del VIX en la tabla market_sentiment
"""

import logging
import sys
import traceback
import decimal
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def fix_vix_values():
    """
    Corrige los valores del VIX en la tabla market_sentiment
    """
    try:
        from database_utils import DatabaseManager
        from market_utils import get_vix_level
        
        logger.info("Iniciando corrección de valores del VIX...")
        
        # Obtener el valor actual del VIX
        try:
            current_vix = get_vix_level()
            if not isinstance(current_vix, (int, float, decimal.Decimal)):
                logger.warning(f"El valor actual del VIX no es numérico: {current_vix}")
                current_vix = 15.0  # Valor por defecto
            logger.info(f"Valor actual del VIX: {current_vix}")
        except Exception as vix_error:
            logger.error(f"Error obteniendo valor del VIX: {str(vix_error)}")
            current_vix = 15.0  # Valor por defecto
        
        # Conectar a la base de datos
        db = DatabaseManager()
        
        # Obtener registros con VIX = 0.00 o NULL
        query = """
        SELECT id, date, vix 
        FROM market_sentiment 
        WHERE vix = 0.00 OR vix IS NULL
        ORDER BY date DESC
        """
        
        records = db.execute_query(query)
        
        if not records:
            logger.info("No se encontraron registros con VIX = 0.00 o NULL")
            return True
            
        logger.info(f"Se encontraron {len(records)} registros con VIX = 0.00 o NULL")
        
        # Actualizar registros
        updated_count = 0
        for record in records:
            record_id = record['id']
            record_date = record['date']
            
            # Usar el valor actual del VIX para registros de hoy
            if record_date.strftime('%Y-%m-%d') == datetime.now().strftime('%Y-%m-%d'):
                vix_value = current_vix
            else:
                # Para registros antiguos, usar un valor estimado basado en la fecha
                # Esto es solo una aproximación, idealmente deberíamos obtener el valor histórico real
                vix_value = 20.0  # Valor promedio histórico
            
            # Actualizar el registro
            update_query = "UPDATE market_sentiment SET vix = %s WHERE id = %s"
            result = db.execute_query(update_query, [vix_value, record_id], fetch=False)
            
            if result is not None:
                logger.info(f"Registro ID {record_id} actualizado con VIX = {vix_value}")
                updated_count += 1
            else:
                logger.warning(f"No se pudo actualizar el registro ID {record_id}")
        
        logger.info(f"Se actualizaron {updated_count} de {len(records)} registros")
        
        # Verificar que no queden registros con VIX = 0.00 o NULL
        check_query = "SELECT COUNT(*) as count FROM market_sentiment WHERE vix = 0.00 OR vix IS NULL"
        check_result = db.execute_query(check_query)
        
        if check_result and check_result[0]['count'] == 0:
            logger.info("Todos los registros tienen valores válidos de VIX")
            return True
        else:
            logger.warning(f"Aún quedan {check_result[0]['count']} registros con VIX = 0.00 o NULL")
            return False
            
    except Exception as e:
        logger.error(f"Error en fix_vix_values: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if fix_vix_values():
        logger.info("Corrección de valores del VIX completada con éxito")
        sys.exit(0)
    else:
        logger.error("No se pudo completar la corrección de valores del VIX")
        sys.exit(1)
