import time
from typing import Sequence, Callable, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import safe_util, spot_util


class PkKanturuUseCase(PkBase):

    def execute(self):
        self.iniciar_pk()

    def iniciar_pk(self):
        self._esperar_safe_se_necessario()
        self.atualizar_lista_player()
        self._sair_da_safe()
        self._ativar_skill()
        self._pklizar_kanturu()
        self.voltar_pra_safe_e_esperar_proximo_pk()

    def _pklizar_kanturu(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_k1,
            spot_util.buscar_spots_k2,
        )
        self.executar_rota_pk(etapas)

    def _esperar_safe_se_necessario(self):
        if self.morreu:
            print('Morreu no KNV. Aguardando na safe…')
            self.morreu = False
            time.sleep(600)

    def _sair_da_safe(self):
        if safe_util.k1(self.handle):
            self.mover_spot.movimentar((46, 222), movimentacao_proxima=True)

    def voltar_pra_safe_e_esperar_proximo_pk(self):
        if not self.morreu:
            voltou = self.mover_spot.movimentar(
                (40, 214),
                verficar_se_movimentou=True,
                movimentacao_proxima=True,
                max_tempo=360
            )
            if voltou:
                print('ESPERANDO 600s PARA PROXIMO PK EM KNV')
                time.sleep(600)
        else:
            time.sleep(8)  # DELAY PARA CASO MORRA E VOLTAR PARA SAFE

    def morreu(self) -> bool:
        return safe_util.k1(self.handle)

    def _esta_na_safe(self):
        return safe_util.k1(self.handle) or safe_util.tk(self.handle)

    def _definir_tipo_pk_e_senha(self) -> str:
        return ''

    def verificar_se_pode_continuar_com_pk(self) -> bool:
        return True
