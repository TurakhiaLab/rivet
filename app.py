from flask import Flask, render_template, jsonify, request, Response, send_from_directory, url_for, redirect, send_file
from flask_caching import Cache
from argparse import ArgumentParser
from collections import OrderedDict
from backend import backend
from backend import util
import pandas as pd
import requests
import time
from time import sleep
import json
import csv

app = Flask(__name__) 
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config.from_mapping(util.get_cache_config())
cache = Cache(app)

@app.route("/breakpoints")
def breakpoints():
    return render_template('breakpoints.html')

@app.route("/about")
def getting_started():
    return render_template('getting_started.html')

@app.route("/upload")
def upload():
    return render_template('upload.html')

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
    print(midpoint_lst)
    
    return jsonify(midpoint_lst)

@app.route('/get_data', methods=['GET', 'POST'])
def get_data():
  content = request.get_json()
  if content is not None:
      row_id = content["row_id"]
      recomb_id = content["recomb_id"]
      donor_id = content["donor_id"]
      acceptor_id = content["acceptor_id"]
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
      breakpoint1 = init_data["breakpoint1"]
      breakpoint2 = init_data["breakpoint2"]
      descendants = init_data["descendants"]

  recomb_informative_only = False
  d = app.config.get('snp_data')
  positions = app.config.get('positions')
  info_sites = app.config.get('info_sites')
  color_schema = app.config.get('color_schema')

  track_data =  OrderedDict()
  track_data = backend.get_all_snps(recomb_id, donor_id, acceptor_id, breakpoint1, breakpoint2, descendants, info_sites, color_schema, d, recomb_informative_only, row_id)
  print("TRIO DATA SELECTED: ", track_data)
  return jsonify(track_data)

@app.route('/')
@cache.cached()
def table():
  results = {} 
  table = cache.get('table')
  if table == None:
      table = app.config.get('table')
  columns = app.config.get('columns')
  results["columns"] = columns
  results["data"] = table
  return render_template('index.html', headings=columns, data=table)


if __name__ == "__main__":
  parser = ArgumentParser()
  parser.add_argument("-v", "--vcf", required=True, type=str, help="Give input VCF containing snps of all recombinant/donor/acceptor trio nodes.")
  parser.add_argument("-r", "--recombinant_results", required=True, type=str, help="Give input recombination results file")
  parser.add_argument("-d", "--descendants_file", required=True, type=str, help="File continaing descendants (up to 10k) for each node in VCF")
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
  init_data = backend.init_data(recomb_results)
  app.config['init_data'] = init_data
  app.config['input_recombination_results'] = recomb_results
  backend.make_plot(recomb_results,"static/midpoint_plot.png")

  # Load VCF file
  tick = time.perf_counter()
  vcf_file = args.vcf
  snp_dict, positions = backend.vcf_to_dict(vcf_file)
  app.config['snp_data'] = snp_dict
  app.config['positions'] = positions

  # Load descendants file
  desc_file = args.descendants_file
  desc_dict = backend.load_descendants(desc_file)
  app.config['desc_data'] = desc_dict
  app.config['desc_file'] = desc_file

  # Load table 
  table, columns, metadata = backend.load_table(recomb_results, config)
  # Preprocess informative site information for snp plot
  info_sites = backend.label_informative_sites(metadata)
  recomb_node_set = set([cell[1] for cell in table])
  recomb_desc_dict = backend.load_recombinant_descendants(desc_file, recomb_node_set)

  app.config['color_schema'] = color_schema
  app.config['info_sites'] = info_sites
  app.config['table'] = table
  app.config['columns'] = columns
  cache.set("table", table)
  app.config['date'] = str(config["date"])
  app.config['recomb_desc'] = recomb_desc_dict

  tock = time.perf_counter()
  print(f"Time elapsed: {tock-tick:.2f} seconds")
  print("Input recombination results datatable being displayed: {}".format(recomb_results))

  app.run(threaded=True)
