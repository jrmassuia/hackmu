import time
from typing import Sequence, Callable, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import mouse_util, safe_util, spot_util, limpar_mob_ao_redor_util


class PkCavaladaKanturuUseCase(PkBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, loop=True):

        def ciclo_tk_knv():
            self.iniciar_pk()
            self._mover_para_k1()

        def ciclo_tk():
            self.iniciar_pk()

        if not loop:
            ciclo_tk_knv()
            return

        while True:
            ciclo_tk()

    def _definir_tipo_pk_e_senha(self) -> str:
        self.tipo_pk = 'KANTURU_1_2'
        return ''

    def iniciar_pk(self):
        self.esperar_se_morreu()
        self.atualizar_lista_player()
        self._sair_da_safe()
        self._ativar_skill()
        self.cavalar_kanturus()

    def _sair_da_safe(self):
        if safe_util.k1(self.handle):
            saiu_safe = self.mover_spot.movimentar((49, 230), movimentacao_proxima=True)
            if not saiu_safe:
                self.morreu = True

    def cavalar_kanturus(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_k2,
        )
        self.executar_rota_pk(etapas)

    def esperar_se_morreu(self):
        if self.morreu:
            print('Morreu em KANTURU — aguardando 120s')
            self.morreu = False
            while True:
                if self.pointer.get_nivel_pk() == 100:
                    time.sleep(60)
                else:
                    time.sleep(120)
                    break

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
        return self.mover_spot.movimentar(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )

    def _mover_para_k1(self):
        if safe_util.tk(self.handle) or self.morreu:
            return

        while True:
            movimentou = self.mover_spot.movimentar(
                (12, 200),
                verficar_se_movimentou=True,
                limpar_spot_se_necessario=True,
                movimentacao_proxima=True,
                max_tempo=240
            )

            if movimentou:
                limpar_mob_ao_redor_util.limpar_mob_ao_redor(self.handle)
                movimentou = self.mover_spot.movimentar((12, 200), verficar_se_movimentou=True, max_tempo=240)

            if movimentou:
                mouse_util.left_clique(self.handle, 158, 139)
                time.sleep(5)

            if safe_util.k1(self.handle):
                break

    def verificar_se_pode_continuar_com_pk(self):
        return True

    def _esta_na_safe(self):
        return safe_util.tk(self.handle)

    def limpar_mob_ao_redor(self):
        pass

    def _ativar_skill(self):
        self.teclado.selecionar_skill_1()
