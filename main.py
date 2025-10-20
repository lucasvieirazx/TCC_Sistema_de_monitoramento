# main.py
import os
import csv
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from config import API_KEY
from enviar_email import enviar_relatorio

# Criação de pastas
os.makedirs("dados_historicos", exist_ok=True)
os.makedirs("relatorios", exist_ok=True)

# Lista de produtos
produtos = [
    {"nome": "Notebook Lenovo Ideapad 3", "url": "https://www.amazon.com.br/s?k=notebook+lenovo+ideapad+3"},
    {"nome": "Notebook Acer Aspire 5", "url": "https://www.amazon.com.br/s?k=notebook+acer+aspire+5"},
    {"nome": "Placa de Vídeo RTX 3060", "url": "https://www.amazon.com.br/s?k=rtx+3060"},
]

def normalizar_preco(valor):
    valor = valor.lower().replace("r$", "").replace(" ", "").replace(",", ".")
    numeros = re.findall(r"\d+(?:\.\d+)?", valor)
    if numeros:
        return min([float(n) for n in numeros])
    return 0.0

def coletar_preco(produto):
    params = {'api_key': API_KEY, 'url': produto["url"]}
    try:
        response = requests.get("https://api.scraperapi.com/", params=params)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            precos = []
            for tag in soup.find_all("span"):
                texto = tag.get_text().strip()
                if re.match(r"r\$ ?\d{1,3}(?:[.,]\d{3})*[.,]\d{2}", texto.lower()):
                    precos.append(texto)
            if not precos:
                conteudo = response.text.lower()
                precos = re.findall(r"r\$ ?\d{1,3}(?:[.,]\d{3})*[.,]\d{2}", conteudo)
            if precos:
                precos_unicos = list(set(precos))
                preco_formatado = sorted(precos_unicos, key=normalizar_preco)[0]
                return preco_formatado.upper()
            else:
                return "Preço não encontrado"
        else:
            return f"Erro HTTP {response.status_code}"
    except Exception as e:
        return f"Erro: {e}"

def salvar_historico(dados):
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Histórico completo
    with open("dados_historicos/precos.csv", "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if csvfile.tell() == 0:
            writer.writerow(["Data", "Produto", "Preço"])
        for produto, preco in dados.items():
            writer.writerow([data, produto, preco])
    # Histórico do último preço
    with open("dados_historicos/ultimo_preco.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Produto", "Preço"])
        for produto, preco in dados.items():
            writer.writerow([produto, preco])

def gerar_relatorio_txt(dados):
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    relatorio_path = "relatorios/relatorio_atual.txt"
    with open(relatorio_path, "w", encoding="utf-8") as txtfile:
        txtfile.write(f"📌 Relatório de preços - {data}\n")
        txtfile.write("="*50 + "\n\n")
        for produto in produtos:
            nome = produto["nome"]
            url = produto["url"]
            preco = dados.get(nome, "Não encontrado")
            txtfile.write(f"💻 {nome}\nURL: {url}\nPreço: {preco}\n\n")
        # Estatísticas simples
        precos_float = [normalizar_preco(preco) for preco in dados.values()
                        if preco != "Preço não encontrado" and "Erro" not in preco]
        if precos_float:
            txtfile.write("="*50 + "\n")
            txtfile.write(f"🔹 Preço mínimo: R${min(precos_float):.2f}\n")
            txtfile.write(f"🔹 Preço máximo: R${max(precos_float):.2f}\n")
            txtfile.write(f"🔹 Preço médio: R${sum(precos_float)/len(precos_float):.2f}\n")
    print(f"✅ Relatório TXT gerado: {relatorio_path}")

if __name__ == "__main__":
    resultados = {}
    print("🔍 Coletando preços...\n")
    for p in produtos:
        preco = coletar_preco(p)
        resultados[p["nome"]] = preco
        print(f"{p['nome']}: {preco}")
    salvar_historico(resultados)
    gerar_relatorio_txt(resultados)
    enviar_relatorio()
    print("\n📌 Processo concluído!")
