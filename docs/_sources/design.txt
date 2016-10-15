Design Choices
==============

Dealing with Dirty Namespaces
-----------------------------

While it's not good practice to leave unqualified elements in a BEL document, sometimes there isn't a proper
namespace at the time. There's a setting in the BELGraph for these occassions.

.. code-block:: python

    >>> from pybel import BELGraph
    >>> g = BELGraph(lenient=True)
    >>> g.parse_from_path('~/Desktop/my_document.bel')

For now, the namespace for naked names is assigned the sentinel value from pybel.parser.parse_identifier.DIRTY.

Here are some suggestions on how to find an appropriate namespace:

- Search the namespaces provided by Selventa, BELIEF, and other sources
- Write your own :code:`belns` file
- Use pybel-tools to convert OWL Ontologies to :code:`belns` file


