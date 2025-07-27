import struct
import os
from PIL import Image
import numpy as np

def to_utf16le_fixed(s, length):
    encoded = s.encode("utf-16le")
    return encoded[:length] + b'\x00' * (length - len(encoded[:length]))

def rgb888_to_rgb565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def reorder_tiles(pixels, width, height):
    tile_order = [
        0,1,8,9,2,3,10,11,16,17,24,25,18,19,26,27,
        4,5,12,13,6,7,14,15,20,21,28,29,22,23,30,31,
        32,33,40,41,34,35,42,43,48,49,56,57,50,51,58,59,
        36,37,44,45,38,39,46,47,52,53,60,61,54,55,62,63
    ]
    out = []
    for ty in range(0, height, 8):
        for tx in range(0, width, 8):
            for i in tile_order:
                x = tx + (i % 8)
                y = ty + (i // 8)
                r, g, b = pixels[y, x][:3]
                out.append(rgb888_to_rgb565(r, g, b))
    return out

def write_smdh(
    path_to_smdh,
    path_to_icon=None,
    short_desc="",
    long_desc="",
    publisher=""
):
    # SMDH is exactly 0x36C8 bytes (14024)
    data = bytearray(0x36C8)

    # Magic + Version
    struct.pack_into("<IHH", data, 0x00, 0x48444D53, 0x0001, 0x0000)
    print("Header written: magic + version")

    for i in range(16):
        base = 0x08 + i * 0x200
        struct.pack_into(f"<{0x40 * 2}s", data, base, to_utf16le_fixed(short_desc, 0x40 * 2))
        struct.pack_into(f"<{0x80 * 2}s", data, base + 0x80, to_utf16le_fixed(long_desc, 0x80 * 2))
        struct.pack_into(f"<{0x40 * 2}s", data, base + 0x180, to_utf16le_fixed(publisher, 0x40 * 2))
    print("Titles (short, long, publisher) written")

    # Default icons (filled if no image is given)
    if path_to_icon and os.path.isfile(path_to_icon):
        img = Image.open(path_to_icon).convert("RGB")
    else:
        print("No valid icon provided, using blank icon")
        img = Image.new("RGB", (48, 48), (0, 0, 0))

    #NOT WORKING (Image will be added through devkitpro's Makefile)
    # Small Icon (24x24) at offset 0x2020
    #small = img.resize((24, 24), Image.Resampling.LANCZOS)
    #small_pixels = np.array(small)
    #small_rgb565 = reorder_tiles(small_pixels, 24, 24)
    #for i, val in enumerate(small_rgb565):
    #    struct.pack_into("<H", data, 0x2020 + i * 2, val)
    #print(f"Small icon written: {len(small_rgb565)} values")

    # Big Icon (48x48) at offset 0x2C08
    #big = img.resize((48, 48), Image.Resampling.LANCZOS)
    #big_pixels = np.array(big)
    #big_rgb565 = reorder_tiles(big_pixels, 48, 48)
    #for i, val in enumerate(big_rgb565):
    #    offset = 0x2C08 + i * 2
    #    if offset + 2 > len(data):
    #        print(f"Skipped pixel {i} at offset {offset}: beyond buffer size")
    #        break
    #    struct.pack_into("<H", data, offset, val)
    #print(f"Big icon written: {min(len(big_rgb565), (len(data)-0x2C08)//2)} values")

    # Write final file
    with open(path_to_smdh, "wb") as f:
        f.write(data)
        print(f"SMDH file written to {path_to_smdh}")

