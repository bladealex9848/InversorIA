
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
    """
    Genera un PDF a partir de contenido HTML con manejo mejorado de errores
    
    Args:
        html_content (str): Contenido HTML
        output_path (str): Ruta de salida del PDF
        options (dict, optional): Opciones para pdfkit
        
    Returns:
        bool: True si se generó correctamente, False en caso contrario
    """
    try:
        import pdfkit
        
        # Intentar encontrar wkhtmltopdf en diferentes ubicaciones
        wkhtmltopdf_paths = [
            '/usr/local/bin/wkhtmltopdf',
            '/usr/bin/wkhtmltopdf',
            'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe',
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
