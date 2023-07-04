# Visualizing Your Results Using the RIVET Frontend

!!! note
    If you are using the `RIVET` frontend to visualize recombinants for pathogens other than SARS-CoV-2, please see the [Using RIVET for Other Pathogens](start/future.md) page.

### Configuration

`RIVET's` frontend settings can be configured using the provided YAML file, `config.yaml`. 

```yaml
# Configuration file for RIVET
### Color Schema Options ####
# Base coloring
a: '#cc0000'
g: '#cc7722'
c: '#57026f'
t: '#338333'
base_matching_reference: '#dadada'
reference_track: '#333333'

# Recombinant-Informative Coloring for polygons/position column labels
recomb_match_acceptor: '#2879C0'
recomb_match_donor: '#F9521E'
non_informative_site: '#dadada'

# Breakpoint Intervals
breakpoint_intervals: '#800000'

# Genomic Coordinate Track (default all genomic regions are same color)
genomic_regions: '#33333'
# Step for tick-marks on genomic coordinate track
tick_step: 1000

# Pathogen
ref_seq: NC_045512.gb

### Taxonium Tree View Options ###
date: 2023-01-31
bucket_name: public_trees

# Keep environment as "local"
environment: local
# If running locally, port to use
port: 2000
```

!!! warning
    When running `RIVET` locally, don't change the `environment` field.  Also, it won't be necessary to change the `date` field or `bucket_name` field.


Run the following command to launch the `RIVET` frontend in your local browser.

!!! example
    Try the following example using example SARS-CoV-2 recombinants provided in the `example/` directory.

```python
python3 rivet-frontend.py -r example/final_recombinants_example.txt -v example/trios_example.vcf -c config.yaml
```
## Required Inputs
`-f, RECOMBINANT_RESULTS`: Input text file containing inferred recombinant nodes.  First three columns in this text file must contain (1) recombinant node ID\t (2) donor node ID (3) acceptor node ID.  Note, donor and acceptor denote the two parental nodes of the inferred recombinant.


!!! note
    The `RIVET` backend will automatically generate the necessary input files above.  Follow the steps listed on the [Inferring Recombinants Using the RIVET Backend](installation/upload.md) page.  However, the `RIVET` frontend can also be used independently of the backend, just ensure that the input files adhere to the expected formatting.

`-v, VCF`: An input VCF containing single-nucleotide variants (SNVs) of all recombinant/donor/acceptor trio nodes present in the input `RECOMBINANT_RESULTS` file.

`-c, CONFIG`: The `config.yaml` file.