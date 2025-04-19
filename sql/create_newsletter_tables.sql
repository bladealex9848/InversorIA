-- Crear tablas para el sistema de suscriptores y envío de boletines

-- Tabla para suscriptores del boletín
CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(100),
    active TINYINT(1) DEFAULT 1,
    subscription_date DATETIME,
    last_sent_date DATETIME,
    send_count INT DEFAULT 0,
    UNIQUE INDEX idx_email (email),
    INDEX idx_active (active),
    INDEX idx_subscription_date (subscription_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para registros de envíos a suscriptores
CREATE TABLE IF NOT EXISTS newsletter_send_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subscriber_id INT NOT NULL,
    email_log_id INT,
    send_date DATETIME,
    status VARCHAR(20),
    error_message TEXT,
    pdf_attached TINYINT(1) DEFAULT 0,
    signals_included TEXT,
    INDEX idx_subscriber_id (subscriber_id),
    INDEX idx_email_log_id (email_log_id),
    INDEX idx_send_date (send_date),
    INDEX idx_status (status),
    FOREIGN KEY (subscriber_id) REFERENCES newsletter_subscribers(id) ON DELETE CASCADE,
    FOREIGN KEY (email_log_id) REFERENCES email_logs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
