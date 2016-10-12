Contributing
============

1. Get the code. Either clone/fork/branch from GitHub using :code:`git` or unzip your archive.

.. code-block:: sh

    git clone https://github.com/cthoyt/pybel.git
	

2. :code:`cd` into your directory

.. code-block:: sh

    cd pybel


3. Install with :code:`pip`. :code:`-e` means that it's editable, and your changes will be reflected in your
installation. This is only necessary if you're changing code.

.. code-block:: sh

   pip install -e .
	
	
4. Make contributions. This project should be well tested, so write unit tests in the :code:`tests/` directory and run.

5. Check that all tests are passing and code coverage is good with :code:`tox` before committing.

.. code-block:: sh

   tox
