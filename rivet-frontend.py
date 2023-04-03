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

app = Flask(__name__) 
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config.from_mapping(util.get_cache_config())
cache = Cache(app)

@app.route("/analysis")
def analysis():
    return render_template('analysis.html')

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

@app.route("/get_tree_view", methods=['POST'])
def get_tree_view():
    content = request.get_json()
    date = app.config.get('date')
    HOST = backend.get_treeview_host(date)
    url = backend.generate_taxonium_link(content["Recomb"], content["Donor"], content["Acceptor"], HOST)
    return jsonify({"url": url})

@app.route("/get_relative_data", methods=['POST'])
def get_relative_data():
    content = request.get_json()
    plot_type = str(content["id"])
    months = app.config.get('months')
    recomb_counts = app.config.get('recomb_counts')
    axis_data = app.config.get('relative_recombinants')
    return jsonify({"months": months, "axis_data": axis_data})


@app.route("/get_count_data", methods=['POST'])
def get_count_data():
    content = request.get_json()
    plot_type = str(content["id"])
    months = app.config.get('months')
    recomb_counts = app.config.get('recomb_counts')
    if plot_type == "plot2":
        axis_data = app.config.get('month_seq_counts')
        hist_data = backend.format_histogram_data(months, recomb_counts, app.config.get('month_seq_counts'), "New Sequences")
    else:
        axis_data = app.config.get('month_case_counts')
        hist_data = backend.format_histogram_data(months, recomb_counts, app.config.get('month_case_counts'), "New Cases")
    return jsonify({"data": hist_data, "month_data": axis_data,  "recomb_counts": recomb_counts})

@app.route("/get_overview", methods=['POST'])
def get_overview():
    content = request.get_json()
    table = app.config.get('table')
    sample_counts = app.config.get('sample_counts')
    #metadata = app.config.get('metadata')
    row_id = int(content["id"])
    # NOTE: Column values hardcoded
    recomb_lineage = table[row_id][7]
    recomb_date = table[row_id][16]
    donor_lineage = table[row_id][9]
    acceptor_lineage = table[row_id][11]
    qc_flags = table[row_id][20]
    #earliest_seq = metadata[str(row_id)]["Earliest_seq"]
    #latest_seq = metadata[str(row_id)]["Latest_seq"]
    #countries = metadata[str(row_id)]["countries"]
    num_desc = sample_counts[table[row_id][1]]
    d = {"recomb_lineage": recomb_lineage,
         "recomb_date": recomb_date,
         "donor_lineage": donor_lineage,
         "acceptor_lineage": acceptor_lineage,
         "qc_flags": util.css_to_list(qc_flags),
         #"earliest_seq": earliest_seq,
         #"latest_seq": latest_seq,
         #"countries": countries,
         "num_desc": num_desc}
    return jsonify({"overview": d})

@app.route("/search_by_sample_id", methods=['POST'])
def search_by_sample_id():
    # Get input search query from user
    query = request.form['query']
    # Load the set of recombinant node ids
    recomb_desc_d = app.config.get('recomb_desc')
    # Return set of recombinant nodes that return true for substring membership query
    recomb_nodes = backend.search_by_sample(query,recomb_desc_d)
    return jsonify({"recomb_nodes": recomb_nodes})

@app.route("/get_descendants", methods=["POST"])
def get_descendants():
    init_data = app.config.get('init_data')
    desc_d = app.config.get('desc_data')
    if desc_d is None:
        return jsonify(None)
    content = request.get_json()
    if content is not None:
        node_id = content["node"]
    else:
        # Initialize default values from input TSV
        node_id = init_data["recomb_id"]
    d = backend.get_node_descendants(desc_d, node_id)
    return jsonify(d)

@app.route("/get_all_descendants", methods=["POST", "GET"])
def get_all_descendants():
    desc_file = app.config.get('desc_file')
    return send_file(desc_file, mimetype="text/plain",  as_attachment=True)

@app.route("/download_mat", methods=["POST", "GET"])
def download_mat():
    date = app.config.get('date')
    return jsonify({"date": date})

@app.route("/download_taxonium", methods=["POST", "GET"])
def download_taxonium():
    date = app.config.get('date')
    return jsonify({"date": date})

@app.route("/download_table", methods=["POST", "GET"])
def download_table():
    results_file = app.config.get('input_recombination_results')
    # Parse results file for table download
    results_data = backend.parse_file(results_file)
    return jsonify(results_data)

@app.route("/download_breakpoint_plot", methods=["POST", "GET"])
def download_breakpoint_plot():
    breakpoint_png = "static/midpoint_plot.png"
    return send_file(breakpoint_png, mimetype="image/png",  as_attachment=True)

@app.route('/download_select_descendants', methods=["POST", "GET"])
def download_select_descendants():
    init_data = app.config.get('init_data')
    desc_d = app.config.get('desc_data')

    content = request.args["id"]
    if content is not None:
        node_id = content
    else:
        #Initialize default values from input descendants txt file
        node_id = init_data["recomb_id"]

    # Get descendants for selected node
    descendant_list = desc_d[node_id]
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

@app.route('/get_data', methods=['GET', 'POST'])
def get_data():
  content = request.get_json()
  env = app.config.get('environment').lower()
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
          breakpoint1 = row_data[4]
          breakpoint2 = row_data[5]
          descendants = row_data[12]

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
  positions = app.config.get('positions')
  info_sites = app.config.get('info_sites')
  color_schema = app.config.get('color_schema')

  track_data =  OrderedDict()
  track_data = backend.get_all_snps(recomb_id, donor_id, acceptor_id, breakpoint1, breakpoint2, descendants, info_sites, color_schema, d, recomb_informative_only, row_id, env)
  return jsonify(track_data)

@app.route('/')
@cache.cached()
def table():
  results = {} 
  table = cache.get('table')
  if table == None:
      table = app.config.get('table')
  columns = app.config.get('columns')
  env = app.config.get('environment')
  template = 'index.html'
  if env.lower() == "local":
      template = 'local.html'
  results["columns"] = columns
  results["data"] = table
  return render_template(template, headings=columns, data=table)


if __name__ == "__main__":
  parser = ArgumentParser()
  parser.add_argument("-v", "--vcf", required=True, type=str, help="Give input VCF containing snps of all recombinant/donor/acceptor trio nodes.")
  parser.add_argument("-r", "--recombinant_results", required=True, type=str, help="Give input recombination results file")
  parser.add_argument("-d", "--descendants_file", required=False, type=str, help="File continaing descendants (up to 10k) for each node in VCF")
  parser.add_argument("-c", "--config", required=True, type=str, help="Configuration file for defining custom color schema for visualizations.")
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
   
  # Load recombination results file and get initial data
  recomb_results = args.recombinant_results
  init_data = backend.init_data(recomb_results, config["environment"])
  app.config['init_data'] = init_data
  app.config['input_recombination_results'] = recomb_results

  # Load VCF file
  tick = time.perf_counter()
  vcf_file = args.vcf
  snp_dict, positions, ref_positions = backend.vcf_to_dict(vcf_file)
  app.config['snp_data'] = snp_dict
  app.config['positions'] = positions

  # Load table 
  if config["environment"].lower() == "local":
      table, columns = backend.load_local_table(recomb_results, config) 
      info_sites = backend.label_informative_sites_from_vcf(snp_dict, positions, table, ref_positions)
  else:
      table, columns, metadata = backend.load_table(recomb_results, config)
      # Preprocess informative site information for snp plot
      info_sites = backend.label_informative_sites(metadata)
      backend.make_plot(recomb_results,"static/midpoint_plot.svg")

      # Load data for recombination counts histogram
      months, month_case_counts, month_seq_counts, recomb_counts, relative_recombinants =  backend.build_counts_histogram(recomb_results)
      app.config['months'] = months
      app.config['month_case_counts'] = month_case_counts
      app.config['month_seq_counts'] = month_seq_counts
      app.config['recomb_counts'] = recomb_counts
      app.config['relative_recombinants'] = relative_recombinants

  # Load descendants file
  desc_file = args.descendants_file
  recomb_node_set, recomb_desc_dict, desc_dict, sample_counts = None,None,None,None
  if desc_file is not None:
      print("Loading provided descendants file: ", desc_file)
      recomb_node_set = set([cell[1] for cell in table])
      desc_dict, recomb_desc_dict, sample_counts = backend.load_descendants(desc_file, recomb_node_set)

  app.config['color_schema'] = color_schema
  app.config['info_sites'] = info_sites
  app.config['table'] = table
  #app.config['metadata'] = metadata
  app.config['sample_counts'] = sample_counts
  app.config['columns'] = columns
  cache.set("table", table)
  app.config['date'] = str(config["date"])
  app.config['recomb_desc'] = recomb_desc_dict
  app.config['desc_data'] = desc_dict
  app.config['desc_file'] = desc_file
  app.config['environment'] = config["environment"]

  tock = time.perf_counter()
  print(f"Time elapsed: {tock-tick:.2f} seconds")
  print("Input recombination results datatable being displayed: {}".format(recomb_results))

  app.run(threaded=True)
