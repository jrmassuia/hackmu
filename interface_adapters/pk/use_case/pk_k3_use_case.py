import time

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import safe_util, spot_util, mouse_util
from typing import Callable, Sequence, List


class PkK3UseCase(PkBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._morreu = False
        self.iniciou_pk = False

    def execute(self):
        while True:
            self.iniciar_pk()

    def _definir_tipo_pk_e_senha(self) -> str:
        return ''

    def morreu(self) -> bool:
        return False

    def iniciar_pk(self):
        self.morreu = False
        self._sair_da_safe()
        if not self.morreu:
            self._ativar_skill()
            self.pklizar_k3()
        self.voltar_pra_safe_e_esperar_proximo_pk()
        self.esperar_safe_se_necessario()

    def _sair_da_safe(self):
        if safe_util.k3(self.handle):
            saiu_safe = self.mover_spot_util.movimentar_kanturu_3((94, 92), max_tempo=15, movimentacao_proxima=True)
            if not saiu_safe:
                self.morreu = True

    def pklizar_k3(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_k3,
        )
        self.executar_rota_pk(etapas)

    def esperar_safe_se_necessario(self):
        if self.morreu:
            print('Morreu k3 esperando na safe!')
            time.sleep(600)

    def voltar_pra_safe_e_esperar_proximo_pk(self):
        if not self.morreu:
            self.mover_spot_util.movimentar_kanturu_3((88, 105), verficar_se_movimentou=True, movimentacao_proxima=True)
            print('ESPERANDO 300s PARA PROXIMO PK EM K3')
            time.sleep(300)

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar_kanturu_3(
                self.coord_spot_atual,
                verficar_se_movimentou=True
            )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _movimentar_char_spot(self, coordenadas):
        return self.mover_spot_util.movimentar_kanturu_3(
            coordenadas,
            max_tempo=600,
            verficar_se_movimentou=True,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True
        )

    def _posicionar_char_pklizar(self, x, y):
        return self.mover_spot_util.movimentar_kanturu_3(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )

    def pk_pode_continuar(self):
        return True
