"""seg_qc_tool package."""

from importlib import import_module


def main() -> None:
    module = import_module("seg_qc_tool.main")
    module.main()

__all__ = ["main"]
