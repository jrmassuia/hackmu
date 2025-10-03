import time

import win32gui

from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from interface_adapters.up.use_case import (
    reset_use_case,
    up_aida_use_case_novo,
    up_atlans_use_case,
    up_icarus_use_case,
    up_land_use_case,
    up_lorencia_use_case,
    up_tk_use_case, up_noria_use_case, up_k3_use_case, up_k2_use_case, up_k6_use_case, up_k7_use_case
)
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class UpController:

    def __init__(self, handle, conexao_arduino):
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.pointer = Pointers(handle)
        self.up_util = Up_util(self.handle, pointer=self.pointer, conexao_arduino=conexao_arduino)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.tela = win32gui.GetWindowText(handle)
        self.teclado_util = Teclado_util(self.handle, conexao_arduino)
        self.conexao_arduino = conexao_arduino
        self.eh_char_noob = None
        self.lvl_reset = None
        self.casos_uso = None
        self.land_com_spot_vazio = None
        self.pode_upar_aida = None
        self.pode_upar_k2 = None
        self.pode_upar_k3 = None
        self.pode_upar_kalima6 = None
        self.pode_upar_kalima7 = None
        self.up_em_land_liberado = None
        self.acc_free = None

    def execute(self):

        self.casos_uso = self._inicializar_use_cases()
        self.eh_char_noob = self.pointer.get_reset() <= 30
        self._enviar_comandos_iniciais()

        self.land_com_spot_vazio = True
        self.pode_upar_aida = True
        self.pode_upar_k2 = False
        self.pode_upar_k3 = False
        self.pode_upar_kalima6 = True
        self.pode_upar_kalima7 = True

        if self.pointer.get_nome_char() == 'Layna_':
            self.up_em_land_liberado = False
            self.acc_free = False
        elif self.pointer.get_nome_char() == 'DL_DoMall':
            self.up_em_land_liberado = False
            self.acc_free = False
        else:
            self.up_em_land_liberado = False
            self.acc_free = True

        self._set_lvl_reset()

        if self.up_em_land_liberado:
            self._delay_por_tela()

        self.up_util.ativar_desc_item_spot()

        inicio = 30
        while True:
            if time.time() - inicio >= 30:
                time.sleep(0.5)
                self.up_util.ativar_up()
            else:
                inicio = time.time()

            lvl = self.pointer.get_lvl()
            if lvl is not None:

                if lvl == 400:
                    if (self.pointer.get_reset() >= 250 and self.pointer.get_zen() <= 220000000) or \
                            (self.pointer.get_reset() < 250 and self.pointer.get_zen() <= 70000000):
                        lvl = 399

                if self.eh_char_noob:
                    self._rotina_noob(lvl)
                else:
                    self._rotina_padrao(lvl)

    def _delay_por_tela(self):
        delays = {'[2/': 60, '[3/': 120}
        for texto_tela, delay in delays.items():
            if texto_tela in self.tela:
                print(f'Esperando {delay}s - {self.tela}')
                time.sleep(delay)
                break

    def _rotina_noob(self, lvl):
        if self._lvl_inicial(lvl):
            self._executar_inicio(lvl)
        elif self._lvl_para_atlans(lvl):
            self._executar_atlans()
        elif lvl < self.lvl_reset:
            self._executar_icarus()
        elif self._lvl_para_reset(lvl):
            self._executar_reset()

    def _rotina_padrao(self, lvl):
        regras = [
            (self._lvl_inicial, lambda: self._executar_inicio(lvl)),
            (self._lvl_para_atlans, self._executar_atlans),
            (self._lvl_para_tarkan, self._executar_tarkan),
            (self._lvl_para_land, self._rotina_land),
            (self._lvl_para_kalima6, self._rotina_kalima6),
            # (self._lvl_para_k2, self._rotina_k2),
            # (self._lvl_para_kalima7, self._rotina_kalima7),
            (self._lvl_para_aida, self._rotina_aida),
            (self._lvl_para_reset, self._executar_reset)
        ]

        for regra, acao in regras:
            if regra(lvl):
                acao()
                break

    def _rotina_land(self):
        self.land_com_spot_vazio = self._executar_land()
        if not self.land_com_spot_vazio:
            self.teclado_util.escrever_texto('/move lorencia')
            time.sleep(2)
            self._enviar_comandos_iniciais()
            self.casos_uso['tarkan'].ja_moveu_para_tarkan = False

    def _rotina_kalima6(self):
        self.pode_upar_kalima6 = self._executar_kalima6()
        if not self.pode_upar_kalima6 and self.casos_uso['kalima6'].up_liberado:
            self.casos_uso['aida'].ja_moveu_para_aida = False

    def _rotina_kalima7(self):
        self.pode_upar_kalima7 = self._executar_kalima7()
        if not self.pode_upar_kalima7:
            self.casos_uso['aida'].ja_moveu_para_aida = False

    def _rotina_k2(self):
        self.pode_upar_k2 = self._executar_k2()

    def _rotina_aida(self):
        self.pode_upar_aida = self._executar_aida()

    def _lvl_inicial(self, lvl):
        return lvl < 70

    def _lvl_para_atlans(self, lvl):
        return 70 <= lvl < 140

    def _lvl_para_tarkan(self, lvl):
        return ((self.up_em_land_liberado and self.land_com_spot_vazio and lvl < 200) or (
                self.up_em_land_liberado and not self.land_com_spot_vazio and lvl < 230)) or (
                not self.up_em_land_liberado and lvl < 250)

    def _lvl_para_land(self, lvl):
        return self.up_em_land_liberado and self.land_com_spot_vazio and lvl < self.lvl_reset

    def _lvl_para_k2(self, lvl):
        return self.pode_upar_k2 and lvl < self.lvl_reset

    def _lvl_para_k3(self, lvl):
        return self.pode_upar_k3 and lvl < self.lvl_reset

    def _lvl_para_kalima6(self, lvl):
        return self.pode_upar_kalima6 and lvl >= 331 and self.pointer.get_reset() >= 120 and lvl < self.lvl_reset

    def _lvl_para_kalima7(self, lvl):
        return self.pode_upar_kalima6 is False and self.pode_upar_kalima7 and lvl >= 350 and \
            self.pointer.get_reset() >= 120 and lvl < self.lvl_reset

    def _lvl_para_aida(self, lvl):
        nao_upa_em_kanturu = not self.pode_upar_k2 and not self.pode_upar_k3
        return nao_upa_em_kanturu and self.pode_upar_aida and lvl < self.lvl_reset

    def _lvl_para_reset(self, lvl):
        return lvl >= self.lvl_reset

    def _executar_inicio(self, lvl):
        if self.classe == 'EF':
            self.casos_uso['noria'].executar()
        else:
            self.casos_uso['lorencia'].executar()

    def _executar_atlans(self):
        return self.casos_uso['atlans'].executar()

    def _executar_icarus(self):
        return self.casos_uso['icarus'].executar()

    def _executar_tarkan(self):
        return self.casos_uso['tarkan'].executar()

    def _executar_land(self):
        return self.casos_uso['land'].executar()

    def _executar_aida(self):
        pode_upar = self.casos_uso['aida'].executar()
        return pode_upar

    def _executar_k2(self):
        pode_upar = self.casos_uso['k2'].executar()
        return pode_upar

    def _executar_k3(self):
        pode_upar = self.casos_uso['k3'].executar()
        return pode_upar

    def _executar_kalima6(self):
        pode_upar = self.casos_uso['kalima6'].executar()
        return pode_upar

    def _executar_kalima7(self):
        pode_upar = self.casos_uso['kalima7'].executar()
        return pode_upar

    def _executar_reset(self):
        self.casos_uso['reset'].executar()
        self.execute()

    def _inicializar_use_cases(self):
        return {
            'lorencia': up_lorencia_use_case.UpLorenciaUseCase(self.handle, self.eh_char_noob, self.conexao_arduino),
            'noria': up_noria_use_case.UpNoriasUseCase(self.handle, self.conexao_arduino),
            'atlans': up_atlans_use_case.UpAtlansUseCase(self.handle, self.conexao_arduino),
            'tarkan': up_tk_use_case.UpTarkanUseCase(self.handle, self.conexao_arduino),
            'icarus': up_icarus_use_case.UpIcarusUseCase(self.handle, self.conexao_arduino),
            'land': up_land_use_case.UpLandUseCase(self.handle, self.conexao_arduino),
            'k2': up_k2_use_case.UpK2UseCase(self.handle, self.conexao_arduino),
            'k3': up_k3_use_case.UpK3UseCase(self.handle, self.conexao_arduino),
            'aida': up_aida_use_case_novo.UpAidaUseCaseNovo(self.handle, self.conexao_arduino),
            'kalima6': up_k6_use_case.UpK6UseCase(self.handle, self.conexao_arduino),
            'kalima7': up_k7_use_case.UpK7UseCase(self.handle, self.conexao_arduino),
            'reset': reset_use_case.ResetUseCase(self.handle, self.conexao_arduino, self.pointer.get_nome_char(),
                                                 self.pointer.get_reset())
        }

    def _enviar_comandos_iniciais(self):
        self.teclado_util.selecionar_skill_1()
        self.up_util.enviar_comandos_iniciais()

    def _set_lvl_reset(self):
        if self.acc_free:
            self._set_lvl_reset_free()
        else:
            self._set_lvl_reset_vip()

    def _set_lvl_reset_vip(self):
        if self.pointer.get_reset() < 15:
            self.lvl_reset = 300
        elif self.pointer.get_reset() < 30:
            self.lvl_reset = 325
        elif self.pointer.get_reset() < 50:
            self.lvl_reset = 350
        elif self.pointer.get_reset() < 140:
            self.lvl_reset = 375
        else:
            self.lvl_reset = 400

    def _set_lvl_reset_free(self):
        if self.pointer.get_reset() < 10:
            self.lvl_reset = 300
        elif self.pointer.get_reset() < 20:
            self.lvl_reset = 325
        elif self.pointer.get_reset() < 35:
            self.lvl_reset = 350
        elif self.pointer.get_reset() < 80:
            self.lvl_reset = 375
        else:
            self.lvl_reset = 400
