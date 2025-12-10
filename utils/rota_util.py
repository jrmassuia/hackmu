from PIL import Image, ImageDraw
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.core.heuristic import chebyshev
from pathfinding.finder.a_star import AStarFinder

from utils.pointer_util import Pointers


class PathFinder:
    MAPA_LORENCIA = "1"
    MAPA_DUNGEON = "2"
    MAPA_DEVIAS = "3"
    MAPA_NORIA = "4"
    MAPA_LOSTTOWER = "5"
    MAPA_STADIUM = "7"
    MAPA_ATLANS = "8"
    MAPA_TARKAN = "9"
    MAPA_ICARUS = "11"
    MAPA_KALIMA = "25"
    MAPA_LOREN = "31"
    MAPA_LAND = "32"
    MAPA_AIDA = "34"
    MAPA_KANTURU_1_E_2 = "38"
    MAPA_KANTURU_3 = "39"

    mapas = [
        ('MAPA_LORENCIA', '1', 1126694912),
        ('MAPA_DUNGEON', '2', 1128562688),
        ('MAPA_DEVIAS', '3', 1129054208),
        ('MAPA_NORIA', '4', 1128464384),
        ('MAPA_LOSTTOWER', '5', 1129447424),
        ('MAPA_STADIUM', '7', 1130332160),
        ('MAPA_ATLANS', '8', 1130233856),
        ('MAPA_TARKAN', '9', 1125613568),
        ('MAPA_ICARUS', '11', 1133412352),
        ('MAPA_KALIMA', '25', 1131413504),
        ('MAPA_LOREN', '31', 1130430464),
        ('MAPA_LAND', '32', 0),  # FALTA IFORMAR O CODIGO DO MAPA
        ('MAPA_AIDA', '34', 1131511808),
        ('MAPA_KANTURU_1_E_2', '38', 1133215744),
        ('MAPA_KANTURU_3', '39', 1126793216),
    ]

    def __init__(self):
        numero_mapa = self.get_numero_mapa_atual()
        self.file_path = "C:/Program Files (x86)/MUCABRASIL/Data/World" + numero_mapa + "/EncTerrain" + numero_mapa + ".att"
        self.grid = self._load_grid()

    def get_numero_mapa_atual(self):
        mapas = {valor: codigo for _, codigo, valor in self.mapas}
        return mapas[Pointers().get_mapa_atual()]

    def get_nome_mapa_atual(self):
        return {codigo: nome for nome, codigo, _ in self.mapas}[self.get_numero_mapa_atual()]

    def _decode_file(self, data: bytes) -> bytes:
        xor_keys = [
            0xD1, 0x73, 0x52, 0xF6,
            0xD2, 0x9A, 0xCB, 0x27,
            0x3E, 0xAF, 0x59, 0x31,
            0x37, 0xB3, 0xE7, 0xA2,
        ]
        key = 0x5E
        result = bytearray(len(data))
        for i in range(len(data)):
            result[i] = data[i] ^ xor_keys[i % 16]
            diff = result[i] - key
            if diff < 0:
                diff = 256 + diff
            result[i] = diff
            key = (data[i] + 0x3D) & 0xFF
        return result

    def _normalize_terrain_data(self, terrain_data: bytes) -> bytes:
        data = bytearray(terrain_data)
        while len(data) > 65536:
            data = data[0::2]
        for i in range(len(data)):
            data[i] &= 0x0F
        return bytes(data)

    def _bytes_to_grid(self, data: bytes) -> list[list[int]]:
        if len(data) != 65536:
            raise ValueError("Data must be exactly 65536 bytes.")
        grid_size = 256
        grid = [[0] * grid_size for _ in range(grid_size)]
        for i in range(65536):
            x, y = i & 0xFF, (i >> 8) & 0xFF
            value = data[i]
            tile_type = 1 if value == 1 else 2 if value in [0, 2, 3] else 0
            grid[y][x] = tile_type
        return grid

    def _xor_3(self, data: bytes) -> bytes:
        xor3_keys = (0xFC, 0xCF, 0xAB)
        return bytes(b ^ xor3_keys[i % 3] for i, b in enumerate(data))

    def _load_grid(self) -> list[list[int]]:
        try:
            with open(self.file_path, "rb") as f:
                enc_data = f.read()
            decoded = self._decode_file(enc_data)
            decrypted = self._xor_3(decoded)
            terrain_data = self._normalize_terrain_data(decrypted[4:])
            return self._bytes_to_grid(terrain_data)
        except:
            return []

    def find_path(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:

        self.bloquear_bordas(margem=1)

        grid_obj = Grid(matrix=self.grid)

        start_node = grid_obj.node(start[0], start[1])
        end_node = grid_obj.node(end[0], end[1])

        finder = AStarFinder(
            diagonal_movement=DiagonalMovement.if_at_most_one_obstacle,
            heuristic=chebyshev
        )

        path, _ = finder.find_path(start_node, end_node, grid_obj)

        # converte para (y, x) ou (x, y) de acordo com seu uso
        path_array = [(y, x) for (y, x) in path]

        # *** AQUI: simplifica respeitando passo máximo de 4 tiles ***
        path_array = self._simplificar_caminho(path_array, passo_max=4)

        return path_array

    def _simplificar_caminho(self, path: list[tuple[int, int]], passo_max: int = 4) -> list[tuple[int, int]]:
        """
        Simplifica o caminho garantindo que cada salto entre pontos consecutivos
        tenha distância Chebyshev <= passo_max (no seu caso, 4).
        Assim, cada próximo ponto sempre estará dentro da matriz 9x9 de clique.
        """
        if len(path) <= 2:
            return path

        simplificado = [path[0]]
        idx = 0
        n = len(path)

        while idx < n - 1:
            next_idx = idx + 1

            # tenta ir o mais longe possível a partir de 'idx' sem ultrapassar passo_max
            for j in range(idx + 1, n):
                dy = path[j][0] - path[idx][0]
                dx = path[j][1] - path[idx][1]

                if max(abs(dy), abs(dx)) <= passo_max:
                    next_idx = j
                else:
                    # passou do limite, para de tentar ir mais longe
                    break

            simplificado.append(path[next_idx])
            idx = next_idx

        return simplificado

    def draw_path_on_map(self, path: list[tuple[int, int]]) -> None:
        img = Image.new("RGB", (256, 256), "black")
        draw = ImageDraw.Draw(img)
        for y in range(256):
            for x in range(256):
                if self.grid[y][x] == 1:
                    draw.point((x, y), fill=(0, 200, 0))
                elif self.grid[y][x] == 2:
                    draw.point((x, y), fill=(200, 200, 200))
        for x, y in path:
            draw.point((x, y), fill=(255, 0, 0))
        # img.save(f"./{self.MAP_NAME}_path.png")

    def bloquear_bordas(self, margem=1):
        """
        Define uma margem de 'margem' células como não caminhável (valor 0).
        """
        for y in range(256):
            for x in range(256):
                if x < margem or x >= 256 - margem or y < margem or y >= 256 - margem:
                    self.grid[y][x] = 0  # Não caminhável

    def descricao_mapa_atual(self):
        mapas = {valor: codigo for _, codigo, valor in PathFinder.mapas}
        return mapas[Pointers().get_mapa_atual()]

# Exemplo de uso
# for a in range(80):
#     pathfinder = PathFinder(str(a))
#     start_position = (10, 17)
#     end_position = (33, 63)
#     if len(pathfinder.grid) > 0:
#         path = pathfinder.find_path(start_position, end_position)
#         # print("Caminho encontrado:", path)
#         print("Caminho encontrado:", [(x, y) for x, y in path])
#         pathfinder.draw_path_on_map(path)
