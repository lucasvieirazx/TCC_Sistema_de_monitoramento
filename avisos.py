# avisos.py
import csv

def queda(resultados_atual: dict, arquivo_csv: str, minima: float = 10.0):
    
    """
    Compara os preços atuais com o último preço salvo no CSV.
    Retorna dicionário com produtos que tiveram queda >= minima (%)
    e imprime os resultados no console.
    """
    ultimo = {}

    # Lê histórico anterior
    try:
        with open(arquivo_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for linha in reader:
                produto = linha["produto"]
                preco = linha["preco"]
                try:
                    preco_float = float(str(preco).replace(",", "."))
                    ultimo[produto] = preco_float
                except ValueError:
                    continue
    except FileNotFoundError:
        print("⚠️ Nenhum histórico encontrado ainda. Criando novo arquivo...")
        return {}

    avisos = {}
    for produto, preco_atual_str in resultados_atual.items():
        try:
            preco_atual = float(str(preco_atual_str).replace("R$", "").replace(",", ".").replace(" ", ""))
        except ValueError:
            continue

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
