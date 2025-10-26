"""
Scheduler para execução periódica do monitoramento
Executa o monitoramento a cada hora
"""

import schedule
import time
import sys
from datetime import datetime
from monitor import monitor


def job():
    """Job que será executado periodicamente"""
    print(f"\n{'='*60}")
    print(f"Execução iniciada em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        monitor()
    except Exception as e:
        print(f"✗ Erro durante execução: {e}")
    
    print(f"\nPróxima execução em 1 hora...")


def main():
    """Função principal do scheduler"""
    print("🚀 T CrB Monitoring Scheduler")
    print("⏰ Intervalo: A cada hora")
    print(f"📅 Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nPressione Ctrl+C para parar\n")
    
    # Agenda execução a cada hora
    schedule.every().hour.do(job)
    
    # Executa imediatamente na primeira vez
    print("Executando primeira coleta...")
    job()
    
    # Loop principal
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler encerrado pelo usuário")
        return 0
    except Exception as e:
        print(f"\n✗ Erro no scheduler: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())