import time
from typing import Callable, Sequence, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import safe_util, spot_util, mouse_util, limpar_mob_ao_redor_util


class PktarkanUseCase(PkBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, loop=True):
        """
        Execute pode rodar em ciclo contínuo (loop=True) ou uma vez (loop=False).
        """

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
        # sem senha por padrão
        self.tipo_pk = 'TARKAN'
        return ''

    def iniciar_pk(self):
        self.esperar_se_morreu()
        self.atualizar_lista_player()
        self._sair_da_safe()
        self._ativar_skill()
        self.pklizar_tarkan()

    def _sair_da_safe(self):
        if safe_util.tk(self.pointer.get_coordernada_y_x()):
            saiu_safe = self.mover_spot.movimentar((205, 100), movimentacao_proxima=True)
            if not saiu_safe:
                self.morreu = True

    def pklizar_tarkan(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_tk1,
            lambda: spot_util.buscar_spots_tk2(nao_ignorar_spot_pk=True),
        )
        self.executar_rota_pk(etapas)

    def esperar_se_morreu(self):
        if self.morreu:
            print('Morreu em Tarkan — aguardando 600s')
            self.morreu = False
            time.sleep(600)
    def _mover_para_k1(self):
        """
        Tenta subir para k1: movimenta, limpa mobs ao redor e verifica safe.
        """
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
