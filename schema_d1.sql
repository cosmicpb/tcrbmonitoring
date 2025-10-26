-- Schema atualizado para D1 - T CrB Monitoring
-- Alinhado com o scraper histórico

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star TEXT NOT NULL,
    date_original TEXT NOT NULL,
    date_br TEXT NOT NULL,
    magnitude REAL NOT NULL,
    error REAL,
    band TEXT,
    observer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(star, date_original, magnitude, band, observer)
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_star_date ON observations(star, date_br);
CREATE INDEX IF NOT EXISTS idx_magnitude ON observations(magnitude);
CREATE INDEX IF NOT EXISTS idx_band ON observations(band);
CREATE INDEX IF NOT EXISTS idx_date_original ON observations(date_original);