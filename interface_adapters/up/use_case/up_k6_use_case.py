from interface_adapters.up.use_case.up_kalima_base import UpKalimaBase


class UpK6UseCase(UpKalimaBase):
    def caminho_convite(self):
        return './static/inventario/convitek6.png'

    def nome_mapa(self):
        return 'Kalima6'
