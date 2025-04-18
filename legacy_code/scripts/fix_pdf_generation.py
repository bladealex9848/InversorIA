"""
Script para corregir los errores de generación de PDF con wkhtmltopdf
"""

import logging
import os
import sys
import traceback

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def fix_pdf_generation():
    """
    Corrige los problemas con la generación de PDF
    """
    try:
        # Verificar si pdfkit está instalado
        try:
            import pdfkit
            logger.info("pdfkit está instalado")
        except ImportError:
            logger.warning("pdfkit no está instalado. Instalando...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfkit"])
            logger.info("pdfkit instalado correctamente")
            import pdfkit
        
        # Buscar archivos que usan pdfkit
        files_to_check = [
            "email_utils.py",
            "pdf_generator.py",
            "bulletin_generator.py",
            "newsletter_utils.py"
        ]
        
        modified_files = []
        
        for file_path in files_to_check:
            if not os.path.exists(file_path):
                continue
                
            logger.info(f"Revisando archivo: {file_path}")
            
            # Leer el contenido del archivo
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Verificar si el archivo usa pdfkit
            if "import pdfkit" in content or "from pdfkit" in content:
                logger.info(f"El archivo {file_path} usa pdfkit")
                
                # Modificar el código para manejar mejor los errores de wkhtmltopdf
                new_content = content
                
                # Reemplazar la configuración de pdfkit
                if "pdfkit.configuration" in content:
                    logger.info(f"Modificando configuración de pdfkit en {file_path}")
                    
                    # Agregar código para manejar la ausencia de wkhtmltopdf
                    config_code = """
    # Intentar configurar pdfkit con manejo de errores mejorado
    pdf_config = None
    try:
        # Intentar encontrar wkhtmltopdf en diferentes ubicaciones
        wkhtmltopdf_paths = [
            '/usr/local/bin/wkhtmltopdf',
            '/usr/bin/wkhtmltopdf',
            'C:\\\\Program Files\\\\wkhtmltopdf\\\\bin\\\\wkhtmltopdf.exe',
            'wkhtmltopdf'  # Buscar en PATH
        ]
        
        for path in wkhtmltopdf_paths:
            if os.path.exists(path) or (path == 'wkhtmltopdf'):
                pdf_config = pdfkit.configuration(wkhtmltopdf=path)
                logger.info(f"wkhtmltopdf encontrado en: {path}")
                break
                
        if not pdf_config:
            # Si no se encuentra wkhtmltopdf, usar configuración por defecto
            pdf_config = pdfkit.configuration()
            logger.warning("No se encontró wkhtmltopdf, usando configuración por defecto")
    except Exception as config_error:
        logger.warning(f"Error configurando pdfkit: {str(config_error)}")
        # Continuar sin configuración
        pdf_config = None
"""
                    
                    # Buscar dónde se configura pdfkit
                    import re
                    config_pattern = r'(config|configuration)\s*=\s*pdfkit\.configuration\([^\)]*\)'
                    match = re.search(config_pattern, content)
                    
                    if match:
                        # Reemplazar la configuración existente
                        new_content = content.replace(match.group(0), "pdf_config = None" + config_code)
                    else:
                        # Agregar la configuración después de la importación de pdfkit
                        import_pattern = r'import\s+pdfkit'
                        new_content = re.sub(import_pattern, "import pdfkit\nimport os" + config_code, content)
                
                # Modificar las llamadas a pdfkit.from_string y pdfkit.from_file
                if "pdfkit.from_string" in content or "pdfkit.from_file" in content:
                    logger.info(f"Modificando llamadas a pdfkit en {file_path}")
                    
                    # Reemplazar pdfkit.from_string
                    new_content = new_content.replace(
                        "pdfkit.from_string(html, output_path",
                        "pdfkit.from_string(html, output_path, configuration=pdf_config"
                    )
                    
                    # Reemplazar pdfkit.from_file
                    new_content = new_content.replace(
                        "pdfkit.from_file(html_file, output_path",
                        "pdfkit.from_file(html_file, output_path, configuration=pdf_config"
                    )
                
                # Guardar los cambios si se modificó el contenido
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    logger.info(f"Archivo {file_path} modificado")
                    modified_files.append(file_path)
        
        # Verificar si se modificaron archivos
        if modified_files:
            logger.info(f"Se modificaron {len(modified_files)} archivos: {', '.join(modified_files)}")
            return True
        else:
            logger.warning("No se encontraron archivos que usen pdfkit para modificar")
            
            # Si no se encontraron archivos existentes, crear un nuevo archivo de utilidad
            utility_file = "pdf_utils.py"
            logger.info(f"Creando archivo de utilidad {utility_file}")
            
            utility_content = """
import os
import logging
import traceback

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def generate_pdf(html_content, output_path, options=None):
    \"\"\"
    Genera un PDF a partir de contenido HTML con manejo mejorado de errores
    
    Args:
        html_content (str): Contenido HTML
        output_path (str): Ruta de salida del PDF
        options (dict, optional): Opciones para pdfkit
        
    Returns:
        bool: True si se generó correctamente, False en caso contrario
    \"\"\"
    try:
        import pdfkit
        
        # Intentar encontrar wkhtmltopdf en diferentes ubicaciones
        wkhtmltopdf_paths = [
            '/usr/local/bin/wkhtmltopdf',
            '/usr/bin/wkhtmltopdf',
            'C:\\\\Program Files\\\\wkhtmltopdf\\\\bin\\\\wkhtmltopdf.exe',
            'wkhtmltopdf'  # Buscar en PATH
        ]
        
        pdf_config = None
        for path in wkhtmltopdf_paths:
            if os.path.exists(path) or (path == 'wkhtmltopdf'):
                try:
                    pdf_config = pdfkit.configuration(wkhtmltopdf=path)
                    logger.info(f"wkhtmltopdf encontrado en: {path}")
                    break
                except Exception:
                    continue
        
        # Si no se pudo configurar, intentar sin configuración
        if not pdf_config:
            logger.warning("No se pudo configurar wkhtmltopdf, intentando sin configuración")
        
        # Opciones por defecto si no se proporcionan
        if options is None:
            options = {
                'page-size': 'Letter',
                'encoding': 'UTF-8',
                'no-outline': None,
                'quiet': ''
            }
        
        # Intentar generar el PDF con configuración
        try:
            if pdf_config:
                pdfkit.from_string(html_content, output_path, options=options, configuration=pdf_config)
            else:
                pdfkit.from_string(html_content, output_path, options=options)
            
            logger.info(f"PDF generado correctamente: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error generando PDF: {str(e)}")
            
            # Intentar con opciones básicas
            logger.info("Intentando generar PDF con opciones básicas...")
            try:
                basic_options = {'quiet': ''}
                if pdf_config:
                    pdfkit.from_string(html_content, output_path, options=basic_options, configuration=pdf_config)
                else:
                    pdfkit.from_string(html_content, output_path, options=basic_options)
                
                logger.info(f"PDF generado con opciones básicas: {output_path}")
                return True
            except Exception as basic_error:
                logger.error(f"Error al generar PDF con opciones básicas: {str(basic_error)}")
                
                # Último intento: guardar el HTML directamente
                try:
                    html_path = output_path.replace('.pdf', '.html')
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"No se pudo generar PDF, pero se guardó el HTML: {html_path}")
                except Exception as html_error:
                    logger.error(f"Error guardando HTML: {str(html_error)}")
                
                return False
    
    except ImportError:
        logger.error("pdfkit no está instalado. Instálalo con: pip install pdfkit")
        
        # Guardar el HTML como alternativa
        try:
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"No se pudo generar PDF (pdfkit no instalado), pero se guardó el HTML: {html_path}")
        except Exception as html_error:
            logger.error(f"Error guardando HTML: {str(html_error)}")
        
        return False
    except Exception as e:
        logger.error(f"Error inesperado generando PDF: {str(e)}")
        traceback.print_exc()
        return False
"""
            
            with open(utility_file, 'w', encoding='utf-8') as file:
                file.write(utility_content)
            
            logger.info(f"Archivo de utilidad {utility_file} creado correctamente")
            return True
            
    except Exception as e:
        logger.error(f"Error en fix_pdf_generation: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if fix_pdf_generation():
        logger.info("Corrección de generación de PDF aplicada con éxito")
        sys.exit(0)
    else:
        logger.error("No se pudo aplicar la corrección de generación de PDF")
        sys.exit(1)
