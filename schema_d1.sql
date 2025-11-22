-- Schema correto para D1 - T CrB Monitoring
-- Alinhado com o schema real do D1 em produção

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    jd TEXT NOT NULL,
    calendar_date TEXT NOT NULL,
    magnitude TEXT NOT NULL,
    error TEXT,
    filter TEXT,
    observer TEXT,
    scraped_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(star, jd, magnitude, filter, observer)
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_jd ON observations(jd);
CREATE INDEX IF NOT EXISTS idx_calendar_date ON observations(calendar_date);
CREATE INDEX IF NOT EXISTS idx_star ON observations(star);
CREATE INDEX IF NOT EXISTS idx_magnitude ON observations(magnitude);