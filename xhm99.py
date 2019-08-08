#!/usr/bin/env python

# xhm99: An HFE image manager that focuses on the TI 99
#
# Copyright (c) 2016-2019 Ralph Benzinger <xdt99@endlos.net>
#
# This program is part of the TI 99 Cross-Development Tools (xdt99).
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.


import sys


VERSION = "3.0.0"


# Utility functions

def ordw(word):
    """word ord"""
    return (word[0] << 8) | word[1]


def chrw(word):
    """word chr"""
    return bytes((word >> 8, word & 0xff))


def rordl(word):
    """reverse long ord"""
    return word[3] << 24 | word[2] << 16 | word[1] << 8 | word[0]


def rchrw(word):
    """reverse word chr"""
    return bytes((word & 0xff, word >> 8))


def chunk(data, size):
    """split into chunks of equal size"""
    return [data[i:i + size] for i in range(0, len(data), size)]


def flatten(list_of_lists):
    """flattens list of lists into list"""
    return [item for list_ in list_of_lists for item in list_]


def writedata(name, data, mode="wb"):
    """write data to file or STDOUT"""
    if name == "-":
        if "b" in mode:
            sys.stdout.buffer.write(data)
        else:
            sys.stdout.write(data)
    else:
        with open(name, mode) as f:
            f.write(data)


def readdata(name, mode="rb"):
    """read data from file or STDIN"""
    if name == "-":
        if "b" in mode:
            return sys.stdin.buffer.read()
        else:
            return sys.stdin.read()
    else:
        with open(name, mode) as f:
            return f.read()


def crc16(crc, stream):
    """compute CRC-16 code"""
    msb, lsb = crc >> 8, crc & 0xff
    for b in stream:
        x = b ^ msb
        x ^= (x >> 4)
        msb = (lsb ^ (x >> 3) ^ (x << 4)) & 0xff
        lsb = (x ^ (x << 5)) & 0xff
    return [msb, lsb]


class HFEError(Exception):
    pass


class SDFormat:

    sectors = 9
    track_len = 17 + 9 * 334 + 113  # 3136

    leadin = [0xaa, 0xa8, 0xa8, 0x22] + [0xaa] * (4 * 16)  # fc ff
    lvleadin = 17
    leadout = [0xaa] * (4 * 77) + [0xaa, 0x50] + [0x55] * (2 + 4 * 35)  # cannot decode
    lvleadout = 113

    address_mark = [0xaa, 0x88, 0xa8, 0x2a]  # fe
    vaddress_mark = [0xfe]
    lvaddress_mark = 1
    data_mark = [0xaa, 0x88, 0x28, 0xaa]  # fb
    vdata_mark = [0xfb]
    lvdata_mark = 1

    pregap = [0x22] * (4 * 6)  # 00
    lvpregap = 6
    gap1 = [0xaa] * (4 * 11) + [0x22] * (4 * 6)  # ff 00
    lvgap1 = 17
    gap2 = [0xaa] * (4 * 45)  # ff
    lvgap2 = 45

    sector_interleave = (0, 7, 5, 3, 1, 8, 6, 4, 2,  # offset 0
                         6, 4, 2, 0, 7, 5, 3, 1, 8,  # offset 6
                         3, 1, 8, 6, 4, 2, 0, 7, 5)  # offset 3
    sector_interleave_wtf = (4, 2, 0, 7, 5, 3, 1, 8, 6,
                             1, 8, 6, 4, 2, 0, 7, 5, 3,
                             7, 5, 3, 1, 8, 6, 4, 2, 0)

    # twisted encoded bytes with clock bits
    fm_codes = [
        [0x22, 0x22, 0x22, 0x22], [0x22, 0x22, 0x22, 0xa2], [0x22, 0x22, 0x22, 0x2a],
        [0x22, 0x22, 0x22, 0xaa], [0x22, 0x22, 0xa2, 0x22], [0x22, 0x22, 0xa2, 0xa2],
        [0x22, 0x22, 0xa2, 0x2a], [0x22, 0x22, 0xa2, 0xaa], [0x22, 0x22, 0x2a, 0x22],
        [0x22, 0x22, 0x2a, 0xa2], [0x22, 0x22, 0x2a, 0x2a], [0x22, 0x22, 0x2a, 0xaa],
        [0x22, 0x22, 0xaa, 0x22], [0x22, 0x22, 0xaa, 0xa2], [0x22, 0x22, 0xaa, 0x2a],
        [0x22, 0x22, 0xaa, 0xaa], [0x22, 0xa2, 0x22, 0x22], [0x22, 0xa2, 0x22, 0xa2],
        [0x22, 0xa2, 0x22, 0x2a], [0x22, 0xa2, 0x22, 0xaa], [0x22, 0xa2, 0xa2, 0x22],
        [0x22, 0xa2, 0xa2, 0xa2], [0x22, 0xa2, 0xa2, 0x2a], [0x22, 0xa2, 0xa2, 0xaa],
        [0x22, 0xa2, 0x2a, 0x22], [0x22, 0xa2, 0x2a, 0xa2], [0x22, 0xa2, 0x2a, 0x2a],
        [0x22, 0xa2, 0x2a, 0xaa], [0x22, 0xa2, 0xaa, 0x22], [0x22, 0xa2, 0xaa, 0xa2],
        [0x22, 0xa2, 0xaa, 0x2a], [0x22, 0xa2, 0xaa, 0xaa], [0x22, 0x2a, 0x22, 0x22],
        [0x22, 0x2a, 0x22, 0xa2], [0x22, 0x2a, 0x22, 0x2a], [0x22, 0x2a, 0x22, 0xaa],
        [0x22, 0x2a, 0xa2, 0x22], [0x22, 0x2a, 0xa2, 0xa2], [0x22, 0x2a, 0xa2, 0x2a],
        [0x22, 0x2a, 0xa2, 0xaa], [0x22, 0x2a, 0x2a, 0x22], [0x22, 0x2a, 0x2a, 0xa2],
        [0x22, 0x2a, 0x2a, 0x2a], [0x22, 0x2a, 0x2a, 0xaa], [0x22, 0x2a, 0xaa, 0x22],
        [0x22, 0x2a, 0xaa, 0xa2], [0x22, 0x2a, 0xaa, 0x2a], [0x22, 0x2a, 0xaa, 0xaa],
        [0x22, 0xaa, 0x22, 0x22], [0x22, 0xaa, 0x22, 0xa2], [0x22, 0xaa, 0x22, 0x2a],
        [0x22, 0xaa, 0x22, 0xaa], [0x22, 0xaa, 0xa2, 0x22], [0x22, 0xaa, 0xa2, 0xa2],
        [0x22, 0xaa, 0xa2, 0x2a], [0x22, 0xaa, 0xa2, 0xaa], [0x22, 0xaa, 0x2a, 0x22],
        [0x22, 0xaa, 0x2a, 0xa2], [0x22, 0xaa, 0x2a, 0x2a], [0x22, 0xaa, 0x2a, 0xaa],
        [0x22, 0xaa, 0xaa, 0x22], [0x22, 0xaa, 0xaa, 0xa2], [0x22, 0xaa, 0xaa, 0x2a],
        [0x22, 0xaa, 0xaa, 0xaa], [0xa2, 0x22, 0x22, 0x22], [0xa2, 0x22, 0x22, 0xa2],
        [0xa2, 0x22, 0x22, 0x2a], [0xa2, 0x22, 0x22, 0xaa], [0xa2, 0x22, 0xa2, 0x22],
        [0xa2, 0x22, 0xa2, 0xa2], [0xa2, 0x22, 0xa2, 0x2a], [0xa2, 0x22, 0xa2, 0xaa],
        [0xa2, 0x22, 0x2a, 0x22], [0xa2, 0x22, 0x2a, 0xa2], [0xa2, 0x22, 0x2a, 0x2a],
        [0xa2, 0x22, 0x2a, 0xaa], [0xa2, 0x22, 0xaa, 0x22], [0xa2, 0x22, 0xaa, 0xa2],
        [0xa2, 0x22, 0xaa, 0x2a], [0xa2, 0x22, 0xaa, 0xaa], [0xa2, 0xa2, 0x22, 0x22],
        [0xa2, 0xa2, 0x22, 0xa2], [0xa2, 0xa2, 0x22, 0x2a], [0xa2, 0xa2, 0x22, 0xaa],
        [0xa2, 0xa2, 0xa2, 0x22], [0xa2, 0xa2, 0xa2, 0xa2], [0xa2, 0xa2, 0xa2, 0x2a],
        [0xa2, 0xa2, 0xa2, 0xaa], [0xa2, 0xa2, 0x2a, 0x22], [0xa2, 0xa2, 0x2a, 0xa2],
        [0xa2, 0xa2, 0x2a, 0x2a], [0xa2, 0xa2, 0x2a, 0xaa], [0xa2, 0xa2, 0xaa, 0x22],
        [0xa2, 0xa2, 0xaa, 0xa2], [0xa2, 0xa2, 0xaa, 0x2a], [0xa2, 0xa2, 0xaa, 0xaa],
        [0xa2, 0x2a, 0x22, 0x22], [0xa2, 0x2a, 0x22, 0xa2], [0xa2, 0x2a, 0x22, 0x2a],
        [0xa2, 0x2a, 0x22, 0xaa], [0xa2, 0x2a, 0xa2, 0x22], [0xa2, 0x2a, 0xa2, 0xa2],
        [0xa2, 0x2a, 0xa2, 0x2a], [0xa2, 0x2a, 0xa2, 0xaa], [0xa2, 0x2a, 0x2a, 0x22],
        [0xa2, 0x2a, 0x2a, 0xa2], [0xa2, 0x2a, 0x2a, 0x2a], [0xa2, 0x2a, 0x2a, 0xaa],
        [0xa2, 0x2a, 0xaa, 0x22], [0xa2, 0x2a, 0xaa, 0xa2], [0xa2, 0x2a, 0xaa, 0x2a],
        [0xa2, 0x2a, 0xaa, 0xaa], [0xa2, 0xaa, 0x22, 0x22], [0xa2, 0xaa, 0x22, 0xa2],
        [0xa2, 0xaa, 0x22, 0x2a], [0xa2, 0xaa, 0x22, 0xaa], [0xa2, 0xaa, 0xa2, 0x22],
        [0xa2, 0xaa, 0xa2, 0xa2], [0xa2, 0xaa, 0xa2, 0x2a], [0xa2, 0xaa, 0xa2, 0xaa],
        [0xa2, 0xaa, 0x2a, 0x22], [0xa2, 0xaa, 0x2a, 0xa2], [0xa2, 0xaa, 0x2a, 0x2a],
        [0xa2, 0xaa, 0x2a, 0xaa], [0xa2, 0xaa, 0xaa, 0x22], [0xa2, 0xaa, 0xaa, 0xa2],
        [0xa2, 0xaa, 0xaa, 0x2a], [0xa2, 0xaa, 0xaa, 0xaa], [0x2a, 0x22, 0x22, 0x22],
        [0x2a, 0x22, 0x22, 0xa2], [0x2a, 0x22, 0x22, 0x2a], [0x2a, 0x22, 0x22, 0xaa],
        [0x2a, 0x22, 0xa2, 0x22], [0x2a, 0x22, 0xa2, 0xa2], [0x2a, 0x22, 0xa2, 0x2a],
        [0x2a, 0x22, 0xa2, 0xaa], [0x2a, 0x22, 0x2a, 0x22], [0x2a, 0x22, 0x2a, 0xa2],
        [0x2a, 0x22, 0x2a, 0x2a], [0x2a, 0x22, 0x2a, 0xaa], [0x2a, 0x22, 0xaa, 0x22],
        [0x2a, 0x22, 0xaa, 0xa2], [0x2a, 0x22, 0xaa, 0x2a], [0x2a, 0x22, 0xaa, 0xaa],
        [0x2a, 0xa2, 0x22, 0x22], [0x2a, 0xa2, 0x22, 0xa2], [0x2a, 0xa2, 0x22, 0x2a],
        [0x2a, 0xa2, 0x22, 0xaa], [0x2a, 0xa2, 0xa2, 0x22], [0x2a, 0xa2, 0xa2, 0xa2],
        [0x2a, 0xa2, 0xa2, 0x2a], [0x2a, 0xa2, 0xa2, 0xaa], [0x2a, 0xa2, 0x2a, 0x22],
        [0x2a, 0xa2, 0x2a, 0xa2], [0x2a, 0xa2, 0x2a, 0x2a], [0x2a, 0xa2, 0x2a, 0xaa],
        [0x2a, 0xa2, 0xaa, 0x22], [0x2a, 0xa2, 0xaa, 0xa2], [0x2a, 0xa2, 0xaa, 0x2a],
        [0x2a, 0xa2, 0xaa, 0xaa], [0x2a, 0x2a, 0x22, 0x22], [0x2a, 0x2a, 0x22, 0xa2],
        [0x2a, 0x2a, 0x22, 0x2a], [0x2a, 0x2a, 0x22, 0xaa], [0x2a, 0x2a, 0xa2, 0x22],
        [0x2a, 0x2a, 0xa2, 0xa2], [0x2a, 0x2a, 0xa2, 0x2a], [0x2a, 0x2a, 0xa2, 0xaa],
        [0x2a, 0x2a, 0x2a, 0x22], [0x2a, 0x2a, 0x2a, 0xa2], [0x2a, 0x2a, 0x2a, 0x2a],
        [0x2a, 0x2a, 0x2a, 0xaa], [0x2a, 0x2a, 0xaa, 0x22], [0x2a, 0x2a, 0xaa, 0xa2],
        [0x2a, 0x2a, 0xaa, 0x2a], [0x2a, 0x2a, 0xaa, 0xaa], [0x2a, 0xaa, 0x22, 0x22],
        [0x2a, 0xaa, 0x22, 0xa2], [0x2a, 0xaa, 0x22, 0x2a], [0x2a, 0xaa, 0x22, 0xaa],
        [0x2a, 0xaa, 0xa2, 0x22], [0x2a, 0xaa, 0xa2, 0xa2], [0x2a, 0xaa, 0xa2, 0x2a],
        [0x2a, 0xaa, 0xa2, 0xaa], [0x2a, 0xaa, 0x2a, 0x22], [0x2a, 0xaa, 0x2a, 0xa2],
        [0x2a, 0xaa, 0x2a, 0x2a], [0x2a, 0xaa, 0x2a, 0xaa], [0x2a, 0xaa, 0xaa, 0x22],
        [0x2a, 0xaa, 0xaa, 0xa2], [0x2a, 0xaa, 0xaa, 0x2a], [0x2a, 0xaa, 0xaa, 0xaa],
        [0xaa, 0x22, 0x22, 0x22], [0xaa, 0x22, 0x22, 0xa2], [0xaa, 0x22, 0x22, 0x2a],
        [0xaa, 0x22, 0x22, 0xaa], [0xaa, 0x22, 0xa2, 0x22], [0xaa, 0x22, 0xa2, 0xa2],
        [0xaa, 0x22, 0xa2, 0x2a], [0xaa, 0x22, 0xa2, 0xaa], [0xaa, 0x22, 0x2a, 0x22],
        [0xaa, 0x22, 0x2a, 0xa2], [0xaa, 0x22, 0x2a, 0x2a], [0xaa, 0x22, 0x2a, 0xaa],
        [0xaa, 0x22, 0xaa, 0x22], [0xaa, 0x22, 0xaa, 0xa2], [0xaa, 0x22, 0xaa, 0x2a],
        [0xaa, 0x22, 0xaa, 0xaa], [0xaa, 0xa2, 0x22, 0x22], [0xaa, 0xa2, 0x22, 0xa2],
        [0xaa, 0xa2, 0x22, 0x2a], [0xaa, 0xa2, 0x22, 0xaa], [0xaa, 0xa2, 0xa2, 0x22],
        [0xaa, 0xa2, 0xa2, 0xa2], [0xaa, 0xa2, 0xa2, 0x2a], [0xaa, 0xa2, 0xa2, 0xaa],
        [0xaa, 0xa2, 0x2a, 0x22], [0xaa, 0xa2, 0x2a, 0xa2], [0xaa, 0xa2, 0x2a, 0x2a],
        [0xaa, 0xa2, 0x2a, 0xaa], [0xaa, 0xa2, 0xaa, 0x22], [0xaa, 0xa2, 0xaa, 0xa2],
        [0xaa, 0xa2, 0xaa, 0x2a], [0xaa, 0xa2, 0xaa, 0xaa], [0xaa, 0x2a, 0x22, 0x22],
        [0xaa, 0x2a, 0x22, 0xa2], [0xaa, 0x2a, 0x22, 0x2a], [0xaa, 0x2a, 0x22, 0xaa],
        [0xaa, 0x2a, 0xa2, 0x22], [0xaa, 0x2a, 0xa2, 0xa2], [0xaa, 0x2a, 0xa2, 0x2a],
        [0xaa, 0x2a, 0xa2, 0xaa], [0xaa, 0x2a, 0x2a, 0x22], [0xaa, 0x2a, 0x2a, 0xa2],
        [0xaa, 0x2a, 0x2a, 0x2a], [0xaa, 0x2a, 0x2a, 0xaa], [0xaa, 0x2a, 0xaa, 0x22],
        [0xaa, 0x2a, 0xaa, 0xa2], [0xaa, 0x2a, 0xaa, 0x2a], [0xaa, 0x2a, 0xaa, 0xaa],
        [0xaa, 0xaa, 0x22, 0x22], [0xaa, 0xaa, 0x22, 0xa2], [0xaa, 0xaa, 0x22, 0x2a],
        [0xaa, 0xaa, 0x22, 0xaa], [0xaa, 0xaa, 0xa2, 0x22], [0xaa, 0xaa, 0xa2, 0xa2],
        [0xaa, 0xaa, 0xa2, 0x2a], [0xaa, 0xaa, 0xa2, 0xaa], [0xaa, 0xaa, 0x2a, 0x22],
        [0xaa, 0xaa, 0x2a, 0xa2], [0xaa, 0xaa, 0x2a, 0x2a], [0xaa, 0xaa, 0x2a, 0xaa],
        [0xaa, 0xaa, 0xaa, 0x22], [0xaa, 0xaa, 0xaa, 0xa2], [0xaa, 0xaa, 0xaa, 0x2a],
        [0xaa, 0xaa, 0xaa, 0xaa]
    ]

    @classmethod
    def decode(cls, stream):
        """decode FM bit stream into bytes"""
        bs = []
        for i in range(0, len(stream), 4):
            v = rordl(stream[i:i + 4])
            # bit format:  ABCDEFGH <->  H...G... F...E... D...C... B...A...
            b = (
                (0x01 if v & 0x80000000 else 0) |
                (0x02 if v & 0x08000000 else 0) |
                (0x04 if v & 0x00800000 else 0) |
                (0x08 if v & 0x00080000 else 0) |
                (0x10 if v & 0x00008000 else 0) |
                (0x20 if v & 0x00000800 else 0) |
                (0x40 if v & 0x00000080 else 0) |
                (0x80 if v & 0x00000008 else 0)
                )
            bs.append(b)
        return bs

    @classmethod
    def encode(cls, track):
        """encode SD track into FM bit stream"""
        stream = []
        for b in track:
            stream.extend(cls.fm_codes[b])
        return stream

    @classmethod
    def interleave(cls, side, track, sector, wtf80t):
        if not wtf80t or side == 0:
            return cls.sector_interleave[(track * cls.sectors + sector) % 27]
        elif track < 37:
            return cls.sector_interleave_wtf[(track * cls.sectors + sector) % 27]  # WTF?
        else:
            return cls.sector_interleave[((track - 37) * cls.sectors + sector) % 27]  # off-series

    @classmethod
    def fix_clocks(cls, stream):
        """fix clock bits in stream (inline)"""
        pass  # clocks are correct


class DDFormat:

    sectors = 18
    track_len = 32 + 18 * 342 + 84  # 6272

    leadin = [0x49, 0x2a] * 32  # 4e
    lvleadin = 32
    leadout = [0x49, 0x2a] * 84  # 4e
    lvleadout = 84

    address_mark = [0x22, 0x91, 0x22, 0x91, 0x22, 0x91, 0xaa, 0x2a]
    vaddress_mark = [0xa1, 0xa1, 0xa1, 0xfe]
    lvaddress_mark = 4
    data_mark = [0x22, 0x91, 0x22, 0x91, 0x22, 0x91, 0xaa, 0xa2]
    vdata_mark = [0xa1, 0xa1, 0xa1, 0xfb]
    lvdata_mark = 4

    pregap = [0x55] * (2 * 12)  # 00
    lvpregap = 12
    gap1 = [0x49, 0x2a] * 22 + [0x55] * (2 * 12)  # 4e/00
    lvgap1 = 34
    gap2 = [0x49, 0x2a] * 24  # 4e
    lvgap2 = 24

    sector_interleave = (0, 11, 4, 15, 8, 1, 12, 5, 16,
                         9, 2, 13, 6, 17, 10, 3, 14, 7)

    # computation rule: w = int(bs[7::-1], 2) * 256 + int(bs[:7:-1], 2)
    mfm_codes = [
        [0x55, 0x55], [0x55, 0x95], [0x55, 0x25], [0x55, 0xa5],
        [0x55, 0x49], [0x55, 0x89], [0x55, 0x29], [0x55, 0xa9],
        [0x55, 0x52], [0x55, 0x92], [0x55, 0x22], [0x55, 0xa2],
        [0x55, 0x4a], [0x55, 0x8a], [0x55, 0x2a], [0x55, 0xaa],
        [0x95, 0x54], [0x95, 0x94], [0x95, 0x24], [0x95, 0xa4],
        [0x95, 0x48], [0x95, 0x88], [0x95, 0x28], [0x95, 0xa8],
        [0x95, 0x52], [0x95, 0x92], [0x95, 0x22], [0x95, 0xa2],
        [0x95, 0x4a], [0x95, 0x8a], [0x95, 0x2a], [0x95, 0xaa],
        [0x25, 0x55], [0x25, 0x95], [0x25, 0x25], [0x25, 0xa5],
        [0x25, 0x49], [0x25, 0x89], [0x25, 0x29], [0x25, 0xa9],
        [0x25, 0x52], [0x25, 0x92], [0x25, 0x22], [0x25, 0xa2],
        [0x25, 0x4a], [0x25, 0x8a], [0x25, 0x2a], [0x25, 0xaa],
        [0xa5, 0x54], [0xa5, 0x94], [0xa5, 0x24], [0xa5, 0xa4],
        [0xa5, 0x48], [0xa5, 0x88], [0xa5, 0x28], [0xa5, 0xa8],
        [0xa5, 0x52], [0xa5, 0x92], [0xa5, 0x22], [0xa5, 0xa2],
        [0xa5, 0x4a], [0xa5, 0x8a], [0xa5, 0x2a], [0xa5, 0xaa],
        [0x49, 0x55], [0x49, 0x95], [0x49, 0x25], [0x49, 0xa5],
        [0x49, 0x49], [0x49, 0x89], [0x49, 0x29], [0x49, 0xa9],
        [0x49, 0x52], [0x49, 0x92], [0x49, 0x22], [0x49, 0xa2],
        [0x49, 0x4a], [0x49, 0x8a], [0x49, 0x2a], [0x49, 0xaa],
        [0x89, 0x54], [0x89, 0x94], [0x89, 0x24], [0x89, 0xa4],
        [0x89, 0x48], [0x89, 0x88], [0x89, 0x28], [0x89, 0xa8],
        [0x89, 0x52], [0x89, 0x92], [0x89, 0x22], [0x89, 0xa2],
        [0x89, 0x4a], [0x89, 0x8a], [0x89, 0x2a], [0x89, 0xaa],
        [0x29, 0x55], [0x29, 0x95], [0x29, 0x25], [0x29, 0xa5],
        [0x29, 0x49], [0x29, 0x89], [0x29, 0x29], [0x29, 0xa9],
        [0x29, 0x52], [0x29, 0x92], [0x29, 0x22], [0x29, 0xa2],
        [0x29, 0x4a], [0x29, 0x8a], [0x29, 0x2a], [0x29, 0xaa],
        [0xa9, 0x54], [0xa9, 0x94], [0xa9, 0x24], [0xa9, 0xa4],
        [0xa9, 0x48], [0xa9, 0x88], [0xa9, 0x28], [0xa9, 0xa8],
        [0xa9, 0x52], [0xa9, 0x92], [0xa9, 0x22], [0xa9, 0xa2],
        [0xa9, 0x4a], [0xa9, 0x8a], [0xa9, 0x2a], [0xa9, 0xaa],
        [0x52, 0x55], [0x52, 0x95], [0x52, 0x25], [0x52, 0xa5],
        [0x52, 0x49], [0x52, 0x89], [0x52, 0x29], [0x52, 0xa9],
        [0x52, 0x52], [0x52, 0x92], [0x52, 0x22], [0x52, 0xa2],
        [0x52, 0x4a], [0x52, 0x8a], [0x52, 0x2a], [0x52, 0xaa],
        [0x92, 0x54], [0x92, 0x94], [0x92, 0x24], [0x92, 0xa4],
        [0x92, 0x48], [0x92, 0x88], [0x92, 0x28], [0x92, 0xa8],
        [0x92, 0x52], [0x92, 0x92], [0x92, 0x22], [0x92, 0xa2],
        [0x92, 0x4a], [0x92, 0x8a], [0x92, 0x2a], [0x92, 0xaa],
        [0x22, 0x55], [0x22, 0x95], [0x22, 0x25], [0x22, 0xa5],
        [0x22, 0x49], [0x22, 0x89], [0x22, 0x29], [0x22, 0xa9],
        [0x22, 0x52], [0x22, 0x92], [0x22, 0x22], [0x22, 0xa2],
        [0x22, 0x4a], [0x22, 0x8a], [0x22, 0x2a], [0x22, 0xaa],
        [0xa2, 0x54], [0xa2, 0x94], [0xa2, 0x24], [0xa2, 0xa4],
        [0xa2, 0x48], [0xa2, 0x88], [0xa2, 0x28], [0xa2, 0xa8],
        [0xa2, 0x52], [0xa2, 0x92], [0xa2, 0x22], [0xa2, 0xa2],
        [0xa2, 0x4a], [0xa2, 0x8a], [0xa2, 0x2a], [0xa2, 0xaa],
        [0x4a, 0x55], [0x4a, 0x95], [0x4a, 0x25], [0x4a, 0xa5],
        [0x4a, 0x49], [0x4a, 0x89], [0x4a, 0x29], [0x4a, 0xa9],
        [0x4a, 0x52], [0x4a, 0x92], [0x4a, 0x22], [0x4a, 0xa2],
        [0x4a, 0x4a], [0x4a, 0x8a], [0x4a, 0x2a], [0x4a, 0xaa],
        [0x8a, 0x54], [0x8a, 0x94], [0x8a, 0x24], [0x8a, 0xa4],
        [0x8a, 0x48], [0x8a, 0x88], [0x8a, 0x28], [0x8a, 0xa8],
        [0x8a, 0x52], [0x8a, 0x92], [0x8a, 0x22], [0x8a, 0xa2],
        [0x8a, 0x4a], [0x8a, 0x8a], [0x8a, 0x2a], [0x8a, 0xaa],
        [0x2a, 0x55], [0x2a, 0x95], [0x2a, 0x25], [0x2a, 0xa5],
        [0x2a, 0x49], [0x2a, 0x89], [0x2a, 0x29], [0x2a, 0xa9],
        [0x2a, 0x52], [0x2a, 0x92], [0x2a, 0x22], [0x2a, 0xa2],
        [0x2a, 0x4a], [0x2a, 0x8a], [0x2a, 0x2a], [0x2a, 0xaa],
        [0xaa, 0x54], [0xaa, 0x94], [0xaa, 0x24], [0xaa, 0xa4],
        [0xaa, 0x48], [0xaa, 0x88], [0xaa, 0x28], [0xaa, 0xa8],
        [0xaa, 0x52], [0xaa, 0x92], [0xaa, 0x22], [0xaa, 0xa2],
        [0xaa, 0x4a], [0xaa, 0x8a], [0xaa, 0x2a], [0xaa, 0xaa],
    ]

    @classmethod
    def interleave(cls, side, track, sector, wtf80t):
        return sector * 11 % cls.sectors

    @classmethod
    def decode(cls, stream):
        """decode MFM bit stream into bytes"""
        lookup = {word[0] << 8 | word[1]: i
                  for i, word in enumerate(cls.mfm_codes)}
        bs = []
        for j, i in enumerate(range(0, len(stream), 2)):
            w = ordw(stream[i:i + 2])
            if w == 0x2291:  # address mark
                b = 0xa1
            else:
                try:
                    b = lookup[w]
                except KeyError:
                    # NOTE: no such collisions in lookup table!
                    b = lookup[w | 0x0100]  # extra clock bit
            bs.append(b)
        return bs

    @classmethod
    def encode(cls, track):
        """encode SD track into MFM bit stream"""
        stream = []
        for b in track:
            w = cls.mfm_codes[b]
            stream.extend(w)
        return stream

    @classmethod
    def fix_clocks(cls, stream):
        """fix clock bits in stream (inline)"""
        for i in range(1, len(stream), 2):
            if stream[i] & 0x80:
                stream[i + 1] &= 0xfe


class HFEDisk:

    hfe_interface_mode = 7
    hfe_bit_rate = 250

    hfe_sd_encoding = 2
    hfe_dd_encoding = 0
    valid_encodings = [0, 2]

    def __init__(self, image):
        """create HFE disk from image"""
        self.header = image[0:512]
        self.lut = image[512:1024]
        self.trackdata = image[1024:]

        self.tracks, self.sides, self.encoding, self.ifmode = self.get_hfe_params(self.header)
        if self.encoding != HFEDisk.hfe_sd_encoding and self.encoding != HFEDisk.hfe_dd_encoding:
            raise HFEError("Invalid encoding")
        self.dd = self.encoding == HFEDisk.hfe_dd_encoding
        if self.ifmode != 7:
            raise HFEError("Invalid mode")

    @classmethod
    def get_hfe_params(cls, image):
        """checks if image is HFE image"""
        if image[:8] != b"HXCPICFE":
            raise HFEError("Not a HFE image")
        return image[9], image[10], image[11], image[16]

    def to_disk_image(self):
        """extract sector data from HFE image"""
        fmt = DDFormat if self.dd else SDFormat
        tracks = self.get_tracks()
        return self.extract_sectors(fmt, tracks)

    def get_tracks(self):
        """return list of decoded track data"""
        size = DDFormat.track_len if self.dd else SDFormat.track_len
        decode = DDFormat.decode if self.dd else SDFormat.decode
        chunks = chunk(self.trackdata, 256)
        side_0 = b"".join(chunks[0::2])
        side_1 = b"".join(chunks[1::2])
        tracks0 = chunk(decode(side_0), size)
        tracks1 = chunk(decode(side_1), size) if self.sides == 2 else []
        tracks1.reverse()
        return tracks0 + tracks1

    def extract_sectors(self, fmt, tracks):
        """extract sector data from list of track data"""
        sectors = []
        if len(tracks) != self.sides * self.tracks:
            raise HFEError("Invalid track count")
        assert len(tracks[0]) == fmt.track_len
        for j in range(self.sides * self.tracks):
            track = tracks[j]
            h0, h1 = 0, fmt.lvleadin  # leadin is track[h0:h1]
            track_sectors = {}
            for i in range(fmt.sectors):
                # pregap
                h0, h1 = h1, h1 + fmt.lvpregap
                # pregap at track[h0:h1]
                # ID address mark
                h0, h1 = h1, h1 + fmt.lvaddress_mark
                address_mark = track[h0:h1]
                assert address_mark == fmt.vaddress_mark
                # sector ID
                h0, h1 = h1, h1 + 6
                # track_id at track[h0]
                # side_id at track[h0 + 1]
                sector_id = track[h0 + 2]
                assert sector_id not in track_sectors
                # size_id at track[h0 + 3]
                # crc1 at track[h0 + 4:h0 + 6]
                # gap1
                h0, h1 = h1, h1 + fmt.lvgap1
                # gap1 at track[h0:h1]
                # data mark
                h0, h1 = h1, h1 + fmt.lvdata_mark
                data_mark = track[h0:h1]
                assert data_mark == fmt.vdata_mark
                # sector data
                h0, h1 = h1, h1 + 258
                track_sectors[sector_id] = track[h0:h0 + 256]
                # crc2 at track[h0 + 256:h0 + 258]
                # gap2
                h0, h1 = h1, h1 + fmt.lvgap2
                # gap2 at track[h0:h1]
            # leadout
            h0, h1 = h1, h1 + fmt.lvleadout
            assert h1 == len(track)
            sectors.extend(flatten([track_sectors[k] for k in sorted(track_sectors)]))
        return bytes(sectors)

    @classmethod
    def create(cls, image):
        """create HFE disk from disk image"""
        hfe = cls.create_image(image)
        return HFEDisk(hfe)

    @classmethod
    def create_image(cls, image):
        """create HFE image from disk image"""
        tracks = image[0x11]
        sides = image[0x12]
        dd = image[0x13] == 2
        protected = image[0x10] == b"P"

        header = cls.create_header(tracks, sides, dd, protected)
        lut = cls.create_lut(tracks, dd)

        fmt = DDFormat if dd else SDFormat
        side_0, side_1 = cls.create_tracks(tracks, sides, fmt, image)
        dummy = bytes(256) if not side_1 else None
        sandwich = b"".join([side_0[i:i+256] + (dummy or side_1[i:i+256])
                            for i in range(0, len(side_0), 256)])
        assert len(header) == len(lut) == 512
        return header + lut + sandwich

    @classmethod
    def create_header(cls, tracks, sides, dd, protected):
        """create HFE disk header"""
        info = (b"HXCPICFE" +
                bytes((0,  # revision
                       tracks, sides,
                       HFEDisk.hfe_dd_encoding if dd else HFEDisk.hfe_sd_encoding)) +
                rchrw(HFEDisk.hfe_bit_rate) +  # bit rate
                rchrw(0) +  # RPM (not used)
                bytes((HFEDisk.hfe_interface_mode, 1)) +
                rchrw(1) +  # LUT offset // 512
                (b"\x00" if protected else b"\xff"))
        return info + b"\xff" * (512 - len(info))

    @classmethod
    def create_lut(cls, tracks, dd):
        """create HFE LUT"""
        lut = b"".join([rchrw(0x31 * i + 2) +
                        (bytes((0xc0, 0x61)) if dd else bytes((0xb0, 0x61)))
                        for i in range(tracks)])
        return lut + b"\xff" * (512 - 4 * tracks)

    @classmethod
    def create_tracks(cls, tracks, sides, fmt, sectors):
        """create HFE tracks"""
        track_data = ([], [])
        for s in range(sides):
            for j in range(tracks):
                sector_data = []
                for i in range(fmt.sectors):
                    track_id = tracks - 1 - j if s else j  # 0 .. 39 39 .. 0
                    sector_id = fmt.interleave(s, j, i, tracks == 80)
                    offset = ((s * tracks + j) * fmt.sectors + sector_id) * 256
                    sector = [b for b in sectors[offset:offset + 256]]
                    addr = [track_id, s, sector_id, 0x01]
                    crc1 = crc16(0xffff, fmt.vaddress_mark + addr)
                    crc2 = crc16(0xffff, fmt.vdata_mark + sector)
                    sector_data.extend(
                        fmt.pregap +
                        fmt.address_mark +
                        fmt.encode(addr + crc1) +
                        fmt.gap1 +
                        fmt.data_mark +
                        fmt.encode(sector + crc2) +
                        fmt.gap2)
                fmt.fix_clocks(sector_data)
                track = fmt.leadin + sector_data + fmt.leadout
                track_data[s].append(bytes(track))
        track_data[1].reverse()
        return b"".join(track_data[0]), b"".join(track_data[1])


# main

def main(argv):
    import os.path
    import argparse
    import glob

    class GlobStore(argparse.Action):
        """argparse globbing for Windows platforms"""

        def __call__(self, parser, namespace, values, option_string=None):
            if os.name == "nt":
                names = [glob.glob(fn) if "*" in fn or "?" in fn else [fn]
                         for fn in values]
                values = [f for n in names for f in n]
            setattr(namespace, self.dest, values)

    args = argparse.ArgumentParser(
        description="xhm99: HFE image and file manipulation tool, v" + VERSION)
    cmd = args.add_mutually_exclusive_group(required=True)
    # xdm99 delegattion
    cmd.add_argument(
        "filename", type=str, nargs="?",
        help="HFE image filename")
    # conversion
    cmd.add_argument(
        "-T", "--to-hfe", action=GlobStore, dest="tohfe", nargs="+",
        metavar="<file>", help="convert disk images to HFE images")
    cmd.add_argument(
        "-F", "--from-hfe", "--to-dsk_id", action=GlobStore, dest="fromhfe", nargs="+",
        metavar="<file>", help="convert HFE images to disk images")
    cmd.add_argument(
        "-I", "--hfe-info", action=GlobStore, dest="hfeinfo", nargs="+",
        metavar="<file>", help="show basic information about HFE images")
    cmd.add_argument(
        "--dump", action=GlobStore, dest="dump", nargs="+",
        metavar="<file>", help="dump raw decoded HFE data")
    # general options
    args.add_argument(
        "-o", "--output", dest="output", metavar="<file>",
        help="set output filename")
    opts, other = args.parse_known_args(argv)

    result = []
    try:
        # delegate to xdm99
        if opts.filename:
            import xdm99 as xdm
            try:
                image = readdata(opts.filename, "rb")
                disk = HFEDisk(image).to_disk_image()
            except IOError:
                disk = "\x00"
            if opts.output:
                other += ["-o", opts.filename]
            barename = os.path.splitext(os.path.basename(opts.filename))[0]
            result = xdm.main([barename[:10].upper()] + other, disk)
            if isinstance(result, tuple):  # disk modified?
                dsk, _ = result
                hfe = HFEDisk.create_image(dsk)
                result = (hfe, opts.filename)
        # HFE/DSK conversion
        for name in opts.fromhfe or []:
            image = readdata(name, "rb")
            dsk = HFEDisk(image).to_disk_image()
            barename = os.path.splitext(os.path.basename(name))[0]
            result.append((dsk, barename + ".dsk_id"))
        for name in opts.tohfe or []:
            image = readdata(name, "rb")
            hfe = HFEDisk.create_image(image)
            barename = os.path.splitext(os.path.basename(name))[0]
            result.append((hfe, barename + ".hfe"))
        for name in opts.dump or []:
            image = readdata(name, "rb")
            hfe = HFEDisk(image)
            tracks = hfe.get_tracks()
            data = "".join([chr(b) for b in flatten(tracks)])
            barename = os.path.splitext(os.path.basename(name))[0]
            result.append((data, barename + ".dump"))
        # image analysis
        for name in opts.hfeinfo or []:
            image = readdata(name, "rb")
            tracks, sides, enc, ifmode = HFEDisk.get_hfe_params(image)
            sys.stdout.write("Tracks: %d\nSides: %d\n" % (tracks, sides))
            sys.stdout.write("Encoding: %d\nInterface mode: %d\n" % (enc, ifmode))
            if enc not in HFEDisk.valid_encodings or ifmode != HFEDisk.hfe_interface_mode:
                sys.stdout.write("Not a suitable HFE image for the TI 99\n")
                return 1
    except (IOError, HFEError) as e:
        sys.exit("Error: " + str(e))

    # write result
    if isinstance(result, tuple):
        result = [result]
    for data, name in result:
        outname = opts.output or name
        try:
            writedata(outname, data, "wb")
        except IOError as e:
            sys.exit("Error: " + str(e))

    # return status
    return 0


if __name__ == "__main__":
    status = main(sys.argv[1:])
    sys.exit(status)
