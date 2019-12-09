# -*- coding: utf-8 -*-

"""Constants for PyBEL-Jupyter."""

from ...constants import ABUNDANCE, BIOPROCESS, COMPLEX, COMPOSITE, GENE, MIRNA, PATHOLOGY, PROTEIN, REACTION, RNA

#: The color map defining the node colors in visualization
DEFAULT_COLOR_MAP = {
    PROTEIN: "#1F77B4",
    PATHOLOGY: "#FF7F0E",
    BIOPROCESS: "#2CA02C",
    MIRNA: "#D62728",
    COMPLEX: "#98DF8A",
    COMPOSITE: "#9467BD",
    REACTION: "#000000",
    GENE: "#FFBB78",
    ABUNDANCE: "#AEC7E8",
    RNA: "#FF9896",
}
