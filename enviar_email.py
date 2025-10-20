# enviar_email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
from datetime import datetime
from config import EMAIL, SENHA

def enviar_relatorio():
    """Envia e-mail com relatório detalhado e comparativo de preços."""
    
    # Lê o histórico do último preço
    ultimo = {}
    try:
        with open("dados_historicos/ultimo_preco.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for linha in reader:
                nome = linha["Produto"]
                preco = linha["Preço"]
                # Converte para float para poder calcular percentual
                preco_float = float(preco.replace("R$", "").replace(" ", "").replace(",", "."))
                ultimo[nome] = preco_float
    except FileNotFoundError:
        print("⚠️ Arquivo ultimo_preco.csv não encontrado. Não será possível comparar com preços anteriores.")

    # Lê o relatório atual
    atuais = {}
    with open("dados_historicos/precos.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        linhas = list(reader)
        if linhas:
            ultima_linha = linhas[-len(ultimo):]  # pega os últimos registros
            for linha in ultima_linha:
                nome = linha["Produto"]
                preco = linha["Preço"]
                preco_float = float(preco.replace("R$", "").replace(" ", "").replace(",", "."))
                atuais[nome] = preco_float

    # Monta o corpo do e-mail
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    corpo = f"📌 Relatório de preços - {data}\n\n"

    for produto in atuais:
        preco_atual = atuais[produto]
        preco_antigo = ultimo.get(produto, preco_atual)
        queda = ((preco_antigo - preco_atual) / preco_antigo * 100) if produto in ultimo else 0
        if queda > 0:
            emoji = "📉"
        else:
            emoji = "✅"
        corpo += (
            f"💻 {produto}\n"
            f"Preço anterior: R${preco_antigo:.2f}\n"
            f"Preço atual: R${preco_atual:.2f}\n"
            f"Queda: {queda:.2f}% {emoji}\n\n"
        )

    corpo += "🎯 Todos os preços atualizados!\n"

    # Monta o e-mail
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = EMAIL  # Pode trocar para lista de destinatários
    msg["Subject"] = "📬 Relatório de Preços Atualizado"
    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(EMAIL, SENHA)
        servidor.sendmail(EMAIL, EMAIL, msg.as_string())
        servidor.quit()
        print("📩 E-mail de relatório enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
