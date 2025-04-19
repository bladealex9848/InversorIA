-- Crear tabla de suscriptores para el boletín
CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(150),
    active BOOLEAN DEFAULT TRUE,
    subscription_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_sent_date DATETIME,
    send_count INT DEFAULT 0,
    preferences JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear tabla para registrar los envíos de boletines a suscriptores
CREATE TABLE IF NOT EXISTS newsletter_send_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subscriber_id INT NOT NULL,
    email_log_id INT,
    send_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    pdf_attached BOOLEAN DEFAULT FALSE,
    signals_included TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscriber_id) REFERENCES newsletter_subscribers(id) ON DELETE CASCADE,
    FOREIGN KEY (email_log_id) REFERENCES email_logs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar algunos suscriptores de ejemplo (opcional)
INSERT IGNORE INTO newsletter_subscribers (email, name, last_name, company, active)
VALUES 
('ejemplo@correo.com', 'Usuario', 'Ejemplo', 'Empresa Ejemplo', TRUE),
('inversor@ejemplo.com', 'Inversor', 'Prueba', 'Inversiones Test', TRUE);
