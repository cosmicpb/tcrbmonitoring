#!/usr/bin/env python3
"""
Script wrapper para executar o scraper robusto sem interação
"""

import sys
import os

# Adiciona resposta automática para inputs
class AutoInput:
    def __init__(self, responses):
        self.responses = responses
        self.index = 0
    
    def __call__(self, prompt=''):
        if self.index < len(self.responses):
            response = self.responses[self.index]
            self.index += 1
            print(f"{prompt}{response}")
            return response
        return 'n'

# Substitui input por respostas automáticas
# Respostas: [retomar checkpoint?, iniciar coleta?]
sys.modules['builtins'].input = AutoInput(['s', 's'])

# Importa e executa o scraper
from robust_scraper import main

if __name__ == "__main__":
    main()