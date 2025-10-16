import time

from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from utils import mouse_util, safe_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.selecionar_char_util import SelecionarCharUtil
from utils.teclado_util import Teclado_util


class ResetUseCase:

    def __init__(self, handle, conexao_arduino, char_nome, resets):
        self.handle = handle
        self.char_nome = char_nome
        self.resets = resets
        self.sessao = Sessao(handle=handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.pointer = Pointers(handle)
        self.conexao_arduino = conexao_arduino
        self.teclado_util = Teclado_util(self.handle, conexao_arduino)

    def executar(self):
        if self.resets >= 250:
            self._resetar_lorencia_desafio()
        elif self.classe == 'EF':
            self._resetar_noria()
        else:
            self._resetar_lorencia()

        mouse_util.mover(self.handle, 1, 1)
        time.sleep(6)  # AGUARDA VOLTAR PARA SELECIONAR CHAR
        self.selecionar_char_no_launcher()
        self._destribuir_pontos()
        time.sleep(1)

    def _resetar_noria(self):
        self.teclado_util.escrever_texto("/move noria")
        time.sleep(2)
        self._move_coordenada_reset()
        mouse_util.left_clique(self.handle, 561, 204)  # CLICA NO NPC RESET

    def _resetar_lorencia(self):
        self.teclado_util.escrever_texto("/move lorencia")
        time.sleep(2)
        self._move_coordenada_reset()
        mouse_util.left_clique(self.handle, 236, 216)  # CLICA NO NPC RESET

    def _resetar_lorencia_desafio(self):
        self.teclado_util.escrever_texto("/move lorencia")
        time.sleep(2)
        MoverSpotUtil(self.handle).movimentar_lorencia((103, 127))
        MoverSpotUtil(self.handle).movimentar_lorencia((91, 127))
        self._move_coordenada_reset(desafio=True)
        mouse_util.left_clique(self.handle, 396, 160)  # CLICA NO NPC RESET

    def _move_coordenada_reset(self, desafio=False):
        pointer = Pointers(self.handle)
        while True:
            if desafio:
                y_coord_reset = 77
                x_coord_reset = 149
                MoverSpotUtil(self.handle).movimentar_lorencia((y_coord_reset, x_coord_reset))
            elif self.classe == 'EF':
                y_coord_reset = 187
                x_coord_reset = 124
                MoverSpotUtil(self.handle).movimentar_noria((y_coord_reset, x_coord_reset))
            else:
                y_coord_reset = 124
                x_coord_reset = 125
                MoverSpotUtil(self.handle).movimentar_lorencia((y_coord_reset, x_coord_reset))

            time.sleep(.5)
            if y_coord_reset == pointer.get_cood_y() and x_coord_reset == pointer.get_cood_x():
                break

    def selecionar_char_no_launcher(self):
        selecionar_char = SelecionarCharUtil(self.handle, self.conexao_arduino)
        while True:
            selecionar_char.selecionar_char_no_launcher()
            if safe_util.lorencia(self.handle) or safe_util.noria(self.handle):
                break
            else:
                print('Char não está na safe de lorencia/noria!')

    def _destribuir_pontos(self):

        if self.char_nome == 'DL_DoMall':
            self.teclado_util.escrever_texto("/f 16974")
            self.teclado_util.escrever_texto("/a 11980")
            self.teclado_util.escrever_texto("/v 5000")
            self.teclado_util.escrever_texto("/e 32485")
        elif self.char_nome == 'TOROUVC':
            self.teclado_util.escrever_texto("/f 1000")
            self.teclado_util.escrever_texto("/a 26000")
            self.teclado_util.escrever_texto("/v 1000")
            self.teclado_util.escrever_texto("/e 32474")
        elif self.char_nome == 'Layna_':
            self.teclado_util.escrever_texto("/f 2478")
            self.teclado_util.escrever_texto("/a 20000")
            self.teclado_util.escrever_texto("/v 3000")
            self.teclado_util.escrever_texto("/e 32485")
        elif self.char_nome == 'ReiDav1':
            self.teclado_util.escrever_texto("/f 500")
            self.teclado_util.escrever_texto("/a 12000")
            self.teclado_util.escrever_texto("/v 500")
            self.teclado_util.escrever_texto("/e 20000")

        elif self.pointer.get_nome_char() == 'NC_elf':
            self.teclado_util.escrever_texto("/f 2000")
            self.teclado_util.escrever_texto("/a 20000")
            self.teclado_util.escrever_texto("/v 500")
            self.teclado_util.escrever_texto("/e 32485")
