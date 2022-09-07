import pandas as pd 
import json
import vcf
from pysam import VariantFile, TabixFile, asVCF
from collections import OrderedDict

def tsv_to_json(results_tsvfile):
    """
      Load TSV file and convert into JSON file that is dumped into current directory.
    """
    dictionary = {} 
    with open(results_tsvfile) as f:
      for line in f:
        splitline = line.strip().split('\t')
        recomb_node_id = splitline[0]
        dictionary[recomb_node_id] = splitline 
 
    json_file = open("{}.json".format(results_tsvfile.strip(".txt")), "w")
    json.dump(dictionary, json_file, indent = 4, sort_keys = False)
    json_file.close()

def tsv_to_dict(results_tsvfile):
    """
    Convert the recombination TSV results file to a dictionary and use
    recombination_node_id as the key for each data row.
    """
    dictionary = {}
    with open(results_tsvfile) as f:
      column_headers = f.readline().strip().split('\t')
      # Once column headers are extracted, skip over header line
      next(f)
      for line in f:
        splitline = line.strip().split('\t')
        recomb_node_id = splitline[0]
        # Build dictionary with key: recomb_node_id
        # and value : corresponding data for that recombinant node
        dictionary[recomb_node_id] = splitline 
    return dictionary, column_headers

def query_recomb_data(recomb_node_id, results_dict):
    """
    Get data for given recomb_node_id
    """
    return results_dict[recomb_node_id]

def build_table(results_dict, rows=3, columns=[]):
    """
    Build a table from a dictionary.
    """
    table = []
    dictionary = []
    i = 0
    for [key, value] in results_dict.items():
        # Testing: Load just 10 rows
        if i == 10:
            break
        #Add row elements in the order given by columns
        # TODO: Bug to fix, testing hardcoded columns 
        row = [value[0], value[1], value[2], value[3], value[4], value[5], value[6], value[7], value[8], value[9]]
        table.append(row)
        i+=1
    return table


def load_table(results_file):
    """
    Create table from dictionary. Return table and columns as separate lists.
    """
    #Convert final recombination results file to dictionary indexed by recomb_node_id
    # Extract datatable column headers also
    results_dict, columns = tsv_to_dict(results_file)

    # Add additional column for Taxodium tree view links
    columns.append("Click to View Tree")

    table = build_table(results_dict, columns)

    return table, columns

def vcf_to_dict(vcf_file):
  """
  Function to retrieve snps from a single VCF file containing variants for all trio nodes.

  Return:
    Dictionary of OrderedDicts, ie) { node id: {pos:genotype, ...} ... }
  """
  # Load vcf file
  vcf_reader = vcf.Reader(open(vcf_file, 'r'))

  # Create dictionary of all node_ids (recomb/donor/acceptor) (samples from VCF file).
  # Then the value at each node id, is an OrderedDict with the genotypes at each position, 
  # ordered by increasing genomic position.
  nodes_ids = {key: OrderedDict() for key in vcf_reader.samples}
  nodes_ids["Reference"] = OrderedDict()

  # Iterate over genomic positions
  for record in vcf_reader:
      # Record reference allele at each genomic position
      nodes_ids["Reference"][str(record.POS)] = str(record.REF)
      # Record alleles of all nodes (samples) at each genomic position
      for s in record.samples:
          if s["GT"] == "0":
              continue
          if s["GT"] == "1":
              nodes_ids[str(s.sample)][str(record.POS)] = str(record.ALT[0])
          elif s["GT"] == "2":
              nodes_ids[str(s.sample)][str(record.POS)] = str(record.ALT[1])
          elif s["GT"] == "3":
              nodes_ids[str(s.sample)][str(record.POS)] = str(record.ALT[2])
          else:
              print("Unknown genotype. Check VCF file")
              print(str(record.ALT))
              exit(1)

  # Return nested dictionary contaning all nodes and corresponding snps
  return nodes_ids
