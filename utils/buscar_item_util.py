import os

import cv2
import numpy as np

from sessao_handle import get_handle_atual
from utils import screenshot_util


class BuscarItemUtil:
    def __init__(self):
        self.handle = get_handle_atual()

    def _carregar_template(self, caminho_imagem):
        template = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"Erro ao carregar imagem: {caminho_imagem}")
        return template

    def buscar_imagem_na_janela(self, screenshot, caminho_template, precisao=0.8, todas=False):
        try:
            imagem_cinza = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            template = self._carregar_template(caminho_template)
            if template is None:
                return [] if todas else None

            resultado = cv2.matchTemplate(imagem_cinza, template, cv2.TM_CCOEFF_NORMED)
            y_coords, x_coords = np.where(resultado >= precisao)
            altura, largura = template.shape[:2]

            posicoes = [
                (x + largura // 2, y + altura // 2)
                for x, y in zip(x_coords, y_coords)
            ]

            if not posicoes:
                return None

            return posicoes if todas else posicoes[0]
        except Exception as e:
            print(f'Erro ao processar imagem: {e}')
            return None

    def _ignorar_chat(self, x, y):
        return not (x <= 150 and y <= 150)

    def _buscar_item_autopick(self, item_especifico=None):
        return self._buscar_em_pasta('./static/autopick', item_especifico)

    def buscar_item_especifico_autopick(self, item_especifico):
        return self._buscar_item_autopick(item_especifico)

    def buscar_item_geral_autopick(self):
        return self._buscar_item_autopick(None)

    def buscar_item_spot(self):
        x, y, item = self._buscar_em_pasta('./static/item_spot')
        return item is not None

    def _buscar_em_pasta(self, caminho_pasta, item_especifico=None):
        screenshot = screenshot_util.capture_window(self.handle)
        if screenshot is None:
            return None, None, None

        imagem_cinza = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        templates = []

        for arquivo in os.listdir(caminho_pasta):
            if arquivo.endswith((".png", ".jpg")):
                caminho = os.path.join(caminho_pasta, arquivo)
                template = self._carregar_template(caminho)
                if template is not None:
                    templates.append((arquivo, template))

        for nome_arquivo, template in templates:
            resultado = cv2.matchTemplate(imagem_cinza, template, cv2.TM_CCOEFF_NORMED)
            y_coords, x_coords = np.where(resultado >= 0.8)

            altura, largura = template.shape
            for x, y in zip(x_coords, y_coords):
                centro_x = x + largura // 2
                centro_y = y + altura // 2

                if self._ignorar_chat(centro_x, centro_y):
                    if item_especifico:
                        if nome_arquivo in item_especifico:
                            return centro_x, centro_y, os.path.join(caminho_pasta, nome_arquivo)
                    return centro_x, centro_y, os.path.join(caminho_pasta, nome_arquivo)

        return None, None, None

    def buscar_posicoes_de_item(self, imagem_item, screenshot=None, precisao=0.8):
        if screenshot is None:
            screenshot = screenshot_util.capture_window(self.handle)
        return self.buscar_imagem_na_janela(screenshot, imagem_item, precisao, todas=True)

    def buscar_varios_itens(self, caminho_pasta, screenshot=None, precisao=0.9):
        if screenshot is None:
            screenshot = screenshot_util.capture_window(self.handle)

        imagem_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        itens_encontrados = []

        for nome_arquivo in os.listdir(caminho_pasta):
            caminho_template = os.path.join(caminho_pasta, nome_arquivo)
            img_template = cv2.imread(caminho_template)
            if img_template is None:
                continue

            resultado = cv2.matchTemplate(imagem_bgr, img_template, cv2.TM_CCOEFF_NORMED)
            locais = np.where(resultado >= precisao)

            for pt in zip(*locais[::-1]):
                nome_item = os.path.splitext(nome_arquivo)[0]
                itens_encontrados.append([pt[0], pt[1], nome_item])

        return itens_encontrados

    def buscar_item_simples(self, caminho_imagem):
        screenshot = screenshot_util.capture_window(self.handle)
        if screenshot is None:
            return None
        return self.buscar_imagem_na_janela(screenshot, caminho_imagem)


def load_template(template_image_path):
    """Carrega a imagem do template e retorna em escala de cinza."""
    template = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"Erro ao carregar a imagem: {template_image_path}")
    return template


def buscar_posicoes_item_epecifico(item, screenshot, confidence_=0.8):
    return find_image_in_window(screenshot, item, confidence_threshold=confidence_, find_all=True)


def find_image_in_window(screenshot, template_image_path, confidence_threshold=0.8, find_all=False):
    try:
        # Converte a captura de tela para escala de cinza
        screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

        # Carrega o template e verifica se foi carregado corretamente
        template = load_template(template_image_path)
        if template is None:
            return [] if find_all else None

        # Aplica a correspondência de template
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)

        # Encontra todas as localizações com o valor de confiança maior ou igual ao limiar
        y_coords, x_coords = np.where(result >= confidence_threshold)
        template_height, template_width = template.shape[:2]

        # Armazena as coordenadas centrais das correspondências encontradas
        positions = [
            (x + template_width // 2, y + template_height // 2)
            for x, y in zip(x_coords, y_coords)
        ]

        if len(positions) == 0:
            return None

        # Retorna conforme a necessidade
        if find_all:
            return positions
        return positions[0] if positions else None
    except Exception as e:
        print(f'ERRO AO PROCESSAR IMAGEM! {e}')
        return None
