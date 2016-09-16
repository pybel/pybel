# PyBEL

PyBEL provides tools for loading and parsing Biological Expression Language (BEL) files.

```python
import pybel
import networkx

url = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
g = pybel.parse_from_url(url)

networkx.draw(g)
```

## Installation

### Development

For developers, this repository can be cloned and locally installed with pip using the following commands:

```bash
git clone https://github.com/cthoyt/pybel.git
cd pybel
pip install -e .
```

### Usage

In the future, this repository will be open to the public for use. Installation will be as easy as:

```bash
pip install pybel
```
