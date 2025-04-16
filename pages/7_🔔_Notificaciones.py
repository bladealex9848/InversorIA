import streamlit as st
import pandas as pd
import numpy as np
import logging
import socket
import time
import smtplib
import mysql.connector
import sys
import os
import io
import decimal
import tempfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Intentar importar pdfkit para la generación de PDF
try:
    import pdfkit

    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    logging.warning(
        "pdfkit no está instalado. La funcionalidad de PDF no estará disponible."
    )

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configurar nivel de logging para bibliotecas externas
logging.getLogger("mysql").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)
logging.getLogger("streamlit").setLevel(logging.INFO)

# Verificación de autenticación
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.title("🔒 Acceso Restringido")
    st.warning("Por favor, inicie sesión desde la página principal del sistema.")
    st.stop()

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Notificaciones",
    layout="wide",
    page_icon="🔔",
    initial_sidebar_state="expanded",
)

# Título principal
st.title("🔔 Sistema de Notificaciones y Seguimiento")

# Barra lateral para configuración
with st.sidebar:
    st.header("Configuración")

    # Filtros para señales
    st.subheader("Filtros de Señales")
    categoria = st.selectbox(
        "Categoría",
        [
            "Todas",
            "Tecnología",
            "Finanzas",
            "Salud",
            "Energía",
            "Consumo",
            "Índices",
            "Materias Primas",
        ],
    )

    confianza = st.multiselect(
        "Nivel de Confianza", ["Alta", "Media", "Baja"], default=["Alta", "Media"]
    )

    direccion = st.selectbox(
        "Dirección",
        ["Todas", "CALL", "PUT", "NEUTRAL"],
        help="Filtra por dirección de la señal",
    )

    alta_confianza_only = st.checkbox(
        "Solo señales de alta confianza",
        help="Mostrar solo señales marcadas como alta confianza",
    )

    dias_atras = st.slider("Días a mostrar", min_value=1, max_value=30, value=7)

    # Configuración de correo
    st.subheader("Configuración de Correo")
    destinatarios = st.text_area(
        "Destinatarios (separados por coma)",
        placeholder="ejemplo@correo.com, otro@correo.com",
    )

    include_pdf = st.checkbox(
        "Incluir PDF del boletín",
        value=True,
        help="Adjunta una versión PDF del boletín al correo",
    )

    # Botón para limpiar caché
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.success("Caché limpiado correctamente")


# Añadir directorio raíz al path para importar módulos del proyecto principal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Clase para gestionar la conexión a la base de datos
class DatabaseManager:
    """Gestiona la conexión y operaciones con la base de datos MariaDB"""

    def __init__(self):
        """Inicializa el gestor de base de datos con credenciales desde secrets"""
        try:
            # Obtener credenciales desde secrets.toml
            self.db_config = {
                "host": st.secrets.get("db_host", "localhost"),
                "user": st.secrets.get("db_user", ""),
                "password": st.secrets.get("db_password", ""),
                "database": st.secrets.get("db_name", "inversoria"),
                "port": st.secrets.get("db_port", 3306),
            }
            self.connection = None
            logger.info("Configuración de base de datos inicializada")
        except Exception as e:
            logger.error(
                f"Error inicializando configuración de base de datos: {str(e)}"
            )
            self.db_config = None

    def connect(self):
        """Establece conexión con la base de datos"""
        if not self.db_config:
            return False

        try:
            # En modo desarrollo, simular conexión exitosa si no hay credenciales
            if not self.db_config.get("user") or not self.db_config.get("password"):
                logger.warning(
                    "Usando modo simulación para base de datos (no hay credenciales)"
                )
                return True

            self.connection = mysql.connector.connect(**self.db_config)
            return True
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {str(e)}")
            return False

    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexión a base de datos cerrada")

    def execute_query(self, query, params=None, fetch=True):
        """Ejecuta una consulta SQL y opcionalmente devuelve resultados"""
        # Validar que hay una consulta
        if not query:
            logger.error("No se especificó una consulta SQL")
            return None

        # Intentar conectar a la base de datos
        if not self.connect():
            logger.error("No se pudo conectar a la base de datos")
            return None

        try:
            # Verificar si estamos en modo sin conexión
            if not hasattr(self, "connection") or self.connection is None:
                logger.error("No hay conexión a la base de datos disponible")
                # Devolver lista vacía o error en lugar de datos simulados
                if "SELECT" in query.upper() and fetch:
                    logger.warning(
                        "Devolviendo lista vacía para consulta SELECT sin conexión"
                    )
                    return []
                else:
                    logger.warning(
                        "Devolviendo error para operación de escritura sin conexión"
                    )
                    return None

            # Ejecutar consulta real
            cursor = self.connection.cursor(dictionary=True)
            logger.info(f"Ejecutando consulta: {query}")
            logger.info(f"Parámetros: {params}")

            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
                logger.info(f"Consulta devuelve {len(result)} resultados")
            else:
                self.connection.commit()
                result = cursor.rowcount
                logger.info(f"Consulta afectó {result} filas")

            cursor.close()
            return result
        except mysql.connector.Error as e:
            logger.error(f"Error de MySQL: {str(e)}\nQuery: {query}")
            return None
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {str(e)}\nQuery: {query}")
            return None
        finally:
            self.disconnect()

    def get_signals(
        self,
        days_back=7,
        categories=None,
        confidence_levels=None,
        direction=None,
        high_confidence_only=False,
    ):
        """Obtiene señales de trading filtradas con todos los campos detallados"""
        query = """SELECT * FROM trading_signals
                  WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"""
        params = [days_back]

        # Añadir filtros adicionales
        if categories and "Todas" not in categories:
            placeholders = ", ".join(["%s"] * len(categories))
            query += f" AND category IN ({placeholders})"
            params.extend(categories)

        if confidence_levels and len(confidence_levels) > 0:
            placeholders = ", ".join(["%s"] * len(confidence_levels))
            query += f" AND confidence_level IN ({placeholders})"
            params.extend(confidence_levels)

        if direction and direction != "Todas":
            query += " AND direction = %s"
            params.append(direction)

        if high_confidence_only:
            query += " AND is_high_confidence = 1"

        query += " ORDER BY created_at DESC"

        return self.execute_query(query, params)

    def get_market_sentiment(self, days_back=7):
        """Obtiene sentimiento de mercado reciente"""
        query = """SELECT * FROM market_sentiment 
                  WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                  ORDER BY date DESC LIMIT 1"""
        params = [days_back]

        result = self.execute_query(query, params)

        # Convertir valores Decimal a float para evitar problemas
        if result and len(result) > 0:
            for key, value in result[0].items():
                if isinstance(value, decimal.Decimal):
                    result[0][key] = float(value)

        return result

    def get_market_news(self, days_back=7, limit=5):
        """Obtiene noticias de mercado recientes"""
        query = """SELECT * FROM market_news
                  WHERE DATE(news_date) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                  ORDER BY news_date DESC, impact DESC
                  LIMIT %s"""
        params = [days_back, limit]

        return self.execute_query(query, params)

    def get_detailed_analysis(self, symbol):
        """Obtiene análisis detallado para un símbolo específico"""
        query = """SELECT * FROM trading_signals
                  WHERE symbol = %s
                  ORDER BY created_at DESC
                  LIMIT 1"""
        params = [symbol]

        result = self.execute_query(query, params)

        # Convertir valores Decimal a float para evitar problemas
        if result and len(result) > 0:
            for key, value in result[0].items():
                if isinstance(value, decimal.Decimal):
                    result[0][key] = float(value)

        return result

    def save_signal(self, signal_data):
        """Guarda una nueva señal de trading en la base de datos"""
        # Creamos una versión básica para compatibilidad con señales existentes
        query = """INSERT INTO trading_signals
                  (symbol, price, direction, confidence_level, timeframe,
                   strategy, category, analysis, created_at)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())"""

        params = (
            signal_data.get("symbol"),
            signal_data.get("price"),
            signal_data.get("direction"),
            signal_data.get("confidence_level"),
            signal_data.get("timeframe"),
            signal_data.get("strategy"),
            signal_data.get("category"),
            signal_data.get("analysis"),
        )

        return self.execute_query(query, params, fetch=False)

    def log_email_sent(self, email_data):
        """Registra el envío de un correo electrónico"""
        query = """INSERT INTO email_logs
                  (recipients, subject, content_summary, signals_included, sent_at, status, error_message)
                  VALUES (%s, %s, %s, %s, NOW(), %s, %s)"""

        params = (
            email_data.get("recipients"),
            email_data.get("subject"),
            email_data.get("content_summary"),
            email_data.get("signals_included"),
            email_data.get("status", "success"),
            email_data.get("error_message"),
        )

        return self.execute_query(query, params, fetch=False)

    def save_market_sentiment(self, sentiment_data):
        """Guarda el sentimiento del mercado en la base de datos"""
        # Primero verificar si ya existe un registro para la fecha actual
        check_query = """SELECT id FROM market_sentiment WHERE date = CURDATE()"""
        result = self.execute_query(check_query)

        if result and len(result) > 0:
            # Si existe, actualizar el registro existente
            query = """UPDATE market_sentiment
                      SET overall = %s, vix = %s, sp500_trend = %s,
                          technical_indicators = %s, volume = %s, notes = %s
                      WHERE date = CURDATE()"""
            logger.info("Actualizando sentimiento del mercado existente para hoy")
        else:
            # Si no existe, insertar un nuevo registro
            query = """INSERT INTO market_sentiment
                      (date, overall, vix, sp500_trend, technical_indicators, volume, notes, created_at)
                      VALUES (CURDATE(), %s, %s, %s, %s, %s, %s, NOW())"""
            logger.info("Insertando nuevo sentimiento del mercado para hoy")

        params = (
            sentiment_data.get("overall"),
            sentiment_data.get("vix"),
            sentiment_data.get("sp500_trend"),
            sentiment_data.get("technical_indicators"),
            sentiment_data.get("volume"),
            sentiment_data.get("notes", "Generado automáticamente al enviar boletín"),
        )

        return self.execute_query(query, params, fetch=False)

    def save_market_news(self, news_data):
        """Guarda una noticia del mercado en la base de datos"""
        # Verificar si la noticia ya existe (por título)
        check_query = """SELECT id FROM market_news WHERE title = %s AND DATE(news_date) = CURDATE()"""
        result = self.execute_query(check_query, (news_data.get("title"),))

        if result and len(result) > 0:
            # Si existe, no hacer nada para evitar duplicados
            logger.info(
                f"La noticia '{news_data.get('title')}' ya existe en la base de datos"
            )
            return True

        # Si no existe, insertar la noticia
        query = """INSERT INTO market_news
                  (title, summary, source, url, news_date, impact, created_at)
                  VALUES (%s, %s, %s, %s, NOW(), %s, NOW())"""

        params = (
            news_data.get("title"),
            news_data.get("summary"),
            news_data.get("source"),
            news_data.get("url", ""),
            news_data.get("impact", "Medio"),
        )

        return self.execute_query(query, params, fetch=False)


# Clase para gestionar el envío de correos electrónicos
class EmailManager:
    """Gestiona el envío de correos electrónicos con boletines de trading"""

    def __init__(self):
        """Inicializa el gestor de correos con credenciales desde secrets"""
        try:
            # Obtener credenciales desde secrets.toml
            self.email_config = {
                "smtp_server": st.secrets.get("smtp_server", "smtp.gmail.com"),
                "smtp_port": st.secrets.get("smtp_port", 587),
                "email_user": st.secrets.get("email_user", ""),
                "email_password": st.secrets.get("email_password", ""),
                "email_from": st.secrets.get("email_from", ""),
            }
            logger.info("Configuración de correo electrónico inicializada")
        except Exception as e:
            logger.error(f"Error inicializando configuración de correo: {str(e)}")
            self.email_config = None

    def send_email(
        self, recipients, subject, html_content, pdf_attachment=None, images=None
    ):
        """Envía un correo electrónico con contenido HTML, PDF y opcionalmente imágenes"""
        # Validar que hay destinatarios
        if not recipients:
            logger.error("No se especificaron destinatarios para el correo")
            return False

        # Convertir a lista si es un string
        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.split(",") if r.strip()]

        # Validar configuración de correo
        if not self.email_config or not self.email_config.get("email_user"):
            logger.warning(
                "Configuración de correo no disponible, verificando secrets.toml"
            )
            # Intentar obtener credenciales nuevamente
            try:
                self.email_config = {
                    "smtp_server": st.secrets.get("smtp_server", "smtp.gmail.com"),
                    "smtp_port": st.secrets.get("smtp_port", 587),
                    "email_user": st.secrets.get("email_user", ""),
                    "email_password": st.secrets.get("email_password", ""),
                    "email_from": st.secrets.get("email_from", ""),
                }
                logger.info(
                    f"Credenciales de correo actualizadas: {self.email_config['email_user']}"
                )
            except Exception as e:
                logger.error(f"Error obteniendo credenciales de correo: {str(e)}")
                return False

        # Validar que hay credenciales
        if not self.email_config.get("email_user") or not self.email_config.get(
            "email_password"
        ):
            logger.error("Faltan credenciales de correo en secrets.toml")
            return False

        try:
            # Crear mensaje
            msg = MIMEMultipart("related")
            msg["Subject"] = subject
            msg["From"] = self.email_config.get("email_from") or self.email_config.get(
                "email_user"
            )
            msg["To"] = ", ".join(recipients)

            logger.info(f"Preparando correo para: {msg['To']}")

            # Crear parte alternativa para texto plano/HTML
            alt = MIMEMultipart("alternative")
            msg.attach(alt)

            # Añadir versión de texto plano (simplificada)
            text_plain = "Este correo contiene un boletín de trading de InversorIA Pro. Por favor, utilice un cliente de correo que soporte HTML para visualizarlo correctamente."
            text_part = MIMEText(text_plain, "plain")
            alt.attach(text_part)

            # Adjuntar contenido HTML
            html_part = MIMEText(html_content, "html")
            alt.attach(html_part)

            # Adjuntar PDF si existe
            if pdf_attachment:
                pdf_part = MIMEApplication(pdf_attachment, _subtype="pdf")
                pdf_part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename="InversorIA_Pro_Boletin_Trading.pdf",
                )
                msg.attach(pdf_part)
                logger.info("PDF adjuntado al correo")

            # Adjuntar imágenes si existen
            if images and isinstance(images, dict):
                for img_id, img_data in images.items():
                    image = MIMEImage(img_data)
                    image.add_header("Content-ID", f"<{img_id}>")
                    msg.attach(image)

            # Conectar al servidor SMTP con timeout
            logger.info(
                f"Conectando a servidor SMTP: {self.email_config.get('smtp_server')}:{self.email_config.get('smtp_port')}"
            )

            # Verificar si el puerto es 465 (SSL) o 587 (TLS)
            port = self.email_config.get("smtp_port")
            use_ssl = port == 465

            try:
                if use_ssl:
                    # Conexión SSL directa
                    logger.info("Usando conexión SSL")
                    server = smtplib.SMTP_SSL(
                        self.email_config.get("smtp_server"),
                        port,
                        timeout=10,  # Timeout de 10 segundos
                    )
                else:
                    # Conexión normal con STARTTLS
                    logger.info("Usando conexión con STARTTLS")
                    server = smtplib.SMTP(
                        self.email_config.get("smtp_server"),
                        port,
                        timeout=10,  # Timeout de 10 segundos
                    )
                    server.starttls()

                server.set_debuglevel(
                    1
                )  # Activar debug para ver la comunicación con el servidor
            except socket.timeout:
                logger.error(
                    f"Timeout al conectar con el servidor SMTP: {self.email_config.get('smtp_server')}:{port}"
                )
                return False
            except ConnectionRefusedError:
                logger.error(
                    f"Conexión rechazada por el servidor SMTP: {self.email_config.get('smtp_server')}:{port}"
                )
                return False

            # Intentar login
            logger.info(
                f"Iniciando sesión con usuario: {self.email_config.get('email_user')}"
            )
            server.login(
                self.email_config.get("email_user"),
                self.email_config.get("email_password"),
            )

            # Enviar correo con timeout
            logger.info("Enviando mensaje...")
            try:
                server.send_message(msg)
                server.quit()
                logger.info(f"Correo enviado exitosamente a {msg['To']}")
                return True
            except smtplib.SMTPServerDisconnected:
                logger.error("El servidor SMTP se desconectó durante el envío")
                return False
            except socket.timeout:
                logger.error("Timeout durante el envío del correo")
                return False
            except Exception as e:
                logger.error(f"Error durante el envío del correo: {str(e)}")
                return False

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {str(e)}")
            logger.error(
                "Verifica tu usuario y contraseña. Si usas Gmail, asegúrate de usar una 'Clave de aplicación'."
            )
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error enviando correo: {str(e)}")
            return False

    def create_newsletter_html(self, signals, market_sentiment, news_summary):
        """Crea el contenido HTML para el boletín de trading con diseño mejorado"""
        # Fecha actual formateada
        current_date = datetime.now().strftime("%d de %B de %Y")

        # Encabezado del boletín con diseño mejorado
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>InversorIA Pro - Boletín de Trading {current_date}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
                
                body {{ 
                    font-family: 'Roboto', Arial, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background-color: #f9f9f9;
                    padding: 0;
                }}
                
                .header {{ 
                    background: linear-gradient(135deg, #2c3e50 0%, #1a2a3a 100%);
                    color: white; 
                    padding: 30px 20px; 
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    letter-spacing: 0.5px;
                }}
                
                .header p {{
                    margin: 10px 0 0;
                    opacity: 0.9;
                    font-size: 16px;
                }}
                
                .content {{ 
                    background-color: white;
                    padding: 30px; 
                    border-radius: 0 0 8px 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                    margin-bottom: 20px;
                }}
                
                .section-title {{
                    color: #2c3e50;
                    border-bottom: 2px solid #eaeaea;
                    padding-bottom: 10px;
                    margin-top: 30px;
                    margin-bottom: 20px;
                    font-weight: 500;
                    font-size: 22px;
                    page-break-after: avoid;
                }}
                
                .footer {{ 
                    background-color: #f8f9fa; 
                    padding: 20px; 
                    text-align: center; 
                    font-size: 13px; 
                    color: #666; 
                    border-radius: 8px;
                    margin-top: 30px;
                }}
                
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 20px 0; 
                    box-shadow: 0 2px 3px rgba(0,0,0,0.03);
                    border-radius: 6px;
                    overflow: hidden;
                }}
                
                th {{ 
                    padding: 15px; 
                    text-align: left; 
                    background-color: #f2f6f9; 
                    color: #2c3e50;
                    font-weight: 500;
                    border: none;
                }}
                
                td {{ 
                    padding: 15px; 
                    text-align: left; 
                    border-bottom: 1px solid #f2f2f2; 
                }}
                
                tr:last-child td {{
                    border-bottom: none;
                }}
                
                .signal-high {{ background-color: rgba(212, 237, 218, 0.3); }}
                .signal-high:hover {{ background-color: rgba(212, 237, 218, 0.5); }}
                
                .signal-medium {{ background-color: rgba(255, 243, 205, 0.3); }}
                .signal-medium:hover {{ background-color: rgba(255, 243, 205, 0.5); }}
                
                .signal-low {{ background-color: rgba(248, 249, 250, 0.3); }}
                .signal-low:hover {{ background-color: rgba(248, 249, 250, 0.5); }}
                
                .buy {{ color: #28a745; font-weight: 500; }}
                .sell {{ color: #dc3545; font-weight: 500; }}
                .neutral {{ color: #6c757d; font-weight: 500; }}
                
                .card {{
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    page-break-inside: avoid;
                }}
                
                .sentiment {{ 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    page-break-inside: avoid;
                }}
                
                .sentiment-title {{
                    font-size: 18px;
                    margin-top: 0;
                    margin-bottom: 15px;
                    font-weight: 500;
                }}
                
                .sentiment-bullish {{ 
                    background-color: rgba(40, 167, 69, 0.1); 
                    border-left: 4px solid #28a745; 
                }}
                
                .sentiment-bearish {{ 
                    background-color: rgba(220, 53, 69, 0.1); 
                    border-left: 4px solid #dc3545; 
                }}
                
                .sentiment-neutral {{ 
                    background-color: rgba(108, 117, 125, 0.1); 
                    border-left: 4px solid #6c757d; 
                }}
                
                .news {{ 
                    background-color: white;
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    page-break-inside: avoid;
                }}
                
                .news-item {{
                    border-bottom: 1px solid #f2f2f2;
                    padding-bottom: 15px;
                    margin-bottom: 15px;
                }}
                
                .news-item:last-child {{
                    border-bottom: none;
                    padding-bottom: 0;
                    margin-bottom: 0;
                }}
                
                .news-title {{
                    color: #2c3e50;
                    margin-top: 0;
                    margin-bottom: 10px;
                    font-weight: 500;
                }}
                
                .news-meta {{
                    font-size: 12px;
                    color: #6c757d;
                }}
                
                .detailed-analysis {{ 
                    background-color: white; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    page-break-inside: avoid;
                }}
                
                .detailed-analysis-call {{
                    border-left: 4px solid #28a745;
                }}
                
                .detailed-analysis-put {{
                    border-left: 4px solid #dc3545;
                }}
                
                .detailed-analysis-neutral {{
                    border-left: 4px solid #6c757d;
                }}
                
                .detailed-analysis h3 {{ 
                    color: #2c3e50; 
                    margin-top: 0; 
                    font-weight: 500;
                }}
                
                .levels {{ 
                    display: flex; 
                    flex-wrap: wrap;
                    justify-content: space-between; 
                    margin: 15px 0; 
                }}
                
                .levels-column {{ 
                    flex: 0 0 48%;
                }}
                
                .level-title {{
                    font-weight: 500;
                    margin-bottom: 10px;
                    color: #2c3e50;
                }}
                
                .level-item {{ 
                    background-color: white; 
                    padding: 10px 15px; 
                    border-radius: 6px; 
                    margin-bottom: 8px; 
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                    font-weight: 500;
                }}
                
                .support {{ border-left: 3px solid #28a745; }}
                .resistance {{ border-left: 3px solid #dc3545; }}
                
                .pattern {{ 
                    background-color: rgba(0, 123, 255, 0.1); 
                    padding: 8px 12px; 
                    border-radius: 20px; 
                    display: inline-block; 
                    margin: 3px; 
                    font-size: 13px;
                    color: #007bff;
                }}
                
                .metrics-container {{
                    display: flex;
                    flex-wrap: wrap;
                    margin: 0 -10px;
                }}
                
                .metric-card {{
                    flex: 1 0 20%;
                    min-width: 180px;
                    background-color: white;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }}
                
                .metric-title {{
                    font-size: 14px;
                    color: #6c757d;
                    margin-bottom: 5px;
                }}
                
                .metric-value {{
                    font-size: 18px;
                    font-weight: 500;
                    color: #2c3e50;
                }}
                
                .indicators-section {{
                    background-color: #f8f9fa;
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 15px;
                }}
                
                .indicators-title {{
                    font-size: 16px;
                    font-weight: 500;
                    color: #2c3e50;
                    margin-top: 0;
                    margin-bottom: 10px;
                }}
                
                .indicators-grid {{
                    display: flex;
                    flex-wrap: wrap;
                }}
                
                .indicator {{
                    flex: 1 0 25%;
                    min-width: 120px;
                    padding: 8px;
                }}
                
                .analysis-box {{
                    background-color: rgba(0, 123, 255, 0.05);
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 15px;
                    border-left: 3px solid #007bff;
                }}
                
                .analysis-text {{
                    margin: 0;
                    line-height: 1.5;
                }}
                
                .company-info {{
                    background-color: #f8f9fa;
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 15px;
                }}
                
                .high-impact {{ color: #dc3545; font-weight: 500; }}
                .medium-impact {{ color: #fd7e14; font-weight: 500; }}
                .low-impact {{ color: #6c757d; font-weight: 500; }}
                
                .setup-badge {{
                    display: inline-block;
                    padding: 5px 10px;
                    background-color: #e9f5ff;
                    border-radius: 20px;
                    font-size: 13px;
                    color: #0275d8;
                    margin-right: 5px;
                    margin-bottom: 5px;
                }}
                
                .price-targets {{
                    display: flex;
                    flex-wrap: wrap;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                    margin-top: 20px;
                }}
                
                .price-target-item {{
                    flex: 1 0 30%;
                    min-width: 150px;
                    text-align: center;
                    padding: 10px;
                }}
                
                .price-target-title {{
                    font-size: 14px;
                    color: #6c757d;
                    margin-bottom: 5px;
                }}
                
                .price-target-value {{
                    font-size: 18px;
                    font-weight: 700;
                }}
                
                .price-target-value.entry {{
                    color: #0275d8;
                }}
                
                .price-target-value.stop {{
                    color: #dc3545;
                }}
                
                .price-target-value.target {{
                    color: #28a745;
                }}
                
                .risk-reward {{
                    display: inline-block;
                    padding: 5px 10px;
                    background-color: #f2f6f9;
                    border-radius: 5px;
                    margin-top: 5px;
                    font-weight: 500;
                }}
                
                .risk-reward.good {{
                    color: #28a745;
                }}
                
                .risk-reward.neutral {{
                    color: #6c757d;
                }}
                
                .risk-reward.poor {{
                    color: #dc3545;
                }}
                
                .trend-analysis {{
                    display: flex;
                    flex-wrap: wrap;
                    margin-top: 15px;
                    background-color: #f8f9fa;
                    border-radius: 6px;
                    padding: 15px;
                }}
                
                .trend-timeframe {{
                    flex: 1 0 30%;
                    min-width: 160px;
                    margin-bottom: 15px;
                }}
                
                .trend-title {{
                    font-size: 14px;
                    color: #6c757d;
                    margin-bottom: 5px;
                }}
                
                .trend-value {{
                    display: flex;
                    align-items: center;
                }}
                
                .trend-badge {{
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                
                .trend-badge.bullish {{
                    background-color: rgba(40, 167, 69, 0.1);
                    color: #28a745;
                }}
                
                .trend-badge.bearish {{
                    background-color: rgba(220, 53, 69, 0.1);
                    color: #dc3545;
                }}
                
                .trend-badge.neutral {{
                    background-color: rgba(108, 117, 125, 0.1);
                    color: #6c757d;
                }}
                
                .expert-analysis {{
                    background-color: rgba(25, 118, 210, 0.05);
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 20px;
                    border-left: 3px solid #1976d2;
                }}
                
                .expert-title {{
                    font-size: 16px;
                    font-weight: 500;
                    color: #1976d2;
                    margin-top: 0;
                    margin-bottom: 10px;
                }}
                
                .trading-specialist {{
                    background-color: rgba(40, 167, 69, 0.05);
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 20px;
                    border-left: 3px solid #28a745;
                }}
                
                .trading-specialist-title {{
                    font-size: 16px;
                    font-weight: 500;
                    color: #28a745;
                    margin-top: 0;
                    margin-bottom: 10px;
                }}
                
                .specialist-signal {{
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: 500;
                    margin-right: 10px;
                }}
                
                .specialist-signal.buy {{
                    background-color: rgba(40, 167, 69, 0.1);
                    color: #28a745;
                }}
                
                .specialist-signal.sell {{
                    background-color: rgba(220, 53, 69, 0.1);
                    color: #dc3545;
                }}
                
                .specialist-signal.neutral {{
                    background-color: rgba(108, 117, 125, 0.1);
                    color: #6c757d;
                }}
                
                .separator {{
                    height: 1px;
                    background-color: #eaeaea;
                    margin: 15px 0;
                }}
                
                .indicator-badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 13px;
                    margin: 2px;
                }}
                
                .indicator-bullish {{
                    background-color: rgba(40, 167, 69, 0.1);
                    color: #28a745;
                }}
                
                .indicator-bearish {{
                    background-color: rgba(220, 53, 69, 0.1);
                    color: #dc3545;
                }}
                
                /* Estilos para impresión */
                @media print {{
                    body {{
                        background-color: white;
                        font-size: 12pt;
                    }}
                    
                    .content, .detailed-analysis, .sentiment, .news {{
                        box-shadow: none;
                        border: 1px solid #eaeaea;
                    }}
                    
                    .header {{
                        background: #2c3e50;
                        box-shadow: none;
                    }}
                    
                    .footer {{
                        background: white;
                        border-top: 1px solid #eaeaea;
                    }}
                    
                    table {{
                        page-break-inside: avoid;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>InversorIA Pro - Boletín de Trading</h1>
                <p>{current_date}</p>
            </div>
            <div class="content">
                <h2 class="section-title">Señales de Trading Recientes</h2>
        """

        # Tabla de señales
        if signals and len(signals) > 0:
            html += """
                <table>
                    <tr>
                        <th>Símbolo</th>
                        <th>Dirección</th>
                        <th>Precio</th>
                        <th>Confianza</th>
                        <th>Estrategia</th>
                        <th>Timeframe</th>
                    </tr>
            """

            for signal in signals:
                confidence_class = (
                    "signal-high"
                    if signal.get("confidence_level") == "Alta"
                    else (
                        "signal-medium"
                        if signal.get("confidence_level") == "Media"
                        else "signal-low"
                    )
                )
                direction_class = (
                    "buy"
                    if signal.get("direction") == "CALL"
                    else "sell" if signal.get("direction") == "PUT" else "neutral"
                )
                direction_text = (
                    "Compra"
                    if signal.get("direction") == "CALL"
                    else "Venta" if signal.get("direction") == "PUT" else "Neutral"
                )

                html += f"""
                    <tr class="{confidence_class}">
                        <td><strong>{signal.get('symbol', '')}</strong></td>
                        <td class="{direction_class}">{direction_text}</td>
                        <td>${signal.get('price', '0.00')}</td>
                        <td>{signal.get('confidence_level', 'Baja')}</td>
                        <td>{signal.get('strategy', 'N/A')}</td>
                        <td>{signal.get('timeframe', 'Corto')}</td>
                    </tr>
                """

            html += "</table>"

            # Añadir análisis detallado para señales (especialmente las de alta confianza)
            high_confidence_signals = [
                s
                for s in signals
                if s.get("is_high_confidence") == 1
                or s.get("confidence_level") == "Alta"
            ]

            if high_confidence_signals:
                html += "<h2 class='section-title'>Análisis Detallado de Señales</h2>"

                for signal in high_confidence_signals:
                    symbol = signal.get("symbol", "")
                    direction = signal.get("direction", "NEUTRAL")
                    direction_text = (
                        "Compra"
                        if direction == "CALL"
                        else "Venta" if direction == "PUT" else "Neutral"
                    )
                    direction_class = (
                        "buy"
                        if direction == "CALL"
                        else "sell" if direction == "PUT" else "neutral"
                    )

                    analysis_border_class = (
                        "detailed-analysis-call"
                        if direction == "CALL"
                        else (
                            "detailed-analysis-put"
                            if direction == "PUT"
                            else "detailed-analysis-neutral"
                        )
                    )

                    # Obtener precio y cambio porcentual
                    price = signal.get("price", 0)
                    price_formatted = f"${price:,.2f}" if price else "N/A"

                    # Obtener datos de setup y tendencia
                    setup_type = signal.get("setup_type", "")
                    trend = signal.get("trend", "")
                    trend_strength = signal.get("trend_strength", "")

                    html += f"""
                    <div class="detailed-analysis {analysis_border_class}">
                        <h3>{symbol} - <span class="{direction_class}">{direction_text}</span></h3>
                        
                        <div class="metrics-container">
                            <div class="metric-card">
                                <div class="metric-title">Precio Actual</div>
                                <div class="metric-value">{price_formatted}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">Confianza</div>
                                <div class="metric-value">{signal.get('confidence_level', 'N/A')}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">Estrategia</div>
                                <div class="metric-value">{signal.get('strategy', 'N/A')}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">Timeframe</div>
                                <div class="metric-value">{signal.get('timeframe', 'Corto Plazo')}</div>
                            </div>
                        </div>
                    """

                    # Añadir setup type si está disponible
                    if setup_type:
                        html += f"""
                        <div style="margin-top: 15px;">
                            <span class="setup-badge">{setup_type}</span>
                        </div>
                        """

                    # Añadir precios de entrada, stop y objetivo
                    entry_price = signal.get("entry_price")
                    stop_loss = signal.get("stop_loss")
                    target_price = signal.get("target_price")
                    risk_reward = signal.get("risk_reward")

                    if entry_price or stop_loss or target_price:
                        html += f"""
                        <div class="price-targets">
                        """

                        if entry_price:
                            html += f"""
                            <div class="price-target-item">
                                <div class="price-target-title">Precio de Entrada</div>
                                <div class="price-target-value entry">${entry_price:,.2f}</div>
                            </div>
                            """

                        if stop_loss:
                            html += f"""
                            <div class="price-target-item">
                                <div class="price-target-title">Stop Loss</div>
                                <div class="price-target-value stop">${stop_loss:,.2f}</div>
                            </div>
                            """

                        if target_price:
                            html += f"""
                            <div class="price-target-item">
                                <div class="price-target-title">Objetivo</div>
                                <div class="price-target-value target">${target_price:,.2f}</div>
                            </div>
                            """

                        html += """
                        </div>
                        """

                        # Añadir ratio riesgo/recompensa
                        if risk_reward:
                            rr_class = (
                                "good"
                                if risk_reward >= 2
                                else ("neutral" if risk_reward >= 1 else "poor")
                            )
                            html += f"""
                            <div style="text-align: center; margin-top: 5px;">
                                <span class="risk-reward {rr_class}">Ratio Riesgo/Recompensa: {risk_reward:,.2f}</span>
                            </div>
                            """

                    # Añadir análisis principal
                    analysis_text = signal.get("analysis")
                    if analysis_text:
                        html += f"""
                        <div class="analysis-box">
                            <p class="analysis-text">{analysis_text}</p>
                        </div>
                        """

                    # Añadir análisis técnico si está disponible
                    technical_analysis = signal.get("technical_analysis")
                    if technical_analysis:
                        html += f"""
                        <div style="margin-top: 15px;">
                            <h4 style="color: #2c3e50; margin-bottom: 10px;">Análisis Técnico</h4>
                            <p>{technical_analysis}</p>
                        </div>
                        """

                    # Añadir análisis de tendencia
                    if (
                        trend
                        or signal.get("daily_trend")
                        or signal.get("weekly_trend")
                        or signal.get("monthly_trend")
                    ):
                        trend_class = (
                            "bullish"
                            if "ALCISTA" in trend.upper()
                            else "bearish" if "BAJISTA" in trend.upper() else "neutral"
                        )

                        html += """
                        <div class="trend-analysis">
                        """

                        if trend:
                            html += f"""
                            <div class="trend-timeframe">
                                <div class="trend-title">Tendencia Principal</div>
                                <div class="trend-value">
                                    <span class="trend-badge {trend_class}">{trend}</span>
                                    {f'<span style="margin-left: 5px; color: #6c757d;">({trend_strength})</span>' if trend_strength else ''}
                                </div>
                            </div>
                            """

                        daily_trend = signal.get("daily_trend", "")
                        if daily_trend:
                            daily_class = (
                                "bullish"
                                if "ALCISTA" in daily_trend.upper()
                                else (
                                    "bearish"
                                    if "BAJISTA" in daily_trend.upper()
                                    else "neutral"
                                )
                            )
                            html += f"""
                            <div class="trend-timeframe">
                                <div class="trend-title">Tendencia Diaria</div>
                                <div class="trend-value">
                                    <span class="trend-badge {daily_class}">{daily_trend}</span>
                                </div>
                            </div>
                            """

                        weekly_trend = signal.get("weekly_trend", "")
                        if weekly_trend:
                            weekly_class = (
                                "bullish"
                                if "ALCISTA" in weekly_trend.upper()
                                else (
                                    "bearish"
                                    if "BAJISTA" in weekly_trend.upper()
                                    else "neutral"
                                )
                            )
                            html += f"""
                            <div class="trend-timeframe">
                                <div class="trend-title">Tendencia Semanal</div>
                                <div class="trend-value">
                                    <span class="trend-badge {weekly_class}">{weekly_trend}</span>
                                </div>
                            </div>
                            """

                        monthly_trend = signal.get("monthly_trend", "")
                        if monthly_trend:
                            monthly_class = (
                                "bullish"
                                if "ALCISTA" in monthly_trend.upper()
                                else (
                                    "bearish"
                                    if "BAJISTA" in monthly_trend.upper()
                                    else "neutral"
                                )
                            )
                            html += f"""
                            <div class="trend-timeframe">
                                <div class="trend-title">Tendencia Mensual</div>
                                <div class="trend-value">
                                    <span class="trend-badge {monthly_class}">{monthly_trend}</span>
                                </div>
                            </div>
                            """

                        html += """
                        </div>
                        """

                    # Añadir indicadores técnicos
                    rsi = signal.get("rsi")
                    support_level = signal.get("support_level")
                    resistance_level = signal.get("resistance_level")

                    has_technical_indicators = (
                        rsi is not None or support_level or resistance_level
                    )

                    if has_technical_indicators:
                        html += """
                        <div class="indicators-section">
                            <h4 class="indicators-title">Indicadores Técnicos</h4>
                            <div class="indicators-grid">
                        """

                        if rsi is not None:
                            html += f"""
                            <div class="indicator">
                                <strong>RSI:</strong> {rsi if isinstance(rsi, str) else f"{rsi:.1f}"}
                            </div>
                            """

                        if support_level:
                            html += f"""
                            <div class="indicator">
                                <strong>Soporte:</strong> ${support_level:,.2f}
                            </div>
                            """

                        if resistance_level:
                            html += f"""
                            <div class="indicator">
                                <strong>Resistencia:</strong> ${resistance_level:,.2f}
                            </div>
                            """

                        html += """
                            </div>
                        </div>
                        """

                    # Mostrar indicadores bullish y bearish
                    bullish_indicators = signal.get("bullish_indicators", "")
                    bearish_indicators = signal.get("bearish_indicators", "")

                    if bullish_indicators or bearish_indicators:
                        html += """
                        <div style="margin-top: 15px;">
                        """

                        if bullish_indicators:
                            bull_indicators = (
                                bullish_indicators.split(",")
                                if isinstance(bullish_indicators, str)
                                else []
                            )
                            if bull_indicators:
                                html += """
                                <div style="margin-bottom: 10px;">
                                    <strong>Indicadores Alcistas:</strong>
                                    <div style="margin-top: 5px;">
                                """
                                for indicator in bull_indicators:
                                    indicator = indicator.strip()
                                    if indicator:
                                        html += f"""
                                        <span class="indicator-badge indicator-bullish">{indicator}</span>
                                        """
                                html += """
                                    </div>
                                </div>
                                """

                        if bearish_indicators:
                            bear_indicators = (
                                bearish_indicators.split(",")
                                if isinstance(bearish_indicators, str)
                                else []
                            )
                            if bear_indicators:
                                html += """
                                <div>
                                    <strong>Indicadores Bajistas:</strong>
                                    <div style="margin-top: 5px;">
                                """
                                for indicator in bear_indicators:
                                    indicator = indicator.strip()
                                    if indicator:
                                        html += f"""
                                        <span class="indicator-badge indicator-bearish">{indicator}</span>
                                        """
                                html += """
                                    </div>
                                </div>
                                """

                        html += """
                        </div>
                        """

                    # Añadir Trading Specialist Signal si está disponible
                    trading_specialist_signal = signal.get(
                        "trading_specialist_signal", ""
                    )
                    trading_specialist_confidence = signal.get(
                        "trading_specialist_confidence", ""
                    )

                    if trading_specialist_signal:
                        specialist_class = (
                            "buy"
                            if "COMPRA" in trading_specialist_signal.upper()
                            else (
                                "sell"
                                if "VENTA" in trading_specialist_signal.upper()
                                else "neutral"
                            )
                        )

                        html += f"""
                        <div class="trading-specialist">
                            <h4 class="trading-specialist-title">Análisis del Trading Specialist</h4>
                            <div>
                                <span class="specialist-signal {specialist_class}">{trading_specialist_signal}</span>
                                {f'<span style="color: #6c757d;">Confianza: {trading_specialist_confidence}</span>' if trading_specialist_confidence else ''}
                            </div>
                        """

                        # Añadir análisis multi-timeframe si está disponible
                        mtf_analysis = signal.get("mtf_analysis", "")
                        if mtf_analysis:
                            html += f"""
                            <div class="separator"></div>
                            <p>{mtf_analysis}</p>
                            """

                        html += """
                        </div>
                        """

                    # Añadir análisis experto si está disponible
                    expert_analysis = signal.get("expert_analysis", "")
                    if expert_analysis:
                        html += f"""
                        <div class="expert-analysis">
                            <h4 class="expert-title">Análisis del Experto</h4>
                            <p>{expert_analysis}</p>
                        </div>
                        """

                    # Añadir recomendación final si está disponible
                    recommendation = signal.get("recommendation", "")
                    if recommendation:
                        rec_class = (
                            "buy"
                            if "COMPRAR" in recommendation.upper()
                            else (
                                "sell"
                                if "VENDER" in recommendation.upper()
                                else "neutral"
                            )
                        )

                        html += f"""
                        <div style="margin-top: 20px; text-align: center;">
                            <h4 style="margin-bottom: 10px;">Recomendación Final</h4>
                            <div style="display: inline-block; padding: 10px 20px; background-color: {
                                '#e8f5e9' if rec_class == 'buy' else (
                                '#ffebee' if rec_class == 'sell' else '#f5f5f5'
                                )
                            }; border-radius: 8px; font-weight: 700; color: {
                                '#28a745' if rec_class == 'buy' else (
                                '#dc3545' if rec_class == 'sell' else '#6c757d'
                                )
                            }; font-size: 18px;">
                                {recommendation}
                            </div>
                        </div>
                        """

                    # Añadir noticias relacionadas si están disponibles
                    latest_news = signal.get("latest_news", "")
                    news_source = signal.get("news_source", "")
                    additional_news = signal.get("additional_news", "")

                    if latest_news:
                        html += f"""
                        <div style="margin-top: 20px; background-color: #f8f9fa; border-radius: 6px; padding: 15px;">
                            <h4 style="margin-top: 0; color: #2c3e50;">Noticias Relacionadas</h4>
                            <div style="margin-bottom: 10px;">
                                <p style="margin: 0 0 5px 0;"><strong>{latest_news}</strong></p>
                                {f'<p style="margin: 0; font-size: 12px; color: #6c757d;">Fuente: {news_source}</p>' if news_source else ''}
                            </div>
                        """

                        if additional_news:
                            additional_news_items = (
                                additional_news.split("||")
                                if "||" in additional_news
                                else [additional_news]
                            )
                            for item in additional_news_items:
                                if item.strip():
                                    html += f"""
                                    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eaeaea;">
                                        <p style="margin: 0;">{item.strip()}</p>
                                    </div>
                                    """

                        html += """
                        </div>
                        """

                    html += "</div>"
        else:
            html += "<p>No hay señales de trading disponibles en este momento.</p>"

        # Sección de sentimiento de mercado
        if market_sentiment:
            sentiment_class = (
                "sentiment-bullish"
                if market_sentiment.get("overall") == "Alcista"
                else (
                    "sentiment-bearish"
                    if market_sentiment.get("overall") == "Bajista"
                    else "sentiment-neutral"
                )
            )

            html += f"""
                    <h2 class="section-title">Sentimiento de Mercado</h2>
                    <div class="sentiment {sentiment_class}">
                        <h3 class="sentiment-title">Sentimiento General: {market_sentiment.get('overall', 'Neutral')}</h3>
                        <div class="metrics-container">
                            <div class="metric-card">
                                <div class="metric-title">VIX</div>
                                <div class="metric-value">{market_sentiment.get('vix', 'N/A')}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">S&P 500</div>
                                <div class="metric-value">{market_sentiment.get('sp500_trend', 'N/A')}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">Indicadores Técnicos</div>
                                <div class="metric-value">{market_sentiment.get('technical_indicators', 'N/A')}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">Volumen</div>
                                <div class="metric-value">{market_sentiment.get('volume', 'N/A')}</div>
                            </div>
                        </div>
                    </div>
            """

        # Sección de noticias
        html += """
                <h2 class="section-title">Noticias Relevantes</h2>
                <div class="news">
        """

        if news_summary and len(news_summary) > 0:
            for news in news_summary:
                # Añadir indicador de impacto si está disponible
                impact = news.get("impact", "")
                impact_class = (
                    "high-impact"
                    if impact == "Alto"
                    else ("medium-impact" if impact == "Medio" else "low-impact")
                )

                # Formatear fecha de forma elegante
                news_date = news.get("news_date", datetime.now())
                if isinstance(news_date, datetime):
                    formatted_date = news_date.strftime("%d %b %Y")
                else:
                    formatted_date = str(news_date)

                html += f"""
                    <div class="news-item">
                        <h3 class="news-title">{news.get('title', '')}</h3>
                        <p>{news.get('summary', '')}</p>
                        <p class="news-meta">
                            {f'<span class="{impact_class}">Impacto: {impact}</span> • ' if impact else ''}
                            Fuente: {news.get('source', '')} • {formatted_date}
                        </p>
                    </div>
                """
        else:
            html += "<p>No hay noticias relevantes disponibles en este momento.</p>"

        html += """
                </div>
            </div>
            <div class="footer">
                <p>Este boletín es generado automáticamente por InversorIA Pro. La información proporcionada es solo para fines educativos y no constituye asesoramiento financiero.</p>
                <p>Los datos presentados son calculados en tiempo real utilizando análisis técnico avanzado y algoritmos de inteligencia artificial.</p>
                <p>&copy; 2025 InversorIA Pro. Todos los derechos reservados.</p>
            </div>
        </body>
        </html>
        """

        return html

    def generate_pdf(self, html_content):
        """Genera un PDF a partir del contenido HTML"""
        # Verificar si pdfkit está disponible
        if not PDFKIT_AVAILABLE:
            logger.warning("pdfkit no está disponible. No se puede generar PDF.")
            return None

        try:
            # Opciones para pdfkit (ajustar según sea necesario)
            options = {
                "page-size": "A4",
                "margin-top": "10mm",
                "margin-right": "10mm",
                "margin-bottom": "10mm",
                "margin-left": "10mm",
                "encoding": "UTF-8",
                "no-outline": None,
                "enable-local-file-access": "",
                "print-media-type": "",
            }

            # Generar PDF
            pdf = pdfkit.from_string(html_content, False, options=options)
            logger.info("PDF generado correctamente")
            return pdf
        except Exception as e:
            logger.error(f"Error al generar PDF: {str(e)}")
            return None


# Clase para gestionar las señales de trading
class SignalManager:
    """Gestiona las señales de trading y su procesamiento"""

    def __init__(self):
        """Inicializa el gestor de señales"""
        self.db_manager = DatabaseManager()
        self.email_manager = EmailManager()

    def get_active_signals(
        self,
        days_back=7,
        categories=None,
        confidence_levels=None,
        direction=None,
        high_confidence_only=False,
        refresh=False,
    ):
        """Obtiene las señales activas filtradas desde la base de datos"""
        # Verificar si hay señales en caché de sesión y no se solicita actualización
        if (
            "cached_signals" in st.session_state
            and st.session_state.cached_signals
            and not refresh
        ):
            logger.info(
                f"Usando {len(st.session_state.cached_signals)} señales desde la caché de sesión"
            )
            cached_signals = st.session_state.cached_signals

            # Aplicar filtros a las señales en caché
            filtered_signals = []
            for signal in cached_signals:
                # Filtrar por categoría
                if (
                    categories
                    and categories != "Todas"
                    and signal.get("category") not in categories
                ):
                    continue

                # Filtrar por nivel de confianza
                if (
                    confidence_levels
                    and signal.get("confidence_level") not in confidence_levels
                ):
                    continue

                # Filtrar por dirección
                if (
                    direction
                    and direction != "Todas"
                    and signal.get("direction") != direction
                ):
                    continue

                # Filtrar por alta confianza
                if high_confidence_only and signal.get("is_high_confidence") != 1:
                    continue

                # Filtrar por fecha
                created_at = signal.get("created_at")
                if isinstance(created_at, datetime):
                    if (datetime.now() - created_at).days > days_back:
                        continue

                filtered_signals.append(signal)

            if filtered_signals:
                logger.info(
                    f"Se encontraron {len(filtered_signals)} señales en caché que cumplen los filtros"
                )
                return filtered_signals

        # Si no hay señales en caché o se fuerza actualización, obtener de la base de datos
        logger.info("Obteniendo señales desde la base de datos...")

        # Determinar categoría para filtrar
        category_filter = None if categories == "Todas" else categories
        direction_filter = None if direction == "Todas" else direction

        # Obtener señales de la base de datos
        signals_from_db = self.db_manager.get_signals(
            days_back,
            category_filter,
            confidence_levels,
            direction_filter,
            high_confidence_only,
        )

        # Si hay señales en la base de datos, actualizamos la caché
        if signals_from_db and len(signals_from_db) > 0:
            logger.info(
                f"Se encontraron {len(signals_from_db)} señales en la base de datos"
            )

            # Verificar que las fechas no sean futuras
            for signal in signals_from_db:
                if "created_at" in signal and isinstance(
                    signal["created_at"], datetime
                ):
                    # Si la fecha es futura, corregirla a la fecha actual
                    if signal["created_at"] > datetime.now():
                        signal["created_at"] = datetime.now()
                        logger.warning(
                            f"Se corrigió una fecha futura para la señal {signal.get('symbol')}"
                        )

                # Convertir valores Decimal a float
                for key, value in signal.items():
                    if isinstance(value, decimal.Decimal):
                        signal[key] = float(value)

            # Actualizar la caché de sesión
            st.session_state.cached_signals = signals_from_db

            # Compartir señales con otras páginas
            st.session_state.market_signals = signals_from_db

            return signals_from_db

        # Si no hay señales en la base de datos, devolver lista vacía
        logger.info(
            "No se encontraron señales en la base de datos, devolviendo lista vacía"
        )
        return []

    def get_market_sentiment(self):
        """Obtiene el sentimiento actual del mercado desde la base de datos"""
        sentiment_data = self.db_manager.get_market_sentiment()

        if sentiment_data and len(sentiment_data) > 0:
            logger.info("Se obtuvo sentimiento de mercado desde la base de datos")

            # Asegurar que no hay valores Decimal
            sentiment_object = sentiment_data[0]
            for key, value in sentiment_object.items():
                if isinstance(value, decimal.Decimal):
                    sentiment_object[key] = float(value)

            return sentiment_object

        # Si no hay datos, devolver un objeto con valores predeterminados
        logger.warning("No se encontraron datos de sentimiento en la base de datos")
        return {
            "overall": "Neutral",
            "vix": "N/A",
            "sp500_trend": "No disponible",
            "technical_indicators": "No disponible",
            "volume": "No disponible",
            "notes": f"Datos no disponibles - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        }

    def get_market_news(self, limit=5):
        """Obtiene noticias relevantes del mercado desde la base de datos"""
        news_data = self.db_manager.get_market_news(limit=limit)

        if news_data and len(news_data) > 0:
            logger.info(
                f"Se obtuvieron {len(news_data)} noticias desde la base de datos"
            )

            # Convertir valores Decimal a float
            for news in news_data:
                for key, value in news.items():
                    if isinstance(value, decimal.Decimal):
                        news[key] = float(value)

            return news_data

        logger.warning("No se encontraron noticias en la base de datos")
        return []

    def get_detailed_analysis(self, symbol):
        """Obtiene análisis detallado para un símbolo específico desde la base de datos"""
        analysis_data = self.db_manager.get_detailed_analysis(symbol)

        if analysis_data and len(analysis_data) > 0:
            logger.info(
                f"Se obtuvo análisis detallado para {symbol} desde la base de datos"
            )

            # Convertir valores Decimal a float
            detailed_analysis = analysis_data[0]
            for key, value in detailed_analysis.items():
                if isinstance(value, decimal.Decimal):
                    detailed_analysis[key] = float(value)

            return detailed_analysis

        logger.warning(
            f"No se encontró análisis detallado para {symbol} en la base de datos"
        )
        return None

    def save_signal(self, signal_data):
        """Guarda una nueva señal en la base de datos"""
        return self.db_manager.save_signal(signal_data)

    def send_newsletter(
        self, recipients, signals, market_sentiment, news_summary, include_pdf=True
    ):
        """Envía un boletín con las señales y análisis"""
        # Guardar las señales en la base de datos si no existen ya
        signal_ids = []
        if signals and len(signals) > 0:
            for signal in signals:
                # Si la señal ya tiene ID, asumir que ya está en la base de datos
                if "id" in signal and signal["id"]:
                    signal_ids.append(str(signal["id"]))
                    continue

                # Si no tiene ID, intentar guardarla
                try:
                    # Preparar datos para guardar
                    signal_data = {
                        "symbol": signal.get("symbol"),
                        "price": signal.get("price"),
                        "direction": signal.get("direction"),
                        "confidence_level": signal.get("confidence_level"),
                        "timeframe": signal.get("timeframe"),
                        "strategy": signal.get("strategy"),
                        "category": signal.get("category"),
                        "analysis": signal.get("analysis"),
                    }

                    # Conectar a la base de datos
                    if self.db_manager.connect():
                        cursor = self.db_manager.connection.cursor(dictionary=True)

                        # Verificar si la señal ya existe para el mismo símbolo y fecha
                        check_query = """
                            SELECT id FROM trading_signals
                            WHERE symbol = %s AND DATE(created_at) = CURDATE()
                            LIMIT 1
                        """
                        cursor.execute(check_query, (signal_data.get("symbol"),))
                        existing = cursor.fetchone()

                        if existing:
                            # Si ya existe, usar ese ID
                            signal_ids.append(str(existing["id"]))
                            logger.info(
                                f"Señal para {signal_data.get('symbol')} ya existe con ID: {existing['id']}"
                            )
                        else:
                            # Si no existe, insertar nueva
                            insert_query = """
                                INSERT INTO trading_signals
                                (symbol, price, direction, confidence_level, timeframe,
                                strategy, category, analysis, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            """

                            params = (
                                signal_data.get("symbol"),
                                signal_data.get("price"),
                                signal_data.get("direction"),
                                signal_data.get("confidence_level"),
                                signal_data.get("timeframe"),
                                signal_data.get("strategy"),
                                signal_data.get("category"),
                                signal_data.get("analysis"),
                            )

                            cursor.execute(insert_query, params)
                            self.db_manager.connection.commit()
                            new_id = cursor.lastrowid

                            if new_id:
                                signal_ids.append(str(new_id))
                                logger.info(f"Nueva señal guardada con ID: {new_id}")
                            else:
                                # ID temporal en caso de error
                                signal_ids.append(f"temp_{len(signal_ids)}")
                                logger.warning(
                                    "No se pudo obtener ID de la nueva señal"
                                )

                        cursor.close()
                    else:
                        # ID temporal en caso de error de conexión
                        signal_ids.append(f"temp_{len(signal_ids)}")
                        logger.warning("No se pudo conectar a la base de datos")

                    self.db_manager.disconnect()
                except Exception as e:
                    # ID temporal en caso de excepción
                    signal_ids.append(f"temp_{len(signal_ids)}")
                    logger.error(f"Error al guardar señal: {str(e)}")

        # Crear contenido HTML del boletín
        html_content = self.email_manager.create_newsletter_html(
            signals, market_sentiment, news_summary
        )

        # Generar PDF si está habilitado
        pdf_content = None
        if include_pdf and PDFKIT_AVAILABLE:
            try:
                pdf_content = self.email_manager.generate_pdf(html_content)
                if pdf_content:
                    logger.info("PDF generado correctamente para adjuntar al correo")
                else:
                    logger.warning("No se pudo generar el PDF para adjuntar al correo")
            except Exception as e:
                logger.error(f"Error generando PDF: {str(e)}")

        # Enviar correo
        subject = (
            f"InversorIA Pro - Boletín de Trading {datetime.now().strftime('%d/%m/%Y')}"
        )
        success = self.email_manager.send_email(
            recipients, subject, html_content, pdf_content
        )

        # Registrar envío en la base de datos si fue exitoso
        if success:
            # Usar los IDs de las señales guardadas o existentes
            signal_ids_str = ", ".join(signal_ids) if signal_ids else "Ninguna"

            email_data = {
                "recipients": (
                    recipients if isinstance(recipients, str) else ", ".join(recipients)
                ),
                "subject": subject,
                "content_summary": f"Boletín con {len(signals) if signals else 0} señales",
                "signals_included": signal_ids_str,
                "status": "success",
                "error_message": None,
            }
            self.db_manager.log_email_sent(email_data)
            return True
        else:
            # Registrar el error en la base de datos
            email_data = {
                "recipients": (
                    recipients if isinstance(recipients, str) else ", ".join(recipients)
                ),
                "subject": subject,
                "content_summary": f"Boletín con {len(signals) if signals else 0} señales",
                "signals_included": ", ".join(signal_ids) if signal_ids else "Ninguna",
                "status": "failed",
                "error_message": "Error enviando el correo electrónico",
            }
            self.db_manager.log_email_sent(email_data)
            return False


# Crear pestañas para organizar la interfaz
tab1, tab2, tab3 = st.tabs(
    ["📋 Señales Activas", "📬 Envío de Boletines", "📊 Historial de Señales"]
)

# Inicializar estado de sesión para señales
if "cached_signals" not in st.session_state:
    st.session_state.cached_signals = []

# Verificar si hay señales en otras páginas
if "market_signals" in st.session_state and st.session_state.market_signals:
    # Combinar señales sin duplicados
    existing_symbols = {
        signal.get("symbol") for signal in st.session_state.cached_signals
    }
    for signal in st.session_state.market_signals:
        if signal.get("symbol") not in existing_symbols:
            st.session_state.cached_signals.append(signal)
            existing_symbols.add(signal.get("symbol"))

    logger.info(
        f"Se importaron {len(st.session_state.market_signals)} señales desde otras páginas"
    )

# Inicializar el gestor de señales
signal_manager = SignalManager()

# Contenido de la pestaña "Señales Activas"
with tab1:
    st.header("📋 Señales de Trading Activas")

    # Añadir botón de actualización
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(
            "Utilice los filtros de la barra lateral para personalizar los resultados."
        )
    with col2:
        refresh = st.button(
            "🔄 Actualizar Datos",
            help="Fuerza una nueva consulta de la base de datos",
        )

    # Obtener señales filtradas
    categoria_filtro = "Todas" if categoria == "Todas" else [categoria]
    signals = signal_manager.get_active_signals(
        days_back=dias_atras,
        categories=categoria_filtro,
        confidence_levels=confianza,
        direction=direccion,
        high_confidence_only=alta_confianza_only,
        refresh=refresh,  # Forzar actualización si se presiona el botón
    )

    # Mostrar mensaje de actualización si se presionó el botón
    if refresh:
        st.success("Datos actualizados con éxito desde la base de datos.")

    # Mostrar señales en tarjetas
    if signals and len(signals) > 0:
        # Dividir en columnas para mostrar las tarjetas
        cols = st.columns(2)

        for i, signal in enumerate(signals):
            # Alternar entre columnas
            with cols[i % 2]:
                # Determinar color de fondo según dirección (compatible con modo oscuro)
                if signal.get("direction") == "CALL":
                    card_bg = "rgba(40, 167, 69, 0.2)"  # Verde semi-transparente
                    text_color = "#28a745"  # Verde
                    border_color = "#28a745"
                    direction_text = "📈 COMPRA"
                elif signal.get("direction") == "PUT":
                    card_bg = "rgba(220, 53, 69, 0.2)"  # Rojo semi-transparente
                    text_color = "#dc3545"  # Rojo
                    border_color = "#dc3545"
                    direction_text = "📉 VENTA"
                else:
                    card_bg = "rgba(108, 117, 125, 0.2)"  # Gris semi-transparente
                    text_color = "#6c757d"  # Gris
                    border_color = "#6c757d"
                    direction_text = "↔️ NEUTRAL"

                # Formatear fecha (asegurarse de que no sea futura)
                created_at = signal.get("created_at")
                if isinstance(created_at, datetime):
                    # Corregir fechas futuras
                    if created_at > datetime.now():
                        created_at = datetime.now()
                        signal["created_at"] = (
                            created_at  # Actualizar la fecha en el objeto original
                        )
                    fecha = created_at.strftime("%d/%m/%Y %H:%M")
                else:
                    # Si no es un objeto datetime, usar la fecha actual
                    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                    signal["created_at"] = (
                        datetime.now()
                    )  # Actualizar la fecha en el objeto original

                # Badge para Alta Confianza
                high_confidence_badge = ""
                if signal.get("is_high_confidence") == 1:
                    high_confidence_badge = f"""
                    <div style="position: absolute; top: 10px; right: 10px; 
                                background-color: #28a745; color: white; 
                                padding: 5px 10px; border-radius: 20px; 
                                font-size: 12px; font-weight: bold;">
                        Alta Confianza
                    </div>
                    """

                # Setup type (si está disponible)
                setup_badge = ""
                if signal.get("setup_type"):
                    setup_badge = f"""
                    <div style="display: inline-block; margin-top: 10px; margin-bottom: 5px;
                                padding: 5px 10px; background-color: #e9f5ff; 
                                border-radius: 20px; font-size: 13px; color: #0275d8;">
                        {signal.get("setup_type")}
                    </div>
                    """

                # Datos de precio target/stop loss (si disponibles)
                price_targets = ""
                entry_price = signal.get("entry_price")
                stop_loss = signal.get("stop_loss")
                target_price = signal.get("target_price")
                risk_reward = signal.get("risk_reward")

                if entry_price or stop_loss or target_price:
                    price_targets = """
                    <div style="display: flex; flex-wrap: wrap; 
                                margin-top: 15px; padding: 10px; 
                                background-color: #f8f9fa; border-radius: 6px;">
                    """

                    if entry_price:
                        price_targets += f"""
                        <div style="flex: 1; min-width: 100px; text-align: center; margin-bottom: 5px;">
                            <div style="font-size: 12px; color: #6c757d;">Entrada</div>
                            <div style="font-size: 16px; font-weight: 700; color: #0275d8;">
                                ${entry_price:,.2f}
                            </div>
                        </div>
                        """

                    if stop_loss:
                        price_targets += f"""
                        <div style="flex: 1; min-width: 100px; text-align: center; margin-bottom: 5px;">
                            <div style="font-size: 12px; color: #6c757d;">Stop Loss</div>
                            <div style="font-size: 16px; font-weight: 700; color: #dc3545;">
                                ${stop_loss:,.2f}
                            </div>
                        </div>
                        """

                    if target_price:
                        price_targets += f"""
                        <div style="flex: 1; min-width: 100px; text-align: center; margin-bottom: 5px;">
                            <div style="font-size: 12px; color: #6c757d;">Objetivo</div>
                            <div style="font-size: 16px; font-weight: 700; color: #28a745;">
                                ${target_price:,.2f}
                            </div>
                        </div>
                        """

                    price_targets += "</div>"

                    # Añadir Ratio Riesgo/Recompensa si está disponible
                    if risk_reward:
                        rr_color = (
                            "#28a745"
                            if risk_reward >= 2
                            else ("#6c757d" if risk_reward >= 1 else "#dc3545")
                        )
                        price_targets += f"""
                        <div style="text-align: center; margin-top: 5px;">
                            <span style="display: inline-block; padding: 5px 10px; 
                                    background-color: #f2f6f9; border-radius: 4px; 
                                    font-weight: 500; color: {rr_color};">
                                R/R: {risk_reward:,.2f}
                            </span>
                        </div>
                        """

                # Tendencia (si está disponible)
                trend_info = ""
                trend = signal.get("trend", "")
                trend_strength = signal.get("trend_strength", "")

                if trend:
                    trend_color = (
                        "#28a745"
                        if "ALCISTA" in trend.upper()
                        else ("#dc3545" if "BAJISTA" in trend.upper() else "#6c757d")
                    )
                    trend_info = f"""
                    <div style="margin-top: 15px;">
                        <div style="font-size: 13px; color: #6c757d; margin-bottom: 5px;">Tendencia:</div>
                        <div style="display: inline-block; padding: 5px 10px; 
                                    background-color: rgba({
                                        "40, 167, 69, 0.1" if "ALCISTA" in trend.upper() else
                                        ("220, 53, 69, 0.1" if "BAJISTA" in trend.upper() else "108, 117, 125, 0.1")
                                    }); border-radius: 5px; color: {trend_color}; font-weight: 500;">
                            {trend}
                            {f' • <span style="font-size: 12px; opacity: 0.8;">{trend_strength}</span>' if trend_strength else ''}
                        </div>
                    </div>
                    """

                # Crear tarjeta con CSS mejorado (compatible con modo oscuro)
                st.markdown(
                    f"""
                <div style="position: relative; background-color: {card_bg}; padding: 20px; 
                           border-radius: 10px; margin-bottom: 20px; 
                           border: 1px solid {border_color}; 
                           box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    {high_confidence_badge}
                    <h3 style="margin-top: 0; color: {text_color}; font-size: 20px; font-weight: 600;">
                        {signal.get('symbol', '')} - {direction_text}
                    </h3>
                    
                    {setup_badge}
                    
                    <div style="display: flex; flex-wrap: wrap; margin-bottom: 10px;">
                        <div style="flex: 1; min-width: 140px; margin-bottom: 10px;">
                            <strong style="color: #555;">Precio:</strong> 
                            <span style="font-size: 16px; font-weight: 500;">${signal.get('price', '0.00')}</span>
                        </div>
                        <div style="flex: 1; min-width: 140px; margin-bottom: 10px;">
                            <strong style="color: #555;">Confianza:</strong> 
                            <span style="font-size: 16px; font-weight: 500;">{signal.get('confidence_level', 'Baja')}</span>
                        </div>
                    </div>
                    
                    <div style="display: flex; flex-wrap: wrap; margin-bottom: 15px;">
                        <div style="flex: 1; min-width: 140px; margin-bottom: 10px;">
                            <strong style="color: #555;">Estrategia:</strong> 
                            <span>{signal.get('strategy', 'N/A')}</span>
                        </div>
                        <div style="flex: 1; min-width: 140px; margin-bottom: 10px;">
                            <strong style="color: #555;">Timeframe:</strong> 
                            <span>{signal.get('timeframe', 'Corto')}</span>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 10px;">
                        <strong style="color: #555;">Categoría:</strong> {signal.get('category', 'N/A')}
                    </div>
                    
                    <div style="margin-bottom: 10px;">
                        <strong style="color: #555;">Fecha:</strong> {fecha}
                    </div>
                    
                    {price_targets}
                    
                    {trend_info}
                    
                    <details style="margin-top: 15px; cursor: pointer;">
                        <summary style="color: {text_color}; font-weight: 500;">Ver análisis detallado</summary>
                        <div style="background-color: rgba(255,255,255,0.5); padding: 15px; 
                                   border-radius: 8px; margin-top: 10px;">
                            <p style="margin: 0;">{signal.get('analysis', 'No hay análisis disponible.')}</p>
                            
                            {f'<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(0,0,0,0.1);"><strong>Análisis Técnico:</strong><p>{signal.get("technical_analysis", "")}</p></div>' if signal.get("technical_analysis") else ''}
                        </div>
                    </details>
                </div>
                """,
                    unsafe_allow_html=True,
                )
    else:
        # Mostrar mensaje más detallado cuando no hay señales
        st.warning("No se encontraron señales activas con los filtros seleccionados.")

        # Sugerir acciones al usuario
        st.markdown(
            """
        ### Sugerencias:
        1. **Prueba a cambiar los filtros** - Selecciona "Todas" en la categoría o "Baja" en el nivel de confianza para ver más resultados.
        2. **Actualiza los datos** - Usa el botón "Actualizar Datos" para forzar una nueva consulta de la base de datos.
        3. **Verifica la conexión** - Asegúrate de tener una conexión a la base de datos configurada correctamente.
        4. **Verifica que haya datos** - Asegúrate de que existan registros en la tabla 'trading_signals' de la base de datos.
        """
        )

    # Mostrar sentimiento de mercado
    st.subheader("📈 Sentimiento de Mercado")

    # Crear un contenedor para mostrar un mensaje de carga
    sentiment_container = st.container()
    with sentiment_container:
        with st.spinner("Consultando sentimiento de mercado..."):
            sentiment = signal_manager.get_market_sentiment()

    # Verificar si hay datos de sentimiento válidos
    has_valid_sentiment = sentiment and (
        sentiment.get("overall", "Neutral") != "Neutral"
        or sentiment.get("vix", "N/A") != "N/A"
        or sentiment.get("sp500_trend", "N/A") != "No disponible"
        or sentiment.get("volume", "N/A") != "No disponible"
    )

    if has_valid_sentiment:
        # Determinar color según sentimiento
        if sentiment.get("overall") == "Alcista":
            sentiment_color = "#28a745"  # Verde
        elif sentiment.get("overall") == "Bajista":
            sentiment_color = "#dc3545"  # Rojo
        else:
            sentiment_color = "#6c757d"  # Gris

        # Convertir valores decimales a cadenas o flotantes antes de mostrarlos
        # Esto soluciona el error con los valores de tipo decimal.Decimal
        cols = st.columns(4)
        with cols[0]:
            st.metric("Sentimiento", str(sentiment.get("overall", "Neutral")))
        with cols[1]:
            # Convertir explícitamente el valor VIX a string para evitar el error
            vix_value = sentiment.get("vix", "N/A")
            if isinstance(vix_value, decimal.Decimal):
                vix_value = str(float(vix_value))
            st.metric("VIX", vix_value)
        with cols[2]:
            st.metric("S&P 500", str(sentiment.get("sp500_trend", "N/A")))
        with cols[3]:
            st.metric("Volumen", str(sentiment.get("volume", "N/A")))

        # Mostrar notas adicionales si están disponibles
        if sentiment.get("notes"):
            st.caption(sentiment.get("notes"))
    else:
        # Mostrar mensaje cuando no hay datos válidos
        st.warning(
            "No se pudieron obtener datos de sentimiento de mercado desde la base de datos."
        )

        # Sugerir acciones al usuario
        st.markdown(
            """
        **Sugerencias:**
        - Verifica que existan registros en la tabla 'market_sentiment'
        - Intenta actualizar la página
        - Verifica la conexión a la base de datos
        """
        )

    # Mostrar noticias relevantes
    st.subheader("📰 Noticias Relevantes")

    # Crear un contenedor para mostrar un mensaje de carga
    news_container = st.container()
    with news_container:
        with st.spinner("Buscando noticias relevantes..."):
            news = signal_manager.get_market_news()

    if news and len(news) > 0:
        # Mostrar contador de noticias
        st.write(f"Se encontraron {len(news)} noticias relevantes.")

        for item in news:
            # Formatear fecha (asegurarse de que no sea futura)
            news_date = item.get("news_date")
            if isinstance(news_date, datetime):
                # Corregir fechas futuras
                if news_date > datetime.now():
                    news_date = datetime.now()
                    item["news_date"] = (
                        news_date  # Actualizar la fecha en el objeto original
                    )
                fecha = news_date.strftime("%d/%m/%Y")
            else:
                # Si no es un objeto datetime, usar la fecha actual
                fecha = datetime.now().strftime("%d/%m/%Y")
                item["news_date"] = (
                    datetime.now()
                )  # Actualizar la fecha en el objeto original

            # Determinar color según impacto
            impact = item.get("impact", "Medio")
            if impact == "Alto":
                impact_color = "#dc3545"  # Rojo
            elif impact == "Medio":
                impact_color = "#fd7e14"  # Naranja
            else:
                impact_color = "#6c757d"  # Gris

            # Mostrar noticia con diseño mejorado (compatible con modo oscuro)
            st.markdown(
                f"""
            <div style="background-color: rgba(255,255,255,0.05); padding: 20px; 
                       border-radius: 10px; margin-bottom: 15px; 
                       border: 1px solid rgba(0,0,0,0.05); 
                       box-shadow: 0 4px 6px rgba(0,0,0,0.03);">
                <h4 style="margin-top: 0; color: #0275d8; font-weight: 600; font-size: 18px;">
                    {item.get('title', '')}
                </h4>
                <p>{item.get('summary', '')}</p>
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="color: {impact_color}; font-weight: 500; margin-right: 10px;">
                            Impacto: {impact}
                        </span>
                        <span style="color: #6c757d; margin-right: 10px;">·</span>
                        <span style="color: #6c757d;">Fuente: {item.get('source', '')}</span>
                    </div>
                    <div style="color: #6c757d; font-size: 14px;">{fecha}</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        # Mostrar mensaje cuando no hay noticias disponibles
        st.warning("No se pudieron obtener noticias relevantes desde la base de datos.")

        # Sugerir acciones al usuario
        st.markdown(
            """
        **Sugerencias:**
        - Verifica que existan registros en la tabla 'market_news'
        - Intenta actualizar la página
        - Verifica la conexión a la base de datos
        """
        )

# Contenido de la pestaña "Envío de Boletines"
with tab2:
    st.header("📬 Envío de Boletines de Trading")

    # Selección de señales para incluir en el boletín
    st.subheader("Paso 1: Seleccionar Señales para el Boletín")

    # Añadir botón de actualización
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write("Seleccione las señales que desea incluir en el boletín.")
    with col2:
        refresh_bulletin = st.button(
            "🔄 Actualizar Señales",
            help="Fuerza una nueva consulta de la base de datos",
            key="refresh_bulletin",
        )

    # Obtener todas las señales disponibles
    all_signals = signal_manager.get_active_signals(
        days_back=dias_atras,
        refresh=refresh_bulletin,  # Forzar actualización si se presiona el botón
    )

    # Mostrar mensaje de actualización si se presionó el botón
    if refresh_bulletin:
        st.success("Señales actualizadas con éxito desde la base de datos.")

    if all_signals and len(all_signals) > 0:
        # Crear opciones para multiselect
        signal_options = {}
        for signal in all_signals:
            # Crear texto descriptivo para cada señal
            direction = (
                "COMPRA"
                if signal.get("direction") == "CALL"
                else "VENTA" if signal.get("direction") == "PUT" else "NEUTRAL"
            )
            confidence = signal.get("confidence_level", "")
            high_confidence = "⭐" if signal.get("is_high_confidence") == 1 else ""
            key = (
                f"{signal.get('symbol')} - {direction} - {confidence} {high_confidence}"
            )
            signal_options[key] = signal

        # Permitir al usuario seleccionar señales (priorizar alta confianza en defaults)
        high_confidence_keys = [k for k in signal_options.keys() if "⭐" in k]
        default_keys = high_confidence_keys[: min(3, len(high_confidence_keys))]
        if len(default_keys) < 3 and len(signal_options) > 0:
            remaining_keys = [k for k in signal_options.keys() if k not in default_keys]
            default_keys.extend(
                remaining_keys[: min(3 - len(default_keys), len(remaining_keys))]
            )

        selected_signals = st.multiselect(
            "Seleccionar señales para incluir:",
            options=list(signal_options.keys()),
            default=default_keys,
        )

        # Obtener las señales seleccionadas
        signals_to_include = [signal_options[key] for key in selected_signals]
    else:
        st.warning("No hay señales disponibles para incluir en el boletín.")
        signals_to_include = []

    # Configuración del boletín
    st.subheader("Paso 2: Configurar Boletín")

    # Obtener sentimiento de mercado y noticias
    market_sentiment = signal_manager.get_market_sentiment()
    market_news = signal_manager.get_market_news()

    # Permitir personalizar el boletín
    include_sentiment = st.checkbox("Incluir Sentimiento de Mercado", value=True)
    include_news = st.checkbox("Incluir Noticias Relevantes", value=True)

    # Permitir seleccionar cuántas señales detalladas mostrar
    if signals_to_include:
        max_detailed = min(len(signals_to_include), 5)
        num_detailed = st.slider(
            "Número de señales con análisis detallado a incluir",
            min_value=1,
            max_value=max_detailed,
            value=min(3, max_detailed),
            help="Las señales de alta confianza se mostrarán primero",
        )

        # Ordenar señales para mostrar alta confianza primero
        signals_to_include = sorted(
            signals_to_include,
            key=lambda x: (
                0 if x.get("is_high_confidence") == 1 else 1,
                (
                    0
                    if x.get("confidence_level") == "Alta"
                    else (1 if x.get("confidence_level") == "Media" else 2)
                ),
            ),
        )

        # Limitar las señales detalladas
        detailed_signals = signals_to_include[:num_detailed]
        summary_signals = signals_to_include
    else:
        detailed_signals = []
        summary_signals = []

    # Validar destinatarios
    if not destinatarios:
        st.warning("Por favor, ingrese al menos un destinatario en la barra lateral.")

    # Vista previa del boletín
    st.subheader("Paso 3: Vista Previa del Boletín")

    # Crear contenido HTML del boletín
    preview_sentiment = market_sentiment if include_sentiment else {}
    preview_news = market_news if include_news else []

    # Mostrar un mensaje de espera mientras se genera la vista previa
    with st.spinner("Generando vista previa del boletín..."):
        html_content = signal_manager.email_manager.create_newsletter_html(
            summary_signals, preview_sentiment, preview_news
        )

    # Mostrar vista previa
    with st.expander("Ver Vista Previa del Boletín", expanded=True):
        st.components.v1.html(html_content, height=600, scrolling=True)

    # Botón para enviar boletín
    st.subheader("Paso 4: Enviar Boletín")

    col1, col2 = st.columns([3, 1])
    with col1:
        if destinatarios:
            recipient_list = [
                email.strip() for email in destinatarios.split(",") if email.strip()
            ]
            st.write(f"Se enviará a: {', '.join(recipient_list)}")
        else:
            st.write("No hay destinatarios configurados.")

    with col2:
        send_button = st.button(
            "📩 Enviar Boletín",
            disabled=not destinatarios or len(signals_to_include) == 0,
        )

    # Opción para modo simulación (solo para desarrollo)
    simulation_mode = st.checkbox(
        "Modo simulación (sin enviar correo real)", value=False
    )

    if send_button:
        with st.spinner("Enviando boletín..."):
            if simulation_mode:
                # Simular envío exitoso
                logger.info(
                    f"[SIMULACIÓN] Simulando envío de boletín a: {', '.join(recipient_list)}"
                )
                time.sleep(2)  # Simular tiempo de envío
                success = True

                # Mostrar el contenido del correo en la consola para depuración
                logger.info(
                    "[SIMULACIÓN] Contenido del boletín (primeros 500 caracteres):"
                )
                logger.info(html_content[:500] + "...")
            else:
                # Usar la función real de envío de correos
                success = signal_manager.send_newsletter(
                    recipient_list,
                    summary_signals,
                    preview_sentiment,
                    preview_news,
                    include_pdf,
                )

            # Registrar el resultado en el log
            if success:
                msg = "Boletín enviado correctamente" + (
                    " (SIMULACIÓN)" if simulation_mode else ""
                )
                logger.info(f"{msg} a: {', '.join(recipient_list)}")
                st.success(f"{msg} a los destinatarios.")
            else:
                logger.error(f"Error al enviar boletín a: {', '.join(recipient_list)}")
                st.error(
                    "Error al enviar el boletín. Por favor, verifica la configuración de correo."
                )

# Contenido de la pestaña "Historial de Señales"
with tab3:
    st.header("📊 Historial de Señales y Envíos")

    # Crear pestañas para separar historial de señales y envíos
    hist_tab1, hist_tab2 = st.tabs(["Historial de Señales", "Registro de Envíos"])

    # Historial de señales
    with hist_tab1:
        st.subheader("Señales Registradas")

        # Filtros adicionales para el historial
        col1, col2, col3 = st.columns(3)
        with col1:
            hist_days = st.slider("Período (días)", 1, 90, 30, key="hist_days_slider")
        with col2:
            hist_direction = st.selectbox(
                "Dirección",
                ["Todas", "CALL (Compra)", "PUT (Venta)", "NEUTRAL"],
                key="hist_direction_selectbox",
            )
        with col3:
            hist_confidence = st.selectbox(
                "Confianza",
                ["Todas", "Alta", "Media", "Baja"],
                key="hist_confidence_selectbox",
            )

        # Filtro adicional para alta confianza
        col1, col2 = st.columns(2)
        with col1:
            hist_high_confidence = st.checkbox(
                "Solo señales de alta confianza",
                value=False,
                key="hist_high_confidence_checkbox",
            )
        with col2:
            hist_category = st.selectbox(
                "Categoría",
                [
                    "Todas",
                    "Tecnología",
                    "Finanzas",
                    "Salud",
                    "Energía",
                    "Consumo",
                    "Índices",
                    "Materias Primas",
                ],
                key="hist_category_selectbox",
            )

        # Obtener señales históricas de la base de datos
        try:
            # Construir la consulta base
            query = """SELECT * FROM trading_signals
                      WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"""
            params = [hist_days]

            # Añadir filtros adicionales si es necesario
            if hist_direction != "Todas":
                direction_filter = hist_direction.split(" ")[
                    0
                ]  # Extraer CALL, PUT o NEUTRAL
                query += " AND direction = %s"
                params.append(direction_filter)

            if hist_confidence != "Todas":
                query += " AND confidence_level = %s"
                params.append(hist_confidence)

            if hist_high_confidence:
                query += " AND is_high_confidence = 1"

            if hist_category != "Todas":
                query += " AND category = %s"
                params.append(hist_category)

            query += " ORDER BY created_at DESC"

            # Conectar a la base de datos y ejecutar la consulta
            db_manager = DatabaseManager()
            historic_signals = db_manager.execute_query(query, params)

            if historic_signals is not None:
                logger.info(
                    f"Se obtuvieron {len(historic_signals)} señales históricas de la base de datos"
                )

                # Convertir valores Decimal a float
                for signal in historic_signals:
                    for key, value in signal.items():
                        if isinstance(value, decimal.Decimal):
                            signal[key] = float(value)
            else:
                logger.warning("No se pudieron obtener señales históricas")
                historic_signals = []
        except Exception as e:
            logger.error(f"Error al obtener señales históricas: {str(e)}")
            st.error(f"Error al obtener datos de la base de datos: {str(e)}")
            historic_signals = []

        # Mostrar tabla de señales
        if historic_signals and len(historic_signals) > 0:
            # Convertir a DataFrame para mejor visualización
            df_signals = pd.DataFrame(historic_signals)

            # Formatear columnas para visualización
            if "created_at" in df_signals.columns:
                df_signals["Fecha"] = df_signals["created_at"].apply(
                    lambda x: (
                        x.strftime("%d/%m/%Y %H:%M")
                        if isinstance(x, datetime)
                        else str(x)
                    )
                )

            # Formatear la dirección (CALL/PUT/NEUTRAL) para mejor visualización
            if "direction" in df_signals.columns:
                df_signals["Dirección"] = df_signals["direction"].apply(
                    lambda x: (
                        "📈 Compra"
                        if x == "CALL"
                        else "📉 Venta" if x == "PUT" else "↔️ Neutral"
                    )
                )

            # Indicar señales de alta confianza
            if "is_high_confidence" in df_signals.columns:
                df_signals["Alta Conf."] = df_signals["is_high_confidence"].apply(
                    lambda x: "⭐" if x == 1 else ""
                )

            # Seleccionar y renombrar columnas para la tabla
            display_cols = {
                "symbol": "Símbolo",
                "Dirección": "Dirección",
                "price": "Precio",
                "entry_price": "Entrada",
                "stop_loss": "Stop Loss",
                "target_price": "Objetivo",
                "risk_reward": "R/R",
                "confidence_level": "Confianza",
                "Alta Conf.": "Alta Conf.",
                "strategy": "Estrategia",
                "setup_type": "Setup",
                "category": "Categoría",
                "Fecha": "Fecha",
            }

            # Crear DataFrame para mostrar (seleccionar solo columnas disponibles)
            available_cols = [c for c in display_cols.keys() if c in df_signals.columns]
            df_display = df_signals[available_cols].copy()
            df_display.columns = [display_cols[c] for c in available_cols]

            # Aplicar formato condicional para la columna de dirección
            styled_df = df_display.style

            # Aquí aplicamos estilos manualmente para evitar problemas de compatibilidad
            if "Dirección" in df_display.columns:
                styled_df = styled_df.applymap(
                    lambda x: (
                        "color: #28a745; font-weight: bold"
                        if "Compra" in str(x)
                        else (
                            "color: #dc3545; font-weight: bold"
                            if "Venta" in str(x)
                            else "color: #6c757d"
                        )
                    ),
                    subset=["Dirección"],
                )

            # Mostrar tabla con estilo
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Opción para exportar datos
            if st.button("📥 Exportar a CSV", key="export_signals"):
                # Generar CSV para descarga
                csv = df_display.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"senales_trading_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
        else:
            st.info("No se encontraron señales con los filtros seleccionados.")

    # Registro de envíos
    with hist_tab2:
        st.subheader("Registro de Boletines Enviados")

        # Obtener datos de envíos de la base de datos
        try:
            # Consultar los últimos 30 días de envíos
            query = """SELECT id, recipients, subject, content_summary, signals_included, sent_at, status, error_message
                      FROM email_logs
                      WHERE sent_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                      ORDER BY sent_at DESC"""

            # Conectar a la base de datos y ejecutar la consulta
            db_manager = DatabaseManager()
            email_logs = db_manager.execute_query(query)

            if email_logs is not None:
                logger.info(
                    f"Se obtuvieron {len(email_logs)} registros de envíos de la base de datos"
                )
            else:
                logger.warning("No se pudieron obtener registros de envíos")
                email_logs = []
        except Exception as e:
            logger.error(f"Error al obtener registros de envíos: {str(e)}")
            st.error(f"Error al obtener datos de la base de datos: {str(e)}")
            email_logs = []

        # Mostrar tabla de envíos
        if email_logs and len(email_logs) > 0:
            # Convertir a DataFrame
            df_emails = pd.DataFrame(email_logs)

            # Formatear fecha
            if "sent_at" in df_emails.columns:
                df_emails["Fecha de Envío"] = df_emails["sent_at"].apply(
                    lambda x: (
                        x.strftime("%d/%m/%Y %H:%M")
                        if isinstance(x, datetime)
                        else str(x)
                    )
                )

            # Formatear estado
            if "status" in df_emails.columns:
                df_emails["Estado"] = df_emails["status"].apply(
                    lambda x: "✅ Exitoso" if x == "success" else "❌ Fallido"
                )

            # Seleccionar columnas para mostrar
            display_cols = {
                "subject": "Asunto",
                "recipients": "Destinatarios",
                "content_summary": "Contenido",
                "signals_included": "Señales Incluidas",
                "Estado": "Estado",
                "Fecha de Envío": "Fecha de Envío",
            }

            # Crear DataFrame para mostrar
            df_display = df_emails[
                [c for c in display_cols.keys() if c in df_emails.columns]
            ].copy()
            df_display.columns = [display_cols[c] for c in df_display.columns]

            # Aplicar formato condicional para la columna de estado
            styled_df = df_display.style

            if "Estado" in df_display.columns:
                styled_df = styled_df.applymap(
                    lambda x: (
                        "color: #28a745; font-weight: bold"
                        if "Exitoso" in str(x)
                        else "color: #dc3545; font-weight: bold"
                    ),
                    subset=["Estado"],
                )

            # Mostrar tabla
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Añadir explicación detallada del significado de "Señales Incluidas"
            st.info(
                """
            **Nota sobre "Señales Incluidas"**:
            Los números que aparecen en esta columna son los IDs de las señales de trading que fueron incluidas en el boletín.
            Estos IDs corresponden a los registros en la base de datos de señales de trading (tabla `trading_signals`).

            **Proceso completo cuando se envía un boletín:**
            1. **Guardado de señales:** Cada señal seleccionada se guarda en la base de datos, generando un ID único.
            2. **Guardado de sentimiento:** El sentimiento de mercado incluido en el boletín se guarda en la tabla `market_sentiment`.
            3. **Guardado de noticias:** Las noticias relevantes incluidas se guardan en la tabla `market_news`.
            4. **Registro del envío:** Se crea un registro en la tabla `email_logs` que incluye los IDs de las señales enviadas.

            **Beneficios de este sistema:**
            - **Trazabilidad completa:** Permite rastrear qué señales específicas se enviaron en cada boletín.
            - **Análisis de rendimiento:** Facilita el análisis posterior del rendimiento de las señales enviadas.
            - **Histórico de datos:** Mantiene un registro histórico completo del sentimiento de mercado y noticias relevantes.
            """
            )
        else:
            st.info("No hay registros de envíos de boletines.")
