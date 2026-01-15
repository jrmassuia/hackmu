def _dentro_da_area(coordenadas, x_min, x_max, y_min, y_max):
    y, x = coordenadas
    return x is not None and y is not None and x_min <= x <= x_max and y_min <= y <= y_max


def lorencia(coordenadas):
    return _dentro_da_area(coordenadas, 115, 136, 113, 155)


def noria(coordenadas):
    return _dentro_da_area(coordenadas, 90, 130, 165, 201)


def devias(coordenadas):
    return _dentro_da_area(coordenadas, 30, 60, 190, 220)


def atlans(coordenadas):
    return _dentro_da_area(coordenadas, 11, 24, 12, 29)


def losttower(coordenadas):
    return _dentro_da_area(coordenadas, 70, 85, 200, 215)


def tk(coordenadas):
    return _dentro_da_area(coordenadas, 50, 74, 185, 207)


def tk2_portal(coordenadas):
    return _dentro_da_area(coordenadas, 190, 210, 7, 20)


def aida(coordenadas):
    return _dentro_da_area(coordenadas, 5, 17, 75, 92)


def knv(coordenadas):
    return _dentro_da_area(coordenadas, 174, 188, 66, 76)


def k1(coordenadas):
    return _dentro_da_area(coordenadas, 190, 220, 15, 43)


def k3(coordenadas):
    return _dentro_da_area(coordenadas, 100, 110, 70, 77)


def kalima(coordenadas):
    return _dentro_da_area(coordenadas, 10, 30, 6, 20)


def fora_land(coordenadas):
    return _dentro_da_area(coordenadas, 70, 120, 100, 150)


def sair_da_safe_atlans(moverSpotUtil):
    moverSpotUtil.movimentar((20, 31), movimentacao_proxima=True)


def sair_da_safe_k3(moverSpotUtil):
    moverSpotUtil.movimentar((94, 105), movimentacao_proxima=True)
