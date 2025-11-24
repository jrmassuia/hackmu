import time

from interface_adapters.helpers.session_manager_new import *
from interface_adapters.up.up_util.up_util import Up_util
from menu import Menu
from sessao_menu import obter_menu
from utils import mouse_util, screenshot_util
from utils.buscar_item_util import BuscarItemUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class PegarItemUseCase:

    def __init__(self, handle):
        self.handle = handle
        self.up_util = Up_util(self.handle)
        self.pointer = Pointers(handle)
        self.buscar_item = BuscarItemUtil(self.handle)
        self.teclado_util = Teclado_util(self.handle)
        self.classe = self.pointer.get_classe()

    def execute(self):
        self._ativar_up()
        x, y, item = self._buscar_item()
        if self._coordenadas_validas(x, y, item):
            self._processar_item(x, y, item)

    def _ativar_up(self):
        if self.classe == 'DL' or self.classe == 'EF':
            self.up_util.ativar_up()
        else:
            self.up_util.ativar_up_e_centralizar()

    def _coordenadas_validas(self, x, y, item):
        return x is not None and y is not None and item is not None

    def _buscar_item(self):
        x, y, item = self.buscar_item.buscar_item_geral_autopick()
        x, y = self._calibrar(x, y, item)
        return x, y, item

    def _buscar_item_especifico(self, item_especifico):
        if 'gemstone' in item_especifico:
            eh_geno = self.buscar_item.buscar_item_simples('./static/img/genocider.png')
            if eh_geno:
                return None, None, None

        x, y, item = self.buscar_item.buscar_item_especifico_autopick(item_especifico)
        x, y = self._calibrar(x, y, item)
        return x, y, item

    def _processar_item(self, x, y, item):
        time.sleep(0.5)  # Tempo para o item cair no chão
        tentativa = 0
        item_especial = ('gemstone' in item) or ('joia' in item) or ('boxgreen' in item) or ('kalima' in item) or (
                'complex' in item)

        while True:
            if not self._achou_item(item, x, y):
                if not item_especial or tentativa > 1:
                    break
                tentativa += 1
                continue

            if 'zen' in item and self.classe in ['DL', 'EF']:
                self.teclado_util.tap_espaco()
            else:
                mouse_util.left_clique(self.handle, x, y)

            if item_especial:
                novo_x, novo_y, novo_item = self._buscar_item_especifico(item)
                if novo_x and novo_y:
                    x, y, item = novo_x, novo_y, novo_item
                    tentativa += 1
                    continue  # Continua tentando até conseguir
            break  # Sai do loop se não for item especial ou já clicou

    def _achou_item(self, item, x, y):
        try:
            regiao_img = screenshot_util.capture_region(self.handle, x - 50, y + 8, 150, 25)
            achou_item = screenshot_util.is_image_in_region(regiao_img, item, threshold=.8)

            if achou_item and self._achou_item_zen(item, x, y) is False:
                achou_item = False
        except:
            achou_item = False

        return achou_item

    def _achou_item_zen(self, item, x, y):
        if obter_menu(self.handle).get(Menu.UPAR) == 1:
            x = int(x)
            y = int(y)
            if 'zen' in item:
                if self.classe in ['DL', 'EF']:
                    raio = 100
                else:
                    raio = 60
                x_alvo, y_alvo = 400, 255  # CENTRO DA TELA

                distancia = ((x - x_alvo) ** 2 + (y - y_alvo) ** 2) ** 0.5
                return distancia <= raio
        return True

    def _calibrar(self, x, y, item):
        if item is None:
            return None, None

        if obter_menu(self.handle).get(Menu.JOIAS) == 1 or obter_menu(self.handle).get(Menu.UPAR) == 1 or obter_menu(
                self.handle).get(Menu.PICKKANTURU) == 1:
            if 'gemstone' in item:
                return self._calibrar_comum(x, y)
            # elif 'joia' in item:
            #     return self._calibrar_joia(x, y)
            # elif 'key' in item:c
            # elif 'kalima' in item and self.sessao.ler_menu(MenuFields.UPAR) == 1 and self.classe != 'EF':
            #     return self._calibrar_comum(x, y)
            elif 'zen' in item and obter_menu(self.handle).get(Menu.UPAR) == 1:
                return self._calibrar_zen(x, y)
        else:
            if 'gemsto ne' in item:
                return self._calibrar_comum(x, y)
            elif 'joia' in item:
                return self._calibrar_joia(x, y)
            elif 'complex' in item:
                return self._calibrar_comum(x, y)
            # elif 'uniria' in item:
            #     return self._calibrar_comum(x, y)
            elif 'kalima' in item:
                return self._calibrar_comum(x, y)
            elif 'zen' in item:
                return self._calibrar_zen(x, y)

        return None, None

    def _calibrar_comum(self, x, y):
        return x, y + 12

    def _calibrar_joia(self, x, y):
        return x + 12, y + 12

    def _calibrar_zen(self, x, y):
        return x + 12, y + 12
