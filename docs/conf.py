"""Sphinx configuration."""
project = "OpenWx"
author = "Jason Washburn"
copyright = "2022, Jason Washburn"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
