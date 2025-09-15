import random
import time

from interface_adapters.up.up_util.up_util import Up_util
from utils import mouse_util
from utils.teclado_util import Teclado_util


class AlterarCharSalaService:
    def __init__(self, handle, senha, conexao_arduino=None):
        self.handle = handle
        self.senha = senha
        self.conexao_arduino = conexao_arduino
        self.up_util = Up_util(self.handle, conexao_arduino=conexao_arduino)
        self.teclado_util = Teclado_util(self.handle, conexao_arduino)

    def selecionar_sala(self, sala=None):
        self.teclado_util.tap_esc()
        mouse_util.tira_mouse_tela(self.handle)
        time.sleep(2)

        acoes_troca_sala = [
            ["./static/img/escolhersala.png", (398, 208)],
            ["./static/img/selecionarsalas.png", (222, 216)]
        ]

        if sala == 7:
            acoes_troca_sala.append(["./static/img/sala7.png", (420, 371)])
        else:
            salas = [
                (401, 249),  # 2
                (402, 272),  # 3
                (394, 294),  # 4
                (385, 396)  # 10
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

        # Digitar senha e confirmar
        # Teclado_util(self.handle, self.conexao_arduino).
        # self.teclado_util.enviar_texto_senha(self.handle, self.senha)
        mouse_util.clicar_na_imagem_ou_coordenada(self.handle, "./static/img/btnoksenha.png", None)
        self.up_util.selecionar_char_no_launcher()
