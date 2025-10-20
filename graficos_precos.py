# graficos_precos.py
import matplotlib.pyplot as plt

def gerar_graficos():
    """Função de teste garantida para rodar sem erro."""
    print("Função gerar_graficos importada com sucesso!")
    # Gráfico de teste
    plt.plot([1, 2, 3], [4, 5, 6])
    plt.title("Gráfico de teste")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.show()

# Teste rápido
if __name__ == "__main__":
    gerar_graficos()
