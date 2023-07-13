# Quality Control and Filtration Checks

## 3SeqP02
P-value from 3-seq > 0.2.

## russPval005
False-discovery rate (FDR) of the parsimony improvement > 0.05. (See [Supplementary Text S3 of RIPPLES](https://www.nature.com/articles/s41586-022-05189-9#MOESM1) for details of the null model.)

## Alt
"Alternate": Other recombination trios with the same recombination node have more parsimony improvement, fewer possible breakpoint intervals, or better P-values.

## cluster 
All recombination informative mutations occur within a span of 20 nucleotides.

## redundant
More than two of the recombination node, donor node, and acceptor node appear in that of another trios.

## Informative_sites_clump
More than 5 recombination-informative mutations in a 20-nucleotide span.

## Suspicious_mutation_clump
More than 6 mutations (or 3 near indels) in a 20-nucleotide span on any of the donor node, the aceptor node or the recombination node.

## Too_many_mutations_near_INDELs
Too many mutations on 100-nt spans near indels or a string of Ns.