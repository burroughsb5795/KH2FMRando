"""Registry of known 03system.bin / 00battle.bin sub-table parsers.

Maps a BAR entry name (e.g. "trsr", "item", "enmp") to its parse/write
functions. Entries not listed here have no known binary layout yet:
03system.bin's pref/ftst/ipic, and 00progress.bin's per-world tables (zz, tt,
hb, ...) -- none of these appear anywhere in KH2FM_Editor (see
kh2fm_editor_reference memory).
"""

from __future__ import annotations
from typing import Callable, Dict, NamedTuple

from .trsr import TrsrEntry, TrsrTable, parse_trsr, write_trsr
from .rcct import RcctEntry, RcctTable, parse_rcct, write_rcct
from .cmd import CmdEntry, CmdTable, parse_cmd, write_cmd
from .sklt import SkltEntry, SkltTable, parse_sklt, write_sklt
from .evtp import EvtpEntry, EvtpTable, parse_evtp, write_evtp
from .memt import MemtTable, parse_memt, write_memt
from .wmst import WmstEntry, WmstTable, parse_wmst, write_wmst
from .item import ItemTable, parse_item, write_item
from .arif import ArifTable, parse_arif, write_arif
from .shop import ShopTable, parse_shop, write_shop
from .went import WentTable, parse_went, write_went
from .atkp import AtkpEntry, AtkpTable, parse_atkp, write_atkp
from .bons import BonsEntry, BonsTable, parse_bons, write_bons
from .btlv import BtlvEntry, BtlvTable, parse_btlv, write_btlv
from .enmp import EnmpEntry, EnmpTable, parse_enmp, write_enmp
from .fmlv import FmlvEntry, FmlvTable, parse_fmlv, write_fmlv
from .limt import LimtEntry, LimtTable, parse_limt, write_limt
from .lvpm import LvpmEntry, LvpmTable, parse_lvpm, write_lvpm
from .lvup import LvupTable, parse_lvup, write_lvup
from .magc import MagcEntry, MagcTable, parse_magc, write_magc
from .patn import PatnEntry, PatnTable, parse_patn, write_patn
from .plrp import PlrpEntry, PlrpTable, parse_plrp, write_plrp
from .przt import PrztEntry, PrztTable, parse_przt, write_przt
from .ptya import PtyaTable, parse_ptya, write_ptya
from .stop import StopEntry, StopTable, parse_stop, write_stop
from .sumn import SumnEntry, SumnTable, parse_sumn, write_sumn
from .vtbl import VtblEntry, VtblTable, parse_vtbl, write_vtbl


class TableSpec(NamedTuple):
    parse: Callable[[bytes], object]
    write: Callable[[object], bytes]


# name -> (parse_fn, write_fn); every write_fn(parse_fn(data)) round-trips byte-perfect.
REGISTRY: Dict[str, TableSpec] = {
    # 03system.bin
    "trsr": TableSpec(parse_trsr, write_trsr),
    "rcct": TableSpec(parse_rcct, write_rcct),
    "cmd": TableSpec(parse_cmd, write_cmd),
    "sklt": TableSpec(parse_sklt, write_sklt),
    "evtp": TableSpec(parse_evtp, write_evtp),
    "memt": TableSpec(parse_memt, write_memt),
    "wmst": TableSpec(parse_wmst, write_wmst),
    "item": TableSpec(parse_item, write_item),
    "arif": TableSpec(parse_arif, write_arif),
    "shop": TableSpec(parse_shop, write_shop),
    "went": TableSpec(parse_went, write_went),
    # 00battle.bin
    "atkp": TableSpec(parse_atkp, write_atkp),
    "bons": TableSpec(parse_bons, write_bons),
    "btlv": TableSpec(parse_btlv, write_btlv),
    "enmp": TableSpec(parse_enmp, write_enmp),
    "fmlv": TableSpec(parse_fmlv, write_fmlv),
    "limt": TableSpec(parse_limt, write_limt),
    "lvpm": TableSpec(parse_lvpm, write_lvpm),
    "lvup": TableSpec(parse_lvup, write_lvup),
    "magc": TableSpec(parse_magc, write_magc),
    "patn": TableSpec(parse_patn, write_patn),
    "plrp": TableSpec(parse_plrp, write_plrp),
    "przt": TableSpec(parse_przt, write_przt),
    "ptya": TableSpec(parse_ptya, write_ptya),
    "stop": TableSpec(parse_stop, write_stop),
    "sumn": TableSpec(parse_sumn, write_sumn),
    "vtbl": TableSpec(parse_vtbl, write_vtbl),
}


class FlatTableSpec(NamedTuple):
    entry_cls: type
    table_cls: type
    parse: Callable[[bytes], object]
    write: Callable[[object], bytes]
    header_field: str  # name of the table-level header field (e.g. "version"/"type"), or "" if none
    default_header: int  # observed value for header_field in the US FM data


# Tables with a single flat `.entries` list of *scalar-only* fields -- these
# support generic CSV parse/pack. (memt, item, arif, shop, went, atkp, lvup,
# ptya are composite/nested; btlv, enmp, plrp, vtbl have a List[int] sub-field
# each -- e.g. per-difficulty battle levels -- so they're excluded too.)
FLAT_TABLES: Dict[str, FlatTableSpec] = {
    # 03system.bin
    "trsr": FlatTableSpec(TrsrEntry, TrsrTable, parse_trsr, write_trsr, "version", 3),
    "rcct": FlatTableSpec(RcctEntry, RcctTable, parse_rcct, write_rcct, "type", 1),
    "cmd": FlatTableSpec(CmdEntry, CmdTable, parse_cmd, write_cmd, "type", 2),
    "sklt": FlatTableSpec(SkltEntry, SkltTable, parse_sklt, write_sklt, "type", 1),
    "evtp": FlatTableSpec(EvtpEntry, EvtpTable, parse_evtp, write_evtp, "type", 1),
    "wmst": FlatTableSpec(WmstEntry, WmstTable, parse_wmst, write_wmst, "", 0),
    # 00battle.bin
    "bons": FlatTableSpec(BonsEntry, BonsTable, parse_bons, write_bons, "type", 2),
    "fmlv": FlatTableSpec(FmlvEntry, FmlvTable, parse_fmlv, write_fmlv, "type", 2),
    "limt": FlatTableSpec(LimtEntry, LimtTable, parse_limt, write_limt, "type", 2),
    "lvpm": FlatTableSpec(LvpmEntry, LvpmTable, parse_lvpm, write_lvpm, "", 0),
    "magc": FlatTableSpec(MagcEntry, MagcTable, parse_magc, write_magc, "type", 1),
    "patn": FlatTableSpec(PatnEntry, PatnTable, parse_patn, write_patn, "type", 2),
    "przt": FlatTableSpec(PrztEntry, PrztTable, parse_przt, write_przt, "type", 2),
    "stop": FlatTableSpec(StopEntry, StopTable, parse_stop, write_stop, "type", 1),
    "sumn": FlatTableSpec(SumnEntry, SumnTable, parse_sumn, write_sumn, "type", 2),
}
