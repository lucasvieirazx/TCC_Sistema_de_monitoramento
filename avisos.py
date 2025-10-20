# avisos.py
import csv
import re

def extrair_valor(texto):
    """
    Extrai o menor número de um intervalo ou de texto.
    Ex:
      "R$1.700 A R$3.200" -> 1700.0
      "R$21.200 E MAIS" -> 21200.0
      "R$3.500" -> 3500.0
    """
    texto = texto.replace("R$", "").replace(" ", "").replace(",", ".")
    numeros = re.findall(r"\d+(?:\.\d+)?", texto)
    if numeros:
        valores = [float(n) for n in numeros]
        return min(valores)
    return 0.0

def queda(resultados_atual: dict, arquivo_csv: str, minima: float = 10.0):
    """
    Compara os preços atuais com o último preço salvo no CSV.
    Retorna dicionário com produtos que tiveram queda >= minima (%)
    """
    ultimo = {}

    # Lê histórico anterior
    try:
        with open(arquivo_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Ignora maiúsculas/minúsculas nos nomes das colunas
            field_map = {name.lower(): name for name in reader.fieldnames}

            for linha in reader:
                produto = linha[field_map.get("produto", "Produto")]
                preco = linha[field_map.get("preço", "Preço")]
                try:
                    preco_float = extrair_valor(preco)
                    ultimo[produto] = preco_float
                except ValueError:
                    continue
    except FileNotFoundError:
        print("⚠️ Nenhum histórico encontrado ainda. Criando novo arquivo...")
        return {}

    avisos = {}
    for produto, preco_atual_str in resultados_atual.items():
        preco_atual = extrair_valor(preco_atual_str)
        if produto in ultimo:
            preco_antigo = ultimo[produto]
            if preco_atual < preco_antigo:
                queda_pct = ((preco_antigo - preco_atual) / preco_antigo) * 100
                if queda_pct >= minima:
                    avisos[produto] = {
                        "antigo": preco_antigo,
                        "novo": preco_atual,
                        "queda": round(queda_pct, 2)
                    }

    # Imprime no console os produtos que caíram
    if avisos:
        print("\n⚠️ Produtos com queda de preço detectada:")
        for produto, dados in avisos.items():
            print(f"{produto}: caiu de R${dados['antigo']:.2f} para R${dados['novo']:.2f} ({dados['queda']}%)")
    else:
        print("\n✅ Nenhuma queda significativa detectada.")

    return avisos
