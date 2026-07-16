Installation
============

From source (this repository):

.. code-block:: bash

   git clone https://github.com/marclamberts/waltzinganalytics.git
   cd waltzinganalytics
   pip install -e .

For the plotting helpers (:mod:`opta_setpieces.viz`, the :ref:`gallery`),
running the test suite, or building the docs:

.. code-block:: bash

   pip install -e ".[viz]"    # matplotlib, mplsoccer -- pitch plots
   pip install -e ".[dev]"    # pytest
   pip install -e ".[docs]"   # sphinx, pydata-sphinx-theme, sphinx-gallery, viz

Requirements
------------

- Python 3.9+
- pandas >= 1.5
- matplotlib >= 3.6 and mplsoccer >= 1.2 (only for :mod:`opta_setpieces.viz`)

Input data
----------

``opta_setpieces`` reads **Opta / Stats Perform F24** match event JSON
exports -- the feed with top-level ``matchDetails`` and ``event`` keys,
where each event carries a ``typeId`` and a list of ``qualifier`` objects.
This is the standard "F24" feed used across most Opta-powered football data
providers.
