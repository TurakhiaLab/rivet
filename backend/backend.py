"""
Backend functions for RIVET UI
"""

import numpy as np
import json
import yaml
import time
import datetime
import random
import string
from cyvcf2 import VCF
from functools import lru_cache
from collections import OrderedDict
from alive_progress import alive_bar, alive_it
import heapq
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from urllib.parse import quote_plus
import sys
import seaborn as sns
import matplotlib.patches as patches
import gzip
import lzma
import csv
import io
import os


def parse_config(config_file):
    """
    Parse input configuration file to use custom coloring for visualization.
    """
    with open(config_file) as f:
      config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def default_color_schema():
    """
    Default color schema to use if config file not provided.
    """
    d = {'a': '#cc0000', 'g': '#003366', 'c': '#57026f', 't': '#338333', 'base_matching_reference': '#dadada', 'reference_track': '#333333', 'recomb_match_acceptor': '#2879C0', 'recomb_match_donor': '#F9521E', 'non_informative_site': '#dadada', 'breakpoint_intervals': '#800000', 'genomic_regions': '#33333'}
    return d

def get_treeview_host(date):
    """
    Get the HOST url for public Taxonium tree view .jsonl.gz file.
    """
    BUCKET_NAME = "public_trees"
    OBJECT_NAME = "{}.taxonium.jsonl.gz".format(date)
    HOST = "https://storage.googleapis.com/"
    HOST += "/".join([BUCKET_NAME,OBJECT_NAME])
    return HOST

def usher_upload(samples):
    """
    """
    USHER_WEB_BASE = "https://genome.ucsc.edu/cgi-bin/hgPhyloPlace?db=wuhCor1&subtreeSize=1000&phyloPlaceTree=hgPhyloPlaceData/wuhCor1/public.plusGisaid.latest.masked.pb&namesOrIds="
    url = USHER_WEB_BASE + quote_plus('\n'.join(samples))
    return url

def format_histogram_data(months, recomb_counts, count_list, label):
    """
    """
    data = []
    for i in range(len(months)):
        data.append({
                "month": months[i],
                "values":
                    [
                      {"key": label, "value": count_list[i]},
                      {"key": "Recombinants Count", "value": recomb_counts[i]}
                    ]
                  })
    return data

def create_month_bins():
    years = ["2020", "2021", "2022", "2023"]
    months =["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    month_bins = {}
    for y in years:
        for m in months:
            # Stop at current month (2023_02)
            if y == "2023" and m == "03":
                return month_bins
            month_bins[y + "_" + m] = set()

def build_counts_histogram(results_file):
    """
    """
    month_bins = create_month_bins()
    #TODO: Load this data from an additional file

    #Month counts for new infections
    #Data(daily global time - series)
    # obtained from : https:  // github.com/CSSEGISandData/COVID-19
    #Separate scripts used to process this data by month
    month_counts_new_infections = {"2020_01": 9927, "2020_02": 76096, "2020_03": 783348, "2020_04": 2412716, "2020_05": 2901229, "2020_06": 4292072, "2020_07": 7118656, "2020_08": 7941296, "2020_09": 8498335, "2020_10": 12122070, "2020_11": 17266494, "2020_12": 20356383, "2021_01": 19546070, "2021_02": 11253786,
        "2021_03": 14772312, "2021_04": 22542204, "2021_05": 19347136, "2021_06": 11472596, "2021_07": 15676958, "2021_08": 19894993, "2021_09": 16061455,
        "2021_10": 13064658, "2021_11": 15702891, "2021_12": 25614610, "2022_01": 90483564, "2022_02": 58251972, "2022_03": 51347034, "2022_04": 25217142,
        "2022_05": 16213566, "2022_06": 17732748, "2022_07": 29650733, "2022_08": 25713990, "2022_09": 14721332, "2022_10": 12795215, "2022_11": 12388536,
        "2022_12": 17219669, "2023_01": 10270797, "2023_02": 4587649}

    #Month counts for sequences added to the MAT
    #New sequenced genomes each month obtained from public metadata
    # file : https://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/
    month_new_seq_counts = {"2020_01": 368, "2020_02": 622, "2020_03": 28008, "2020_04": 32225, "2020_05": 15548, "2020_06": 15521, "2020_07": 17312,
        "2020_08": 19188, "2020_09": 26088, "2020_10": 48073, "2020_11": 59890, "2020_12": 75421, "2021_01": 126779, "2021_02": 137727,
        "2021_03": 214674, "2021_04": 210270, "2021_05": 146672, "2021_06": 152416, "2021_07": 303144, "2021_08": 470300, "2021_09": 458061,
        "2021_10": 453609, "2021_11": 581793, "2021_12": 529523, "2022_01": 471163, "2022_02": 435674, "2022_03": 466953, "2022_04": 217273,
        "2022_05": 162331, "2022_06": 172118, "2022_07": 186467, "2022_08": 129673, "2022_09": 85326, "2022_10": 77278, "2022_11": 71777,
        "2022_12": 86676, "2023_01": 59626, "2023_02": 18069}

    #Months is ticks on x - axis
    months = list(month_bins.keys())

    #Case counts(right y - axis, for plot 1)
    month_infection_counts = list([x for x in month_counts_new_infections.values()])

    #New sequence counts(right y - axis, for plot 2)
    month_sequence_counts = list([x for x in month_new_seq_counts.values()])

    f = open(results_file, "r")
    recomb_id_to_date = dict()
    next(f)
    for line in f:
        splitline = line.strip().split('\t')
        recomb_id = splitline[0]
        recomb_date = splitline[15]
        parsed_date = recomb_date.split('-')
        year = str(parsed_date[0])
        month = str(parsed_date[1])
        joined_date = "_".join([year, month])
        if joined_date not in month_bins.keys():
            print("[ERROR] CHECK Formatting: {}".format(joined_date))
            exit(1)
        month_bins[joined_date].add(recomb_id)
    recomb_counts = list([len(x) for x in month_bins.values()])
    f.close()

    # Proportion of new recombinants relative to new genome sequences added to the MAT each month
    relative_recombinants = []
    for i in range(len(recomb_counts)):
        relative = (recomb_counts[i]/month_sequence_counts[i])*1000
        relative_recombinants.append(relative)
    return months, month_infection_counts, month_sequence_counts, recomb_counts, relative_recombinants

def parse_file(file):
    """
    """
    data = []
    f = open(file, "r")
    for line in f:
        data.append(line.strip().split('\t'))
    return data

def check_column_format(row):
    """
    Check to make sure input results file columns start with 3 trio node ids:
        recomb_node_id \t donor_node_id \t acceptor_node_id
    """
    substr = "node_"
    if (row[0].startswith(substr) and row[1].startswith(substr) and row[2].startswith(substr)):
          return False
    return True

def fetch_row_data(table, row_id):
    """
    Fetch data from table for a given row id
    """
    return [row[row_id] for row in table]

def init_data(results_file, env):
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
        if env.lower() == "local":
            continue
        d["breakpoint1"] = splitline[3]
        d["breakpoint2"] = splitline[4]
        d["descendants"] = "NA"
        return d

def load_descendants(desc_file, recomb_node_set):
    """
    """
    tick = time.perf_counter()
    # TODO: Load a more succinct lookup table for all descendants
    # and for each recombinant node store an index into descendants table
    if desc_file is None:
        return None, None
    BUF_SIZE = 1048576 # Read 1MB at a time
    if desc_file.endswith(".xz"):
        f = io.TextIOWrapper(io.BufferedReader(lzma.open(desc_file, 'rb'), buffer_size=BUF_SIZE))
    elif desc_file.endswith(".gz"):
        f = io.TextIOWrapper(io.BufferedReader(gzip.open(desc_file, 'rb'), buffer_size=BUF_SIZE))
    else:
        f = open(desc_file, 'r', buffering=BUF_SIZE)
    d = {}
    recomb_to_d = {}
    sample_counts = {}

    # Skip over column headers (assuming one)
    f.readline()
    for line in f:
        splitline = line.strip().split('\t')
        node_id = splitline[0]
        descendants_string = splitline[1]
        descendants_list = descendants_string.split(', ')
        d[node_id] = descendants_list
        if node_id not in recomb_node_set:
            continue
        recomb_to_d[node_id] = descendants_list
        sample_counts[node_id] = len(descendants_list)

    f.close()
    tock = time.perf_counter()
    print(f"Time elapsed loading desc file: {tock-tick:.2f} seconds")
    return d, recomb_to_d, sample_counts

def load_recombinant_descendants(desc_file, recomb_node_set):
    """
    """
    if desc_file == None:
        return None
    with open(desc_file) as f:
      d = {}
      # Skip over column headers (assuming one)
      next(f)
      for line in f:
        splitline = line.strip().split('\t')
        node_id = splitline[0]
        if node_id not in recomb_node_set:
            continue
        descendants_string = splitline[1]
        descendants_list = descendants_string.split(', ')
        d[node_id] = descendants_list
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

def format_info_sites(csv_string):
    """
    Parse comma separated string of informative sites to a list of informative sites
    """
    _list = csv_string.split(",")
    return _list

def tsv_to_dict(results_tsvfile, metadata_start_col = None):
    """
    Convert the recombination TSV results file to a dictionary and use recombination_node_id as the key for each data row.

    @param: metadata_start_col: 
        Starting position of extra metadata columns to remove and not display in UI datatable
    """
    dictionary = {}
    metadata = {}
    with open(results_tsvfile) as f:
      # Extract column headers from input results tsv file, removing extra metadata columns
      column_headers = f.readline().strip().split('\t')[:metadata_start_col - 1]
      column_headers.append("Quality Control (QC) Flags")
      #for i,name in enumerate(column_headers):
      #  if(name=="Filter"):
      #      column_headers[i]="Quality Control (QC) Flags"
      lines = f.readlines()
      for index, line in enumerate(lines):
        splitline = line.strip().split('\t')

        node_metadata = {}
        # Do not display extra metadata columns in results datatable
        if metadata_start_col is not None:
            dictionary[str(index)] = splitline[:metadata_start_col - 1]
            #print(splitline[:metadata_start_col - 1])
            #NOTE: Expecting Filter/QC annotations to be at column 20 in results file
            # Get QC annotations from results file
            dictionary[str(index)].append(splitline[20])

            # Get string of informative sites and parse each position to a list of (str) positions
            info_sites_list = splitline[metadata_start_col-1:][0].split(",")
            
            # Check number of informative positions matches the number of characters in ABAB string
            err_message = "Informative sites not matching ABAB string for recomb node: {}".format(splitline[0])
            assert len(info_sites_list) == len(splitline[12]), err_message
            
            # Add informative site and informative seq to metadata
            node_metadata["recomb_id"] = splitline[0]
            node_metadata["InfoSites"] = info_sites_list
            node_metadata["InfoSeq"] = splitline[12]
            if len(splitline) > 21:
                node_metadata["Earliest_seq"] = splitline[21]
                node_metadata["Latest_seq"] = splitline[22]
                node_metadata["countries"] = splitline[23]
            
            metadata[str(index)] = node_metadata
        else:
            # Build dictionary with key: recomb_node_id
            # and value : corresponding data for that recombinant node
            dictionary[str(index)] = splitline 
    return dictionary, column_headers, metadata


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
        #if splitline[19]!="PASS":
        if splitline[len(splitline)-1]!="PASS":
            continue
        intervals.append(tuple( format_bp_interval(splitline[bp1_col_idx])))
        interval2=tuple(format_bp_interval(splitline[bp2_col_idx]))
        if (interval2[1]!=29903):
            intervals.append(interval2)
        
    return sorted(intervals)

def place_intervals(intervals):
    track_heap=[]
    segments_to_plot=[]
    empty_tracks=[]
    max_track_cnt=0
    for interval in intervals:
        cur_track_cnt=None
        if( ( len(track_heap)==0 or track_heap[0][0]>interval[0]) and (len(empty_tracks)==0) ):
            cur_track_cnt=len(track_heap)
        else:
            while(len(track_heap)>0 and track_heap[0][0]<=interval[0]):
                heapq.heappush(empty_tracks,heapq.heappop(track_heap)[1])
            cur_track_cnt=heapq.heappop(empty_tracks)
        heapq.heappush(track_heap,(interval[1],cur_track_cnt))
        max_track_cnt=max(max_track_cnt,len(track_heap))
        segments_to_plot.append([(interval[0],cur_track_cnt),(interval[1],cur_track_cnt)])
    return (max_track_cnt,segments_to_plot)

def make_plot(recomb_results_file, plot_file):
    dpi=96
    intervals=load_intervals(recomb_results_file)
    (max_height,segments_to_plot)=place_intervals(intervals)
    fig,[ax,region_plot_ax] = plt.subplots(2,1,sharex=True,gridspec_kw={'height_ratios': [20, 1],'hspace': 0.08},figsize=(1500/dpi,1000/dpi))
    ax.set_xlim(0,30000)
    ax.set_ylim(0,max_height*1.1)
    ax.set_ylabel("Breakpoint Intervals")
    line_segments = LineCollection(segments_to_plot,linewidths=0.5)
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
    plt.savefig(plot_file, format='svg', dpi=1200)

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
    # Enable mutation types to show in tree
    link += '&mutationTypesEnabled={"aa":true, "nt":true}'
    # Enable treenome by default
    link += '&treenomeEnabled=true'
    return link

def label_informative_sites(metadata):
    """
    For each recombinant node, check list of recombination-informative positions
    and label each position as either matching the "D" (Donor), or "A" (Acceptor)
    """
    info_node_matches = {}
    # Iterate through list of recombination results
    for (key,value) in metadata.items():
        info_positions = value["InfoSites"]
        info_seq = value["InfoSeq"]
        i = 0
        positions = {}
        for pos in info_positions:
            # Position where recomb matches the acceptor
            if info_seq[i] == "B":
                positions[pos] = "A"
            else:
                # Otherwise this is a position where recomb matches the donor
                positions[pos] = "D"

            # Move to next sequence in ABAB string
            i+=1
        info_node_matches[key] = positions
    return info_node_matches

def determine_informative(recomb_snp, donor_snp, acceptor_snp):
    """
    Return "D" if the recombinant matched only the donor
    Return "A" if the recombinant matched only the acceptor
    Return None if not an informative SNV position
    """
    if donor_snp == acceptor_snp:
        return None
    if recomb_snp == donor_snp:
        return "D"
    if recomb_snp == acceptor_snp:
        return "A"

def label_informative_sites_from_vcf(snp_dict, positions, table, ref_positions):
    """
    For each recombinant node, check VCF to see if position is recombinant-informative site
    and label each position as either matching the "D" (Donor), or "A" (Acceptor)
    """
    info_node_matches = {}
    row_ids = [cell[0] for cell in table]
    recomb_ids = [cell[1] for cell in table]
    donor_ids = [cell[2] for cell in table]
    acceptor_ids = [cell[3] for cell in table]
    for index in range(0,len(row_ids)):
        _id = row_ids[index]
        recomb_id = recomb_ids[index]
        donor_id = donor_ids[index]
        acceptor_id = acceptor_ids[index]
        pos = {}
        for p in positions:
            if p in snp_dict[recomb_id]:
                r_allele = snp_dict[recomb_id][p]
            else:
                r_allele = ref_positions[p]
            if p in snp_dict[donor_id]:
                d_allele = snp_dict[donor_id][p]
            else:
                d_allele = ref_positions[p]
            if p in snp_dict[acceptor_id]:
                a_allele = snp_dict[acceptor_id][p]
            else:
                a_allele = ref_positions[p]

            char = determine_informative(r_allele, d_allele, a_allele)
            if char:
                pos[p] = char
        info_node_matches[str(index)] = pos
    return info_node_matches


def build_table(results_dict, columns, config):
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
        for i in range(0,len(row)):
            try:
                str=row[i]
                if(str[0]=="(" and str[-1]==")"):
                    fields=str[1:-1].split(",")
                    if((len(fields)==2) and (fields[0]=="0" or fields[1]=="29903" )):
                        row[i]="-"
            except IndexError:
                pass
        row.append(generate_taxonium_link(value[0], value[1], value[2], get_treeview_host(config["date"])))
        # Add unique row key as first element in each row
        row.insert(0,key)
        table.append(row)

        # Iterate row for error message
        row_num +=1

    return table

def load_local_table(results_file, config):
    """
    Create table for displaying results locally.
    """
    results_dict = {}
    with open(results_file) as f:
      # Extract column headers from input results tsv file
      column_headers = f.readline().strip().split('\t')
      for i,name in enumerate(column_headers):
        if(name=="Filter"):
            column_headers[i]="Quality Control (QC) Flags"
      lines = f.readlines()
      for index, line in enumerate(lines):
        # Assumes recomb_id, donor_id, acceptor_id are first 3 columns in results file
        splitline = line.strip().split('\t')
        results_dict[str(index)] = splitline 
    table = []
    row_num = 1 
    for [key, value] in results_dict.items():
        # Check that first 3 columns are node_ids
        if(check_column_format(value)):
            raise RuntimeError(colored("[ERROR]: First 3 columns must be: recomb_node_id\t donor_node_id\t acceptor_node_id.  Formatting error occurring at line: {}".format(row_num), 'red', attrs=['reverse']))
            
        row = [value[i] for i in range(0,len(column_headers))]
        # Add unique row key as first element in each row
        row.insert(0,key)
        table.append(row)

        # Iterate row for error message
        row_num +=1
    # Add first hidden column with row ids to datatable
    column_headers.insert(0,"Row")
    return table, column_headers


def load_table(results_file, config):
    """
    Create table from dictionary. Return table and columns as separate lists.
    """
    # Check date in config file properly formatted
    if not isinstance(config["date"], datetime.date):
        raise RuntimeError(colored("[ERROR]: Check formatting of MAT 'date' field provided in config.yaml file (-c). Expected format: year-month-day"), 'red', attrs=['reverse'])

    #Convert final recombination results file to dictionary indexed by row_id
    # Extract datatable column headers also
    results_dict, columns, metadata = tsv_to_dict(results_file, 20)

    # Add additional column for Taxodium tree view links
    # Last visible column in datatable by default
    columns.append("Click to View")

    # Check header information present in file
    if(len(columns) == 0):
        raise RuntimeError(colored("[ERROR]: Check input results file: {}. Empty file or missing header information".format(results_file), 'red', attrs=['reverse']))

    table = build_table(results_dict, columns, config)

    # Add first hidden column with row ids to datatable
    columns.insert(0,"Row")

    return table, columns, metadata


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
  ref_positions = {} 

  # Create dictionary of all node_ids (recomb/donor/acceptor) (samples from VCF file).
  # Then the value at each node id, is an OrderedDict with the genotypes at each position, 
  # ordered by increasing genomic position.
  nodes_ids = {key: OrderedDict() for key in samples}
  nodes_ids["Reference"] = OrderedDict()
  print("Loading input VCF file: {}".format(vcf_file))

  # Iterate over genomic positions
  for record in alive_it(vcf_reader):
      # Record reference allele at each genomic position
      nodes_ids["Reference"][str(record.POS)] = str(record.REF)
      positions.append(str(record.POS))
      ref_positions[str(record.POS)] = str(record.REF)

      position = str(record.POS)
      alleles_indexes = np.nonzero(record.gt_types)
      genotype_array = record.gt_bases

      for i in np.nditer(alleles_indexes):
          sample_name = samples[i]
          nodes_ids[sample_name][position] = genotype_array[i]

  # Return nested dictionary contaning all nodes and corresponding snps
  return nodes_ids, positions, ref_positions


def get_positions(snp_data):
    """
    """
    pos = set()
    for (key, value) in enumerate(snp_data.items()):
        pos.add(value[0])
    return pos

def get_all_snps(recomb_id, donor_id, acceptor_id, breakpoint1, breakpoint2, descendants, info_sites, color_schema, d, recomb_informative_only, row_id, env):
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
    positions = set()

    for snps in [recomb_id, donor_id, acceptor_id]:
        positions = positions.union(get_positions(d[snps]))
    pos = list(positions)
    pos.sort()
    #print("Number of positions: ", len(pos))

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
    if env != "local":
      try:
          breakpoint1 = breakpoint1[1:len(breakpoint1)-1]
          interval1 = {}
          intervals1 = breakpoint1.split(",")
          interval1["xpos"] = intervals1[0]
          interval1["end"] = intervals1[1]
          breakpoints["breakpoint1"] = interval1
      except IndexError:
          pass

      try:
          breakpoint2 = breakpoint2[1:len(breakpoint2)-1]
          interval2 = {}
          intervals2 = breakpoint2.split(",")
          interval2["xpos"] = intervals2[0]
          interval2["end"] = intervals2[1]
          breakpoints["breakpoint2"] = interval2
      except IndexError:
          pass

      # Now add breakpoints to the rest of the data
      data["BREAKPOINTS"] = breakpoints
      data["DESCENDANTS"] = descendants
    data["NODE_IDS"] = node_ids

    # Add recombinant-informative metadata to track data
    data["INFO_SITES"] = info_sites[row_id]

    # Add color_schema from input config file to track data
    data["COLOR"] = color_schema
    data["ID"] = row_id
    
    return data


def get_node_descendants(desc_d, node_id):
    """
    Fetch node descendants for the selected node, up to 10k max
    """
    limit = 10000
    descendant_list = desc_d[node_id]
    if len(descendant_list) > limit:
        return descendant_list[:limit]
    return descendant_list

def search_by_sample(substr, recomb_desc_dict):
    """
    """
    filtered_results = {}
    recomb_nodes = set()
    pattern = substr.lower()
    for key,value in recomb_desc_dict.items():
        if pattern in value[0].lower():
            filtered_results[key] = value
            recomb_nodes.add(key)
    return list(recomb_nodes)
