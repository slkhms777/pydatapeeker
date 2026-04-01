"""Loader registry and public load entry point."""

from pydatapeekr.loaders.core import load_file, register_loader

from pydatapeekr.loaders import csv_loader, json_loader, numpy_loader, parquet_loader, pickle_loader, yaml_loader

__all__ = [
    "load_file",
    "register_loader",
    "csv_loader",
    "json_loader",
    "numpy_loader",
    "parquet_loader",
    "pickle_loader",
    "yaml_loader",
]
