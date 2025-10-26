-- Schema para banco de dados T CrB Monitoring
-- PostgreSQL / Cloudflare D1

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star VARCHAR(50) NOT NULL,
    jd VARCHAR(50) NOT NULL UNIQUE,
    calendar_date VARCHAR(100) NOT NULL,
    magnitude VARCHAR(50) NOT NULL,
    error VARCHAR(50),
    filter VARCHAR(50) NOT NULL,
    observer VARCHAR(50) NOT NULL,
    scraped_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_jd ON observations(jd);
CREATE INDEX IF NOT EXISTS idx_calendar_date ON observations(calendar_date);
CREATE INDEX IF NOT EXISTS idx_created_at ON observations(created_at);
CREATE INDEX IF NOT EXISTS idx_magnitude ON observations(magnitude);