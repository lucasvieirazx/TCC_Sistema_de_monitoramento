# main.py
import requests
import csv
import os
from datetime import datetime
from avisos import queda
from config import API_KEY
from enviar_email import enviar_relatorio
from bs4 import BeautifulSoup
import re
from historico import salvar_historico
from config import EMAIL, SENHA

# Lista de produtos para monitorar
produtos = [
    {"nome": "Notebook Lenovo Ideapad 3", "url": "https://www.amazon.com.br/s?k=notebook+lenovo+ideapad+3"},
    {"nome": "Notebook Acer Aspire 5", "url": "https://www.amazon.com.br/s?k=notebook+acer+aspire+5"},
    {"nome": "Placa de Vídeo RTX 3060", "url": "https://www.amazon.com.br/s?k=rtx+3060"},
]

def normalizar_preco(valor):
    """Converte string de preço para float, ignorando intervalos ou texto extra."""
    valor = valor.lower().replace("r$", "").replace(" ", "")
    valor = valor.replace(",", ".")
    match = re.search(r"\d+(\.\d+)*", valor)
    if match:
        numero = match.group()
        # Remove pontos de milhar, mantendo o decimal correto
        if numero.count(".") > 1:
            partes = numero.split(".")
            numero = "".join(partes[:-1]) + "." + partes[-1]
        return float(numero)
    else:
        return 0.0

def coletar_preco(produto):
    """Coleta o preço principal de um produto na página usando BeautifulSoup."""
    params = {'api_key': API_KEY, 'url': produto["url"]}
    try:
        response = requests.get("https://api.scraperapi.com/", params=params)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            possiveis_precos = []
            for tag in soup.find_all("span"):
                texto = tag.get_text().strip()
                if re.match(r"r\$ ?\d{1,3}(?:[.,]\d{3})*[.,]\d{2}", texto.lower()):
                    possiveis_precos.append(texto)

            if not possiveis_precos:
                conteudo = response.text.lower()
                possiveis_precos = re.findall(r"r\$ ?\d{1,3}(?:[.,]\d{3})*[.,]\d{2}", conteudo)

            if possiveis_precos:
                # Remove duplicatas
                precos_unicos = list(set(possiveis_precos))

                # Pega o menor preço (normalmente o padrão do produto)
                preco_formatado = sorted(precos_unicos, key=normalizar_preco)[0]

                # Retorna o preço sem duplicação
                return preco_formatado.upper()
            else:
                return "Preço não encontrado"
        else:
            return f"Erro HTTP {response.status_code}"
    except Exception as e:
        return f"Erro: {e}"


def gerar_relatorios(dados):
    """Cria CSV e TXT com os preços coletados"""
    os.makedirs("dados_historicos", exist_ok=True)
    os.makedirs("relatorios", exist_ok=True)

    data = datetime.now().strftime("%Y-%m-%d %H:%M")

    # CSV
    with open("dados_historicos/precos.csv", "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if csvfile.tell() == 0:
            writer.writerow(["Data", "Produto", "Preço"])
        for produto, preco in dados.items():
            writer.writerow([data, produto, preco])

    # TXT
    with open("relatorios/relatorio_atual.txt", "w", encoding="utf-8") as txtfile:
        txtfile.write(f"Relatório de preços - {data}\n")
        txtfile.write("="*50 + "\n")
        for produto, preco in dados.items():
            txtfile.write(f"{produto}: {preco}\n")

    print("\n✅ Relatórios gerados com sucesso!")
    print("→ dados_historicos/precos.csv")
    print("→ relatorios/relatorio_atual.txt")

if __name__ == "__main__":
    resultados = {}
    print("🔍 Coletando preços...\n")

    for p in produtos:
        preco = coletar_preco(p)
        resultados[p["nome"]] = preco
        print(f"{p['nome']}: {preco}")

    gerar_relatorios(resultados)

    # Envia relatório por e-mail
    enviar_relatorio()

    from historico import salvar_historico

# Depois de gerar relatórios
salvar_historico(resultados)
print("📌 Histórico atualizado com sucesso!")

# Queda
alertas = queda(resultados, "dados_historicos/precos.csv", minima=10)
print("Alertas retornados:", alertas)