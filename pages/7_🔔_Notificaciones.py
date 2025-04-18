import streamlit as st
import pandas as pd
import logging
import socket
import time
import smtplib
import mysql.connector
import sys
import os
import decimal

# import tempfile  # No se utiliza, usar carpeta 'temp' para archivos temporales
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta

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
        # No guardamos el sentimiento de mercado aquí, ya que se carga al inicio de la aplicación principal
        logger.info(
            "Omitiendo guardado de sentimiento de mercado, ya que se carga al inicio de la aplicación principal"
        )
        return None

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

        # Asegurar que el símbolo esté presente
        if not news_data.get("symbol"):
            news_data["symbol"] = "SPY"  # Valor por defecto

        # Traducir y condensar el título y resumen al español
        try:
            # Importar función para obtener análisis del experto
            sys.path.append(
                os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            )
            from ai_utils import get_expert_analysis

            # Detectar palabras en inglés para verificación
            english_words = [
                "the",
                "and",
                "why",
                "what",
                "how",
                "is",
                "are",
                "to",
                "for",
                "in",
                "on",
                "at",
                "stock",
                "market",
                "shares",
                "price",
                "report",
                "earnings",
                "revenue",
                "growth",
                "investors",
                "trading",
                "financial",
                "company",
                "business",
                "quarter",
                "year",
            ]

            # Procesar título - siempre traducir para asegurar consistencia
            title = news_data.get("title", "")
            if title and not title.startswith("Error") and len(title) > 5:
                # Verificar si está en inglés
                is_english = any(
                    word.lower() in title.lower().split() for word in english_words
                )

                # Traducir título (siempre, para asegurar calidad)
                prompt = f"""Traduce este título de noticia financiera al español de forma profesional y concisa.
                Si ya está en español, mejóralo para que sea claro y profesional: '{title}'"""

                translated_title = get_expert_analysis(prompt)
                if translated_title and len(translated_title) > 5:
                    news_data["title"] = translated_title.strip()
                    logger.info(f"Título procesado: {news_data['title']}")

            # Procesar resumen - siempre crear uno si no existe o mejorarlo si existe
            summary = news_data.get("summary", "")

            # Si no hay resumen o es muy corto, intentar generarlo desde el título
            if not summary or len(summary) < 20:
                if title and len(title) > 10:
                    prompt = f"""Genera un resumen informativo en español (máximo 200 caracteres) para una noticia financiera
                    con este título: '{title}'. El resumen debe ser profesional, informativo y relevante para inversores."""

                    generated_summary = get_expert_analysis(prompt)
                    if generated_summary and len(generated_summary) > 20:
                        news_data["summary"] = generated_summary.strip()
                        logger.info(f"Resumen generado: {news_data['summary']}")
            else:
                # Hay un resumen, verificar si está en inglés
                is_english = any(
                    word.lower() in summary.lower().split() for word in english_words
                )

                # Traducir y mejorar el resumen
                prompt = f"""Traduce y mejora este resumen de noticia financiera al español de forma profesional y concisa (máximo 200 caracteres).
                Si ya está en español, mejóralo para que sea claro, informativo y relevante para inversores: '{summary}'"""

                processed_summary = get_expert_analysis(prompt)
                if processed_summary and len(processed_summary) > 20:
                    news_data["summary"] = processed_summary.strip()
                    logger.info(f"Resumen procesado: {news_data['summary']}")
        except Exception as e:
            logger.warning(f"No se pudo procesar la noticia: {str(e)}")
            # Asegurar que hay un resumen mínimo si falló el procesamiento
            if not news_data.get("summary") and news_data.get("title"):
                news_data["summary"] = (
                    f"Noticia relacionada con {news_data.get('symbol')}: {news_data.get('title')}"
                )

        # Asegurar que siempre haya un resumen
        if not news_data.get("summary") and news_data.get("title"):
            news_data["summary"] = (
                f"Noticia relacionada con {news_data.get('symbol', 'mercado')}: {news_data.get('title')}"
            )
            logger.info(f"Generando resumen básico para noticia: {news_data['title']}")

        # Si no existe, insertar la noticia
        query = """INSERT INTO market_news
                  (title, summary, source, url, news_date, impact, symbol, created_at)
                  VALUES (%s, %s, %s, %s, NOW(), %s, %s, NOW())"""

        params = (
            news_data.get("title"),
            news_data.get(
                "summary", f"Noticia sobre {news_data.get('symbol', 'mercado')}"
            ),  # Valor por defecto
            news_data.get("source"),
            news_data.get("url", ""),
            news_data.get("impact", "Medio"),
            news_data.get("symbol"),
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
        """Crea el contenido HTML para el boletín de trading con diseño mejorado optimizado para clientes de correo"""
        # Fecha actual formateada
        current_date = datetime.now().strftime("%d de %B de %Y")

        # Encabezado del boletín con diseño mejorado para compatibilidad con clientes de correo
        html = f"""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
            <title>InversorIA Pro - Boletín de Trading {current_date}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333333; background-color: #f9f9f9;">
            <!-- Contenedor principal -->
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse;">
                <tr>
                    <td style="padding: 20px 0;">
                        <!-- Contenido central limitado a 600px para mejor visualización -->
                        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 8px;">

                            <!-- HEADER -->
                            <tr>
                                <td align="center" bgcolor="#2c3e50" style="padding: 30px 20px; color: #ffffff; border-radius: 8px 8px 0 0; background: linear-gradient(135deg, #2c3e50 0%, #1a2a3a 100%);">
                                    <h1 style="margin: 0; font-size: 28px; font-weight: bold; font-family: Arial, sans-serif;">InversorIA Pro - Boletín de Trading</h1>
                                    <p style="margin: 10px 0 0; font-size: 16px; font-family: Arial, sans-serif;">{current_date}</p>
                                </td>
                            </tr>

                            <!-- CONTENIDO -->
                            <tr>
                                <td style="padding: 30px 20px;">
                                    <!-- Introducción contextual del boletín -->
                                    <div style="margin-bottom: 30px;">
                                        <p style="margin: 0 0 15px; line-height: 1.6; color: #444;">
                                            Estimado inversor,
                                        </p>
                                        <p style="margin: 0 0 15px; line-height: 1.6; color: #444;">
                                            Le presentamos nuestro boletín de trading con las oportunidades más relevantes identificadas por InversorIA Pro.
                                            En un mercado caracterizado por {self._get_market_context(market_sentiment)},
                                            nuestros algoritmos han detectado señales que podrían representar oportunidades significativas.
                                        </p>
                                        <p style="margin: 0 0 15px; line-height: 1.6; color: #444;">
                                            A continuación encontrará un análisis detallado de cada activo, con recomendaciones específicas
                                            y niveles clave a vigilar. Recuerde que estas señales son el resultado de un análisis técnico y fundamental
                                            exhaustivo, complementado con la evaluación de nuestro Trading Specialist.
                                        </p>
                                    </div>

                                    <h2 style="color: #2c3e50; font-size: 22px; margin-top: 0; margin-bottom: 20px; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; font-family: Arial, sans-serif;">Señales de Trading Recientes</h2>
        """

        # Tabla de señales
        if signals and len(signals) > 0:
            html += """
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 30px;">
                <tr style="background-color: #f2f6f9;">
                    <th style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; font-size: 14px; font-weight: bold; color: #2c3e50;">Símbolo</th>
                    <th style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; font-size: 14px; font-weight: bold; color: #2c3e50;">Dirección</th>
                    <th style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; font-size: 14px; font-weight: bold; color: #2c3e50;">Precio</th>
                    <th style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; font-size: 14px; font-weight: bold; color: #2c3e50;">Confianza</th>
                    <th style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; font-size: 14px; font-weight: bold; color: #2c3e50;">Timeframe</th>
                </tr>
            """

            for signal in signals:
                # Determinar color de fondo según nivel de confianza
                if signal.get("confidence_level") == "Alta":
                    bg_color = "#d4edda"
                elif signal.get("confidence_level") == "Media":
                    bg_color = "#fff3cd"
                else:
                    bg_color = "#f8f9fa"

                if signal.get("direction") == "CALL":
                    direction_color = "#28a745"
                    direction_text = "Compra"
                elif signal.get("direction") == "PUT":
                    direction_color = "#dc3545"
                    direction_text = "Venta"
                else:
                    direction_color = "#6c757d"
                    direction_text = "Neutral"

                # Obtener nombre completo de la empresa
                symbol = signal.get("symbol", "")
                company_name = ""
                if symbol:
                    # Importar función para obtener información de la empresa
                    try:
                        from company_data import get_company_info

                        company_info = get_company_info(symbol)
                        company_name = company_info.get("name", "")
                    except Exception as e:
                        logger.warning(
                            f"No se pudo obtener información de la empresa para {symbol}: {str(e)}"
                        )

                # Mostrar símbolo y nombre completo
                symbol_display = symbol
                if company_name:
                    symbol_display = f"{symbol}<br/><span style='font-size: 11px; font-weight: normal; color: #666;'>{company_name}</span>"

                # Determinar color de fondo de la fila según la dirección
                if signal.get("direction") == "CALL":
                    row_bg_color = "#e8f5e9"  # Verde claro para CALL
                elif signal.get("direction") == "PUT":
                    row_bg_color = "#ffebee"  # Rojo claro para PUT
                else:
                    row_bg_color = (
                        bg_color  # Mantener el color original basado en confianza
                    )

                # Obtener parámetros del activo desde market_utils.py
                asset_params = {}
                try:
                    from market_utils import MarketUtils

                    market_utils = MarketUtils()
                    symbol_key = signal.get("symbol", "")
                    if symbol_key in market_utils.options_params:
                        asset_params = market_utils.options_params[symbol_key]
                except Exception as e:
                    logger.warning(
                        f"No se pudieron obtener parámetros del activo para {signal.get('symbol', '')}: {str(e)}"
                    )

                # Crear cadena de parámetros del activo
                params_str = ""
                if asset_params:
                    params_list = []
                    if "costo_strike" in asset_params:
                        params_list.append(
                            f"Costo strike: {asset_params['costo_strike']}"
                        )
                    if "volumen_min" in asset_params:
                        params_list.append(
                            f"Volumen mínimo: {asset_params['volumen_min']}"
                        )
                    if "distance_spot_strike" in asset_params:
                        params_list.append(
                            f"Distancia spot-strike: {asset_params['distance_spot_strike']}"
                        )

                    if params_list:
                        params_str = f"<br/><span style='font-size: 10px; color: #666;'>{' | '.join(params_list)}</span>"

                html += f"""
                <tr style="background-color: {row_bg_color};">
                    <td style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #f2f2f2; font-weight: bold;">{symbol_display}{params_str}</td>
                    <td style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #f2f2f2; color: {direction_color}; font-weight: bold;">{direction_text}</td>
                    <td style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #f2f2f2;">${signal.get('price', '0.00')}</td>
                    <td style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #f2f2f2;">{signal.get('confidence_level', 'Baja')}</td>
                    <td style="padding: 12px 15px; text-align: left; border-bottom: 1px solid #f2f2f2;">{signal.get('timeframe', 'Corto')}</td>
                </tr>
                """

            html += "</table>"

            # Sección de análisis detallado
            high_confidence_signals = [
                s
                for s in signals
                if s.get("is_high_confidence") == 1
                or s.get("confidence_level") == "Alta"
            ]

            if high_confidence_signals:
                html += """
                <h2 style="color: #2c3e50; font-size: 22px; margin-top: 30px; margin-bottom: 20px; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; font-family: Arial, sans-serif;">Análisis Detallado de Señales</h2>
                """

                for signal in high_confidence_signals:
                    symbol = signal.get("symbol", "")
                    direction = signal.get("direction", "NEUTRAL")

                    # Color según dirección
                    if direction == "CALL":
                        border_color = "#28a745"
                        direction_text = "Compra"
                        direction_color = "#28a745"
                    elif direction == "PUT":
                        border_color = "#dc3545"
                        direction_text = "Venta"
                        direction_color = "#dc3545"
                    else:
                        border_color = "#6c757d"
                        direction_text = "Neutral"
                        direction_color = "#6c757d"

                    # Obtener datos básicos para la visualización
                    entry_price = signal.get("entry_price")
                    stop_loss = signal.get("stop_loss")
                    target_price = signal.get("target_price")
                    risk_reward = signal.get("risk_reward")

                    # Obtener nombre completo de la empresa para la señal detallada
                    company_name = ""
                    company_description = ""
                    if symbol:
                        try:
                            from company_data import get_company_info

                            company_info = get_company_info(symbol)
                            company_name = company_info.get("name", "")
                            company_description = company_info.get("description", "")
                        except Exception as e:
                            logger.warning(
                                f"No se pudo obtener información detallada de la empresa para {symbol}: {str(e)}"
                            )

                    # Inicializar variables de tendencia
                    trend = signal.get("trend", "")
                    trend_strength = signal.get("trend_strength", "")
                    trend_bg = "#ffffff"  # Color por defecto

                    # Determinar color de fondo según tendencia si está disponible
                    if trend:
                        if "ALCISTA" in trend.upper():
                            trend_bg = "#e8f5e9"  # Verde claro para tendencia alcista
                        elif "BAJISTA" in trend.upper():
                            trend_bg = "#ffebee"  # Rojo claro para tendencia bajista
                        else:
                            trend_bg = "#f5f5f5"  # Gris claro para tendencia neutral

                    html += f"""
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 30px; border-left: 4px solid {border_color}; background-color: {trend_bg}; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);" class="signal-{direction_text.lower()}">
                        <tr>
                            <td style="padding: 20px;">
                                <!-- Encabezado de la señal con más información -->
                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div>
                                        <h3 style="margin-top: 0; color: {direction_color}; font-size: 18px; font-weight: bold; margin-bottom: 5px;">
                                            {symbol} - {direction_text}
                                        </h3>
                                        <p style="margin: 0 0 5px; color: #444; font-size: 15px;">{company_name}</p>
                                        {f'<p style="margin: 0 0 15px; color: #666; font-size: 13px; font-style: italic;">{company_description}</p>' if company_description else ''}
                                    </div>
                                    <div style="text-align: right;">
                                        <span style="display: inline-block; padding: 5px 10px; background-color: {direction_color}; color: white; border-radius: 20px; font-size: 12px; font-weight: bold;">{signal.get('confidence_level', 'Media')}</span>
                                        {f'<p style="margin: 5px 0 0; font-size: 12px; color: #666;">Actualizado: {signal.get("created_at").strftime("%d/%m/%Y") if isinstance(signal.get("created_at"), datetime) else "Hoy"}</p>' if signal.get("created_at") else ''}
                                    </div>
                                </div>

                                <!-- Información básica -->
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 15px;">
                                    <tr>
                                        <td width="50%" style="padding: 8px 0;"><strong>Estrategia:</strong> {signal.get('strategy', 'N/A')}</td>
                                        <td width="50%" style="padding: 8px 0;"><strong>Confianza:</strong> {signal.get('confidence_level', 'N/A')}</td>
                                    </tr>
                                    <tr>
                                        <td width="50%" style="padding: 8px 0;"><strong>Categoría:</strong> {signal.get('category', 'N/A')}</td>
                                        <td width="50%" style="padding: 8px 0;"><strong>Timeframe:</strong> {signal.get('timeframe', 'N/A')}</td>
                                    </tr>
                                </table>
                    """

                    # Precios objetivos si están disponibles
                    if entry_price or stop_loss or target_price:
                        html += """
                        <!-- Precios objetivos -->
                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 15px; background-color: #f8f9fa; border-radius: 4px;">
                            <tr>
                        """

                        if entry_price:
                            html += f"""
                            <td align="center" width="33%" style="padding: 12px;">
                                <p style="margin: 0; font-size: 12px; color: #6c757d;">Entrada</p>
                                <p style="margin: 5px 0 0; font-size: 16px; font-weight: bold; color: #0275d8;">${entry_price}</p>
                            </td>
                            """

                        if stop_loss:
                            html += f"""
                            <td align="center" width="33%" style="padding: 12px;">
                                <p style="margin: 0; font-size: 12px; color: #6c757d;">Stop Loss</p>
                                <p style="margin: 5px 0 0; font-size: 16px; font-weight: bold; color: #dc3545;">${stop_loss}</p>
                            </td>
                            """

                        if target_price:
                            html += f"""
                            <td align="center" width="33%" style="padding: 12px;">
                                <p style="margin: 0; font-size: 12px; color: #6c757d;">Objetivo</p>
                                <p style="margin: 5px 0 0; font-size: 16px; font-weight: bold; color: #28a745;">${target_price}</p>
                            </td>
                            """

                        html += """
                            </tr>
                        </table>
                        """

                        # Ratio riesgo/recompensa
                        if risk_reward:
                            rr_color = (
                                "#28a745"
                                if risk_reward >= 2
                                else ("#6c757d" if risk_reward >= 1 else "#dc3545")
                            )
                            html += f"""
                            <p style="margin: 10px 0; text-align: center;">
                                <span style="background-color: #f2f6f9; padding: 6px 12px; border-radius: 4px; font-weight: bold; color: {rr_color};">
                                    R/R: {risk_reward:.2f}
                                </span>
                            </p>
                            """

                    # Tendencias - usar las variables ya definidas
                    if trend:
                        trend_color = (
                            "#28a745"
                            if "ALCISTA" in trend.upper()
                            else (
                                "#dc3545" if "BAJISTA" in trend.upper() else "#6c757d"
                            )
                        )
                        # trend_bg ya está definido arriba

                        html += f"""
                        <p style="margin: 15px 0 5px; font-size: 14px; color: #6c757d;">Tendencia:</p>
                        <p style="margin: 0 0 15px; padding: 8px 12px; background-color: {trend_bg}; display: inline-block; border-radius: 4px; color: {trend_color}; font-weight: bold;">
                            {trend} {f'({trend_strength})' if trend_strength else ''}
                        </p>
                        """

                    # Timeframes adicionales
                    timeframes_available = (
                        signal.get("daily_trend")
                        or signal.get("weekly_trend")
                        or signal.get("monthly_trend")
                    )

                    if timeframes_available:
                        html += """
                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin: 15px 0; background-color: #f8f9fa; border-radius: 4px;">
                            <tr>
                        """

                        if signal.get("daily_trend"):
                            dt = signal.get("daily_trend")
                            dt_color = (
                                "#28a745"
                                if "ALCISTA" in dt.upper()
                                else (
                                    "#dc3545" if "BAJISTA" in dt.upper() else "#6c757d"
                                )
                            )
                            html += f"""
                            <td width="33%" style="padding: 10px; text-align: center;">
                                <p style="margin: 0; font-size: 12px; color: #6c757d;">Diario</p>
                                <p style="margin: 5px 0 0; color: {dt_color}; font-weight: bold;">{dt}</p>
                            </td>
                            """

                        if signal.get("weekly_trend"):
                            wt = signal.get("weekly_trend")
                            wt_color = (
                                "#28a745"
                                if "ALCISTA" in wt.upper()
                                else (
                                    "#dc3545" if "BAJISTA" in wt.upper() else "#6c757d"
                                )
                            )
                            html += f"""
                            <td width="33%" style="padding: 10px; text-align: center;">
                                <p style="margin: 0; font-size: 12px; color: #6c757d;">Semanal</p>
                                <p style="margin: 5px 0 0; color: {wt_color}; font-weight: bold;">{wt}</p>
                            </td>
                            """

                        if signal.get("monthly_trend"):
                            mt = signal.get("monthly_trend")
                            mt_color = (
                                "#28a745"
                                if "ALCISTA" in mt.upper()
                                else (
                                    "#dc3545" if "BAJISTA" in mt.upper() else "#6c757d"
                                )
                            )
                            html += f"""
                            <td width="33%" style="padding: 10px; text-align: center;">
                                <p style="margin: 0; font-size: 12px; color: #6c757d;">Mensual</p>
                                <p style="margin: 5px 0 0; color: {mt_color}; font-weight: bold;">{mt}</p>
                            </td>
                            """

                        html += """
                            </tr>
                        </table>
                        """

                    # Verificar si hay un error en el análisis experto
                    expert_analysis = signal.get("expert_analysis", "")
                    has_expert_error = False

                    # Detectar errores comunes en el análisis experto
                    if (
                        expert_analysis
                        and "st.session_state has no attribute" in expert_analysis
                    ):
                        has_expert_error = True
                        logger.warning(
                            f"Error detectado en el análisis experto para {signal.get('symbol', '')}: {expert_analysis[:100]}..."
                        )

                    # Usar el análisis experto si está disponible y no tiene errores, o los análisis básicos si no
                    if (
                        expert_analysis
                        and len(expert_analysis) > 50
                        and not has_expert_error
                    ):  # Verificar que sea un análisis sustancial
                        # Convertir el formato markdown a HTML para el correo
                        try:
                            # Importar markdown para convertir el formato
                            import markdown

                            # Convertir markdown a HTML
                            expert_html = markdown.markdown(expert_analysis)

                            # Aplicar estilos adicionales para mejorar la presentación
                            expert_html = expert_html.replace(
                                "<h2>",
                                '<h2 style="color: #2c3e50; font-size: 18px; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;">',
                            )
                            expert_html = expert_html.replace(
                                "<p>",
                                '<p style="margin: 10px 0; font-size: 14px; line-height: 1.6; color: #444;">',
                            )
                            expert_html = expert_html.replace(
                                "<ul>",
                                '<ul style="margin: 10px 0; padding-left: 20px;">',
                            )
                            expert_html = expert_html.replace(
                                "<li>",
                                '<li style="margin: 5px 0; font-size: 14px; line-height: 1.6; color: #444;">',
                            )

                            html += f"""
                            <div style="margin-top: 15px; background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
                                {expert_html}
                            </div>
                            """
                        except Exception as e:
                            logger.warning(
                                f"Error al convertir markdown a HTML: {str(e)}"
                            )
                            # Si falla la conversión, mostrar el texto plano con formato básico
                            html += f"""
                            <div style="margin-top: 15px; background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
                                <pre style="white-space: pre-wrap; font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #444;">{expert_analysis}</pre>
                            </div>
                            """
                    else:
                        # Usar los análisis básicos si no hay análisis experto o hay errores
                        analysis_content = signal.get("analysis", "")
                        technical_analysis_content = signal.get(
                            "technical_analysis", ""
                        )

                        # Si hay contenido en alguno de los campos de análisis, usarlo
                        if analysis_content and len(analysis_content) > 10:
                            html += f"""
                            <div style="margin-top: 15px; background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
                                <h3 style="margin-top: 0; color: #2c3e50; font-size: 16px;">Análisis Fundamental</h3>
                                <p style="margin: 10px 0; font-size: 14px; line-height: 1.6; color: #444;">
                                    {analysis_content}
                                </p>
                            </div>
                            """
                        else:
                            html += f"""
                            <p style="margin: 15px 0; font-size: 15px; line-height: 1.6; font-style: italic; color: #666;">
                                No hay análisis fundamental disponible para este activo.
                            </p>
                            """

                        # Añadir análisis técnico si está disponible
                        if (
                            technical_analysis_content
                            and len(technical_analysis_content) > 10
                        ):
                            html += f"""
                            <div style="margin-top: 15px; background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
                                <h3 style="margin-top: 0; color: #2c3e50; font-size: 16px;">Análisis Técnico</h3>
                                <p style="margin: 10px 0; font-size: 14px; line-height: 1.6; color: #444;">
                                    {technical_analysis_content}
                                </p>
                            </div>
                            """
                        elif not analysis_content or len(analysis_content) <= 10:
                            html += f"""
                            <p style="margin: 15px 0; font-size: 15px; line-height: 1.6; font-style: italic; color: #666;">
                                No hay análisis técnico disponible para este activo.
                            </p>
                            """

                    # Recomendación final
                    recommendation = signal.get("recommendation")
                    if recommendation:
                        rec_color = (
                            "#28a745"
                            if "COMPRAR" in recommendation.upper()
                            else (
                                "#dc3545"
                                if "VENDER" in recommendation.upper()
                                else "#6c757d"
                            )
                        )
                        rec_bg = (
                            "#e8f5e9"
                            if "COMPRAR" in recommendation.upper()
                            else (
                                "#ffebee"
                                if "VENDER" in recommendation.upper()
                                else "#f5f5f5"
                            )
                        )

                        html += f"""
                        <div style="margin: 20px 0 10px; text-align: center;">
                            <p style="margin: 0 0 8px; font-size: 14px; color: #6c757d;">Recomendación Final</p>
                            <p style="margin: 0; display: inline-block; padding: 8px 20px; background-color: {rec_bg};
                                    border: 2px solid {rec_color}; border-radius: 20px; font-size: 16px; font-weight: bold; color: {rec_color};">
                                {recommendation}
                            </p>
                        </div>
                        """

                    html += """
                            </td>
                        </tr>
                    </table>
                    """
        else:
            html += """
            <p style="margin-bottom: 30px; color: #6c757d; font-style: italic;">No hay señales de trading disponibles en este momento.</p>
            """

        # Sección de sentimiento de mercado
        if market_sentiment:
            # Determinar colores según el sentimiento
            if market_sentiment.get("overall") == "Alcista":
                sentiment_border = "#28a745"
                sentiment_bg = "#e8f5e9"
            elif market_sentiment.get("overall") == "Bajista":
                sentiment_border = "#dc3545"
                sentiment_bg = "#ffebee"
            else:
                sentiment_border = "#6c757d"
                sentiment_bg = "#f5f5f5"

            html += f"""
            <h2 style="color: #2c3e50; font-size: 22px; margin-top: 30px; margin-bottom: 20px; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; font-family: Arial, sans-serif;">Sentimiento de Mercado</h2>

            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 30px; background-color: {sentiment_bg}; border-left: 4px solid {sentiment_border}; border-radius: 4px;">
                <tr>
                    <td style="padding: 20px;">
                        <h3 style="margin-top: 0; margin-bottom: 15px; font-size: 18px; color: #2c3e50;">Sentimiento General: {market_sentiment.get('overall', 'Neutral')}</h3>

                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse;">
                            <tr>
                                <td width="50%" style="padding: 8px 0;"><strong>VIX:</strong> {market_sentiment.get('vix', 'N/A')}</td>
                                <td width="50%" style="padding: 8px 0;"><strong>S&P 500:</strong> {market_sentiment.get('sp500_trend', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td width="50%" style="padding: 8px 0;"><strong>Indicadores Técnicos:</strong> {market_sentiment.get('technical_indicators', 'N/A')}</td>
                                <td width="50%" style="padding: 8px 0;"><strong>Volumen:</strong> {market_sentiment.get('volume', 'N/A')}</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            """

        # Sección de noticias
        html += """
        <h2 style="color: #2c3e50; font-size: 22px; margin-top: 30px; margin-bottom: 20px; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; font-family: Arial, sans-serif;">Noticias Relevantes</h2>
        <p style="margin: 0 0 20px; line-height: 1.6; color: #444;">
            A continuación presentamos las noticias más relevantes que podrían impactar sus decisiones de inversión.
            Estas noticias han sido seleccionadas por su potencial impacto en los mercados y en los activos destacados en este boletín.
        </p>
        """

        if news_summary and len(news_summary) > 0:
            for item in news_summary:
                # Formatear fecha
                news_date = item.get("news_date", datetime.now())
                if isinstance(news_date, datetime):
                    formatted_date = news_date.strftime("%d %b %Y")
                else:
                    formatted_date = str(news_date)

                # Color según impacto
                impact = item.get("impact", "Medio")
                if impact == "Alto":
                    impact_color = "#dc3545"
                elif impact == "Medio":
                    impact_color = "#fd7e14"
                else:
                    impact_color = "#6c757d"

                # Obtener información de la empresa para la noticia
                symbol = item.get("symbol", "")
                company_name = ""
                if symbol:
                    try:
                        from company_data import get_company_info

                        company_info = get_company_info(symbol)
                        company_name = company_info.get("name", "")
                    except Exception as e:
                        logger.warning(
                            f"No se pudo obtener información de la empresa para noticia de {symbol}: {str(e)}"
                        )

                # Preparar enlace si hay URL
                title_display = item.get("title", "")
                url = item.get("url", "")
                if url and len(url) > 5:
                    title_display = f"<a href='{url}' target='_blank' style='color: #0275d8; text-decoration: none;'>{item.get('title', '')} <span style='font-size: 12px;'>&#128279;</span></a>"

                html += f"""
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse: collapse; margin-bottom: 20px; background-color: #ffffff; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <tr>
                        <td style="padding: 20px;">
                            <h3 style="margin-top: 0; margin-bottom: 10px; color: #0275d8; font-size: 18px;">{title_display}</h3>
                            {f'<p style="margin: 0 0 10px; font-size: 13px; color: #444;"><strong>{symbol}</strong> - {company_name}</p>' if symbol and company_name else ''}
                            <p style="margin: 0 0 15px; line-height: 1.6;">{item.get('summary', '')}</p>
                            <p style="margin: 0; font-size: 12px; color: #6c757d;">
                                {f'<span style="color: {impact_color}; font-weight: bold;">Impacto: {impact}</span> &bull; ' if impact else ''}
                                Fuente: {item.get('source', '')} &bull; {formatted_date}
                            </p>
                        </td>
                    </tr>
                </table>
                """
        else:
            html += """
            <p style="margin-bottom: 30px; color: #6c757d; font-style: italic;">No hay noticias relevantes disponibles en este momento.</p>
            """

        # Pie de página
        html += """
                                </td>
                            </tr>

                            <!-- FOOTER -->
                            <tr>
                                <td style="padding: 30px 20px; background-color: #f8f9fa; border-top: 1px solid #eaeaea; border-radius: 0 0 8px 8px; color: #6c757d; text-align: center; font-size: 12px;">
                                    <p style="margin: 0 0 15px;"><strong>Aviso importante:</strong> Este boletín es generado automáticamente por InversorIA Pro. La información proporcionada es solo para fines educativos y no constituye asesoramiento financiero.</p>
                                    <p style="margin: 0 0 15px;">Los datos presentados son calculados utilizando análisis técnico avanzado, algoritmos de inteligencia artificial y evaluación de expertos en trading. Recuerde que toda inversión conlleva riesgos y los resultados pasados no garantizan rendimientos futuros.</p>
                                    <p style="margin: 0 0 15px;">Para obtener análisis más detallados y personalizados, le recomendamos consultar la plataforma completa de InversorIA Pro, donde encontrará herramientas adicionales y funcionalidades avanzadas.</p>
                                    <p style="margin: 0;">&copy; 2025 InversorIA Pro. Todos los derechos reservados.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        return html

    def _get_market_context(self, market_sentiment):
        """Genera un contexto de mercado basado en el sentimiento"""
        if not market_sentiment:
            return "un mercado en constante evolución"

        overall = market_sentiment.get("overall", "Neutral")
        vix_value = market_sentiment.get("vix", "")
        sp500_trend = market_sentiment.get("sp500_trend", "")
        volume = market_sentiment.get("volume", "")

        # Convertir valores numéricos a cadenas de texto
        vix_description = ""
        if vix_value is not None:
            try:
                # Si es un valor numérico, interpretarlo
                if isinstance(vix_value, (int, float)) or (
                    isinstance(vix_value, str)
                    and vix_value.replace(".", "", 1).isdigit()
                ):
                    vix_num = (
                        float(vix_value) if isinstance(vix_value, str) else vix_value
                    )
                    if vix_num < 15:
                        vix_description = "bajo"
                    elif vix_num < 25:
                        vix_description = "moderado"
                    else:
                        vix_description = "alto"
                elif isinstance(vix_value, str):
                    # Si es texto, usar directamente
                    vix_description = vix_value.lower()
            except (ValueError, TypeError):
                # Si hay error al convertir, usar un valor por defecto
                vix_description = (
                    "" if not isinstance(vix_value, str) else vix_value.lower()
                )

        # Construir descripción del contexto
        if overall == "Alcista":
            context = "un mercado con tendencia alcista"
            if (
                sp500_trend
                and isinstance(sp500_trend, str)
                and "alcista" in sp500_trend.lower()
            ):
                context += ", respaldado por un S&P 500 en ascenso"
            if vix_description and any(
                x in vix_description
                for x in ["bajo", "disminuyendo", "cayendo", "moderado"]
            ):
                context += " y niveles de volatilidad controlados"
            elif vix_description and any(
                x in vix_description for x in ["alto", "elevado", "aumentando"]
            ):
                context += ", aunque con cierta volatilidad presente"
        elif overall == "Bajista":
            context = "un mercado con tendencia bajista"
            if (
                sp500_trend
                and isinstance(sp500_trend, str)
                and "bajista" in sp500_trend.lower()
            ):
                context += ", con un S&P 500 en descenso"
            if vix_description and any(
                x in vix_description for x in ["alto", "elevado", "aumentando"]
            ):
                context += " y alta volatilidad"
        else:  # Neutral
            context = "un mercado con tendencia neutral"
            if vix_description and any(
                x in vix_description for x in ["alto", "elevado", "aumentando"]
            ):
                context += (
                    " pero con volatilidad elevada que podría generar oportunidades"
                )
            elif vix_description and any(
                x in vix_description
                for x in ["bajo", "disminuyendo", "cayendo", "moderado"]
            ):
                context += " y baja volatilidad"

        # Añadir información de volumen si está disponible
        if volume and isinstance(volume, str) and "alto" in volume.lower():
            context += ", con volumen de negociación significativo"
        elif volume and isinstance(volume, str) and "bajo" in volume.lower():
            context += ", aunque con volumen de negociación reducido"

        return context

    def generate_pdf(self, html_content):
        """Genera un PDF a partir del contenido HTML con diseño mejorado"""
        # Verificar si pdfkit está disponible
        if not PDFKIT_AVAILABLE:
            logger.warning("pdfkit no está disponible. No se puede generar PDF.")
            return None

        try:
            # Mejorar el HTML para el PDF con estilos adicionales
            # Añadir CSS para mejorar la apariencia en el PDF
            pdf_styles = """
            <style>
                @page {
                    size: A4;
                    margin: 1cm;
                }
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }
                h1, h2, h3, h4 {
                    color: #2c3e50;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                img {
                    max-width: 100%;
                    height: auto;
                }
                .page-break {
                    page-break-after: always;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #eaeaea;
                }
                .footer {
                    text-align: center;
                    font-size: 10px;
                    color: #6c757d;
                    margin-top: 30px;
                    padding-top: 10px;
                    border-top: 1px solid #eaeaea;
                }
                /* Estilos para señales de trading */
                .signal-call {
                    background-color: #e8f5e9;
                    border-left: 4px solid #28a745;
                }
                .signal-put {
                    background-color: #ffebee;
                    border-left: 4px solid #dc3545;
                }
                .signal-neutral {
                    background-color: #f5f5f5;
                    border-left: 4px solid #6c757d;
                }
                /* Estilos para tablas */
                .data-table th {
                    background-color: #f2f6f9;
                    color: #2c3e50;
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #dee2e6;
                }
                .data-table td {
                    padding: 8px;
                    border-bottom: 1px solid #f2f2f2;
                }
                .data-table tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
            </style>
            """

            # Insertar los estilos en el HTML
            enhanced_html = html_content
            if "</head>" in enhanced_html:
                enhanced_html = enhanced_html.replace("</head>", f"{pdf_styles}</head>")
            else:
                enhanced_html = f"<html><head>{pdf_styles}</head><body>{enhanced_html}</body></html>"

            # Verificar si wkhtmltopdf está instalado
            try:
                import subprocess

                subprocess.run(
                    ["which", "wkhtmltopdf"], check=True, capture_output=True
                )
                logger.info("wkhtmltopdf está instalado en el sistema")
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning(
                    "wkhtmltopdf no está instalado o no se encuentra en el PATH"
                )
                # Intentar usar la ruta configurada en pdfkit
                try:
                    config = pdfkit.configuration()
                    logger.info(f"Usando configuración de pdfkit: {config.wkhtmltopdf}")
                except Exception as config_error:
                    logger.warning(
                        f"Error obteniendo configuración de pdfkit: {str(config_error)}"
                    )

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
                "javascript-delay": "1000",  # Esperar a que se carguen los scripts
                "enable-javascript": "",  # Habilitar JavaScript
                "images": "",  # Incluir imágenes
                "quiet": "",  # Modo silencioso
            }

            # Generar PDF
            try:
                # Intentar con configuración personalizada primero
                try:
                    config = pdfkit.configuration()
                    pdf = pdfkit.from_string(
                        enhanced_html, False, options=options, configuration=config
                    )
                    logger.info(
                        "PDF generado correctamente con configuración personalizada"
                    )
                    return pdf
                except Exception as config_error:
                    logger.warning(
                        f"Error con configuración personalizada: {str(config_error)}"
                    )
                    # Intentar sin configuración personalizada
                    pdf = pdfkit.from_string(enhanced_html, False, options=options)
                    logger.info("PDF generado correctamente con diseño mejorado")
                    return pdf
            except Exception as pdf_error:
                logger.error(f"Error generando PDF completo: {str(pdf_error)}")
                # Intentar con opciones más básicas
                try:
                    logger.info("Intentando generar PDF con opciones básicas...")
                    options = {
                        "page-size": "A4",
                        "encoding": "UTF-8",
                        "no-outline": None,
                    }
                    pdf = pdfkit.from_string(html_content, False, options=options)
                    logger.info("PDF generado correctamente con opciones básicas")
                    return pdf
                except Exception as basic_error:
                    logger.error(
                        f"Error al generar PDF con opciones básicas: {str(basic_error)}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Error general al generar PDF: {str(e)}")
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

        # Generar PDF mejorado si está habilitado
        pdf_content = None
        if include_pdf and PDFKIT_AVAILABLE:
            try:
                # Crear una versión mejorada del HTML para el PDF
                # Añadir información adicional para el PDF que no está en el correo
                pdf_html = html_content

                # Añadir información detallada de cada señal para el PDF
                if signals and len(signals) > 0:
                    pdf_html = pdf_html.replace(
                        "</body>",
                        """
                    <div class="page-break"></div>
                    <h1 style="text-align: center; margin-top: 20px;">Análisis Detallado de Señales</h1>
                    <p style="text-align: center; color: #666;">Este análisis detallado solo está disponible en la versión PDF del boletín</p>
                    """,
                    )

                    for signal in signals:
                        symbol = signal.get("symbol", "")
                        company_name = signal.get("company_name", symbol)
                        analysis = signal.get("analysis", "")
                        technical_analysis = signal.get("technical_analysis", "")
                        expert_analysis = signal.get("expert_analysis", "")

                        pdf_html += f"""
                        <div style="margin: 30px 0; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                            <h2>{symbol} - {company_name}</h2>
                            <h3>Análisis Fundamental</h3>
                            <p>{analysis}</p>

                            <h3>Análisis Técnico</h3>
                            <p>{technical_analysis}</p>

                            <h3>Análisis del Experto</h3>
                            <p>{expert_analysis}</p>
                        </div>
                        """

                    pdf_html += "</body>"

                # Añadir información detallada de noticias para el PDF
                if news_summary and len(news_summary) > 0:
                    pdf_html = pdf_html.replace(
                        "</body>",
                        """
                    <div class="page-break"></div>
                    <h1 style="text-align: center; margin-top: 20px;">Noticias Completas</h1>
                    <p style="text-align: center; color: #666;">Versión completa de las noticias mencionadas en el boletín</p>
                    """,
                    )

                    for news in news_summary:
                        title = news.get("title", "")
                        summary = news.get("summary", "")
                        source = news.get("source", "")
                        url = news.get("url", "")

                        pdf_html += f"""
                        <div style="margin: 20px 0; padding: 15px; border: 1px solid #eee; border-radius: 8px;">
                            <h3>{title}</h3>
                            <p>{summary}</p>
                            <p style="color: #666; font-size: 12px;">Fuente: {source} {f'<a href="{url}">{url}</a>' if url else ''}</p>
                        </div>
                        """

                    pdf_html += "</body>"

                # Generar el PDF con el contenido mejorado
                pdf_content = self.email_manager.generate_pdf(pdf_html)
                if pdf_content:
                    logger.info(
                        "PDF mejorado generado correctamente para adjuntar al correo"
                    )
                else:
                    logger.warning(
                        "No se pudo generar el PDF mejorado para adjuntar al correo"
                    )
                    # Intentar con el HTML original como fallback
                    pdf_content = self.email_manager.generate_pdf(html_content)
                    if pdf_content:
                        logger.info("PDF básico generado como alternativa")
            except Exception as e:
                logger.error(f"Error generando PDF: {str(e)}")
                # Intentar con opciones más básicas
                try:
                    logger.info("Intentando generar PDF con opciones básicas...")
                    pdf_content = self.email_manager.generate_pdf(html_content)
                    if pdf_content:
                        logger.info("PDF básico generado como alternativa")
                except Exception as e2:
                    logger.error(f"Error generando PDF básico: {str(e2)}")

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

# Importar información de compañías
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from company_data import get_company_info

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

    # Enriquecer señales con información completa de compañías
    for signal in signals:
        symbol = signal.get("symbol", "")
        if symbol:
            company_info = get_company_info(symbol)
            signal["company_name"] = company_info.get("name", symbol)
            signal["company_sector"] = company_info.get(
                "sector", signal.get("category", "N/A")
            )
            signal["company_description"] = company_info.get("description", "")

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
                # Determinar color de fondo según dirección
                if signal.get("direction") == "CALL":
                    card_bg = "rgba(40, 167, 69, 0.2)"
                    text_color = "#28a745"
                    border_color = "#28a745"
                    direction_text = "📈 COMPRA"
                elif signal.get("direction") == "PUT":
                    card_bg = "rgba(220, 53, 69, 0.2)"
                    text_color = "#dc3545"
                    border_color = "#dc3545"
                    direction_text = "📉 VENTA"
                else:
                    card_bg = "rgba(108, 117, 125, 0.2)"
                    text_color = "#6c757d"
                    border_color = "#6c757d"
                    direction_text = "↔️ NEUTRAL"

                # Formatear fecha
                created_at = signal.get("created_at")
                if isinstance(created_at, datetime):
                    if created_at > datetime.now():
                        created_at = datetime.now()
                    fecha = created_at.strftime("%d/%m/%Y %H:%M")
                else:
                    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

                # Construir el HTML con diseño mejorado
                html = f"""
                <div style="position: relative; background-color: {card_bg}; padding: 25px;
                        border-radius: 12px; margin-bottom: 25px;
                        border: 1px solid {border_color};
                        box-shadow: 0 8px 15px rgba(0,0,0,0.08);">
                """

                # Badge para Alta Confianza
                if signal.get("is_high_confidence") == 1:
                    html += """
                    <div style="position: absolute; top: 15px; right: 15px;
                                background-color: #28a745; color: white;
                                padding: 5px 12px; border-radius: 20px;
                                font-size: 12px; font-weight: bold;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        ⭐ Alta Confianza
                    </div>
                    """

                # Header con símbolo, nombre completo y dirección
                company_name = signal.get("company_name", signal.get("symbol", ""))
                company_sector = signal.get(
                    "company_sector", signal.get("category", "N/A")
                )
                company_description = signal.get("company_description", "")

                html += f"""
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="width: 50px; height: 50px; background-color: {text_color}; color: white;
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            font-size: 24px; margin-right: 15px; font-weight: bold;">
                        {signal.get('symbol', '')[0]}
                    </div>
                    <div style="flex: 1;">
                        <h3 style="margin: 0; color: {text_color}; font-size: 22px; font-weight: 600;">
                            {signal.get('symbol', '')} - {direction_text}
                        </h3>
                        <div style="font-size: 15px; color: #444; margin-top: 3px; font-weight: 500;">
                            {company_name}
                        </div>
                        <div style="font-size: 13px; color: #666; margin-top: 3px;">
                            {company_sector} • {fecha}
                        </div>
                    </div>
                </div>
                """

                # Descripción de la empresa si está disponible
                if company_description:
                    html += f"""
                    <div style="margin-bottom: 15px; font-size: 14px; color: #555; font-style: italic;
                            background-color: rgba(0,0,0,0.02); padding: 10px; border-radius: 5px;">
                        {company_description}
                    </div>
                    """

                # Setup type como badge
                if signal.get("setup_type"):
                    html += f"""
                    <div style="display: inline-block; margin: 10px 0 15px 0;
                                padding: 6px 12px; background-color: #e9f5ff;
                                border-radius: 20px; font-size: 14px; color: #0275d8;
                                border: 1px solid rgba(2, 117, 216, 0.2);">
                        <i>Setup:</i> {signal.get("setup_type")}
                    </div>
                    """

                # Precios y Objetivos - Diseño mejorado
                html += """
                <div style="background-color: white; border-radius: 8px; margin: 15px 0;
                        padding: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                        border: 1px solid #eee;">
                """

                # Grid de precios
                html += """
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); grid-gap: 15px;">
                """

                # Precio actual
                if signal.get("price"):
                    html += f"""
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Precio Actual</div>
                        <div style="font-size: 18px; font-weight: 600;">${signal.get('price', '0.00')}</div>
                    </div>
                    """

                # Precio de entrada
                if signal.get("entry_price"):
                    html += f"""
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Entrada</div>
                        <div style="font-size: 18px; font-weight: 600; color: #0275d8;">${signal.get('entry_price')}</div>
                    </div>
                    """

                # Stop Loss
                if signal.get("stop_loss"):
                    html += f"""
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Stop Loss</div>
                        <div style="font-size: 18px; font-weight: 600; color: #dc3545;">${signal.get('stop_loss')}</div>
                    </div>
                    """

                # Target Price
                if signal.get("target_price"):
                    html += f"""
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Objetivo</div>
                        <div style="font-size: 18px; font-weight: 600; color: #28a745;">${signal.get('target_price')}</div>
                    </div>
                    """

                html += "</div>"  # Cierre de grid

                # Risk/Reward y Confianza
                html += """
                <div style="display: flex; justify-content: space-between; margin-top: 15px; align-items: center;">
                """

                # Risk/Reward
                if signal.get("risk_reward"):
                    rr_value = signal.get("risk_reward")
                    rr_color = (
                        "#28a745"
                        if rr_value >= 2
                        else ("#fd7e14" if rr_value >= 1 else "#dc3545")
                    )
                    rr_text = (
                        "Excelente"
                        if rr_value >= 3
                        else (
                            "Bueno"
                            if rr_value >= 2
                            else ("Aceptable" if rr_value >= 1 else "Bajo")
                        )
                    )

                    html += f"""
                    <div style="display: flex; align-items: center;">
                        <div style="background-color: {rr_color}; color: white;
                                border-radius: 50%; width: 40px; height: 40px; display: flex;
                                align-items: center; justify-content: center; font-weight: bold;
                                margin-right: 10px;">
                            {rr_value:.1f}
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #666;">Ratio R/R</div>
                            <div style="font-size: 14px; font-weight: 500; color: {rr_color};">{rr_text}</div>
                        </div>
                    </div>
                    """

                # Nivel de confianza
                confidence = signal.get("confidence_level")
                conf_color = (
                    "#28a745"
                    if confidence == "Alta"
                    else ("#fd7e14" if confidence == "Media" else "#6c757d")
                )

                html += f"""
                <div style="background-color: rgba({
                            "40, 167, 69, 0.1" if confidence == "Alta" else
                            ("253, 126, 20, 0.1" if confidence == "Media" else "108, 117, 125, 0.1")
                        });
                        padding: 5px 12px; border-radius: 15px;
                        color: {conf_color}; font-weight: 500;">
                    Confianza: {confidence}
                </div>
                """

                html += "</div>"  # Cierre de Risk/Reward y Confianza
                html += "</div>"  # Cierre de sección de precios

                # Indicadores Técnicos
                html += """
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); grid-gap: 15px; margin: 20px 0;">
                """

                # RSI
                if signal.get("rsi"):
                    rsi_value = signal.get("rsi")
                    rsi_color = (
                        "#dc3545"
                        if rsi_value > 70
                        else ("#28a745" if rsi_value < 30 else "#6c757d")
                    )
                    rsi_text = (
                        "Sobrecompra"
                        if rsi_value > 70
                        else ("Sobreventa" if rsi_value < 30 else "Neutral")
                    )

                    html += f"""
                    <div style="background-color: white; border-radius: 8px; padding: 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">RSI</div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-size: 16px; font-weight: 600;">{rsi_value:.2f}</div>
                            <div style="font-size: 13px; color: {rsi_color};">{rsi_text}</div>
                        </div>
                    </div>
                    """

                # Soporte
                if signal.get("support_level"):
                    html += f"""
                    <div style="background-color: white; border-radius: 8px; padding: 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee;
                            border-left: 3px solid #28a745;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Soporte</div>
                        <div style="font-size: 16px; font-weight: 600;">${signal.get('support_level')}</div>
                    </div>
                    """

                # Resistencia
                if signal.get("resistance_level"):
                    html += f"""
                    <div style="background-color: white; border-radius: 8px; padding: 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee;
                            border-left: 3px solid #dc3545;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Resistencia</div>
                        <div style="font-size: 16px; font-weight: 600;">${signal.get('resistance_level')}</div>
                    </div>
                    """

                # Volatilidad
                if signal.get("volatility"):
                    html += f"""
                    <div style="background-color: white; border-radius: 8px; padding: 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Volatilidad</div>
                        <div style="font-size: 16px; font-weight: 600;">{signal.get('volatility')}%</div>
                    </div>
                    """

                html += "</div>"  # Cierre de grid de indicadores

                # Análisis de tendencia multi-timeframe
                trends_available = (
                    signal.get("trend")
                    or signal.get("daily_trend")
                    or signal.get("weekly_trend")
                    or signal.get("monthly_trend")
                )

                if trends_available:
                    html += """
                    <div style="background-color: white; border-radius: 8px; margin: 15px 0;
                            padding: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                            border: 1px solid #eee;">
                        <div style="font-size: 14px; font-weight: 500; color: #444; margin-bottom: 12px;">
                            Análisis de Tendencia
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); grid-gap: 10px;">
                    """

                    # Tendencia principal
                    if signal.get("trend"):
                        trend = signal.get("trend")
                        trend_strength = signal.get("trend_strength", "")
                        trend_color = (
                            "#28a745"
                            if "ALCISTA" in trend.upper()
                            else (
                                "#dc3545" if "BAJISTA" in trend.upper() else "#6c757d"
                            )
                        )
                        trend_bg = (
                            "rgba(40, 167, 69, 0.1)"
                            if "ALCISTA" in trend.upper()
                            else (
                                "rgba(220, 53, 69, 0.1)"
                                if "BAJISTA" in trend.upper()
                                else "rgba(108, 117, 125, 0.1)"
                            )
                        )

                        html += f"""
                        <div>
                            <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Tendencia Global</div>
                            <div style="display: inline-block; padding: 5px 10px;
                                    background-color: {trend_bg}; border-radius: 5px;
                                    color: {trend_color}; font-weight: 500;">
                                {trend}
                                {f' <small>({trend_strength})</small>' if trend_strength else ''}
                            </div>
                        </div>
                        """

                    # Tendencia diaria
                    if signal.get("daily_trend"):
                        daily_trend = signal.get("daily_trend")
                        dt_color = (
                            "#28a745"
                            if "ALCISTA" in daily_trend.upper()
                            else (
                                "#dc3545"
                                if "BAJISTA" in daily_trend.upper()
                                else "#6c757d"
                            )
                        )
                        dt_bg = (
                            "rgba(40, 167, 69, 0.1)"
                            if "ALCISTA" in daily_trend.upper()
                            else (
                                "rgba(220, 53, 69, 0.1)"
                                if "BAJISTA" in daily_trend.upper()
                                else "rgba(108, 117, 125, 0.1)"
                            )
                        )

                        html += f"""
                        <div>
                            <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Diaria</div>
                            <div style="display: inline-block; padding: 5px 10px;
                                    background-color: {dt_bg}; border-radius: 5px;
                                    color: {dt_color}; font-weight: 500;">
                                {daily_trend}
                            </div>
                        </div>
                        """

                    # Tendencia semanal
                    if signal.get("weekly_trend"):
                        weekly_trend = signal.get("weekly_trend")
                        wt_color = (
                            "#28a745"
                            if "ALCISTA" in weekly_trend.upper()
                            else (
                                "#dc3545"
                                if "BAJISTA" in weekly_trend.upper()
                                else "#6c757d"
                            )
                        )
                        wt_bg = (
                            "rgba(40, 167, 69, 0.1)"
                            if "ALCISTA" in weekly_trend.upper()
                            else (
                                "rgba(220, 53, 69, 0.1)"
                                if "BAJISTA" in weekly_trend.upper()
                                else "rgba(108, 117, 125, 0.1)"
                            )
                        )

                        html += f"""
                        <div>
                            <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Semanal</div>
                            <div style="display: inline-block; padding: 5px 10px;
                                    background-color: {wt_bg}; border-radius: 5px;
                                    color: {wt_color}; font-weight: 500;">
                                {weekly_trend}
                            </div>
                        </div>
                        """

                    # Tendencia mensual
                    if signal.get("monthly_trend"):
                        monthly_trend = signal.get("monthly_trend")
                        mt_color = (
                            "#28a745"
                            if "ALCISTA" in monthly_trend.upper()
                            else (
                                "#dc3545"
                                if "BAJISTA" in monthly_trend.upper()
                                else "#6c757d"
                            )
                        )
                        mt_bg = (
                            "rgba(40, 167, 69, 0.1)"
                            if "ALCISTA" in monthly_trend.upper()
                            else (
                                "rgba(220, 53, 69, 0.1)"
                                if "BAJISTA" in monthly_trend.upper()
                                else "rgba(108, 117, 125, 0.1)"
                            )
                        )

                        html += f"""
                        <div>
                            <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Mensual</div>
                            <div style="display: inline-block; padding: 5px 10px;
                                    background-color: {mt_bg}; border-radius: 5px;
                                    color: {mt_color}; font-weight: 500;">
                                {monthly_trend}
                            </div>
                        </div>
                        """

                    html += """
                        </div>
                    </div>
                    """

                # Indicadores específicos
                bullish_indicators = signal.get("bullish_indicators")
                bearish_indicators = signal.get("bearish_indicators")

                if bullish_indicators or bearish_indicators:
                    html += """
                    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0;">
                    """

                    # Indicadores alcistas
                    if bullish_indicators:
                        bull_items = (
                            bullish_indicators.split(",")
                            if isinstance(bullish_indicators, str)
                            else []
                        )
                        if bull_items:
                            for item in bull_items:
                                item = item.strip()
                                if item:
                                    html += f"""
                                    <div style="background-color: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.2);
                                            color: #28a745; padding: 5px 10px; border-radius: 15px; font-size: 12px;">
                                        🔼 {item}
                                    </div>
                                    """

                    # Indicadores bajistas
                    if bearish_indicators:
                        bear_items = (
                            bearish_indicators.split(",")
                            if isinstance(bearish_indicators, str)
                            else []
                        )
                        if bear_items:
                            for item in bear_items:
                                item = item.strip()
                                if item:
                                    html += f"""
                                    <div style="background-color: rgba(220, 53, 69, 0.1); border: 1px solid rgba(220, 53, 69, 0.2);
                                            color: #dc3545; padding: 5px 10px; border-radius: 15px; font-size: 12px;">
                                        🔽 {item}
                                    </div>
                                    """

                    html += "</div>"

                # Trading Specialist (si existe)
                trading_specialist_signal = signal.get("trading_specialist_signal")
                trading_specialist_confidence = signal.get(
                    "trading_specialist_confidence"
                )

                if trading_specialist_signal:
                    ts_color = (
                        "#28a745"
                        if "COMPRA" in trading_specialist_signal.upper()
                        else (
                            "#dc3545"
                            if "VENTA" in trading_specialist_signal.upper()
                            else "#6c757d"
                        )
                    )

                    html += f"""
                    <div style="background-color: rgba(25, 118, 210, 0.05); border-radius: 8px;
                            padding: 12px 15px; margin: 15px 0; border-left: 3px solid #1976d2;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-size: 14px; font-weight: 500; color: #1976d2;">
                                👨‍💼 Trading Specialist
                            </div>
                            <div style="color: {ts_color}; font-weight: 500;">
                                {trading_specialist_signal}
                                {f' • {trading_specialist_confidence}' if trading_specialist_confidence else ''}
                            </div>
                        </div>
                    </div>
                    """

                # Recomendación final si existe
                recommendation = signal.get("recommendation")
                if recommendation:
                    rec_color = (
                        "#28a745"
                        if "COMPRAR" in recommendation.upper()
                        else (
                            "#dc3545"
                            if "VENDER" in recommendation.upper()
                            else "#6c757d"
                        )
                    )

                    html += f"""
                    <div style="text-align: center; margin: 20px 0 10px 0;">
                        <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Recomendación Final</div>
                        <div style="display: inline-block; padding: 8px 20px;
                                background-color: {
                                    "rgba(40, 167, 69, 0.1)" if "COMPRAR" in recommendation.upper() else
                                    ("rgba(220, 53, 69, 0.1)" if "VENDER" in recommendation.upper() else "rgba(108, 117, 125, 0.1)")
                                };
                                border: 2px solid {rec_color};
                                border-radius: 20px; font-size: 16px; font-weight: 600; color: {rec_color};">
                            {recommendation}
                        </div>
                    </div>
                    """

                # Sección de análisis detallado
                html += f"""
                <details style="margin-top: 20px; cursor: pointer;">
                    <summary style="color: {text_color}; font-weight: 500; padding: 10px;
                                background-color: rgba(0,0,0,0.03); border-radius: 5px;">
                        Ver análisis detallado
                    </summary>
                    <div style="background-color: white; padding: 15px;
                            border-radius: 8px; margin-top: 10px; border: 1px solid #eee;">
                """

                # Análisis principal
                if signal.get("analysis"):
                    html += f"""
                    <div style="margin-bottom: 15px;">
                        <p style="margin: 0;">{signal.get('analysis')}</p>
                    </div>
                    """

                # Análisis técnico detallado
                if signal.get("technical_analysis"):
                    html += f"""
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                        <div style="font-size: 14px; font-weight: 500; color: #444; margin-bottom: 10px;">
                            Análisis Técnico
                        </div>
                        <p>{signal.get("technical_analysis")}</p>
                    </div>
                    """

                # Análisis multi-timeframe
                if signal.get("mtf_analysis"):
                    html += f"""
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                        <div style="font-size: 14px; font-weight: 500; color: #444; margin-bottom: 10px;">
                            Análisis Multi-Timeframe
                        </div>
                        <p>{signal.get("mtf_analysis")}</p>
                    </div>
                    """

                # Análisis de experto
                if signal.get("expert_analysis"):
                    html += f"""
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                        <div style="font-size: 14px; font-weight: 500; color: #444; margin-bottom: 10px;">
                            Análisis del Experto
                        </div>
                        <p>{signal.get("expert_analysis")}</p>
                    </div>
                    """

                # Análisis de opciones
                if signal.get("options_analysis"):
                    html += f"""
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                        <div style="font-size: 14px; font-weight: 500; color: #444; margin-bottom: 10px;">
                            Análisis de Opciones
                        </div>
                        <p>{signal.get("options_analysis")}</p>
                    </div>
                    """

                # Noticias relevantes
                latest_news = signal.get("latest_news")
                news_source = signal.get("news_source")
                additional_news = signal.get("additional_news")

                if latest_news:
                    html += f"""
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                        <div style="font-size: 14px; font-weight: 500; color: #444; margin-bottom: 10px;">
                            Noticias Relevantes
                        </div>
                    """

                    # Preparar enlace si hay fuente de noticias
                    news_link = ""
                    if news_source and news_source.startswith("http"):
                        news_link = f"<a href='{news_source}' target='_blank' style='color: #0275d8; text-decoration: none;'>Ver fuente <span style='font-size: 12px;'>&#128279;</span></a>"

                    html += f"""
                        <div style="background-color: #f8f9fa; padding: 10px 15px; border-radius: 5px; margin-bottom: 10px;">
                            <p style="margin: 0 0 8px 0; font-weight: 500;">{latest_news}</p>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <small style="color: #666;">{signal.get('symbol', '')}</small>
                                {f'<small style="color: #0275d8;">{news_link}</small>' if news_link else ''}
                            </div>
                        </div>
                    """

                    if additional_news:
                        news_items = (
                            additional_news.split("||")
                            if "||" in additional_news
                            else [additional_news]
                        )
                        for item in news_items:
                            if item.strip():
                                html += f"""
                                <div style="background-color: #f8f9fa; padding: 10px 15px; border-radius: 5px; margin-top: 8px;">
                                    <p style="margin: 0;">{item.strip()}</p>
                                </div>
                                """

                    html += "</div>"

                html += """
                    </div>
                </details>
                """

                # Cerrar div principal
                html += "</div>"

                # Renderizar con components.v1.html
                st.components.v1.html(html, height=None, scrolling=False)
    else:
        # Mostrar mensaje si no hay señales
        st.warning("No se encontraron señales activas con los filtros seleccionados.")

        # Sugerencias para el usuario
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
            # Preparar URL para enlace si existe
            url = item.get("url", "")
            title_with_link = item.get("title", "")
            if url and len(url) > 5:  # Verificar que la URL sea válida
                title_with_link = f"<a href='{url}' target='_blank' style='text-decoration: none; color: #0275d8;'>{item.get('title', '')} <span style='font-size: 14px;'>&#128279;</span></a>"

            # Preparar símbolo y nombre de empresa si existe
            symbol = item.get("symbol", "")
            company_name = ""
            if symbol:
                # Obtener información completa de la empresa
                company_info = get_company_info(symbol)
                company_name = company_info.get("name", "")

                # Crear badge con símbolo y nombre
                badge_text = f"{symbol}"
                if company_name:
                    badge_text = f"{symbol} - {company_name}"

                symbol_badge = f"<span style='background-color: rgba(2, 117, 216, 0.1); color: #0275d8; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-right: 10px;'>{badge_text}</span>"
            else:
                symbol_badge = ""

            st.markdown(
                f"""
            <div style="background-color: rgba(255,255,255,0.05); padding: 20px;
                       border-radius: 10px; margin-bottom: 15px;
                       border: 1px solid rgba(0,0,0,0.05);
                       box-shadow: 0 4px 6px rgba(0,0,0,0.03);">
                <h4 style="margin-top: 0; font-weight: 600; font-size: 18px;">
                    {title_with_link}
                </h4>
                <p>{item.get('summary', '')}</p>
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        {symbol_badge}
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
                styled_df = styled_df.map(
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
            # Corregido: Styler object no tiene método astype
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
                styled_df = styled_df.map(
                    lambda x: (
                        "color: #28a745; font-weight: bold"
                        if "Exitoso" in str(x)
                        else "color: #dc3545; font-weight: bold"
                    ),
                    subset=["Estado"],
                )

            # Mostrar tabla
            # Corregido: Styler object no tiene método astype
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
