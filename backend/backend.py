"""
Backend functions for RIVET UI
"""

import pandas as pd 
import numpy as np
import json
import time
import random
import string
from cyvcf2 import VCF
from functools import lru_cache
from collections import OrderedDict
from alive_progress import alive_bar, alive_it


def get_treeview_host():
    """
    """
    #TODO: Update with config file for specific recombination run
    BUCKET_NAME = "public_trees"
    OBJECT_NAME = "2022-09-06.taxonium.jsonl.gz"
    HOST = "https://storage.googleapis.com/"
    HOST += "/".join([BUCKET_NAME,OBJECT_NAME])
    return HOST

def check_column_format(row):
    """
    Check to make sure input results file columns start with 3 trio node ids:
        recomb_node_id \t donor_node_id \t acceptor_node_id
    """
    substr = "node_"
    if (row[0].startswith(substr) and row[1].startswith(substr) and row[2].startswith(substr)):
          return False
    return True


def init_data(results_file):
    """
    Grab first line of data from input results file to initialize visualization.
    """
    with open(results_file) as f:
      d = {}
      # Skip over column headers (assuming one)
      next(f)
      for line in f:
        #TODO: Get this information from columns header parse
        splitline = line.strip().split('\t')
        d["recomb_id"] = splitline[0]
        d["donor_id"] = splitline[1]
        d["acceptor_id"] = splitline[2]
        d["breakpoint1"] = splitline[3]
        d["breakpoint2"] = splitline[4]
        d["descendants"] = "NA"
        return d

def load_descendants(desc_file):
    """
    """
    with open(desc_file) as f:
      d = {}
      # Skip over column headers (assuming one)
      next(f)
      for line in f:
        splitline = line.strip().split('\t')
        recomb_node_id = splitline[0]
        descendants_string = splitline[1]
        descendants_list = descendants_string.split(', ')
        d[recomb_node_id] = descendants_list
      
    return d

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
    Convert the recombination TSV results file to a dictionary and use recombination_node_id as the key for each data row.
    """
    dictionary = {}
    with open(results_tsvfile) as f:
      # Extract column headers from input results tsv file
      column_headers = f.readline().strip().split('\t')
      for line in f:
        splitline = line.strip().split('\t')
        recomb_node_id = splitline[0]
        # Build dictionary with key: recomb_node_id
        # and value : corresponding data for that recombinant node
        dictionary[recomb_node_id] = splitline 
    return dictionary, column_headers

def calculate_midpoint(bp_lower_bound, bp_upper_bound):
    """
    Return, floor midpoint
    """
    return (bp_lower_bound + bp_upper_bound)//2

def format_bp_interval(bp_interval):
    """
    Basic string formatting to get int values out of bp interval string
    formatted like this: "(21839,23403)"
    Return list of string with starting and ending of interval: ["start", "end"]
    """
    # Remove outer parenthesis
    bp_interval = bp_interval[1:len(bp_interval)-1]
    interval = map(int, bp_interval.split(","))
    return interval

def format_bp_data(bp_dictionary):
    """
    Reformat the breakpoint data for vizualization from OrderedDict, to ordered list of dictionaries.
    """
    lst = []
    # Adding positions in order
    for [key,value] in bp_dictionary.items():
        lst.append(value)
    return lst

def generate_breakpoint_data(recomb_results_file):
    """
    """
    data = []
    midpoints = {}
    with open(recomb_results_file) as f:
      # Extract breakpoint column headers from input results tsv file
      column_headers = f.readline().strip().split('\t')
      # Column indices (0-based) of the two breakpoint intervals in the input recombination results file
      #TODO: Get this information from init
      bp1_col_idx= 3
      bp2_col_idx= 4

      for line in f:
        splitline = line.strip().split('\t')

        interval1_start, interval1_end = format_bp_interval(splitline[bp1_col_idx])
        interval2_start, interval2_end = format_bp_interval(splitline[bp2_col_idx])
        midpoint1 = calculate_midpoint(interval1_start, interval1_end)
        midpoint2 = calculate_midpoint(interval2_start, interval2_end)

        # Add the two position values
        if midpoint1 not in midpoints:
            midpoints[midpoint1] = {"position": midpoint1, "count": 1}

        # If midpoint position already added to dataset, increament count
        else:
            midpoints[midpoint1]["count"]+= 1

        if midpoint2 not in midpoints:
            midpoints[midpoint2] = {"position": midpoint2, "count": 1}
        else:
            midpoints[midpoint2]["count"]+= 1
        
    midpoints = OrderedDict(sorted(midpoints.items()))
    return midpoints


def generate_taxonium_link(recomb_id, donor_id, acceptor_id, HOST):
    """
    Generate link to view trio nodes in Taxonium tree.
    """
    HOST = get_treeview_host()
    link = "https://taxonium.org/?protoUrl=" + HOST
    # Search Recomb id
    link += '&srch=[{"key":"aa1","type":"name","method":"text_exact","text":"'
    link += recomb_id
    link += '","gene":"S","position":484,"new_residue":"any","min_tips":0},'
    # Search donor id
    link += '{"key":"bb2","type":"name","method":"text_exact","text":"'
    link += donor_id
    link += '","gene":"S","position":484,"new_residue":"any","min_tips":0},'
    # Search acceptor id
    link += '{"key":"cc3","type":"name","method":"text_exact","text":"'
    link += acceptor_id
    link += '"}]'
    # Enable mulitple search parameters
    link += '&enabled={"aa1":true, "bb2":true, "cc3":true}'
    # Enable treenome by default
    link += '&treenomeEnabled=true'
    return link

def build_table(results_dict, columns):
    """
    Build a table from a dictionary.
    """
    # Assumes recomb_id, donor_id, acceptor_id are first 3 columns in results file
    table = []
    dictionary = []
    row_num = 1 
    for [key, value] in results_dict.items():
        # Check that first 3 columns are node_ids
        if(check_column_format(value)):
            raise RuntimeError(colored("[ERROR]: First 3 columns must be: recomb_node_id\t donor_node_id\t acceptor_node_id.  Formatting error occurring at line: {}".format(row_num), 'red', attrs=['reverse']))
            
        row = [value[i] for i in range(0,len(columns)-1)]
        row.append(generate_taxonium_link(value[0], value[1], value[2], get_treeview_host()))
        table.append(row)

        # Iterate row for error message
        row_num +=1

    return table


def load_table(results_file):
    """
    Create table from dictionary. Return table and columns as separate lists.
    """
    #Convert final recombination results file to dictionary indexed by recomb_node_id
    # Extract datatable column headers also
    results_dict, columns = tsv_to_dict(results_file)

    # Add additional column for Taxodium tree view links
    # Last column in datatable by default
    columns.append("Click to View")

    # Check header information present in file
    if(len(columns) == 0):
        raise RuntimeError(colored("[ERROR]: Check input results file: {}. Empty file or missing header information".format(results_file), 'red', attrs=['reverse']))

    table = build_table(results_dict, columns)

    return table, columns

def vcf_to_dict(vcf_file):
  """
  Function to retrieve snps from a single VCF file containing variants for all trio nodes.

  Return:
    Dictionary of OrderedDicts, ie) { node id: {pos:genotype, ...} ... }
  """
  # Load vcf file
  vcf_reader = VCF(vcf_file)
  samples = vcf_reader.samples

  # Create dictionary of all node_ids (recomb/donor/acceptor) (samples from VCF file).
  # Then the value at each node id, is an OrderedDict with the genotypes at each position, 
  # ordered by increasing genomic position.
  nodes_ids = {key: OrderedDict() for key in samples}
  nodes_ids["Reference"] = OrderedDict()

  # Get number of records in input VCF file
  print("Loading VCF file.")

  # Iterate over genomic positions
  for record in alive_it(vcf_reader):
      # Record reference allele at each genomic position
      nodes_ids["Reference"][str(record.POS)] = str(record.REF)

      position = str(record.POS)
      alleles_indexes = np.nonzero(record.gt_types)
      genotype_array = record.gt_bases

      for i in np.nditer(alleles_indexes):
          sample_name = samples[i]
          sample_alt_allele = genotype_array[i]
          nodes_ids[sample_name][position] = sample_alt_allele

  # Return nested dictionary contaning all nodes and corresponding snps
  return nodes_ids

# TODO: Explicitly cache d for this function
def get_track_data(recomb_id, donor_id, acceptor_id, breakpoint1, breakpoint2, descendants, d, recomb_informative_only):
    """
    Pass in dictionary of snp data for all nodes.
    Lookup and format into smaller dictionary containing 
    snp data for only a single track to display.

    @param: recomb_informative_only (bool), to display all snps 
        or only recombination-informative snps
    """
    print("Fetching data for given recomb_id row selection: {}".format(recomb_id))

    data = {}
    track_data =  OrderedDict()
    recomb_data = d[recomb_id]
    for coordinate,allele in recomb_data.items():
        # Initialize dictionary for track snps at each coordinate
        snps = {}

        # Add position to snp data, (redundant, but simple for now)
        snps["Position"] = coordinate

        # Get reference allele at this coordinate
        snps["Reference"] = d["Reference"][coordinate] 
        # Get recombinant node allele at this coordinate
        snps["Recomb"] = allele 

        # Only store node snps in d,
        # if coordinate is not snp, get reference allele
        if coordinate not in d[donor_id].keys():
            snps["Donor"] = d["Reference"][coordinate]
        # Otherwise fetch and assign snp
        else:
            snps["Donor"] = d[donor_id][coordinate]
        if coordinate not in d[acceptor_id].keys():
            snps["Acceptor"] = d["Reference"][coordinate]
        else:
            snps["Acceptor"] = d[acceptor_id][coordinate]
       
        # If including all snps, add them to track data and continue
        if recomb_informative_only == False:
            track_data[coordinate] = snps
            continue

        # If recombinant allele matches one of donor/acceptor, but not both, include it
        if (snps["Recomb"] == snps["Donor"] or snps["Recomb"] == snps["Acceptor"]) and not (snps["Recomb"] == snps["Donor"] and snps["Recomb"] == snps["Acceptor"]):
            # Add snps dict at this genomic coordinate to track dataset
            track_data[coordinate] = snps

    data["SNPS"] = track_data

    node_ids = {}
    node_ids["Recomb"] = recomb_id
    node_ids["Donor"] = donor_id
    node_ids["Acceptor"] = acceptor_id

    breakpoints = {}
    # TODO: Clean up
    breakpoint1 = breakpoint1[1:len(breakpoint1)-1]
    breakpoint2 = breakpoint2[1:len(breakpoint2)-1]
    interval1 = {}
    interval2 = {}
    intervals1 = breakpoint1.split(",")
    intervals2 = breakpoint2.split(",")
    interval1["xpos"] = intervals1[0]
    interval1["end"] = intervals1[1]
    interval2["xpos"] = intervals2[0]
    interval2["end"] = intervals2[1]

    breakpoints["breakpoint1"] = interval1
    breakpoints["breakpoint2"] = interval2
    # Now add breakpoints to the rest of the data
    data["BREAKPOINTS"] = breakpoints
    data["NODE_IDS"] = node_ids
    data["DESCENDANTS"] = descendants
    
    return data
