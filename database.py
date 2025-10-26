"""
Módulo de gerenciamento do banco de dados PostgreSQL
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class Database:
    """Gerenciador de conexão e operações com PostgreSQL"""
    
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'tcrb_monitoring'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
        self.conn = None
    
    def connect(self):
        """Estabelece conexão com o banco de dados"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            print("✓ Conectado ao banco de dados PostgreSQL")
            return True
        except psycopg2.Error as e:
            print(f"✗ Erro ao conectar ao banco de dados: {e}")
            return False
    
    def disconnect(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            self.conn.close()
            print("✓ Conexão com banco de dados fechada")
    
    def create_tables(self):
        """Cria as tabelas necessárias se não existirem"""
        create_table_sql = """
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
        
        CREATE INDEX IF NOT EXISTS idx_jd ON observations(jd);
        CREATE INDEX IF NOT EXISTS idx_calendar_date ON observations(calendar_date);
        CREATE INDEX IF NOT EXISTS idx_created_at ON observations(created_at);
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(create_table_sql)
                self.conn.commit()
            print("✓ Tabelas criadas/verificadas com sucesso")
            return True
        except psycopg2.Error as e:
            print(f"✗ Erro ao criar tabelas: {e}")
            self.conn.rollback()
            return False
    
    def insert_observation(self, data: Dict) -> Optional[int]:
        """
        Insere uma nova observação no banco de dados
        
        Args:
            data: Dicionário com os dados da observação
            
        Returns:
            ID da observação inserida ou None se já existir/erro
        """
        insert_sql = """
        INSERT INTO observations (star, jd, calendar_date, magnitude, error, filter, observer, scraped_at)
        VALUES (%(star)s, %(jd)s, %(calendar_date)s, %(magnitude)s, %(error)s, %(filter)s, %(observer)s, %(scraped_at)s)
        ON CONFLICT (jd) DO NOTHING
        RETURNING id;
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_sql, data)
                result = cur.fetchone()
                self.conn.commit()
                
                if result:
                    obs_id = result[0]
                    print(f"✓ Nova observação inserida (ID: {obs_id})")
                    return obs_id
                else:
                    print("ℹ️  Observação já existe no banco de dados")
                    return None
                    
        except psycopg2.Error as e:
            print(f"✗ Erro ao inserir observação: {e}")
            self.conn.rollback()
            return None
    
    def observation_exists(self, jd: str) -> bool:
        """
        Verifica se uma observação já existe no banco
        
        Args:
            jd: Julian Date da observação
            
        Returns:
            True se existe, False caso contrário
        """
        query = "SELECT COUNT(*) FROM observations WHERE jd = %s"
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (jd,))
                count = cur.fetchone()[0]
                return count > 0
        except psycopg2.Error as e:
            print(f"✗ Erro ao verificar existência: {e}")
            return False
    
    def get_latest_observations(self, limit: int = 10) -> List[Dict]:
        """
        Retorna as últimas N observações
        
        Args:
            limit: Número de observações a retornar
            
        Returns:
            Lista de dicionários com as observações
        """
        query = """
        SELECT * FROM observations
        ORDER BY jd DESC
        LIMIT %s
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (limit,))
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"✗ Erro ao buscar observações: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """
        Retorna estatísticas do banco de dados
        
        Returns:
            Dicionário com estatísticas
        """
        query = """
        SELECT 
            COUNT(*) as total,
            MIN(calendar_date) as oldest_date,
            MAX(calendar_date) as latest_date,
            (SELECT magnitude FROM observations ORDER BY jd DESC LIMIT 1) as latest_magnitude
        FROM observations
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return dict(cur.fetchone())
        except psycopg2.Error as e:
            print(f"✗ Erro ao buscar estatísticas: {e}")
            return {}


def main():
    """Função principal para teste"""
    db = Database()
    
    if not db.connect():
        return 1
    
    if not db.create_tables():
        db.disconnect()
        return 1
    
    # Mostra estatísticas
    stats = db.get_stats()
    print("\n=== Estatísticas do Banco ===")
    for key, value in stats.items():
        print(f"{key:20}: {value}")
    
    # Mostra últimas observações
    observations = db.get_latest_observations(5)
    print(f"\n=== Últimas {len(observations)} Observações ===")
    for obs in observations:
        print(f"ID {obs['id']}: {obs['calendar_date']} - Magnitude: {obs['magnitude']}")
    
    db.disconnect()
    return 0


if __name__ == "__main__":
    exit(main())