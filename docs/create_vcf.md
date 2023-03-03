# Building a VCF file when running the RIVET frontend locally 

In order for the RIVET frontend to generate the SNVs visualization of potential recombinant sequence trios, an input tab-delimited file (`results.txt`) is required.  The only requirement of this file is that the first three columns must contain your recombinant node id, donor node id and acceptor node id, in this order, as seen below.  Additional columns can be added after this, and will be displayed in the frontend results table.

| Recombinant Node ID       | Donor Node ID | Acceptor Node ID | Optional additional columns ... |
| ------------------------- | -----------   | ---------------- | ------------------------------- |
| node_1156861              | node_1155169  | node_1167556     |                                 |
| node_1067629              | node_1021823  | node_1156861     |                                 |

## Generating a VCF file for the RIVET frontend using matUtils
Following this requirement, running the RIVET frontend locally also requires an input VCF that contains the SNVs for every node in the first three columns (recomb/donor/acceptor) in your results tab-delimited file.

A VCF file can be generated using `matUtils`, which is a suite of tools to analyze, edit and manipulate mutation annotated tree (.pb) files, and is available within [USHER](https://github.com/yatisht/usher).

Running the following command with these command line flags will yield an output VCF that can be uploaded to the RIVET frontend.

```
matUtils extract -i <MAT> -s <node_ids.txt> -v <output.vcf>
```
Options:
- `<MAT>`: Input mutation annotated tree (.pb) file which should already containing the node_ids listed in your input results file. (New samples should be placed on MAT first, before recombination inference)
- `<node_ids.txt>`: An input plain text file containing all the unique internal node ids from your input results file (first 3 columns) explicitly naming them, one per line.
- `<output.vcf>`: The name of the written output VCF, containing the SNVs for each ancestral node listed in `<node_ids.txt>`.

This `<output.vcf>` file can be uploaded to the RIVET frontend locally, using the `-v` command line flag.