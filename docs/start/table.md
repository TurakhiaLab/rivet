# RIVET Results Table
Each of the sections below describes the columns of RIVET's results table of inferred recombinant ancestors.

## Recombinant Node ID 
* UShER assigned node id for inferred recombinant node

## Donor Node ID
* UShER assigned node id for donor (recombinant parentental node)

## Acceptor Node ID
* UShER assigned node id for acceptor (recombinant parentental node)

## Breakpoint 1 Interval
* RIPPLES inferred breakpoint interval 1

## Breakpoint 2 Interval
* RIPPLES inferred breakpoint interval 2

!!! info

    For more information on the `RIPPLES` algorithm, please see: [Pandemic-scale phylogenomics reveals the SARS-CoV-2 recombination landscape](https://www.nature.com/articles/s41586-022-05189-9)


## Recombinant Clade
* Recombinant clade classification as assigned by `Nextstrain`

## Recombinant Lineage
* Recombinant lineage designation as assigned by `Pangolin`

## Donor Clade
* Donor clade classification as assigned by `Nextstrain`

## Donor Lineage
* Donor lineage designation as assigned by `Pangolin`

## Acceptor Clade
* Acceptor clade classification as assigned by `Nextstrain`

## Acceptor Lineage
* Acceptor lineage designation as assigned by `Pangolin`

## Chronumental-inferred origin date
* Inferred first emergence of recombinant ancestor sequence using the [Chronumental](https://github.com/theosanderson/chronumental) method, which runs automatically as part of the `RIVET` pipeline. In short, `Chronumental` is a accurate and scalable time-tree estimation method that uses stochastic gradient descent to estimate lengths of time for tree branches under a probabilistic model. For more information on this method, please see the [Chronumental](https://doi.org/10.1101/2021.10.27.465994) paper.

## Recombinant Ranking Score
* The ranking score represents a **growth score** that we compute for each inferred recombinant, which is designed to help prioritize recently emerging recombinants and recombinants with many descendant circulating sequences.
* By default, we order the main `RIVET` results table by maximum ranking score, which attempts to prioritize highest concern recombinants of interest at the top of the list.

The recombinant **growth metric** below, *G(R)*, for a recombinant node with a set of descendants *S* is defined below:

$$ \ G(R) = 2^{-m(R)} * \sum_{s\in S} 2^{-m(s)} $$

In the equation above, and correspond to the number of months (30-day intervals) *𝑚(𝑅)* *𝑚(𝑠)*
elapsed since the recombinant node was inferred to have originated and its descendant *𝑅*
sequence was sampled, respectively. The growth score above, *G(R)*, is computed for each
detected recombinant *R*, and the final recombinant list is ranked based on descending growth
scores.

## Representative Descendant
* This selected sample is a descendant with the fewest additional mutations as compared to it's recombinant ancestor.


## Informative Site Sequence
* The informative site sequence is a binary string of `A` and `B` for each trio sequence, where an `A` is assigned if the recombinant node allele at the site matches only the donor node allele at that site, or a `B` if the recombinant matched only the acceptor.


## 3SEQ (M, N, K)
* 3SEQ M, M, K values used to check individual p-values in a pre-generated 3SEQ p-value table.


## 3SEQ P-Value

!!! info
    For more information on the `3SEQ` method and its use in `RIPPLES`, please see [Improved Algorithmic Complexity for the 3SEQ Recombination Detection Algorithm](https://academic.oup.com/mbe/article/35/1/247/4318635) and the Supplementary Section of [Pandemic-scale phylogenomics reveals the SARS-CoV-2 recombination landscape](https://www.nature.com/articles/s41586-022-05189-9#MOESM1)




## Original Parsimony Score
* The original parsimony placement score on the global phylogeny.

## Parsimony Score Improvement
* Highest parsimony score improvement relative to original parsimony score.


## Quality Control (QC) Flags
* This column represents quality control (QC) or filtration checks that where flagged, meaning that this inferred recombinant is not high-confidence and could represent a false-positive recombinant resulting from bioinformatic, contamination or other sequencing errors. 


!!! info

    For detailed description of each quality control and filtration check performed in `RIVET's` backend pipeline, see the [Quality Control and Filtration Checks](filtration.md) page.

**Common sources of <span style="color:red">false positive</span> errors in `RIVET’s` pipeline include, but are not limited to:**

* Contamination, sequencing, or assembly errors in the recombinant or parent sequences
* Missing sequences resulting in artificially long branches in the UCSC public tree
* Misalignments or phylogenetic inconsistencies


**Common sources of <span style="color:red">false negative</span> errors in `RIVET’s` pipeline include, but are not limited to:**

* Too few recombination-informative sites in the recombinant
* More than two breakpoints are required to explain the recombinant
* Too few descendants of the recombinant or its parent in the UCSC public tree


## "Click to View" Taxonium
* When clicked, this button will open a separate tab launching the [Taxonium](https://taxonium.org/) browser in order to view the particular recombinant trio (recombinant/donor/acceptor) in the context of the global phylogeny.
In short, [Taxonium](https://elifesciences.org/articles/82392) is a visualization tool for exploring large trees.

