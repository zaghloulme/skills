#!/usr/bin/env python3
"""
Daily todo thermal printer (print_v7 style)
Reads a YAML task list and prints to a 72mm ESC/POS printer over TCP.

Usage:
  python3 print-daily-todos.py
  python3 print-daily-todos.py --file daily-todos/2026-06-13.yaml
  python3 print-daily-todos.py --ip 10.0.1.111 --port 9100
  python3 print-daily-todos.py --save
"""

from __future__ import annotations

import argparse
import socket
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TODAY = datetime.now().strftime("%Y-%m-%d")
DEFAULT_YAML = SCRIPT_DIR / "daily-todos" / f"{TODAY}.yaml"

PRINTER_IP = "10.0.1.111"
PRINTER_PORT = 9100
W = 40


class EscPosBuilder:
    def __init__(self) -> None:
        self.out = bytearray()

    def b(self, *codes: int) -> None:
        self.out.extend(codes)

    def s(self, text: str) -> None:
        safe = (
            text.replace("\u2014", " - ")
            .replace("\u2013", "-")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
        )
        self.out.extend(safe.encode("ascii", errors="replace"))

    def nl(self) -> None:
        self.b(0x0A)

    def feed(self, n: int = 1) -> None:
        self.b(0x1B, 0x64, n)

    def bold(self, on: bool = True) -> None:
        self.b(0x1B, 0x45, 1 if on else 0)

    def size(self, w: int = 1, h: int = 1) -> None:
        self.b(0x1D, 0x21, ((h - 1) << 4) | (w - 1))

    def invert(self, on: bool = True) -> None:
        self.b(0x1D, 0x42, 1 if on else 0)

    def cut(self) -> None:
        self.b(0x1D, 0x56, 0x42, 5)

    def ctr(self, text: str, w: int = 1, h: int = 1, em: bool = False) -> None:
        self.b(0x1B, 0x61, 1)
        self.size(w, h)
        if em:
            self.bold(True)
            self.s(text)
            self.bold(False)
        else:
            self.s(text)
        self.size(1, 1)
        self.nl()

    def hrule(self, char: str = "=") -> None:
        self.b(0x1B, 0x61, 1)
        self.s(char * W)
        self.nl()

    def inv_ctr(self, text: str) -> None:
        self.b(0x1B, 0x61, 1)
        self.invert(True)
        self.s(text.center(W))
        self.invert(False)
        self.nl()

    def left(self, text: str) -> None:
        self.b(0x1B, 0x61, 0)
        self.s(text[:W])
        self.nl()

    def task(self, text: str) -> None:
        prefix = "[ ] "
        indent = " " * len(prefix)
        words = text.split()
        if not words:
            self.left(prefix)
            return
        line = words[0]
        for word in words[1:]:
            candidate = f"{line} {word}"
            if len(prefix + candidate) <= W:
                line = candidate
            else:
                self.left(prefix + line)
                prefix = indent
                line = word
        self.left(prefix + line)

    def bytes(self) -> bytes:
        return bytes(self.out)


def _parse_scalar(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    data: dict = {"categories": []}
    current_cat: dict | None = None
    section: str | None = None

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- name:"):
            current_cat = {"name": _parse_scalar(stripped.split(":", 1)[1]), "tasks": []}
            data.setdefault("categories", []).append(current_cat)
            section = "category"
            continue

        if stripped.startswith("- ") and section == "tasks" and current_cat is not None:
            current_cat["tasks"].append(_parse_scalar(stripped[2:]))
            continue

        if ":" not in stripped:
            continue

        key, val = stripped.split(":", 1)
        key = key.strip()
        val = _parse_scalar(val)

        if key == "categories":
            section = "categories"
            data["categories"] = []
            current_cat = None
            continue

        if key == "tasks":
            section = "tasks"
            continue

        if key == "name" and current_cat is not None:
            current_cat["name"] = val
            continue

        section = None
        data[key] = val

    return data


def generate_daily_todos(data: dict) -> bytes:
    e = EscPosBuilder()
    e.b(0x1B, 0x40)

    e.ctr("TODAY", 2, 2, em=True)
    date_str = data.get("date", "")
    if date_str:
        e.ctr(date_str)
    e.feed()
    e.hrule()
    e.feed()

    for cat in data.get("categories") or []:
        name = cat.get("name", "Tasks")
        e.inv_ctr(f" {name} ")
        e.feed()
        for task in cat.get("tasks") or []:
            e.task(str(task))
        e.feed()

    e.hrule("-")
    e.ctr("one at a time")
    e.feed(3)
    e.cut()
    return e.bytes()


def send_to_printer(data: bytes, ip: str, port: int) -> bool:
    print(f"{len(data)} bytes -> {ip}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip, port))
        sock.sendall(data)
        sock.close()
        print("Sent.")
        return True
    except OSError as e:
        print(f"Failed: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Print daily todos to thermal printer")
    parser.add_argument("--file", type=Path, default=DEFAULT_YAML)
    parser.add_argument("--ip", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    yaml_path = args.file
    if not yaml_path.is_absolute() and (SCRIPT_DIR / yaml_path).exists():
        yaml_path = SCRIPT_DIR / yaml_path

    if not yaml_path.exists():
        print(f"File not found: {yaml_path}", file=sys.stderr)
        return 1

    data = load_yaml(yaml_path)
    ip = args.ip or data.get("printer_ip") or PRINTER_IP
    port = args.port or PRINTER_PORT
    receipt = generate_daily_todos(data)
    out_path = Path("/tmp/daily-todos.bin")

    if args.save:
        out_path.write_bytes(receipt)
        print(f"Saved {len(receipt)} bytes to {out_path}")
        return 0

    ok = send_to_printer(receipt, ip, port)
    out_path.write_bytes(receipt)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
