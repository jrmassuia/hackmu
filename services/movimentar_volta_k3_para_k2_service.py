import time

from services.alterar_char_sala_service import AlterarCharSalaService
from utils import mouse_util, safe_util


class MovimentacaoVotaK3ParaK2Service:
    def __init__(self, handle, mover_spot_util, arduino, senha):
        self.handle = handle
        self.mover_spot_util = mover_spot_util
        self.arduino = arduino
        self.senha = senha
        self.iniciou_up = False

    def mover_para_k3(self):

        if safe_util.tk(self.handle):
            while True:
                self.mover_spot_util.movimentar((157, 58))
                movimentou = self.mover_spot_util.movimentar((8, 199), verficar_se_movimentou=True,
                                                                    limpar_spot_se_necessario=True,
                                                                    max_tempo=240)
                if movimentou:
                    mouse_util.left_clique(self.handle, 281, 207)
                    break

        self._selicionar_sala()

        if not self._mover_ate_porta_k3():
            return self.mover_para_k3()

        mouse_util.left_clique(self.handle, 490, 338, delay=3)

        self._selicionar_sala(sala=7)

        mouse_util.left_clique(self.handle, 310, 152, delay=1)

        self._movimentar_dentro_k3()

    def _mover_ate_porta_k3(self):
        self.mover_spot_util.movimentar((48, 227), movimentacao_proxima=True)
        return self.mover_spot_util.movimentar(
            (82, 91),
            verficar_se_movimentou=True,
            limpar_spot_se_necessario=True,
            max_tempo=300,
            movimentacao_proxima=True
        )

    def _movimentar_dentro_k3(self):
        coordenadas = [((68, 95), (53, 100))]

        for coord in coordenadas:
            movimentou = self.mover_spot_util.movimentar(
                coord,
                verficar_se_movimentou=True,
                movimentacao_proxima=True
            )
            if not movimentou:
                break

    def _selicionar_sala(self, sala=None):
        alterar_sala = AlterarCharSalaService(self.handle, self.senha, self.arduino)
        alterar_sala.selecionar_sala(sala)
        self.iniciou_up = True
