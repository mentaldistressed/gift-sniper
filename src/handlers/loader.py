import pkgutil, importlib
from pathlib import Path
from typing import Generator

from aiogram import Router


def get_all_routers() -> Generator[tuple[Router, str], None, None]:
    for module_info in pkgutil.iter_modules([str(Path(__file__).parent)]):
        module = importlib.import_module(f"src.handlers.{module_info.name}")
        if hasattr(module, 'router'):
            yield module.router, module.rname