import time

from utils import mouse_util


def limpar_mob_ao_redor(handle):
    posicoes = [
        (542, 262),
        (427, 330),
        (414, 331),
        (424, 331),
        (450, 325),
        (472, 312),
        (490, 289),
        (498, 256),
        (497, 226),
        (490, 212),
        (464, 185),
        (430, 167),
        (397, 156),
        (365, 155),
        (330, 162),
        (290, 187),
        (274, 216),
        (270, 251),
        (277, 289),
        (301, 318),
        (355, 335),
        (390, 336),
        (401, 337),
    ]

    mouse_util.ativar_click_direito(handle)
    for x, y in posicoes:
        mouse_util.mover(handle, x, y)
        time.sleep(.2)
    mouse_util.desativar_click_direito(handle)
