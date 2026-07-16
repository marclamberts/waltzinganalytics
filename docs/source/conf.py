from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

project = "wa-setpieces"
copyright = "2026, Waltzing Analytics"
author = "Waltzing Analytics"

try:
    from wa_setpieces import __version__ as release
except ImportError:
    release = "0.1.0"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_gallery.gen_gallery",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
}

# -- sphinx-gallery: renders examples_gallery/*.py into docs/source/gallery,
# executing each script and capturing its matplotlib figures + printed
# output, mplsoccer-style. ------------------------------------------------
sphinx_gallery_conf = {
    "examples_dirs": "../../examples_gallery",
    "gallery_dirs": "gallery",
    "filename_pattern": r"plot_.*\.py",
    "remove_config_comments": True,
    "download_all_examples": False,
    "within_subsection_order": "FileNameSortKey",
    "backreferences_dir": None,
    "image_scrapers": ("matplotlib",),
    "matplotlib_animations": False,
    "min_reported_time": 999999,  # don't print per-example run times
}

# -- Theme: pydata-sphinx-theme, same family mplsoccer's docs use ---------
html_theme = "pydata_sphinx_theme"
html_title = "wa-setpieces"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "github_url": "https://github.com/marclamberts/waltzinganalytics",
    "show_prev_next": False,
    "navigation_with_keys": False,
    "icon_links": [],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "secondary_sidebar_items": ["page-toc"],
    "footer_start": ["copyright"],
    "footer_end": [],
    "pygments_light_style": "tango",
    "pygments_dark_style": "monokai",
}

html_context = {
    "default_mode": "auto",
}

html_sidebars = {
    "**": ["sidebar-nav-bs"],
}
