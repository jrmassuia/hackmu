import os
import time

from utils import mouse_util, screenshot_util
from utils.buscar_item_util import BuscarItemUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class SelecionarCharUtil:

    def __init__(self, handle):
        self.handle = handle
        self.teclado_util = Teclado_util()
        self.char_atual = Pointers().get_nome_char()

    def _lista_char_para_selecionar(self):
        return [
            ('BLEKALT', 0), ('DL_DoMall', 2),
            #
            ('TOROUVC', 1),
            #
            ('INFECTRIX', 0),
            #
            ('Omale_DL', 1),
            #
            ('ESTAMUERTO', 1),
            #
            ('Deef_Stret', 0),
            #
            ('ReiDav1', 4),
            #
            ('Shokito', 0),
            #
            ('Yzzuth', 0),
            #
            ('AlfaVictor', 3),
            #
            ('_Offensive', 2),
            #
            ('LAZLU', 3),
            #
            ('DL_JirayA', 3)
        ]

    def reiniciar_char(self):
        self.teclado_util.tap_esc()
        mouse_util.tira_mouse_tela(self.handle)
        while True:
            clicou = mouse_util.clicar_na_imagem_ou_coordenada(
                self.handle, "./static/img/selecionarpersonagem.png", None
            )
            if clicou:
                self.selecionar_char_no_launcher()
                time.sleep(3)
                self.teclado_util.selecionar_skill_1()
                break

    def selecionar_char_no_launcher(self):
        time.sleep(6)  # AGUARDA VOLTAR PARA SELECIONAR CHAR
        achou = self.selecionar_char_por_posicao()
        if not achou:
            self.selecionar_char_por_imagem()

        print('Achou personagem ao selecionar no launcher: ' + self.char_atual)
        self.teclado_util.selecionar_skill_1()
        self.teclado_util.pressionar_zoon()
        self.teclado_util.escrever_texto('/re off')

    def selecionar_char_por_posicao(self):
        for nome, posicao in self._lista_char_para_selecionar():
            if nome == self.char_atual:
                x = 0
                y = 0
                if posicao == 0:
                    x = 156
                    y = 410
                elif posicao == 1:
                    x = 274
                    y = 410
                elif posicao == 2:
                    x = 406
                    y = 410
                elif posicao == 3:
                    x = 534
                    y = 410
                elif posicao == 4:
                    x = 655
                    y = 410

                mouse_util.left_clique(self.handle, x, y)
                mouse_util.left_clique(self.handle, x, y)
                time.sleep(1)

                self.clicar_na_imagem_ou_fallback('./static/img/btnconnect.png', None)
                time.sleep(3)
                return True
        return False

    def selecionar_char_por_imagem(self):
        folder_path = "./static/up/char"
        mouse_util.tira_mouse_tela(self.handle)
        print('Procurando char no launcher!')
        while True:
            for filename in os.listdir(folder_path):
                if filename.endswith((".png", ".jpg")):
                    image_position = self.verifica_se_personagem_esta_na_tela(folder_path, filename)
                    if image_position:
                        x, y = image_position
                        mouse_util.left_clique(self.handle, x, y + 160)
                        mouse_util.left_clique(self.handle, x, y + 160)
                        time.sleep(1)
                        self.clicar_na_imagem_ou_fallback('./static/img/btnconnect.png', None)
                        time.sleep(3)

                        image_position = self.verifica_se_personagem_esta_na_tela(folder_path, filename)
                        if image_position:
                            print('Não achou personagem ao selecionar no launcher: ' + filename)
                            self.selecionar_char_no_launcher()
                        else:
                            return True

    def verifica_se_personagem_esta_na_tela(self, folder_path, filename):
        template_image_path = os.path.join(folder_path, filename)
        screenshot = screenshot_util.capture_window(self.handle)
        image_position = BuscarItemUtil().buscar_imagem_na_janela(screenshot,
                                                                  template_image_path,
                                                                  precisao=.80)
        return image_position

    def clicar_na_imagem_ou_fallback(self, imagem_path, fallback_position, timeout=60):
        mouse_util.mover(self.handle, 1, 1)
        start_time = time.time()
        while time.time() - start_time < timeout:
            # posicao = buscar_item_util.buscar_item_especifico(self.handle, imagem_path)
            posicao = BuscarItemUtil().buscar_item_simples(imagem_path)
            if posicao:
                mouse_util.left_clique(self.handle, posicao[0], posicao[1])
                return True
            else:
                if fallback_position:
                    mouse_util.mover_click(*fallback_position)
        return False
