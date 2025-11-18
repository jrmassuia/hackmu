from utils import buscar_coordenada_util


def _coordenadas(handle):
    y, x = buscar_coordenada_util.coordernada(handle)
    return x, y if x and y else (None, None)


def _dentro_da_area(x, y, x_min, x_max, y_min, y_max):
    return x is not None and y is not None and x_min <= x <= x_max and y_min <= y <= y_max


def lorencia(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 115, 136, 130, 151)


def noria(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 90, 130, 165, 201)


def devias(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 30, 60, 190, 220)


def atlans(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 11, 24, 12, 29)


def losttower(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 70, 85, 200, 215)


def tk(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 50, 74, 185, 207)


def tk2_portal(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 190, 210, 7, 20)


def aida(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 5, 17, 75, 92)


def knv(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 174, 188, 66, 76)


def k1(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 190, 220, 15, 43)


def k3(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 100, 110, 70, 77)


def kalima(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 10, 30, 6, 20)


def fora_land(handle):
    x, y = _coordenadas(handle)
    return _dentro_da_area(x, y, 70, 120, 100, 150)


def sair_da_safe_atlans(moverSpotUtil):
    moverSpotUtil.movimentar((20, 31), movimentacao_proxima=True)


def sair_da_safe_k3(moverSpotUtil):
    moverSpotUtil.movimentar((94, 105), movimentacao_proxima=True)
