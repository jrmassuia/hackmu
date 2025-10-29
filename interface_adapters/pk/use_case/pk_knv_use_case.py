import time
from typing import Callable, Sequence, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import safe_util, spot_util, mouse_util


class PkKnvUseCase(PkBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, loop=True):

        def ciclo_knv_tk():
            self.iniciar_pk()
            self._mover_para_tk()

        def ciclo_tk():
            self.iniciar_pk()

        if not loop:
            ciclo_knv_tk()
            return

        while True:
            ciclo_tk()

    def iniciar_pk(self):
        self._esperar_safe_se_necessario()
        self._sair_da_safe()
        self._ativar_skill()
        self._pklizar_knv()
        self.voltar_pra_safe_e_esperar_proximo_pk()

    def _sair_da_safe(self):
        if not safe_util.k1(self.handle):
            self._marcar_morte()
            return

        while True:
            # 1) Sair da safe
            # DESBUGAR MOVIMENTACAO
            self.mover_spot.movimentar_kanturu_1_2((24, 206), max_tempo=5, movimentacao_proxima=True)
            movimentou = self.mover_spot.movimentar_kanturu_1_2((20, 201))
            if not movimentou:
                self.morreu = True
                return
            else:
                time.sleep(.5)
                break

        if self._mover_portal_knv():
            # 2) Entrar em KNV
            saiu_safe = self.mover_spot.movimentar_kanturu_1_2((57, 155), max_tempo=15, movimentacao_proxima=True)
            if not saiu_safe:
                self.morreu = True

    def _mover_portal_knv(self):
        mouse_util.left_clique(self.handle, 433, 44)  # clica no portal knv
        time.sleep(8)

        if not safe_util.knv(self.handle):
            self.morreu = True
            return False
        return True

    def _pklizar_knv(self):
        etapas: Sequence[Callable[[], List]] = (spot_util.buscar_spots_knv,)
        self.executar_rota_pk(etapas)

    def _esperar_safe_se_necessario(self):
        if self.morreu:
            print('Morreu no KNV. Aguardando na safe…')
            self.morreu = False
            time.sleep(600)

    def voltar_pra_safe_e_esperar_proximo_pk(self):
        if not self.morreu:
            voltou = self.mover_spot.movimentar_kanturu_1_2(
                (71, 180),
                verficar_se_movimentou=True,
                movimentacao_proxima=True
            )
            if voltou:
                print('ESPERANDO 600s PARA PROXIMO PK EM KNV')
                time.sleep(600)
        else:
            time.sleep(8)  # DELAY PARA CASO MORRA E VOLTAR PARA SAFE

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot.movimentar_kanturu_1_2(
                self.coord_spot_atual,
                verficar_se_movimentou=True
            )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _movimentar_char_spot(self, coordenadas):
        return self.mover_spot.movimentar_kanturu_1_2(
            coordenadas,
            max_tempo=600,
            verficar_se_movimentou=True,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True
        )

    def _posicionar_char_pklizar(self, x, y):
        return self.mover_spot.movimentar_kanturu_1_2(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )

    def _mover_para_tk(self):
        if safe_util.k1(self.handle):
            mouse_util.left_clique(self.handle, 472, 40)
            time.sleep(5)
            self.mover_spot.movimentar_tarkan((17, 198), verficar_se_movimentou=True,
                                              limpar_spot_se_necessario=True,
                                              movimentacao_proxima=True,
                                              max_tempo=5)

    def _marcar_morte(self):
        self.morreu = True

    def _definir_tipo_pk_e_senha(self) -> str:
        return ''

    def morreu(self) -> bool:
        return self.morreu

    def verificar_se_pode_continuar_com_pk(self) -> bool:
        return True

    def _esta_na_safe(self):
        return safe_util.k1(self.handle)
