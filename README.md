<img src="static/images/rivet-icon.png" width="300">

# RIVET: SARS-CoV-2 RecombInation ViEwer and Tracker

## Table of Contents
- [Overview](#overview)
- [RIVET Frontend](#rivet_frontend)
    - [Viewing your own recombinants with RIVET on a local HTTP server](#rivet_local)
    - [Example](#rivet_example)
- [RIVET Backend](#rivet_backend)
    - [RIVET Backend Setup](#rivet_backend_setup)
    - [RIVET Backend Pipeline Results](#rivet_backend_results)
- [Citing RIVET](#cite_rivet)


## <a name="overview"></a> Overview
<br>

![](images/rivet_backend_diagram.jpg)

RIVET is a program designed to aid in SARS-CoV-2 recombination analysis and consists of backend and frontend components:
1. [Backend](#rivet_backend): RIVET's backend pipeline uses [RIPPLES](https://www.nature.com/articles/s41586-022-05189-9) for recombination detection in a [mutation-annotated tree](https://usher-wiki.readthedocs.io/en/latest/UShER.html) and has a subsequent automated filtration pipeline to flag potential false-positives resulting from bioinformatic, contamination or other sequencing errors.  Next, the recombination results are ranked and additional results/metadata files are generated by the RIVET backend pipeline that can be loaded by the RIVET frontend.
2. [Frontend](#rivet_frontend): The RIVET frontend is an interactive, web-browser interface for online visualization, tracking, and analysis of recombination detection results.

We routinely run RIVET's backend pipeline on the [SARS-CoV-2 global MAT](https://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/) that is publicly shared by UCSC and make these results available for visualization on https://rivet.ucsd.edu/.

## <a name="rivet_frontend"></a> RIVET Frontend

### <a name="rivet_local"></a>Viewing your own recombinants with RIVET on a local HTTP server

RIVET can also be run locally to visualize SNVs of potential recombinant sequences, with the recombinant-informative sites highlighted.  The following two files are minimally required to run RIVET locally: <br>

- `results.txt`: a tab-separated file with one recombinant sequence per row, that must contain your recombinant node id, donor node id and acceptor node id as the first three column entires, as seen below.  Additional columns after the first three can be added to this results file, which will be rendered in the UI table.<br>

    | Recombinant Node ID       | Donor Node ID | Acceptor Node ID |
    | ------------------------- | -----------   | ---------------- |
    | node_1156861              | node_1155169  | node_1167556     |
    | node_1067629              | node_1021823  | node_1156861     |
<br>

- `VCF` file containing SNVs for all trio nodes. Each node (recomb/donor/acceptor) in the first three columns of every row in your results tsv file, should be included in this VCF file. Please note, when constructing your `VCF` file, that currently RIVET only supports viewing SNVs, and not indels or SVs. Please see the following workflow to [create a VCF](docs/create_vcf.md) for uploading to RIVET locally.

<br>

- `config.yaml`: A config file is provided for running RIVET locally. **The default `environment` field is set to `local` and should not be changed for running RIVET as a local HTTP server.** . Additional fields in the config file are provided to the user to customize various elements of the SNV plot coloring, such as the color of nucleotide bases or the color of the highlighted recombinant-informative sites in the visual. Please feel free to change these colorings according to your own preference. 

### <a name="rivet_example"></a>Example
All the RIVET dependencies have been added to Conda environment setup, that can be found in the `install` directory.
Run the following commands to activate the `rivet` Conda environment.
```
conda env create -f install/rivet_env.yml
conda activate rivet
```
<br>

Example data files are provided under the `example` directory.
Run the following command and past the URL to your local web-browser to see the RIVET UI locally.
```
python3 rivet-frontend.py -v example/trios_example.vcf -r example/final_recombinants_example.txt -c config.yaml
```
Type the following help command to see these the options and their descriptions:
```
python3 rivet-frontend.py --help
```


## <a name="rivet_backend"></a>RIVET Backend

The RIVET backend uses [RIPPLES](https://www.nature.com/articles/s41586-022-05189-9) for recombination detection. For more information on the RIPPLES algorithm and the automated filtration piepeline, please see: [Pandemic-Scale Phylogenomics Reveals The SARS-CoV-2 Recombination Landscape](https://doi.org/10.1038/s41586-022-05189-9)

### <a name="rivet_backend_setup"></a> RIVET Backend Setup

Please see the following docs for setting up an account with Google Cloud Platform: [GCP Setup Docs](docs/gcp_setup.md)

For ease of use, the entire RIVET backend pipeline, including recombinant ranking, is contained within a pre-built public docker image.


To launch a Docker shell, run the following two commands.
- Note: Put your GCP service account key file (obtained following the docs linked above) in the corresponding location as the command below or update the location in the command below:
```
KEY=~/.config/gcloud/<key_file.json>
docker run -it -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/<key_file.json> -v ${KEY}:/tmp/keys/<key_file.json>:ro mrkylesmith/ripples_pipeline:latest
```

This will drop you into Docker shell where you can launch a RIVET job on GCP.<br>

Copy the config template into the current directory to customize for your current RIVET job.
```
cp template/ripples.yaml .
```
Add all RIVET runtime parameters and GCP machine configurations to your ripples.yaml file.

```yaml
# GCP credentials
bucket_id: 
project_id: 
# Path to key file
# If inside Docker shell, make sure key_file matches /tmp/keys/<key_file.json> 
key_file: 

# GCP machine and Storage Bucket config
# Number of GCP machines to use (data automatically partitioned/parallelized)
instances: 
# Don't change boot disk size
boot_disk_size: 40
machine_type: n2d-highcpu-32 

# Format job_name/logging (follow this format of top_folder_name/logging)  
# Format job_name/results (follow this format of top_folder_name/results)
# <job_name> will be a unique folder name in your GCP Storage bucket
logging: 
results: 

# Ripples parameters config [REQURIED]
version: ripples-fast
# Name of mutation-annotated tree 
mat: public-date.all.masked.pb
# Naming for Newick tree that will be generated by pipeline
newick: tree.nwk
# Name of metadata file, corresponding to input MAT
metadata: public-date.metadata.tsv.gz
# Date in format: 2023-01-31 (year-month-day)
date: 
# SARS-CoV-2 reference genome placed in top level folder of GCP Storage Bucket (keep same name: reference.fa)
reference: reference.fa

# Ripples parameters
# Minimum number of leaves that a node should have to be considered for recombination
num_descendants: 5

```

**Note:** The following files with the same naming from the above config need to be placed in the top level directory of a GCP Storage Bucket (`bucket_id`) ahead of time:
- `mat`: Obtain a [SARS-CoV-2 global MAT](https://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/)
- `metadata`: Obtain [metadata](https://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/) matching the input MAT
- `raw sequence files:` Downloadable at the following links, for a given `$TREE_DATE`:
    - `https://hgwdev.gi.ucsc.edu/~angie/sarscov2phylo/ncbi.$TREE_DATE/genbank.fa.xz`
    - `https://hgwdev.gi.ucsc.edu/~angie/sarscov2phylo/cogUk.$TREE_DATE/cog_all.fasta.xz`

<br>

After the `ripples.yaml` config has been completely filled out, to launch the RIVET job on GCP instances simply run the following command:
```
python3 run.py
```

### <a name="rivet_backend_results"></a>RIVET Backend Results
The pipeline will create a local results directory, based on the name given for the `results` field in `ripples.yaml`

The pipeline will automatically output the following four files within your local `results` directory:

- `final_recombinants.txt`: a txt file containing the detected recombinants, with the recombinant node id, donor node id and acceptor node id as the first three columns in the file. The rest of the columns contain information about each detected recombinant, including clade/lineage assignments, 3SEQ M,N,K and p-values, a representative descendant (containing the fewest additional mutations wrt the recombinant node), recombinant ranking scores, and other information to be displayed by the RIVET frontend.
- `trios.vcf.gz`: VCF file containing the SNVs of each trio (recombinant and its parents) node.
- `sample_descedants.txt.gz`: a TSV file containing a mapping from each trio node id, to a set of descendant samples.
- `<tree_data>.taxonium.jsonl.gz`: a jsonl file used by RIVET frontend to display the recombinant node trios within the context of the global phylogeny, powered by Taxonium and Treenome.


## <a name="cite_rivet"></a> Citing RIVET
Please cite the following papers if you found this website helpful in your research:

- Kyle Smith, Cheng Ye, Yatish Turakhia, "Tracking and curating putative SARS-CoV-2 recombinants with RIVET", bioRxiv (2023), https://doi.org/10.1101/2023.02.17.529036.
<br>
- Yatish Turakhia*, Bryan Thornlow*, Angie S. Hinrichs, Jakob McBroome, Nicolas Ayala, Cheng Ye, Kyle Smith, Nicola De Maio, David Haussler, Robert Lanfear, Russell Corbett-Detig, "Pandemic-Scale Phylogenomics Reveals The SARS-CoV-2 Recombination Landscape", Nature (2022), https://doi.org/10.1038/s41586-022-05189-9.