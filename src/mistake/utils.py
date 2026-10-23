import re
import sys

RUNTIME_USE_VULKAN = "--vulkan" in sys.argv

def is_latin_alph(c: str) -> bool:
    return re.fullmatch(r"[a-zA-Z]", c) is not None


def to_decimal_seconds(seconds: float):
    return seconds * 0.864


def from_decimal_seconds(seconds: float):
    return seconds / 0.864

ansi_color = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "black": "\033[30m",
    "reset": "\033[0m"
}

def print_color(color: str, *args):
    print(f"{ansi_color[color]}{' '.join(map(str, args))}{ansi_color['reset']}")
