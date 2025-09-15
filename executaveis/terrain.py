from typing import Any

import numpy as np
from PIL import Image


def _decode_file(data: bytes) -> bytes:
    # fmt: off
    xor_keys =[
        0xD1, 0x73, 0x52, 0xF6,
        0xD2, 0x9A, 0xCB, 0x27,
        0x3E, 0xAF, 0x59, 0x31,
        0x37, 0xB3, 0xE7, 0xA2,
    ]
    # fmt: on

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
        grid[x][y] = tile_type

    return grid


def xor_3(data: bytes) -> bytes:
    xor3_keys = (0xFC, 0xCF, 0xAB)

    size = len(data)

    result = bytearray(data)
    for i in range(size):
        result[i] ^= xor3_keys[i % 3]

    return bytes(result)


def _terrain_color_map(terrain_grid: list[list[int]]) -> np.ndarray[Any, np.dtype[np.ubyte]]:
    pixels = np.zeros((256, 256, 3), dtype=np.ubyte)

    for x in range(255):
        for y in range(255):

            value = terrain_grid[x][y]

            if value in [1]:  # safe
                color = (0, 200, 0)
            elif value in [2]:  # normal
                color = (200, 200, 200)
            else:
                color = (0, 0, 0)

            pixels[x, y] = color

    return pixels


def draw_terrain_data(terrain_grid: list[list[int]], map_name: str) -> None:
    pixels = _terrain_color_map(terrain_grid)

    img = Image.fromarray(pixels)

    img.save(f"./{map_name}.png")


terrain_att_path = "C:/Program Files (x86)/MUCABRASIL/Data/World1/EncTerrain1.att"
with open(terrain_att_path, "rb") as f:
    enc_terrain_att = f.read()

decoded_file = _decode_file(enc_terrain_att)
xor3_decrypted = xor_3(decoded_file)

terrain_data = xor3_decrypted[4:]

terrain_data = _normalize_terrain_data(terrain_data)

grid = _bytes_to_grid(terrain_data)

draw_terrain_data(grid, "Lorencia")
