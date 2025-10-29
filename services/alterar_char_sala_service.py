import random
import time

import win32gui

from interface_adapters.up.up_util.up_util import Up_util
from utils import mouse_util
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class AlterarCharSalaService:
    def __init__(self, handle, senha, arduino):
        self.handle = handle
        self.senha = senha
        self.arduino = arduino
        self.up_util = Up_util(self.handle, conexao_arduino=arduino)
        self.pointer = Pointers(self.handle)
        self.teclado_util = Teclado_util(self.handle, arduino)
        self.titulo_janela = win32gui.GetWindowText(handle)

    def selecionar_sala(self, sala=None):
        mouse_util.desativar_click_esquerdo(self.handle)
        mouse_util.desativar_click_direito(self.handle)
        self.teclado_util.tap_esc()
        mouse_util.tira_mouse_tela(self.handle)
        time.sleep(2)

        acoes_troca_sala = [
            ["./static/img/escolhersala.png", (398, 208)],
            ["./static/img/selecionarsalas.png", (222, 216)]
        ]

        print('Movendo para sala:' + str(sala) + ' - ' + self.titulo_janela)

        if sala == 2:
            acoes_troca_sala.append(["./static/img/sala2.png", (401, 249)])
        elif sala == 3:
            acoes_troca_sala.append([None, (401, 272)])
        elif sala == 8:
            acoes_troca_sala.append([None, (401, 401)])
        elif sala == 7:
            acoes_troca_sala.append(["./static/img/sala7.png", (420, 371)])
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

        for menu, coord_mouse in acoes_troca_sala:
            if menu is None:
                mouse_util.left_clique(self.handle, *coord_mouse)
            else:
                mouse_util.clicar_na_imagem_ou_coordenada(self.handle, menu, coord_mouse)
                if 'escolhersala' in menu:
                    time.sleep(4)
            time.sleep(2)

        mouse_util.tira_mouse_tela(self.handle)

        self.teclado_util.digitar_senha(self.senha)
        mouse_util.clicar_na_imagem_ou_coordenada(self.handle, "./static/img/btnoksenha.png", None)
        self.up_util.selecionar_char_no_launcher()

        if sala is not None and sala != self.pointer.get_sala_atual():
            print('Tentado  selecionar novamente a sala!')
            self.selecionar_sala(sala)
