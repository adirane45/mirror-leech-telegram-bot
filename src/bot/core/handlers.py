"""Backward-compatible handler bootstrap entrypoint."""

from importlib import import_module
from typing import Callable, cast


def add_handlers() -> None:
	core_handlers_module = import_module("bot.core.core_handlers")
	add_handlers_fn = cast(Callable[[], None], getattr(core_handlers_module, "add_handlers"))
	add_handlers_fn()


__all__ = ["add_handlers"]
