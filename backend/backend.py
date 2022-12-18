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
import heapq
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import sys
import seaborn as sns
import matplotlib.patches as patches


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

def load_intervals(recomb_results_file):
    intervals=[]
    with open(recomb_results_file) as f:
      # Extract breakpoint column headers from input results tsv file
      # Column indices (0-based) of the two breakpoint intervals in the input recombination results file
      #TODO: Get this information from init
      bp1_col_idx= 3
      bp2_col_idx= 4
      next(f)
      for line in f:
        splitline = line.strip().split('\t')
        intervals.append(tuple( format_bp_interval(splitline[bp1_col_idx])))
        intervals.append(tuple(format_bp_interval(splitline[bp2_col_idx])))
        
    return sorted(intervals)

def place_intervals(intervals):
    track_heap=[]
    segments_to_plot=[]
    empty_tracks=[]
    for interval in intervals:
        cur_track_cnt=None
        if( ( len(track_heap)==0 or track_heap[0][0]>interval[0]) and (len(empty_tracks)==0) ):
            cur_track_cnt=len(track_heap)
        else:
            while(len(track_heap)>0 and track_heap[0][0]<=interval[0]):
                heapq.heappush(empty_tracks,heapq.heappop(track_heap)[1])
            cur_track_cnt=heapq.heappop(empty_tracks)
        heapq.heappush(track_heap,(interval[1],cur_track_cnt))
        segments_to_plot.append([(interval[0],cur_track_cnt),(interval[1],cur_track_cnt)])
    return (len(track_heap),segments_to_plot)

def make_plot(recomb_results_file, plot_file):
    dpi=96
    intervals=load_intervals(recomb_results_file)
    (max_height,segments_to_plot)=place_intervals(intervals)
    fig,[ax,region_plot_ax] = plt.subplots(2,1,sharex=True,gridspec_kw={'height_ratios': [20, 1],'hspace': 0.08},figsize=(1500/dpi,1000/dpi))
    ax.set_xlim(0,30000)
    ax.set_ylim(0,max_height+1)
    ax.set_ylabel("Breakpoint Intervals")
    line_segments = LineCollection(segments_to_plot,linewidths=1,colors='k')
    ax.add_collection(line_segments)
    ax2=ax.twinx()
    ax.tick_params('x',reset=True)
    midpoints=map(lambda a: calculate_midpoint(a[0],a[1]), intervals)
    sns.kdeplot(x=midpoints,ax=ax2,linewidth=2,color='k')
    plt.setp(ax.get_xticklabels(),visible=True)
    region_dict={
		'ORF1a': {"xpos": 274, "end": 13409, "color": '#add8e6'},
		'ORF1b': {"xpos": 13409, "end": 21531, "color": '#ffb1b1'},
		'S': {"xpos": 21531, "end": 25268, "color": '#ffffe0'},
		'3a': {"xpos": 25268, "end": 26126, "color": '#ffdc9d'},
		'E': {"xpos": 26126, "end": 26471, "color": '#bcf5bc'},
		'M': {"xpos": 26471, "end": 28471, "color": '#ffceff'},
		'N': {"xpos": 28471, "end": 29903, "color": '#ffa500'}
	}
    region_plot_ax.set_axis_off()
    for region in region_dict.items():
        rect=patches.Rectangle((region[1]["xpos"],0),region[1]["end"]-region[1]["xpos"],1,color=region[1]["color"])
        region_plot_ax.add_patch(rect)
        region_plot_ax.text(calculate_midpoint(region[1]["xpos"],region[1]["end"])-200,0.2,region[0],size='large')

    plt.savefig(plot_file)

def find_recomb_midpoints(recomb_results_file):
    midpoints=[]
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
        midpoints.append(midpoint1)
        midpoints.append(midpoint2)
    return midpoints

def generate_breakpoint_data(recomb_results_file):
    """
    """
    midpoints_vec=find_recomb_midpoints(recomb_results_file)
    midpoints = {}
    for midpoint in midpoints_vec:
        # Add the two position values
        if midpoint not in midpoints:
            midpoints[midpoint] = {"position": midpoint, "count": 1}

        # If midpoint position already added to dataset, increament count
        else:
            midpoints[midpoint]["count"]+= 1
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

def vcf_to_dict(vcf_file):
  """
  Function to retrieve snps from a single VCF file containing variants for all trio nodes.

  Return:
    Dictionary of OrderedDicts, ie) { node id: {pos:genotype, ...} ... }
  """
  # Load vcf file
  vcf_reader = VCF(vcf_file)
  samples = vcf_reader.samples
  positions = []

  # Create dictionary of all node_ids (recomb/donor/acceptor) (samples from VCF file).
  # Then the value at each node id, is an OrderedDict with the genotypes at each position, 
  # ordered by increasing genomic position.
  nodes_ids = {key: OrderedDict() for key in samples}
  nodes_ids["Reference"] = OrderedDict()
  print("Loading VCF file.")

  # Iterate over genomic positions
  for record in alive_it(vcf_reader):
      # Record reference allele at each genomic position
      nodes_ids["Reference"][str(record.POS)] = str(record.REF)
      positions.append(str(record.POS))

      position = str(record.POS)
      alleles_indexes = np.nonzero(record.gt_types)
      genotype_array = record.gt_bases

      for i in np.nditer(alleles_indexes):
          sample_name = samples[i]
          nodes_ids[sample_name][position] = genotype_array[i]

  # Return nested dictionary contaning all nodes and corresponding snps
  return nodes_ids, positions


def get_positions(snp_data):
    """
    """
    pos = set()
    for (key, value) in enumerate(snp_data.items()):
        pos.add(value[0])
    return pos



def get_all_snps(recomb_id, donor_id, acceptor_id, breakpoint1, breakpoint2, descendants, d, recomb_informative_only):
    """
    Pass in dictionary of snp data for all nodes.
    Lookup and format into smaller dictionary containing 
    snp data for only a single track to display.

    @param: recomb_informative_only (bool), to display all snps 
        or only recombination-informative snps
    """
    print("Fetching data for given recomb_id row selection: {}".format(recomb_id))

    data = {}
    track_data = OrderedDict()
    positions_test = set()

    for snps in [recomb_id, donor_id, acceptor_id]:
        positions_test = positions_test.union(get_positions(d[snps]))
    pos = list(positions_test)
    pos.sort()

    # Iterate wrt genomic positions
    for p in pos:
        # Initialize dictionary for track snps at each coordinate
        snps = {}

        # Add position to snp data, (redundant, but simple for now)
        snps["Position"] = p

        # Get reference allele at this coordinate
        snps["Reference"] = d["Reference"][p] 

        # Get recombinant node allele at this coordinate
        if d[recomb_id].get(p):
            snps["Recomb"] = d[recomb_id][p]
        else:
            snps["Recomb"] = d["Reference"][p] 

        # Get donor node allele at this coordinate
        if d[donor_id].get(p):
            snps["Donor"] = d[donor_id][p]
        # If coordinate is not snp, get reference allele
        else:
            snps["Donor"] = d["Reference"][p]

        # Get acceptor node allele at this coordinate
        if d[acceptor_id].get(p):
            snps["Acceptor"] = d[acceptor_id][p]
        else:
            snps["Acceptor"] = d["Reference"][p]

        # If showing all snps, just add position to track data
        if recomb_informative_only == False:
            track_data[p] = snps
            continue

        # TODO: Add back functionality 
        # If recombinant allele matches only one of donor/acceptor, but not both, include it
        #if(determine_informative(snps)):
        #    # Add snps dict at this genomic coordinate to track dataset
        #    track_data[p] = snps

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
