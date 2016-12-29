Installation
============

For end users:

.. code-block:: sh

   pip install pybel

For the latest and greatest:

.. code-block:: sh

   pip install git+https://github.com/pybel/pybel.git@develop

For development:

.. code-block:: sh

   git clone https://github.com/pybel/pybel.git@develop
   cd pybel
   pip install -e .

Caveats
-------

PyBEL extends the :code:`networkx` for its core data structure. Many of the graphical aspects of :code:`networkx`
depend on :code:`matplotlib`, which is an optional dependency.
