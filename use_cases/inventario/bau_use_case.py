from PIL import Image

from interface_adapters.helpers.buscar_localizacao_item_na_tela_manager import BuscarLocalizacaoItemNaTelaManager


class BauUseCase:


    @staticmethod
    def buscar_local_campo_vazio_bau():
        return BuscarLocalizacaoItemNaTelaManager.buscar_no_bau(Image.open(r'static\img\campovazio.jpg'))