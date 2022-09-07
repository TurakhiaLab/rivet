import json
from flask import Flask, render_template, jsonify, request, Response, send_from_directory, url_for
from argparse import ArgumentParser
from collections import OrderedDict
from backend import backend

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/snp_data')
def snp_data():
  d = app.config.get('snp_data')
  return jsonify(d)


@app.route('/datatable')
def datatable():
  results = {} 
  table, columns = backend.load_table(app.config.get('input_recombination_results'))
  results["columns"] = columns
  results["data"] = table
  return jsonify(results)


if __name__ == "__main__":
  parser = ArgumentParser()
  parser.add_argument("-v", "--vcf", required=True, type=str, help="Give input VCF containing snps of all recombinant/donor/acceptor trio nodes.")
  parser.add_argument("-r", "--recombinant_results", required=True, type=str, help="Give input recombination results file")
  args = parser.parse_args()
  vcf_file = args.vcf
  recomb_results = args.recombinant_results
  print("Loading VCF file.")
  snp_dict = backend.vcf_to_dict(vcf_file)
  app.config['snp_data'] = snp_dict
  print("Input recombination results datatable being displayed: {}".format(recomb_results))
  app.config['input_recombination_results'] = recomb_results
  app.run()
