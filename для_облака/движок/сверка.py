"""Точка входа:  python -m движок.сверка <документ или папка> --каталог <файл>"""
import sys

from .tz_engine.cli import main

if __name__ == "__main__":
    sys.exit(main())
