"""
Script principal de monitoramento da estrela T CrB
Integra scraping e armazenamento no banco de dados
"""

import sys
from scraper import TCrbScraper
from database import Database


def monitor():
    """
    Executa uma iteração do monitoramento:
    1. Faz scraping dos dados mais recentes
    2. Salva no banco de dados se for nova observação
    """
    print("=" * 60)
    print("T CrB Monitoring System")
    print("=" * 60)
    
    # Inicializa scraper
    scraper = TCrbScraper()
    
    # Busca dados mais recentes
    data = scraper.fetch_latest_observation()
    if not data:
        print("✗ Falha ao coletar dados")
        return False
    
    # Conecta ao banco de dados
    db = Database()
    if not db.connect():
        print("✗ Falha ao conectar ao banco de dados")
        return False
    
    try:
        # Cria tabelas se necessário
        db.create_tables()
        
        # Verifica se já existe
        if db.observation_exists(data['jd']):
            print(f"ℹ️  Observação JD {data['jd']} já existe no banco")
            
            # Mostra estatísticas
            stats = db.get_stats()
            print(f"\n📊 Total de observações: {stats.get('total', 0)}")
            print(f"📊 Última magnitude: {stats.get('latest_magnitude', 'N/A')}")
            return True
        
        # Insere nova observação
        obs_id = db.insert_observation(data)
        if obs_id:
            print(f"✓ Nova observação salva com sucesso!")
            print(f"   ID: {obs_id}")
            print(f"   JD: {data['jd']}")
            print(f"   Data: {data['calendar_date']}")
            print(f"   Magnitude: {data['magnitude']}")
            
            # Mostra estatísticas atualizadas
            stats = db.get_stats()
            print(f"\n📊 Total de observações: {stats.get('total', 0)}")
            return True
        else:
            print("✗ Falha ao salvar observação")
            return False
            
    finally:
        db.disconnect()


def main():
    """Função principal"""
    try:
        success = monitor()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        return 130
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())