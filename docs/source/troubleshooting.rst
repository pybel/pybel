Troubleshooting
===============

Common problems and questions will be posted here.


Encoding Issues
~~~~~~~~~~~~~~~

Sometimes, Windows computers stick a weird unicode object :code:`\u2013` at the beginning of files. This makes the
function :py:func:`pybel.parser.utils.sanitize_file_lines` have a problem. The solution, when loading a BEL script
via :py:func:`pybel.from_path` is to use the :code:`encodings` keyword argument to specify the right encoding.
The default is :code:`utf-8` because this is the most common, but when this error happens, set it explicitly to
:code:`utf_8_sig`. More specific documentation is available in the Inputs and Outputs page.

Scenario
********

.. code-block:: python

    >>> import pybel
    >>> graph = pybel.from_path('~/Desktop/small_corpus.bel')

    UnicodeDecodeError Traceback (most recent call last) <ipython-input-11-99f2a76596b1> in <module>()
    7 ad = pybel.from_pickle(path_2_AD_pickle)
    8 else:
    ----> 9 ad = pybel.from_path(path_2_AD_bel)
    10 pybel.to_pickle(ad, path_2_AD_pickle)

    C:\Users\s8310253\AppData\Local\Continuum\Anaconda3420\lib\site-packages\pybel\graph.py in from_path(path, **kwargs)
    61 log.info('Loading from path: %s', path)
    62 with open(os.path.expanduser(path)) as f:
    ---> 63 return BELGraph(lines=f, **kwargs)
    64
    65

    C:\Users\s8310253\AppData\Local\Continuum\Anaconda3420\lib\site-packages\pybel\graph.py in __init__(self, lines, context, lenient, definition_cache_manager, log_stream, *attrs, **kwargs)
    102
    103 if lines is not None:
    --> 104 self.parse_lines(lines, context, lenient,
    --> definition_cache_manager, log_stream)
    105
    106 def parse_lines(self, lines, context=None, lenient=False, definition_cache_manager=None, log_stream=None):

    C:\Users\s8310253\AppData\Local\Continuum\Anaconda3420\lib\site-packages\pybel\graph.py in parse_lines(self, lines, context, lenient, definition_cache_manager, log_stream)
    125 self.context = context
    126
    --> 127 docs, defs, states =
    --> split_file_to_annotations_and_definitions(lines)
    128
    129 if isinstance(definition_cache_manager, DefinitionCacheManager):

    C:\Users\s8310253\AppData\Local\Continuum\Anaconda3420\lib\site-packages\pybel\parser\utils.py in split_file_to_annotations_and_definitions(file)
    49 def split_file_to_annotations_and_definitions(file):
    50 """Enumerates a line iterable and splits into 3 parts"""
    ---> 51 content = list(sanitize_file_lines(file))
    52
    53 end_document_section = 1 + max(j for j, (i, l) in enumerate(content) if l.startswith('SET DOCUMENT'))

    C:\Users\s8310253\AppData\Local\Continuum\Anaconda3420\lib\site-packages\pybel\parser\utils.py in sanitize_file_lines(f)
    16 it = iter(it)
    17
    ---> 18 for line_number, line in it:
    19 if line.endswith('\\'):
    20 log.log(4, 'Multiline quote starting on line: %d', line_number)

    C:\Users\s8310253\AppData\Local\Continuum\Anaconda3420\lib\site-packages\pybel\parser\utils.py in <genexpr>(.0)
    12 def sanitize_file_lines(f):
    13 """Enumerates a line iterator and returns the pairs of (line number, line) that are cleaned"""
    ---> 14 it = (line.strip() for line in f)
    15 it = filter(lambda i_l: i_l[1] and not i_l[1].startswith('#'), enumerate(it, start=1))
    16 it = iter(it)

    C:\Users\s8310253\AppData\Local\Continuum\Anaconda3420\lib\encodings\cp1252.py in decode(self, input, final)
    21 class IncrementalDecoder(codecs.IncrementalDecoder):
    22 def decode(self, input, final=False):
    ---> 23 return
    ---> codecs.charmap_decode(input,self.errors,decoding_table)[0]
    24
    25 class StreamWriter(Codec,codecs.StreamWriter):

    UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 4668: character maps to <undefined>

Solution
********

.. code-block:: python

    >>> import pybel
    >>> graph = pybel.from_path('~/Desktop/small_corpus.bel', encoding='utf_8_sig')
    >>> # Success!