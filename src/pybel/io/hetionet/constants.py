# -*- coding: utf-8 -*-

"""Constants for Hetionet."""

from ...dsl import Abundance, BiologicalProcess, Pathology, Population, Protein, Rna
from ...struct import BELGraph

HETIONET_PUBMED = '28936969'

##################
# Hetionet types #
##################

ANATOMY = 'Anatomy'
GENE = 'Gene'
PATHWAY = 'Pathway'
BIOPROCESS = 'Biological Process'
COMPOUND = 'Compound'
SIDE_EFFECT = 'Side Effect'
DISEASE = 'Disease'
PHARMACOLOGICAL_CLASS = 'Pharmacologic Class'
SYMPTOM = 'Symptom'

DSL_MAP = {
    ANATOMY: 'uberon',
    GENE: 'ncbigene',
    PATHWAY: 'reactome',
    BIOPROCESS: 'go',
    COMPOUND: 'drugbank',
    SIDE_EFFECT: 'umls',
    DISEASE: 'doid',
    PHARMACOLOGICAL_CLASS: 'drugcentral',
    SYMPTOM: 'mesh',
}

TYPE_BLACKLIST = {'Molecular Function', 'Cellular Component'}

QUALIFIED_MAPPING = {
    (ANATOMY, Population, 'upregulates', GENE, Rna, BELGraph.add_positive_correlation),
    (ANATOMY, Population, 'downregulates', GENE, Rna, BELGraph.add_negative_correlation),
    (ANATOMY, Population, 'expresses', GENE, Rna, BELGraph.add_correlation),
    (COMPOUND, Abundance, 'resembles', COMPOUND, Abundance, BELGraph.add_association),
    (COMPOUND, Abundance, 'upregulates', GENE, Protein, BELGraph.add_increases),
    (COMPOUND, Abundance, 'downregulates', GENE, Protein, BELGraph.add_decreases),
    (COMPOUND, Abundance, 'treats', DISEASE, Pathology, BELGraph.add_decreases),
    (COMPOUND, Abundance, 'palliates', DISEASE, Pathology, BELGraph.add_decreases),
    (COMPOUND, Abundance, 'causes', SIDE_EFFECT, Pathology, BELGraph.add_increases),
    (GENE, Protein, 'interacts', GENE, Protein, BELGraph.add_binds),  # FIXME look into this
    (GENE, Protein, 'regulates', GENE, Protein, BELGraph.add_regulates),
    (GENE, Rna, 'covaries', GENE, Rna, BELGraph.add_correlation),
    (DISEASE, Pathology, 'localizes', ANATOMY, Population, BELGraph.add_association),
    (DISEASE, Pathology, 'associates', GENE, Protein, BELGraph.add_association),
    (DISEASE, Pathology, 'upregulates', GENE, Rna, BELGraph.add_positive_correlation),
    (DISEASE, Pathology, 'downregulates', GENE, Rna, BELGraph.add_negative_correlation),
    (DISEASE, Pathology, 'presents', SYMPTOM, Pathology, BELGraph.add_association),
    (DISEASE, Pathology, 'resembles', DISEASE, Pathology, BELGraph.add_association),
}
UNQUALIFIED_MAPPING = {
    (GENE, Protein, 'participates', PATHWAY, BiologicalProcess, BELGraph.add_part_of),
    (GENE, Protein, 'participates', BIOPROCESS, BiologicalProcess, BELGraph.add_part_of),
}

####################
# Drug action tags #
####################

ACTIVATES_ACTIONS = {
    'agonist', 'potentiator', 'inducer', 'positive modulator', 'partial agonist', 'positive allosteric modulator',
    'activator', 'stimulator',
}
INHIBITS_ACTIONS = {
    'inhibitor', 'antagonist', 'blocker', 'partial antagonist', 'inhibitor, competitive', 'negative modulator',
    'negative allosteric modulator', 'allosteric antagonist', 'suppressor', 'inhibitory allosteric modulator',
    'conversion inhibitor',
}
REGULATES_ACTIONS = {
    'modulator', 'allosteric modulator',
}
BINDS_ACTIONS = {
    'substrate', 'binder', 'other/unknown', 'ligand', 'cofactor', 'product of', 'opener', 'desensitize the target',
    'other', 'unknown', 'antibody', 'binding', 'adduct', 'multitarget', 'releasing agent',
}
TBH_ACTIONS = {}

ACTIVATES_ACTION_PAIRS = {
    ('activator', 'substrate'),
    ('agonist', 'binder'),
    ('agonist', 'partial agonist'), ('inducer', 'substrate'),
    ('agonist', 'positive allosteric modulator'),
    ('positive allosteric modulator', 'potentiator'),
}
INHIBITS_ACTION_PAIR = {
    ('agonist', 'positive modulator'),
    ('allosteric antagonist', 'antagonist'),
    ('antagonist', 'blocker'),
    ('antagonist', 'inhibitor'),
    ('antagonist', 'multitarget'),
    ('antagonist', 'substrate'),
    ('blocker', 'inhibitor'),
    ('blocker', 'modulator'),
    ('inhibitor', 'modulator'),
    ('inhibitor', 'multitarget'),
    ('inhibitor', 'negative modulator'),
    ('inhibitor', 'other'),
    ('inhibitor', 'substrate'),
    ('negative modulator', 'releasing agent'),
}
CONFLICTING_ACTION_PAIR = {
    ('inducer', 'inhibitor', 'substrate'),
    ('inducer', 'inhibitor'),
    ('agonist', 'antagonist'),
    ('antagonist', 'partial agonist'),
    ('adduct', 'inhibitor'),
    ('agonist', 'antagonist', 'modulator'),
}
UNINTERPRETABLE_ACTION_PAIR = {
    ('binder', 'opener'),
}
