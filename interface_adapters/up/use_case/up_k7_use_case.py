from interface_adapters.up.use_case.up_kalima_base import UpKalimaBase


class UpK7UseCase(UpKalimaBase):
    def caminho_convite(self):
        return './static/inventario/convitek7.png'

    def nome_mapa(self):
        return 'Kalima7'
