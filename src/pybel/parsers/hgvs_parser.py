from pyparsing import *

from .language import dna_nucleotide_chars, rna_nucleotide_chars, amino_acid_dict

aa_triple = oneOf(amino_acid_dict.values())

nucleotides = oneOf(dna_nucleotide_chars)

dna_nucleotide_seq = Word(''.join(dna_nucleotide_chars))
rna_nucleotide_seq = Word(''.join(rna_nucleotide_chars))

hgvs_rna_del = (Suppress('r.') + pyparsing_common.integer() +
                Suppress('_') + pyparsing_common.integer() + 'del' +
                rna_nucleotide_seq)

hgvs_dna_del = (Suppress('c.') + pyparsing_common.integer() +
                Suppress('_') + pyparsing_common.integer() + 'del' +
                dna_nucleotide_seq)

hgvs_chromosome = (Suppress('g.') + pyparsing_common.integer() +
                   Suppress('_') + pyparsing_common.integer() + 'del' +
                   dna_nucleotide_seq)

hgvs_snp = 'del' + dna_nucleotide_seq

hgvs_protein_del = Suppress('p.') + aa_triple + pyparsing_common.integer() + 'del'

hgvs_protein_mut = Suppress('p.') + aa_triple + pyparsing_common.integer() + aa_triple

hgvs_protein_fs = Suppress('p.') + aa_triple + pyparsing_common.integer() + aa_triple + 'fs'

hgvs_genomic = Suppress('g.') + pyparsing_common.integer() + nucleotides + Suppress('>') + nucleotides

hgvs = (hgvs_rna_del | hgvs_dna_del | hgvs_chromosome | hgvs_snp | hgvs_protein_del
        | hgvs_protein_fs | hgvs_protein_mut | hgvs_genomic | '=' | '?')
