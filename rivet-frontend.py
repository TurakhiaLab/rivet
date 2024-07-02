from flask import Flask, render_template, jsonify, request, Response, send_from_directory, url_for, redirect, send_file
from flask_caching import Cache
from argparse import ArgumentParser
from collections import OrderedDict
from backend import backend
from backend import util
import requests
import time
from time import sleep
import json
import csv
import os
import sys
import webbrowser

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config.from_mapping(util.get_cache_config())
cache = Cache(app)

@app.route("/statistics")
def statistics():
    return render_template('statistics.html')

@app.route("/about")
def getting_started():
    return render_template('getting_started.html')

@app.route("/upload")
def upload():
    return render_template('upload.html')

@app.route("/init", methods=['POST'])
def init():
    env = app.config.get('environment')
    return jsonify({"env": env})

@app.route("/init_track", methods=['POST'])
def init_track():
    genome_size = app.config.get('genome_size')
    genomic_range = app.config.get('genomic_range')
    gene_region_data = app.config.get('gene_region_data')
    env = app.config.get('environment')
    data = {"env": env, "GENOME_SIZE": genome_size,
            "GENOMIC_RANGE": genomic_range,
            "REGION_DATA": gene_region_data}
    return jsonify(data)

@app.route("/get_tree_view", methods=['POST'])
def get_tree_view():
    content = request.get_json()
    date = app.config.get('date')
    HOST = backend.get_treeview_host(date)
    url = backend.generate_taxonium_link(content["Recomb"], content["Donor"], content["Acceptor"], HOST)
    return jsonify({"url": url})

@app.route("/get_usher_link", methods=['POST'])
def get_usher_link():
    content = request.get_json()
    results_file = None
    if content is not None:
        if content["tree"] == 'public':
            results_file = app.config.get('input_recombination_results')
        else:
            results_file = app.config.get('fulltree_recombination_results')
        #TODO: Handle for local version 
        #    return jsonify(None)
        node_id = content["node"]
        _type = content["type"]
    else:
        # Initialize default values from input TSV
        node_id = init_data["recomb_id"]

    samples = backend.get_sampled_desc(results_file, node_id, _type)
    if not samples:
        print("[Error] {} not found in results file.".format(node_id))
        samples = ["England/PHEP-YYGTYSK/2023|2023-03-18", 
                   "England/PHEP-YYGO141/2023|2023-03-13", 
                   "OX449571.1|2023-03-01", 
                   "England/PHEP-YYGPO9T/2023|2023-02-28"]
    # Generate UShER Bio url with samples to place
    url = backend.usher_upload(samples)
    return jsonify({"url": url})

@app.route("/get_relative_data", methods=['POST'])
def get_relative_data():
    months = app.config.get('months')

    content = request.get_json()
    plot_type = str(content["id"])
    tree_type = content["tree_type"]

    if tree_type == 'public':
        recomb_counts = app.config.get('recomb_counts')
        axis_data = app.config.get('relative_recombinants')
    else:
        recomb_counts = app.config.get('full_tree_recomb_counts')
        axis_data = app.config.get('full_tree_relative_recombinants')

    return jsonify({"months": months, "axis_data": axis_data})


@app.route("/get_count_data", methods=['POST'])
def get_count_data():
    months = app.config.get('months')
    content = request.get_json()
    plot_type = str(content["id"])
    tree_selected = content["tree_type"]
    if tree_selected == 'public':
        recomb_counts = app.config.get('recomb_counts')
        month_seq_counts = app.config.get('month_seq_counts')
        month_case_counts = app.config.get('month_case_counts')
    else:
        recomb_counts = app.config.get('full_tree_recomb_counts')
        month_seq_counts = app.config.get('full_tree_month_seq_counts')
        month_case_counts = app.config.get('full_tree_month_case_counts')

    if plot_type == "plot2":
        axis_data = month_seq_counts
        hist_data = backend.format_histogram_data(months, recomb_counts, month_seq_counts, "New Sequences")
    else:
        axis_data = month_case_counts
        hist_data = backend.format_histogram_data(months, recomb_counts, month_case_counts, "New Cases")
    return jsonify({"data": hist_data, "month_data": axis_data,  "recomb_counts": recomb_counts})


@app.route("/get_detailed_overview", methods=['POST'])
def get_detailed_overview():
    content = request.get_json()
    table = app.config.get('table')
    sample_counts = app.config.get('sample_counts')
    metadata = app.config.get('metadata')
    row_id = int(content["id"])
    # NOTE: Column values hardcoded
    recomb_lineage = table[row_id][10]
    recomb_date = table[row_id][15]
    donor_lineage = table[row_id][12]
    acceptor_lineage = table[row_id][14]
    num_desc = sample_counts[table[row_id][1]]
    qc_flags = table[row_id][23]
    earliest_seq = metadata[str(row_id)]["Earliest_seq"]
    latest_seq = metadata[str(row_id)]["Latest_seq"]
    countries = metadata[str(row_id)]["countries"]
    d = {"recomb_lineage": recomb_lineage,
         "recomb_date": recomb_date,
         "donor_lineage": donor_lineage,
         "acceptor_lineage": acceptor_lineage,
         "num_desc": num_desc, 
         "qc_flags": util.css_to_list(qc_flags),
         "earliest_seq": earliest_seq,
         "latest_seq": latest_seq,
         "countries": countries
         }
    return jsonify({"overview": d})

@app.route("/get_overview", methods=['POST'])
def get_overview():
    content = request.get_json()
    tree = content["tree_type"]
    row_id = int(content["id"])

    # NOTE: Column values hardcoded
    if tree == "public":
        table = app.config.get('table')
        sample_counts = app.config.get('sample_counts')
        metadata = app.config.get('metadata')
    else:
        table = app.config.get('full_tree_table')
        sample_counts = app.config.get('full_tree_sample_counts')
        metadata = app.config.get('full_tree_metadata')

    recomb_lineage = table[row_id][10]
    recomb_date = table[row_id][15]
    donor_lineage = table[row_id][12]
    acceptor_lineage = table[row_id][14]
    qc_flags = table[row_id][23]
    earliest_seq = metadata[str(row_id)]["Earliest_seq"]
    latest_seq = metadata[str(row_id)]["Latest_seq"]
    num_desc = sample_counts[table[row_id][1]]
    countries = util.format_css(metadata[str(row_id)]["countries"])
    d = {"recomb_lineage": recomb_lineage,
         "recomb_date": recomb_date,
         "donor_lineage": donor_lineage,
         "acceptor_lineage": acceptor_lineage,
         "qc_flags": util.css_to_list(qc_flags),
         "earliest_seq": earliest_seq,
         "latest_seq": latest_seq,
         "countries": countries,
         "num_desc": num_desc}
    return jsonify({"overview": d})

@app.route("/search_by_sample_id", methods=['POST'])
def search_by_sample_id():
    # Get input search query from user
    query = request.form['query']
    tree = request.form['tree']
    db_file = app.config.get('db_file')
    sample_table = app.config.get('sample_table')
    desc_col = app.config.get('desc_col')

    # Return set of recombinant nodes that return true for substring membership query
    recomb_nodes = backend.search_by_sample_query(db_file, sample_table, desc_col, query)
    return jsonify({"recomb_nodes": recomb_nodes})

@app.route("/search_by_aa_mutation", methods=['POST'])
def search_by_aa_mutation():
    # Get input search query from user
    query = request.form['query']
    db_file = app.config.get('db_file')
    aa_tables = app.config.get('aa_tables')
    aa_col = app.config.get('aa_col')
    node_col = app.config.get('node_col')

    # Return set of recombinant nodes that return true for amino acid membership query
    recomb_nodes = backend.search_by_aa(db_file, aa_tables[1], query, node_col, aa_col)
    return jsonify({"recomb_nodes": recomb_nodes})

@app.route("/get_descendants", methods=["POST"])
def get_descendants():
    init_data = app.config.get('init_data')
    content = request.get_json()
    desc_lookup_table, desc_file = None, None
    if content is not None:
        if content["tree"] == 'public':
            desc_lookup_table = app.config.get('desc_data')
            desc_file = app.config.get('desc_file')
        else:
            desc_lookup_table = app.config.get('full_tree_desc_data')
            desc_file = app.config.get('full_tree_desc_file')
        # If descendants file not provided in local mode, disable feature
        if desc_lookup_table is None:
            print("NONE")
            return jsonify(None)
        node_id = content["node"]
    else:
        # Initialize default values from input TSV
        node_id = init_data["recomb_id"]
    d = backend.query_desc_file(desc_file, desc_lookup_table, node_id)
    #TODO: Add unit tests
    #d = backend.get_node_descendants(desc_d, node_id)
    return jsonify(d)

@app.route("/get_aa_mutations", methods=["POST"])
def get_aa_mutations():
    content = request.get_json()
    recomb_node_id = content["recomb_node_id"]
    tree = content["tree"]
    db_file = app.config.get('db_file')
    aa_tables = app.config.get('aa_tables')
    node_col = app.config.get('node_col')
    if tree == "public":
        aa_mutations, nt_mutations = backend.get_aa_mutations(db_file, aa_tables[0], node_col, recomb_node_id)
    else:
        aa_mutations, nt_mutations = backend.get_aa_mutations(db_file, aa_tables[1], node_col, recomb_node_id)
    return jsonify({"aa": aa_mutations, "nt": nt_mutations})

@app.route("/get_all_full_descendants", methods=["POST", "GET"])
def get_all_full_descendants():
    file =  app.config.get('full_tree_desc_file')
    return send_file(file, mimetype="text/plain",  as_attachment=True)

@app.route("/get_all_public_descendants", methods=["POST", "GET"])
def get_all_public_descendants():
    file =  app.config.get('desc_file')
    return send_file(file, mimetype="text/plain",  as_attachment=True)

@app.route("/download_mat", methods=["POST", "GET"])
def download_mat():
    date = app.config.get('date')
    return jsonify({"date": date})

@app.route("/download_taxonium", methods=["POST", "GET"])
def download_taxonium():
    date = app.config.get('date')
    return jsonify({"date": date})

@app.route("/download_public_table", methods=["POST", "GET"])
def download_public_table():
    # Download public tree results file
    results_file = app.config.get('input_recombination_results')
    return send_file(results_file, mimetype="text/plain",  as_attachment=True)

@app.route("/download_table", methods=["POST", "GET"])
def download_table():
    # Download full tree results file
    results_file = app.config.get('fulltree_recombination_results')
    return send_file(results_file, mimetype="text/plain",  as_attachment=True)

@app.route("/download_breakpoint_plot", methods=["POST", "GET"])
def download_breakpoint_plot():
    breakpoint_png = "static/midpoint_plot.png"
    return send_file(breakpoint_png, mimetype="image/png",  as_attachment=True)

@app.route('/download_select_descendants', methods=["POST", "GET"])
def download_select_descendants():
    init_data = app.config.get('init_data')

    tree = request.args["tree"]
    desc_dict = None
    if tree == 'public':
        desc_lookup_table = app.config.get('desc_data')
        desc_file = app.config.get('desc_file')
    else:
        desc_lookup_table = app.config.get('full_tree_desc_data')
        desc_file = app.config.get('full_tree_desc_file')

    content = request.args["id"]
    if content is not None:
        node_id = content
    else:
        #Initialize default values from input descendants txt file
        node_id = init_data["recomb_id"]

    # Get all descendants for selected node, no max limit of 10k
    desc_string = backend.query_desc_file(desc_file, desc_lookup_table, node_id, True)
    descendant_list = desc_string.split(',')
    filename = node_id + "_descendants.txt"

    def generate_descendants():
        for d in descendant_list:
            yield "{}\n".format(d)

    return Response(
        generate_descendants(),
        mimetype='text/plain',
        headers={'content-disposition': 'attachment; filename={}'.format(filename)})

@app.route("/get_breakpoint_data")
def get_breakpoint_data():
    results_file = app.config.get('input_recombination_results')
    midpoints_dict = backend.generate_breakpoint_data(results_file)
    midpoint_lst = backend.format_bp_data(midpoints_dict)
    return jsonify(midpoint_lst)

@app.route('/get_data_full_tree', methods=['GET', 'POST'])
def get_data_full_tree():
  content = request.get_json()
  env = app.config.get('environment').lower()
  genome_size = app.config.get('genome_size')
  genomic_range = app.config.get('genomic_range')
  gene_region_data = app.config.get('gene_region_data')

  breakpoint1, breakpoint2, descendants = None, None, None
  if content is not None and len(content.keys()) == 2:
      full_table = app.config.get('full_tree_table')
      if content['click'] == "next":
          # Unless index at last row, move to next row
          index = int(content["row_id"]) + 1
          if index < len(full_table):
              row_data = full_table[index]
          else:
              row_data = full_table[int(content["row_id"])]
      elif content['click'] == "previous":
          # Unless index at first row, move to prev row
          index = int(content["row_id"]) - 1
          if not index < 0:
              row_data = full_table[index]
          else:
              row_data = full_table[int(content["row_id"])]
      row_id = row_data[0]
      recomb_id = row_data[1]
      donor_id = row_data[2]
      acceptor_id = row_data[3]
      if env.lower() != "local":
          breakpoint1 = row_data[7]
          breakpoint2 = row_data[8]
          descendants = row_data[17]

  elif content is not None:
      row_id = content["row_id"]
      recomb_id = content["recomb_id"]
      donor_id = content["donor_id"]
      acceptor_id = content["acceptor_id"]
      if env.lower() != "local":
          breakpoint1 = content["breakpoint1"]
          breakpoint2 = content["breakpoint2"]
          descendants = content["descendant"]
  else:
      # Fetch init data on startup, to initialize visualization
      # before user selected input
      init_data = app.config.get('init_data')
      row_id = "0"
      recomb_id = init_data["recomb_id"]
      donor_id = init_data["donor_id"]
      acceptor_id = init_data["acceptor_id"]
      if env != "local":
          breakpoint1 = init_data["breakpoint1"]
          breakpoint2 = init_data["breakpoint2"]
          descendants = init_data["descendants"]

  recomb_informative_only = False
  d = app.config.get('full_tree_snp_data')
  full_tree_positions = app.config.get('full_tree_positions')
  full_tree_info_sites = app.config.get('full_tree_info_sites')
  color_schema = app.config.get('color_schema')

  track_data =  OrderedDict()
  track_data = backend.get_all_snps(recomb_id, donor_id, acceptor_id, breakpoint1, breakpoint2, descendants, full_tree_info_sites, color_schema, d, recomb_informative_only, row_id, env)
  track_data["GENOME_SIZE"] = genome_size
  track_data["GENOMIC_RANGE"] = genomic_range
  track_data["REGION_DATA"] = gene_region_data
  return jsonify(track_data)

@app.route('/get_data', methods=['GET', 'POST'])
def get_data():
  content = request.get_json()
  env = app.config.get('environment').lower()
  genome_size = app.config.get('genome_size')
  genomic_range = app.config.get('genomic_range')
  gene_region_data = app.config.get('gene_region_data')

  breakpoint1, breakpoint2, descendants = None, None, None
  if content is not None and len(content.keys()) == 2:
      table = app.config.get('table')
      if content['click'] == "next":
          # Unless index at last row, move to next row
          index = int(content["row_id"]) + 1
          if index < len(table):
              row_data = table[index]
          else:
              row_data = table[int(content["row_id"])]
      elif content['click'] == "previous":
          # Unless index at first row, move to prev row
          index = int(content["row_id"]) - 1
          if not index < 0:
              row_data = table[index]
          else:
              row_data = table[int(content["row_id"])]
      row_id = row_data[0]
      recomb_id = row_data[1]
      donor_id = row_data[2]
      acceptor_id = row_data[3]
      if env.lower() != "local":
          breakpoint1 = row_data[7]
          breakpoint2 = row_data[8]
          descendants = row_data[17]

  elif content is not None:
      row_id = content["row_id"]
      recomb_id = content["recomb_id"]
      donor_id = content["donor_id"]
      acceptor_id = content["acceptor_id"]
      if env.lower() != "local":
          breakpoint1 = content["breakpoint1"]
          breakpoint2 = content["breakpoint2"]
          descendants = content["descendant"]
  else:
      # Fetch init data on startup, to initialize visualization
      # before user selected input
      init_data = app.config.get('init_data')
      row_id = "0"
      recomb_id = init_data["recomb_id"]
      donor_id = init_data["donor_id"]
      acceptor_id = init_data["acceptor_id"]
      if env != "local":
          breakpoint1 = init_data["breakpoint1"]
          breakpoint2 = init_data["breakpoint2"]
          descendants = init_data["descendants"]

  recomb_informative_only = False
  d = app.config.get('snp_data')
  #positions = app.config.get('positions')
  info_sites = app.config.get('info_sites')
  color_schema = app.config.get('color_schema')

  track_data =  OrderedDict()
  track_data = backend.get_all_snps(recomb_id, donor_id, acceptor_id, breakpoint1, breakpoint2, descendants, info_sites, color_schema, d, recomb_informative_only, row_id, env)
  track_data["GENOME_SIZE"] = genome_size
  track_data["GENOMIC_RANGE"] = genomic_range
  track_data["REGION_DATA"] = gene_region_data
  return jsonify(track_data)

@app.route('/')
@cache.cached()
def table():
  results = {} 
  table = cache.get('table')
  full_table = cache.get('full_tree_table')
  formatted_date = backend.upload_date(app.config.get('date'))
  if table == None:
      table = app.config.get('table')
  if full_table == None:
      full_table = app.config.get('full_tree_table')
  columns = app.config.get('columns')
  full_tree_columns = app.config.get('full_tree_columns')
  env = app.config.get('environment')
  template = 'index.html'
  if env.lower() == "local":
      template = 'local.html'
  results["columns"] = columns
  results["data"] = table
  results["full_columns"] = full_tree_columns
  results["full_data"] = full_table
  return render_template(template, headings=columns, data=table, full_headings=columns, full_data=full_table, date=formatted_date)


if __name__ == "__main__":
  parser = ArgumentParser()
  parser.add_argument("-v", "--vcf", required=True, type=str, help="Give input VCF containing snps of all recombinant/donor/acceptor trio nodes.")
  parser.add_argument("-r", "--recombinant_results", required=True, type=str, help="Give input recombination results file")
  parser.add_argument("-d", "--descendants_file", required=False, type=str, help="File containing descendants (up to 10k) for each node in VCF")
  parser.add_argument("-c", "--config", required=True, type=str, help="Configuration file for defining custom color schema for visualizations.")
  parser.add_argument("-a", "--analysis", required=False, type=str, help="Extra data files with counts of new genomes sequenced per month. Not for general use.")
  args = parser.parse_args()

  # Load and parse config file
  config = backend.parse_config(args.config)
  print("Loading RIVET for MAT date: ", config["date"])

  color_schema = config
  #color_schema = None
  #if args.config != None:
  #    color_schema = backend.parse_config(args.config)
  #else:
  #    print("Config file not provided, using default RIVET settings.")
  #    color_schema = backend.default_color_schema()
  #TODO: Check extensions for input files for correct file format (ie. genbank file)

  # Load recombination results file and get initial data
  results_files = args.recombinant_results.split(",")
  recomb_results = results_files[0]
  fulltree_results = None
  if len(results_files) > 1:
      fulltree_results = results_files[1]
  init_data = backend.init_data(recomb_results, config["environment"])
  app.config['init_data'] = init_data
  # Input recombination results files
  app.config['input_recombination_results'] = recomb_results
  app.config['fulltree_recombination_results'] = fulltree_results

  # Load VCF file
  tick = time.perf_counter()
  vcf_files = args.vcf.split(",")
  vcf_file = vcf_files[0]

  # Load VCF data for public tree
  snp_dict, positions, ref_positions = backend.vcf_to_dict(vcf_file)
  app.config['snp_data'] = snp_dict
  app.config['positions'] = positions

  full_tree_vcf, full_tree_snp_dict, full_tree_positions = None, None, None
  if len(vcf_files) > 1:
      full_tree_vcf = vcf_files[1]
      # Load VCF data for full tree
      full_tree_snp_dict, full_tree_positions, full_tree_positions = backend.vcf_to_dict(full_tree_vcf)
  app.config['full_tree_snp_data'] = full_tree_snp_dict
  app.config['full_tree_positions'] = full_tree_positions

  # Load table 
  full_tree_table, full_tree_columns, metadata, full_tree_metadata, full_tree_info_sites = None, None, None, None, None
  if config["environment"].lower() == "local":
      table, columns = backend.load_local_table(recomb_results, config) 
      info_sites = backend.label_informative_sites_from_vcf(snp_dict, positions, table, ref_positions)
  # Load table for production env
  else:
      table, columns, metadata = backend.load_table(recomb_results, config)
      # Preprocess informative site information for snp plot
      info_sites = backend.label_informative_sites(metadata)
      #backend.make_plot(recomb_results,"static/midpoint_plot.svg")

      # Load table for full tree recombination results
      full_tree_table, full_tree_columns, full_tree_metadata = backend.load_table(fulltree_results, config)
      # Preprocess informative site information for snp plot
      full_tree_info_sites = backend.label_informative_sites(full_tree_metadata)

      # Load additional analysis data files (NOTE: For use at rivet.ucsd.edu analysis page only)
      analysis_files = args.analysis.split(",")
      public_month_counts_file = analysis_files[0]
      full_tree_month_counts_file = analysis_files[1]
      # Load data for recombination counts histogram
      months, month_case_counts, month_seq_counts, recomb_counts, relative_recombinants =  backend.build_counts_histogram(recomb_results, public_month_counts_file)
      app.config['months'] = months
      app.config['month_case_counts'] = month_case_counts
      app.config['month_seq_counts'] = month_seq_counts
      app.config['recomb_counts'] = recomb_counts
      app.config['relative_recombinants'] = relative_recombinants

      full_tree_month_case_counts,full_tree_month_seq_counts,full_tree_recomb_counts,full_tree_relative_recombinants, = None,None,None,None
      if len(results_files) > 1:
          months, full_tree_month_case_counts, full_tree_month_seq_counts, full_tree_recomb_counts, full_tree_relative_recombinants =  backend.build_counts_histogram(fulltree_results, full_tree_month_counts_file)
      app.config['full_tree_month_case_counts'] = full_tree_month_case_counts
      app.config['full_tree_month_seq_counts'] = full_tree_month_seq_counts
      app.config['full_tree_recomb_counts'] = full_tree_recomb_counts
      app.config['full_tree_relative_recombinants'] = full_tree_relative_recombinants


  # App parameters for full tree recombination results
  app.config['full_tree_table'] = full_tree_table
  cache.set("full_tree_table", full_tree_table)
  app.config['full_tree_columns'] = full_tree_columns
  app.config['full_tree_metadata'] = full_tree_metadata
  app.config['full_tree_info_sites'] = full_tree_info_sites

  # Load descendants file
  desc_file, desc_position_table, full_tree_desc_position_table, full_tree_desc_file, recomb_node_set, recomb_desc_dict, desc_dict, sample_counts, full_tree_desc_file, full_tree_sample_counts, full_tree_recomb_node_set = None,None,None,None,None,None,None,None,None,None,None
  if args.descendants_file:
      desc_files = args.descendants_file.split(",")
      print("Loading provided descendants file/s: ", desc_files)
      desc_file = desc_files[0]
      # Load public tree desc file
      recomb_node_set = set([cell[1] for cell in table])
      desc_position_table, sample_counts = backend.preprocess_desc_file(desc_file, recomb_node_set)
      #TODO: recomb_desc_dict -> Only used by search_by_sample feature, disabled for full tree currently

      if len(desc_files) > 1:
          full_tree_desc_file = desc_files[1]
          # Load full tree desc file
          full_tree_recomb_node_set = set([cell[1] for cell in full_tree_table])
          full_tree_desc_position_table, full_tree_sample_counts = backend.preprocess_desc_file(full_tree_desc_file, full_tree_recomb_node_set)


  # App parameter for public tree recombination results 
  app.config['info_sites'] = info_sites
  app.config['table'] = table
  cache.set("table", table)
  app.config['metadata'] = metadata
  app.config['sample_counts'] = sample_counts
  app.config['columns'] = columns
  app.config['recomb_node_set'] = recomb_node_set
  app.config['full_tree_recomb_node_set'] = full_tree_recomb_node_set

  # Parameters for public tree descendants information
  app.config['recomb_desc'] = recomb_desc_dict
  app.config['desc_data'] = desc_position_table
  app.config['desc_file'] = desc_file
 
  # Parameters for full tree descendants information
  app.config['full_tree_recomb_desc'] = full_tree_desc_position_table
  app.config['full_tree_sample_counts'] = full_tree_sample_counts
  app.config['full_tree_desc_data'] = full_tree_desc_position_table
  app.config['full_tree_desc_file'] = full_tree_desc_file
  
  # App tree and config parameters
  app.config['environment'] = config["environment"]
  app.config['date'] = str(config["date"])
  app.config['color_schema'] = color_schema

  # GenBank gene annotation information for given pathogen
  genbank_file = config["ref_seq"]
  features, genome_size = backend.parse_genbank_file(genbank_file)

  # Get tick mark intervals for genomic coordinate track
  genomic_range = []
  genomic_range = [i for i in range(0, genome_size, config["tick_step"])]
  genomic_range[-1] = genome_size
  gene_region_data = backend.get_gene_annotations(features)

  app.config['genome_size'] = genome_size
  app.config['genomic_range'] = genomic_range
  app.config['gene_region_data'] = gene_region_data
  # Name of persistent database file
  app.config['db_file'] = config['db_file']
  app.config['aa_tables'] = (config['aa_public'], config['aa_full'])
  app.config['sample_table'] = config['sample_table']
  app.config['desc_col'] = config['desc_col']
  app.config['aa_col'] = config['aa_col']
  app.config['node_col'] = config['node_col']

  tock = time.perf_counter()
  print(f"Time elapsed: {tock-tick:.2f} seconds")
  print("Input recombination results datatable being displayed: {}".format(recomb_results))

  port = config["port"]
  if config["environment"].lower() == "local":
    webbrowser.open_new('http://127.0.0.1:{}/'.format(port))
    app.run(port=port, threaded=True)
  else:
    app.run(threaded=True)
