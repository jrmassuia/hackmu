import win32gui

window_title = "[1/3] MUCABRASIL - NVIDIA GeForce GTX 1050 Ti/PCIe/SSE2 - Rota Illusion66"
handle = win32gui.FindWindow(None, window_title)

from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

def mostrar_cores_unicas(img_path):
    # Carrega a imagem
    img = Image.open(img_path)
    img_np = np.array(img)

    # Redimensiona a imagem para uma lista de pixels (r, g, b)
    pixels = img_np.reshape(-1, img_np.shape[-1])

    # Extrai cores únicas
    cores_unicas = np.unique(pixels, axis=0)

    # Exibe as cores únicas
    print(f"Total de cores únicas encontradas: {len(cores_unicas)}")
    for i, cor in enumerate(cores_unicas):
        print(f"Cor {i+1}: RGB {cor}")

    # Plota as cores únicas em uma grade
    tamanho_grid = int(np.ceil(np.sqrt(len(cores_unicas))))
    fig, axs = plt.subplots(tamanho_grid, tamanho_grid, figsize=(10, 10))

    # Remove eixos de todos os subplots
    for ax in axs.ravel():
        ax.axis('off')

    for i, cor in enumerate(cores_unicas):
        r, g, b = cor[:3]  # Apenas os três primeiros valores para RGB
        ax = axs[i // tamanho_grid, i % tamanho_grid]
        ax.set_facecolor((r / 255, g / 255, b / 255))

    plt.show()

# Exemplo de uso
img_path = 'region.png'  # Caminho para a imagem
mostrar_cores_unicas(img_path)
