"""ROS 2 のメッセージを CDR(XCDR1)形式で読み書きする最小限の実装。

ROS 2 は DDS 由来の CDR でメッセージをバイト列にする。zenoh-bridge-ros2dds も rmw_zenoh も
この CDR のバイト列をそのまま Zenoh のペイロードとして流すので、Zenoh 側でも同じ形式で読み書きすれば
ROS 2 のノードとやり取りできる。

形式の要点:
  - 先頭 4 バイトはカプセル化ヘッダー。00 01 00 00 ならリトルエンディアンの CDR
  - 以降の各値は、ヘッダーの直後を 0 とした位置で、自分のサイズの倍数にそろえて(アラインして)置く
  - string は「終端の NUL を含む長さ(uint32)」+「UTF-8 の本体」+「NUL」

ここでは std_msgs/msg/String と geometry_msgs/msg/Twist だけを実装している。
ほかの型を扱うなら、rosbags や pycdr2 などのライブラリを使うと楽になる。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

CDR_LE_HEADER = b"\x00\x01\x00\x00"  # CDR, little endian
CDR_BE_HEADER = b"\x00\x00\x00\x00"  # CDR, big endian


class CdrWriter:
    def __init__(self) -> None:
        self._buf = bytearray()

    def _align(self, size: int) -> None:
        self._buf += b"\x00" * ((-len(self._buf)) % size)

    def uint32(self, value: int) -> None:
        self._align(4)
        self._buf += struct.pack("<I", value)

    def float64(self, value: float) -> None:
        self._align(8)
        self._buf += struct.pack("<d", value)

    def string(self, value: str) -> None:
        raw = value.encode("utf-8") + b"\x00"
        self.uint32(len(raw))
        self._buf += raw

    def to_bytes(self) -> bytes:
        return CDR_LE_HEADER + bytes(self._buf)


class CdrReader:
    def __init__(self, data: bytes) -> None:
        if len(data) < 4:
            raise ValueError("CDR データが短すぎます")
        header = bytes(data[:4])
        if header[:2] == CDR_LE_HEADER[:2]:
            self._endian = "<"
        elif header[:2] == CDR_BE_HEADER[:2]:
            self._endian = ">"
        else:
            raise ValueError(f"未対応のカプセル化ヘッダーです: {header.hex(' ')}")
        self._data = bytes(data[4:])
        self._pos = 0

    def _align(self, size: int) -> None:
        self._pos += (-self._pos) % size

    def _unpack(self, fmt: str, size: int):
        self._align(size)
        (value,) = struct.unpack_from(self._endian + fmt, self._data, self._pos)
        self._pos += size
        return value

    def uint32(self) -> int:
        return self._unpack("I", 4)

    def float64(self) -> float:
        return self._unpack("d", 8)

    def string(self) -> str:
        length = self.uint32()
        raw = self._data[self._pos : self._pos + length]
        self._pos += length
        return raw.rstrip(b"\x00").decode("utf-8")


# ---- std_msgs/msg/String -------------------------------------------------


def encode_string(text: str) -> bytes:
    w = CdrWriter()
    w.string(text)
    return w.to_bytes()


def decode_string(data: bytes) -> str:
    return CdrReader(data).string()


# ---- geometry_msgs/msg/Twist ---------------------------------------------


@dataclass
class Twist:
    linear_x: float = 0.0
    linear_y: float = 0.0
    linear_z: float = 0.0
    angular_x: float = 0.0
    angular_y: float = 0.0
    angular_z: float = 0.0


def encode_twist(t: Twist) -> bytes:
    w = CdrWriter()
    for v in (t.linear_x, t.linear_y, t.linear_z, t.angular_x, t.angular_y, t.angular_z):
        w.float64(v)
    return w.to_bytes()


def decode_twist(data: bytes) -> Twist:
    r = CdrReader(data)
    return Twist(*(r.float64() for _ in range(6)))
