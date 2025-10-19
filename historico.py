# historico.py
import csv
from datetime import datetime
import os

def salvar_historico(resultados: dict):
    """
    Salva no CSV: data, produto, preço.
    Cria o arquivo com cabeçalho se não existir.
    """
    caminho = "dados_historicos/precos.csv"
    os.makedirs("dados_historicos", exist_ok=True)

    arquivo_existe = os.path.isfile(caminho)

    with open(caminho, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Se for a primeira vez, grava o cabeçalho
        if not arquivo_existe:
            writer.writerow(["data", "produto", "preco"])

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for produto, preco in resultados.items():
            writer.writerow([agora, produto, preco])
