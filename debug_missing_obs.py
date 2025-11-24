"""
Debug: Por que algumas observações não são coletadas?
Analisa o HTML das observações problemáticas
"""

# HTML das 3 observações
obs_6 = """<tr class="obs tr-even" id="ob-6">
  
  
  <td class="empty" colspan="3"></td>
  

  <td>T CrB</td>
  <td>2461002.24360764</td>
  <td>2025 Nov. 22.74361</td>
  
  <td><a target="_blank" href="https://www.aavso.org/LCGv2/index.htm?DateFormat=Julian&amp;RequestedBands=&amp;view=api.delim&amp;ident=000-BBW-825&amp;fromjd=2460902.24360764&amp;tojd=2461102.24360764&amp;delimiter=@@@">11.0255</a></td>
  
  <td>0.0782</td>
  <td>TB</td>
  <td>MCHB</td>
  <td><a href="#" class="obs-link" id="ob-6">Details...</a>
  </td>
</tr>"""

obs_7 = """<tr class="obs tr-odd" id="ob-7">
  
  
  <td class="empty" colspan="3"></td>
  

  <td>T CrB</td>
  <td>2461002.24360764</td>
  <td>2025 Nov. 22.74361</td>
  
  <td><a target="_blank" href="https://www.aavso.org/LCGv2/index.htm?DateFormat=Julian&amp;RequestedBands=&amp;view=api.delim&amp;ident=000-BBW-825&amp;fromjd=2460902.24360764&amp;tojd=2461102.24360764&amp;delimiter=@@@">9.9277</a></td>
  
  <td>0.0509</td>
  <td>TG</td>
  <td>MCHB</td>
  <td><a href="#" class="obs-link" id="ob-7">Details...</a>
  </td>
</tr>"""

obs_8 = """<tr class="obs tr-even" id="ob-8">
  
  
  <td class="empty" colspan="3"></td>
  

  <td>T CrB</td>
  <td>2461002.24360764</td>
  <td>2025 Nov. 22.74361</td>
  
  <td><a target="_blank" href="https://www.aavso.org/LCGv2/index.htm?DateFormat=Julian&amp;RequestedBands=&amp;view=api.delim&amp;ident=000-BBW-825&amp;fromjd=2460902.24360764&amp;tojd=2461102.24360764&amp;delimiter=@@@">9.225</a></td>
  
  <td>0.0416</td>
  <td>TR</td>
  <td>MCHB</td>
  <td><a href="#" class="obs-link" id="ob-8">Details...</a>
  </td>
</tr>"""


def parse_row(row_html, obs_id):
    """Simula o parser do scraper"""
    print(f"\n{'='*60}")
    print(f"Analisando {obs_id}")
    print(f"{'='*60}")
    
    # Extrai células (mesmo algoritmo do scraper)
    cells = []
    cell_pos = 0
    while True:
        td_start = row_html.find('<td', cell_pos)
        if td_start == -1:
            break
        td_end = row_html.find('</td>', td_start)
        cell_content = row_html[td_start:td_end + 5]
        
        text_start = cell_content.find('>')
        text = cell_content[text_start + 1:].replace('</td>', '')
        
        # Remove tags HTML
        while '<' in text:
            tag_start = text.find('<')
            tag_end = text.find('>', tag_start)
            if tag_end == -1:
                break
            text = text[:tag_start] + text[tag_end + 1:]
        
        cells.append(text.strip())
        cell_pos = td_end + 5
    
    print(f"\nTotal de células: {len(cells)}")
    for i, cell in enumerate(cells):
        print(f"  Célula {i}: '{cell}' (vazia: {not cell})")
    
    # Remove células vazias
    non_empty_cells = [cell for cell in cells if cell]
    print(f"\nCélulas não-vazias: {len(non_empty_cells)}")
    for i, cell in enumerate(non_empty_cells):
        print(f"  {i}: '{cell}'")
    
    # Verifica se passa no filtro
    if len(non_empty_cells) < 7:
        print(f"\n❌ REJEITADO: Menos de 7 células não-vazias ({len(non_empty_cells)})")
        return None
    else:
        print(f"\n✅ ACEITO: {len(non_empty_cells)} células não-vazias")
        
        # Monta dados
        observer = non_empty_cells[6]
        if 'Details' in observer:
            observer = observer.split('Details')[0].strip()
        
        data = {
            'star': non_empty_cells[0],
            'jd': non_empty_cells[1],
            'calendar_date': non_empty_cells[2],
            'magnitude': non_empty_cells[3],
            'error': non_empty_cells[4],
            'filter': non_empty_cells[5],
            'observer': observer
        }
        
        print(f"\nDados extraídos:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        
        return data


# Testa as 3 observações
parse_row(obs_6, "ob-6 (COLETADO)")
parse_row(obs_7, "ob-7 (NÃO COLETADO)")
parse_row(obs_8, "ob-8 (NÃO COLETADO)")

print(f"\n{'='*60}")
print("ANÁLISE COMPLETA")
print(f"{'='*60}")