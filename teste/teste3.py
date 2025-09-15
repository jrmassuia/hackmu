from typing import Any
import numpy as np
from PIL import Image, ImageDraw
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder


def _decode_file(data: bytes) -> bytes:
    xor_keys = [
        0xD1, 0x73, 0x52, 0xF6,
        0xD2, 0x9A, 0xCB, 0x27,
        0x3E, 0xAF, 0x59, 0x31,
        0x37, 0xB3, 0xE7, 0xA2,
    ]
    size = len(data)
    key = 0x5E
    result = bytearray(size)
    for i in range(size):
        result[i] = data[i] ^ xor_keys[i % 16]
        diff = result[i] - key
        if diff < 0:
            diff = 256 + diff
        result[i] = diff
        key = (data[i] + 0x3D) & 0xFF
    return result


def _normalize_terrain_data(terrain_data: bytes) -> bytes:
    size = int(len(terrain_data))
    data = bytearray(terrain_data)
    while size > 65536:
        data = data[0::2]
        size = len(data)
    for i in range(size):
        data[i] &= 0x0F
    return bytes(data)


def _bytes_to_grid(data: bytes) -> list[list[int]]:
    if len(data) != 65536:
        raise ValueError("Data must be exactly 65536 bytes.")
    grid_size = 256
    grid = [[0] * grid_size for _ in range(grid_size)]
    for i in range(65536):
        x = i & 0xFF
        y = (i >> 8) & 0xFF
        value = data[i]
        if value in [1]:  # Safe Zone
            tile_type = 1
        elif value in [0, 2, 3]:  # Normal Zone
            tile_type = 2
        else:  # Not Walkable
            tile_type = 0
        grid[y][x] = tile_type  # Corrigido para alinhar corretamente os eixos
    return grid


def xor_3(data: bytes) -> bytes:
    xor3_keys = (0xFC, 0xCF, 0xAB)
    size = len(data)
    result = bytearray(data)
    for i in range(size):
        result[i] ^= xor3_keys[i % 3]
    return bytes(result)


def find_path(grid: list[list[int]], start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    grid_obj = Grid(matrix=grid)
    start_node = grid_obj.node(*start)
    end_node = grid_obj.node(*end)
    finder = AStarFinder()
    path, _ = finder.find_path(start_node, end_node, grid_obj)
    return path


def draw_path_on_map(grid: list[list[int]], path: list[tuple[int, int]], map_name: str) -> None:
    img = Image.new("RGB", (256, 256), "black")
    draw = ImageDraw.Draw(img)

    for y in range(256):
        for x in range(256):
            if grid[y][x] == 1:
                draw.point((x, y), fill=(0, 200, 0))
            elif grid[y][x] == 2:
                draw.point((x, y), fill=(200, 200, 200))

    for x, y in path:
        draw.point((x, y), fill=(255, 0, 0))

    img.save(f"./{map_name}_path.png")


# terrain_att_path = "C:/Program Files (x86)/MUCABRASIL/Data/World1/EncTerrain1.att" - LORENCIA
name = '3'
terrain_att_path = "C:/Program Files (x86)/MUCABRASIL/Data/World"+name+"/EncTerrain"+name+".att"
with open(terrain_att_path, "rb") as f:
    enc_terrain_att = f.read()

decoded_file = _decode_file(enc_terrain_att)
xor3_decrypted = xor_3(decoded_file)
terrain_data = xor3_decrypted[4:]
terrain_data = _normalize_terrain_data(terrain_data)
grid = _bytes_to_grid(terrain_data)

# Definir pontos de início e fim para o caminho
start_position = (31, 27)
end_position = (61, 52)

# Encontrar o caminho
path = find_path(grid, start_position, end_position)
print("Caminho encontrado:", [(x, y) for x, y in path])

draw_path_on_map(grid, path, "Lorencia")
