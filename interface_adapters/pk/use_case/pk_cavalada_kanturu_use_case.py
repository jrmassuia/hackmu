import time
from typing import Sequence, Callable, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import mouse_util, safe_util, spot_util, limpar_mob_ao_redor_util


class PkCavaladaKanturuUseCase(PkBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _definir_tipo_pk_e_senha(self) -> str:
        self.tipo_pk = 'KANTURU_1_2'
        return ''

    def execute(self):
        while True:
            self.atualizar_lista_player()
            self.iniciar_pk()

    def iniciar_pk(self):
        self.morreu = False
        self._sair_da_safe()
        if not self.morreu:
            self._ativar_skill()
            self.cavalar_kanturus()
        self.esperar_se_morreu()

    def _sair_da_safe(self):
        if safe_util.k1(self.pointer.get_coordernada_y_x()):
            saiu_safe = self.mover_spot.movimentar((49, 230), movimentacao_proxima=True)
            if not saiu_safe:
                self.morreu = True

    def cavalar_kanturus(self):
        etapas: Sequence[Callable[[], List]] = (
            self.buscar_spots_k1,
            spot_util.buscar_spots_k2,
        )
        self.executar_rota_pk(etapas)

    def buscar_spots_k1(self):
        spots = spot_util.buscar_spots_k1()
        return spots[6:]

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

    def _mover_para_k1(self):
        if safe_util.tk(self.pointer.get_coordernada_y_x()) or self.morreu:
            return

        while True:
            movimentou = self.mover_spot.movimentar(
                (12, 200),
                verficar_se_movimentou=True,
                movimentacao_proxima=True,
                max_tempo=240
            )

            if movimentou:
                limpar_mob_ao_redor_util.limpar_mob_ao_redor(self.handle)
                movimentou = self.mover_spot.movimentar((12, 200), verficar_se_movimentou=True, max_tempo=240)

            if movimentou:
                mouse_util.left_clique(self.handle, 158, 139)
                time.sleep(5)

            if safe_util.k1(self.pointer.get_coordernada_y_x()):
                break

    def verificar_se_pode_continuar_com_pk(self):
        return True

    def _esta_na_safe(self):
        return safe_util.tk(self.pointer.get_coordernada_y_x())

    def limpar_mob_ao_redor(self):
        pass

    def _ativar_skill(self):
        self.teclado.selecionar_skill_1()
