import random
import time
import pyperclip
import pyautogui
import win32gui

from interface_adapters.up.up_util.up_util import Up_util
from utils import mouse_util
from utils.buscar_item_util import BuscarItemUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class AlterarCharSalaService:
    def __init__(self, handle, senha, char=None):
        self.handle = handle
        self.senha = senha
        self.char = char
        self.up_util = Up_util()
        self.pointer = Pointers()
        self.teclado_util = Teclado_util()
        self.titulo_janela = win32gui.GetWindowText(handle)
        self.buscar_imagem = BuscarItemUtil(self.handle)

    def selecionar_sala(self, sala=None):
        mouse_util.desativar_click_esquerdo(self.handle)
        mouse_util.desativar_click_direito(self.handle)
        mouse_util.tira_mouse_tela(self.handle)

        acoes_troca_sala = []

        print('Movendo para sala:' + str(sala) + ' - ' + self.titulo_janela)

        if sala == 1:
            acoes_troca_sala.append([None, (401, 216)])
        elif sala == 2:
            acoes_troca_sala.append(["./static/img/sala2.png", (401, 249)])
        elif sala == 3:
            acoes_troca_sala.append([None, (401, 272)])
        elif sala == 4:
            acoes_troca_sala.append([None, (401, 294)])
        elif sala == 5:
            acoes_troca_sala.append([None, (401, 318)])
        elif sala == 6:
            acoes_troca_sala.append([None, (401, 346)])
        elif sala == 7:
            acoes_troca_sala.append(["./static/img/sala7.png", (401, 371)])
        elif sala == 8:
            acoes_troca_sala.append([None, (401, 401)])
        elif sala == 9:
            acoes_troca_sala.append([None, (401, 427)])
        else:
            salas = [
                (401, 249),  # 2
                (401, 272),  # 3
                (401, 294),  # 4
                (401, 318),  # 5
                # (401, 346),  # 6
                # (401, 374),  # 7
                (401, 401),  # 8
                (401, 427),  # 9
                (401, 396)  # 10
            ]
            escolha = random.choice(salas)
            acoes_troca_sala.append([None, escolha])

        self._clicar_no_escolher_sala()
        self._clicar_no_selecionar_sala()

        for menu, coord_mouse in acoes_troca_sala:
            if menu is None:
                mouse_util.left_clique(self.handle, *coord_mouse)
            else:
                mouse_util.clicar_na_imagem_ou_coordenada(self.handle, menu, coord_mouse)
            time.sleep(2)

        mouse_util.tira_mouse_tela(self.handle)

        self.teclado_util.digitar_senha(self.senha)
        mouse_util.clicar_na_imagem_ou_coordenada(self.handle, "./static/img/btnoksenha.png", None)

        if 'Narukami' == self.char:
            while True:
                mouse_util.tira_mouse_tela(self.handle)
                pyautogui.moveTo(500, 500)  # clica no token do navegador
                pyautogui.click()
                token = pyperclip.paste()
                self.teclado_util.digitar_token(token)
                mouse_util.clicar_na_imagem_ou_coordenada(self.handle, "./static/img/btnoktoken.png", None)
                time.sleep(1)
                msgtokeninvalido = self.buscar_imagem.buscar_posicoes_de_item(
                    './static/img/msgtokeninvalido.png', precisao=0.90)
                if msgtokeninvalido is None:
                    break
                else:
                    mouse_util.left_clique(self.handle, 402, 330)  # CLICA NO OK MSG TOKEN INVALIDO

        self.up_util.selecionar_char_no_launcher(self.char)

        if sala is not None and sala != self.pointer.get_sala_atual():
            print('Tentado  selecionar novamente a sala!')
            self.selecionar_sala(sala)

    def _clicar_no_escolher_sala(self):
        imagem = './static/img/escolhersala.png'
        while True:
            mouse_util.tira_mouse_tela(self.handle)
            self.teclado_util.tap_esc()
            time.sleep(2)
            achou = self._validar_se_opcao_esta_na_tela(imagem)
            if achou:
                mouse_util.left_clique(self.handle, 398, 208)
                break
        time.sleep(5)

    def _clicar_no_selecionar_sala(self):
        imagem = './static/img/selecionarsalas.png'
        while True:
            mouse_util.tira_mouse_tela(self.handle)
            achou = self._validar_se_opcao_esta_na_tela(imagem)
            if achou:
                mouse_util.left_clique(self.handle, 222, 216)
                break
            else:
                self._clicar_no_escolher_sala()
        time.sleep(3)

    def _validar_se_opcao_esta_na_tela(self, imagem):
        end_time = time.time() + 10
        while time.time() < end_time:
            imagem_apareceu = self.buscar_imagem.buscar_posicoes_de_item(imagem)
            if imagem_apareceu:
                return True
        print('NAO ACHOU A IMAGEM AO SELECIONAR OPÇÃO: ' + imagem)
        return False
