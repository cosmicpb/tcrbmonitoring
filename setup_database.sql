-- Script de configuração do banco de dados T CrB Monitoring
-- Execute este script como usuário postgres

-- Criar banco de dados
CREATE DATABASE tcrb_monitoring;

-- Conectar ao banco
\c tcrb_monitoring

-- Criar usuário (altere a senha!)
CREATE USER tcrb_user WITH PASSWORD 'tcrb_password_123';

-- Conceder privilégios
GRANT ALL PRIVILEGES ON DATABASE tcrb_monitoring TO tcrb_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO tcrb_user;

-- Criar tabela
CREATE TABLE IF NOT EXISTS observations (
    id SERIAL PRIMARY KEY,
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

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_jd ON observations(jd);
CREATE INDEX IF NOT EXISTS idx_calendar_date ON observations(calendar_date);
CREATE INDEX IF NOT EXISTS idx_created_at ON observations(created_at);
CREATE INDEX IF NOT EXISTS idx_magnitude ON observations(magnitude);

-- Conceder permissões na tabela
GRANT ALL PRIVILEGES ON TABLE observations TO tcrb_user;
GRANT USAGE, SELECT ON SEQUENCE observations_id_seq TO tcrb_user;

-- Mostrar informações
\dt
\du