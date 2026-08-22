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

# -- Theme: sphinx_rtd_theme -- the classic always-visible left nav tree,
# same theme mplsoccer's own docs use (confirmed against their built HTML:
# the "wy-nav-side" class is this theme's signature, not pydata-sphinx-theme's
# top-navbar layout this project used before). ----------------------------
html_theme = "sphinx_rtd_theme"
html_title = "wa-setpieces"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    # Waltzing Analytics navy, not this theme's default teal -- see custom.css
    # for the rest of the WA reskin (accent color, links, code blocks).
    "style_nav_header_background": "#14202B",
}
