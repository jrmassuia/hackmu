import time
from typing import Sequence, Callable, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import spot_util, safe_util, mouse_util


class PkAidaUseCase(PkBase):
    """
    Implementação de PK para Aida.
    - Mantive o nome da classe e o método execute (loop padrão).
    - Variáveis e métodos em Português, docstrings explicativas.
    - Preserva a lógica original: seleção por nome, sequência de spots por tipo, saída de safe e correções.
    """

    PKLIZAR_AIDA_1 = 'AIDA_1'
    PKLIZAR_AIDA_2 = 'AIDA_2'
    PKLIZAR_AIDA_CORREDOR = 'AIDA_CORREDOR'
    PKLIZAR_AIDA_FINAL = 'AIDA_FINAL'

    def _definir_tipo_pk_e_senha(self) -> str:
        nome = self.pointer.get_nome_char()

        # AIDA 1
        if nome == '_Offensive':
            senha = 'kuChx98f'
            self.tipo_pk = self.PKLIZAR_AIDA_1
        elif nome == 'Omale_DL':
            senha = 'gtkn6iVy'
            self.tipo_pk = self.PKLIZAR_AIDA_1

        # AIDA 2
        elif nome == 'LAZLU':
            senha = 'bebe133171'
            self.tipo_pk = self.PKLIZAR_AIDA_2
        elif nome == 'Heisemberg':
            senha = '93148273'
            self.tipo_pk = self.PKLIZAR_AIDA_2
        elif nome == 'AlfaVictor':
            senha = 'thiago123'
            self.tipo_pk = self.PKLIZAR_AIDA_2
        elif nome == 'INFECTRIX':
            senha = '9876Sonso'
            self.tipo_pk = self.PKLIZAR_AIDA_2
        elif nome == 'ESTAMUERTO':
            senha = '93148273'
            self.tipo_pk = self.PKLIZAR_AIDA_2

        # AIDA CORREDOR
        elif nome == 'SisteMatyc':
            senha = 'carenae811'
            self.tipo_pk = self.PKLIZAR_AIDA_CORREDOR
        elif nome == 'SM_Troyer':
            senha = 'romualdo12'
            self.tipo_pk = self.PKLIZAR_AIDA_CORREDOR

        # AIDA FINAL
        elif nome == 'DL_JirayA':
            senha = '134779'
            self.tipo_pk = self.PKLIZAR_AIDA_FINAL
        elif nome == 'ReiDav1':
            senha = 'romualdo12'
            self.tipo_pk = self.PKLIZAR_AIDA_FINAL
        else:
            print('Tela sem configuração definida! ' + self.titulo_janela)
            senha = ''

        return senha

    def iniciar_pk(self):
        self.morreu = False
        self.mover_para_sala(self.sala_pk)
        self.teclado.escrever_texto('/re off')
        self._sair_da_safe()

        if not self.morreu:
            self._ativar_skill()

            if self.tipo_pk == self.PKLIZAR_AIDA_1:
                self.pklizar_aida1()
            elif self.tipo_pk == self.PKLIZAR_AIDA_2:
                self.pklizar_aida2()
            elif self.tipo_pk == self.PKLIZAR_AIDA_CORREDOR:
                self.pklizar_aida_corredor()
            elif self.tipo_pk == self.PKLIZAR_AIDA_FINAL:
                self.pklizar_aida_final()
            else:
                self.pklizar_aida2()

        if not self.morreu:
            print('Relizada a rota completa de PK: ' + self.titulo_janela)

    def pklizar_aida(self):
        etapas: Sequence[Callable[[], List]] = (
            lambda: spot_util.buscar_spots_aida_1(ignorar_spot_pk=True),
            self.buscar_spot_extra_aida1,
            self.buscar_spot_aida2,
            spot_util.buscar_spots_aida_corredor,
            spot_util.buscar_spots_aida_final,
        )
        return self.executar_rota_pk(etapas)

    def pklizar_aida1(self):
        etapas: Sequence[Callable[[], List]] = (
            lambda: spot_util.buscar_spots_aida_1(ignorar_spot_pk=True),
            self.buscar_spot_extra_aida1,
            spot_util.buscar_spots_aida_corredor,
            self.buscar_spot_aida2,
            spot_util.buscar_spots_aida_final
        )
        return self.executar_rota_pk(etapas)

    def pklizar_aida2(self):
        etapas: Sequence[Callable[[], List]] = (
            self.buscar_spot_aida2,
            spot_util.buscar_spots_aida_corredor,
            spot_util.buscar_spots_aida_final,
            
            self.buscar_spot_extra_aida1,
        )
        return self.executar_rota_pk(etapas)

    def pklizar_aida_corredor(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_aida_corredor,
            self.buscar_spot_extra_aida1,
            lambda: spot_util.buscar_spots_aida_1(ignorar_spot_pk=True),
            self.buscar_spot_aida2,
            spot_util.buscar_spots_aida_final,
        )
        return self.executar_rota_pk(etapas)

    def pklizar_aida_final(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_aida_final,
            spot_util.buscar_spots_aida_corredor,
            self.buscar_spot_extra_aida1,
            self.buscar_spot_aida2,
        )
        return self.executar_rota_pk(etapas)

    def buscar_spot_extra_aida1(self) -> List:
        spots = spot_util.buscar_spots_aida_1()
        inicio = max(0, len(spots) - 3)
        return [spots[i] for i in range(inicio, len(spots))]

    def buscar_spot_aida2(self) -> List:
        spots = spot_util.buscar_spots_aida_volta_final(ignorar_spot_pk=True)
        spots.extend(spot_util.buscar_spots_aida_2(ignorar_spot_pk=True))
        return spots

    def _sair_da_safe(self):
        if safe_util.aida(self.handle):
            self._desbugar_goblin()
            saiu = self.mover_spot.movimentar(
                (115, 13),
                max_tempo=60,
                movimentacao_proxima=True
            )
            if saiu is False:
                self.morreu = True

    def _desbugar_goblin(self):
        btn_fechar = self.buscar_imagem.buscar_item_simples('./static/img/fechar_painel.png')
        if btn_fechar:
            x, y = btn_fechar
            mouse_util.left_clique(self.handle, x, y)
            time.sleep(1)
            # clique extra em posição conhecida (fallback)
            mouse_util.left_clique(self.handle, 38, 369)


    def _esta_na_safe(self) -> bool:
        return safe_util.aida(self.handle)
