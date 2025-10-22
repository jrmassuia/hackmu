import time
from typing import Sequence, Callable, List, Optional

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

    # ---------- Definição de senha/tipo ----------
    def _definir_tipo_pk_e_senha(self) -> str:
        """
        Define self.tipo_pk e retorna a senha correspondente ao personagem (se houver).
        """
        nome = self.pointer.get_nome_char()
        senha = ''

        # AIDA 1
        if nome == 'AlfaVictor':
            senha = 'thiago123'
            self.tipo_pk = self.PKLIZAR_AIDA_1
        elif nome == 'ReiDav1':
            senha = 'romualdo12'
            self.tipo_pk = self.PKLIZAR_AIDA_1

        # AIDA 2
        elif nome == 'LAZLU':
            senha = 'bebe133171'
            self.tipo_pk = self.PKLIZAR_AIDA_2
        elif nome == 'DL_JirayA':
            senha = '134779'
            self.tipo_pk = self.PKLIZAR_AIDA_2
        elif nome == 'Omale_DL':
            senha = 'gtkn6iVy'
            self.tipo_pk = self.PKLIZAR_AIDA_2

        # AIDA CORREDOR
        elif nome == 'SM_Troyer':
            senha = 'romualdo12'
            self.tipo_pk = self.PKLIZAR_AIDA_CORREDOR
        elif nome == 'SisteMatyc':
            senha = 'carenae811'
            self.tipo_pk = self.PKLIZAR_AIDA_CORREDOR

        # AIDA FINAL
        elif nome == '_Offensive':
            senha = 'kuChx98f'
            self.tipo_pk = self.PKLIZAR_AIDA_FINAL
        elif nome == 'INFECTRIX':
            senha = '9876Sonso'
            self.tipo_pk = self.PKLIZAR_AIDA_FINAL
        else:
            # padrão
            print('Tela sem configuração definida! ' + self.titulo_janela)
            exit()

        return senha

    # ---------- Entrada do fluxo ----------
    def execute(self):
        """
        Loop principal para Aida — mantém o comportamento de execução contínua.
        """
        while True:
            self.iniciar_pk()

    def iniciar_pk(self):
        """
        Fluxo principal de PK para Aida:
        - assegura sala 7, desliga /re, sai da safe, ativa skill e executa a sequência
          correspondente ao tipo de Aida definido.
        """
        salas = [7, 3, 8, 9]
        for sala in salas:
            self.mover_para_sala(sala)
            self.teclado.escrever_texto('/re off')
            self._sair_da_safe()

            if not self.morreu:
                self._ativar_skill()

                if sala != 7:
                    self.pklizar_aida()
                elif self.tipo_pk == self.PKLIZAR_AIDA_1:
                    self.pklizar_aida1()
                elif self.tipo_pk == self.PKLIZAR_AIDA_2:
                    self.pklizar_aida2()
                elif self.tipo_pk == self.PKLIZAR_AIDA_CORREDOR:
                    self.pklizar_aida_corredor()
                elif self.tipo_pk == self.PKLIZAR_AIDA_FINAL:
                    self.pklizar_aida_final()
                else:
                    self.pklizar_aida1()
            else:
                break

    # ---------- Sequências específicas ----------
    def pklizar_aida(self):
        etapas: Sequence[Callable[[], List]] = (
            # lambda: spot_util.buscar_spots_aida_1(ignorar_spot_pk=True),
            # self.buscar_spot_extra_aida1,
            # self.buscar_spot_aida2,
            # spot_util.buscar_spots_aida_corredor,
            # spot_util.buscar_spots_aida_final,
        )
        self.executar_rota_pk(etapas)

    def pklizar_aida1(self):
        etapas: Sequence[Callable[[], List]] = (
            lambda: spot_util.buscar_spots_aida_1(ignorar_spot_pk=True),
            self.buscar_spot_extra_aida1,
            spot_util.buscar_spots_aida_corredor,
            self.buscar_spot_aida2,
        )
        self.executar_rota_pk(etapas)

    def pklizar_aida2(self):
        etapas: Sequence[Callable[[], List]] = (
            self.buscar_spot_aida2,
            spot_util.buscar_spots_aida_corredor,
            spot_util.buscar_spots_aida_final,
            self.buscar_spot_extra_aida1,
        )
        self.executar_rota_pk(etapas)

    def pklizar_aida_corredor(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_aida_corredor,
            self.buscar_spot_extra_aida1,
            lambda: spot_util.buscar_spots_aida_1(ignorar_spot_pk=True),
            self.buscar_spot_aida2,
            spot_util.buscar_spots_aida_final,
        )
        self.executar_rota_pk(etapas)

    def pklizar_aida_final(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_aida_final,
            spot_util.buscar_spots_aida_corredor,
            self.buscar_spot_extra_aida1,
            self.buscar_spot_aida2,
        )
        self.executar_rota_pk(etapas)

    # ---------- helpers de busca de spots ----------
    def buscar_spot_extra_aida1(self) -> List:
        """
        Retorna os 3 últimos grupos de spots da lista de Aida_1 (caso existam).
        """
        spots = spot_util.buscar_spots_aida_1()
        inicio = max(0, len(spots) - 3)
        return [spots[i] for i in range(inicio, len(spots))]

    def buscar_spot_aida2(self) -> List:
        """
        Combina spots de volta final + spots de Aida 2 e retorna a lista concatenada.
        """
        spots = spot_util.buscar_spots_aida_volta_final(ignorar_spot_pk=True)
        spots.extend(spot_util.buscar_spots_aida_2(ignorar_spot_pk=True))
        return spots

    # ---------- saída da safe e correções ----------
    def _sair_da_safe(self):
        """
        Se estiver na safe de Aida, tenta sair movendo para coordenada conhecida.
        Inclui um passo para "desbugar" painéis que possam atrapalhar.
        """
        if safe_util.aida(self.handle):
            self._desbugar_goblin()
            saiu = self.mover_spot.movimentar_aida(
                (104, 8),
                max_tempo=5,
                movimentacao_proxima=True
            )
            if not saiu:
                self.morreu = True

    def _desbugar_goblin(self):
        """
        Fecha painéis abertos (se houver) para evitar bloqueios ao sair da safe.
        """
        btn_fechar = self.buscar_imagem.buscar_item_simples('./static/img/fechar_painel.png')
        if btn_fechar:
            x, y = btn_fechar
            mouse_util.left_clique(self.handle, x, y)
            time.sleep(1)
            # clique extra em posição conhecida (fallback)
            mouse_util.left_clique(self.handle, 38, 369)

    # ---------- correção de coordenadas / movimentação ----------
    def _corrigir_coordenada_e_mouse(self):
        """
        Se o código já tinha um spot/mouse salvo, tenta reposicionar para reduzir erros.
        """
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot.movimentar_aida(
                self.coord_spot_atual,
                verficar_se_movimentou=True
            )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _movimentar_char_spot(self, coordenadas):
        """
        Move o personagem até o spot informado usando mover_spot.movimentar_aida com parâmetros
        que refletem o comportamento original (timeout longo, limpeza de spot se necessário).
        """
        return self.mover_spot.movimentar_aida(
            coordenadas,
            max_tempo=600,
            verficar_se_movimentou=True,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True
        )

    def _posicionar_char_pklizar(self, x: int, y: int) -> bool:
        """
        Posiciona o personagem para "pklizar" um alvo nas coordenadas (x,y).
        Note a inversão (y,x) quando o mover espera (linha, coluna).
        """
        return self.mover_spot.movimentar_aida(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )

    def _esta_na_safe(self) -> bool:
        """
        Retorna True se o personagem estiver na safe da Aida.
        """
        return safe_util.aida(self.handle)
