import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime
from astropy.time import Time
import os  # Para verificar se o arquivo CSV existe

# URL do site com os dados de observação
url = "https://apps.aavso.org/webobs/results/?star=000-BBW-825&num_results=200"

# Função para raspar os dados da tabela
def scrape_data():
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Encontrar a tabela de observações
    table = soup.find('table', class_='observations')

    # Pegar todas as linhas dentro do corpo da tabela (tbody)
    rows = table.find('tbody').find_all('tr')

    # Ignorar a primeira linha (cabeçalho) e pegar a primeira linha de dados
    first_row = rows[0]  # Isso pegará a primeira linha de dados

    # Extrair as células da primeira linha de dados
    cells = first_row.find_all('td')

    # Pegar os dados: JD (Julian Date), Magnitude, Error, Filter, Observer
    julian_date = cells[2].text.strip()
    magnitude = cells[4].text.strip()
    error = cells[5].text.strip()
    filter_used = cells[6].text.strip()
    observer = cells[7].text.strip()

    # Converter Julian Date para data de calendário
    jd_value = float(julian_date)
    t = Time(jd_value, format='jd')

    # Converter a data e hora para o formato desejado (dd/mm/yyyy hh:MM)
    date_str = t.datetime.strftime("%d/%m/%Y")
    hour_str = t.datetime.strftime("%H:%M")

    # Retornar os dados raspados e formatados
    return [date_str, hour_str, magnitude, error, filter_used, observer]

# Função para adicionar os dados no CSV
def append_to_csv(data):
    csv_file = "observations.csv"
    file_exists = os.path.isfile(csv_file)

    # Se o arquivo não existe, criar com o cabeçalho
    if not file_exists:
        with open(csv_file, mode='w', newline='', encoding='utf-8-sig') as file:  # Adiciona a codificação correta
            writer = csv.writer(file)
            writer.writerow(["date", "hour", "magnitude", "error", "filter", "observer"])  # Cabeçalho
            print("Cabeçalho adicionado ao CSV.")

    # Verificar se o dado já está no CSV para evitar duplicatas
    with open(csv_file, mode='r', encoding='utf-8-sig') as file:  # Adiciona a codificação correta
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == data[0] and row[1] == data[1]:  # Comparando data e hora
                print("Dado já existe no CSV.")
                return

    # Se o dado for novo, adicionar ao CSV com a quebra de linha correta
    with open(csv_file, mode='a', newline='', encoding='utf-8-sig') as file:  # Adiciona a codificação correta
        writer = csv.writer(file)
        writer.writerow(data)  # Escrever os dados como uma nova linha no CSV
        print("Dado adicionado ao CSV:", data)

def run():
    scraped_data = scrape_data()
    append_to_csv(scraped_data)  # Chamar a função corretamente

if __name__ == "__main__":
    run()
