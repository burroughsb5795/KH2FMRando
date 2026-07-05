"""SHOP shop/inventory/product table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Shop/*.cs):
16-byte header (shop count is a uint16 at offset 6), then N 24-byte ShopItem
records, then one 8-byte InventoryItem per shop.inventory_count (concatenated
in shop order), then 2-byte ProductItem records filling the rest of the file
(driven by each inventory's product_count).
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

HEADER_SIZE = 16
SHOP_COUNT_OFFSET = 6

SHOP_SIZE = 24
_SHOP_FMT = "<HHHHHHHHHBBHH"

INVENTORY_SIZE = 8
_INVENTORY_FMT = "<HHHH"

PRODUCT_SIZE = 2
_PRODUCT_FMT = "<H"


@dataclass
class ShopItem:
    id: int
    unlock: int
    name: int
    entity: int
    pos_x: int
    pos_y: int
    pos_z: int
    sound: int
    inventory_count: int
    unk18: int
    unk19: int
    inventory_ofst: int
    padding: int


@dataclass
class InventoryItem:
    unlock_event: int
    product_count: int
    product_ofst: int
    padding: int


@dataclass
class ProductItem:
    product: int


@dataclass
class ShopTable:
    header: bytes
    shops: List[ShopItem]
    inventories: List[InventoryItem]
    products: List[ProductItem]


def parse_shop(data: bytes) -> ShopTable:
    header = data[:HEADER_SIZE]
    shop_count = struct.unpack_from("<H", data, SHOP_COUNT_OFFSET)[0]

    shops = []
    for i in range(shop_count):
        base = HEADER_SIZE + i * SHOP_SIZE
        fields = struct.unpack_from(_SHOP_FMT, data, base)
        shops.append(ShopItem(*fields))

    inv_start = HEADER_SIZE + shop_count * SHOP_SIZE
    total_inventories = sum(s.inventory_count for s in shops)
    inventories = []
    for i in range(total_inventories):
        base = inv_start + i * INVENTORY_SIZE
        fields = struct.unpack_from(_INVENTORY_FMT, data, base)
        inventories.append(InventoryItem(*fields))

    prod_start = inv_start + total_inventories * INVENTORY_SIZE
    total_products = (len(data) - prod_start) // PRODUCT_SIZE
    products = []
    for i in range(total_products):
        base = prod_start + i * PRODUCT_SIZE
        product = struct.unpack_from(_PRODUCT_FMT, data, base)[0]
        products.append(ProductItem(product=product))

    return ShopTable(header=header, shops=shops, inventories=inventories, products=products)


def write_shop(table: ShopTable) -> bytes:
    header = bytearray(table.header)
    struct.pack_into("<H", header, SHOP_COUNT_OFFSET, len(table.shops))

    out = bytearray(header)
    for s in table.shops:
        out += struct.pack(
            _SHOP_FMT,
            s.id, s.unlock, s.name, s.entity, s.pos_x, s.pos_y, s.pos_z,
            s.sound, s.inventory_count, s.unk18, s.unk19, s.inventory_ofst, s.padding,
        )
    for inv in table.inventories:
        out += struct.pack(_INVENTORY_FMT, inv.unlock_event, inv.product_count, inv.product_ofst, inv.padding)
    for p in table.products:
        out += struct.pack(_PRODUCT_FMT, p.product)
    return bytes(out)
