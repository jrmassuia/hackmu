import time
from typing import Sequence, Callable, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import safe_util, spot_util, mouse_util


class PkK3UseCase(PkBase):
    """
    Implementação de PK para K3 (Kalima 3 / Kanturu 3).
    Mantém o nome da classe e execute() conforme pedido.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.morreu = False
        self.iniciou_pk = False

    def execute(self):
        while True:
            self.atualizar_lista_player()
            self.iniciar_pk()

    def _definir_tipo_pk_e_senha(self) -> str:
        self.tipo_pk = 'K3'
        return ''

    def iniciar_pk(self):
        self.morreu = False
        self._sair_da_safe()
        if not self.morreu:
            self._ativar_skill()
            self.pklizar_k3()
        self.voltar_para_safe_e_esperar()
        self.esperar_se_morreu()

    def _sair_da_safe(self):
        if safe_util.k3(self.handle):
            saiu = self.mover_spot.movimentar((109, 79), max_tempo=20, movimentacao_proxima=True)
            if not saiu:
                self.morreu = True

    def pklizar_k3(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_k3,
        )
        return self.executar_rota_pk(etapas)

    def esperar_se_morreu(self):
        if self.morreu:
            print('Morreu em K3 — aguardando 900s')
            time.sleep(900)

    def voltar_para_safe_e_esperar(self):
        if not self.morreu:
            self.mover_spot.movimentar((88, 105), verficar_se_movimentou=True, movimentacao_proxima=True)
            print('Esperando 600s para próximo PK em K3')
            time.sleep(600)

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot.movimentar(
                self.coord_spot_atual,
                verficar_se_movimentou=True
            )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _movimentar_char_spot(self, coordenadas):
        return self.mover_spot.movimentar(
            coordenadas,
            max_tempo=600,
            verficar_se_movimentou=True,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True
        )

    def _posicionar_char_pklizar(self, x, y):
        # observe que o mover_kanturu_3 espera (linha,coluna) diferente do x,y
        return self.mover_spot.movimentar(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )

    def verificar_se_pode_continuar_com_pk(self):
        return True

    def _esta_na_safe(self):
        return safe_util.k3(self.handle)
