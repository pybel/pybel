Cache
=====

Manager API
-----------

The BaseManager takes care of building and maintaining the connection to the database via SQLAlchemy.

.. autoclass:: pybel.manager.BaseManager
    :members:

The Manager collates multiple groups of functions for interacting with the database. For sake of code clarity, they
are separated across multiple classes that are documented below.

.. autoclass:: pybel.manager.Manager
    :members:
    :show-inheritance:

Manager Components
------------------

.. autoclass:: pybel.manager.NetworkManager
    :members:

.. autoclass:: pybel.manager.QueryManager
    :members:

Database Models
---------------

.. automodule:: pybel.manager.models
    :members:
