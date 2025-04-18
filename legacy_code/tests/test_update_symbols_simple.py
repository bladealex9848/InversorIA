import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test")
logger.setLevel(logging.DEBUG)

# Asegurar que los mensajes se muestren en la consola
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

print("Iniciando prueba...")
logger.debug("Este es un mensaje de debug")
logger.info("Este es un mensaje de info")
logger.warning("Este es un mensaje de warning")
logger.error("Este es un mensaje de error")
print("Prueba finalizada")
