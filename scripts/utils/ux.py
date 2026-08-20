"""
scripts/utils/ux.py
-------------------
Módulo compartilhado de UX para terminal do PulseRatingsBrasil.
Fornece cores ANSI, ícones, helpers visuais, logger colorido e CLI comum.
Adaptado do PulseFlat (PulseDataLabs/PulseFlat).
"""

import argparse
import logging
import os
import sys
from collections.abc import Iterator

# ── Detecção de Ambiente ──────────────────────────────────────────────
_CI = os.environ.get("CI", "")
_NO_COLOR = os.environ.get("NO_COLOR", "")
_TERM = os.environ.get("TERM", "")

IS_TTY = sys.stdout.isatty()
USE_COLOR = (IS_TTY or bool(_CI)) and not _NO_COLOR and _TERM != "dumb"

# Detecção de suporte a Unicode
# Verifica encoding do stdout, LANG/LC_ALL, ou assume True se for TTY
_utf_env = any(
    "UTF" in os.environ.get(v, "").upper().replace("-", "") for v in ("LC_ALL", "LC_CTYPE", "LANG")
)
try:
    _utf_stdout = "UTF" in (sys.stdout.encoding or "").upper().replace("-", "")
except Exception:
    _utf_stdout = False

USE_UNICODE = _utf_stdout or _utf_env or (IS_TTY and _utf_stdout)


def configure(*, use_color: bool | None = None, use_unicode: bool | None = None) -> None:
    global USE_COLOR, USE_UNICODE, ICON
    if use_color is not None:
        USE_COLOR = use_color
    if use_unicode is not None:
        USE_UNICODE = use_unicode
    if use_unicode is not None:
        _rebuild_icons()


def _rebuild_icons() -> None:
    global ICON
    u = USE_UNICODE
    ICON.clear()
    ICON.update(
        {
            "success": "✔" if u else "[OK]",
            "fail": "✖" if u else "[FAIL]",
            "warn": "⚠" if u else "[WARN]",
            "info": "ℹ" if u else "[INFO]",
            "skip": "⏭" if u else "[SKIP]",
            "file": "📄" if u else "[FILE]",
            "refresh": "🔄" if u else "[REFRESH]",
            "clean": "🧹" if u else "[CLEAN]",
            "chart": "📊" if u else "[CHART]",
            "clock": "⏱" if u else "[TIME]",
            "folder": "📁" if u else "[DIR]",
            "search": "🔍" if u else "[SEARCH]",
            "gear": "⚙" if u else "[GEAR]",
            "rocket": "🚀" if u else "[ROCKET]",
        }
    )


# ── Códigos ANSI Core ─────────────────────────────────────────────────
def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def bold(t: str) -> str:
    return _c("1", t)


def dim(t: str) -> str:
    return _c("2", t)


def red(t: str) -> str:
    return _c("31", t)


def green(t: str) -> str:
    return _c("32", t)


def yellow(t: str) -> str:
    return _c("33", t)


def blue(t: str) -> str:
    return _c("34", t)


def magenta(t: str) -> str:
    return _c("35", t)


def cyan(t: str) -> str:
    return _c("36", t)


def white(t: str) -> str:
    return _c("97", t)


def b_red(t: str) -> str:
    return _c("1;31", t)


def b_green(t: str) -> str:
    return _c("1;32", t)


def b_yellow(t: str) -> str:
    return _c("1;33", t)


def b_blue(t: str) -> str:
    return _c("1;34", t)


def b_magenta(t: str) -> str:
    return _c("1;35", t)


def b_cyan(t: str) -> str:
    return _c("1;36", t)


# ── Ícones ────────────────────────────────────────────────────────────
ICON: dict[str, str] = {}
_rebuild_icons()

GROUP_ICON = {
    "anbima": "🟡",
    "b3": "🔵",
    "bcb": "🟢",
    "cvm": "🟣",
    "ibge": "🔴",
    "ratings": "⚪",
    "misc": "🟤",
}

GROUP_COLOR = {
    "anbima": yellow,
    "b3": cyan,
    "bcb": green,
    "cvm": magenta,
    "ibge": red,
    "ratings": white,
    "misc": blue,
}


# ── Helpers Visuais ───────────────────────────────────────────────────
def line(char: str = "─", width: int = 64) -> str:
    return dim(char * width)


def progress_bar(done: int, total: int, width: int = 24) -> str:
    if total == 0:
        return dim("(sem total)")
    filled = int(width * done / total)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(100 * done / total)
    return cyan(bar) + dim(f"  {pct:3d}%  ({done}/{total})")


def spinner(frames: str = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏") -> Iterator[str]:
    i = 0
    while True:
        yield frames[i % len(frames)]
        i += 1


# ── Funções de Status ─────────────────────────────────────────────────
def print_start(msg: str, icon: str = "refresh") -> None:
    print(f"  {ICON[icon]}  {msg}")


def print_done(msg: str, elapsed: float | None = None, icon: str = "success") -> None:
    time_str = f"  {dim(f'{elapsed:.1f}s')}" if elapsed is not None else ""
    print(f"  {green(ICON[icon])}  {msg}{time_str}")


def print_fail(msg: str, elapsed: float | None = None, icon: str = "fail") -> None:
    time_str = f"  {dim(f'{elapsed:.1f}s')}" if elapsed is not None else ""
    print(f"  {red(ICON[icon])}  {msg}{time_str}")


def print_warn(msg: str, icon: str = "warn") -> None:
    print(f"  {yellow(ICON[icon])}  {msg}")


def print_skip(msg: str, icon: str = "skip") -> None:
    print(f"  {dim(ICON[icon])}  {msg}")


def print_info(msg: str, icon: str = "info") -> None:
    print(f"  {cyan(ICON[icon])}  {msg}")


def print_table(
    rows: list[tuple],
    headers: list[str],
    title: str = "",
) -> None:
    if not rows:
        return

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    total_w = sum(col_widths) + len(headers) * 3 + 1

    sep = dim("─" * total_w)
    head = dim("│") + dim("│").join(f" {bold(h):{w}} " for h, w in zip(headers, col_widths)) + dim("│")

    if title:
        print()
        print(f"  {bold(title)}")
        print(sep)
        print(head)
        print(sep)
    else:
        print()
        print(head)
        print(sep)

    for row in rows:
        line_str = dim("│") + dim("│").join(f" {str(c):{w}} " for c, w in zip(row, col_widths)) + dim("│")
        print(line_str)
    print(sep)
    print()


def print_summary(
    title: str,
    total: int,
    success: int,
    failed: int,
    skipped: int = 0,
    elapsed: float = 0.0,
    details: list[tuple[str, str, str]] | None = None,
) -> None:
    details = details or []
    print()
    print(line("═"))
    print(f"  {bold(title)}")
    print(line("─"))

    parts = [
        f"  {bold('Total')}: {white(str(total))}",
        b_green(f"✔ {success} ok"),
    ]
    if failed:
        parts.append(b_red(f"✖ {failed} erro(s)"))
    else:
        parts.append(dim("0 erros"))
    if skipped:
        parts.append(yellow(f"⏭ {skipped} pulado(s)"))
    parts.append(cyan(f"⏱ {elapsed:.1f}s"))
    print("  │  ".join(parts))

    if details:
        print()
        print(dim("  Detalhes:"))
        for icon_key, label, value in details:
            icon_char = ICON.get(icon_key, "•")
            print(f"    {icon_char}  {label}: {white(value)}")

    print(line("═"))
    print()


# ── Logger Colorido ────────────────────────────────────────────────────
class ColorLogger:
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)
            self._logger.propagate = False

    def _log(self, level: int, msg: str, color_fn) -> None:
        if USE_COLOR:
            self._logger.log(level, color_fn(msg))
        else:
            self._logger.log(level, msg)

    def debug(self, msg: str) -> None:
        self._log(logging.DEBUG, msg, dim)

    def info(self, msg: str) -> None:
        self._log(logging.INFO, msg, white)

    def success(self, msg: str) -> None:
        self._log(logging.INFO, msg, green)

    def warning(self, msg: str) -> None:
        self._log(logging.WARNING, msg, yellow)

    def error(self, msg: str) -> None:
        self._log(logging.ERROR, msg, red)


# ── CLI Helpers ───────────────────────────────────────────────────────
def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--quiet", "-q", action="store_true", help="Suprime output não-essencial")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostra output detalhado")
    parser.add_argument("--no-color", action="store_true", help="Desabilita cores ANSI")
    parser.add_argument("--dry-run", action="store_true", help="Simula execução sem gravar arquivos")


def apply_common_args(args: argparse.Namespace) -> None:
    global USE_COLOR
    if args.no_color:
        USE_COLOR = False
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)


# ── Banner e Seção ────────────────────────────────────────────────────
def banner(title: str, subtitle: str = "") -> None:
    print()
    print(line("═"))
    print(f"  {bold(title)}")
    if subtitle:
        print(f"  {dim(subtitle)}")
    print(line("═"))
    print()


def section(title: str, icon: str = "gear") -> None:
    print()
    print(line())
    print(f"  {ICON[icon]}  {bold(title)}")
    print(line())
    print()
