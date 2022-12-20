from flask import Flask, render_template, jsonify, request, Response, send_from_directory, url_for, redirect
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

@app.route("/start")
def getting_started():
    return render_template('getting_started.html')

@app.route("/upload")
def upload():
    return render_template('upload.html')

@app.route("/get_descendants", methods=["POST", "GET"])
def get_descendants():
    init_data = app.config.get('init_data')
    desc_d = app.config.get('desc_data')

    content = request.get_json()
    if content is not None:
        node_id = content["node"]
    else:
        # Initialize default values from input TSV
        node_id = init_data["recomb_id"]

    return jsonify(desc_d[node_id])


@app.route("/get_all_descendants", methods=["POST", "GET"])
def get_all_descendants():
    desc_file = app.config.get('desc_file')
    desc_data = backend.parse_file(desc_file)
    return jsonify(desc_data)

@app.route("/download_table", methods=["POST", "GET"])
def download_table():
    results_file = app.config.get('input_recombination_results')
    results_data = backend.parse_file(results_file)
    return jsonify(results_data)

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
      recomb_id = init_data["recomb_id"]
      donor_id = init_data["donor_id"]
      acceptor_id = init_data["acceptor_id"]
      breakpoint1 = init_data["breakpoint1"]
      breakpoint2 = init_data["breakpoint2"]
      descendants = init_data["descendants"]

  #TODO: Add back visualization settings side panel toggle
  recomb_informative_only = False
      
  d = app.config.get('snp_data')
  positions = app.config.get('positions')

  track_data =  OrderedDict()
  #TODO: Add back functionality to this function for displaying recombinant informative snps only
  track_data = backend.get_all_snps(recomb_id, donor_id, acceptor_id, breakpoint1, breakpoint2, descendants, d, recomb_informative_only)
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
  args = parser.parse_args()
  
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
  table, columns = backend.load_table(recomb_results)
  app.config['table'] = table
  app.config['columns'] = columns
  cache.set("table", table)

  tock = time.perf_counter()
  print(f"Time elapsed: {tock-tick:.2f} seconds")
  print("Input recombination results datatable being displayed: {}".format(recomb_results))

  app.run(threaded=True)
