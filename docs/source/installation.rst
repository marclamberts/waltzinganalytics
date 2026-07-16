Installation
============

From source (this repository):

.. code-block:: bash

   git clone https://github.com/marclamberts/waltzinganalytics.git
   cd waltzinganalytics
   pip install -e .

For running the test suite or building the docs:

.. code-block:: bash

   pip install -e ".[dev]"    # pytest
   pip install -e ".[docs]"   # sphinx, furo, myst-parser

Requirements
------------

- Python 3.9+
- pandas >= 1.5

Input data
----------

``opta_setpieces`` reads **Opta / Stats Perform F24** match event JSON
exports -- the feed with top-level ``matchDetails`` and ``event`` keys,
where each event carries a ``typeId`` and a list of ``qualifier`` objects.
This is the standard "F24" feed used across most Opta-powered football data
providers.
