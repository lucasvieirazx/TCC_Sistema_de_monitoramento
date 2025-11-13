# enviar_email.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL, SENHA
from datetime import datetime
import csv
import re
import os

def parse_price(text):
    """
    Converte várias formas de texto de preço para float seguro.
    - Remove 'R$', espaços, troca ',' por '.'
    - Se houver vários pontos, assume último como decimal e junta os anteriores
    - Para intervalos, retorna o menor valor encontrado
    - Para 'E MAIS' pega o número presente
    - Retorna float (0.0 se não conseguir)
    """
    if text is None:
        return 0.0
    s = str(text).strip()
    # normaliza virgulas -> pontos, remove currency
    s = s.replace("R$", "").replace(" ", "").replace(",", ".")
    # extrai números com pontos
    nums = re.findall(r"\d+(?:\.\d+)*", s)
    if not nums:
        return 0.0

    # Se houver múltiplos grupos (por exemplo intervalo "1700.00A3200.00" -> ['1700.00','3200.00'])
    floats = []
    for n in nums:
        # remover caracteres indesejados
        part = re.sub(r"[^0-9.]", "", n)
        if not part:
            continue
        parts = part.split(".")
        try:
            if len(parts) > 2:
                # ex: "3.597.00" -> juntar todos menos o último como inteiro e o último como decimal
                integer = "".join(parts[:-1])
                decimal = parts[-1]
                normalized = integer + "." + decimal
                val = float(normalized)
            elif len(parts) == 2:
                # um ponto: se a parte depois do ponto tem 3 dígitos, provavelmente separador de milhar (21.200)
                if len(parts[1]) == 3:
                    normalized = parts[0] + parts[1]  # remove ponto como milhar
                    val = float(normalized)
                else:
                    val = float(part)
            else:
                val = float(part)
            floats.append(val)
        except Exception:
            # fallback: extrai dígitos e faz tentativa
            digits = re.findall(r"\d+", part)
            if not digits:
                continue
            joined = "".join(digits)
            if len(joined) <= 2:
                try:
                    floats.append(float(joined))
                except:
                    pass
            else:
                try:
                    floats.append(float(joined[:-2] + "." + joined[-2:]))
                except:
                    pass
    if not floats:
        return 0.0
    # se veio intervalo (múltiplos valores), usar o menor (regra que você escolheu)
    return min(floats)


def enviar_relatorio():
    """
    Envia um e-mail formatado em HTML com os preços coletados e um resumo.
    Destinatários: EMAIL (config.py) e lucasdossantosvieira3@gmail.com
    """
    try:
        # Caminhos
        txt_path = os.path.join("relatorios", "relatorio_atual.txt")
        ultimo_path = os.path.join("dados_historicos", "ultimo_preco.csv")
        precos_path = os.path.join("dados_historicos", "precos.csv")

        # Lê conteúdo do TXT (fallback para lista simples)
        produtos_txt = []
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                linhas = [l.strip() for l in f.readlines() if l.strip()]
            produtos_txt = [l for l in linhas if ":" in l]

        # Lê último_preco.csv (se existir)
        ultimo = {}
        if os.path.exists(ultimo_path):
            with open(ultimo_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for linha in reader:
                    nome = linha.get("Produto") or linha.get("produto")
                    preco_text = linha.get("Preço") or linha.get("preco")
                    if nome and preco_text is not None:
                        ultimo[nome] = parse_price(preco_text)

        # Lê precos.csv e pega a última ocorrência por produto (último preço atual)
        atuais = {}
        if os.path.exists(precos_path):
            with open(precos_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for linha in reader:
                    nome = linha.get("Produto") or linha.get("produto")
                    preco_text = linha.get("Preço") or linha.get("preco")
                    if nome and preco_text is not None:
                        atuais[nome] = parse_price(preco_text)
        else:
            print("⚠️ dados_historicos/precos.csv não encontrado. O e-mail será gerado com base no TXT, se disponível.")

        # Monta corpo HTML elegante
        data = datetime.now().strftime("%d/%m/%Y %H:%M")
        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f7f9fc; padding: 20px;">
            <h2 style="color:#2e86de;">🧠 Relatório Automático de Monitoramento de Preços</h2>
            <p><b>Data:</b> {data}</p>
            <p>📊 <b>Total de produtos analisados:</b> {len(atuais) if atuais else len(produtos_txt)}</p>
            <hr style="border:1px solid #ccc;">
            <h3>💻 Produtos Monitorados:</h3>
        """

        if atuais:
            for nome, preco_atual in atuais.items():
                preco_antigo = ultimo.get(nome)
                if preco_antigo is None:
                    queda_pct = 0.0
                else:
                    try:
                        queda_pct = ((preco_antigo - preco_atual) / preco_antigo) * 100 if preco_antigo != 0 else 0.0
                    except Exception:
                        queda_pct = 0.0
                emoji = "📉" if queda_pct > 0 else "✅"
                corpo_html += f"""
                <div style="margin-bottom:12px;">
                    <p style="margin:0;">🔹 <b>{nome}</b></p>
                    <p style="margin:0;">Preço atual: R${preco_atual:,.2f}</p>
                """
                if preco_antigo is not None:
                    corpo_html += f"<p style='margin:0;'>Preço anterior: R${preco_antigo:,.2f} — Variação: {queda_pct:.2f}% {emoji}</p>"
                corpo_html += "</div>"
        else:
            # fallback ao TXT simples
            for linha in produtos_txt:
                corpo_html += f"<p>🔹 {linha}</p>"

        corpo_html += """
            <hr style="border:1px solid #ccc;">
            <p>🤖 <i>Relatório gerado automaticamente pelo Sistema Inteligente de Monitoramento de Preços.</i></p>
            <p>📈 Desenvolvido por <b>Grupo TCC</b></p>
        </body>
        </html>
        """

        # Monta mensagem
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "📊 Relatório de Preços - Sistema Inteligente"
        msg["From"] = EMAIL
        destinatarios = [EMAIL, "lucasdossantosvieira3@gmail.com"]
        msg["To"] = ", ".join(destinatarios)
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        # Envia
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login(EMAIL, SENHA)
            servidor.sendmail(EMAIL, destinatarios, msg.as_string())

        print(f"📩 E-mail enviado com sucesso para: {', '.join(destinatarios)}")

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
